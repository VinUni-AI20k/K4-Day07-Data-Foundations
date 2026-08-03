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

        # A boundary consists of terminal punctuation followed by whitespace.
        # The lookbehind leaves that meaningful punctuation on the sentence.
        sentences = re.split(r"(?<=[.!?])(?:[ \t]+|\n+)", text.strip())
        sentences = [re.sub(r"\s+", " ", sentence).strip() for sentence in sentences]
        sentences = [sentence for sentence in sentences if sentence]

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
            return [text]
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]
        if not remaining_separators:
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        lower_priority = remaining_separators[1:]
        if separator == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]
        if separator not in current_text:
            return self._split(current_text, lower_priority)

        # Attach each separator to the preceding piece. This preserves all
        # source text while still allowing adjacent pieces to be packed.
        raw_pieces = current_text.split(separator)
        pieces = [
            piece + separator if index < len(raw_pieces) - 1 else piece
            for index, piece in enumerate(raw_pieces)
        ]

        chunks: list[str] = []
        pending = ""
        for piece in pieces:
            if not piece:
                continue
            if len(piece) > self.chunk_size:
                if pending:
                    chunks.append(pending)
                    pending = ""
                chunks.extend(self._split(piece, lower_priority))
            elif len(pending) + len(piece) <= self.chunk_size:
                pending += piece
            else:
                if pending:
                    chunks.append(pending)
                pending = piece

        if pending:
            chunks.append(pending)
        return chunks


class MarkdownHeadingChunker:
    """Split policy Markdown while retaining heading and clause context.

    Markdown headings form a hierarchy. Numbered policy labels such as ``3.``
    and ``3.2.`` form an additional clause hierarchy beneath it. Every chunk
    produced for a section starts with its active heading path and clause
    labels, including chunks created recursively from an oversized section.
    """

    _MARKDOWN_HEADING = re.compile(r"^\s*(#{1,6})\s+(.+?)\s*$")
    _NUMBERED_CLAUSE = re.compile(
        r"^\s*(?P<label>\d+(?:\.\d+)*[.)]?)(?:\s+)(?P<content>\S.*)$"
    )

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if self.chunk_size <= 0:
            return [text]

        sections = self._sectionize(text)
        chunks: list[str] = []
        for heading_context, body in sections:
            prefix = "\n".join(heading_context).strip()
            content = body.strip()
            if not prefix:
                chunks.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(content))
                continue

            complete_section = f"{prefix}\n{content}" if content else prefix
            if len(complete_section) <= self.chunk_size:
                chunks.append(complete_section)
                continue

            # Repeating the prefix is deliberate: a retrieved continuation
            # must still identify the policy section and numbered clause.
            body_size = max(1, self.chunk_size - len(prefix) - 1)
            body_chunks = RecursiveChunker(chunk_size=body_size).chunk(content)
            if not body_chunks:
                chunks.append(prefix)
            else:
                chunks.extend(f"{prefix}\n{piece.strip()}" for piece in body_chunks)
        return [chunk for chunk in chunks if chunk]

    def _sectionize(self, text: str) -> list[tuple[list[str], str]]:
        sections: list[tuple[list[str], str]] = []
        markdown_stack: list[tuple[int, str]] = []
        clause_stack: list[tuple[int, str]] = []
        current_context: list[str] = []
        current_body: list[str] = []

        def flush() -> None:
            nonlocal current_body
            body = "".join(current_body)
            if body.strip() or (current_context and not sections):
                sections.append((list(current_context), body))
            current_body = []

        for line in text.splitlines(keepends=True):
            clean_line = line.strip()
            markdown_match = self._MARKDOWN_HEADING.match(clean_line)
            clause_match = self._NUMBERED_CLAUSE.match(clean_line)

            if markdown_match:
                flush()
                level = len(markdown_match.group(1))
                markdown_stack = [item for item in markdown_stack if item[0] < level]
                markdown_stack.append((level, clean_line))
                clause_stack = []
                current_context = [heading for _, heading in markdown_stack]
            elif clause_match:
                flush()
                label = clause_match.group("label")
                numeric_label = label.rstrip(".)")
                level = numeric_label.count(".") + 1
                clause_stack = [item for item in clause_stack if item[0] < level]
                clause_stack.append((level, label))
                current_context = [heading for _, heading in markdown_stack]
                current_context.extend(item[1] for item in clause_stack)
                current_body.append(clause_match.group("content") + line[len(line.rstrip("\r\n")) :])
            else:
                current_body.append(line)

        flush()
        return sections


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
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=0),
            "by_sentences": SentenceChunker(),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }
        comparison = {}
        for name, strategy in strategies.items():
            chunks = strategy.chunk(text)
            comparison[name] = self._summarize(chunks)
        return comparison

    def compare_with_custom(self, text: str, chunk_size: int = 200) -> dict:
        """Compare the assigned custom strategy with all three baselines."""
        comparison = self.compare(text, chunk_size=chunk_size)
        custom_chunks = MarkdownHeadingChunker(chunk_size=chunk_size).chunk(text)
        comparison["markdown_heading_clause"] = self._summarize(custom_chunks)
        return comparison

    @staticmethod
    def _summarize(chunks: list[str]) -> dict:
        return {
            "count": len(chunks),
            "avg_length": sum(len(chunk) for chunk in chunks) / len(chunks) if chunks else 0.0,
            "chunks": chunks,
        }
