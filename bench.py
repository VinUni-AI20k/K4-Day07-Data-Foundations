from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from ingest import build_knowledge_base
from src import LocalEmbedder, RecursiveChunker


DATA_DIR = Path("data/tiktok_shop_after_sales")
BENCHMARK_PATH = Path("benchmarks/tiktok_shop_after_sales.json")


class HeadingChunker:
    """Keep each Markdown heading with its section and recursively split long bodies."""

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = max(1, chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        chunks: list[str] = []
        for block in re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE):
            block = block.strip()
            if not block:
                continue
            if len(block) <= self.chunk_size:
                chunks.append(block)
                continue

            first_line, separator, body = block.partition("\n")
            if separator and first_line.startswith("#"):
                body_size = max(1, self.chunk_size - len(first_line) - 2)
                pieces = RecursiveChunker(chunk_size=body_size).chunk(body)
                chunks.extend(f"{first_line}\n\n{piece}" for piece in pieces)
            else:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(block))
        return chunks


def _result_summary(result: dict) -> dict:
    return {
        "score": round(float(result["score"]), 6),
        "doc_id": result["metadata"].get("doc_id"),
        "chunk_index": result["metadata"].get("chunk_index"),
        "preview": result["content"][:180].replace("\n", " "),
    }


def run_benchmark(chunk_size: int = 500) -> dict:
    benchmarks = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))
    embedder = LocalEmbedder()
    store = build_knowledge_base(DATA_DIR, embedder, chunker=HeadingChunker(chunk_size))

    runs = []
    for item in benchmarks:
        unfiltered = store.search(item["query"], top_k=3)
        filtered = store.search_with_filter(
            item["query"], top_k=3, metadata_filter=item["metadata_filter"]
        )
        evidence = item["evidence_phrase"].casefold()
        runs.append(
            {
                **item,
                "unfiltered_hit": any(evidence in result["content"].casefold() for result in unfiltered),
                "filtered_hit": any(evidence in result["content"].casefold() for result in filtered),
                "unfiltered_top3": [_result_summary(result) for result in unfiltered],
                "filtered_top3": [_result_summary(result) for result in filtered],
            }
        )

    return {
        "strategy": "heading_with_recursive_fallback",
        "chunk_size": chunk_size,
        "embedding_model": embedder._backend_name,
        "collection_size": store.get_collection_size(),
        "runs": runs,
    }


def self_check() -> None:
    sample = "# Mục một\n\n" + ("Nội dung dài. " * 80) + "\n\n# Mục hai\n\nNgắn."
    chunks = HeadingChunker(chunk_size=160).chunk(sample)
    assert len(chunks) > 2
    assert all(len(chunk) <= 160 for chunk in chunks)
    assert all(chunk.startswith("# Mục") for chunk in chunks)
    print(f"HeadingChunker self-check: PASS ({len(chunks)} chunks)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the personal Lab 07 retrieval benchmark.")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return 0
    print(json.dumps(run_benchmark(args.chunk_size), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
