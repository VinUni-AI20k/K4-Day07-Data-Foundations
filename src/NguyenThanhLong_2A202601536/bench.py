import os
from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.agent import KnowledgeBaseAgent

def main():
    # 1. Chọn chunker của riêng bạn, đây là DÒNG DUY NHẤT khác với bạn cùng nhóm
    chunker = RecursiveChunker(chunk_size=400)
    
    # 2. Nạp cả thư mục corpus. embedding_fn là tham số bắt buộc thứ hai.
    embedder = _mock_embed
    store = build_knowledge_base("data/k4_ecommerce", embedder, chunker=chunker)
    
    print(f"=== Strategy: RecursiveChunker(chunk_size=400) ===")
    print(f"Số chunk đã nạp: {store.get_collection_size()}\n")
    
    # 3. Chạy 5 query qua search()
    queries = [
        "Quy trình xử lý yêu cầu trả hàng?",
        "Thời gian nhận tiền hoàn là bao lâu?",
        "Hàng giả có được hoàn tiền không?",
        "Phí gửi hàng hoàn trả ai chịu?",
        "Có thể trả hàng vì không còn nhu cầu không?"
    ]
    
    agent = KnowledgeBaseAgent(store, llm_fn=lambda prompt: f"[DEMO LLM] {prompt[:100]}...")
    
    for q in queries:
        print(f"--- Câu hỏi: {q} ---")
        results = store.search(q, top_k=3)
        for i, res in enumerate(results, 1):
            doc_id = res['metadata'].get('doc_id', 'unknown')
            print(f"{i}. score={res['score']:.3f} source={doc_id}")
            print(f"   {res['content'][:80]}...")
        
        answer = agent.answer(q, top_k=3)
        print(f"Agent trả lời:\n{answer}\n")

if __name__ == "__main__":
    main()
