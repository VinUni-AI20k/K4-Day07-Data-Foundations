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
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
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
        text = text.strip()
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]
        if not sentences:
            return [text]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            chunks.append(" ".join(sentences[start : start + self.max_sentences_per_chunk]))
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
        text = text.strip()
        if not text:
            return []
        return self._split(text, self.separators or [""])

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        if separator == "":
            return [
                current_text[start : start + self.chunk_size].strip()
                for start in range(0, len(current_text), self.chunk_size)
                if current_text[start : start + self.chunk_size].strip()
            ]
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        parts = current_text.split(separator)
        units = [
            part + (separator if index < len(parts) - 1 else "")
            for index, part in enumerate(parts)
            if part.strip()
        ]

        chunks: list[str] = []
        current = ""
        for unit in units:
            if len(unit) > self.chunk_size:
                if current.strip():
                    chunks.append(current.strip())
                    current = ""
                chunks.extend(self._split(unit, remaining_separators[1:]))
                continue

            candidate = current + unit if current else unit
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = unit

        if current.strip():
            chunks.append(current.strip())
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(sum(value * value for value in vec_a))
    norm_b = math.sqrt(sum(value * value for value in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            avg_length = sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0
            comparison[name] = {
                "count": len(chunks),
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return comparison
