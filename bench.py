"""
bench.py — Benchmark retrieval cho Lab 07 (K4 · corpus phap luat TMDT Viet Nam).

Cach chay:
    python bench.py                    # strategy ca nhan cua toi (heading)
    python bench.py clause             # strategy cua mot thanh vien khac
    python bench.py --team             # 4 chien luoc chinh cua nhom
    python bench.py --all              # them baseline src/ + cac ablation
    python bench.py --all > report/bench_output_lexical.txt

    # Windows PowerShell — dung embedder co nghia (khuyen dung):
    $env:EMBEDDING_PROVIDER="lexical"; python bench.py --team

=============================================================================
FILE NAY LA PHAN DUNG CHUNG — KHONG AI DUOC SUA.
=============================================================================
Bon thanh vien dung chung: corpus `data/k4_ecommerce/`, 5 benchmark query ben
duoi, embedder, pipeline `ingest.build_knowledge_base`, va cach cham diem.
Bien DUY NHAT thay doi giua bon nguoi la CHUNKER.

Muon them/sua chien luoc: viet file cua ban trong `chunkers/` roi them mot
dong vao `chunkers/__init__.py::STRATEGIES`. Xem `chunkers/base.py` truoc.

Chunker chua implement se duoc bo qua (in "CHUA IMPLEMENT"), khong lam crash
ca lan chay.
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

from chunkers import OWNERS, STRATEGIES, TEAM_STRATEGIES, build
from chunkers.ha_heading import LLMSemanticChunker
from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

DATA_DIR = os.getenv("LAB_DATA_DIR", "data/k4_ecommerce")
TOP_K = 3

# ---------------------------------------------------------------------------
# 5 BENCHMARK QUERY — nhom chot, KHONG doi sau khi da chay strategy nao do.
#   anchors: chuoi dac trung PHAI xuat hien trong context truy xuat duoc.
#            Cham o muc CHUNK, khong chi kiem doc_id (xem docs/EVALUATION.md).
# ---------------------------------------------------------------------------
BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "kind": "so lieu",
        "question": (
            "Neu nguoi ban khong cong bo ro thoi han tra loi, sau bao lau de nghi "
            "giao ket hop dong cua khach hang het hieu luc?"
        ),
        "question_vi": (
            "Nếu người bán không công bố rõ thời hạn trả lời, sau bao lâu đề nghị "
            "giao kết hợp đồng của khách hàng hết hiệu lực?"
        ),
        "gold_answer": (
            "Trong vòng 12 (mười hai) giờ kể từ khi gửi đề nghị giao kết hợp đồng "
            "mà khách hàng không nhận được trả lời thì đề nghị được coi là chấm dứt "
            "hiệu lực (khoản 2 Điều 20 Nghị định 52/2013/NĐ-CP)."
        ),
        "gold_doc_id": "nd52-quy-trinh-dat-hang-truc-tuyen",
        "anchors": ["12 (mười hai) giờ"],
        "metadata_filter": None,
    },
    {
        "id": "Q2",
        "kind": "dieu kien",
        "question": (
            "San giao dich thuong mai dien tu phai thong bao truoc bao nhieu ngay khi "
            "thay doi quy che hoat dong?"
        ),
        "question_vi": (
            "Sàn giao dịch thương mại điện tử phải thông báo trước bao nhiêu ngày khi "
            "thay đổi quy chế hoạt động?"
        ),
        "gold_answer": (
            "Phải thông báo cho tất cả đối tượng sử dụng dịch vụ ít nhất 5 ngày trước "
            "khi áp dụng thay đổi (khoản 3 Điều 38 Nghị định 52/2013/NĐ-CP)."
        ),
        "gold_doc_id": "nd52-quy-che-hoat-dong-san",
        "anchors": ["ít nhất 5 ngày"],
        "metadata_filter": None,
    },
    {
        "id": "Q3",
        "kind": "quy trinh",
        "question": (
            "Co che ra soat va xac nhan noi dung hop dong phai hien thi nhung thong tin "
            "gi cho khach hang truoc khi dat hang?"
        ),
        "question_vi": (
            "Cơ chế rà soát và xác nhận nội dung hợp đồng phải hiển thị những thông tin "
            "gì cho khách hàng trước khi đặt hàng?"
        ),
        "gold_answer": (
            "Tên hàng hóa/dịch vụ, số lượng và chủng loại; phương thức và thời hạn giao "
            "hàng; tổng giá trị hợp đồng và chi tiết phương thức thanh toán. Ngoài ra "
            "phải hiển thị cách thức và thời hạn trả lời đề nghị giao kết, và cho phép "
            "hủy giao dịch (Điều 18 Nghị định 52/2013/NĐ-CP)."
        ),
        "gold_doc_id": "nd52-quy-trinh-dat-hang-truc-tuyen",
        "anchors": ["Tổng giá trị của hợp đồng"],
        "metadata_filter": None,
    },
    {
        "id": "Q4",
        "kind": "liet ke + FILTER BAT BUOC",
        "question": (
            "Chinh sach kiem hang co phai la mot dieu kien giao dich chung bat buoc phai "
            "cong bo khong?"
        ),
        "question_vi": (
            "Chính sách kiểm hàng có phải là một điều kiện giao dịch chung bắt buộc "
            "phải công bố không?"
        ),
        "gold_answer": (
            "Có. Từ ngày 01/01/2022, chính sách kiểm hàng là một trong những điều kiện "
            "giao dịch chung bắt buộc phải công bố trên website TMĐT (Nghị định "
            "85/2021/NĐ-CP). Bản gốc Điều 32 Nghị định 52/2013/NĐ-CP KHÔNG liệt kê "
            "chính sách kiểm hàng — trả lời theo bản 2013 là sai."
        ),
        "gold_doc_id": "nd85-2021-diem-moi-bao-ve-nguoi-tieu-dung",
        "anchors": ["chính sách kiểm hàng"],
        "metadata_filter": {"customer_role": "buyer"},
    },
    {
        "id": "Q5",
        "kind": "ngoai le",
        "question": (
            "Website niem yet gia ma khong noi ro da bao gom thue va phi van chuyen "
            "chua thi hieu the nao?"
        ),
        "question_vi": (
            "Website niêm yết giá mà không nói rõ đã bao gồm thuế và phí vận chuyển "
            "chưa thì hiểu thế nào?"
        ),
        "gold_answer": (
            "Trừ trường hợp các bên có thỏa thuận khác, giá niêm yết được hiểu là đã "
            "bao gồm mọi chi phí liên quan như thuế, phí đóng gói, phí vận chuyển và "
            "chi phí phát sinh khác (khoản 2 Điều 31 Nghị định 52/2013/NĐ-CP)."
        ),
        "gold_doc_id": "seller-listing",
        "anchors": ["được hiểu là đã bao gồm mọi chi phí"],
        "metadata_filter": None,
    },
]

# Registry strategy nam trong `chunkers/__init__.py`. Moi thanh vien them mot
# dong o do va viet chunker cua minh trong file rieng duoi `chunkers/`.
# KHONG sua file nay — day la phan dung chung de so sanh cong bang.
MY_STRATEGY = "heading"


# ---------------------------------------------------------------------------
def _make_llm_fn():
    """Tra ve ham LLM that neu co OPENAI_API_KEY, khong thi tra None (-> fallback)."""
    load_dotenv(override=False)
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from openai import OpenAI

        client = OpenAI()
        model = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

        def _call(prompt: str) -> str:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content or ""

        return _call
    except Exception:
        return None


def select_embedder():
    """mock (mac dinh) | lexical | local | openai.

    `lexical` la backend TF-IDF tu viet (lexical_embedding.py): khong can
    PyTorch, khong can API key, nhung score co y nghia hon mock rat nhieu.
    Dat EMBEDDING_PROVIDER=lexical trong .env hoac bien moi truong.
    """
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "lexical":
        from lexical_embedding import LexicalEmbedder

        return LexicalEmbedder(DATA_DIR)
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception:
            print("[!] Local embedder khong san sang; dung mock.")
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception:
            print("[!] OpenAI embedder khong san sang; dung mock.")
    return _mock_embed


def demo_llm(prompt: str) -> str:
    """LLM gia: tra lai chinh context da retrieve, de kiem tra grounding.

    Khong co API key nen khong sinh chu moi. Tra ve dong dau cua tung chunk
    de nhin thay agent thuc su duoc cho an nhung gi.
    """
    context = prompt.split("Context:", 1)[-1].split("Question:", 1)[0].strip()
    heads = [line.strip() for line in context.splitlines() if line.strip()][:6]
    return "[MOCK LLM] Tra loi dua tren context: " + " | ".join(heads)


# ---------------------------------------------------------------------------
# Cham diem o MUC CHUNK (rubric docs/EVALUATION.md)
#   2 = anchor nam trong top-3 VA o vi tri top-1
#   1 = anchor nam trong top-3 nhung khong phai top-1
#   0 = khong co bang chung dap an trong top-3
# ---------------------------------------------------------------------------
def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def score_results(results: list[dict], query: dict) -> tuple[int, str]:
    anchors = [_norm(a) for a in query["anchors"]]
    hit_ranks = [
        rank
        for rank, result in enumerate(results, start=1)
        if any(anchor in _norm(result["content"]) for anchor in anchors)
    ]
    doc_hit = any(r["metadata"].get("doc_id") == query["gold_doc_id"] for r in results)

    if not hit_ranks:
        note = (
            "0 — khong chunk nao chua anchor"
            + (" (DUNG doc_id nhung SAI section)" if doc_hit else "")
        )
        return 0, note
    if hit_ranks[0] == 1:
        return 2, "2 — anchor nam o chunk top-1"
    return 1, f"1 — anchor nam o top-{hit_ranks[0]}, khong phai top-1"


def run_query(store, agent, query: dict, use_filter: bool) -> dict:
    metadata_filter = query["metadata_filter"] if use_filter else None
    if metadata_filter:
        results = store.search_with_filter(
            query["question_vi"], top_k=TOP_K, metadata_filter=metadata_filter
        )
    else:
        results = store.search(query["question_vi"], top_k=TOP_K)

    points, note = score_results(results, query)
    answer = (
        agent.llm_fn(agent.build_prompt(query["question_vi"], results))
        if results
        else agent.NO_CONTEXT_MESSAGE
    )
    return {"results": results, "points": points, "note": note, "answer": answer}


def print_run(query: dict, run: dict, label: str) -> None:
    print(f"  --- {label} ---")
    if not run["results"]:
        print("    (khong co ket qua)")
    for rank, result in enumerate(run["results"], start=1):
        metadata = result["metadata"]
        preview = " ".join(result["content"].split())[:110]
        print(
            f"    {rank}. score={result['score']:+.4f}  "
            f"doc_id={metadata.get('doc_id')}  "
            f"chunk={metadata.get('chunk_index')}  "
            f"role={metadata.get('customer_role')}"
        )
        print(f"       {preview}...")
    print(f"    -> diem chunk-level: {run['note']}")
    print(f"    -> agent: {run['answer'][:220]}")


def run_strategy(name: str, embedder) -> dict | None:
    """Chay mot strategy. Tra None neu chunker do chua duoc implement."""
    context = {"embedding_fn": embedder, "llm_fn": _make_llm_fn()}

    print("=" * 78)
    print(f"STRATEGY: {name}   [{OWNERS.get(name, '?')}]")

    try:
        chunker = build(name, context)
        params = chunker.params() if hasattr(chunker, "params") else repr(vars(chunker))
        print(f"PARAMS  : {params}")
        store = build_knowledge_base(DATA_DIR, embedder, chunker=chunker)
    except NotImplementedError as error:
        print(f"PARAMS  : -")
        print(f"TRANG THAI: CHUA IMPLEMENT — bo qua.\n  ({error})")
        print("-" * 78)
        return None

    agent = KnowledgeBaseAgent(store=store, llm_fn=demo_llm)
    total_chunks = store.get_collection_size()
    print(f"CHUNKS  : {total_chunks} chunk tu {DATA_DIR}")
    if isinstance(chunker, LLMSemanticChunker):
        print(f"LLM     : {chunker.fallback_reason}")
    print("-" * 78)

    per_query = {}
    total_points = 0
    for query in BENCHMARK_QUERIES:
        print(f"\n[{query['id']}] ({query['kind']}) {query['question_vi']}")
        print(f"  gold doc : {query['gold_doc_id']}   anchor: {query['anchors']}")

        run_nofilter = run_query(store, agent, query, use_filter=False)
        print_run(query, run_nofilter, "KHONG FILTER")

        entry = {"no_filter": run_nofilter}
        if query["metadata_filter"]:
            run_filter = run_query(store, agent, query, use_filter=True)
            print_run(query, run_filter, f"CO FILTER {query['metadata_filter']}")
            same = [r["id"] for r in run_nofilter["results"]] == [
                r["id"] for r in run_filter["results"]
            ]
            print(f"    -> A/B: ket qua {'GIONG HET' if same else 'KHAC NHAU'}")
            entry["filter"] = run_filter
            entry["ab_identical"] = same
            scored = run_filter["points"]
        else:
            scored = run_nofilter["points"]

        entry["points"] = scored
        total_points += scored
        per_query[query["id"]] = entry

    print("-" * 78)
    print(f"TONG DIEM {name}: {total_points}/10  (chunks={total_chunks})")
    return {
        "name": name,
        "params": params,
        "chunks": total_chunks,
        "total_points": total_points,
        "per_query": per_query,
    }


def print_summary(summaries: list[dict], skipped: list[str]) -> None:
    print("\n" + "=" * 78)
    print("BANG SO SANH STRATEGY (diem chunk-level, toi da 10)")
    print("=" * 78)
    header = (
        f"{'strategy':22} {'nguoi phu trach':22} {'chunks':>7} "
        + " ".join(f"{q['id']:>4}" for q in BENCHMARK_QUERIES)
        + f" {'TONG':>6}"
    )
    print(header)
    print("-" * len(header))
    for summary in summaries:
        cells = " ".join(
            f"{summary['per_query'][q['id']]['points']:>4}" for q in BENCHMARK_QUERIES
        )
        owner = OWNERS.get(summary["name"], "?")[:22]
        print(
            f"{summary['name']:22} {owner:22} {summary['chunks']:>7} {cells} "
            f"{summary['total_points']:>6}"
        )
    print("-" * len(header))
    print("Q4 duoc cham theo lan CO metadata_filter (customer_role=buyer).")

    if skipped:
        print()
        for name in skipped:
            print(f"[CHUA IMPLEMENT] {name:22} — {OWNERS.get(name, '?')}")

    done = [s["name"] for s in summaries if s["name"] in TEAM_STRATEGIES]
    print(
        f"\n4 chien luoc chinh cua nhom: {len(done)}/{len(TEAM_STRATEGIES)} da xong "
        f"({', '.join(TEAM_STRATEGIES)})."
    )


def main() -> int:
    args = [a for a in sys.argv[1:] if a.strip()]
    embedder = select_embedder()
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Embedding backend: {backend}")
    if backend == "mock embeddings fallback":
        print(
            "[!] Dang dung MockEmbedder: score chi phan anh hash, KHONG phan anh ngu "
            "nghia. Ket qua duoi day dung de kiem luong ky thuat + so sanh so chunk / "
            "coherence / provenance, khong dung de ket luan strategy nao 'hieu' hon."
        )
    print()

    if args and args[0] in ("--all", "--team"):
        # --team: chi 4 chien luoc chinh cua nhom.
        # --all : them ca baseline cua src/ va cac bien the/ablation.
        names = TEAM_STRATEGIES if args[0] == "--team" else list(STRATEGIES)
        summaries, skipped = [], []
        for name in names:
            result = run_strategy(name, embedder)
            (summaries if result else skipped).append(result or name)
        print_summary(summaries, skipped)
        return 0

    name = args[0] if args else MY_STRATEGY
    if name not in STRATEGIES:
        print(f"Strategy khong hop le: {name}.")
        print(f"Chon mot trong: {sorted(STRATEGIES)}")
        return 1
    run_strategy(name, embedder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
