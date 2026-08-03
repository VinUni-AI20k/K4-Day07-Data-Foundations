from __future__ import annotations

import os
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

            persist_dir = os.getenv("CHROMA_PERSIST_DIR")
            client = (
                chromadb.PersistentClient(path=persist_dir)
                if persist_dir
                else chromadb.Client()
            )
            self._collection = client.get_or_create_collection(name=self._collection_name)
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
        query_vec = self._embedding_fn(query)
        scored = sorted(
            ((_dot(query_vec, record["embedding"]), record) for record in records),
            key=lambda pair: pair[0],
            reverse=True,
        )
        results = []
        for score, record in scored[:top_k]:
            result = dict(record)
            result["score"] = score
            results.append(result)
        return results

    def add_documents(self, docs: list[Document]) -> None:
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
        if self._use_chroma:
            response = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
            )
            results = []
            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]
            for index, record_id in enumerate(ids):
                results.append(
                    {
                        "id": record_id,
                        "content": documents[index],
                        "metadata": metadatas[index] or {},
                        "score": 1.0 - distances[index],
                    }
                )
            return results
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        if metadata_filter is None:
            metadata_filter = {}
        if self._use_chroma:
            response = self._collection.query(
                query_embeddings=[self._embedding_fn(query)],
                n_results=top_k,
                where=metadata_filter,
            )
            results = []
            ids = response.get("ids", [[]])[0]
            documents = response.get("documents", [[]])[0]
            metadatas = response.get("metadatas", [[]])[0]
            distances = response.get("distances", [[]])[0]
            for index, record_id in enumerate(ids):
                results.append(
                    {
                        "id": record_id,
                        "content": documents[index],
                        "metadata": metadatas[index] or {},
                        "score": 1.0 - distances[index],
                    }
                )
            return results

        candidates = [
            record
            for record in self._store
            if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, candidates, top_k)

    def delete_document(self, doc_id: str) -> bool:
        if self._use_chroma:
            existing = self._collection.get(where={"doc_id": doc_id})
            ids = existing.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        before = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["id"] != doc_id and record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < before
