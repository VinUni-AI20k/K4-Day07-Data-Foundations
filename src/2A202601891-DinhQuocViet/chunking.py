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

    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])[ \n]")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Cắt SAU dấu câu (lookbehind) để giữ lại "." / "!" / "?" trong câu.
        sentences = [part.strip() for part in self._SENTENCE_BOUNDARY.split(text)]
        sentences = [part for part in sentences if part]
        if not sentences:
            return []

        size = self.max_sentences_per_chunk
        return [
            " ".join(sentences[start : start + size])
            for start in range(0, len(sentences), size)
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
        if not text:
            return []
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        # Đủ ngắn -> giữ nguyên, đây là điều kiện dừng của đệ quy.
        if len(current_text) <= self.chunk_size:
            return [current_text]
        # Hết separator (hoặc gặp "") -> buộc phải cắt cứng theo ký tự.
        if not remaining_separators:
            return self._hard_split(current_text)

        separator, rest = remaining_separators[0], remaining_separators[1:]
        if separator == "":
            return self._hard_split(current_text)

        pieces = current_text.split(separator)
        if len(pieces) == 1:
            # Separator này không xuất hiện -> thử separator ưu tiên kế tiếp.
            return self._split(current_text, rest)

        # Gộp các mảnh liền kề lại cho tới sát chunk_size để tránh chunk vụn.
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)
            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                # Một mảnh vẫn quá dài -> hạ xuống separator mức thấp hơn.
                chunks.extend(self._split(piece, rest))
                buffer = ""

        if buffer:
            chunks.append(buffer)
        return [chunk for chunk in chunks if chunk]

    def _hard_split(self, text: str) -> list[str]:
        """Cắt cứng theo chunk_size khi không còn ranh giới ngữ nghĩa nào."""
        return [text[start : start + self.chunk_size] for start in range(0, len(text), self.chunk_size)]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # overlap=0 để count/avg_length so sánh được công bằng với 2 chiến lược kia
        # (có overlap thì tổng ký tự bị đếm lặp, avg_length mất ý nghĩa đối chiếu).
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total_length = sum(len(chunk) for chunk in chunks)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": round(total_length / len(chunks), 2) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
