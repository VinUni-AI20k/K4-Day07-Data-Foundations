"""
chunkers/ — 4 chien luoc chia nho tai lieu cua nhom (Lab 07 · K4).

Nguyen tac to chuc
------------------
Bon thanh vien dung CHUNG corpus (`data/k4_ecommerce/`), CHUNG 5 benchmark
query (`bench.py::BENCHMARK_QUERIES`), CHUNG embedder (`lexical_embedding.py`)
va CHUNG pipeline nap du lieu (`ingest.build_knowledge_base`).

Bien duy nhat thay doi giua bon nguoi la CHUNKER. Nho vay bang so sanh trong
`REPORT_NHOM.md` moi la so sanh cong bang.

    chunkers/
      base.py            <- hop dong + helper dung chung. DOC TRUOC KHI VIET.
      ha_heading.py      <- Nguyen Quang Ha        (DA XONG)
      tv2_clause.py      <- Thanh vien 2           (CHUA IMPLEMENT)
      tv3_sliding.py     <- Thanh vien 3           (CHUA IMPLEMENT)
      tv4_semantic.py    <- Thanh vien 4           (CHUA IMPLEMENT)

Quy trinh lam viec
------------------
1. Moi nguoi CHI sua file cua minh. Khong ai sua `bench.py`, `ingest.py`,
   `lexical_embedding.py`, `src/`, hay file cua nguoi khac.
2. Chunker chua implement thi `bench.py --all` van chay binh thuong; no se in
   "CHUA IMPLEMENT" va bo qua, khong crash.
3. Lam xong thi chay:
       $env:EMBEDDING_PROVIDER="lexical"; python bench.py <ten-strategy>
   Rieng bang so sanh ca nhom:
       $env:EMBEDDING_PROVIDER="lexical"; python bench.py --all
4. Cuoi cung moi nguoi copy toan bo repo ve repo rieng cua minh
   (`DAY07-<MSSV>-<HoVaTen>`) de nop.

Them mot strategy moi
---------------------
Tao file `chunkers/<ten>.py`, ke thua `BaseChunker`, roi them mot dong vao
`STRATEGIES` ben duoi. Khong phai sua cho nao khac.
"""
from __future__ import annotations

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker

from .base import BaseChunker
from .ha_heading import HeadingChunker, LLMSemanticChunker
from .tv2_clause import ClauseChunker
from .tv3_sliding import SlidingWindowChunker
from .tv4_semantic import SemanticSplitChunker

__all__ = [
    "BaseChunker",
    "HeadingChunker",
    "LLMSemanticChunker",
    "ClauseChunker",
    "SlidingWindowChunker",
    "SemanticSplitChunker",
    "STRATEGIES",
    "OWNERS",
    "build",
]


# ---------------------------------------------------------------------------
# Registry: ten strategy -> factory.
# Factory nhan mot dict `ctx` chua cac thu bench.py co the cung cap:
#     ctx["embedding_fn"] : embedder chung cua nhom
#     ctx["llm_fn"]       : ham LLM neu co OPENAI_API_KEY, khong thi None
# Chunker nao khong can thi cu bo qua `ctx`.
# ---------------------------------------------------------------------------
STRATEGIES = {
    # --- 4 chien luoc chinh cua nhom, moi nguoi mot dong -------------------
    "heading": lambda ctx: HeadingChunker(max_chunk_size=900, min_chunk_size=120),
    "clause": lambda ctx: ClauseChunker(max_chunk_size=700, min_chunk_size=120),
    "sliding": lambda ctx: SlidingWindowChunker(chunk_size=500, overlap=200),
    "semantic": lambda ctx: SemanticSplitChunker(
        embedding_fn=ctx.get("embedding_fn"), percentile=25
    ),
    # --- Baseline co san trong src/, de doi chieu -------------------------
    "fixed": lambda ctx: FixedSizeChunker(chunk_size=500, overlap=50),
    "recursive": lambda ctx: RecursiveChunker(chunk_size=400),
    "sentence": lambda ctx: SentenceChunker(max_sentences_per_chunk=3),
    # --- Bien the / ablation cua Ha ---------------------------------------
    "heading_nobreadcrumb": lambda ctx: HeadingChunker(
        max_chunk_size=400, min_chunk_size=120, keep_breadcrumb=False
    ),
    "llm_semantic": lambda ctx: LLMSemanticChunker(
        llm_fn=ctx.get("llm_fn"), max_chunk_size=900
    ),
}

# Ai phu trach strategy nao — in ra trong bang so sanh cua bench.py.
OWNERS = {
    "heading": "Nguyen Quang Ha",
    "clause": "TV2 (chua dien ten)",
    "sliding": "TV3 (chua dien ten)",
    "semantic": "TV4 (chua dien ten)",
    "fixed": "baseline src/",
    "recursive": "baseline src/",
    "sentence": "baseline src/",
    "heading_nobreadcrumb": "Ha — ablation",
    "llm_semantic": "Ha — bonus",
}

# Bon strategy chinh, dung cho bang so sanh giua cac thanh vien.
TEAM_STRATEGIES = ["heading", "clause", "sliding", "semantic"]


def build(name: str, ctx: dict | None = None):
    """Tao chunker theo ten. `ctx` chua embedding_fn / llm_fn neu co."""
    if name not in STRATEGIES:
        raise KeyError(f"Strategy khong ton tai: {name}. Co: {sorted(STRATEGIES)}")
    return STRATEGIES[name](ctx or {})
