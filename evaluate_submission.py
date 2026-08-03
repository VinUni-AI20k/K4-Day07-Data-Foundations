from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path

from ingest import build_knowledge_base, load_documents
from src import ChunkingStrategyComparator, FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.custom_chunking import HeadingChunker


class KeywordHashEmbedder:
    """Offline lexical embedding for reproducible Vietnamese benchmark runs."""

    def __init__(self, dim: int = 2048) -> None:
        self.dim = dim
        self._backend_name = "offline keyword-hash benchmark"

    def __call__(self, text: str) -> list[float]:
        tokens = re.findall(r"[\wÀ-ỹ]+", text.lower(), flags=re.UNICODE)
        vector = [0.0] * self.dim
        for token in tokens:
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self.dim
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


BENCHMARKS = [
    {
        "query": "T-Hexa hỗ trợ những phương thức thanh toán nào?",
        "gold_doc": "t-hexa-payment-policy",
        "gold_answer": "Ví T-Hexa, chuyển khoản trực tiếp và COD.",
        "filter": None,
    },
    {
        "query": "Khách hàng phải gửi yêu cầu đổi trả trong bao lâu và sản phẩm cần đáp ứng điều kiện gì?",
        "gold_doc": "t-hexa-returns-policy",
        "gold_answer": "Trong 3 ngày; sản phẩm chưa dùng, chưa giặt, không mùi lạ và đủ phụ kiện.",
        "filter": None,
    },
    {
        "query": "Tổng thời gian thông thường từ khi xác nhận đơn đến khi nhận hàng là bao lâu?",
        "gold_doc": "t-hexa-shipping-policy",
        "gold_answer": "Khoảng 3 đến 9 ngày làm việc.",
        "filter": None,
    },
    {
        "query": "Người bán cần đáp ứng điều kiện gì khi đăng hình ảnh và nội dung thiết kế?",
        "gold_doc": "t-hexa-seller-listing-policy",
        "gold_answer": "Phải có quyền sử dụng và không đăng nội dung vi phạm bản quyền, giả mạo, thù ghét, lừa đảo hoặc trái luật.",
        "filter": {"customer_role": "seller"},
    },
    {
        "query": "T-Hexa thu thập dữ liệu cá nhân nào và sử dụng để làm gì?",
        "gold_doc": "t-hexa-privacy-policy",
        "gold_answer": "Thu thập thông tin liên hệ, giao hàng, đơn hàng, thiết kế và lịch sử hỗ trợ để xử lý giao dịch, hỗ trợ, chống gian lận, cải thiện dịch vụ và tuân thủ pháp luật.",
        "filter": None,
    },
]


def extractive_answer(query: str, results: list[dict]) -> str:
    query_tokens = set(re.findall(r"[\wÀ-ỹ]+", query.lower(), flags=re.UNICODE))
    candidates = []
    for result in results:
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", result["content"]):
            sentence = sentence.strip().lstrip("# ")
            if not sentence:
                continue
            sentence_tokens = set(re.findall(r"[\wÀ-ỹ]+", sentence.lower(), flags=re.UNICODE))
            overlap = len(query_tokens & sentence_tokens)
            candidates.append((overlap, sentence))
    candidates.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
    selected = []
    for overlap, sentence in candidates:
        if overlap <= 0:
            continue
        if sentence not in selected:
            selected.append(sentence)
        if len(selected) == 2:
            break
    return " ".join(selected) if selected else "Không đủ thông tin trong ngữ cảnh truy xuất."


def evaluate_strategy(name: str, chunker) -> dict:
    embedder = KeywordHashEmbedder()
    store = build_knowledge_base("data/k4_ecommerce", embedder, chunker=chunker, collection_name=f"eval_{name}")
    rows = []
    points = 0
    for item in BENCHMARKS:
        if item["filter"]:
            results = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
        else:
            results = store.search(item["query"], top_k=3)
        ids = [result["metadata"].get("doc_id") for result in results]
        rank = ids.index(item["gold_doc"]) + 1 if item["gold_doc"] in ids else None
        score = 2 if rank == 1 else 1 if rank in (2, 3) else 0
        points += score
        rows.append({
            "query": item["query"],
            "gold_doc": item["gold_doc"],
            "rank": rank,
            "points": score,
            "top1_doc": ids[0] if ids else None,
            "top1_score": round(results[0]["score"], 4) if results else None,
            "top1_preview": results[0]["content"][:180].replace("\n", " ") if results else "",
            "filter": item["filter"],
            "agent_answer": extractive_answer(item["query"], results),
        })
    return {"strategy": name, "chunks": store.get_collection_size(), "points": points, "rows": rows}


def main() -> None:
    documents = load_documents("data/k4_ecommerce")
    baseline = {}
    comparator = ChunkingStrategyComparator()
    for document in documents[:3]:
        baseline[document.id] = comparator.compare(document.content, chunk_size=300)

    strategies = [
        evaluate_strategy("HeadingChunker", HeadingChunker(chunk_size=700, overlap=60)),
        evaluate_strategy("RecursiveChunker-350", RecursiveChunker(chunk_size=350)),
        evaluate_strategy("SentenceChunker-3", SentenceChunker(max_sentences_per_chunk=3)),
        evaluate_strategy("FixedSizeChunker-450-75", FixedSizeChunker(chunk_size=450, overlap=75)),
        evaluate_strategy("SentenceChunker-2", SentenceChunker(max_sentences_per_chunk=2)),
    ]
    output = {"document_count": len(documents), "baselines": baseline, "strategies": strategies}
    Path("evaluation_results.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
