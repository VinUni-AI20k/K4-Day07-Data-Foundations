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
            return "Không tìm thấy dữ liệu liên quan để trả lời."
            
        context_parts = []
        for i, res in enumerate(results, 1):
            doc_id = res.get("metadata", {}).get("doc_id", "unknown")
            context_parts.append(f"[{i}] (Source: {doc_id}) {res['content']}")
            
        context_str = "\n".join(context_parts)
        
        prompt = f"Instruction: chỉ dùng context; nói rõ khi context không đủ.\nContext: {context_str}\nQuestion: {question}\nAnswer:"
        return self.llm_fn(prompt)
