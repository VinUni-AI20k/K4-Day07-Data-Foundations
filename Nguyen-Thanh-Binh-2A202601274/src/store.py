from __future__ import annotations

import os
import warnings
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


def _chroma_safe_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Ép metadata về kiểu vô hướng mà ChromaDB chấp nhận (str/int/float/bool).

    `ingest.py` dùng pyyaml nếu có, nên `retrieved_at: 2026-08-02` ra `datetime.date`.
    Chroma từ chối nguyên cả lô khi gặp kiểu không vô hướng — không ép kiểu thì toàn
    bộ tài liệu sẽ không vào được Chroma. Bản gốc vẫn giữ nguyên trong `self._store`
    nên việc lọc/tìm kiếm không bị ảnh hưởng bởi phép ép này.
    """
    safe: dict[str, Any] = {}
    for key, value in metadata.items():
        safe[str(key)] = value if isinstance(value, (str, int, float, bool)) else str(value)
    return safe


def _matches(stored_value: Any, wanted: Any) -> bool:
    """So khớp một cặp metadata.

    Mặc định là so bằng (==) đúng như đặc tả. Thêm 2 nới lỏng có chủ đích:
      - `wanted` là list/tuple/set  -> khớp nếu thuộc tập đó, ví dụ
        {"customer_role": ["seller", "both"]} để không bỏ sót tài liệu dùng chung.
      - so bằng chuỗi khi kiểu khác nhau -> `ingest.py` dùng pyyaml nếu có, nên
        `retrieved_at: 2026-08-02` ra `datetime.date` khi có pyyaml và `str` khi không.
        Nếu chỉ dùng `==` thì lọc theo ngày sẽ âm thầm trả về rỗng tuỳ môi trường.
    """
    if isinstance(wanted, (list, tuple, set)):
        return any(_matches(stored_value, option) for option in wanted)
    if stored_value == wanted:
        return True
    return stored_value is not None and str(stored_value) == str(wanted)


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "").strip()
            if persist_dir:
                client = chromadb.PersistentClient(path=persist_dir)
            else:
                # Ephemeral = chạy hoàn toàn trong RAM: mỗi store mới bắt đầu rỗng,
                # nên get_collection_size() của store vừa tạo luôn = 0 (tất định cho test).
                client = chromadb.EphemeralClient()

            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass  # collection chưa tồn tại -> không có gì để xoá

            self._client = client
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuẩn hoá một Document thành bản ghi lưu trữ (đã nhúng sẵn embedding)."""
        metadata = dict(doc.metadata or {})
        # doc_id là khoá để lọc & xoá theo tài liệu gốc; nếu ingest chưa gắn thì lấy từ id.
        metadata.setdefault("doc_id", doc.id)

        record = {
            "id": doc.id,
            # id nội bộ luôn duy nhất -> thêm cùng một doc.id nhiều lần vẫn đếm đúng.
            "storage_id": f"{doc.id}#{self._next_index}",
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": metadata,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Tìm kiếm tương tự trong bộ nhớ trên đúng tập bản ghi được truyền vào."""
        if not records or top_k is None or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                # Embedding của lab đã được chuẩn hoá L2 -> dot product == cosine similarity.
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        scored.sort(key=lambda result: result["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["storage_id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[_chroma_safe_metadata(record["metadata"]) for record in records],
                )
            except Exception as error:
                # Chroma lỗi (schema metadata, version...) -> quay về in-memory, không mất dữ liệu.
                # Cảnh báo tường minh thay vì im lặng, để người dùng biết store đang chạy chế độ nào.
                warnings.warn(f"ChromaDB add thất bại ({error}); chuyển sang store in-memory.", stacklevel=2)
                self._use_chroma = False
                self._collection = None

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return int(self._collection.count())
            except Exception:
                pass
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                if all(_matches(record["metadata"].get(key), value) for key, value in metadata_filter.items())
            ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        size_before = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        removed = size_before - len(self._store)

        if removed and self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                self._use_chroma = False
                self._collection = None

        return removed > 0
