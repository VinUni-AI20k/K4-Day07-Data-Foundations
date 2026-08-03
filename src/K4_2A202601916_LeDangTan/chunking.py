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
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be non-negative and smaller than chunk_size")
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
        if not text or not text.strip():
            return []

        # Keep the terminal punctuation with its sentence.  ``\s+`` covers both
        # ordinary spaces and newlines without creating empty sentences.
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
            if sentence.strip()
        ]
        if not sentences:
            return []

        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return [piece.strip() for piece in self._split(text, self.separators) if piece.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # No separator left means that a single long token must be split by
        # character length.  This also makes an explicitly empty separator list
        # useful instead of failing.
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        following = remaining_separators[1:]
        if not separator:
            return self._split(current_text, [])
        if separator not in current_text:
            return self._split(current_text, following)

        # Reattach separators so that punctuation/newline context is retained.
        raw_parts = current_text.split(separator)
        parts = [
            part + (separator if index < len(raw_parts) - 1 else "")
            for index, part in enumerate(raw_parts)
        ]

        chunks: list[str] = []
        pending = ""
        for part in parts:
            if len(part) > self.chunk_size:
                if pending:
                    chunks.append(pending)
                    pending = ""
                chunks.extend(self._split(part, following))
            elif pending and len(pending) + len(part) > self.chunk_size:
                chunks.append(pending)
                pending = part
            else:
                pending += part
        if pending:
            chunks.append(pending)
        return chunks


class PolicySectionChunker:
    """Chunk e-commerce policies by heading or clause before splitting by size.

    Policy documents commonly put an exception, deadline, or responsibility
    immediately below a Markdown heading (``#``/``##``) or a numbered clause
    (``Điều 2``, ``2.1``).  Keeping that label in every derived chunk improves
    both retrieval and the ability to trace an answer back to its policy area.
    """

    SECTION_START = re.compile(
        r"(?=^#{1,6}\s+|^\s*(?:điều|mục)\s+\d+\b|^\s*\d+(?:\.\d+)*[.)]\s+)",
        re.IGNORECASE | re.MULTILINE,
    )

    def __init__(self, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = [section.strip() for section in self.SECTION_START.split(text.strip()) if section.strip()]
        if len(sections) <= 1:
            return RecursiveChunker(chunk_size=self.chunk_size).chunk(text)

        chunks: list[str] = []
        for section in sections:
            lines = section.splitlines()
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

            # A preamble without a heading is still useful, but it does not need
            # a repeated label when it is split.
            is_labeled_section = bool(self.SECTION_START.match(section))
            if not is_labeled_section or not body:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(section))
                continue

            available_body_size = self.chunk_size - len(title) - 1
            if available_body_size <= 0:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(section))
                continue
            for piece in RecursiveChunker(chunk_size=available_body_size).chunk(body):
                chunks.append(f"{title}\n{piece}".strip())
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=min(50, chunk_size - 1)),
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
