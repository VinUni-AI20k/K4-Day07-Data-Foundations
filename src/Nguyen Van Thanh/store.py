from __future__ import annotations

import os
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """Small vector store with a deterministic in-memory implementation.

    When ChromaDB is installed, records are mirrored to a Chroma collection. The
    in-memory representation remains the source of truth so classroom tests stay
    reproducible and the public API behaves identically with or without Chroma.
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

            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            client = chromadb.PersistentClient(path=persist_dir) if persist_dir else chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        storage_id = f"{self._collection_name}-{self._next_index}-{doc.id}"
        self._next_index += 1
        return {
            "id": doc.id,
            "storage_id": storage_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": [float(value) for value in self._embedding_fn(doc.content)],
        }

    def _search_records(
        self,
        query: str,
        records: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if top_k <= 0 or not records:
            return []
        query_embedding = self._embedding_fn(query)
        ranked = []
        for record in records:
            ranked.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": dict(record["metadata"]),
                    "score": float(_dot(query_embedding, record["embedding"])),
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            if self._use_chroma and self._collection is not None:
                try:
                    self._collection.add(
                        ids=[record["storage_id"]],
                        documents=[record["content"]],
                        embeddings=[record["embedding"]],
                        metadatas=[record["metadata"]],
                    )
                except Exception:
                    # Chroma is optional; a backend-specific metadata limitation
                    # must not break the required in-memory implementation.
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
    ) -> list[dict]:
        if not metadata_filter:
            return self.search(query, top_k=top_k)
        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        removed = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") == doc_id or record["id"] == doc_id
        ]
        if not removed:
            return False

        removed_storage_ids = [record["storage_id"] for record in removed]
        self._store = [record for record in self._store if record not in removed]
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=removed_storage_ids)
            except Exception:
                pass
        return True
