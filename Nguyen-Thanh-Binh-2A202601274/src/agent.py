from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore

PROMPT_TEMPLATE = """Bạn là trợ lý tri thức. Chỉ được trả lời DỰA TRÊN ngữ cảnh bên dưới.

Quy tắc:
- Nếu ngữ cảnh không đủ thông tin, hãy nói rõ là không tìm thấy trong tài liệu; tuyệt đối không bịa.
- Khi trả lời, trích dẫn số hiệu đoạn ngữ cảnh đã dùng, ví dụ [1], [2].
- Trả lời ngắn gọn, bám sát câu chữ của tài liệu.

NGỮ CẢNH:
{context}

CÂU HỎI: {question}

TRẢ LỜI:"""

NO_CONTEXT = "(Không tìm thấy đoạn tài liệu nào liên quan trong cơ sở tri thức.)"


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

    def answer(self, question: str, top_k: int = 3, metadata_filter: dict | None = None) -> str:
        # 1) Truy xuất (lọc metadata trước khi xếp hạng nếu có yêu cầu — cần cho K4)
        if metadata_filter:
            results = self.store.search_with_filter(question, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = self.store.search(question, top_k=top_k)

        # 2) Dựng ngữ cảnh có đánh số + nguồn để câu trả lời truy vết được
        if results:
            blocks = []
            for index, result in enumerate(results, start=1):
                metadata = result.get("metadata") or {}
                source = metadata.get("source_url") or metadata.get("doc_id") or result.get("id", "unknown")
                blocks.append(
                    f"[{index}] (nguồn: {source} | score={result.get('score', 0.0):.3f})\n{result.get('content', '')}"
                )
            context = "\n\n".join(blocks)
        else:
            context = NO_CONTEXT

        prompt = PROMPT_TEMPLATE.format(context=context, question=question)

        # 3) Sinh câu trả lời
        answer = self.llm_fn(prompt)
        return answer if isinstance(answer, str) else str(answer)
