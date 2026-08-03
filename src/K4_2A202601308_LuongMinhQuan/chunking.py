from __future__ import annotations

import math
import re

# Tách câu tại khoảng trắng đứng sau ".", "!" hoặc "?".
# Lookbehind giữ dấu câu ở cuối phần đứng trước, nên "Câu một. Câu hai."
# cho ["Câu một.", "Câu hai."] chứ không mất dấu chấm.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


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
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in _SENTENCE_BOUNDARY.split(text)
            if sentence.strip()
        ]
        if not sentences:
            return []

        limit = self.max_sentences_per_chunk
        return [
            " ".join(sentences[index : index + limit])
            for index in range(0, len(sentences), limit)
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

        pieces = self._split(text, self.separators)
        return [piece.strip() for piece in pieces if piece and piece.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: đã đủ ngắn, không cần chia thêm.
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Base case 2: hết separator (hoặc separator rỗng) -> cắt cứng theo chunk_size.
        if not remaining_separators or remaining_separators[0] == "":
            return self._fixed_cut(current_text)

        separator = remaining_separators[0]
        rest = remaining_separators[1:]

        # Separator không xuất hiện -> hạ một bậc ưu tiên, text giữ nguyên.
        if separator not in current_text:
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for part in current_text.split(separator):
            candidate = part if not buffer else buffer + separator + part
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)
                buffer = ""
            if len(part) > self.chunk_size:
                # Phần lẻ vẫn quá dài: xử lý lại bằng separator ưu tiên thấp hơn.
                chunks.extend(self._split(part, rest))
            else:
                buffer = part

        if buffer:
            chunks.append(buffer)
        return chunks

    def _fixed_cut(self, text: str) -> list[str]:
        """Cắt cố định theo chunk_size — lối thoát cuối khi không còn ranh giới nào."""
        size = max(1, self.chunk_size)
        return [text[start : start + size] for start in range(0, len(text), size)]


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
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total = sum(len(chunk) for chunk in chunks)
            comparison[name] = {
                "count": len(chunks),
                # text rỗng -> 0 chunk: chia cho len(chunks) sẽ nổ, nên chốt 0.0.
                "avg_length": (total / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
