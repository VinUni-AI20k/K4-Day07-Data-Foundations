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
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        # Lab cho phep chon in-memory hoac ChromaDB. O day chon in-memory:
        # deterministic, khong phu thuoc I/O, va moi method deu di qua _store.
        # Giu _use_chroma = False de khong co hai duong code khac nhau.
        self._use_chroma = False
        self._collection = None

    # ------------------------------------------------------------------
    # Helper (viet truoc, 4 method cong khai ben duoi dung lai)
    # ------------------------------------------------------------------
    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Chuan hoa mot Document thanh mot record luu trong store."""
        # Copy metadata: khong sua nham dict cua nguoi goi.
        metadata = dict(doc.metadata or {})
        # doc_id phai luon ton tai -> delete_document() moi hoat dong.
        metadata.setdefault("doc_id", doc.id)

        return {
            # Ghep doc.id voi _next_index de id record khong bao gio trung.
            "id": f"{doc.id}#{self._next_index}",
            "doc_id": metadata["doc_id"],
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Xep hang mot tap record theo do tuong dong voi query."""
        if not records or top_k <= 0:
            return []

        # Embed query MOT lan, khong goi lai trong vong lap.
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
        return scored[:top_k]

    # ------------------------------------------------------------------
    # API cong khai
    # ------------------------------------------------------------------
    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return
        for doc in docs:
            record = self._make_record(doc)
            self._next_index += 1
            self._store.append(record)

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
        # Khong co filter -> hanh vi phai TRUNG KHOP voi search().
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

        # FILTER TRUOC, RANK SAU. Lam nguoc lai (lay top-k roi loai) co the
        # tra ve 0 ket qua du store van con tai lieu hop le.
        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        remaining = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        removed = len(self._store) - len(remaining)
        self._store = remaining
        return removed > 0
