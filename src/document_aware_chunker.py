from __future__ import annotations

import re
from dataclasses import dataclass

from .chunking import RecursiveChunker


@dataclass
class _Section:
    path: list[str]
    lines: list[str]


class DocumentAwareChunker:
    """Chunk Markdown documents by heading-defined sections."""

    HEADING_RE = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, max_chunk_size: int = 700) -> None:
        self.max_chunk_size = max(1, max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []

        sections = self._parse_sections(text)
        if not sections:
            return self._fallback_chunks("Document", text)

        chunks: list[str] = []
        for section in sections:
            section_text = "\n".join(line.rstrip() for line in section.lines).strip()
            if not section_text:
                continue
            path = " > ".join(section.path) if section.path else "Document"
            chunks.extend(self._section_to_chunks(path, section_text))
        return [chunk for chunk in chunks if chunk.strip()]

    def _parse_sections(self, text: str) -> list[_Section]:
        sections: list[_Section] = []
        heading_stack: dict[int, str] = {}
        current: _Section | None = None
        preamble: list[str] = []

        for line in text.splitlines():
            match = self.HEADING_RE.match(line)
            if not match:
                if current is None:
                    preamble.append(line)
                else:
                    current.lines.append(line)
                continue

            if current is not None:
                sections.append(current)
            elif any(item.strip() for item in preamble):
                sections.append(_Section(path=["Document"], lines=preamble))
                preamble = []

            level = len(match.group(1))
            title = match.group(2).strip()
            for stored_level in list(heading_stack):
                if stored_level >= level:
                    del heading_stack[stored_level]
            heading_stack[level] = title
            path = [heading_stack[index] for index in sorted(heading_stack) if index <= level]
            current = _Section(path=path, lines=[line])

        if current is not None:
            sections.append(current)
        elif any(item.strip() for item in preamble):
            sections.append(_Section(path=["Document"], lines=preamble))

        return sections

    def _section_to_chunks(self, heading_path: str, section_text: str) -> list[str]:
        prefix = f"[Heading path: {heading_path}]\n\n"
        if len(prefix + section_text) <= self.max_chunk_size:
            return [prefix + section_text]
        return self._fallback_chunks(heading_path, section_text)

    def _fallback_chunks(self, heading_path: str, text: str) -> list[str]:
        prefix = f"[Heading path: {heading_path}]\n\n"
        available_size = self.max_chunk_size - len(prefix)
        if available_size <= 0:
            return [prefix + text.strip()] if text.strip() else []

        fallback = RecursiveChunker(separators=self.DEFAULT_SEPARATORS, chunk_size=available_size)
        return [
            prefix + piece
            for piece in fallback.chunk(text)
            if piece.strip()
        ]
