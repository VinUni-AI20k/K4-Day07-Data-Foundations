from __future__ import annotations

import math
import re
from typing import Any


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
        if not text or not text.strip():
            return []

        # Keep sentence-ending punctuation in the sentence.  The look-behind
        # makes the whitespace after a full stop, exclamation mark, or question
        # mark the actual split point (and also covers the documented ".\n").
        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text.strip())
            if sentence.strip()
        ]

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
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        chunks = self._split(text, self.separators)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]

        if not remaining_separators:
            # No structural separator remains.  Character slicing is the only
            # way to preserve the maximum-size guarantee for an unbroken span.
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator, *next_separators = remaining_separators
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        # If this separator is absent it cannot make progress, so try the next
        # one on the same text instead of recursing forever.
        if separator not in current_text:
            return self._split(current_text, next_separators)

        chunks: list[str] = []
        for piece in current_text.split(separator):
            if not piece:
                continue
            if len(piece) <= self.chunk_size:
                chunks.append(piece)
            else:
                chunks.extend(self._split(piece, next_separators))
        return chunks


class SemanticChunkerAdapter:
    """Adapt a ``semantic-chunkers`` object to this project's chunker interface.

    ``semantic-chunkers`` objects are called with ``[text]`` and return
    ``list[list[Chunk]]``.  The ingestion pipeline in this project expects a
    ``chunk(text) -> list[str]`` method, so this adapter extracts each
    ``Chunk.content`` value.
    """

    def __init__(self, chunker: Any) -> None:
        self.chunker_impl = chunker

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        document_chunks = self.chunker_impl([text])
        if not document_chunks:
            return []

        chunks = document_chunks[0]
        return [
            content
            for item in chunks
            if (content := str(getattr(item, "content", item)).strip())
        ]


class StatisticalSemanticChunker(SemanticChunkerAdapter):
    """Project-compatible wrapper around ``semantic_chunkers.StatisticalChunker``."""

    def __init__(self, encoder: Any, **kwargs: Any) -> None:
        from semantic_chunkers import StatisticalChunker

        super().__init__(StatisticalChunker(encoder=encoder, **kwargs))


class ConsecutiveSemanticChunker(SemanticChunkerAdapter):
    """Project-compatible wrapper around ``semantic_chunkers.ConsecutiveChunker``."""

    def __init__(self, encoder: Any, **kwargs: Any) -> None:
        from semantic_chunkers import ConsecutiveChunker

        super().__init__(ConsecutiveChunker(encoder=encoder, **kwargs))


class CumulativeSemanticChunker(SemanticChunkerAdapter):
    """Project-compatible wrapper around ``semantic_chunkers.CumulativeChunker``."""

    def __init__(self, encoder: Any, **kwargs: Any) -> None:
        from semantic_chunkers import CumulativeChunker

        super().__init__(CumulativeChunker(encoder=encoder, **kwargs))


class RegexSemanticChunker(SemanticChunkerAdapter):
    """Project-compatible wrapper around ``semantic_chunkers.RegexChunker``."""

    def __init__(self, **kwargs: Any) -> None:
        from semantic_chunkers import RegexChunker

        super().__init__(RegexChunker(**kwargs))


def build_semantic_chunkers(encoder: Any | None = None) -> dict[str, SemanticChunkerAdapter]:
    """Create all four optional ``semantic-chunkers`` strategies.

    Pass an existing encoder to avoid constructing/downloading it here.  When
    omitted, ``HuggingFaceEncoder`` is created lazily.
    """

    if encoder is None:
        from semantic_router.encoders import HuggingFaceEncoder

        encoder = HuggingFaceEncoder()

    return {
        "statistical": StatisticalSemanticChunker(encoder=encoder),
        "consecutive": ConsecutiveSemanticChunker(encoder=encoder),
        "cumulative": CumulativeSemanticChunker(encoder=encoder),
        "regex": RegexSemanticChunker(),
    }


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run built-in and optional semantic chunking strategies."""

    def __init__(
        self,
        semantic_strategies: dict[str, Any] | None = None,
    ) -> None:
        """Accept raw ``semantic-chunkers`` objects or project-compatible adapters."""

        self.semantic_strategies = semantic_strategies or {}

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        strategies.update(
            {
                name: (
                    strategy
                    if hasattr(strategy, "chunk")
                    else SemanticChunkerAdapter(strategy)
                )
                for name, strategy in self.semantic_strategies.items()
            }
        )

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0
                ),
                "chunks": chunks,
            }
        return comparison
