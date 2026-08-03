"""Recursive policy-section strategy owned by Luong Minh Quan."""

from src.chunking import RecursiveChunker


class SellerPolicyChunker(RecursiveChunker):
    """Use policy-friendly separators and moderate chunks for seller documents."""

    def __init__(self) -> None:
        super().__init__(chunk_size=420)
