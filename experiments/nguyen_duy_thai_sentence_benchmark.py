"""Reproducible SentenceChunker benchmark for Nguyễn Duy Thái.

Run from the repository root with UTF-8 enabled::

    python experiments/nguyen_duy_thai_sentence_benchmark.py

The script deliberately records the five high/low predictions as constants before
computing any score. It prints JSON to stdout so measured results can be copied
into the personal report and the team handoff without silently changing them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import chunk_document, load_documents
from src import ChunkingStrategyComparator, KnowledgeBaseAgent, LocalEmbedder, SentenceChunker
from src.chunking import compute_similarity
from src.models import Document
from src.store import EmbeddingStore


DATA_DIR = ROOT / "data" / "k4_ecommerce"
CONFIGURATIONS = (3, 5, 8)

# These labels are the predictions made before model scoring.
SIMILARITY_PAIRS = (
    {
        "id": 1,
        "a": "Người mua có thể yêu cầu trả hàng và hoàn tiền trong vòng 15 ngày.",
        "b": "Khách hàng được phép hoàn trả sản phẩm trong thời hạn mười lăm ngày.",
        "prediction": "cao",
    },
    {
        "id": 2,
        "a": "Đơn hàng ở trạng thái Chờ lấy hàng cần người bán đồng ý mới hủy được.",
        "b": "Muốn hủy đơn đang chờ lấy hàng, người mua phải đợi phản hồi của người bán.",
        "prediction": "cao",
    },
    {
        "id": 3,
        "a": "Người bán phải đăng ảnh thật của sản phẩm.",
        "b": "Shopee bảo vệ dữ liệu cá nhân của người dùng.",
        "prediction": "thấp",
    },
    {
        "id": 4,
        "a": "Sản phẩm bị cấm có thể khiến tài khoản người bán bị đình chỉ.",
        "b": "Vi phạm danh mục hàng cấm có thể dẫn đến khóa tài khoản.",
        "prediction": "cao",
    },
    {
        "id": 5,
        "a": "Shopee chuyển tiền cho người bán vào ngày thứ tư sau khi giao hàng thành công.",
        "b": "Mỹ phẩm phải có thông tin nguồn gốc và hạn sử dụng.",
        "prediction": "thấp",
    },
)


QUERIES = (
    {
        "id": 1,
        "query": "Đơn hàng do đơn vị vận chuyển không phải SPX đang ở trạng thái Chờ lấy hàng thì Người mua có thể hủy ngay không?",
        "filter": {"customer_role": "buyer"},
        "relevant": lambda item: (
            item["metadata"].get("doc_id") == "shopee-order-cancellation"
            and "Chờ lấy hàng" in item["content"]
            and ("chờ phản hồi" in item["content"] or "chấp nhận" in item["content"])
        ),
    },
    {
        "id": 2,
        "query": "Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn được giao thành công, và thời hạn riêng cho thực phẩm tươi sống hoặc đông lạnh là bao lâu?",
        "filter": None,
        "relevant": lambda item: (
            item["metadata"].get("doc_id") == "shopee-return-refund-policy"
            and "15" in item["content"]
            and "24" in item["content"]
            and "thực phẩm" in item["content"].lower()
        ),
    },
    {
        "id": 3,
        "query": "Ảnh sản phẩm đăng bán trên Shopee phải đáp ứng yêu cầu tối thiểu nào về ảnh thật và tỷ lệ diện tích sản phẩm?",
        "filter": None,
        "relevant": lambda item: (
            item["metadata"].get("doc_id") == "shopee-product-listing-rules"
            and "40%" in item["content"]
            and "ảnh thật" in item["content"].lower()
        ),
    },
    {
        "id": 4,
        "query": "Vi phạm Chính sách Cấm/Hạn chế Sản phẩm có thể khiến Người bán chịu những nhóm chế tài nào?",
        "filter": None,
        "relevant": lambda item: (
            item["metadata"].get("doc_id") == "shopee-prohibited-products-policy"
            and sum(
                marker in item["content"].lower()
                for marker in ("xóa", "giới hạn", "đình chỉ", "cấn trừ", "phong tỏa")
            )
            >= 2
        ),
    },
    {
        "id": 5,
        "query": "Nếu Người mua không nhấn Đã nhận được hàng hoặc Trả hàng/Hoàn tiền, Shopee chuyển tiền cho Người bán sớm nhất khi nào?",
        "filter": None,
        "relevant": lambda item: (
            item["metadata"].get("doc_id") == "shopee-terms-of-service"
            and ("ngày thứ 04" in item["content"].lower() or "ngày thứ 4" in item["content"].lower())
            and "giao hàng thành công" in item["content"].lower()
        ),
    },
)


class CachedEmbedder:
    """Use precomputed batch embeddings, falling back to the same local model."""

    def __init__(self, base: LocalEmbedder, cache: dict[str, list[float]]) -> None:
        self.base = base
        self.cache = cache

    def __call__(self, text: str) -> list[float]:
        if text not in self.cache:
            self.cache[text] = self.base(text)
        return self.cache[text]


def batch_cache(embedder: LocalEmbedder, texts: list[str]) -> dict[str, list[float]]:
    unique_texts = list(dict.fromkeys(texts))
    vectors = embedder.model.encode(
        unique_texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return {
        text: vector.tolist() if hasattr(vector, "tolist") else list(vector)
        for text, vector in zip(unique_texts, vectors)
    }


def compact_result(item: dict, relevant: Callable[[dict], bool]) -> dict:
    return {
        "doc_id": item["metadata"].get("doc_id"),
        "chunk_index": item["metadata"].get("chunk_index"),
        "score": round(float(item["score"]), 6),
        "relevant": bool(relevant(item)),
        "snippet": " ".join(item["content"].split())[:260],
    }


def extract_first_context(prompt: str) -> str:
    """Transparent no-API demo backend: return Context 1 verbatim.

    This is intentionally labelled extractive. It validates the RAG prompt path
    without pretending that a production generative LLM was evaluated.
    """
    marker = "[Context 1 | source:"
    if marker not in prompt:
        return "Không đủ ngữ cảnh để trả lời."
    first_context = prompt.split(marker, 1)[1]
    content = first_context.split("\n", 1)[1]
    return content.split("\n\n[Context 2 | source:", 1)[0].strip()


def run() -> dict:
    documents = load_documents(DATA_DIR)
    embedder = LocalEmbedder()

    pair_texts = [text for pair in SIMILARITY_PAIRS for text in (pair["a"], pair["b"])]
    pair_cache = batch_cache(embedder, pair_texts)
    pair_results = []
    for pair in SIMILARITY_PAIRS:
        score = compute_similarity(pair_cache[pair["a"]], pair_cache[pair["b"]])
        predicted_high = pair["prediction"] == "cao"
        pair_results.append(
            {
                **pair,
                "score": round(score, 6),
                "correct_at_0_5": predicted_high == (score >= 0.5),
            }
        )

    benchmark = {}
    for max_sentences in CONFIGURATIONS:
        chunker = SentenceChunker(max_sentences_per_chunk=max_sentences)
        chunks: list[Document] = []
        for document in documents:
            chunks.extend(chunk_document(document, chunker))

        all_texts = [chunk.content for chunk in chunks] + [entry["query"] for entry in QUERIES]
        cache = batch_cache(embedder, all_texts)
        store = EmbeddingStore(
            collection_name=f"thai_sentence_{max_sentences}",
            embedding_fn=CachedEmbedder(embedder, cache),
        )
        store.add_documents(chunks)
        agent = KnowledgeBaseAgent(store=store, llm_fn=extract_first_context)

        query_results = []
        for entry in QUERIES:
            if entry["filter"]:
                retrieved = store.search_with_filter(
                    entry["query"], top_k=3, metadata_filter=entry["filter"]
                )
            else:
                retrieved = store.search(entry["query"], top_k=3)
            compact = [compact_result(item, entry["relevant"]) for item in retrieved]
            relevant_rank = next(
                (rank for rank, item in enumerate(compact, start=1) if item["relevant"]), None
            )
            query_results.append(
                {
                    "id": entry["id"],
                    "query": entry["query"],
                    "filter": entry["filter"],
                    "relevant_rank": relevant_rank,
                    "top3": compact,
                    "agent_mode": "extractive Context 1 (no production LLM)",
                    "agent_answer_excerpt": " ".join(
                        agent.answer(entry["query"], top_k=3).split()
                    )[:500],
                }
            )

        cancellation = QUERIES[0]
        unfiltered = store.search(cancellation["query"], top_k=3)
        filtered = store.search_with_filter(
            cancellation["query"], top_k=3, metadata_filter=cancellation["filter"]
        )
        lengths = [len(chunk.content) for chunk in chunks]
        benchmark[str(max_sentences)] = {
            "chunk_count": len(chunks),
            "avg_chunk_length": round(sum(lengths) / len(lengths), 2),
            "max_chunk_length": max(lengths),
            "top3_relevant": sum(result["relevant_rank"] is not None for result in query_results),
            "top1_relevant": sum(result["relevant_rank"] == 1 for result in query_results),
            "queries": query_results,
            "cancellation_filter_comparison": {
                "unfiltered": [compact_result(item, cancellation["relevant"]) for item in unfiltered],
                "buyer_filtered": [compact_result(item, cancellation["relevant"]) for item in filtered],
            },
        }

    baseline = {}
    selected_doc_ids = {
        "shopee-order-cancellation",
        "shopee-return-refund-policy",
        "shopee-terms-of-service",
    }
    comparator = ChunkingStrategyComparator()
    for document in documents:
        if document.id not in selected_doc_ids:
            continue
        comparison = comparator.compare(document.content, chunk_size=500)
        baseline[document.id] = {
            name: {
                "count": values["count"],
                "avg_length": round(values["avg_length"], 2),
                "max_length": max((len(chunk) for chunk in values["chunks"]), default=0),
            }
            for name, values in comparison.items()
        }

    return {
        "member": {"name": "Nguyễn Duy Thái", "student_id": "2A202601552"},
        "embedding_backend": embedder._backend_name,
        "prediction_rule": "cao nếu cosine >= 0.5; thấp nếu cosine < 0.5",
        "similarity_predictions_locked_before_scoring": pair_results,
        "sentence_benchmark": benchmark,
        "baseline_comparator_chunk_size_500": baseline,
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
