"""Recursive product-section strategy owned by Luong Minh Quan."""

from src.chunking import RecursiveChunker


class ProductRecursiveChunker(RecursiveChunker):
    """Use recursive separators and moderate chunks for product descriptions."""

    def __init__(self) -> None:
        super().__init__(chunk_size=420)
