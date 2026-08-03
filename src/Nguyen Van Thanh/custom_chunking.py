from __future__ import annotations

import re

from .chunking import FixedSizeChunker


class HeadingChunker:
    """Chunk Markdown policies by headings/clauses, then cap long sections.

    This custom K4 strategy keeps each policy heading with its body so retrieved
    chunks are coherent and easy to cite during the demo.
    """

    def __init__(self, chunk_size: int = 700, overlap: int = 60) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        text = text.strip()
        if not text:
            return []
        parts = re.split(r"(?=^#{1,4}\s+)", text, flags=re.MULTILINE)
        sections = [part.strip() for part in parts if part.strip()]
        chunks: list[str] = []
        fallback = FixedSizeChunker(chunk_size=self.chunk_size, overlap=self.overlap)
        for section in sections:
            if len(section) <= self.chunk_size:
                chunks.append(section)
            else:
                chunks.extend(fallback.chunk(section))
        return chunks
