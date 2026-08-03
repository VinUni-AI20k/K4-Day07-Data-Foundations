"""
Bài tập 3.1 + 3.4 — Chạy 5 câu hỏi đánh giá trên mã nguồn cá nhân (phần CÁ NHÂN, mục 5).

Gồm 3 phần:
    1. Baseline: ChunkingStrategyComparator().compare() trên các tài liệu của corpus
    2. So sánh 3 chiến lược chunking trên đúng 5 câu hỏi benchmark
    3. Chạy chi tiết top-3 + KnowledgeBaseAgent cho chiến lược đã chọn

LLM: repo không cấu hình API key nên dùng `extractive_stub_llm` — một "LLM" tất định
chỉ TRÍCH câu có độ trùng từ khoá cao nhất trong ngữ cảnh được truy xuất. Nhờ vậy
câu trả lời của agent luôn bám vào chunk (kiểm chứng được grounding), và không bịa.

Chạy:
    EMBEDDING_PROVIDER=local python scripts/retrieval_benchmark.py
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent.parent  # thư mục cá nhân của tôi
REPO_ROOT = BUNDLE_ROOT.parent  # repo chung của nhóm (chứa ingest.py, main.py, data/)
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BUNDLE_ROOT))  # src/ của RIÊNG tôi — ưu tiên cao hơn

from ingest import build_knowledge_base, load_documents  # noqa: E402
from main import _select_embedder  # noqa: E402
from src import (  # noqa: E402
    ChunkingStrategyComparator,
    ClauseChunker,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    SentenceChunker,
)

# Corpus DÙNG CHUNG của nhóm, nằm ở gốc repo — cả 5 thành viên phải chạy cùng bộ dữ liệu
# thì kết quả so sánh giữa các chiến lược mới có ý nghĩa (yêu cầu Giai đoạn 2).
DATA_DIR = os.getenv("LAB_DATA_DIR", str(REPO_ROOT / "data" / "k4_ecommerce"))

# 5 câu hỏi đánh giá + gold answer, trích được từ chính corpus K4.
# Câu 3 là câu BẮT BUỘC của K4: cần metadata_filter customer_role=seller.
BENCHMARK = [
    {
        "id": 1,
        "query": "Đơn vị vận chuyển liên hệ người mua mấy lần để giao hàng, và nếu không liên hệ được thì người mua được yêu cầu giao lại trong thời hạn bao lâu?",
        "gold": "Đơn vị vận chuyển liên hệ 2-3 lần; người mua có thể yêu cầu giao lại trong không quá 5 ngày kể từ lần liên hệ đầu tiên.",
        "gold_doc": "delivery-process",
        "gold_snippet": "không quá 5 ngày kể từ lần liên hệ đầu tiên",
        "filter": None,
    },
    {
        "id": 2,
        "query": "Tôi trả hàng bằng cách tự sắp xếp vận chuyển cho đơn khác tỉnh/thành thì Shopee hoàn lại phí vận chuyển hoàn trả bao nhiêu và bằng hình thức gì?",
        "gold": "Hoàn bằng Shopee Xu trong 3-5 ngày làm việc: 25.000 Xu cùng tỉnh/thành, 40.000 Xu nếu khác tỉnh/thành.",
        "gold_doc": "return-shipping-fee",
        "gold_snippet": "40.000 Shopee Xu nếu khác tỉnh/thành",
        "filter": None,
    },
    {
        "id": 3,
        "query": "Gian hàng cần đáp ứng điều kiện gì để được tham gia chương trình ưu đãi phí vận chuyển của Shopee?",
        "gold": "Chỉ áp dụng cho người bán thuộc Shopee Mall đáp ứng đủ yêu cầu của sàn; phí dịch vụ 6%, tối đa 50.000 VNĐ mỗi sản phẩm.",
        "gold_doc": "shipping-fee-discount-program",
        "gold_snippet": "chỉ áp dụng cho người bán thuộc Shopee Mall",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 4,
        "query": "Người bán có được đăng bán đồ cổ và tác phẩm nghệ thuật trên Shopee không, và nếu vi phạm chính sách sản phẩm cấm thì bị xử lý ra sao?",
        "gold": "Không được. Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép nằm trong nhóm bị cấm; vi phạm bị xóa sản phẩm, khóa tài khoản, tịch thu số dư.",
        "gold_doc": "restricted-products-policy",
        "gold_snippet": "Đồ cổ và tác phẩm nghệ thuật chưa được cấp phép",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 5,
        "query": "Người mua gửi khiếu nại đơn hàng ở đâu trên ứng dụng và Shopee đưa ra quyết định trong bao lâu đối với khiếu nại thông thường?",
        "gold": "Khiếu nại qua mục Đơn Mua; Shopee quyết định trong vòng 7 ngày làm việc với khiếu nại thông thường.",
        "gold_doc": "marketplace-operating-regulation",
        "gold_snippet": "7 ngày làm việc đối với khiếu nại thông thường",
        # Tài liệu gold có customer_role=both -> lọc cứng "buyer" sẽ MẤT gold doc.
        "filter": {"customer_role": ["buyer", "both"]},
    },
]

STRATEGIES = {
    "fixed_size (500/50)": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "by_sentences (3 câu)": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive (400)": lambda: RecursiveChunker(chunk_size=400),
    "clause (1 câu)": lambda: ClauseChunker(max_sentences_per_clause=1),
}
CHOSEN = "clause (1 câu)"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[^\w\sÀ-ỹ]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(text: str) -> set[str]:
    return {token for token in _normalize(text).split() if len(token) > 2}


def extractive_stub_llm(prompt: str) -> str:
    """LLM giả lập tất định: trích câu bám sát câu hỏi nhất TRONG ngữ cảnh, có ghi [n].

    Điểm của một câu = (số từ trùng với câu hỏi) x (trọng số theo THỨ HẠNG truy xuất),
    với trọng số 1/rank cho đoạn [1], [2], [3].

    Vì sao phải nhân trọng số thứ hạng: nếu chỉ đếm từ trùng thì đây là keyword
    matching thuần, và nó sẽ **phủ định luôn công dụng của embedding**. Ví dụ thật
    trong benchmark — câu hỏi "Người bán có trách nhiệm gì khi người mua gửi yêu cầu
    đổi trả?" nhắc tới người mua như BỐI CẢNH nhưng hỏi nghĩa vụ NGƯỜI BÁN: câu sai
    (về người mua) trùng 7 từ, câu đúng (về người bán) chỉ trùng 4 từ. Retriever ngữ
    nghĩa đã xếp đúng câu về người bán ở #1 — bỏ qua thứ hạng đó là vứt đi đúng
    thông tin mà cả hệ RAG sinh ra để có.
    """
    question = prompt.split("CÂU HỎI:")[-1].split("TRẢ LỜI:")[0].strip()
    context = prompt.split("NGỮ CẢNH:")[-1].split("CÂU HỎI:")[0].strip()
    if not context or context.startswith("(Không tìm thấy"):
        return "Không tìm thấy thông tin trong tài liệu."

    question_tokens = _tokens(question)
    best_sentence, best_block, best_score, best_overlap = "", 0, -1.0, 0
    block_index = 0
    for line in context.splitlines():
        marker = re.match(r"^\[(\d+)\]", line.strip())
        if marker:
            block_index = int(marker.group(1))
            continue
        rank_weight = 1.0 / block_index if block_index else 1.0
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            overlap = len(question_tokens & _tokens(sentence))
            score = overlap * rank_weight
            if score > best_score:
                best_sentence, best_block, best_score, best_overlap = sentence, block_index, score, overlap
    if best_overlap <= 0:
        return "Ngữ cảnh truy xuất được không chứa thông tin trả lời câu hỏi này."
    return f"{best_sentence} [{best_block}]"


def is_gold_chunk(result: dict, item: dict) -> bool:
    """Chunk có THỰC SỰ chứa câu trả lời chuẩn hay không (chỉ số nghiêm, đúng rubric)."""
    return _normalize(item["gold_snippet"]) in _normalize(result.get("content", ""))


def hit_rank(results: list[dict], item: dict, level: str = "chunk") -> int:
    """Thứ hạng (1-based) đầu tiên trúng đích; 0 nếu trượt.

    level="chunk": chunk phải chứa nguyên văn gold answer  -> dùng để chấm điểm.
    level="doc"  : chỉ cần đúng tài liệu nguồn             -> chỉ số nới lỏng để đối chiếu.
    """
    for rank, result in enumerate(results, start=1):
        if level == "chunk":
            if is_gold_chunk(result, item):
                return rank
        elif result["metadata"].get("doc_id") == item["gold_doc"]:
            return rank
    return 0


def section_baseline(embedder) -> None:
    print("=" * 90)
    print("PHẦN 1 — BASELINE: ChunkingStrategyComparator().compare()")
    print("=" * 90)
    comparator = ChunkingStrategyComparator()
    for doc in load_documents(DATA_DIR):
        print(f"\nTài liệu: {doc.id}  ({len(doc.content)} ký tự)")
        print(f"{'Chiến lược':<16}{'Số chunk':<12}{'Độ dài TB':<12}")
        for name, stats in comparator.compare(doc.content, chunk_size=400).items():
            print(f"{name:<16}{stats['count']:<12}{stats['avg_length']:<12}")


def section_strategy_matrix(embedder) -> dict:
    print("\n" + "=" * 90)
    print("PHẦN 2 — SO SÁNH 3 CHIẾN LƯỢC TRÊN 5 CÂU HỎI (thứ hạng của tài liệu chứa gold answer)")
    print("=" * 90)
    stores = {}
    print(f"{'Chiến lược':<24}{'#chunk':<9}" + "".join(f"Q{item['id']:<6}" for item in BENCHMARK) + "Top-3 hit")
    print("-" * 90)
    for name, factory in STRATEGIES.items():
        store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=factory(), collection_name=name)
        stores[name] = store
        ranks, hits = [], 0
        for item in BENCHMARK:
            results = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
            rank = hit_rank(results, item)
            ranks.append(rank)
            hits += 1 if rank else 0
        cells = "".join(f"{('#' + str(r)) if r else 'trượt':<7}" for r in ranks)
        print(f"{name:<24}{store.get_collection_size():<9}{cells}{hits}/5")
    return stores


def section_detail(store, embedder) -> None:
    print("\n" + "=" * 90)
    print(f"PHẦN 3 — CHI TIẾT TOP-3 + AGENT (chiến lược đã chọn: {CHOSEN})")
    print("=" * 90)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_stub_llm)
    total = 0
    for item in BENCHMARK:
        results = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
        rank = hit_rank(results, item)
        total += 1 if rank else 0
        print(f"\n--- Q{item['id']}: {item['query']}")
        print(f"    Gold: {item['gold']}  (tài liệu: {item['gold_doc']})")
        print(f"    metadata_filter: {item['filter']}")
        for position, result in enumerate(results, start=1):
            flag = "<== CHUNK CHỨA GOLD" if is_gold_chunk(result, item) else ""
            preview = result["content"].replace("\n", " ")[:110]
            print(f"    top{position} score={result['score']:.4f} doc={result['metadata'].get('doc_id')} {flag}")
            print(f"          {preview}...")
        print(f"    Thứ hạng chunk chứa gold: {'#' + str(rank) if rank else 'TRƯỢT khỏi top-3'}")
        print(f"    Agent: {agent.answer(item['query'], top_k=3, metadata_filter=item['filter'])}")

    print(f"\n>>> Tổng: {total}/5 câu có chunk chứa nguyên văn gold answer trong top-3")

    print("\n--- Đối chứng câu 3: có vs không có metadata filter ---")
    item = BENCHMARK[2]
    for label, metadata_filter in (("CÓ filter", item["filter"]), ("KHÔNG filter", None)):
        results = store.search_with_filter(item["query"], top_k=3, metadata_filter=metadata_filter)
        docs = [result["metadata"].get("doc_id") for result in results]
        print(f"    {label:<14} -> top-3 doc: {docs} | hạng chunk gold: {hit_rank(results, item) or 'trượt'}")


def main() -> int:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Thư mục dữ liệu: {DATA_DIR}")
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print("CẢNH BÁO: mock embedder cho điểm gần như ngẫu nhiên — chỉ dùng để chạy thử.\n")

    section_baseline(embedder)
    stores = section_strategy_matrix(embedder)
    section_detail(stores[CHOSEN], embedder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
