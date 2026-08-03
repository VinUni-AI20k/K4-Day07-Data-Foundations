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
        if results:
            context = "\n\n".join(
                (
                    f"[Nguồn {index}: {result['metadata'].get('source', result['id'])}; "
                    f"score={result['score']:.3f}]\n{result['content']}"
                )
                for index, result in enumerate(results, start=1)
            )
        else:
            context = "(Không tìm thấy đoạn tài liệu nào liên quan.)"

        prompt = f"""Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức.
Chỉ trả lời dựa trên NGỮ CẢNH bên dưới. Nếu ngữ cảnh không đủ để trả lời,
hãy nói rõ rằng bạn chưa có đủ thông tin; không suy đoán.

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""
        return self.llm_fn(prompt)
