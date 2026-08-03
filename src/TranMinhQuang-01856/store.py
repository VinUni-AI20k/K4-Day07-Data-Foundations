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
        self._client = None
        self._next_index = 0

        try:
            import chromadb

            self._client = chromadb.Client()
            try:
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
            except TypeError:
                # Older/minimal Chroma clients may not accept collection metadata.
                self._collection = self._client.get_or_create_collection(
                    name=self._collection_name
                )
            self._use_chroma = True
        except Exception:
            self._disable_chroma()

    def _disable_chroma(self) -> None:
        """Switch to the deterministic in-memory backend after a Chroma error."""
        self._use_chroma = False
        self._collection = None
        self._client = None

    def _embed(self, text: str) -> list[float]:
        """Return a plain-float vector accepted by both supported backends."""
        return [float(value) for value in self._embedding_fn(text)]

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        # Chunk documents may already carry their parent document ID.  Plain
        # documents need this default so delete_document() works for both forms.
        metadata.setdefault("doc_id", doc.id)

        storage_id = f"{doc.id}::{self._next_index}"
        embedding = self._embed(doc.content)
        self._next_index += 1
        return {
            "id": doc.id,
            "_storage_id": storage_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    @staticmethod
    def _public_result(record: dict[str, Any], score: float) -> dict[str, Any]:
        """Remove backend-only fields from a search result."""
        return {
            "id": record["id"],
            "content": record["content"],
            "metadata": dict(record["metadata"]),
            "score": float(score),
        }

    def _rank_records(
        self,
        query_embedding: list[float],
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []

        scored = [
            (float(_dot(query_embedding, record["embedding"])), record)
            for record in records
        ]
        # sorted() is stable, so equal-score records retain insertion order.
        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            self._public_result(record, score)
            for score, record in scored[:top_k]
        ]

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []
        return self._rank_records(self._embed(query), records, top_k)

    @staticmethod
    def _chroma_where(metadata_filter: dict | None) -> dict | None:
        """Translate exact-match filters to Chroma's portable where syntax."""
        if not metadata_filter:
            return None
        if len(metadata_filter) == 1:
            return dict(metadata_filter)
        return {
            "$and": [{key: {"$eq": value}} for key, value in metadata_filter.items()]
        }

    def _query_chroma_records(
        self,
        query_embedding: list[float],
        top_k: int,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]] | None:
        """Ask Chroma for candidates, returning None when memory should take over."""
        if not self._use_chroma or self._collection is None:
            return None

        candidates = [
            record
            for record in self._store
            if not metadata_filter
            or all(
                key in record["metadata"]
                and record["metadata"][key] == value
                for key, value in metadata_filter.items()
            )
        ]
        result_count = min(top_k, len(candidates))
        if result_count <= 0:
            return []

        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": result_count,
            "include": ["distances"],
        }
        where = self._chroma_where(metadata_filter)
        if where is not None:
            query_kwargs["where"] = where

        try:
            response = self._collection.query(**query_kwargs)
            raw_ids = response.get("ids", [])
            if raw_ids and isinstance(raw_ids[0], (list, tuple)):
                raw_ids = raw_ids[0]

            selected_ids = set(raw_ids)
            selected = [
                record
                for record in candidates
                if record["_storage_id"] in selected_ids
            ]
            if len(selected) != result_count:
                # This can happen when a named Chroma collection already
                # contains records owned by another EmbeddingStore instance.
                return None
            return selected
        except Exception:
            self._disable_chroma()
            return None

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        # Build all records before mutating the store, so an embedding failure
        # does not leave a partially-added batch in memory.
        records = [self._make_record(doc) for doc in docs]
        self._store.extend(records)

        if not self._use_chroma or self._collection is None:
            return

        try:
            self._collection.add(
                ids=[record["_storage_id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[dict(record["metadata"]) for record in records],
            )
        except Exception:
            # Chroma is optional; the complete batch is already available in
            # the canonical in-memory store.
            self._disable_chroma()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0 or not self._store:
            return []

        query_embedding = self._embed(query)
        candidates = self._query_chroma_records(query_embedding, top_k)
        if candidates is None:
            candidates = self._store
        return self._rank_records(query_embedding, candidates, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)
        if top_k <= 0 or not self._store:
            return []

        filtered = [
            record
            for record in self._store
            if all(
                key in record["metadata"]
                and record["metadata"][key] == value
                for key, value in metadata_filter.items()
            )
        ]
        if not filtered:
            return []

        query_embedding = self._embed(query)
        candidates = self._query_chroma_records(
            query_embedding,
            top_k,
            metadata_filter=metadata_filter,
        )
        if candidates is None:
            candidates = filtered
        return self._rank_records(query_embedding, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        removed = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") == doc_id
        ]
        if not removed:
            return False

        removed_storage_ids = [
            record["_storage_id"] for record in removed
        ]
        removed_storage_id_set = set(removed_storage_ids)
        self._store = [
            record
            for record in self._store
            if record["_storage_id"] not in removed_storage_id_set
        ]

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=removed_storage_ids)
            except Exception:
                self._disable_chroma()
        return True
