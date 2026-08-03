"""
bench.py — Kịch bản chạy Benchmark đánh giá chiến lược truy xuất cá nhân (Lab 07).
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingest import build_knowledge_base
from src.HoangXuanQuan_2A202601868 import (
    FixedSizeChunker,
    SentenceChunker,
    RecursiveChunker,
    KnowledgeBaseAgent,
    _mock_embed,
)


# 1. Chọn chiến lược chunking của cá nhân bạn (ví dụ: RecursiveChunker)
CHUNKER = RecursiveChunker(chunk_size=400)
CHUNKER_NAME = "RecursiveChunker (chunk_size=400)"

# 2. Danh sách 5 câu hỏi Benchmark thống nhất của nhóm (xem REPORT_NHOM.md)
BENCHMARK_QUERIES = [
    {
        "id": 1,
        "query": "Tôi có bao nhiêu ngày để gửi yêu cầu Trả hàng/Hoàn tiền sau khi đơn hàng giao thành công?",
        "filter": None,
    },
    {
        "id": 2,
        "query": "Thanh toán bằng thẻ tín dụng thì bao lâu mới nhận được tiền hoàn?",
        "filter": None,
    },
    {
        "id": 3,
        "query": "Mua cây cảnh hoặc thực phẩm đông lạnh, hàng còn nguyên vẹn nhưng không còn nhu cầu thì trả được không?",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Hệ thống báo trả hàng thành công nhưng Shop chưa nhận được hàng hoàn, Người bán phải phản hồi Shopee trong bao lâu?",
        "filter": {"customer_role": "seller"},
    },
    {
        "id": 5,
        "query": "Hình thức trả hàng nào người mua phải tự trả phí trước?",
        "filter": None,
    },
]


def run_benchmark():
    print(f"=== BẮT ĐẦU CHẠY BENCHMARK BÀI TẬP CÁ NHÂN ===")
    print(f"Chiến lược Chunking: {CHUNKER_NAME}\n")

    # Nạp dữ liệu vào Vector Store
    store = build_knowledge_base("data/k4_ecommerce", _mock_embed, chunker=CHUNKER)
    agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: f"Agent Answer Preview:\n{prompt[:250]}...")

    total_chunks = store.get_collection_size()
    print(f"Tổng số chunk đã nạp vào Vector Store: {total_chunks}\n")
    print("=" * 60)

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        query = item["query"]
        meta_filter = item["filter"]

        print(f"\n[Câu hỏi #{q_id}] {query}")
        if meta_filter:
            print(f"  📌 Metadata Filter: {meta_filter}")

        if meta_filter:
            results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)
        else:
            results = store.search(query, top_k=3)

        print("  🔍 Top-3 Chunks tìm được:")
        for idx, res in enumerate(results, 1):
            doc_id = res.get("metadata", {}).get("doc_id", "unknown")
            score = res.get("score", 0.0)
            content_snippet = res.get("content", "").replace("\n", " ")[:90]
            print(f"    {idx}. Score: {score:.4f} | Doc: {doc_id} | Snippet: {content_snippet}...")

        ans = agent.answer(query, top_k=3)
        print(f"  🤖 Agent Answer: {ans[:150]}...")
        print("-" * 60)


if __name__ == "__main__":
    run_benchmark()
