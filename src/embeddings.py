"""Compatibility facade for the active personal implementation."""

from .K4_2A202601934_NguyenDangLong.embeddings import (
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)

EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"

__all__ = [
    "LOCAL_EMBEDDING_MODEL",
    "OPENAI_EMBEDDING_MODEL",
    "LocalEmbedder",
    "MockEmbedder",
    "OpenAIEmbedder",
    "_mock_embed",
    "EMBEDDING_PROVIDER_ENV",
]
