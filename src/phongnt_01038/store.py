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
            import chromadb.client  # noqa: F401

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        return {
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": {**doc.metadata, "doc_id": doc.id},
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records:
            return []
        query_embedding = self._embedding_fn(query)
        scored = []
        for record in records:
            score = sum(q * r for q, r in zip(query_embedding, record["embedding"]))
            scored.append((score, record))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, record in scored[:top_k]:
            results.append({
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })
        return results

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        for doc in docs:
            record = self._make_record(doc)
            if self._use_chroma and self._collection is not None:
                self._collection.add(
                    ids=[doc.id],
                    documents=[doc.content],
                    embeddings=[record["embedding"]],
                    metadatas=[record["metadata"]],
                )
            else:
                record["index"] = self._next_index
                self._next_index += 1
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            query_embedding = self._embedding_fn(query)
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            output = []
            for i in range(len(results["ids"][0])):
                output.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": float(results["distances"][0][i]) if "distances" in results else 0.0,
                })
            return output
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k)

        if self._use_chroma and self._collection is not None:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                where=metadata_filter,
            )
            output = []
            for i in range(len(results["ids"][0])):
                output.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": float(results["distances"][0][i]) if "distances" in results else 0.0,
                })
            return output

        # In-memory: filter first, then search
        filtered = [
            record for record in self._store
            if all(record["metadata"].get(k) == v for k, v in metadata_filter.items())
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(where={"doc_id": doc_id})
                return True
            except Exception:
                return False

        # In-memory: filter out records with matching doc_id
        original_len = len(self._store)
        self._store = [r for r in self._store if r["metadata"].get("doc_id") != doc_id]
        return len(self._store) < original_len
