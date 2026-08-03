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
        context_sections = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or result.get("document_id")
            context_sections.append(
                f"[Context {index} | source: {source}]\n{result['content']}"
            )

        context = "\n\n".join(context_sections) or "No relevant context was retrieved."
        prompt = (
            "You are a knowledge-base assistant. Answer the question using only "
            "the retrieved context below. If the context is insufficient, say that "
            "you do not have enough information rather than inventing an answer.\n\n"
            f"Question:\n{question}\n\n"
            f"Retrieved context:\n{context}\n\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
