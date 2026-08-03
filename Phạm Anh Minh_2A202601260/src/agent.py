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
        self._store = store
        self._llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self._store.search(question, top_k=top_k)
        context = "\n\n".join(f"[{i}] {r['content']}" for i, r in enumerate(results, start=1))
        prompt = (
            f"Dựa trên ngữ cảnh dưới đây, trả lời câu hỏi sau:{question}\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
        )
        return self._llm_fn(prompt)
