import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set module path to load the student's personal package
os.environ["LAB_SOLUTION_PACKAGE"] = "src.2A202601490_LuongHoangMinh"

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.agent import KnowledgeBaseAgent
from main import demo_llm

def run_benchmark():
    print("=== CHẠY BENCHMARK CÁ NHÂN ===")
    
    # 1. Chọn chunker của riêng bạn
    chunker = RecursiveChunker(chunk_size=400)
    print(f"Chiến lược (Strategy): RecursiveChunker(chunk_size=400)\n")

    # 2. Nạp cả thư mục corpus
    store = build_knowledge_base("data/k4_ecommerce", _mock_embed, chunker=chunker)
    print(f"Số chunk đã nạp vào Store: {store.get_collection_size()}\n")
    
    # Khởi tạo Agent
    agent = KnowledgeBaseAgent(store, llm_fn=demo_llm)

    # 3. Chạy 5 query đã chốt
    queries = [
        {
            "q": "Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store?",
            "filter": None
        },
        {
            "q": "Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không?",
            "filter": None
        },
        {
            "q": "Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không?",
            "filter": None
        },
        {
            "q": "Tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không?",
            "filter": {"customer_role": "buyer"}
        },
        {
            "q": "Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không?",
            "filter": {"customer_role": "both"}
        }
    ]

    for i, item in enumerate(queries, 1):
        q = item["q"]
        f = item["filter"]
        print("-" * 50)
        print(f"Query {i}: {q}")
        if f:
            print(f"Filter: {f}")
            results = store.search_with_filter(q, top_k=3, metadata_filter=f)
        else:
            results = store.search(q, top_k=3)
            
        print("Top-3 Chunks Retrieval:")
        for rank, res in enumerate(results, 1):
            doc_id = res["metadata"].get("doc_id", "unknown")
            preview = res["content"][:80].replace("\n", " ") + "..."
            print(f"  {rank}. score={res['score']:.3f} | doc={doc_id} | preview={preview}")
            
        answer = agent.answer(q, top_k=3, metadata_filter=f)
        print(f"\nCâu trả lời của Agent:\n{answer}\n")

if __name__ == "__main__":
    run_benchmark()
