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

        try:
            import chromadb

            self._client = chromadb.Client()
            # Unique per-instance collection so independent stores never share
            # state, and cosine space so distances map cleanly onto similarity.
            self._collection = self._client.get_or_create_collection(
                name=f"{collection_name}-{id(self)}",
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record (with embedding) for one document."""
        metadata = dict(doc.metadata or {})
        # Guarantee doc_id is queryable via metadata so filtering + delete work
        # even when the caller passed empty metadata.
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "doc_id": doc.id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Rank the provided in-memory records against query by similarity."""
        query_embedding = self._embedding_fn(query)
        scored = [
            {
                "content": rec["content"],
                "score": _dot(query_embedding, rec["embedding"]),
                "metadata": rec["metadata"],
                "doc_id": rec["doc_id"],
            }
            for rec in records
        ]
        scored.sort(key=lambda r: r["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma:
            self._collection.add(
                ids=[r["id"] for r in records],
                documents=[r["content"] for r in records],
                embeddings=[r["embedding"] for r in records],
                metadatas=[r["metadata"] for r in records],
            )
        else:
            self._store.extend(records)

    def _chroma_search(
        self, query: str, top_k: int, where: dict | None
    ) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, top_k),
            where=where or None,
        )
        hits: list[dict[str, Any]] = []
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        for content, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            hits.append(
                {
                    "content": content,
                    # cosine space: distance = 1 - similarity
                    "score": 1.0 - distance,
                    "metadata": metadata,
                    "doc_id": metadata.get("doc_id"),
                }
            )
        return hits[:top_k]

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            return self._chroma_search(query, top_k, where=None)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma:
            return self._chroma_search(query, top_k, where=metadata_filter)

        if metadata_filter:
            records = [
                rec
                for rec in self._store
                if all(rec["metadata"].get(k) == v for k, v in metadata_filter.items())
            ]
        else:
            records = self._store
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            existing = self._collection.get(where={"doc_id": doc_id})
            ids = existing.get("ids") or []
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        before = len(self._store)
        self._store = [rec for rec in self._store if rec["doc_id"] != doc_id]
        return len(self._store) < before
