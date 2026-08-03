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
        # Split on sentence terminators (". ", "! ", "? ", ".\n") while keeping
        # the terminator attached to the sentence via a look-behind.
        pieces = re.split(r"(?<=[.!?])\s+", text.strip())
        sentences = [s.strip() for s in pieces if s.strip()]

        chunks: list[str] = []
        step = self.max_sentences_per_chunk
        for start in range(0, len(sentences), step):
            group = sentences[start : start + step]
            chunks.append(" ".join(group))
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
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # Base case 1: the text already fits inside chunk_size.
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        # Base case 2: no separators left (or the "" separator) -> hard split.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[i : i + self.chunk_size]
                for i in range(0, len(current_text), self.chunk_size)
                if current_text[i : i + self.chunk_size].strip()
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        pieces = current_text.split(separator)

        # Greedily merge neighbouring pieces back up to chunk_size so we keep
        # chunks as large (and coherent) as possible; recurse on oversized pieces.
        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            if len(piece) > self.chunk_size:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                chunks.extend(self._split(piece, rest))
                continue

            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = piece
        if buffer:
            chunks.append(buffer)

        return [c for c in chunks if c.strip()]


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
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size).chunk(text),
            "by_sentences": SentenceChunker().chunk(text),
            "recursive": RecursiveChunker(chunk_size=chunk_size).chunk(text),
        }

        comparison: dict = {}
        for name, chunks in strategies.items():
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": avg_length,
                "chunks": chunks,
            }
        return comparison


class HeadingChunker:
    """Chiến lược tùy chỉnh: chia Markdown theo ranh giới TIÊU ĐỀ (#, ##, ###...).

    Lý do thiết kế (cho corpus K4 ASOS product listings):
        - Thân tài liệu có cấu trúc heading rõ ràng: `## Thong tin san pham`,
          `### Dac diem`, `### Look After Me`, `### About Me`, `### Brand`...
          Mỗi mục là một ý trọn vẹn (giá / đặc điểm / bảo quản / chất liệu).
        - Chia theo heading giữ "chunk coherence": không cắt ngang giữa mục như
          FixedSize/Recursive, nên chunk vừa mạch lạc vừa dễ truy vết.
        - Bỏ FOOTER nguồn/license ("Nguon: [url] ...") vì đó là boilerplate làm
          nhiễu embedding (URL dài, câu về dataset), không phải nội dung sản phẩm.

    Cơ chế:
        1. Loại footer (dòng bắt đầu bằng footer marker + rule `---` ở đuôi).
        2. Gom các dòng thành từng "mục" bắt đầu tại mỗi dòng tiêu đề.
        3. Gộp tham lam các mục nhỏ liền kề tới ~max_chars; tách mục quá lớn.
    """

    _HEADING = re.compile(r"^#{1,6}\s")

    def __init__(
        self,
        max_chars: int = 500,
        drop_footer: bool = True,
        footer_markers: tuple[str, ...] = ("Nguon:", "Nguồn:", "Thu thap qua dataset", "Source:"),
    ) -> None:
        self.max_chars = max(1, max_chars)
        self.drop_footer = drop_footer
        self.footer_markers = tuple(footer_markers)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        lines = text.splitlines()
        if self.drop_footer:
            lines = self._strip_footer(lines)
        sections = self._split_sections(lines)
        return self._pack(sections)

    def _strip_footer(self, lines: list[str]) -> list[str]:
        cut = len(lines)
        for index, line in enumerate(lines):
            stripped = line.strip()
            if any(stripped.startswith(marker) for marker in self.footer_markers):
                cut = index
                break
        trimmed = lines[:cut]
        # Bỏ thematic break / dòng trống thừa ở đuôi (thường đứng trước footer).
        while trimmed and trimmed[-1].strip() in ("", "---", "***", "___"):
            trimmed.pop()
        return trimmed

    def _split_sections(self, lines: list[str]) -> list[str]:
        sections: list[str] = []
        current: list[str] = []
        for line in lines:
            if self._HEADING.match(line) and current:
                section = "\n".join(current).strip()
                if section:
                    sections.append(section)
                current = [line]
            else:
                current.append(line)
        section = "\n".join(current).strip()
        if section:
            sections.append(section)
        return sections

    def _pack(self, sections: list[str]) -> list[str]:
        chunks: list[str] = []
        buffer = ""
        for section in sections:
            if len(section) > self.max_chars:
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                chunks.extend(self._split_large_section(section))
                continue
            candidate = section if not buffer else buffer + "\n\n" + section
            if len(candidate) <= self.max_chars:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                buffer = section
        if buffer:
            chunks.append(buffer)
        return [c for c in chunks if c.strip()]

    def _split_large_section(self, section: str) -> list[str]:
        # Mục vượt max_chars: giữ dòng TIÊU ĐỀ gắn vào MỌI mảnh con để không mất
        # ngữ cảnh (mỗi mảnh vẫn biết mình thuộc mục nào).
        lines = section.splitlines()
        if lines and self._HEADING.match(lines[0]):
            heading, body = lines[0], "\n".join(lines[1:]).strip()
        else:
            heading, body = "", section
        prefix = f"{heading}\n" if heading else ""
        budget = max(1, self.max_chars - len(prefix))
        pieces = self._pack_lines(body, budget)
        result = [(prefix + piece).strip() for piece in pieces if piece.strip()]
        return result or ([heading] if heading.strip() else [])

    def _pack_lines(self, text: str, budget: int) -> list[str]:
        out: list[str] = []
        buffer = ""
        for line in text.splitlines():
            while len(line) > budget:  # dòng đơn quá dài -> cắt cứng theo ký tự
                if buffer:
                    out.append(buffer)
                    buffer = ""
                out.append(line[:budget])
                line = line[budget:]
            candidate = line if not buffer else buffer + "\n" + line
            if len(candidate) <= budget:
                buffer = candidate
            else:
                if buffer:
                    out.append(buffer)
                buffer = line
        if buffer:
            out.append(buffer)
        return out
