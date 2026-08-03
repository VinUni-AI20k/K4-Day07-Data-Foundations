"""
strategies.py — DA CHUYEN SANG package `chunkers/`. File nay chi giu tuong thich.

Nhom co 4 nguoi, moi nguoi mot chien luoc chunking rieng, nen code da duoc tach
thanh mot file cho moi nguoi:

    chunkers/base.py          hop dong + helper dung chung  (DOC TRUOC)
    chunkers/ha_heading.py    Nguyen Quang Ha
    chunkers/tv2_clause.py    Thanh vien 2
    chunkers/tv3_sliding.py   Thanh vien 3
    chunkers/tv4_semantic.py  Thanh vien 4
    chunkers/__init__.py      registry STRATEGIES + OWNERS

Import moi:
    from chunkers import build, STRATEGIES
    from chunkers.ha_heading import HeadingChunker
"""
from __future__ import annotations

import warnings

from chunkers import STRATEGIES  # noqa: F401
from chunkers.ha_heading import HeadingChunker, LLMSemanticChunker  # noqa: F401

warnings.warn(
    "strategies.py da duoc thay bang package chunkers/. "
    "Dung `from chunkers.ha_heading import HeadingChunker`.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["HeadingChunker", "LLMSemanticChunker", "STRATEGIES"]
