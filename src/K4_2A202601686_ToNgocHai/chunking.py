from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """Chia văn bản theo số ký tự, có thể chồng lấn giữa hai chunk."""

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
        chunks = []
        for start in range(0, len(text), step):
            chunks.append(text[start : start + self.chunk_size])
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """Tách ở cuối câu rồi gom tối đa một số câu vào mỗi chunk."""

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text)
            if sentence.strip()
        ]
        return [
            " ".join(sentences[start : start + self.max_sentences_per_chunk])
            for start in range(0, len(sentences), self.max_sentences_per_chunk)
        ]


class RecursiveChunker:
    """Ưu tiên ranh giới đoạn/câu/từ và đệ quy khi một phần còn quá dài."""

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        chunks = self._split(text.strip(), self.separators)
        return [chunk.strip() for chunk in chunks if chunk.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        if separator not in current_text:
            return self._split(current_text, remaining_separators[1:])

        parts = current_text.split(separator)
        units: list[str] = []
        for index, part in enumerate(parts):
            if not part:
                continue
            # Gắn lại separator để không làm thay đổi nội dung/ngữ nghĩa của câu.
            unit = part + (separator if index < len(parts) - 1 else "")
            if len(unit) > self.chunk_size:
                units.extend(self._split(unit, remaining_separators[1:]))
            else:
                units.append(unit)

        chunks: list[str] = []
        buffer = ""
        for unit in units:
            if not buffer:
                buffer = unit
            elif len(buffer) + len(unit) <= self.chunk_size:
                buffer += unit
            else:
                chunks.append(buffer)
                buffer = unit
        if buffer:
            chunks.append(buffer)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Tính cosine similarity; vector 0 có similarity bằng 0."""

    magnitude_a = math.sqrt(sum(value * value for value in vec_a))
    magnitude_b = math.sqrt(sum(value * value for value in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return _dot(vec_a, vec_b) / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Chạy ba chiến lược và trả về số chunk, độ dài trung bình, nội dung."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": sum(map(len, chunks)) / len(chunks) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
