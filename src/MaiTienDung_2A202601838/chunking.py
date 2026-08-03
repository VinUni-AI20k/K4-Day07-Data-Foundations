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
        if not text or not text.strip():
            return []

        # Keep the sentence-ending punctuation in the sentence by splitting
        # only on whitespace that follows ., !, or ?.
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

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
        return self._split(text.strip(), list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        current_text = current_text.strip()
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # No usable separator remains. Character slicing is the final,
        # guaranteed fallback, including the case separators=[] .
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        if not separator:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        if separator not in current_text:
            return self._split(current_text, rest)

        pieces = [piece.strip() for piece in current_text.split(separator)]
        pieces = [piece for piece in pieces if piece]

        # Split oversized pieces using the next, lower-priority separator.
        atoms: list[str] = []
        for piece in pieces:
            if len(piece) <= self.chunk_size:
                atoms.append(piece)
            else:
                atoms.extend(self._split(piece, rest))

        # Merge neighboring pieces while preserving the separator. This
        # keeps chunks coherent and prevents unnecessary tiny chunks.
        chunks: list[str] = []
        current = ""
        for atom in atoms:
            candidate = atom if not current else f"{current}{separator}{atom}"
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                current = atom
        if current:
            chunks.append(current.strip())
        return chunks


class MarkdownBlockChunker:
    """Split Markdown by meaningful blocks while preserving section context.

    A heading is prefixed to the following paragraph/list block. Oversized
    blocks are split at sentence boundaries, so answer-bearing Markdown
    sections stay together instead of being cut at arbitrary characters.
    This is a custom strategy for the e-commerce benchmark; it is not part of
    the three-strategy baseline comparator.
    """

    def __init__(self, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        blocks = [
            block.strip()
            for block in re.split(r"\n\s*\n", text.strip())
            if block.strip()
        ]
        chunks: list[str] = []
        heading = ""

        for block in blocks:
            headings = re.findall(r"^#{1,6}\s+.+$", block, flags=re.MULTILINE)
            if headings:
                heading = headings[-1].strip()

            value = block if block.startswith(heading) else f"{heading} {block}".strip()
            if len(value) <= self.chunk_size:
                chunks.append(value)
                continue

            sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+", value)
                if sentence.strip()
            ]
            current = ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                if current and len(candidate) > self.chunk_size:
                    chunks.append(current.strip())
                    current = sentence
                else:
                    current = candidate
            if current:
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
    if len(vec_a) != len(vec_b):
        raise ValueError("vectors must have the same dimension")

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        comparison: dict = {}
        for name, chunks in strategies.items():
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (
                    sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0
                ),
                "chunks": chunks,
            }
        return comparison
