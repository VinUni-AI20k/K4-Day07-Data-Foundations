"""
bench.py — Script đánh giá RAG Benchmark (K4 Variant: E-commerce Policy Retrieval)

Chạy từ thư mục gốc:
    uv run python bench.py

Sử dụng:
- Embeddings: Hugging Face API (dùng HF_TOKEN) / LocalEmbedder
- LLM: Nvidia API (dùng NVIDIA_API_KEY) / fallback demo LLM
- Bộ câu hỏi: 5 benchmark queries trong data/benchmark_queries.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Đảm bảo mã hóa UTF-8 cho Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(dotenv_path=PROJECT_ROOT / ".env", override=True)

from data.benchmark_queries import BENCHMARK_QUERIES
from ingest import build_knowledge_base
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker
from src.embeddings import (
    HuggingFaceEmbedder,
    LocalEmbedder,
    _mock_embed,
)


def select_embedder():
    """Tự động chọn Embedder tốt nhất từ cấu hình .env."""
    provider = os.getenv("EMBEDDING_PROVIDER", "huggingface").strip().lower()
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")

    if provider == "huggingface" and hf_token:
        try:
            embedder = HuggingFaceEmbedder(token=hf_token)
            # Smoke test
            _ = embedder("test")
            return embedder
        except Exception as err:
            print(f"Lỗi khởi tạo Hugging Face Embedder: {err}, dùng LocalEmbedder.")

    try:
        return LocalEmbedder()
    except Exception:
        print("LocalEmbedder không sẵn sàng, dùng MockEmbedder.")
        return _mock_embed


def select_llm():
    """Tự động chọn LLM từ Nvidia API nếu có NVIDIA_API_KEY trong .env."""
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nvidia_key,
                timeout=60.0,
            )
            model_name = os.getenv("NVIDIA_LLM_MODEL", "meta/llama-3.1-8b-instruct")

            def nvidia_llm_fn(prompt: str) -> str:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=512,
                )
                return response.choices[0].message.content

            return nvidia_llm_fn, f"Nvidia API ({model_name})"
        except Exception as err:
            print(f"Lỗi kết nối Nvidia LLM: {err}")

    def fallback_llm(prompt: str) -> str:
        return f"[DEMO LLM] Context length: {len(prompt)} chars"

    return fallback_llm, "Demo Mock LLM"


def run_benchmark(data_dir: str = "data/k4_ecommerce") -> int:
    print("=" * 60)
    print("=== CHẠY DÁNH GIÁ RAG BENCHMARK (K4 VARIANT) ===")
    print("=" * 60)

    if not Path(data_dir).exists():
        print(f"Không tìm thấy thư mục dữ liệu: {data_dir}")
        return 1

    embedder = select_embedder()
    backend_name = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"1. Backend Embeddings: {backend_name}")

    llm_fn, llm_name = select_llm()
    print(f"2. Backend LLM: {llm_name}")

    from src.chunking import SentenceChunker

    chunker = SentenceChunker(max_sentences_per_chunk=3)
    print(f"3. Nạp dữ liệu từ: {data_dir} (Dùng SentenceChunker, max_sentences=3)")
    store = build_knowledge_base(data_dir, embedding_fn=embedder, chunker=chunker, collection_name="bench_sentence_store")
    print(f"   Đã nạp {store.get_collection_size()} chunks vào Vector Store.\n")

    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)

    output_lines = []
    output_lines.append("# BÁO CÁO KẾT QUẢ RAG BENCHMARK (bench.py)\n")
    output_lines.append(f"- **Embedding Provider:** `{backend_name}`")
    output_lines.append(f"- **LLM Provider:** `{llm_name}`")
    output_lines.append(f"- **Tổng số Chunks:** `{store.get_collection_size()}`\n")

    print("=" * 60)
    print("=== KẾT QUẢ THỰC THI 5 BENCHMARK QUERIES ===")
    print("=" * 60)

    for idx, item in enumerate(BENCHMARK_QUERIES, 1):
        q_id = item["id"]
        query = item["query"]
        filt = item["metadata_filter"]
        rel_doc = item["relevant_doc_id"]
        gold = item["gold_answer"]

        print(f"\n[{idx}/5] Query: {q_id}")
        print(f"    Câu hỏi: {query}")
        print(f"    Filter: {filt}")

        results = store.search_with_filter(query, top_k=3, metadata_filter=filt)
        top1 = results[0] if results else None
        top1_doc = top1["metadata"].get("doc_id") if top1 else "N/A"
        top1_score = top1["score"] if top1 else 0.0
        top1_content = top1["content"].replace("\n", " ") if top1 else "N/A"

        found_relevant = any(r["metadata"].get("doc_id") == rel_doc for r in results)
        print(f"    Doc kỳ vọng: {rel_doc} | Doc tìm thấy: {top1_doc} (Score: {top1_score:.4f})")
        print(f"    Có trong Top-3: {'ĐÚNG' if found_relevant else 'SAI'}")

        print("    Đang gọi LLM sinh câu trả lời...")
        answer = agent.answer(query, top_k=3)
        print(f"    Trả lời từ LLM:\n    > {answer[:120]}...\n")

        output_lines.append(f"### Query {idx}: {q_id}")
        output_lines.append(f"- **Câu hỏi:** {query}")
        output_lines.append(f"- **Metadata Filter:** `{filt}`")
        output_lines.append(f"- **Doc kỳ vọng / Doc tìm thấy:** `{rel_doc}` / `{top1_doc}` (Score: `{top1_score:.4f}`)")
        output_lines.append(f"- **Top-1 Content:** {top1_content[:200]}...")
        output_lines.append(f"- **Gold Answer:**\n  > {gold}")
        output_lines.append(f"- **Real LLM Answer:**\n  > {answer}\n")

    report_path = PROJECT_ROOT / "real_benchmark_output.txt"
    report_path.write_text("\n".join(output_lines), encoding="utf-8")
    print("=" * 60)
    print(f"Đã lưu báo cáo benchmark đầy đủ vào: {report_path.name}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_benchmark())
