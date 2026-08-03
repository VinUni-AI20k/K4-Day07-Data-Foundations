from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Retrieval-augmented agent over an EmbeddingStore."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        if results:
            context_blocks = []
            for index, result in enumerate(results, start=1):
                source = result.get("metadata", {}).get("source_url") or result.get("metadata", {}).get("source") or result.get("id")
                context_blocks.append(
                    f"[Nguồn {index} | score={result['score']:.4f} | {source}]\n{result['content']}"
                )
            context = "\n\n".join(context_blocks)
        else:
            context = "Không tìm thấy ngữ cảnh phù hợp trong cơ sở tri thức."

        prompt = (
            "Bạn là trợ lý hỏi đáp dựa trên cơ sở tri thức. "
            "Chỉ trả lời bằng thông tin có trong NGỮ CẢNH; nếu thiếu dữ liệu, hãy nói rõ là không đủ thông tin.\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI:\n{question}\n\n"
            "TRẢ LỜI NGẮN GỌN, CHÍNH XÁC VÀ CÓ CĂN CỨ:"
        )
        return self.llm_fn(prompt)
