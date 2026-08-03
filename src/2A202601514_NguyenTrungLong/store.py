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
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(
        self,
        doc: Document,
        embedding: list[float] | None = None,
    ) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": [
                float(value)
                for value in (
                    embedding
                    if embedding is not None
                    else self._embedding_fn(doc.content)
                )
            ],
        }
        self._next_index += 1
        return record

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        ranked = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": float(_dot(query_embedding, record["embedding"])),
            }
            for record in records
        ]
        ranked.sort(key=lambda result: result["score"], reverse=True)
        return ranked[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it."""
        if not docs:
            return

        embed_many = getattr(self._embedding_fn, "embed_many", None)
        if callable(embed_many):
            embeddings = embed_many([doc.content for doc in docs])
            if len(embeddings) != len(docs):
                raise ValueError("embedding backend returned an unexpected batch size")
            records = [
                self._make_record(doc, embedding)
                for doc, embedding in zip(docs, embeddings)
            ]
        else:
            records = [self._make_record(doc) for doc in docs]
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                )
                return
            except Exception:
                # Keep the documents usable if the optional backend rejects a
                # collection setting or unsupported metadata value.
                self._use_chroma = False
                self._collection = None

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        if top_k <= 0:
            return []
        if self._use_chroma and self._collection is not None:
            result_count = min(top_k, self.get_collection_size())
            if result_count == 0:
                return []
            response = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=result_count,
                include=["documents", "metadatas", "distances"],
            )
            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]
            return [
                {
                    "id": item_id,
                    "content": content,
                    "metadata": dict(metadata or {}),
                    "score": float(1.0 - distance),
                }
                for item_id, content, metadata, distance in zip(
                    ids, documents, metadatas, distances
                )
            ]
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Filter by exact metadata matches, then run similarity search."""
        if top_k <= 0:
            return []
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma and self._collection is not None:
            collection_size = self.get_collection_size()
            if collection_size == 0:
                return []
            fetched = self._collection.get(
                where=metadata_filter,
                include=["documents", "metadatas", "embeddings"],
            )
            records = [
                {
                    "id": item_id,
                    "content": content,
                    "metadata": dict(metadata or {}),
                    "embedding": embedding,
                }
                for item_id, content, metadata, embedding in zip(
                    fetched.get("ids", []),
                    fetched.get("documents", []),
                    fetched.get("metadatas", []),
                    fetched.get("embeddings", []),
                )
            ]
            return self._search_records(query, records, top_k)

        filtered = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """Remove all chunks whose metadata doc_id matches doc_id."""
        if self._use_chroma and self._collection is not None:
            matches = self._collection.get(where={"doc_id": doc_id}, include=[])
            ids = matches.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        original_size = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size
