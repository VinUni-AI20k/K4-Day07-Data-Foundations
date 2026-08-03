"""Sentence-group strategy owned by Dao Minh Chien."""

from src.chunking import SentenceChunker


class BuyerSentenceChunker(SentenceChunker):
    """Group a small number of complete sentences for buyer questions."""

    def __init__(self, sentences_per_chunk: int = 3) -> None:
        super().__init__(max_sentences_per_chunk=sentences_per_chunk)
