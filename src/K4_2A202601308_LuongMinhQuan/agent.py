from typing import Callable

from .store import EmbeddingStore

# Trả về khi store không có chunk nào khớp: nói thẳng là thiếu dữ liệu,
# gọi LLM lúc này chỉ tạo cơ hội cho nó bịa.
NO_CONTEXT_ANSWER = (
    "Không tìm thấy tài liệu liên quan trong kho kiến thức, "
    "nên chưa đủ căn cứ để trả lời câu hỏi này."
)

PROMPT_TEMPLATE = """Bạn là trợ lý trả lời dựa trên tài liệu nội bộ.
Chỉ dùng thông tin trong phần Context bên dưới, không suy diễn ra ngoài Context.
Nếu Context không đủ để trả lời, hãy nói rõ là không đủ thông tin.
Trích dẫn nguồn bằng số hiệu [1], [2], ... ngay sau ý lấy từ chunk tương ứng.

Context:
{context}

Question: {question}
Answer:"""


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
        # Agent không tự nhúng gì cả — toàn bộ việc tìm kiếm đã nằm trong store.
        results = self.store.search(question, top_k=top_k)
        if not results:
            return NO_CONTEXT_ANSWER

        context = self._format_context(results)
        prompt = PROMPT_TEMPLATE.format(context=context, question=question)
        return self.llm_fn(prompt)

    @staticmethod
    def _format_context(results: list[dict]) -> str:
        """Đánh số [1], [2], ... kèm nguồn để truy vết câu trả lời về đúng chunk."""
        blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata") or {}
            # doc_id trỏ về file gốc; source là đường dẫn -> đủ để mở lại tài liệu khi debug.
            source = metadata.get("doc_id") or metadata.get("source") or result.get("id", "unknown")
            blocks.append(f"[{index}] (nguồn: {source})\n{result.get('content', '')}")
        return "\n\n".join(blocks)
