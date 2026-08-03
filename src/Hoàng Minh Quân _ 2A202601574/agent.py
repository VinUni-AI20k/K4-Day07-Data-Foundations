from __future__ import annotations

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
        """
        Answers a user question by retrieving relevant context chunks from
        the vector store, constructing a RAG prompt, and invoking the LLM.
        """
        if not question or not question.strip():
            return "Please provide a valid question."

        # 1. Truy xuất top_k đoạn văn bản liên quan nhất từ kho dữ liệu vector
        retrieved_docs = self.store.search(question, top_k=top_k)

        # 2. Xây dựng ngữ cảnh (context) từ các kết quả truy xuất
        if not retrieved_docs:
            context_str = "No relevant context found."
        else:
            context_blocks = []
            for i, doc in enumerate(retrieved_docs, start=1):
                content = doc.get("content", "").strip()
                context_blocks.append(f"[{i}] {content}")
            context_str = "\n\n".join(context_blocks)

        # 3. Tạo RAG prompt ghép câu hỏi và ngữ cảnh
        prompt = (
            f"Context information is below.\n"
            f"---------------------\n"
            f"{context_str}\n"
            f"---------------------\n"
            f"Given the context information above and not prior knowledge, answer the question.\n"
            f"Question: {question}\n"
            f"Answer:"
        )

        # 4. Gọi hàm LLM để sinh ra câu trả lời và đảm bảo kết quả trả về là str
        response = self.llm_fn(prompt)
        return str(response) if response is not None else ""