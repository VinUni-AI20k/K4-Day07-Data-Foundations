"""
Chiến lược C — Sentence chunks nhỏ + title/section context injection.

Mỗi section được chia bằng SentenceChunker(max_sentences_per_chunk=3). Trước khi
embed, chunk được thêm prefix ``[tên tài liệu > tên mục]`` và metadata ``section``.
Chiến lược lấy top-5 rồi loại các kết quả có score yếu theo cả ngưỡng tuyệt đối
và khoảng cách so với top-1.
"""
from __future__ import annotations

import re
from typing import Any

from strategies.common import Strategy

MAX_SENTENCES = 3
TOP_K = 5
MIN_SCORE = 0.30
MAX_FROM_BEST = 0.12

_MARKER_START = "\x1e"
_MARKER_END = "\x1f"
_NUMBERED_HEADING = re.compile(
    r"^(?:[A-Z]\.|\d+(?:\.\d+)*\.?)\s+\S.{0,88}$",
    flags=re.UNICODE,
)
_PROCEDURAL_HEADING = re.compile(r"^(?:Cách|Bước)\s+\d+\s*:", re.IGNORECASE)


def _looks_like_heading(line: str) -> bool:
    """Recognize Markdown headings and short policy/procedure headings."""
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("#"):
        return True
    if _PROCEDURAL_HEADING.match(stripped) or _NUMBERED_HEADING.match(stripped):
        return True

    letters = [character for character in stripped if character.isalpha()]
    uppercase_ratio = (
        sum(character.isupper() for character in letters) / len(letters)
        if letters
        else 0.0
    )
    return len(stripped) <= 120 and len(letters) >= 4 and uppercase_ratio >= 0.8


def _split_sections(text: str) -> list[tuple[str, str]]:
    """Associate every content block with the latest detected section heading."""
    sections: list[tuple[str, str]] = []
    current_heading = "Nội dung chính"
    content_lines: list[str] = []

    def flush() -> None:
        nonlocal content_lines
        content = "\n".join(content_lines).strip()
        if content:
            sections.append((current_heading, content))
        content_lines = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if _looks_like_heading(line):
            flush()
            current_heading = line.lstrip("#").strip()
        elif line:
            content_lines.append(line)
        elif content_lines:
            content_lines.append("")
    flush()
    return sections


class ContextualSentenceChunker:
    """Section-aware wrapper around the student's SentenceChunker."""

    def __init__(self, package: Any) -> None:
        self._sentence_chunker = package.SentenceChunker(
            max_sentences_per_chunk=MAX_SENTENCES
        )

    def chunk(self, text: str) -> list[str]:
        chunks: list[str] = []
        for section, section_text in _split_sections(text):
            # The corpus uses blank lines for bullets that often have no final
            # punctuation. Treat each such block as a sentence-like unit, then
            # let SentenceChunker group at most three units/sentences.
            paragraphs = [
                " ".join(paragraph.split())
                for paragraph in re.split(r"\n\s*\n", section_text)
                if paragraph.strip()
            ]
            units = [
                paragraph
                if paragraph.endswith((".", "!", "?", ";", ":"))
                else f"{paragraph}."
                for paragraph in paragraphs
            ]
            normalized_section = " ".join(units)
            for piece in self._sentence_chunker.chunk(normalized_section):
                chunks.append(f"{_MARKER_START}{section}{_MARKER_END}{piece}")
        return chunks


def _decorate(chunk_text: str, doc_metadata: dict, chunk_index: int) -> tuple[str, dict]:
    """Replace the internal section marker with the title/section prefix."""
    section = "Nội dung chính"
    content = chunk_text
    if chunk_text.startswith(_MARKER_START) and _MARKER_END in chunk_text:
        marker, content = chunk_text[1:].split(_MARKER_END, 1)
        section = marker.strip() or section

    title = str(doc_metadata.get("title") or doc_metadata.get("doc_id") or "Tài liệu")
    contextual_text = f"[{title} > {section}] {content.strip()}"
    return contextual_text, {
        "section": section,
        "strategy": "sentence_3_context_injection",
    }


def _filter_by_score(results: list[dict]) -> list[dict]:
    """Keep strong top-5 hits using absolute and best-relative thresholds."""
    if not results:
        return []
    cutoff = max(MIN_SCORE, float(results[0]["score"]) - MAX_FROM_BEST)
    filtered = [result for result in results if float(result["score"]) >= cutoff]
    return filtered or results[:1]


STRATEGY = Strategy(
    name="C-sentence-3-context",
    build_chunker=ContextualSentenceChunker,
    decorate=_decorate,
    top_k=TOP_K,
    description=(
        "Chia tối đa 3 câu/đơn vị danh sách theo từng section, rồi prepend "
        "[title > section] trước khi embed. Lấy top-5 và bỏ kết quả yếu bằng "
        f"ngưỡng score >= max({MIN_SCORE:.2f}, top-1 - {MAX_FROM_BEST:.2f})."
    ),
    extra={
        "postprocess_results": _filter_by_score,
        "min_score": MIN_SCORE,
        "max_from_best": MAX_FROM_BEST,
    },
)
