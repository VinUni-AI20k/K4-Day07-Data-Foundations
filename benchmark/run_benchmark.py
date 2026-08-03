#!/usr/bin/env python3
"""Chạy bộ benchmark 5 câu trên MỘT solution package + chiến lược chunking + embedder.

Mục tiêu: mỗi thành viên trỏ vào package của mình để tự chấm phần "Chất lượng
truy xuất" (top-3 có chunk liên quan?) và so sánh trong nhóm (competition).

Ví dụ:
    # Chỉ định package cần chấm; mock chỉ để thử plumbing
    python benchmark/run_benchmark.py --package src.K4_2A202601184_DaoMinhChien \
        --data-dir data/k4_asos_products

    # Package cá nhân + embedder thật (chấm điểm có ý nghĩa)
    LAB_SOLUTION_PACKAGE=src.K4_2A202601078_VuHuuAn \
    EMBEDDING_PROVIDER=local \
    python benchmark/run_benchmark.py --data-dir data/k4_asos_products --chunker recursive

    # In bảng Markdown để dán vào REPORT_NHOM.md
    python benchmark/run_benchmark.py --package src.K4_2A202601184_DaoMinhChien \
        --data-dir data/k4_asos_products --markdown

    # Benchmark chính thức của nhóm với BGE-M3
    LOCAL_EMBEDDING_MODEL=BAAI/bge-m3 EMBEDDING_PROVIDER=local \
    python benchmark/run_benchmark.py --data-dir data/k4_asos_products --chunker heading --markdown

LƯU Ý: với embedder `mock`, điểm tương tự là NHIỄU nên top-3 vô nghĩa — chỉ dùng để
kiểm tra pipeline. Chấm điểm thật cần EMBEDDING_PROVIDER=local (hoặc openai).
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys
from pathlib import Path

# Cho phép chạy trực tiếp (python benchmark/run_benchmark.py) lẫn -m benchmark.run_benchmark
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.queries import BENCHMARK  # noqa: E402
from ingest import load_documents  # noqa: E402  (chỉ dùng để parse front matter → Document)


def select_embedder(package, provider: str):
    """Chọn backend nhúng từ chính solution package (mock | local | openai)."""
    provider = (provider or "mock").strip().lower()
    if provider == "local":
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "").strip()
        return package.LocalEmbedder(model_name=model_name) if model_name else package.LocalEmbedder()
    if provider == "openai":
        return package.OpenAIEmbedder()
    return package._mock_embed


def make_chunker(package, name: str, chunk_size: int):
    name = (name or "recursive").strip().lower()
    if name == "fixed":
        return package.FixedSizeChunker(chunk_size=chunk_size)
    if name == "sentence":
        return package.SentenceChunker()
    if name == "recursive":
        return package.RecursiveChunker(chunk_size=chunk_size)
    if name == "heading":
        chunker_class = getattr(package, "HeadingRecursiveChunker", None)
        if chunker_class is None:
            raise SystemExit(f"Package '{package.__name__}' không cung cấp HeadingRecursiveChunker")
        return chunker_class(chunk_size=chunk_size)
    raise SystemExit(f"Unknown --chunker '{name}' (dùng: fixed | sentence | recursive | heading)")


def build_store(package, data_dir: str, chunker, embedder):
    """Nạp corpus qua chunker + EmbeddingStore CỦA package đang chấm (không hardcode src)."""
    Document = package.Document
    store = package.EmbeddingStore(collection_name="benchmark", embedding_fn=embedder)
    chunk_docs = []
    for doc in load_documents(data_dir):
        for index, piece in enumerate(chunker.chunk(doc.content)):
            meta = dict(doc.metadata)
            meta["doc_id"] = doc.id          # doc_id GỐC để chấm khớp expected_doc_ids
            meta["chunk_index"] = index
            chunk_docs.append(Document(id=f"{doc.id}::chunk_{index}", content=piece, metadata=meta))
    store.add_documents(chunk_docs)
    return store, len(chunk_docs)


def base_doc_of(result: dict) -> str:
    """doc_id gốc của một kết quả (metadata['doc_id'] được gắn khi ingest)."""
    return (result.get("metadata") or {}).get("doc_id") or result.get("doc_id") or ""


def score_query(store, item: dict, top_k: int) -> dict:
    """Chạy một câu hỏi và tự chấm phần retrieval trong đúng ba kết quả đầu."""
    mfilter = item.get("metadata_filter")
    if mfilter:
        results = store.search_with_filter(item["query"], top_k=top_k, metadata_filter=mfilter)
    else:
        results = store.search(item["query"], top_k=top_k)

    expected = set(item["expected_doc_ids"])
    top_docs = [base_doc_of(r) for r in results]
    top_three_docs = top_docs[:3]
    is_multi_result = len(expected) > 1
    hit_top1 = not is_multi_result and bool(top_docs) and top_docs[0] in expected
    if is_multi_result:
        hit_top3 = expected.issubset(set(top_three_docs))
    else:
        hit_top3 = any(doc_id in expected for doc_id in top_three_docs)

    if hit_top1:
        outcome, retrieval_pts = "TOP-1", 1
    elif hit_top3:
        outcome, retrieval_pts = "TOP-3", 1
    else:
        outcome, retrieval_pts = "MISS", 0

    return {
        "results": results,
        "top_docs": top_docs,
        "outcome": outcome,
        "retrieval_pts": retrieval_pts,
    }


def run(args) -> int:
    package_name = os.getenv("LAB_SOLUTION_PACKAGE") or args.package
    provider = os.getenv("EMBEDDING_PROVIDER", args.provider)
    if not package_name:
        print(
            "Hãy truyền --package hoặc đặt LAB_SOLUTION_PACKAGE tới package cá nhân cần chấm.",
            file=sys.stderr,
        )
        return 2
    package = importlib.import_module(package_name)

    if not Path(args.data_dir).exists():
        print(f"Không tìm thấy thư mục dữ liệu: {args.data_dir}", file=sys.stderr)
        print("Corpus K4 nằm trên branch data (data/k4_asos_products). Merge/checkout data trước.", file=sys.stderr)
        return 2

    embedder = select_embedder(package, provider)
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    chunker = make_chunker(package, args.chunker, args.chunk_size)
    store, n_chunks = build_store(package, args.data_dir, chunker, embedder)

    rows = [(item, score_query(store, item, args.top_k)) for item in BENCHMARK]
    total = sum(r["retrieval_pts"] for _, r in rows)

    if args.markdown:
        _print_markdown(package_name, chunker, backend, rows, total)
    else:
        _print_text(package_name, chunker, backend, n_chunks, provider, rows, total)
    return 0


def _print_text(package_name, chunker, backend, n_chunks, provider, rows, total):
    print(f"Package   : {package_name}")
    print(f"Chunker   : {chunker.__class__.__name__}")
    print(f"Embedder  : {backend}")
    print(f"Chunks    : {n_chunks}")
    if backend == "mock embeddings fallback":
        print("!! mock = NHIỄU: top-3 không phản ánh chất lượng ngữ nghĩa. Dùng EMBEDDING_PROVIDER=local để chấm.")
    print("-" * 78)
    for item, r in rows:
        flt = f"  filter={item['metadata_filter']}" if item["metadata_filter"] else ""
        print(f"[Q{item['id']}] {item['type']}{flt}")
        print(f"   Query : {item['query']}")
        print(f"   Gold  : {item['gold_answer']}")
        print(f"   Top-{len(r['top_docs'])}:")
        for rank, res in enumerate(r["results"], start=1):
            hit = "*" if base_doc_of(res) in set(item["expected_doc_ids"]) else " "
            print(f"     {hit}{rank}. score={res['score']:+.3f}  {base_doc_of(res)}")
        print(f"   => {r['outcome']} | retrieval-auto={r['retrieval_pts']}/1 "
              "(điểm thứ hai cần Agent answer đúng — người chấm xác nhận)")
        print("-" * 78)
    print(f"TỔNG retrieval tự động: {total}/5   [điểm cuối /10 cần xác nhận Agent answer]")


def _print_markdown(package_name, chunker, backend, rows, total):
    print(f"**Package:** `{package_name}` · **Chunker:** {chunker.__class__.__name__} · **Embedder:** {backend}\n")
    print("| # | Câu hỏi | Filter | Top-1 doc truy xuất | Có chunk liên quan trong top-3? | Điểm retrieval |")
    print("|---|---------|--------|---------------------|-------------------------------|----------------|")
    for item, r in rows:
        top1 = r["top_docs"][0] if r["top_docs"] else "—"
        flt = str(item["metadata_filter"]) if item["metadata_filter"] else "—"
        yn = "✅" if r["outcome"] in ("TOP-1", "TOP-3") else "❌"
        print(f"| {item['id']} | {item['query_vi']} | {flt} | `{top1}` | {yn} ({r['outcome']}) | {r['retrieval_pts']}/1 |")
    print(f"\n**Tổng retrieval tự động: {total}/5** — điểm còn lại mỗi câu cần Agent answer khớp gold.")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Chấm bộ benchmark 5 câu trên 1 solution package/chiến lược.")
    p.add_argument("--data-dir", default="data/k4_asos_products", help="Thư mục corpus (mặc định data/k4_asos_products)")
<<<<<<< HEAD
    p.add_argument("--package", default="src", help="Solution package (ghi đè bằng env LAB_SOLUTION_PACKAGE)")
    p.add_argument("--chunker", default="recursive", help="fixed | sentence | recursive | heading")
=======
    p.add_argument("--package", help="Solution package; cũng có thể đặt bằng env LAB_SOLUTION_PACKAGE")
    p.add_argument("--chunker", default="recursive", help="fixed | sentence | recursive")
>>>>>>> d1b69550a0c6e68e5d4accdb1ca374febfffddac
    p.add_argument("--chunk-size", type=int, default=400, help="chunk_size cho fixed/recursive")
    p.add_argument("--provider", default="mock", help="mock | local | openai (ghi đè bằng env EMBEDDING_PROVIDER)")
    p.add_argument("--top-k", type=int, default=3, help="Số kết quả top-k (mặc định 3 theo rubric)")
    p.add_argument("--markdown", action="store_true", help="In bảng Markdown để dán vào REPORT_NHOM.md")
    return p.parse_args()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(run(parse_args()))
