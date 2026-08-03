from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base
from src import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    KnowledgeBaseAgent,
    LocalEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.custom_chunking import HeadingChunker

DEFAULT_DATA_DIR = "data/k4_ecommerce"


def select_embedder():
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as exc:
            print(f"Local embedder chưa sẵn sàng ({exc}); dùng mock để demo.")
    if provider == "openai":
        try:
            return OpenAIEmbedder(os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception as exc:
            print(f"OpenAI embedder chưa sẵn sàng ({exc}); dùng mock để demo.")
    return _mock_embed


def demo_llm(prompt: str) -> str:
    return "[DEMO] " + prompt[:500].replace("\n", " ") + "..."


def main() -> int:
    load_dotenv(override=False)
    data_dir = os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR)
    if not Path(data_dir).exists():
        print(f"Không tìm thấy {data_dir}")
        return 1
    embedder = select_embedder()
    store = build_knowledge_base(data_dir, embedder, chunker=HeadingChunker())
    question = " ".join(sys.argv[1:]).strip() or "T-Hexa hỗ trợ phương thức thanh toán nào?"
    print(f"Loaded {store.get_collection_size()} chunks")
    for item in store.search(question, top_k=3):
        print(f"score={item['score']:.4f} doc={item['metadata'].get('doc_id')}: {item['content'][:120]}")
    print(KnowledgeBaseAgent(store, demo_llm).answer(question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
