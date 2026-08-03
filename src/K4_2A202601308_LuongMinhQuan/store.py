from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


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
        self._store: list[dict[str, Any]] = []
        self._next_index = 0

        # Nhóm chọn backend in-memory: mọi method đi qua self._store.
        # Giữ _use_chroma = False (kể cả khi máy có cài chromadb) để không nhánh
        # nào rẽ sang self._collection = None rồi vỡ giữa chừng. ChromaDB là bonus.
        self._use_chroma = False
        self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuẩn hoá một Document thành đúng một record trong store."""
        # Copy metadata: sửa record về sau không được đụng vào dict của người gọi.
        metadata = dict(doc.metadata or {})
        # delete_document() lọc theo metadata['doc_id'], nên record nào cũng phải có.
        # ingest.py đã gắn sẵn doc_id trỏ về FILE GỐC (id chunk là "<doc_id>::chunk_0"),
        # setdefault vì vậy chỉ đỡ cho các Document tạo tay không kèm metadata.
        metadata.setdefault("doc_id", doc.id)
        return {
            # _next_index bảo đảm id duy nhất kể cả khi add trùng doc.id nhiều lần.
            "id": f"{doc.id}#{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Xếp hạng một tập record cho sẵn theo độ tương tự với query."""
        # Nhúng query đúng MỘT lần, không gọi lại trong vòng lặp.
        query_vector = self._embedding_fn(query)
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                "score": _dot(query_vector, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[: max(0, top_k)]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # docs rỗng -> vòng lặp không chạy, hàm return bình thường chứ không lỗi.
        for doc in docs:
            self._store.append(self._make_record(doc))
            self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # LỌC TRƯỚC, XẾP HẠNG SAU. Làm ngược lại (top-k rồi mới bỏ cái lệch metadata)
        # có thể trả về 0 kết quả dù store vẫn còn tài liệu hợp lệ.
        if not metadata_filter:
            candidates = self._store
        else:
            candidates = [
                record
                for record in self._store
                # Chỉ giữ record khớp MỌI cặp key/value được yêu cầu.
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        # Dùng chung _search_records với search() -> metadata_filter=None chắc chắn
        # cho kết quả y hệt search() cùng top_k.
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        remaining = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        removed = len(self._store) - len(remaining)
        self._store = remaining
        return removed > 0
