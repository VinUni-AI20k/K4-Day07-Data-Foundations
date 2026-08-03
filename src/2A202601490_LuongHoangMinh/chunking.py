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
        if not text:
            return []
        # split on ". ", "! ", "? " or ".\n", keep the punctuation in the preceding sentence
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
        limit = self.max_sentences_per_chunk
        return [" ".join(sentences[index : index + limit]) for index in range(0, len(sentences), limit)]


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
        raw_chunks = self._split(text, self.separators)
        return [c.strip() for c in raw_chunks if c.strip()]

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
        
        if not remaining_separators or remaining_separators[0] == "":
            return [current_text[i:i+self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        sep = remaining_separators[0]
        next_seps = remaining_separators[1:]
        
        if sep not in current_text:
            return self._split(current_text, next_seps)
            
        splits = current_text.split(sep)
        chunks = []
        current_chunk = ""
        
        for piece in splits:
            if len(piece) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                chunks.extend(self._split(piece, next_seps))
            else:
                if not current_chunk:
                    current_chunk = piece
                else:
                    if len(current_chunk) + len(sep) + len(piece) <= self.chunk_size:
                        current_chunk += sep + piece
                    else:
                        chunks.append(current_chunk)
                        current_chunk = piece
                        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks


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
        fc = FixedSizeChunker(chunk_size=chunk_size, overlap=20)
        sc = SentenceChunker(max_sentences_per_chunk=3)
        rc = RecursiveChunker(chunk_size=chunk_size)
        
        res_fc = fc.chunk(text)
        res_sc = sc.chunk(text)
        res_rc = rc.chunk(text)
        
        def stats(chunks: list[str]) -> dict:
            if not chunks:
                return {"count": 0, "avg_length": 0.0, "chunks": []}
            avg = sum(len(c) for c in chunks) / len(chunks)
            return {"count": len(chunks), "avg_length": avg, "chunks": chunks}
            
        return {
            "fixed_size": stats(res_fc),
            "by_sentences": stats(res_sc),
            "recursive": stats(res_rc)
        }
