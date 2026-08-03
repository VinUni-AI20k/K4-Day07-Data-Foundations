from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        """Trả lời từ top-k chunks, có thể lọc metadata trước khi truy xuất."""
        chunks = (
            self.store.search_with_filter(question, top_k, metadata_filter)
            if metadata_filter
            else self.store.search(question, top_k=top_k)
        )
        context_parts = []
        for index, chunk in enumerate(chunks, start=1):
            metadata = chunk.get("metadata", {})
            source = metadata.get("source") or metadata.get("doc_id") or chunk.get("id", "unknown")
            context_parts.append(f"[{index}] (source: {source}) {chunk['content']}")

        context = "\n".join(context_parts)
        prompt = (
            "Instruction: Answer using only the provided context. "
            "If the context is insufficient, clearly say so.\n"
            f"Context:\n{context}\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
