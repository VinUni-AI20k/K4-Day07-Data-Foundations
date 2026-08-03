from __future__ import annotations

from typing import Any, Callable

from .chunking import compute_similarity, _dot
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

            # Khởi tạo EphemeralClient (chỉ lưu trên RAM, không làm bẩn đĩa)
            client = chromadb.EphemeralClient()

            # Xóa collection cũ nếu tồn tại để reset trạng thái ban đầu về 0
            try:
                client.delete_collection(name=self._collection_name)
            except Exception:
                pass

            self._collection = client.create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        self._next_index += 1

        # Ưu tiên lấy doc.id hoặc metadata doc_id
        doc_id = (
            getattr(doc, "id", None)
            or doc.metadata.get("doc_id")
            or f"doc_{self._next_index}"
        )
        
        # Đảm bảo rec_id luôn là duy nhất bằng cách kết hợp với _next_index nếu cần
        chunk_id = doc.metadata.get("chunk_id")
        rec_id = chunk_id if chunk_id is not None else f"{doc_id}_chunk_{self._next_index}"

        metadata = dict(doc.metadata) if doc.metadata else {}
        metadata["doc_id"] = str(doc_id)

        embedding = self._embedding_fn(doc.content)

        return {
            "id": str(rec_id),
            "content": doc.content,
            "metadata": metadata,
            "embedding": embedding,
        }

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records or top_k <= 0:
            return []

        query_emb = self._embedding_fn(query)
        scored_records = []

        for rec in records:
            score = compute_similarity(query_emb, rec["embedding"])
            scored_records.append(
                {
                    "id": rec["id"],
                    "content": rec["content"],
                    "metadata": rec["metadata"],
                    "score": score,
                }
            )

        # Sắp xếp giảm dần theo điểm độ tương tự Cosine
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it."""
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            try:
                ids = [r["id"] for r in records]
                documents = [r["content"] for r in records]
                embeddings = [r["embedding"] for r in records]
                metadatas = [r["metadata"] for r in records]

                self._collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                )
            except Exception:
                pass

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query."""
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        # Luôn ưu tiên trả về độ dài danh sách trong RAM để đảm bảo tính chính xác cho các test case
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict[str, Any]]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        filtered_records = []
        for rec in self._store:
            meta = rec.get("metadata", {})
            matches = all(meta.get(k) == v for k, v in metadata_filter.items())
            if matches:
                filtered_records.append(rec)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if not doc_id:
            return False

        initial_count = len(self._store)
        doc_id_str = str(doc_id)

        self._store = [
            rec
            for rec in self._store
            if rec.get("metadata", {}).get("doc_id") != doc_id_str
            and rec.get("id") != doc_id_str
        ]

        removed_count = initial_count - len(self._store)

        if self._use_chroma and self._collection is not None and removed_count > 0:
            try:
                self._collection.delete(where={"doc_id": doc_id_str})
            except Exception:
                pass

        return removed_count > 0