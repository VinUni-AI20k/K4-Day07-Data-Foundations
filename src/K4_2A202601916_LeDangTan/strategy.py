"""Fixed-size overlap strategy owned by Le Dang Tan."""

from src.chunking import FixedSizeChunker


class MetadataFixedChunker(FixedSizeChunker):
    """Use fixed windows to provide a controlled baseline for metadata filters."""

    def __init__(self) -> None:
        super().__init__(chunk_size=360, overlap=80)
