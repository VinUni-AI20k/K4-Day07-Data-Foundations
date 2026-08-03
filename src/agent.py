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

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "I do not have enough context to answer this question."

        context_parts: list[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {}) or {}
            source = metadata.get("doc_id") or metadata.get("source") or "unknown"
            content = result.get("content", "")
            context_parts.append(f"[{index}] (source: {source}) {content}")

        context_str = "\n\n".join(context_parts)
        prompt = (
            "Instruction: Use only the provided context. If the context is insufficient, say so clearly.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)

