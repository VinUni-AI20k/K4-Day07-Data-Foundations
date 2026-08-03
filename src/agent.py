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
            return "I don't have any retrieved context to answer that question."

        # Build numbered context with traceable source (doc_id in metadata)
        context_lines: list[str] = []
        for idx, r in enumerate(results, start=1):
            doc_id = None
            if isinstance(r.get("metadata"), dict):
                doc_id = r["metadata"].get("doc_id")
            header = f"[{idx}]"
            if doc_id:
                header += f" (doc_id={doc_id})"
            content = r.get("content", "")
            context_lines.append(f"{header} {content}")

        context_str = "\n\n".join(context_lines)

        prompt = (
            "Instruction: Only use the provided context to answer. If the context is insufficient, say you don't know.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )

        return self.llm_fn(prompt)

