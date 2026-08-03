"""Demo pipeline chạy trên gói cá nhân K4_2A202601308_LuongMinhQuan.

`main.py` ở thư mục gốc import thẳng `src.chunking` / `src.store` / `src.agent`,
tức gói dùng chung của nhóm — không chạy được chừng nào gói đó còn TODO. File này
là bản demo tương đương nhưng dùng ĐÚNG gói cá nhân, nên không phải sửa file chung.

Chạy từ thư mục gốc của lab:

    python -m src.K4_2A202601308_LuongMinhQuan.main "Chunking là gì?"

Đổi thư mục dữ liệu: LAB_DATA_DIR=data/<thu-muc-cua-nhom>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Chỉ mượn phần parse front matter + gắn metadata của ingest.py (hàm thuần, không
# đụng tới store). `build_knowledge_base` thì KHÔNG dùng được vì nó tự dựng
# EmbeddingStore của gói `src/`, nên store được lắp lại ngay bên dưới.
from ingest import chunk_document, load_documents

from . import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

# Corpus TMĐT của nhóm K4 (thu bằng scripts/fetch_hf_asos_products.py).
DEFAULT_DATA_DIR = "data/k4_asos_products"

# Console Windows mặc định là cp1252, không in được tiếng Việt -> UnicodeEncodeError
# ngay dòng in đầu tiên. Ép stdout/stderr về UTF-8 để demo chạy trọn vẹn.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


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


def build_knowledge_base(data_dir: str | Path, embedding_fn, chunker=None) -> EmbeddingStore:
    """file -> tài liệu đã parse -> chunk (kèm metadata) -> nạp vào EmbeddingStore của gói này."""
    chunker = chunker or FixedSizeChunker()
    chunk_docs = []
    for doc in load_documents(data_dir):
        chunk_docs.extend(chunk_document(doc, chunker))

    store = EmbeddingStore(collection_name="lab7_kb_k4", embedding_fn=embedding_fn)
    store.add_documents(chunk_docs)
    return store


def demo_llm(prompt: str) -> str:
    """LLM giả lập đơn giản để thử RAG thủ công."""
    preview = prompt[:400].replace("\n", " ")
    return f"[DEMO LLM] Generated answer from prompt preview: {preview}..."


def run_manual_demo(question: str | None = None, data_dir: str | None = None) -> int:
    data_dir = data_dir or DEFAULT_DATA_DIR
    query = question or "Tóm tắt thông tin chính từ bộ tài liệu."

    print("=== Demo pipeline nạp dữ liệu (gói K4_2A202601308_LuongMinhQuan) ===")
    print(f"Thư mục dữ liệu: {data_dir}")
    if not Path(data_dir).exists():
        print(f"Không tìm thấy thư mục dữ liệu: {data_dir}")
        print("Thu thập tài liệu vào thư mục này (xem docs/DATA_COLLECTION.md) rồi chạy lại.")
        return 1

    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print(
            "Lưu ý: mock chỉ để chạy thử/unit test và KHÔNG phản ánh chất lượng ngữ nghĩa. "
            "Đặt EMBEDDING_PROVIDER=local để so sánh retrieval có ý nghĩa."
        )

    store = build_knowledge_base(data_dir, embedding_fn=embedder)
    print(f"Đã nạp {store.get_collection_size()} chunk vào EmbeddingStore")

    print("\n=== Tìm kiếm (EmbeddingStore.search) ===")
    print(f"Câu hỏi: {query}")
    for index, result in enumerate(store.search(query, top_k=3), start=1):
        print(f"{index}. score={result['score']:.3f} source={result['metadata'].get('source')}")
        print(f"   {result['content'][:120].replace(chr(10), ' ')}...")

    print("\n=== KnowledgeBaseAgent ===")
    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    print(agent.answer(query, top_k=3))
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or None
    data_dir = os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR)
    return run_manual_demo(question=question, data_dir=data_dir)


if __name__ == "__main__":
    raise SystemExit(main())
