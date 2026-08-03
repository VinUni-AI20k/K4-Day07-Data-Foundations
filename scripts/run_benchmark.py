from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ingest import build_knowledge_base
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.document_aware_chunker import DocumentAwareChunker
from src.embeddings import LOCAL_EMBEDDING_MODEL, LocalEmbedder

BENCHMARK_PATH = ROOT_DIR / "config" / "benchmark_cases.json"
INSUFFICIENT_ANSWER = "Không đủ thông tin trong corpus."
STOPWORDS = {
    "có",
    "cho",
    "của",
    "để",
    "điều",
    "gì",
    "hoặc",
    "khi",
    "là",
    "mất",
    "nào",
    "nếu",
    "như",
    "ra",
    "sao",
    "thế",
    "trong",
    "và",
    "về",
    "với",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the shared ARAMHONLOAN K4 benchmark.")
    parser.add_argument("--strategy", default="document-aware", choices=["document-aware", "fixed", "sentence", "recursive"])
    parser.add_argument("--data-dir", default="data/k4_ecommerce")
    parser.add_argument("--output", default="results/NguyenDucAnh_document_aware.json")
    parser.add_argument("--max-chunk-size", type=int, default=700)
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--max-sentences", type=int, default=3)
    parser.add_argument("--member", default="Nguyễn Đức Anh")
    return parser.parse_args()


def load_benchmark_cases(path: Path = BENCHMARK_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        benchmark = json.load(handle)
    cases = benchmark.get("cases", [])
    if benchmark.get("benchmark_version") != "aramhonloan-k4-v1":
        raise ValueError("Unexpected benchmark version.")
    if benchmark.get("frozen") is not True:
        raise ValueError("Benchmark file must be frozen.")
    if len(cases) != 5:
        raise ValueError(f"Expected exactly 5 benchmark cases, found {len(cases)}.")
    return benchmark


def build_chunker(args: argparse.Namespace):
    if args.strategy == "document-aware":
        return (
            DocumentAwareChunker(max_chunk_size=args.max_chunk_size),
            "Structure-Based / Document-Aware Chunking",
            {"max_chunk_size": args.max_chunk_size},
        )
    if args.strategy == "fixed":
        return (
            FixedSizeChunker(chunk_size=args.chunk_size, overlap=args.overlap),
            "FixedSizeChunker",
            {"chunk_size": args.chunk_size, "overlap": args.overlap},
        )
    if args.strategy == "sentence":
        return (
            SentenceChunker(max_sentences_per_chunk=args.max_sentences),
            "SentenceChunker",
            {"max_sentences_per_chunk": args.max_sentences},
        )
    if args.strategy == "recursive":
        return (
            RecursiveChunker(chunk_size=args.chunk_size),
            "RecursiveChunker",
            {"chunk_size": args.chunk_size},
        )
    raise ValueError(f"Unsupported strategy: {args.strategy}")


def load_local_embedder() -> LocalEmbedder:
    try:
        return LocalEmbedder(model_name=LOCAL_EMBEDDING_MODEL)
    except Exception as exc:
        raise RuntimeError(
            "LocalEmbedder is required for benchmark runs and could not be loaded. "
            "Install requirements-local.txt and ensure the SentenceTransformer model is available. "
            f"Original error: {exc}"
        ) from exc


def format_result(result: dict[str, Any], rank: int) -> dict[str, Any]:
    metadata = json_safe(dict(result.get("metadata", {})))
    return {
        "rank": rank,
        "score": float(result.get("score", 0.0)),
        "doc_id": metadata.get("doc_id", result.get("id", "")),
        "chunk_index": metadata.get("chunk_index"),
        "customer_role": metadata.get("customer_role"),
        "category": metadata.get("category"),
        "source_url": metadata.get("source_url", ""),
        "content": result.get("content", ""),
        "metadata": metadata,
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text).lower()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[\w.%]+", normalize_text(text), flags=re.UNICODE))
    return {token for token in tokens if len(token) > 1 and token not in STOPWORDS}


def clean_candidate(text: str) -> str:
    text = re.sub(r"^\s*#{1,6}\s+", "", text.strip())
    text = re.sub(r"^\s*[*+-]\s+", "", text)
    text = text.replace("**", "")
    return re.sub(r"\s+", " ", text).strip()


def candidate_fragments(content: str) -> list[str]:
    fragments: list[str] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("[Heading path:"):
            continue
        if re.match(r"^\s*[*+-]\s+", line):
            cleaned = clean_candidate(line)
            if cleaned:
                fragments.append(cleaned)
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            cleaned = clean_candidate(sentence)
            if cleaned:
                fragments.append(cleaned)
    return fragments


def grounded_answer(query: str, top_results: list[dict[str, Any]]) -> str:
    query_tokens = tokenize(query)
    if not query_tokens:
        return INSUFFICIENT_ANSWER

    scored: list[tuple[int, int, int, str, str]] = []
    for result_index, result in enumerate(top_results):
        doc_id = result.get("doc_id") or result.get("source_url") or "unknown"
        for fragment_index, fragment in enumerate(candidate_fragments(result.get("content", ""))):
            fragment_tokens = tokenize(fragment)
            overlap = len(query_tokens & fragment_tokens)
            if overlap > 0:
                scored.append((overlap, -result_index, -fragment_index, fragment, str(doc_id)))

    if not scored:
        return INSUFFICIENT_ANSWER

    scored.sort(reverse=True)
    selected: list[str] = []
    seen = set()
    for overlap, _result_rank, _fragment_rank, fragment, doc_id in scored:
        key = normalize_text(fragment)
        if key in seen:
            continue
        seen.add(key)
        selected.append(f"{fragment} (Nguồn: {doc_id})")
        if len(selected) == 3:
            break

    return " ".join(selected) if selected else INSUFFICIENT_ANSWER


def fact_found(text: str, fact: str) -> bool:
    return normalize_text(fact) in normalize_text(text)


def evaluate_case(case: dict[str, Any], official_top3: list[dict[str, Any]], agent_answer: str) -> dict[str, Any]:
    expected_doc_id = case["expected_doc_id"]
    expected_doc_rank = None
    for result in official_top3:
        if result.get("doc_id") == expected_doc_id:
            expected_doc_rank = result["rank"]
            break

    required_facts_found = [
        fact
        for fact in case.get("required_facts", [])
        if fact_found(agent_answer, fact)
    ]
    all_facts_found = len(required_facts_found) == len(case.get("required_facts", []))
    grounded = agent_answer != INSUFFICIENT_ANSWER
    relevant_in_top3 = expected_doc_rank is not None

    if not relevant_in_top3:
        retrieval_point = 0
        notes = "Expected document is absent from the official top-3 results."
    elif expected_doc_rank != 1:
        retrieval_point = 1
        notes = "Expected document is present in top-3 but is not top-1."
    elif not all_facts_found:
        retrieval_point = 1
        missing = [fact for fact in case.get("required_facts", []) if fact not in required_facts_found]
        notes = "Expected document is top-1, but the grounded answer is missing required facts: " + ", ".join(missing)
    elif not grounded:
        retrieval_point = 1
        notes = "Expected document is top-1, but the answer is not sufficiently grounded."
    else:
        retrieval_point = 2
        notes = "Expected document is top-1 and the grounded answer contains all required facts."

    return {
        "expected_doc_rank": expected_doc_rank,
        "relevant_in_top3": relevant_in_top3,
        "required_facts_found": required_facts_found,
        "retrieval_point": retrieval_point,
        "notes": notes,
    }


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    benchmark = load_benchmark_cases()
    chunker, strategy_name, chunker_config = build_chunker(args)
    embedder = load_local_embedder()
    data_dir = Path(args.data_dir)
    store = build_knowledge_base(data_dir, embedding_fn=embedder, chunker=chunker)

    result_cases: list[dict[str, Any]] = []
    for case in benchmark["cases"]:
        query = case["query"]
        unfiltered = [format_result(result, rank) for rank, result in enumerate(store.search(query, top_k=3), start=1)]
        metadata_filter = case.get("metadata_filter") or {}
        if metadata_filter:
            official = [
                format_result(result, rank)
                for rank, result in enumerate(
                    store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter),
                    start=1,
                )
            ]
        else:
            official = unfiltered

        agent_answer = grounded_answer(query, official)
        evaluation = evaluate_case(case, official, agent_answer)

        case_result = {
            "id": case["id"],
            "query": query,
            "gold_answer": case["gold_answer"],
            "expected_doc_id": case["expected_doc_id"],
            "metadata_filter": metadata_filter,
            "top_1": official[0] if len(official) >= 1 else {},
            "top_2": official[1] if len(official) >= 2 else {},
            "top_3": official[2] if len(official) >= 3 else {},
            "unfiltered_top_3": unfiltered,
            "agent_answer": agent_answer,
            **evaluation,
        }
        result_cases.append(case_result)

    top1_scores = [
        case["top_1"]["score"]
        for case in result_cases
        if case.get("top_1") and "score" in case["top_1"]
    ]
    summary = {
        "queries_run": len(result_cases),
        "top3_hits": sum(1 for case in result_cases if case["relevant_in_top3"]),
        "top1_hits": sum(1 for case in result_cases if case["expected_doc_rank"] == 1),
        "retrieval_points": sum(case["retrieval_point"] for case in result_cases),
        "maximum_points": len(result_cases) * 2,
        "average_top1_score": sum(top1_scores) / len(top1_scores) if top1_scores else 0.0,
    }

    return {
        "benchmark_version": benchmark["benchmark_version"],
        "member": args.member,
        "strategy": strategy_name,
        "chunker_config": chunker_config,
        "embedding_model": LOCAL_EMBEDDING_MODEL,
        "data_dir": args.data_dir,
        "cases": result_cases,
        "summary": summary,
    }


def print_summary(results: dict[str, Any]) -> None:
    summary = results["summary"]
    print("Benchmark summary")
    print(f"  version: {results['benchmark_version']}")
    print(f"  member: {results['member']}")
    print(f"  strategy: {results['strategy']}")
    print(f"  queries: {summary['queries_run']}")
    print(f"  top-3 hits: {summary['top3_hits']}/{summary['queries_run']}")
    print(f"  top-1 hits: {summary['top1_hits']}/{summary['queries_run']}")
    print(f"  retrieval score: {summary['retrieval_points']}/{summary['maximum_points']}")
    print(f"  average top-1 score: {summary['average_top1_score']:.4f}")
    for case in results["cases"]:
        top_1 = case.get("top_1", {})
        print(
            f"  {case['id']}: top1={top_1.get('doc_id')} "
            f"score={top_1.get('score', 0.0):.4f} "
            f"point={case['retrieval_point']} "
            f"rank={case['expected_doc_rank']}"
        )


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = parse_args()
    try:
        results = run_benchmark(args)
    except Exception as exc:
        print(f"Benchmark failed: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print_summary(results)
    print(f"Saved results to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
