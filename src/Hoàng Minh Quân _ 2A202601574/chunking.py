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

        # Tách câu bằng regex giữ lại các dấu ngắt câu hợp lệ: ". ", "! ", "? ", ".\n"
        pattern = r"(?<=[.!?])\s+|(?<=\.)\n+"
        raw_sentences = re.split(pattern, text)
        sentences = [s.strip() for s in raw_sentences if s and s.strip()]

        if not sentences:
            return []

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_str = " ".join(group).strip()
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
        if len(text) <= self.chunk_size:
            return [text]

        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []

        # Nếu văn bản đã nhỏ hơn hoặc bằng chunk_size, trả về trực tiếp
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # Nếu đã hết phân cách mà độ dài vẫn vượt quá chunk_size (ví dụ chuỗi dài không có khoảng trắng)
        if not remaining_separators:
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]

        # Trường hợp phân cách là chuỗi rỗng "" (tách theo từng ký tự)
        if sep == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
            ]

        # Tách văn bản theo phân cách hiện tại
        splits = current_text.split(sep)
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for split in splits:
            if not split and sep != " ":
                continue

            # Tính độ dài nếu gộp split này vào chunk hiện tại
            addition_len = len(split) + (len(sep) if current_chunk else 0)

            # Nếu bản thân mảnh split đơn lẻ đã vượt quá chunk_size, cần gọi đệ quy với các sep tiếp theo
            if len(split) > self.chunk_size:
                if current_chunk:
                    chunks.append(sep.join(current_chunk))
                    current_chunk = []
                    current_len = 0

                sub_chunks = self._split(split, next_seps)
                chunks.extend(sub_chunks)
                continue

            # Nếu thêm split vào vượt quá chunk_size -> đẩy chunk hiện tại ra và tạo chunk mới
            if current_len + addition_len > self.chunk_size:
                chunks.append(sep.join(current_chunk))
                current_chunk = [split]
                current_len = len(split)
            else:
                current_chunk.append(split)
                current_len += addition_len

        if current_chunk:
            chunks.append(sep.join(current_chunk))

        return [c for c in chunks if c]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(sum(x * x for x in vec_a))
    norm_b = math.sqrt(sum(y * y for y in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        """
        Runs FixedSizeChunker, SentenceChunker, and RecursiveChunker on input text,
        then computes chunk count and average chunk length for each strategy.
        """
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=20),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        results = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total_chunks = len(chunks)
            avg_length = (
                sum(len(c) for c in chunks) / total_chunks if total_chunks > 0 else 0.0
            )

            results[name] = {
                "chunks": chunks,
                "count": total_chunks,
                "avg_length": round(avg_length, 2),
            }

        return results