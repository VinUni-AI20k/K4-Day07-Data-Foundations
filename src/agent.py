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
        context_blocks = []
        for rank, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source_url") or metadata.get("source") or "unknown"
            context_blocks.append(
                f"[CONTEXT CHUNK {rank}]\n"
                f"document_id: {result.get('id', 'unknown')}\n"
                f"source: {source}\n"
                f"content:\n{result['content']}\n"
                f"[END CONTEXT CHUNK {rank}]"
            )

        context = "\n\n".join(context_blocks) or "[NO CONTEXT WAS RETRIEVED]"
        prompt = (
            "Answer the question using only the retrieved context below. "
            "Do not add facts that the context does not support. If the context "
            "is insufficient, state that the answer is not available in the "
            "retrieved context.\n\n"
            f"RETRIEVED CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{question}\n\n"
            "ANSWER:"
        )
        return self.llm_fn(prompt)
