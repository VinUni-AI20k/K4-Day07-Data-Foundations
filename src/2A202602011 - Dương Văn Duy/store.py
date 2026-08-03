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
            import chromadb  # noqa: F401

            # TODO: initialize chromadb client + collection
            client_factory = getattr(chromadb, "EphemeralClient", chromadb.Client)
            client = client_factory()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # TODO: build a normalized stored record for one document
        metadata = {
            str(key): value if isinstance(value, (str, int, float, bool)) else str(value)
            for key, value in dict(doc.metadata).items()
            if value is not None
        }
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # TODO: run in-memory similarity search over provided records
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        # TODO: embed each doc and add to store
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return
        if self._use_chroma:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                metadatas=[record["metadata"] for record in records],
                embeddings=[record["embedding"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        # TODO: embed query, compute similarities, return top_k
        if self._use_chroma:
            stored = self._collection.get(include=["documents", "metadatas", "embeddings"])
            embeddings = stored.get("embeddings")
            records = [
                {
                    "id": record_id,
                    "content": content,
                    "metadata": metadata or {},
                    "embedding": [float(value) for value in embedding],
                }
                for record_id, content, metadata, embedding in zip(
                    stored.get("ids", []),
                    stored.get("documents", []),
                    stored.get("metadatas", []),
                    embeddings if embeddings is not None else [],
                )
            ]
            return self._search_records(query, records, top_k)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # TODO
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        # TODO: filter by metadata, then search among filtered chunks
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        if self._use_chroma:
            stored = self._collection.get(include=["documents", "metadatas", "embeddings"])
            embeddings = stored.get("embeddings")
            records = [
                {
                    "id": record_id,
                    "content": content,
                    "metadata": metadata or {},
                    "embedding": [float(value) for value in embedding],
                }
                for record_id, content, metadata, embedding in zip(
                    stored.get("ids", []),
                    stored.get("documents", []),
                    stored.get("metadatas", []),
                    embeddings if embeddings is not None else [],
                )
                if all((metadata or {}).get(key) == value for key, value in metadata_filter.items())
            ]
        else:
            records = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        # TODO: remove all stored chunks where metadata['doc_id'] == doc_id
        if self._use_chroma:
            stored = self._collection.get(include=["metadatas"])
            ids_to_delete = [
                record_id
                for record_id, metadata in zip(stored.get("ids", []), stored.get("metadatas", []))
                if (metadata or {}).get("doc_id") == doc_id
            ]
            if ids_to_delete:
                self._collection.delete(ids=ids_to_delete)
            return bool(ids_to_delete)

        original_size = len(self._store)
        self._store = [record for record in self._store if record["metadata"].get("doc_id") != doc_id]
        return len(self._store) < original_size
