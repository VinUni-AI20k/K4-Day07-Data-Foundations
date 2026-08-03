from __future__ import annotations

import hashlib
import math

# Multilingual model suitable for the Vietnamese corpora used in this Lab.
# The local backend remains optional; required checkpoints use MockEmbedder.
LOCAL_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_PROVIDER_ENV = "EMBEDDING_PROVIDER"


class MockEmbedder:
    """Deterministic embedding backend used by tests and default classroom runs."""

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._backend_name = "mock embeddings fallback"

    def __call__(self, text: str) -> list[float]:
        digest = hashlib.md5(text.encode()).hexdigest()
        seed = int(digest, 16)
        vector = []
        for _ in range(self.dim):
            seed = (seed * 1664525 + 1013904223) & 0xFFFFFFFF
            vector.append((seed / 0xFFFFFFFF) * 2 - 1)
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class LocalEmbedder:
    """Sentence Transformers-backed local embedder."""

    def __init__(self, model_name: str = LOCAL_EMBEDDING_MODEL) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._backend_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, text: str) -> list[float]:
        embedding = self.model.encode(text, normalize_embeddings=True)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return [float(value) for value in embedding]


class OpenAIEmbedder:
    """OpenAI embeddings API-backed embedder."""

    def __init__(self, model_name: str = OPENAI_EMBEDDING_MODEL) -> None:
        from openai import OpenAI

        self.model_name = model_name
        self._backend_name = model_name
        self.client = OpenAI()

    def __call__(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model_name, input=text)
        return [float(value) for value in response.data[0].embedding]


BGE_M3_MODEL = "BAAI/bge-m3"


class BGEM3Embedder:
    """Local BGE-M3 dense embedder (đa ngôn ngữ, hợp corpus Việt/Anh của sản phẩm).

    Áp dụng ý tưởng từ embedding server tham khảo (BAAI/bge-m3) nhưng CHẠY LOCAL,
    in-process — không cần HTTP. Ưu tiên backend FlagEmbedding (BGEM3FlagModel, đúng
    như server); nếu môi trường không có thì fallback sang sentence-transformers.
    Trả về vector dense đã L2-normalize để dot == cosine, khớp EmbeddingStore.
    """

    def __init__(self, model_name: str = BGE_M3_MODEL, use_fp16: bool = False, device: str | None = None) -> None:
        self.model_name = model_name
        try:
            from FlagEmbedding import BGEM3FlagModel

            kwargs = {"use_fp16": use_fp16}
            if device:
                kwargs["device"] = device
            self._model = BGEM3FlagModel(model_name, **kwargs)
            self._impl = "flagembedding"
            self._backend_name = "bge-m3 (FlagEmbedding)"
        except Exception:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(model_name, device=device)
            self._impl = "sentence-transformers"
            self._backend_name = "bge-m3 (sentence-transformers)"

    def __call__(self, text: str) -> list[float]:
        if self._impl == "flagembedding":
            output = self._model.encode([text], return_dense=True, return_sparse=False)
            raw = output["dense_vecs"][0]
        else:
            raw = self._model.encode(text, normalize_embeddings=True)
        vector = raw.tolist() if hasattr(raw, "tolist") else [float(value) for value in raw]
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


_mock_embed = MockEmbedder()
