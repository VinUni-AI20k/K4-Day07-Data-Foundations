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

    NO_CONTEXT_MESSAGE = (
        "Tôi không tìm thấy thông tin liên quan trong cơ sở tri thức để trả lời câu hỏi này."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if not results:
            return self.NO_CONTEXT_MESSAGE

        context_blocks = []
        for index, result in enumerate(results, start=1):
            source = result.get("metadata", {}).get("source_url") or result.get("metadata", {}).get(
                "doc_id", "unknown"
            )
            context_blocks.append(f"[{index}] (nguồn: {source})\n{result['content']}")
        context = "\n\n".join(context_blocks)

        prompt = (
            "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp.\n"
            "Chỉ dùng thông tin trong phần NGỮ CẢNH dưới đây. Nếu ngữ cảnh không đủ để trả lời, "
            "hãy nói rõ là không tìm thấy thông tin thay vì suy đoán.\n"
            "Khi trả lời, trích dẫn số hiệu đoạn ngữ cảnh đã dùng, ví dụ [1].\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )
        return self.llm_fn(prompt)
