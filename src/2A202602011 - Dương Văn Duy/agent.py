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
        # TODO: store references to store and llm_fn
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # TODO: retrieve chunks, build prompt, call llm_fn
        results = self.store.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[{index}] {result['content']}" for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Answer the question using only the context below. "
            "If the context does not contain enough information, say that you do not know.\n\n"
            f"Context:\n{context or '[No relevant context found]'}\n\n"
            f"Question: {question}\nAnswer:"
        )
        return self.llm_fn(prompt)
