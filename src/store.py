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
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        meta = dict(doc.metadata) if doc.metadata is not None else {}
        if "doc_id" not in meta:
            meta["doc_id"] = doc.id
        embedding = self._embedding_fn(doc.content)
        record_id = f"{doc.id}_{self._next_index}"
        return {
            "id": record_id,
            "content": doc.content,
            "metadata": meta,
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_emb = self._embedding_fn(query)
        scored_results: list[dict[str, Any]] = []
        for r in records:
            score = _dot(query_emb, r["embedding"])
            scored_results.append(
                {
                    "id": r["id"],
                    "content": r["content"],
                    "metadata": r["metadata"],
                    "score": score,
                }
            )

        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)
            self._next_index += 1

            if self._use_chroma and self._collection is not None:
                try:
                    self._collection.add(
                        ids=[record["id"]],
                        documents=[doc.content],
                        embeddings=[record["embedding"]],
                        metadatas=[record["metadata"]],
                    )
                except Exception:
                    pass

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self._search_records(query, self._store, top_k)

    def _filter_records(self, metadata_filter: dict | None) -> list[dict[str, Any]]:
        if not metadata_filter:
            return list(self._store)

        filtered: list[dict[str, Any]] = []
        for record in self._store:
            meta = record.get("metadata", {})
            if all(meta.get(key) == value for key, value in metadata_filter.items()):
                filtered.append(record)
        return filtered

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        filtered = self._filter_records(metadata_filter)
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_size = len(self._store)
        self._store = [
            r for r in self._store if r.get("id") != doc_id and r.get("metadata", {}).get("doc_id") != doc_id
        ]
        removed = len(self._store) < initial_size

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass

        return removed

