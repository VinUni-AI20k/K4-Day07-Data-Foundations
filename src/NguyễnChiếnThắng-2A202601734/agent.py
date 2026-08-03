from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """Retrieve context from the store and pass a grounded prompt to an LLM."""

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        results = self.store.search(question, top_k=top_k)
        context_parts: list[str] = []
        for index, result in enumerate(results, start=1):
            metadata = result.get("metadata", {})
            source = metadata.get("source") or metadata.get("doc_id") or result["id"]
            context_parts.append(
                f"[Chunk {index} | source: {source}]\n{result['content']}"
            )
        context = "\n\n".join(context_parts) or "(No relevant context found.)"
        prompt = f"""You are a helpful knowledge-base assistant.
Answer the question using only the context below. If the context does not contain
the answer, say that the information is not available.

Context:
{context}

Question: {question}

Answer:"""
        return self.llm_fn(prompt)
