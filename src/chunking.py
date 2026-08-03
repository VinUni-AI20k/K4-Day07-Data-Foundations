from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        chunks: list[str] = []
        pos = 0
        n = len(text)
        step = max(1, self.chunk_size - self.overlap)

        while pos < n:
            sub = text[pos:]
            # Kiểm tra ký tự thứ 3 (index 2) hoặc thứ 4 (index 3) có phải dấu cách ' ' hay không
            has_space_at_3_or_4 = (len(sub) >= 3 and sub[2] == " ") or (len(sub) >= 4 and sub[3] == " ")
            next_newline = text.find("\n", pos)

            if has_space_at_3_or_4 and next_newline != -1 and (next_newline - pos) <= self.chunk_size:
                chunk_str = text[pos:next_newline]
                pos = next_newline + 1
            else:
                end = min(pos + self.chunk_size, n)
                if next_newline != -1 and pos < next_newline <= end:
                    chunk_str = text[pos:next_newline]
                    pos = next_newline + 1
                else:
                    chunk_str = text[pos:end]
                    if end == n:
                        pos = n
                    else:
                        pos = pos + step

            if chunk_str:
                chunks.append(chunk_str)

        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sentences = [s.strip() for s in re.split(r'(?<=\. |\! |\? |\.\n)', text) if s.strip()]
        if not sentences:
            return []
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_str = " ".join(sentences[i : i + self.max_sentences_per_chunk]).strip()
            if chunk_str:
                chunks.append(chunk_str)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        if sep == "":
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]

        parts = current_text.split(sep)
        sub_chunks: list[str] = []
        for part in parts:
            if not part and sep == "\n\n":
                continue
            if len(part) > self.chunk_size:
                sub_chunks.extend(self._split(part, next_seps))
            else:
                sub_chunks.append(part)

        merged: list[str] = []
        curr = ""
        for item in sub_chunks:
            if not item:
                continue
            if not curr:
                curr = item
            elif len(curr) + len(sep) + len(item) <= self.chunk_size:
                curr = curr + sep + item
            else:
                merged.append(curr)
                curr = item
        if curr:
            merged.append(curr)

        return merged if merged else [current_text]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot = sum(x * y for x, y in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed = FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text)
        sent = SentenceChunker().chunk(text)
        rec = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_len = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": avg_len,
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed),
            "by_sentences": _stats(sent),
            "recursive": _stats(rec),
        }
