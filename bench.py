import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct execution
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker
from src.embeddings import LocalEmbedder, _mock_embed
from src.agent import KnowledgeBaseAgent

provider = os.getenv('EMBEDDING_PROVIDER', 'mock').strip().lower()
if provider == 'local':
    try:
        embedder = LocalEmbedder()
    except Exception as exc:
        print(f'Warning: local embedder initialization failed: {exc}')
        print('Falling back to mock embedder.')
        embedder = _mock_embed
else:
    embedder = _mock_embed

chunker = RecursiveChunker(chunk_size=400)

store = build_knowledge_base('data/k4_shopee', embedding_fn=embedder, chunker=chunker)
agent = KnowledgeBaseAgent(store=store, llm_fn=lambda prompt: 'LLM would answer based on context.')

benchmark_queries = [
    {
        'query': 'Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng?',
        'metadata_filter': None,
        'gold_answer': 'Người mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ khi đơn hàng được cập nhật trạng thái giao hàng thành công; với thực phẩm tươi sống và đông lạnh là trong vòng 24 giờ.',
        'expected_doc_id': 'chinh-sach-tra-hang-hoan-tien',
        'expected_evidence': '15 ngày',
    },
    {
        'query': 'Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu?',
        'metadata_filter': {'customer_role': 'seller'},
        'gold_answer': 'Người bán Shopee Mall phải đảm bảo hàng chính hãng, không đăng bán hàng giả/hàng nhái; nếu vi phạm có thể bị xử lý phạt, khóa ví và đóng băng tài khoản theo quy định của Shopee Mall.',
        'expected_doc_id': 'dieu-khoan-dich-vu-shopee-mall',
        'expected_evidence': 'hàng giả',
    },
    {
        'query': 'Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển?',
        'metadata_filter': None,
        'gold_answer': 'Shopee cho phép từ chối nhận hàng khi đồng kiểm nếu hàng có dấu hiệu hư hỏng hoặc sai so với mô tả; người mua được kiểm tra ngoại quan trước khi nhận.',
        'expected_doc_id': 'quy-dinh-chung-tra-hang-hoan-tien',
        'expected_evidence': 'đồng kiểm',
    },
    {
        'query': "Tính năng 'Shopee Đảm Bảo' bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu?",
        'metadata_filter': None,
        'gold_answer': 'Shopee Đảm Bảo bảo vệ người mua bằng cách cho phép yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày và giữ tiền thanh toán cho đến khi khiếu nại được xử lý.',
        'expected_doc_id': 'shopee-dam-bao',
        'expected_evidence': 'Shopee Đảm Bảo',
    },
    {
        'query': 'Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì?',
        'metadata_filter': None,
        'gold_answer': 'Đơn hàng hoàn trả phải được đóng gói an toàn, đầy đủ giấy tờ, vật liệu bảo vệ và tuân thủ quy cách đóng gói của Shopee để tránh hư hỏng.',
        'expected_doc_id': 'cach-dong-goi-don-hoan-tra',
        'expected_evidence': 'đóng gói',
    },
]

print(f'Embedder: {_mock_embed._backend_name}')
print(f'Strategy: RecursiveChunker(chunk_size={chunker.chunk_size})')
print(f'Total chunks loaded: {store.get_collection_size()}')
print()


def format_result(result: dict[str, object]) -> str:
    content_preview = (result.get('content') or '').replace('\n', ' ')
    doc_id = result.get('metadata', {}).get('doc_id')
    return f'score={result["score"]:.4f} doc_id={doc_id} preview={content_preview[:140]}'


def evidence_in_results(results: list[dict[str, object]], evidence: str) -> bool:
    evidence_lower = evidence.lower()
    for r in results:
        if evidence_lower in (r.get('content') or '').lower():
            return True
    return False


def print_results(results: list[dict[str, object]]) -> None:
    if not results:
        print('  No retrieval results.')
        return
    for rank, result in enumerate(results, start=1):
        print(f'  {rank}. {format_result(result)}')


for index, query_spec in enumerate(benchmark_queries, start=1):
    query = query_spec['query']
    metadata_filter = query_spec['metadata_filter']
    expected_doc_id = query_spec['expected_doc_id']
    expected_evidence = query_spec['expected_evidence']

    print(f'Query {index}: {query}')
    print(f'Expected evidence token: {expected_evidence}')
    print(f'Expected doc_id: {expected_doc_id}')

    results_no_filter = store.search(query, top_k=3)
    evidence_no_filter = evidence_in_results(results_no_filter, expected_evidence)

    print('Search without filter:')
    print_results(results_no_filter)
    print(f'  Evidence in top-3 without filter: {evidence_no_filter}')

    if metadata_filter:
        results_with_filter = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
        evidence_with_filter = evidence_in_results(results_with_filter, expected_evidence)
        print('Search with filter:')
        print_results(results_with_filter)
        print(f'  Evidence in top-3 with filter: {evidence_with_filter}')
        same_results = [r['id'] for r in results_no_filter] == [r['id'] for r in results_with_filter]
        print(f'  Filter changed results: {not same_results}')
    else:
        results_with_filter = results_no_filter
        evidence_with_filter = evidence_no_filter

    top1_same = bool(results_with_filter and results_with_filter[0].get('metadata', {}).get('doc_id') == expected_doc_id)
    print(f'  Top-1 matches expected doc_id: {top1_same}')
    answer = agent.answer(query, top_k=3)
    print(f'Agent answer: {answer}')
    print('-' * 80)
