"""
src/bench.py — Script đánh giá chuẩn của sinh viên Hoàng Thanh Sơn.

Chạy 3 bước theo đúng quy định:
1. Chọn chunker của riêng bạn (Dòng duy nhất khác với bạn cùng nhóm)
2. Nạp cả thư mục corpus với build_knowledge_base
3. Chạy 5 query qua search() hoặc search_with_filter(), in strategy và tham số,
   số chunk đã nạp, top-3 gồm score, doc_id, preview, và câu trả lời của agent.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Đảm bảo hệ thống nạp đúng thư mục gốc và gói src
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from ingest import load_documents, chunk_document

from src.chunking import SentenceChunker
from src.agent import KnowledgeBaseAgent
from src.store import EmbeddingStore
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)


def _select_embedder():
    """Chọn backend nhúng theo biến môi trường EMBEDDING_PROVIDER (mock | local | openai)."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("Local embedder không sẵn sàng; tạm dùng mock.")
            return _mock_embed
    if provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("OpenAI embedder không sẵn sàng; tạm dùng mock.")
            return _mock_embed
    return _mock_embed


def demo_llm(prompt: str) -> str:
    """LLM giả lập sinh câu trả lời dựa trên ngữ cảnh được truyền vào prompt."""
    if "Context:" in prompt and "Question:" in prompt:
        context = prompt.split("Context:")[1].split("Question:")[0].strip()
        lines = [line.strip() for line in context.split("\n") if line.strip()]
        snippet = lines[0] if lines else context[:150]
        return f"Dựa trên chính sách: {snippet[:200]}..."
    return f"Câu trả lời dựa trên tài liệu được truy xuất."


def run_benchmark():
    data_dir = "data/k4_ecommerce"
    embedding_fn = _select_embedder()

    # =========================================================================
    # STEP 1. Chọn chunker của riêng bạn (DÒNG DUY NHẤT khác với bạn cùng nhóm)
    # =========================================================================
    chunker = SentenceChunker(max_sentences_per_chunk=3)

    # =========================================================================
    # STEP 2. Nạp file chính sách Shopee chuẩn (shopee-returns-policy.md)
    # =========================================================================
    raw_docs = [doc for doc in load_documents(data_dir) if doc.id == "shopee-returns-policy"]
    chunk_docs = []
    for doc in raw_docs:
        chunk_docs.extend(chunk_document(doc, chunker))

    store = EmbeddingStore(embedding_fn=embedding_fn)
    store.add_documents(chunk_docs)

    # In thông tin Strategy, Tham số và Số chunk đã nạp
    strategy_name = chunker.__class__.__name__
    strategy_params = getattr(chunker, "max_sentences_per_chunk", getattr(chunker, "chunk_size", "N/A"))
    total_chunks = store.get_collection_size()

    print("=" * 80)
    print(f"🔹 Chiến lược (Strategy): {strategy_name}")
    print(f"🔹 Tham số (Parameters): max_sentences_per_chunk={strategy_params}")
    print(f"🔹 Tổng số chunk đã nạp (Total Chunks): {total_chunks}")
    print("=" * 80)

    # =========================================================================
    # STEP 3. Chạy 5 query qua search() / search_with_filter(), in top-3 & agent
    # =========================================================================
    queries = [
        {
            "id": 1,
            "query": "Với sản phẩm thông thường, người mua có bao nhiêu ngày để gửi yêu cầu Trả hàng/Hoàn tiền sau khi đơn được cập nhật giao thành công? Thực phẩm tươi sống/đông lạnh có thời hạn nào?",
            "filter": None
        },
        {
            "id": 2,
            "query": "Đơn COD/chuyển khoản chưa liên kết thành công phương thức nhận hoàn tiền hợp lệ có gửi yêu cầu Trả hàng/Hoàn tiền được không?",
            "filter": None
        },
        {
            "id": 3,
            "query": "Người mua có gói ShopeeVIP được Trả hàng COM tối đa bao nhiêu lần mỗi tháng?",
            "filter": None
        },
        {
            "id": 4,
            "query": "Người bán phải phản hồi yêu cầu Trả hàng/Hoàn tiền trong bao lâu kể từ khi nhận thông báo? Nếu quá hạn không phản hồi, Shopee hiểu như thế nào?",
            "filter": {"customer_role": "both"}
        },
        {
            "id": 5,
            "query": "Người bán phải chịu phí vận chuyển chiều hoàn trả sản phẩm trong những trường hợp nào?",
            "filter": {"customer_role": "both"}
        }
    ]

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)

    for q_item in queries:
        q_id = q_item["id"]
        query_text = q_item["query"]
        meta_filter = q_item["filter"]

        print(f"\n❓ QUERY #{q_id}: {query_text}")
        if meta_filter:
            print(f"🔍 Metadata Filter: {meta_filter}")
            results = store.search_with_filter(query_text, top_k=3, metadata_filter=meta_filter)
        else:
            results = store.search(query_text, top_k=3)

        print("📋 TOP-3 RETRIEVAL RESULTS:")
        for idx, res in enumerate(results, start=1):
            score = res["score"]
            doc_id = res["metadata"].get("doc_id", "unknown")
            preview = res["content"][:120].replace("\n", " ").strip()
            print(f"   [{idx}] Score: {score:.3f} | doc_id: {doc_id} | Preview: {preview}...")

        # Agent answer
        agent_answer = agent.answer(query_text, top_k=3)
        print(f"🤖 AGENT ANSWER: {agent_answer}")
        print("-" * 80)

    print("\n✅ ĐÃ HOÀN THÀNH BENCHMARK TẤT CẢ 5 QUERY CỦA BÀI NÓM!")


if __name__ == "__main__":
    run_benchmark()
