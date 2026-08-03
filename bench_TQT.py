from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base, parse_front_matter
from src.chunking import FixedSizeChunker
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)


DATA_DIR = os.getenv("LAB_DATA_DIR", "data")
TOP_K = 3
_BODY_CACHE: dict[str, str] = {}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

QUERIES = [
    {
        "question": "Mất bao lâu để tôi nhận được tiền hoàn vào ví ShopeePay nếu hủy đơn?",
        "filter": {"customer_role": "buyer", "category": "payment_and_return"},
    },
    {
        "question": "Phí thanh toán cố định hiện tại trên mỗi đơn hàng thành công là bao nhiêu phần trăm?",
        "filter": {"customer_role": "seller"},
    },
    {
        "question": "Làm thế nào để áp dụng mã miễn phí vận chuyển Extra?",
        "filter": {"customer_role": "buyer", "category": "shipping_and_privacy"},
    },
    {
        "question": "Nếu tôi phát hiện shop gửi hàng fake thì Shopee có đền bù không?",
        "filter": {"category": "general_rules"},
    },
    {
        "question": "Shopee Xu của tôi sẽ hết hạn vào ngày nào?",
        "filter": {"customer_role": "both", "category": "general_rules"},
    },
]


def select_embedder():
    """Select the same embedding backend convention used by main.py."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as exc:
            print(f"Local embedder không sẵn sàng ({exc}); tạm dùng mock.")
            return _mock_embed
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception as exc:
            print(f"OpenAI embedder không sẵn sàng ({exc}); tạm dùng mock.")
            return _mock_embed
    return _mock_embed


def preview(text: str, limit: int = 180) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def normalize_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)
    stopwords = {
        "bao",
        "cua",
        "của",
        "de",
        "để",
        "duoc",
        "được",
        "hien",
        "hiện",
        "la",
        "là",
        "lam",
        "làm",
        "neu",
        "nếu",
        "thi",
        "thì",
        "toi",
        "tôi",
        "tren",
        "trên",
        "vao",
        "vào",
    }
    return {token for token in tokens if len(token) > 2 and token not in stopwords}


def normalize_text(text: str) -> str:
    return " ".join(text.casefold().split())


def load_source_body(metadata: dict) -> str:
    source = metadata.get("source")
    if not source:
        return ""

    if source not in _BODY_CACHE:
        path = Path(source)
        if not path.exists():
            _BODY_CACHE[source] = ""
        else:
            _, body = parse_front_matter(path.read_text(encoding="utf-8"))
            _BODY_CACHE[source] = body
    return _BODY_CACHE[source]


def expand_answer_from_source(fragment: str, result: dict, question: str) -> str:
    """Recover a complete source line when a fixed-size chunk cuts a sentence."""
    body = load_source_body(result["metadata"])
    if not body:
        return fragment

    lines = [line.strip(" -") for line in body.splitlines() if line.strip()]
    fragment_key = normalize_text(fragment[:60])
    for line in lines:
        if fragment_key and fragment_key in normalize_text(line):
            return line

    query_tokens = normalize_tokens(question)
    fragment_tokens = normalize_tokens(fragment)
    candidates: list[tuple[int, str]] = []
    for line in lines:
        line_tokens = normalize_tokens(line)
        score = len(query_tokens & line_tokens) + len(fragment_tokens & line_tokens)
        if score:
            candidates.append((score, line))

    if not candidates:
        return fragment
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def extractive_answer(question: str, results: list[dict]) -> str:
    """Return a short evidence-based answer without calling an external LLM."""
    query_tokens = normalize_tokens(question)
    candidates: list[tuple[int, str, dict]] = []

    for result in results:
        sentences = re.split(r"(?<=[.!?])\s+|\n+", result["content"])
        for sentence in sentences:
            sentence = sentence.strip(" -")
            if not sentence:
                continue
            overlap = len(query_tokens & normalize_tokens(sentence))
            if overlap:
                candidates.append((overlap, sentence, result))

    if not candidates:
        return "Không tìm thấy câu trả lời trực tiếp trong top-3 chunk."

    candidates.sort(key=lambda item: item[0], reverse=True)
    best_fragment = candidates[0][1]
    best_result = candidates[0][2]
    best_sentence = expand_answer_from_source(best_fragment, best_result, question)
    best_meta = best_result["metadata"]
    doc_id = best_meta.get("doc_id", "unknown")
    chunk_index = best_meta.get("chunk_index", "?")
    return f"{best_sentence} (nguồn: {doc_id}::chunk_{chunk_index})"


def main() -> int:
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        print(f"Không tìm thấy thư mục dữ liệu: {DATA_DIR}")
        return 1

    # Strategy của Người A: chỉ dòng chọn chunker này khác với các thành viên khác.
    chunker = FixedSizeChunker(chunk_size=200, overlap=50)

    embedder = select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    store = build_knowledge_base(DATA_DIR, embedder, chunker=chunker)

    print("=== Benchmark Chunking Strategy ===")
    print("Người A / Baseline: FixedSizeChunker(chunk_size=200, overlap=50)")
    print(f"Data dir: {DATA_DIR}")
    print(f"Embedding backend: {backend}")
    print(f"Số chunk đã nạp: {store.get_collection_size()}")

    for index, item in enumerate(QUERIES, start=1):
        question = item["question"]
        metadata_filter = item.get("filter")
        results = store.search_with_filter(question, top_k=TOP_K, metadata_filter=metadata_filter)

        print(f"\n--- Query {index} ---")
        print(f"Q: {question}")
        print(f"Filter: {metadata_filter or '{}'}")
        print("Top-3:")
        for rank, result in enumerate(results, start=1):
            metadata = result["metadata"]
            doc_id = metadata.get("doc_id", "unknown")
            chunk_index = metadata.get("chunk_index", "?")
            print(
                f"{rank}. score={result['score']:.4f} "
                f"doc_id={doc_id} chunk={chunk_index} "
                f"preview={preview(result['content'])}"
            )

        print(f"Agent answer: {extractive_answer(question, results)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
