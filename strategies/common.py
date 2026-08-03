"""
strategies/common.py — hạ tầng DÙNG CHUNG cho Giai đoạn 2 (cả 3 thành viên xài chung 1 bản).

File này KHÔNG chứa chiến lược của riêng ai. Nó chỉ lo phần lặp lại:

    1. Nạp package cá nhân của từng thành viên (`src/<MSSV>-<Ten>`) qua LAB_SOLUTION_PACKAGE
    2. Chọn backend embedding theo `.env` (mock | local | openai) — giống hệt main.py
    3. Corpus -> parse front matter -> chunk -> gắn metadata -> nạp EmbeddingStore
    4. Giữ 5 câu hỏi benchmark của nhóm (bản máy đọc được của docs/Benchmark_Query.md)

Vì sao không dùng thẳng `ingest.build_knowledge_base()`? Vì nó import `EmbeddingStore`
từ package `src` gốc (chưa ai hoàn thành TODO). Ở đây ta dựng store từ package CÁ NHÂN,
và tiện thể mở thêm hook `decorate` để chiến lược tự làm giàu metadata / sửa text
trước khi embed. Hàm `parse_front_matter` của ingest.py là hàm thuần nên tái sử dụng lại.

Mỗi thành viên chỉ cần viết 1 file `strategies/strategy_*.py` khai báo biến `STRATEGY`.
"""
from __future__ import annotations

import importlib
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingest import parse_front_matter  # noqa: E402  (cần sys.path ở trên)

DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "k4_ecommerce"
TEXT_EXTENSIONS = {".md", ".txt"}
SOLUTION_PACKAGE_ENV = "LAB_SOLUTION_PACKAGE"


# ---------------------------------------------------------------------------
# 5 câu hỏi đánh giá của nhóm (nguồn: docs/Benchmark_Query.md)
# ---------------------------------------------------------------------------
# gold_docs = các doc_id được coi là ĐÚNG cho câu hỏi đó; benchmark.py dùng để tự chấm
# relevance. gold_answer để trống -> nhóm điền sau khi trích nguyên văn từ corpus
# (bắt buộc theo K4_VARIANT.md: gold answer phải nằm trong tập tài liệu đã thu thập).
BENCHMARK_QUERIES: list[dict[str, Any]] = [
    {
        "id": 1,
        "question": "Tôi nhận hàng bị vỡ thì được hoàn tiền không?",
        "gold_docs": ["shopee-return-refund-policy"],
        "metadata_filter": None,
        "gold_answer": "",
        "note": "Dễ — kiểm tra baseline.",
    },
    {
        "id": 2,
        "question": "Thời hạn gửi yêu cầu trả hàng là bao lâu?",
        "gold_docs": ["shopee-return-refund-policy", "shopee-return-refund-request-guide"],
        "metadata_filter": None,
        "gold_answer": "",
        "note": "Câu trả lời có con số -> dễ chấm đúng/sai.",
    },
    {
        "id": 3,
        "question": "Người bán bị cấm đăng bán những mặt hàng nào?",
        "gold_docs": ["shopee-seller-listing-rules"],
        "metadata_filter": {"customer_role": "seller"},
        "gold_answer": "",
        "note": "Câu BẮT BUỘC dùng metadata filter theo quy tắc K4.",
    },
    {
        "id": 4,
        "question": "Shopee hỗ trợ những phương thức thanh toán nào?",
        "gold_docs": ["shopee-payment-methods"],
        "metadata_filter": None,
        "gold_answer": "",
        "note": "Kiểm tra có kéo nhầm tài liệu giao hàng không.",
    },
    {
        "id": 5,
        "question": "Đơn hàng đang giao bị thất lạc thì xử lý ra sao?",
        "gold_docs": ["shopee-shipping-policy", "shopee-delivery-process"],
        "metadata_filter": None,
        "gold_answer": "",
        "note": "Câu khó — gold trải trên 2 tài liệu, phân biệt rõ 3 chiến lược.",
    },
]


# ---------------------------------------------------------------------------
# Hợp đồng chiến lược
# ---------------------------------------------------------------------------
@dataclass
class Strategy:
    """Một chiến lược truy xuất của một thành viên.

    Bắt buộc:
        name           tên ngắn, hiện trong báo cáo
        build_chunker  nhận package cá nhân -> object có `.chunk(text) -> list[str]`
                       (dùng hàm thay vì instance, vì chunker có thể lấy từ package
                       cá nhân mà package chỉ biết được lúc chạy)

    Tuỳ chọn:
        description    1-2 câu lý do chọn, in kèm khi benchmark
        decorate       hook chạy trên TỪNG chunk:
                           (chunk_text, doc_metadata, chunk_index) -> (text_mới, metadata_thêm)
                       dùng để làm giàu metadata (section_no...) hoặc chèn ngữ cảnh vào
                       text trước khi embed. Mặc định: giữ nguyên.
        top_k          top_k riêng của chiến lược (None -> lấy theo tham số CLI)
    """

    name: str
    build_chunker: Callable[[Any], Any]
    description: str = ""
    decorate: Callable[[str, dict, int], tuple[str, dict]] | None = None
    top_k: int | None = None
    extra: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Nạp package cá nhân + embedder
# ---------------------------------------------------------------------------
def load_solution_package(package_name: str | None = None):
    """Nạp package lời giải của một thành viên (mặc định đọc LAB_SOLUTION_PACKAGE)."""
    name = package_name or os.getenv(SOLUTION_PACKAGE_ENV, "src")
    return importlib.import_module(name)


def select_embedder(package) -> tuple[Callable[[str], list[float]], str]:
    """Chọn backend nhúng theo EMBEDDING_PROVIDER trong .env. Trả (hàm nhúng, tên backend)."""
    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=False)
    except Exception:
        pass

    provider = os.getenv(package.EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    embedder: Any = package._mock_embed

    if provider == "local":
        try:
            embedder = package.LocalEmbedder(
                model_name=os.getenv("LOCAL_EMBEDDING_MODEL", package.LOCAL_EMBEDDING_MODEL)
            )
        except Exception as error:
            print(f"[canh bao] Local embedder khong san sang ({error}); tam dung mock.")
    elif provider == "openai":
        try:
            embedder = package.OpenAIEmbedder(
                model_name=os.getenv("OPENAI_EMBEDDING_MODEL", package.OPENAI_EMBEDDING_MODEL)
            )
        except Exception as error:
            print(f"[canh bao] OpenAI embedder khong san sang ({error}); tam dung mock.")

    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    return embedder, backend


def is_mock_backend(backend_name: str) -> bool:
    return "mock" in backend_name.lower()


# ---------------------------------------------------------------------------
# Corpus -> chunk -> store
# ---------------------------------------------------------------------------
def iter_documents(data_dir: str | Path = DEFAULT_DATA_DIR):
    """Duyệt corpus, trả (doc_id, metadata, body) cho từng file .md/.txt."""
    for path in sorted(Path(data_dir).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = str(metadata.get("doc_id") or path.stem)
        metadata.setdefault("doc_id", doc_id)
        metadata.setdefault("source", path.name)
        yield doc_id, metadata, body


def corpus_summary(data_dir: str | Path = DEFAULT_DATA_DIR) -> list[dict[str, Any]]:
    """Bảng kiểm kê tài liệu — dán thẳng vào REPORT_NHOM mục 1."""
    return [
        {
            "doc_id": doc_id,
            "title": metadata.get("title", ""),
            "customer_role": metadata.get("customer_role", ""),
            "category": metadata.get("category", ""),
            "source_url": metadata.get("source_url", ""),
            "retrieved_at": metadata.get("retrieved_at", ""),
            "document_version": metadata.get("document_version", ""),
            "chars": len(body),
        }
        for doc_id, metadata, body in iter_documents(data_dir)
    ]


def build_chunk_documents(package, strategy: Strategy, data_dir: str | Path = DEFAULT_DATA_DIR) -> list:
    """Corpus -> danh sách chunk-Document (đã gắn doc_id + metadata + hook decorate)."""
    chunker = strategy.build_chunker(package)
    decorate = strategy.decorate
    chunk_docs = []

    for doc_id, doc_metadata, body in iter_documents(data_dir):
        for index, piece in enumerate(chunker.chunk(body)):
            text, extra_metadata = (piece, {}) if decorate is None else decorate(piece, doc_metadata, index)
            if not text or not text.strip():
                continue
            metadata = dict(doc_metadata)
            metadata["doc_id"] = doc_id          # để delete_document()/lọc theo doc_id chạy đúng
            metadata["chunk_index"] = index
            metadata.update(extra_metadata or {})
            chunk_docs.append(
                package.Document(id=f"{doc_id}::chunk_{index}", content=text, metadata=metadata)
            )
    return chunk_docs


def build_kb(
    package,
    strategy: Strategy,
    data_dir: str | Path = DEFAULT_DATA_DIR,
    embedding_fn: Callable[[str], list[float]] | None = None,
    collection_name: str = "lab7_phase2",
) -> tuple[Any, dict[str, Any]]:
    """Dựng EmbeddingStore theo một chiến lược. Trả (store, thống kê chunk)."""
    if embedding_fn is None:
        embedding_fn, _ = select_embedder(package)

    chunk_docs = build_chunk_documents(package, strategy, data_dir)
    store = package.EmbeddingStore(collection_name=collection_name, embedding_fn=embedding_fn)
    store.add_documents(chunk_docs)

    lengths = [len(doc.content) for doc in chunk_docs] or [0]
    stats = {
        "n_docs": len({doc.metadata["doc_id"] for doc in chunk_docs}),
        "n_chunks": len(chunk_docs),
        "avg_length": round(sum(lengths) / len(lengths), 1),
        "min_length": min(lengths),
        "max_length": max(lengths),
    }
    return store, stats
