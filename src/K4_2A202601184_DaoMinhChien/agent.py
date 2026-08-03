from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Answer questions with context retrieved from an EmbeddingStore."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(
        self,
        question: str,
        top_k: int = 3,
        metadata_filter: dict | None = None,
    ) -> str:
        results = self.store.search_with_filter(
            question,
            top_k=top_k,
            metadata_filter=metadata_filter,
        )
        if results:
            context = "\n\n".join(
                f"[Context {index}]\n{result['content']}"
                for index, result in enumerate(results, start=1)
            )
        else:
            context = "No relevant context was found in the knowledge base."

        prompt = (
            "Answer the question using only the context below. "
            "If the context does not contain the answer, say that the available "
            "information is insufficient.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n"
            "Answer:"
        )
        return self.llm_fn(prompt)
