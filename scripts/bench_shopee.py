import sys
from pathlib import Path

# Ensure workspace root is on sys.path so `src` imports work when running this script
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.chunking import RecursiveChunker
from src.embeddings import _mock_embed
from src.agent import KnowledgeBaseAgent
from ingest import build_knowledge_base

# Strategy choice (single line to modify per-member)
chunker = RecursiveChunker(chunk_size=400)

# Build store from corpus
store = build_knowledge_base('data/k4_shopee', embedding_fn=_mock_embed, chunker=chunker)
agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: 'LLM would answer based on context.')

queries = [
    ("Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng?", None),
    ("Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu?", {"customer_role": "seller"}),
    ("Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển?", None),
    ("Tính năng 'Shopee Đảm Bảo' bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu?", None),
    ("Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì?", None),
]

print(f"Strategy: RecursiveChunker(chunk_size={chunker.chunk_size})")
print(f"Total chunks loaded: {store.get_collection_size()}")
print()

for i, (q, filt) in enumerate(queries, start=1):
    print(f"\n=== Query {i}: {q}")
    print(f"Metadata filter: {filt}")
    if filt is None:
        results = store.search(q, top_k=3)
    else:
        results = store.search_with_filter(q, top_k=3, metadata_filter=filt)
    if not results:
        print("No retrieval results.")
    else:
        for rank, r in enumerate(results, start=1):
            meta = r.get('metadata', {})
            doc_id = meta.get('doc_id')
            preview = (r.get('content') or '').replace('\n',' ')[:120]
            print(f"{rank}. score={r['score']:.4f} doc_id={doc_id} preview={preview}")
    answer = agent.answer(q, top_k=3)
    print(f"Agent answer: {answer}")
