from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity
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

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata),
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored = [
            {**record, "score": compute_similarity(query_embedding, record["embedding"])}
            for record in records
        ]
        scored.sort(key=lambda record: record["score"], reverse=True)
        return scored[:top_k]

    def _all_records(self) -> list[dict[str, Any]]:
        if not self._use_chroma:
            return self._store
        raw = self._collection.get(include=["documents", "metadatas", "embeddings"])
        return [
            {"id": doc_id, "content": content, "metadata": metadata, "embedding": embedding}
            for doc_id, content, metadata, embedding in zip(
                raw["ids"], raw["documents"], raw["metadatas"], raw["embeddings"]
            )
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma:
            self._collection.add(
                ids=[doc.id for doc in docs],
                documents=[doc.content for doc in docs],
                embeddings=[self._embedding_fn(doc.content) for doc in docs],
                metadatas=[dict(doc.metadata) for doc in docs],
            )
        else:
            self._store.extend(self._make_record(doc) for doc in docs)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._all_records(), top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        records = self._all_records()
        if metadata_filter:
            records = [
                record
                for record in records
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            matches = self._collection.get(where={"doc_id": doc_id})
            ids = matches.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        before = len(self._store)
        # metadata['doc_id'] covers ingest.py chunks; bare Document ids (no doc_id metadata) fall back to record id.
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id", record["id"]) != doc_id
        ]
        return len(self._store) < before
