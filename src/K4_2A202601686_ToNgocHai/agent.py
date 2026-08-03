from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Agent RAG: truy xuất context, tạo prompt có căn cứ rồi gọi LLM."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[Nguồn {index}] {result['content']}"
            for index, result in enumerate(results, start=1)
        )
        if not context:
            context = "Không tìm thấy thông tin liên quan trong cơ sở tri thức."

        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức. "
            "Chỉ trả lời bằng thông tin trong ngữ cảnh; nếu không đủ thông tin, "
            "hãy nói rõ rằng bạn không biết.\n\n"
            f"Ngữ cảnh:\n{context}\n\n"
            f"Câu hỏi: {question}\n"
            "Trả lời:"
        )
        return self.llm_fn(prompt)
