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

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "ip"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        record = {
            # A store ID identifies one insertion, while metadata.doc_id keeps
            # the caller's logical document identity for filtering/deletion.
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": list(self._embedding_fn(doc.content)),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": float(_dot(query_embedding, record["embedding"])),
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
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        if self._use_chroma:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0 or self.get_collection_size() == 0:
            return []
        if not self._use_chroma:
            return self._search_records(query, self._store, top_k)

        query_embedding = self._embedding_fn(query)
        response = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.get_collection_size()),
            include=["documents", "metadatas", "distances"],
        )
        return self._format_chroma_results(response)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)
        if top_k <= 0:
            return []

        if not self._use_chroma:
            records = [
                record
                for record in self._store
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
            return self._search_records(query, records, top_k)

        chroma_filter = self._to_chroma_filter(metadata_filter)
        matching = self._collection.get(where=chroma_filter, include=[])
        matching_count = len(matching.get("ids") or [])
        if matching_count == 0:
            return []
        response = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=min(top_k, matching_count),
            where=chroma_filter,
            include=["documents", "metadatas", "distances"],
        )
        return self._format_chroma_results(response)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            matches = self._collection.get(where={"doc_id": doc_id}, include=[])
            ids = matches.get("ids") or []
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        original_size = len(self._store)
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size

    @staticmethod
    def _format_chroma_results(response: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert Chroma's nested query response to the public result shape."""
        ids = (response.get("ids") or [[]])[0]
        documents = (response.get("documents") or [[]])[0]
        metadatas = (response.get("metadatas") or [[]])[0]
        distances = (response.get("distances") or [[]])[0]
        results = [
            {
                "id": record_id,
                "content": content,
                "metadata": dict(metadata or {}),
                # With the inner-product collection, Chroma distance is 1 - IP.
                "score": float(1.0 - distance),
            }
            for record_id, content, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results

    @staticmethod
    def _to_chroma_filter(metadata_filter: dict[str, Any]) -> dict[str, Any]:
        """Express an all-fields-match filter using Chroma's where syntax."""
        clauses = [{key: value} for key, value in metadata_filter.items()]
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}
