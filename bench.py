from __future__ import annotations

import os
from pathlib import Path

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import VoyageAIEmbedder, _mock_embed


def demo_llm(prompt: str) -> str:
    """LLM giả lập tóm tắt nội dung trả lời từ ngữ cảnh RAG."""
    preview = prompt[:300].replace("\n", " ")
    return f"[AGENT ANSWER] Trích xuất từ ngữ cảnh: {preview}..."


def main() -> None:
    # 1. Chọn chiến lược chunking riêng của bạn (RecursiveChunker chunk_size=400)
    chunker = RecursiveChunker(chunk_size=400)
    strategy_name = "RecursiveChunker (chunk_size=400)"

    data_dir = "data/k4_shopee" if Path("data/k4_shopee").exists() else "data/k4_ecommerce"

    # 2. Chọn embedder (Voyage AI hoặc Mock Embedder)
    provider = os.getenv("EMBEDDING_PROVIDER", "voyage").strip().lower()
    if provider == "voyage":
        try:
            embedder = VoyageAIEmbedder()
        except Exception:
            embedder = _mock_embed
    else:
        embedder = _mock_embed

    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)

    print("==================================================")
    print("  RAG BENCHMARK EXECUTION (CP5 - bench.py)")
    print("==================================================")
    print(f"Chiến lược Chunking : {strategy_name}")
    print(f"Thư mục dữ liệu     : {data_dir}")
    print(f"Backend Nhúng       : {backend}")

    # Nạp dữ liệu qua ingest.build_knowledge_base
    store = build_knowledge_base(data_dir, embedding_fn=embedder, chunker=chunker)
    total_chunks = store.get_collection_size()
    print(f"Số lượng chunk đã nạp: {total_chunks}")
    print("==================================================\n")

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    # 3. 5 câu hỏi benchmark đã chốt của nhóm
    benchmark_queries = [
        {
            "id": 1,
            "query": "Thời hạn gửi yêu cầu Trả hàng Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng?",
            "filter": None,
            "note": "Thời hạn Trả hàng/Hoàn tiền quy định",
        },
        {
            "id": 2,
            "query": "Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu?",
            "filter": {"customer_role": "seller"},
            "note": "Bắt buộc lọc metadata customer_role='seller'",
        },
        {
            "id": 3,
            "query": "Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển?",
            "filter": None,
            "note": "Quy định đồng kiểm hàng hóa",
        },
        {
            "id": 4,
            "query": "Tính năng Shopee Đảm Bảo bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu?",
            "filter": None,
            "note": "Cơ chế Shopee Đảm Bảo",
        },
        {
            "id": 5,
            "query": "Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì?",
            "filter": None,
            "note": "Quy trình đóng gói hàng hoàn trả",
        },
    ]

    for item in benchmark_queries:
        q_id = item["id"]
        q_text = item["query"]
        q_filter = item["filter"]

        print(f"--- [QUERY {q_id}] {q_text} ---")
        if q_filter:
            print(f"Metadata Filter: {q_filter}")
            results = store.search_with_filter(q_text, top_k=3, metadata_filter=q_filter)
        else:
            results = store.search(q_text, top_k=3)

        print("Top-3 Chunks tìm được:")
        for idx, res in enumerate(results, start=1):
            doc_id = res["metadata"].get("doc_id", "N/A")
            score = res["score"]
            preview = res["content"][:120].replace("\n", " ")
            print(f"  {idx}. score={score:.3f} | doc_id={doc_id} | preview={preview}...")

        answer = agent.answer(q_text, top_k=3)
        print(f"Agent Answer: {answer[:180]}...\n")


if __name__ == "__main__":
    main()
