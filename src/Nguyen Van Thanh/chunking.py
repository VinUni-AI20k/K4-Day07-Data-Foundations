from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Split text into fixed-size chunks with optional overlap."""

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
    """Split text into groups of complete sentences."""

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        cleaned = text.strip()
        if not cleaned:
            return []

        # Keep punctuation attached to its sentence and split on following whitespace.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", cleaned)
            if sentence.strip()
        ]
        if not sentences:
            return [cleaned]

        return [
            " ".join(sentences[index : index + self.max_sentences_per_chunk]).strip()
            for index in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Recursively split text using separators in priority order."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return [piece for piece in self._split(text.strip(), self.separators) if piece]

    def _hard_split(self, text: str) -> list[str]:
        return [text[i : i + self.chunk_size] for i in range(0, len(text), self.chunk_size)]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return self._hard_split(current_text)

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        if separator == "":
            return self._hard_split(current_text)

        raw_parts = current_text.split(separator)
        if len(raw_parts) == 1:
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for raw_part in raw_parts:
            part = raw_part.strip()
            if not part:
                continue
            candidate = part if not buffer else f"{buffer}{separator}{part}"
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer.strip())
                buffer = ""

            if len(part) <= self.chunk_size:
                buffer = part
            else:
                chunks.extend(self._split(part, rest))

        if buffer:
            chunks.append(buffer.strip())
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity, returning 0 for a zero vector."""
    if len(vec_a) != len(vec_b):
        raise ValueError("Vectors must have the same dimension")
    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (sum(len(chunk) for chunk in chunks) / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
