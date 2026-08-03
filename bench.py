from __future__ import annotations

from typing import Callable

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import LocalEmbedder, _mock_embed

DATA_DIR = "data/k4_shopee"
CHUNKER = RecursiveChunker(chunk_size=450)
TOP_K = 3

BENCHMARK_QUERIES = [
    {
        "name": "Trả hàng/Hoàn tiền thời hạn",
        "query": "Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng?",
        "gold_answer": "Người mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trong vòng 7 ngày (hoặc 15 ngày đối với sản phẩm thuộc Shopee Mall) kể từ khi đơn hàng được cập nhật trạng thái 'Giao hàng thành công'.",
        "metadata_filter": None,
        "markers": ["7 ngày", "15 ngày", "Shopee Mall", "Giao hàng thành công"],
    },
    {
        "name": "Shopee Mall hàng chính hãng và bồi thường",
        "query": "Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu?",
        "gold_answer": "Người bán Shopee Mall cam kết 100% hàng chính hãng. Nếu phát hiện bán hàng giả/hàng nhái, Shopee Mall có quyền phạt và yêu cầu hoàn lại 200% giá trị sản phẩm cho Người mua từ chi phí của Người bán.",
        "metadata_filter": {"customer_role": "seller"},
        "markers": ["100% hàng chính hãng", "200%", "hàng giả", "hàng nhái"],
    },
    {
        "name": "Đồng kiểm khi nhận hàng",
        "query": "Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển?",
        "gold_answer": "Người mua được phép đồng kiểm (mở hộp kiểm tra số lượng và ngoại quan sản phẩm, không dùng thử, không làm rách tem niêm phong) trước sự chứng kiến của nhân viên giao hàng khi nhận đơn.",
        "metadata_filter": None,
        "markers": ["đồng kiểm", "kiểm tra số lượng", "ngoại quan", "không dùng thử", "tem niêm phong"],
    },
    {
        "name": "Shopee Đảm Bảo bảo vệ người mua",
        "query": "Tính năng 'Shopee Đảm Bảo' bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu?",
        "gold_answer": "Shopee Đảm Bảo giữ tiền thanh toán của Người mua cho đến khi Người mua xác nhận đã nhận hàng thỏa đáng hoặc hết thời hạn Trả hàng/Hoàn tiền (7-15 ngày), giúp ngăn ngừa rủi ro gian lận.",
        "metadata_filter": None,
        "markers": ["Shopee Đảm Bảo", "giữ tiền", "7-15 ngày", "xác nhận đã nhận hàng"],
    },
    {
        "name": "Đóng gói đơn hàng hoàn trả",
        "query": "Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì?",
        "gold_answer": "Hàng hoàn trả phải được đóng gói kỹ bằng thùng carton/túi niêm phong nguyên vẹn, dán Mã trả hàng/Phiếu giao hoàn trả bên ngoài vỏ hộp và kèm đầy đủ phụ kiện, quà tặng đi kèm ban đầu.",
        "metadata_filter": None,
        "markers": ["đóng gói kỹ", "thùng carton", "túi niêm phong", "Mã trả hàng", "Phiếu giao hoàn trả"],
    },
]


def get_embedder() -> Callable[[str], list[float]]:
    try:
        embedder = LocalEmbedder()
        print(f"Using local embedder: {embedder.model_name}")
        return embedder
    except Exception:
        print("Local embedder unavailable; falling back to mock embedder.")
        return _mock_embed


def _find_markers(text: str, markers: list[str]) -> list[str]:
    normalized = text.lower()
    return [marker for marker in markers if marker.lower() in normalized]


def _print_result(result: dict[str, object], index: int, markers: list[str]) -> bool:
    metadata = result.get("metadata", {})
    preview = result.get("content", "").replace("\n", " ")[:200].strip()
    found = _find_markers(result.get("content", ""), markers)
    print(f"  {index}. score={result['score']:.4f} doc_id={metadata.get('doc_id')} source={metadata.get('source')}")
    print(f"     preview={preview}")
    if found:
        print(f"     matched markers={found}")
    return bool(found)


def run_benchmark() -> int:
    embedder = get_embedder()
    embedder_name = getattr(embedder, "_backend_name", "mock embedder")

    print("=== bench.py: Strategy benchmark ===")
    print(f"Data dir: {DATA_DIR}")
    print(f"Chunker: {CHUNKER.__class__.__name__}(chunk_size={CHUNKER.chunk_size})")
    print(f"Embedding backend: {embedder_name}")

    store = build_knowledge_base(DATA_DIR, embedder, chunker=CHUNKER)
    print(f"Loaded chunks: {store.get_collection_size()}")
    print()

    for idx, item in enumerate(BENCHMARK_QUERIES, start=1):
        print(f"Query {idx}: {item['name']}")
        print(f"  Query text: {item['query']}")
        print(f"  Gold answer: {item['gold_answer']}")
        if item["metadata_filter"]:
            print(f"  Metadata filter: {item['metadata_filter']}")
        else:
            print("  Metadata filter: None")

        for mode in ["no_filter", "with_filter"]:
            if mode == "with_filter" and not item["metadata_filter"]:
                continue
            if mode == "with_filter":
                print("  Run with metadata filter:")
                results = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=item["metadata_filter"])
            else:
                print("  Run without metadata filter:")
                results = store.search(item["query"], top_k=TOP_K)

            if not results:
                print("    No results returned.")
                continue

            markers = item["markers"]
            marker_found = False
            for rank, result in enumerate(results, start=1):
                found = _print_result(result, rank, markers)
                marker_found = marker_found or found
            print(f"    Marker in top-{TOP_K}: {'Yes' if marker_found else 'No'}")
            print()

    return 0


if __name__ == "__main__":
    raise SystemExit(run_benchmark())