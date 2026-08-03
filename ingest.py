"""Pipeline: front matter -> Document -> chunks -> EmbeddingStore."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.chunking import FixedSizeChunker
from src.models import Document
from src.store import EmbeddingStore

TEXT_EXTENSIONS = {".md", ".txt"}


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if closing is None:
        return {}, text
    block = "\n".join(lines[1:closing])
    body = "\n".join(lines[closing + 1 :]).lstrip("\n")
    return _load_flat_yaml(block), body


def _load_flat_yaml(block: str) -> dict:
    try:
        import yaml

        loaded = yaml.safe_load(block) or {}
        if isinstance(loaded, dict):
            return {str(key): value for key, value in loaded.items()}
    except Exception:
        pass

    metadata: dict = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.split(" #", 1)[0].strip().strip('"').strip("'")
        metadata[key.strip()] = value
    return metadata


def load_documents(data_dir: str | Path) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(Path(data_dir).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        doc_id = str(metadata.get("doc_id") or path.stem)
        metadata.setdefault("doc_id", doc_id)
        metadata.setdefault("source", str(path))
        documents.append(Document(id=doc_id, content=body, metadata=metadata))
    return documents


def chunk_document(doc: Document, chunker) -> list[Document]:
    chunks = []
    for index, piece in enumerate(chunker.chunk(doc.content)):
        metadata = dict(doc.metadata)
        metadata["doc_id"] = doc.id
        metadata["chunk_index"] = index
        chunks.append(Document(id=f"{doc.id}::chunk_{index}", content=piece, metadata=metadata))
    return chunks


def build_knowledge_base(
    data_dir: str | Path,
    embedding_fn: Callable[[str], list[float]],
    chunker=None,
    collection_name: str = "lab7_kb",
) -> EmbeddingStore:
    chunker = chunker or FixedSizeChunker()
    all_chunks: list[Document] = []
    for document in load_documents(data_dir):
        all_chunks.extend(chunk_document(document, chunker))
    store = EmbeddingStore(collection_name=collection_name, embedding_fn=embedding_fn)
    store.add_documents(all_chunks)
    return store


if __name__ == "__main__":
    metadata, body = parse_front_matter("---\ndoc_id: demo\nrole: buyer\n---\nNội dung")
    assert metadata["doc_id"] == "demo" and body == "Nội dung"
    print("ingest self-check OK")
