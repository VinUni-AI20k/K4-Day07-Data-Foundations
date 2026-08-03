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
        if self.store.get_collection_size() == 0:
            return "I don't know the answer because the knowledge base is empty."
            
        results = self.store.search(question, top_k=top_k)
        if not results:
            return "I don't know the answer because no relevant information was found."
            
        context_parts = []
        for i, res in enumerate(results, 1):
            doc_id = res.get("metadata", {}).get("doc_id", "unknown")
            context_parts.append(f"[{i}] (Source: {doc_id}) {res['content']}")
            
        context_str = "\n".join(context_parts)
        
        prompt = (
            "Instruction: Answer the question using ONLY the provided context. "
            "If the context does not contain enough information to answer the question, say clearly that you don't know.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        
        return self.llm_fn(prompt)
