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

    NO_CONTEXT_ANSWER = (
        "Tôi không tìm thấy thông tin liên quan trong cơ sở tri thức nên không thể trả lời câu hỏi này."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn
        # Giữ lại kết quả truy xuất gần nhất để Giai đoạn 2 kiểm tra grounding
        # (chunk nào đã sinh ra câu trả lời).
        self.last_results: list[dict] = []

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        self.last_results = results

        # Không có ngữ cảnh thì không gọi LLM: tránh để mô hình bịa (hallucinate).
        if not results:
            return self.NO_CONTEXT_ANSWER

        context = "\n\n".join(
            f"[{index}] (score={result['score']:.3f}) {result['content']}"
            for index, result in enumerate(results, start=1)
        )
        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Chỉ dùng thông tin trong phần NGỮ CẢNH. Nếu ngữ cảnh không đủ, hãy nói rõ là không đủ thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
        return str(self.llm_fn(prompt))
