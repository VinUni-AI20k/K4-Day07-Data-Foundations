from __future__ import annotations

import math
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


def _normalize(vector: list[float]) -> list[float]:
    """Scale a vector to unit length so that a dot product equals cosine similarity."""
    norm = math.sqrt(_dot(vector, vector))
    if norm == 0.0:
        return list(vector)
    return [value / norm for value in vector]


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

            # The in-memory list stays the source of truth; the Chroma collection is a
            # mirror so the same chunks are inspectable from a real vector DB when the
            # optional dependency is installed.
            self._collection = chromadb.Client().get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        # Chunks produced by ingest.py already carry doc_id; plain documents fall back
        # to their own id so delete_document() can find them either way.
        doc_id = str(metadata.get("doc_id") or doc.id)
        metadata["doc_id"] = doc_id

        record = {
            "id": doc.id or f"chunk_{self._next_index}",
            "doc_id": doc_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": _normalize(self._embedding_fn(doc.content)),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = _normalize(self._embedding_fn(query))
        scored = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": record["metadata"],
                # Both vectors are unit length, so the dot product IS the cosine similarity.
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs or []]
        if not records:
            return

        self._store.extend(records)

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[r["id"] for r in records],
                    documents=[r["content"] for r in records],
                    embeddings=[r["embedding"] for r in records],
                    metadatas=[r["metadata"] for r in records],
                )
            except Exception:
                self._use_chroma = False

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
        if not metadata_filter:
            return self._search_records(query, self._store, top_k)

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
        remaining = [record for record in self._store if record["doc_id"] != doc_id]
        if len(remaining) == len(self._store):
            return False

        removed_ids = [record["id"] for record in self._store if record["doc_id"] == doc_id]
        self._store = remaining

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=removed_ids)
            except Exception:
                self._use_chroma = False
        return True
