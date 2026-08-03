"""Reproduce the individual similarity and provisional retrieval report.

Run from the repository root:
    python -m src.K4_2A202601184_DaoMinhChien.evaluation
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

from benchmark.queries import BENCHMARK
from ingest import chunk_document, load_documents

from .agent import KnowledgeBaseAgent
from .chunking import RecursiveChunker, compute_similarity
from .store import EmbeddingStore


SIMILARITY_PAIRS = [
    (
        "Người mua có thể yêu cầu đổi trả khi hàng bị lỗi.",
        "Khách hàng được trả lại sản phẩm nếu sản phẩm có lỗi.",
        "cao",
    ),
    (
        "Người bán phải cung cấp mô tả sản phẩm chính xác.",
        "Thông tin đăng bán cần phản ánh đúng sản phẩm.",
        "cao",
    ),
    (
        "Chính sách đổi trả bảo vệ quyền lợi người mua.",
        "Trời hôm nay có nhiều mây.",
        "thấp",
    ),
    (
        "Sản phẩm bị cấm không được đăng bán.",
        "Người bán không được đăng các mặt hàng bị cấm.",
        "cao",
    ),
    (
        "Yêu cầu đổi trả cần kèm bằng chứng.",
        "Người bán cập nhật giá sản phẩm.",
        "thấp",
    ),
]

BENCHMARK_QUERIES = [item["query"] for item in BENCHMARK]


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _make_lexical_embedder(texts: list[str]):
    vocabulary = sorted({token for text in texts for token in _tokens(text)})

    def embed(text: str) -> list[float]:
        counts = Counter(_tokens(text))
        vector = [float(counts.get(word, 0)) for word in vocabulary]
        magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / magnitude for value in vector]

    return embed


def _extract_top_context(prompt: str) -> str:
    """Small deterministic LLM stub used only to verify Agent prompt grounding."""
    marker = "[Context 1]\n"
    if marker not in prompt:
        return "Không đủ thông tin trong cơ sở tri thức."
    context = prompt.split(marker, 1)[1].split("\n\n[Context 2]", 1)[0]
    return context.strip()


def run_evaluation() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data" / "k4_asos_products"
    documents = load_documents(data_dir)
    if not documents:
        raise RuntimeError(f"Không tìm thấy tài liệu benchmark trong {data_dir}")
    chunker = RecursiveChunker(chunk_size=500)
    chunks = [
        chunk
        for document in documents
        for chunk in chunk_document(document, chunker)
    ]

    source_texts = [text for pair in SIMILARITY_PAIRS for text in pair[:2]]
    source_texts.extend(BENCHMARK_QUERIES)
    source_texts.extend(chunk.content for chunk in chunks)
    embed = _make_lexical_embedder(source_texts)

    similarity_results = []
    for sentence_a, sentence_b, prediction in SIMILARITY_PAIRS:
        score = compute_similarity(embed(sentence_a), embed(sentence_b))
        actual = "cao" if score >= 0.20 else "thấp"
        similarity_results.append(
            {
                "sentence_a": sentence_a,
                "sentence_b": sentence_b,
                "prediction": prediction,
                "score": round(score, 4),
                "actual": actual,
                "correct": prediction == actual,
            }
        )

    store = EmbeddingStore("personal_report", embedding_fn=embed)
    store.add_documents(chunks)
    agent = KnowledgeBaseAgent(store, llm_fn=_extract_top_context)
    retrieval_results = []
    for item in BENCHMARK:
        query = item["query"]
        metadata_filter = item["metadata_filter"]
        results = store.search_with_filter(
            query,
            top_k=3,
            metadata_filter=metadata_filter,
        )
        top_doc_ids = [result["metadata"].get("doc_id") for result in results]
        expected_doc_ids = set(item["expected_doc_ids"])
        if len(expected_doc_ids) > 1:
            document_match_top_3 = expected_doc_ids.issubset(set(top_doc_ids[:3]))
        else:
            document_match_top_3 = any(
                doc_id in expected_doc_ids for doc_id in top_doc_ids[:3]
            )
        retrieval_results.append(
            {
                "id": item["id"],
                "query": query,
                "gold_answer": item["gold_answer"],
                "metadata_filter": metadata_filter,
                "top_1_score": round(results[0]["score"], 4) if results else None,
                "top_1_doc_id": results[0]["metadata"].get("doc_id") if results else None,
                "top_3_doc_ids": top_doc_ids,
                "expected_doc_ids": item["expected_doc_ids"],
                "document_match_top_3": document_match_top_3,
                "agent_answer": agent.answer(
                    query,
                    top_k=3,
                    metadata_filter=metadata_filter,
                ),
            }
        )

    return {
        "embedding": "normalized lexical term-frequency vector",
        "chunker": "RecursiveChunker(chunk_size=500)",
        "chunk_count": len(chunks),
        "similarity_results": similarity_results,
        "retrieval_results": retrieval_results,
    }


def main() -> None:
    print(json.dumps(run_evaluation(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
