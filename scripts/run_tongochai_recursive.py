"""Run the frozen team benchmark with Tô Ngọc Hải's RecursiveChunker package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingest import chunk_document, load_documents
from scripts.run_benchmark import (
    evaluate_case,
    format_result,
    grounded_answer,
    load_benchmark_cases,
    load_local_embedder,
    print_summary,
)
from src.K4_2A202601686_ToNgocHai import EmbeddingStore, RecursiveChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Tô Ngọc Hải's recursive benchmark.")
    parser.add_argument("--data-dir", default="data/k4_ecommerce")
    parser.add_argument("--output", default="results/ToNgocHai_recursive.json")
    parser.add_argument("--chunk-size", type=int, default=500)
    return parser.parse_args()


def run(args: argparse.Namespace) -> dict:
    benchmark = load_benchmark_cases()
    embedder = load_local_embedder()
    chunker = RecursiveChunker(chunk_size=args.chunk_size)

    chunks = []
    for document in load_documents(args.data_dir):
        chunks.extend(chunk_document(document, chunker))
    store = EmbeddingStore(
        collection_name=f"tongochai_recursive_{args.chunk_size}",
        embedding_fn=embedder,
    )
    store.add_documents(chunks)

    cases = []
    for case in benchmark["cases"]:
        query = case["query"]
        unfiltered = [
            format_result(result, rank)
            for rank, result in enumerate(store.search(query, top_k=3), start=1)
        ]
        metadata_filter = case.get("metadata_filter") or {}
        official = [
            format_result(result, rank)
            for rank, result in enumerate(
                store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter),
                start=1,
            )
        ] if metadata_filter else unfiltered
        answer = grounded_answer(query, official)
        cases.append({
            "id": case["id"],
            "query": query,
            "gold_answer": case["gold_answer"],
            "expected_doc_id": case["expected_doc_id"],
            "metadata_filter": metadata_filter,
            "top_1": official[0] if len(official) > 0 else {},
            "top_2": official[1] if len(official) > 1 else {},
            "top_3": official[2] if len(official) > 2 else {},
            "unfiltered_top_3": unfiltered,
            "agent_answer": answer,
            **evaluate_case(case, official, answer),
        })

    top1_scores = [case["top_1"]["score"] for case in cases if case["top_1"]]
    return {
        "benchmark_version": benchmark["benchmark_version"],
        "member": "Tô Ngọc Hải",
        "student_id": "2A202601686",
        "solution_package": "src.K4_2A202601686_ToNgocHai",
        "strategy": "RecursiveChunker",
        "chunker_config": {"chunk_size": args.chunk_size},
        "embedding_model": LOCAL_EMBEDDING_MODEL,
        "data_dir": args.data_dir,
        "chunk_count": len(chunks),
        "cases": cases,
        "summary": {
            "queries_run": len(cases),
            "top3_hits": sum(case["relevant_in_top3"] for case in cases),
            "top1_hits": sum(case["expected_doc_rank"] == 1 for case in cases),
            "retrieval_points": sum(case["retrieval_point"] for case in cases),
            "maximum_points": len(cases) * 2,
            "average_top1_score": sum(top1_scores) / len(top1_scores) if top1_scores else 0.0,
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    results = run(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print_summary(results)
    print(f"  chunks: {results['chunk_count']}")
    print(f"Saved results to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
