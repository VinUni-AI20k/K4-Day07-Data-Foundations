"""FAQ-section strategy owned by Vu Huu An."""

from src.chunking import SentenceChunker


class FAQSectionChunker(SentenceChunker):
    """Keep short FAQ-style answers together while respecting sentence boundaries."""

    def __init__(self) -> None:
        super().__init__(max_sentences_per_chunk=5)
