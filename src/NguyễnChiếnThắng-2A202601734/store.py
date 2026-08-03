from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """A vector store with an in-memory implementation and optional Chroma mirror."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._use_chroma = False
        self._next_index = 0
        try:
            import chromadb
            self._collection = chromadb.Client().get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "id": doc.id,
            "content": doc.content,
            "metadata": dict(doc.metadata or {}),
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []
        query_embedding = self._embedding_fn(query)
        ranked = sorted(
            ((_dot(query_embedding, record["embedding"]), record) for record in records),
            key=lambda item: item[0],
            reverse=True,
        )
        return [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": score,
            }
            for score, record in ranked[:top_k]
        ]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            if self._use_chroma and self._collection is not None:
                chroma_id = f"{doc.id}::{self._next_index}"
                record["_chroma_id"] = chroma_id
                self._next_index += 1
                metadata = record["metadata"] or {"_empty_metadata": True}
                try:
                    self._collection.add(
                        ids=[chroma_id],
                        documents=[record["content"]],
                        embeddings=[record["embedding"]],
                        metadatas=[metadata],
                    )
                except Exception:
                    pass

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)
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
        removed = [
            record
            for record in self._store
            if record["id"] == doc_id or record["metadata"].get("doc_id") == doc_id
        ]
        if not removed:
            return False
        self._store = [
            record
            for record in self._store
            if record["id"] != doc_id and record["metadata"].get("doc_id") != doc_id
        ]
        if self._use_chroma and self._collection is not None:
            chroma_ids = [
                record["_chroma_id"] for record in removed if "_chroma_id" in record
            ]
            if chroma_ids:
                try:
                    self._collection.delete(ids=chroma_ids)
                except Exception:
                    pass
        return True
