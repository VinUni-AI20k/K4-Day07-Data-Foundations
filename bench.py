"""Chạy một chiến lược chunking với embedding đa ngôn ngữ cục bộ."""

import argparse
import sys

from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import LocalEmbedder


# Mỗi thành viên chọn đúng một strategy từ terminal.
CHUNKERS = {
    "fixed": lambda: FixedSizeChunker(chunk_size=400, overlap=50),
    "sentence": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "recursive": lambda: RecursiveChunker(chunk_size=400),
}


# Query, gold answer, metadata filter. Giữ nguyên khi so sánh các strategy.
BENCHMARK = [
    (
        "Tôi có bao nhiêu ngày để yêu cầu trả hàng kể từ khi đơn hàng giao thành công?",
        "15 ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công; riêng "
        "thực phẩm tươi sống/đông lạnh chỉ có 24 giờ.",
        None,
    ),
    (
        "Thời gian xử lý bảo hành dự kiến là bao lâu?",
        "Dự kiến từ 20 đến 45 ngày làm việc kể từ lúc Shopee nhận được sản phẩm, "
        "tùy thuộc linh kiện cần thay thế.",
        None,
    ),
    (
        "Đơn hàng nào không hỗ trợ vận chuyển?",
        "Trên 50.000.000 VNĐ tổng giá trị hàng hóa (đã tính giá khuyến mãi nếu "
        "có, không gồm mã giảm giá, Shopee Xu và phí vận chuyển).",
        None,
    ),
    (
        "Lịch sử trò chuyện với chăm sóc khách hàng lưu trữ tối đa bao lâu?",
        "Tối đa 180 ngày.",
        None,
    ),
    (
        "Người bán vi phạm chính sách sẽ bị áp dụng những chế tài nào?",
        "(i) Xóa sản phẩm; (ii) giới hạn quyền tài khoản; (iii) đình chỉ/xóa tài "
        "khoản; (iv) cấn trừ số dư và phong tỏa rút tiền; (v) các chế tài khác "
        "kể cả phạt hành chính, xử lý hình sự hoặc bồi thường thiệt hại.",
        {"customer_role": "seller"},
    ),
]


def demo_llm(prompt):
    """Agent offline: trả preview context thay vì giả lập một đáp án đúng."""
    context = prompt.partition("Context:\n")[2].partition("\nQuestion:")[0]
    return "[Context preview] " + " ".join(context.split())[:300] + "..."


def run_strategy(chunker, embedding_fn):
    # ingest.py lo parse front matter, gắn metadata, chunk và nạp store.
    store = build_knowledge_base(
        "data/k4_ecommerce", embedding_fn, chunker=chunker,
        collection_name=f"k4_{chunker.__class__.__name__.lower()}",
    )
    print("\n" + "=" * 70)
    print(f"Strategy: {chunker.__class__.__name__} {vars(chunker)}")
    print(f"Embedding: {embedding_fn._backend_name}")
    print(f"Số chunk: {store.get_collection_size()}\n")

    for number, (query, gold, metadata_filter) in enumerate(BENCHMARK, 1):
        results = (
            store.search_with_filter(query, 3, metadata_filter)
            if metadata_filter else store.search(query, 3)
        )
        agent = KnowledgeBaseAgent(store, demo_llm)

        print(f"=== Query {number} ===")
        print("Query :", query)
        print("Gold  :", gold)
        print("Filter:", metadata_filter)
        for rank, result in enumerate(results, 1):
            preview = " ".join(result["content"].split())[:160]
            print(
                f"{rank}. score={result['score']:.4f} "
                f"doc_id={result['metadata'].get('doc_id')}\n   {preview}"
            )
        print(
            "Agent :",
            agent.answer(query, top_k=3, metadata_filter=metadata_filter),
            "\n",
        )


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Chạy benchmark với đúng một chunker có sẵn trong src/chunking.py."
    )
    parser.add_argument(
        "strategy",
        choices=CHUNKERS,
        help="Chunker cần chạy: fixed, sentence hoặc recursive",
    )
    args = parser.parse_args()

    # Giữ nguyên model này cho mọi thành viên để chỉ so sánh chunking strategy.
    embedding_fn = LocalEmbedder()
    chunker = CHUNKERS[args.strategy]()
    run_strategy(chunker, embedding_fn)


if __name__ == "__main__":
    main()
