from __future__ import annotations

import math
import re
from typing import Any


class FixedSizeChunker:
    """Split text into fixed-size chunks with optional character overlap."""

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must satisfy 0 <= overlap < chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            piece = text[start : start + self.chunk_size]
            chunks.append(piece)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Group detected sentences into chunks of a bounded sentence count."""

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk]).strip()
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using separators from strongest to weakest."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self, separators: list[str] | None = None, chunk_size: int = 500
    ) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.separators = (
            list(self.DEFAULT_SEPARATORS) if separators is None else list(separators)
        )
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return self._split(text.strip(), self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return FixedSizeChunker(self.chunk_size, 0).chunk(current_text)
        separator = remaining_separators[0]
        if separator == "":
            return FixedSizeChunker(self.chunk_size, 0).chunk(current_text)
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        parts = current_text.split(separator)
        chunks: list[str] = []
        pending = ""
        next_separators = remaining_separators[1:]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            candidate = part if not pending else f"{pending}{separator}{part}"
            if len(candidate) <= self.chunk_size:
                pending = candidate
                continue
            if pending:
                chunks.append(pending.strip())
                pending = ""
            if len(part) <= self.chunk_size:
                pending = part
            else:
                chunks.extend(self._split(part, next_separators))
        if pending:
            chunks.append(pending.strip())
        return [piece for piece in chunks if piece]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Return cosine similarity, protecting against zero vectors."""

    norm_a = math.sqrt(sum(value * value for value in vec_a))
    norm_b = math.sqrt(sum(value * value for value in vec_b))
    denominator = norm_a * norm_b
    if denominator == 0:
        return 0.0
    return _dot(vec_a, vec_b) / denominator


class ChunkingStrategyComparator:
    """Run the fixed-size, sentence and recursive strategies side by side."""

    def compare(self, text: str, chunk_size: int = 200) -> dict[str, dict[str, Any]]:
        fixed_overlap = min(50, max(0, chunk_size // 2))
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size, fixed_overlap),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison: dict[str, dict[str, Any]] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(piece) for piece in chunks) / len(chunks) if chunks else 0.0
                ),
                "chunks": chunks,
            }
        return comparison
