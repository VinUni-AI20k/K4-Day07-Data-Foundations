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
        # 1. Retrieve the most relevant chunks for the question.
        results = self.store.search(question, top_k=top_k)

        # 2. Build the prompt: numbered chunks as context, then the question.
        if results:
            context = "\n\n".join(
                f"[Đoạn {index}] {result['content']}"
                for index, result in enumerate(results, start=1)
            )
        else:
            context = "(Không truy xuất được đoạn ngữ cảnh nào từ kho tri thức.)"
        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên ngữ cảnh được cung cấp bên dưới.\n"
            "Chỉ sử dụng thông tin trong phần ngữ cảnh; nếu ngữ cảnh không đủ để trả lời, "
            "hãy nói rõ là bạn không có thông tin.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n\n"
            "Trả lời:"
        )

        # 3. Call the LLM to generate the final answer.
        return self.llm_fn(prompt)
