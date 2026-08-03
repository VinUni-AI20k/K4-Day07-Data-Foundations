"""evaluate_congnh.py — kịch bản đánh giá cá nhân của Nguyễn Hữu Công (congnh-01732).

Chạy Phần 4 (dự đoán độ tương tự) và Phần 5 (truy xuất benchmark) trên gói
`src/congnh-01732` thay vì gói `src` gốc:

    .venv/bin/python evaluate_congnh.py

Embedder chọn theo EMBEDDING_PROVIDER trong .env (mock | local | openai),
giống logic của main.py. Phần 5 dùng pipeline ingest.py (parse front matter ->
chunk -> gắn metadata) nhưng nạp vào EmbeddingStore TỰ VIẾT.
"""
from __future__ import annotations

import importlib
import os

from dotenv import load_dotenv

import ingest

# Gói cá nhân (tên chứa gạch nối nên phải nạp qua importlib).
pkg = importlib.import_module("src.congnh-01732")

DATA_DIR = os.getenv("LAB_DATA_DIR", "data/k4_ecommerce")

# ---------------------------------------------------------------- Phần 4
# 5 cặp câu — dự đoán đã ghi trong báo cáo TRƯỚC khi chạy kịch bản này.
SIMILARITY_PAIRS = [
    ("Tôi muốn trả lại sản phẩm vì nó bị lỗi.",
     "Sản phẩm này bị hỏng, tôi muốn hoàn hàng."),
    ("Người bán phải cung cấp thông tin sản phẩm chính xác khi đăng bán.",
     "Khi đăng bán, người bán cần mô tả hàng hóa đúng với thực tế."),
    ("Tôi muốn đổi trả đơn hàng đã mua tuần trước.",
     "Đơn hàng của tôi dự kiến khi nào được giao?"),
    ("Chính sách đổi trả yêu cầu gửi kèm bằng chứng khi hàng bị lỗi.",
     "Hôm nay thời tiết đẹp và trời không mưa."),
    ("Tôi muốn trả lại sản phẩm đã mua hôm qua.",
     "Tôi muốn mua thêm sản phẩm này cho bạn bè."),
]

# --------------------------------------------------------------- Phần 5
# 5 câu hỏi benchmark (DỰ THẢO — cần thống nhất với nhóm trong REPORT_NHOM.md).
BENCHMARK_QUERIES = [
    {"query": "Người mua cần làm gì để yêu cầu đổi trả sản phẩm đã mua?", "filter": None},
    {"query": "Yêu cầu đổi trả cần kèm theo gì khi hàng bị lỗi?", "filter": None},
    {"query": "Người bán phải cung cấp những thông tin gì khi đăng bán sản phẩm?", "filter": None},
    {"query": "Những sản phẩm nào không được phép đăng bán?", "filter": None},
    {"query": "Quy định đăng bán áp dụng cho người bán là gì?",
     "filter": {"customer_role": "seller"}},
]


def select_embedder():
    """Chọn backend nhúng theo EMBEDDING_PROVIDER trong .env (như main.py)."""
    provider = os.getenv(pkg.EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "openai":
        return pkg.OpenAIEmbedder(
            model_name=os.getenv("OPENAI_EMBEDDING_MODEL", pkg.OPENAI_EMBEDDING_MODEL)
        )
    if provider == "local":
        return pkg.LocalEmbedder(
            model_name=os.getenv("LOCAL_EMBEDDING_MODEL", pkg.LOCAL_EMBEDDING_MODEL)
        )
    return pkg._mock_embed


def run_similarity(embedder) -> None:
    print("=== Phần 4: compute_similarity trên 5 cặp câu ===")
    for index, (sent_a, sent_b) in enumerate(SIMILARITY_PAIRS, start=1):
        score = pkg.compute_similarity(embedder(sent_a), embedder(sent_b))
        print(f"Cặp {index}: score={score:.4f}")
        print(f"   A: {sent_a}")
        print(f"   B: {sent_b}")


def extractive_llm(prompt: str) -> str:
    """LLM stub trích xuất: trả lại nội dung [Đoạn 1] (demo khi chưa có LLM thật)."""
    marker = "[Đoạn 1] "
    if marker in prompt:
        return prompt.split(marker, 1)[1].split("\n\n", 1)[0].strip()
    return "(Không truy xuất được ngữ cảnh.)"


def run_benchmark(embedder) -> None:
    print("\n=== Phần 5: 5 câu hỏi benchmark trên store tự viết ===")
    docs = ingest.load_documents(DATA_DIR)
    chunker = pkg.FixedSizeChunker(chunk_size=500, overlap=50)  # baseline
    chunk_docs = [c for d in docs for c in ingest.chunk_document(d, chunker)]
    store = pkg.EmbeddingStore(collection_name="lab7_kb_congnh", embedding_fn=embedder)
    store.add_documents(chunk_docs)
    print(f"Nạp {store.get_collection_size()} chunk từ {len(docs)} tài liệu "
          f"({DATA_DIR}); backend store: "
          f"{'ChromaDB' if store._use_chroma else 'in-memory'}")

    agent = pkg.KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)
    for index, item in enumerate(BENCHMARK_QUERIES, start=1):
        query, metadata_filter = item["query"], item["filter"]
        print(f"\n--- Câu {index}: {query}")
        if metadata_filter:
            print(f"    metadata_filter = {metadata_filter}")
            results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=3)
        for rank, r in enumerate(results, start=1):
            preview = r["content"].replace("\n", " ")[:120]
            print(f"  top-{rank} score={r['score']:.4f} "
                  f"doc={r['metadata'].get('doc_id')} role={r['metadata'].get('customer_role')}")
            print(f"    {preview}...")
        print(f"  Trả lời (agent, llm stub trích xuất): {agent.answer(query)[:200]}")


def main() -> int:
    # override=True: .env là nguồn cấu hình chuẩn cho lab này (theo yêu cầu đề bài),
    # cần ghi đè OPENAI_API_KEY/EMBEDDING_PROVIDER có thể tồn tại sẵn trong shell.
    load_dotenv(override=True)
    embedder = select_embedder()
    print(f"Backend nhúng: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    run_similarity(embedder)
    run_benchmark(embedder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
