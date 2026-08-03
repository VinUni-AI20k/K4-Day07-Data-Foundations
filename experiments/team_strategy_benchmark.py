"""Reproducible cross-member retrieval benchmark for the final team report.

All strategies are evaluated with the same corpus, five queries, evidence
rules, and multilingual embedding backend. Raw cosine scores are retained for
traceability but are not used to compare runs made with another backend.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingest import chunk_document, load_documents
from src import (
    EmbeddingStore,
    FixedSizeChunker,
    LocalEmbedder,
    MarkdownHeadingChunker,
    SentenceChunker,
)


QUERIES = [
    {
        "id": 1,
        "query": (
            "Đơn hàng do đơn vị vận chuyển không phải SPX đang ở trạng thái “Chờ lấy hàng” "
            "thì Người mua có thể hủy ngay không?"
        ),
        "doc_id": "shopee-order-cancellation",
        "relevance_terms": ["chờ lấy hàng"],
        "complete_terms": ["chờ lấy hàng", "chờ phản hồi", "từ chối"],
        "metadata_filter": {"customer_role": "buyer"},
    },
    {
        "id": 2,
        "query": (
            "Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn được giao "
            "thành công, và thời hạn riêng cho thực phẩm tươi sống hoặc đông lạnh là bao lâu?"
        ),
        "doc_id": "shopee-return-refund-policy",
        "relevance_terms": ["15 (mười lăm) ngày", "24 giờ"],
        "complete_terms": ["15 (mười lăm) ngày", "24 giờ"],
    },
    {
        "id": 3,
        "query": (
            "Ảnh sản phẩm đăng bán trên Shopee phải đáp ứng yêu cầu tối thiểu nào về ảnh thật "
            "và tỷ lệ diện tích sản phẩm?"
        ),
        "doc_id": "shopee-product-listing-rules",
        "relevance_terms": ["tự chụp", "40%"],
        "complete_terms": ["tự chụp", "40%"],
    },
    {
        "id": 4,
        "query": (
            "Vi phạm Chính sách Cấm/Hạn chế Sản phẩm có thể khiến Người bán chịu những nhóm "
            "chế tài nào?"
        ),
        "doc_id": "shopee-prohibited-products-policy",
        "relevance_terms": ["sản phẩm bị xóa", "tài khoản bị giới hạn", "phong tỏa quyền rút tiền"],
        "complete_terms": [
            "sản phẩm bị xóa",
            "tài khoản bị giới hạn",
            "tài khoản bị đình chỉ",
            "phong tỏa quyền rút tiền",
            "xử lý hình sự",
        ],
    },
    {
        "id": 5,
        "query": (
            "Nếu Người mua không nhấn “Đã nhận được hàng” hoặc “Trả hàng/Hoàn tiền”, Shopee "
            "chuyển tiền cho Người bán sớm nhất khi nào?"
        ),
        "doc_id": "shopee-terms-of-service",
        "relevance_terms": ["ngày thứ 04"],
        "complete_terms": ["ngày thứ 04", "nghi ngờ thực hiện hành vi gian lận"],
    },
]


class LongBranchRecursiveChunker:
    """Exact recursive behavior committed by Nguyen Hoang Long at 283e835.

    It recursively emits every separated piece instead of repacking adjacent
    pieces. Keeping it in the experiment (not in ``src``) makes the member run
    reproducible without replacing the selected shared implementation.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, list(self.DEFAULT_SEPARATORS))

    def _split(self, text: str, separators: list[str]) -> list[str]:
        text = text.strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        if not separators:
            return [
                text[start : start + self.chunk_size].strip()
                for start in range(0, len(text), self.chunk_size)
                if text[start : start + self.chunk_size].strip()
            ]
        separator, remaining = separators[0], separators[1:]
        if separator == "":
            return self._split(text, [])
        parts = [part for part in text.split(separator) if part.strip()]
        if len(parts) <= 1:
            return self._split(text, remaining)
        chunks: list[str] = []
        for part in parts:
            chunks.extend(self._split(part, remaining))
        return chunks


class BatchCachingEmbedder:
    """SentenceTransformer wrapper that batches corpus encoding for speed."""

    def __init__(self) -> None:
        self.base = LocalEmbedder()
        self._backend_name = self.base._backend_name
        self.cache: dict[str, list[float]] = {}

    def prepare(self, texts: list[str]) -> None:
        unseen = list(dict.fromkeys(text for text in texts if text not in self.cache))
        if not unseen:
            return
        vectors = self.base.model.encode(
            unseen,
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        for text, vector in zip(unseen, vectors):
            self.cache[text] = vector.tolist()

    def __call__(self, text: str) -> list[float]:
        if text not in self.cache:
            self.cache[text] = self.base(text)
        return self.cache[text]


def _is_relevant(result: dict, benchmark: dict) -> bool:
    if result["metadata"].get("doc_id") != benchmark["doc_id"]:
        return False
    content = result["content"].lower()
    return any(term in content for term in benchmark["relevance_terms"])


def _has_complete_evidence(results: list[dict], benchmark: dict) -> bool:
    gold_text = "\n".join(
        result["content"].lower()
        for result in results
        if result["metadata"].get("doc_id") == benchmark["doc_id"]
    )
    return all(term in gold_text for term in benchmark["complete_terms"])


def _configuration_label(parameters: dict) -> str:
    return ", ".join(f"{key}={value}" for key, value in parameters.items())


def evaluate_configuration(
    documents: list,
    embedder: BatchCachingEmbedder,
    strategy: str,
    parameters: dict,
    chunker,
) -> dict:
    chunk_docs = []
    for document in documents:
        chunk_docs.extend(chunk_document(document, chunker))
    contents = [document.content for document in chunk_docs]
    embedder.prepare(contents)

    collection = f"team_{strategy}_{'_'.join(str(value) for value in parameters.values())}"
    store = EmbeddingStore(collection_name=collection, embedding_fn=embedder)
    store.add_documents(chunk_docs)

    query_results = []
    top1_relevant = 0
    top3_relevant = 0
    complete_in_top3 = 0
    for benchmark in QUERIES:
        metadata_filter = benchmark.get("metadata_filter")
        results = (
            store.search_with_filter(benchmark["query"], 3, metadata_filter)
            if metadata_filter
            else store.search(benchmark["query"], 3)
        )
        relevance = [_is_relevant(result, benchmark) for result in results]
        ranks = [rank for rank, relevant in enumerate(relevance, 1) if relevant]
        complete = _has_complete_evidence(results, benchmark)
        top1_relevant += bool(ranks and ranks[0] == 1)
        top3_relevant += bool(ranks)
        complete_in_top3 += complete
        query_results.append(
            {
                "query_id": benchmark["id"],
                "first_relevant_rank": ranks[0] if ranks else None,
                "complete_evidence_in_top3": complete,
                "top3": [
                    {
                        "rank": rank,
                        "doc_id": result["metadata"].get("doc_id"),
                        "chunk_index": result["metadata"].get("chunk_index"),
                        "score": round(float(result["score"]), 6),
                        "relevant": relevance[rank - 1],
                        "preview": result["content"][:240].replace("\n", " "),
                    }
                    for rank, result in enumerate(results, 1)
                ],
            }
        )

    cancellation = QUERIES[0]
    unfiltered = store.search(cancellation["query"], 3)
    filtered = store.search_with_filter(
        cancellation["query"], 3, cancellation["metadata_filter"]
    )
    lengths = [len(content) for content in contents]
    return {
        "strategy": strategy,
        "parameters": parameters,
        "configuration": _configuration_label(parameters),
        "chunk_count": len(lengths),
        "avg_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "max_length": max(lengths, default=0),
        "top1_relevant": top1_relevant,
        "top3_relevant": top3_relevant,
        "complete_evidence_in_top3": complete_in_top3,
        "queries": query_results,
        "filter_impact": {
            "unfiltered_doc_ids": [item["metadata"].get("doc_id") for item in unfiltered],
            "filtered_doc_ids": [item["metadata"].get("doc_id") for item in filtered],
            "unfiltered_first_relevant_rank": next(
                (rank for rank, item in enumerate(unfiltered, 1) if _is_relevant(item, cancellation)),
                None,
            ),
            "filtered_first_relevant_rank": next(
                (rank for rank, item in enumerate(filtered, 1) if _is_relevant(item, cancellation)),
                None,
            ),
        },
    }


def run(data_dir: Path) -> dict:
    documents = load_documents(data_dir)
    embedder = BatchCachingEmbedder()
    definitions = [
        ("fixed_size", {"chunk_size": 500, "overlap": 50}, FixedSizeChunker(500, 50)),
        ("fixed_size", {"chunk_size": 800, "overlap": 100}, FixedSizeChunker(800, 100)),
        ("fixed_size", {"chunk_size": 1200, "overlap": 150}, FixedSizeChunker(1200, 150)),
        ("sentence", {"max_sentences": 3}, SentenceChunker(3)),
        ("sentence", {"max_sentences": 5}, SentenceChunker(5)),
        ("sentence", {"max_sentences": 8}, SentenceChunker(8)),
        ("markdown_heading", {"chunk_size": 500}, MarkdownHeadingChunker(500)),
        ("long_recursive_commit", {"chunk_size": 500}, LongBranchRecursiveChunker(500)),
        ("long_recursive_commit", {"chunk_size": 800}, LongBranchRecursiveChunker(800)),
        ("long_recursive_commit", {"chunk_size": 1200}, LongBranchRecursiveChunker(1200)),
    ]
    configurations = [
        evaluate_configuration(documents, embedder, strategy, parameters, chunker)
        for strategy, parameters, chunker in definitions
    ]

    def quality_key(item: dict) -> tuple:
        return (
            item["top3_relevant"],
            item["top1_relevant"],
            item["complete_evidence_in_top3"],
            -item["max_length"],
            -item["chunk_count"],
        )

    selected_by_strategy = {}
    for item in configurations:
        current = selected_by_strategy.get(item["strategy"])
        if current is None or quality_key(item) > quality_key(current):
            selected_by_strategy[item["strategy"]] = item
    overall = max(selected_by_strategy.values(), key=quality_key)
    return {
        "run_date": "2026-08-03",
        "corpus": str(data_dir).replace("\\", "/"),
        "embedding_backend": embedder._backend_name,
        "embedding_dimension": len(embedder("dimension check")),
        "selection_priority": [
            "top3_relevant",
            "top1_relevant",
            "complete_evidence_in_top3",
            "lower max_length",
            "lower chunk_count",
        ],
        "configurations": configurations,
        "selected_by_strategy": {
            strategy: {
                key: value
                for key, value in item.items()
                if key not in {"queries", "filter_impact"}
            }
            for strategy, item in selected_by_strategy.items()
        },
        "overall_selected": {
            key: value
            for key, value in overall.items()
            if key not in {"queries", "filter_impact"}
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path("data/k4_ecommerce"))
    parser.add_argument(
        "--output", type=Path, default=Path("report/team_benchmark.json")
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    payload = run(args.data_dir)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
