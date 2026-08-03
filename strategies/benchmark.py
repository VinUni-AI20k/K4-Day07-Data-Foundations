"""
strategies/benchmark.py — chạy 5 câu hỏi của nhóm trên MỘT chiến lược, xuất bảng Markdown.

Dùng chung cho cả 3 thành viên: chỉ khác `--package` (package cá nhân) và `--strategy`.

Ví dụ (PowerShell):
    .venv\\Scripts\\python.exe strategies/benchmark.py -p src.2A202601891-DinhQuocViet -s a
    .venv\\Scripts\\python.exe strategies/benchmark.py -p src.2A202601891-DinhQuocViet -s b --top-k 5

Kết quả in ra màn hình và ghi vào report/benchmark_<package>_<strategy>.md —
dán thẳng vào REPORT_CANHAN mục 5 và REPORT_NHOM mục 3.

Cách tự chấm (theo docs/SCORING.md, 2 điểm/câu):
    2 — top-1 thuộc tài liệu gold VÀ câu trả lời của agent chính xác
    1 — gold nằm trong top-3 nhưng không ở top-1, hoặc câu trả lời thiếu chi tiết
    0 — không có chunk liên quan trong top-3
Script chấm tự động phần TRUY XUẤT (dựa trên doc_id). Phần "câu trả lời có chính xác
không" thì người chạy phải tự đối chiếu với gold answer rồi sửa lại cột điểm.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategies.common import (  # noqa: E402
    BENCHMARK_QUERIES,
    DEFAULT_DATA_DIR,
    PROJECT_ROOT,
    build_kb,
    is_mock_backend,
    load_solution_package,
    select_embedder,
)

STRATEGY_ALIASES = {
    "a": "strategies.strategy_a_fixed",
    "b": "strategies.strategy_b_clause",
    "c": "strategies.strategy_c_sentence_ctx",
}


# ---------------------------------------------------------------------------
# Tiện ích hiển thị
# ---------------------------------------------------------------------------
def md_cell(text: str, limit: int = 90) -> str:
    """Rút gọn + thoát ký tự để nhét được vào 1 ô bảng Markdown."""
    flat = " ".join(str(text).split())
    if len(flat) > limit:
        flat = flat[: limit - 1] + "…"
    return flat.replace("|", "\\|")


def resolve_strategy(name: str):
    """Nhận 'a'/'b'/'c' hoặc tên module đầy đủ; trả về biến STRATEGY trong module đó."""
    import importlib

    module_name = STRATEGY_ALIASES.get(name.lower(), name)
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        raise SystemExit(f"Không nạp được chiến lược '{name}' (module {module_name}): {error}")
    if not hasattr(module, "STRATEGY"):
        raise SystemExit(f"Module {module_name} thiếu biến STRATEGY (xem hợp đồng trong common.py).")
    return module.STRATEGY


def make_probe_llm(captured: dict):
    """LLM giả lập: ghi lại prompt để kiểm tra agent có thực sự nhét ngữ cảnh vào không."""

    def probe_llm(prompt: str) -> str:
        captured["prompt"] = prompt
        return f"[STUB LLM] đã nhận {len(prompt)} ký tự ngữ cảnh"

    return probe_llm


def auto_score(results: list[dict], gold_docs: list[str]) -> tuple[int, str]:
    """Chấm phần truy xuất: 2 nếu top-1 đúng tài liệu, 1 nếu gold ở top-3, 0 nếu không."""
    if not results:
        return 0, "không có kết quả"
    doc_ids = [r["metadata"].get("doc_id") for r in results]
    if doc_ids[0] in gold_docs:
        return 2, "top-1 đúng tài liệu gold"
    if any(doc_id in gold_docs for doc_id in doc_ids):
        return 1, "gold ở top-3 nhưng không phải top-1"
    return 0, "không có gold trong top-3"


# ---------------------------------------------------------------------------
# Chạy benchmark
# ---------------------------------------------------------------------------
def run(package_name: str, strategy_name: str, top_k: int, data_dir: Path, out_path: Path | None) -> int:
    package = load_solution_package(package_name)
    strategy = resolve_strategy(strategy_name)
    embedder, backend = select_embedder(package)

    store, stats = build_kb(package, strategy, data_dir=data_dir, embedding_fn=embedder)
    effective_top_k = strategy.top_k or top_k

    captured: dict = {}
    agent = package.KnowledgeBaseAgent(store=store, llm_fn=make_probe_llm(captured))

    lines: list[str] = []
    add = lines.append

    add(f"# Benchmark — chiến lược `{strategy.name}`")
    add("")
    add(f"- **Package cá nhân:** `{package.__name__}`")
    add(f"- **Backend nhúng:** `{backend}`")
    try:
        corpus_label = data_dir.resolve().relative_to(PROJECT_ROOT)
    except ValueError:  # corpus nằm ngoài project
        corpus_label = data_dir
    add(f"- **Corpus:** `{corpus_label}` — {stats['n_docs']} tài liệu")
    add(
        f"- **Chunk:** {stats['n_chunks']} chunk | dài trung bình {stats['avg_length']} "
        f"ký tự (min {stats['min_length']} / max {stats['max_length']})"
    )
    add(f"- **top_k:** {effective_top_k}")
    if strategy.description:
        add(f"- **Mô tả chiến lược:** {strategy.description}")
    if is_mock_backend(backend):
        add("")
        add(
            "> ⚠️ Đang chạy MOCK embedding — điểm số bên dưới KHÔNG phản ánh ngữ nghĩa. "
            "Đặt `EMBEDDING_PROVIDER=local` trong `.env` trước khi lấy số cho báo cáo."
        )
    add("")

    rows_individual: list[str] = []
    rows_detail: list[str] = []
    rows_filter: list[str] = []
    total_score = 0
    hits_in_top3 = 0

    for query in BENCHMARK_QUERIES:
        question = query["question"]
        gold_docs = query["gold_docs"]
        metadata_filter = query["metadata_filter"]

        if metadata_filter:
            results = store.search_with_filter(question, top_k=effective_top_k, metadata_filter=metadata_filter)
            unfiltered = store.search(question, top_k=effective_top_k)
            score_f, _ = auto_score(results, gold_docs)
            score_u, _ = auto_score(unfiltered, gold_docs)
            rows_filter.append(
                f"| {query['id']} | `{metadata_filter}` | {score_u}/2 | {score_f}/2 | "
                f"{md_cell(unfiltered[0]['metadata'].get('doc_id') if unfiltered else '-', 40)} | "
                f"{md_cell(results[0]['metadata'].get('doc_id') if results else '-', 40)} |"
            )
        else:
            results = store.search(question, top_k=effective_top_k)

        score, reason = auto_score(results, gold_docs)
        total_score += score
        if score > 0:
            hits_in_top3 += 1

        captured.clear()
        try:
            answer = agent.answer(question, top_k=effective_top_k)
        except Exception as error:  # để 1 lỗi không làm hỏng cả lượt chạy
            answer = f"[LỖI agent.answer: {error}]"

        prompt = captured.get("prompt", "")
        grounded = "✅" if results and results[0]["content"][:40] in prompt else "❌"

        top1 = results[0] if results else None
        rows_individual.append(
            "| {id} | {question} | {chunk} | {score:.3f} | {relevant} | {answer} |".format(
                id=query["id"],
                question=md_cell(question, 60),
                chunk=md_cell(f"`{top1['id']}` — {top1['content']}" if top1 else "(không có)", 90),
                score=top1["score"] if top1 else 0.0,
                relevant="✅" if score == 2 else ("⚠️" if score == 1 else "❌"),
                answer=md_cell(answer, 60),
            )
        )

        rows_detail.append(f"**Câu {query['id']}: {question}**")
        rows_detail.append(f"gold_docs = `{gold_docs}` | filter = `{metadata_filter}` | tự chấm truy xuất: **{score}/2** ({reason}) | agent nhét ngữ cảnh: {grounded}")
        rows_detail.append("")
        rows_detail.append("| # | chunk_id | score | doc_id | trích 80 ký tự |")
        rows_detail.append("|---|----------|-------|--------|----------------|")
        for rank, result in enumerate(results, start=1):
            rows_detail.append(
                f"| {rank} | `{result['id']}` | {result['score']:.3f} | "
                f"{result['metadata'].get('doc_id')} | {md_cell(result['content'], 80)} |"
            )
        if len(results) >= 2:
            gap = results[0]["score"] - results[-1]["score"]
            rows_detail.append("")
            rows_detail.append(f"Khoảng cách score top-1 → top-{len(results)}: **{gap:.3f}** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)")
        rows_detail.append("")

    add("## Bảng 1 — Kết quả cá nhân (dán vào REPORT_CANHAN mục 5)")
    add("")
    add("| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Liên quan? | Câu trả lời của agent |")
    add("|---|---------|----------------------------|-------|------------|------------------------|")
    lines.extend(rows_individual)
    add("")
    add(f"**Số câu có chunk liên quan trong top-{effective_top_k}: {hits_in_top3}/5**")
    add(f"**Điểm truy xuất tự chấm (chưa tính độ đúng của câu trả lời): {total_score}/10**")
    add("")

    if rows_filter:
        add("## Bảng 2 — Có filter vs không filter (REPORT_NHOM mục 3)")
        add("")
        add("| # | metadata_filter | Điểm khi KHÔNG lọc | Điểm khi CÓ lọc | doc_id top-1 (không lọc) | doc_id top-1 (có lọc) |")
        add("|---|-----------------|--------------------|-----------------|--------------------------|------------------------|")
        lines.extend(rows_filter)
        add("")

    add("## Bảng 3 — Chi tiết top-k từng câu (để phân tích, không cần dán hết)")
    add("")
    lines.extend(rows_detail)

    report = "\n".join(lines)
    print(report)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"\n>>> Đã ghi: {out_path.relative_to(PROJECT_ROOT)}")
    return 0


def main() -> int:
    # Console Windows mặc định cp1252 -> in tiếng Việt sẽ lỗi UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Chạy 5 câu hỏi benchmark của nhóm trên 1 chiến lược.")
    parser.add_argument("-p", "--package", default=None, help="Package cá nhân, ví dụ src.2A202601891-DinhQuocViet")
    parser.add_argument("-s", "--strategy", default="a", help="a | b | c hoặc tên module đầy đủ")
    parser.add_argument("-k", "--top-k", type=int, default=3, help="Số kết quả lấy về (mặc định 3)")
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="Thư mục corpus")
    parser.add_argument("--no-file", action="store_true", help="Chỉ in ra màn hình, không ghi file")
    args = parser.parse_args()

    package_label = (args.package or "src").replace(".", "_")
    out_path = None if args.no_file else PROJECT_ROOT / "report" / f"benchmark_{package_label}_{args.strategy}.md"

    return run(
        package_name=args.package,
        strategy_name=args.strategy,
        top_k=args.top_k,
        data_dir=Path(args.data_dir),
        out_path=out_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
