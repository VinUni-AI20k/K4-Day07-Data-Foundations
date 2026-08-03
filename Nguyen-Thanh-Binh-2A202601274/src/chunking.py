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

    # Cắt SAU dấu kết câu (. ! ?) khi ngay sau đó là khoảng trắng/xuống dòng.
    # Lookbehind giữ dấu câu lại với câu đứng trước, nên chunk vẫn đọc được tự nhiên.
    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [part.strip() for part in self._SENTENCE_BOUNDARY.split(text)]
        sentences = [sentence for sentence in sentences if sentence]
        if not sentences:
            return []

        chunks: list[str] = []
        size = self.max_sentences_per_chunk
        for start in range(0, len(sentences), size):
            group = " ".join(sentences[start : start + size]).strip()
            if group:
                chunks.append(group)
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
        if not text or not text.strip():
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text or not current_text.strip():
            return []

        # Base case 1: đoạn đã đủ nhỏ -> giữ nguyên.
        if len(current_text) <= self.chunk_size:
            return [current_text.strip()]

        # Base case 2: hết separator (hoặc separator rỗng "") -> cắt cứng theo ký tự.
        if not remaining_separators or remaining_separators[0] == "":
            return self._hard_split(current_text)

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        raw_pieces = current_text.split(separator)

        # Separator không xuất hiện -> hạ xuống separator ưu tiên thấp hơn.
        if len(raw_pieces) == 1:
            return self._split(current_text, rest)

        # split() ăn mất separator. Gắn nó lại vào CUỐI mảnh đứng trước để dấu kết câu
        # của separator ". " không bị mất khi mảnh đó bị chốt thành chunk riêng.
        pieces = [piece + separator for piece in raw_pieces[:-1]] + [raw_pieces[-1]]

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = buffer + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            # candidate vượt ngưỡng: chốt buffer hiện tại rồi xử lý piece riêng.
            if buffer.strip():
                chunks.append(buffer.strip())
            buffer = ""

            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                chunks.extend(self._split(piece, rest))

        if buffer.strip():
            chunks.append(buffer.strip())
        return [chunk for chunk in chunks if chunk]

    def _hard_split(self, text: str) -> list[str]:
        """Cắt theo đúng chunk_size ký tự — lưới an toàn cuối cùng của đệ quy."""
        pieces = [text[start : start + self.chunk_size].strip() for start in range(0, len(text), self.chunk_size)]
        return [piece for piece in pieces if piece]


class ClauseChunker:
    """Chia theo ĐIỀU/KHOẢN của văn bản chính sách — chiến lược tuỳ chỉnh cho K4.

    Lý do thiết kế: corpus K4 là chính sách TMĐT dạng Markdown, trong đó mỗi câu
    thường là một nghĩa vụ độc lập và gắn với MỘT chủ thể (người mua / người bán).
    Ba chunker có sẵn đều cắt theo độ dài hoặc theo số câu cố định nên hay gộp
    nghĩa vụ của hai chủ thể vào chung một chunk, khiến agent trích nhầm câu.

    Chiến lược:
      1. Cắt tại ranh giới CẤU TRÚC ở đầu dòng: tiêu đề Markdown (``#``), gạch đầu
         dòng, khoản đánh số (``1.``/``2)``), dòng trống, khối trích dẫn (``>``).
      2. Trong mỗi khối, tách câu và gom tối đa ``max_sentences_per_clause`` câu.
      3. Gắn tiêu đề gần nhất làm tiền tố để mỗi chunk TỰ ĐỦ NGHĨA khi bị lấy ra
         khỏi tài liệu (ví dụ "Đăng bán sản phẩm: Người bán chịu trách nhiệm...").

    ``drop_quotes=True`` bỏ khối ``>`` — trong văn bản chính sách, blockquote
    thường là ghi chú biên tập chứ không phải điều khoản. Đây là đánh đổi có rủi
    ro: nguồn nào dùng blockquote cho nội dung thật sẽ bị mất dữ liệu.
    """

    _HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*)$")
    _BULLET = re.compile(r"^\s{0,3}(?:[-*+]\s+|\d+[.)]\s+)")
    _QUOTE = re.compile(r"^\s{0,3}>")
    _SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

    def __init__(
        self,
        max_sentences_per_clause: int = 1,
        keep_heading: bool = True,
        drop_quotes: bool = False,
    ) -> None:
        self.max_sentences_per_clause = max(1, max_sentences_per_clause)
        self.keep_heading = keep_heading
        self.drop_quotes = drop_quotes

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        blocks: list[tuple[str, str]] = []
        buffer: list[str] = []
        heading = ""

        def flush() -> None:
            block = "\n".join(buffer).strip()
            if block:
                blocks.append((heading, block))
            buffer.clear()

        for line in text.splitlines():
            heading_match = self._HEADING.match(line)
            if heading_match:
                flush()
                heading = heading_match.group(1).strip()
                continue
            if not line.strip():
                flush()
                continue
            if self._QUOTE.match(line):
                flush()
                if not self.drop_quotes:
                    blocks.append((heading, line.lstrip().lstrip(">").strip()))
                continue
            if self._BULLET.match(line):
                if buffer:
                    flush()
                line = self._BULLET.sub("", line, count=1)  # bỏ ký hiệu "-"/"1." khỏi nội dung
            buffer.append(line)
        flush()

        chunks: list[str] = []
        for block_heading, block_text in blocks:
            sentences = [part.strip() for part in self._SENTENCE_BOUNDARY.split(block_text)]
            sentences = [sentence for sentence in sentences if sentence]
            for start in range(0, len(sentences), self.max_sentences_per_clause):
                body = " ".join(sentences[start : start + self.max_sentences_per_clause]).strip()
                if not body:
                    continue
                chunks.append(f"{block_heading}: {body}" if (self.keep_heading and block_heading) else body)
        return chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        overlap = max(0, chunk_size // 10)
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=overlap),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            count = len(chunks)
            avg_length = (sum(len(chunk) for chunk in chunks) / count) if count else 0.0
            comparison[name] = {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }
        return comparison
