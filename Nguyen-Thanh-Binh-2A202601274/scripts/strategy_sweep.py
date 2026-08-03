"""
Quét nhiều chiến lược chunking và CHẤM ĐIỂM tự động theo rubric docs/SCORING.md.

Mỗi câu hỏi:
    2đ — chunk chứa gold ở #1 VÀ agent trả lời đúng
    1đ — chunk chứa gold trong top-3 nhưng không ở #1, HOẶC agent trả lời sai
    0đ — chunk chứa gold không có trong top-3

Chạy (PowerShell):
    $env:EMBEDDING_PROVIDER="local"; .venv/Scripts/python scripts/strategy_sweep.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent.parent  # thư mục cá nhân của tôi
REPO_ROOT = BUNDLE_ROOT.parent  # repo chung của nhóm
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BUNDLE_ROOT))  # src/ của RIÊNG tôi — ưu tiên cao hơn

from ingest import build_knowledge_base  # noqa: E402
from main import _select_embedder  # noqa: E402
from scripts.retrieval_benchmark import (  # noqa: E402
    BENCHMARK,
    DATA_DIR,
    _normalize,
    extractive_stub_llm,
    hit_rank,
)
from src import (  # noqa: E402
    FixedSizeChunker,
    KnowledgeBaseAgent,
    RecursiveChunker,
    SentenceChunker,
)
from src.chunking import ClauseChunker  # noqa: E402

CANDIDATES = {
    "fixed_size(500,50)": lambda: FixedSizeChunker(chunk_size=500, overlap=50),
    "fixed_size(200,40)": lambda: FixedSizeChunker(chunk_size=200, overlap=40),
    "by_sentences(3)": lambda: SentenceChunker(max_sentences_per_chunk=3),
    "by_sentences(2)": lambda: SentenceChunker(max_sentences_per_chunk=2),
    "by_sentences(1)": lambda: SentenceChunker(max_sentences_per_chunk=1),
    "recursive(400)": lambda: RecursiveChunker(chunk_size=400),
    "recursive(200)": lambda: RecursiveChunker(chunk_size=200),
    "recursive(120)": lambda: RecursiveChunker(chunk_size=120),
    "clause(1 câu)": lambda: ClauseChunker(max_sentences_per_clause=1),
    "clause(2 câu)": lambda: ClauseChunker(max_sentences_per_clause=2),
    "clause(1,no-head)": lambda: ClauseChunker(max_sentences_per_clause=1, keep_heading=False),
    "clause(1,drop-qt)": lambda: ClauseChunker(max_sentences_per_clause=1, drop_quotes=True),
}


def agent_is_correct(answer: str, item: dict) -> bool:
    """Câu trả lời của agent có chứa nguyên văn gold answer không."""
    return _normalize(item["gold_snippet"]) in _normalize(answer)


def score_strategy(name: str, chunker, embedder) -> dict:
    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker, collection_name=name)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_stub_llm)

    total, ranks, agent_flags = 0, [], []
    for item in BENCHMARK:
        results = store.search_with_filter(item["query"], top_k=3, metadata_filter=item["filter"])
        rank = hit_rank(results, item)
        answer = agent.answer(item["query"], top_k=3, metadata_filter=item["filter"])
        correct = agent_is_correct(answer, item)

        if rank == 0:
            points = 0
        elif rank == 1 and correct:
            points = 2
        else:
            points = 1

        total += points
        ranks.append(rank)
        agent_flags.append(correct)

    return {
        "name": name,
        "chunks": store.get_collection_size(),
        "ranks": ranks,
        "agent": agent_flags,
        "score": total,
    }


def main() -> int:
    embedder = _select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Backend nhúng: {backend}")
    if backend == "mock embeddings fallback":
        print("CẢNH BÁO: đang dùng mock — kết quả không có ý nghĩa ngữ nghĩa.\n")

    rows = [score_strategy(name, factory(), embedder) for name, factory in CANDIDATES.items()]

    header = f"{'Chiến lược':<20}{'#chunk':<9}" + "".join(f"Q{i:<5}" for i in range(1, 6)) + f"{'Agent đúng':<13}Điểm"
    print(header)
    print("-" * len(header))
    for row in sorted(rows, key=lambda r: -r["score"]):
        cells = "".join(f"{('#' + str(r)) if r else 'trượt':<6}" for r in row["ranks"])
        agent_cells = "".join("✔" if flag else "✘" for flag in row["agent"])
        print(f"{row['name']:<20}{row['chunks']:<9}{cells}{agent_cells:<13}{row['score']}/10")

    best = max(rows, key=lambda r: r["score"])
    print(f"\nCao nhất: {best['name']} — {best['score']}/10")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
