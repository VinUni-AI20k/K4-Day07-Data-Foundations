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
        "Khong tim thay tai lieu nao trong knowledge base de tra loi cau hoi nay."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)

        # Store rong -> tra thong bao ro rang thay vi goi LLM vo ich.
        if not results:
            return self.NO_CONTEXT_MESSAGE

        prompt = self.build_prompt(question, results)
        return self.llm_fn(prompt)

    # ------------------------------------------------------------------
    # Helpers (khong nam trong contract cua test, nhung giup bench.py tai su dung)
    # ------------------------------------------------------------------
    def format_context(self, results: list[dict]) -> str:
        """Danh so [1], [2]... kem doc_id de cau tra loi truy vet duoc ve dung chunk."""
        blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {}) or {}
            doc_id = metadata.get("doc_id", "unknown")
            chunk_index = metadata.get("chunk_index")
            source = metadata.get("source_url") or metadata.get("source") or "n/a"
            label = f"{doc_id}" if chunk_index is None else f"{doc_id}::chunk_{chunk_index}"
            blocks.append(
                f"[{index}] (nguon: {label} | url: {source})\n{result.get('content', '')}"
            )
        return "\n\n".join(blocks)

    def build_prompt(self, question: str, results: list[dict]) -> str:
        context = self.format_context(results)
        return (
            "Instruction: Ban la tro ly tra loi dua tren tai lieu. CHI dung thong tin "
            "trong phan Context ben duoi. Trich dan so hieu nguon dang [1], [2] cho moi "
            "y. Neu Context khong du de tra loi, hay noi ro la khong du thong tin.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
