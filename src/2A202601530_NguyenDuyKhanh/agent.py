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
        retrieved_chunks = self.store.search(question, top_k=top_k)
        if not retrieved_chunks:
            return "I could not find any relevant context in the knowledge base."

        context_lines = []
        for index, chunk in enumerate(retrieved_chunks, start=1):
            metadata = chunk.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "unknown source"
            doc_id = metadata.get("doc_id", chunk.get("id", "unknown doc"))
            context_lines.append(
                f"[{index}] doc_id={doc_id}; source={source}\n{chunk['content']}"
            )

        prompt = (
            "Instruction: Use only the context below to answer the question. "
            "If the context is not sufficient, say that clearly.\n\n"
            "Context:\n"
            f"{chr(10).join(context_lines)}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
