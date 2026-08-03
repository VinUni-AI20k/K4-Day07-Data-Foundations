from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """Vector store backed by ChromaDB when available, otherwise by memory."""

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

            client = chromadb.EphemeralClient()
            physical_name = f"{collection_name[:40]}-{uuid4().hex[:12]}"
            self._collection = client.create_collection(name=physical_name)
            self._use_chroma = True
        except Exception:
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}::{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
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

    def _get_chroma_records(self) -> list[dict[str, Any]]:
        if self._collection is None:
            return []

        payload = self._collection.get(include=["documents", "metadatas", "embeddings"])
        ids = list(payload.get("ids") or [])
        documents = list(payload.get("documents") or [])
        metadatas = list(payload.get("metadatas") or [])
        raw_embeddings = payload.get("embeddings")
        embeddings = list(raw_embeddings) if raw_embeddings is not None else []
        return [
            {
                "id": record_id,
                "content": documents[index],
                "metadata": dict(metadatas[index] or {}),
                "embedding": [float(value) for value in embeddings[index]],
            }
            for index, record_id in enumerate(ids)
        ]

    def add_documents(self, docs: list[Document]) -> None:
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                metadatas=[record["metadata"] for record in records],
                embeddings=[record["embedding"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        records = self._get_chroma_records() if self._use_chroma else self._store
        return self._search_records(query, records, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma and self._collection is not None:
            return int(self._collection.count())
        return len(self._store)

    def search_with_filter(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> list[dict[str, Any]]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        records = self._get_chroma_records() if self._use_chroma else self._store
        records = [
            record
            for record in records
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma and self._collection is not None:
            matching = self._collection.get(where={"doc_id": doc_id}, include=[])
            ids = list(matching.get("ids") or [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        original_size = len(self._store)
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size
