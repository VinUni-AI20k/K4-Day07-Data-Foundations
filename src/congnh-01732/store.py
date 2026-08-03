from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document

# ChromaDB only accepts these scalar types as metadata values; YAML front
# matter can parse dates/objects, so anything else is stringified.
_CHROMA_SAFE_TYPES = (str, int, float, bool)


def _normalize_metadata(metadata: dict) -> dict:
    return {
        key: (value if isinstance(value, _CHROMA_SAFE_TYPES) else str(value))
        for key, value in (metadata or {}).items()
    }


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    # Sequence number used to give every store instance its own physical
    # ChromaDB collection: chromadb's ephemeral storage is shared across
    # clients in the same process, keyed by collection name, so reusing the
    # logical name verbatim would leak records between separate stores.
    _instance_seq = 0

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

            # Ephemeral (in-RAM) client: no persistence needed for the lab,
            # and cosine space so scores match the dot-product semantics of
            # the in-memory fallback (both embedders return normalized vectors).
            type(self)._instance_seq += 1
            physical_name = f"{collection_name}-{type(self)._instance_seq}"
            client_factory = getattr(chromadb, "EphemeralClient", None) or chromadb.Client
            self._client = client_factory()
            self._collection = self._client.get_or_create_collection(
                name=physical_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document.

        Every record carries id / content / embedding / metadata, and the
        document id is injected into the metadata as 'doc_id' so chunks can
        later be filtered or deleted per original document.
        """
        record = {
            "id": f"{doc.id}-{self._next_index}",
            "content": doc.content,
            "embedding": self._embedding_fn(doc.content),
            "metadata": _normalize_metadata({**(doc.metadata or {}), "doc_id": doc.id}),
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records.

        Scores each record by dot product between the query embedding and the
        stored embedding (both normalized => cosine similarity), then returns
        the top_k records sorted by score descending.
        """
        if not records or top_k <= 0:
            return []
        query_vec = self._embedding_fn(query)
        scored = sorted(
            ((_dot(query_vec, record["embedding"]), record) for record in records),
            key=lambda pair: pair[0],
            reverse=True,
        )
        return [
            {
                "id": record["id"],
                "content": record["content"],
                "score": score,
                "metadata": record["metadata"],
            }
            for score, record in scored[:top_k]
        ]

    def _chroma_query(self, query: str, top_k: int, where: dict | None) -> list[dict[str, Any]]:
        """Helper: query the ChromaDB collection and normalize the response."""
        if top_k <= 0:
            return []
        count = self._collection.count()
        if count == 0:
            return []
        result = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=min(top_k, count),
            where=where,
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        return [
            {
                "id": ids[i],
                "content": documents[i],
                # cosine distance = 1 - cosine similarity
                "score": 1.0 - distances[i],
                "metadata": metadatas[i] or {},
            }
            for i in range(len(ids))
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return
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
        if self._use_chroma:
            return self._chroma_query(query, top_k, where=None)
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if self._use_chroma:
            return self._chroma_query(query, top_k, where=metadata_filter)
        records = self._store
        if metadata_filter:
            records = [
                record
                for record in records
                if all(record["metadata"].get(key) == value for key, value in metadata_filter.items())
            ]
        return self._search_records(query, records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            size_before = self._collection.count()
            self._collection.delete(where={"doc_id": doc_id})
            return self._collection.count() < size_before
        size_before = len(self._store)
        self._store = [
            record for record in self._store if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < size_before
