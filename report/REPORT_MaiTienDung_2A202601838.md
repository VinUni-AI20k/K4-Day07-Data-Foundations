# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Mai Tiến Dũng

**Nhóm:** MicroGenius

**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Hai vector có hướng gần nhau, thường biểu diễn nội dung/ngữ nghĩa tương đồng.*

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi thích học Python.
- Câu B: Python là ngôn ngữ lập trình tôi yêu thích.
- Tại sao tương đồng: 2 câu đều mang nghĩa tương đương (nhân vật tôi thích "Python")

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi thích học Python.
- Câu B: Hôm nay trời mưa rất to.
- Tại sao khác: Hai câu mang nghĩa hoàn toàn khác nhau, không có liên quan gì đến nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Cosine similarity thường được ưu tiên cho text embeddings vì nó đo hướng của vector, tức là mức độ giống nhau về ngữ nghĩa, thay vì bị ảnh hưởng nhiều bởi độ lớn của vector như khoảng cách Euclide*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *step = 500 - 50 = 450, số chunk = ceil((10000 - 50) / 450)*
> *Đáp án: 23 chunk*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Nếu overlap tăng lên 100, step = 500 - 100 = 400, số chunk = ceil((10000 - 100) / 400) = 25 (chunks)*
> *Overlap lớn hơn giúp giữ lại nhiều ngữ cảnh ở ranh giới giữa hai chunk, nhưng đồng thời làm tăng số chunk và chi phí embedding/lưu trữ.*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`FixedSizeChunker` — baseline:**
> *Đây là chiến lược cơ sở được cung cấp sẵn. Văn bản được cắt theo số ký tự cố định `chunk_size=500`; các chunk kế tiếp có thể dùng `overlap=50` để giữ lại một phần ngữ cảnh ở ranh giới. Ưu điểm là đơn giản, tốc độ ổn định và dễ dự đoán số lượng chunk; nhược điểm là có thể cắt giữa câu hoặc giữa một mục chính sách.*

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Chuẩn hóa bằng cách loại bỏ khoảng trắng thừa rồi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng đứng sau dấu kết thúc câu. Dấu chấm, dấu chấm than và dấu hỏi vẫn được giữ trong câu. Với chuỗi rỗng hoặc chỉ có khoảng trắng, hàm trả về danh sách rỗng; các câu sau đó được gom tối đa `max_sentences_per_chunk` câu mỗi chunk.*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Thuật toán thử các separator theo thứ tự ưu tiên: đoạn văn, xuống dòng, ranh giới câu, khoảng trắng và cuối cùng là cắt theo ký tự. Base case là khi văn bản không dài hơn `chunk_size`, khi đó trả về một chunk; nếu không còn separator phù hợp thì cắt cố định để bảo đảm kích thước. Sau khi tách, các mảnh nhỏ được ghép lại cùng separator nếu vẫn nằm trong giới hạn kích thước, nhờ đó hạn chế tạo quá nhiều chunk ngắn.*

**`MarkdownBlockChunker` — chiến lược cá nhân custom:**
> *Tài liệu của nhóm chủ yếu là Markdown chính sách, vì vậy tôi tách theo block được ngăn bằng dòng trống và giữ heading gần nhất trong nội dung chunk. Nếu một block vượt `chunk_size`, thuật toán tiếp tục tách theo ranh giới câu. Cách làm này giữ được ngữ cảnh như `## Quy định hạn sử dụng`, `## 7. Apple Pay` hoặc `## Khiếu nại và bồi thường` cùng với phần đáp án, phù hợp hơn với truy vấn hỏi số liệu cụ thể.*

**Lý do chọn chiến lược:**
> *Fixed-size được dùng làm baseline để đối chiếu. Sentence và Recursive giúp kiểm tra ảnh hưởng của ranh giới câu/đoạn. Tôi chọn MarkdownBlock làm chiến lược chính vì dữ liệu có cấu trúc heading rõ ràng; nó đạt 5/5 câu có chunk liên quan trong top-3 và 4/5 câu ở top-1. Đổi lại, chiến lược này tạo nhiều chunk hơn nên tăng chi phí embedding và lưu trữ.*

### So sánh thực nghiệm trên bộ query nhóm

| Chiến lược | Số chunk | Chunk liên quan trong top-3 | Chunk liên quan ở top-1 | Nhận xét |
|---|---:|---:|---:|---|
| `FixedSizeChunker(500, overlap=50)` | 32 | 4/5 | 1/5 | Nhanh nhưng dễ cắt giữa ý |
| `SentenceChunker(max_sentences_per_chunk=3)` | 36 | 5/5 | 2/5 | Giữ câu hoàn chỉnh |
| `RecursiveChunker(chunk_size=500)` | 35 | 5/5 | 3/5 | Cân bằng giữa kích thước và ngữ cảnh |
| **`MarkdownBlockChunker(chunk_size=500)`** | **104** | **5/5** | **4/5** | **Tốt nhất trên corpus Markdown hiện tại** |

Các kết quả trên được chạy bằng embedding thật local và lọc `metadata.category` theo chủ đề của từng câu hỏi. Vì `ChunkingStrategyComparator` của bài yêu cầu đúng ba baseline, `MarkdownBlockChunker` được thử nghiệm riêng và không thay thế ba chiến lược chuẩn trong comparator.

**`compute_similarity`** — hướng tiếp cận:
> *cài công thức cosine `dot(a, b) / (||a|| * ||b||)`. Nếu một vector có độ dài bằng 0, hàm trả về `0.0` để tránh chia cho 0; nếu hai vector khác số chiều, hàm báo lỗi để tránh tính sai. `ChunkingStrategyComparator` gọi FixedSize, Sentence và Recursive rồi trả về số chunk, độ dài trung bình và nội dung chunk của từng chiến lược.*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Mỗi `Document` được chuyển thành record gồm `id`, `content`, `metadata` và embedding. Bản triển khai dùng danh sách in-memory làm backend bắt buộc, đồng thời có thể khởi tạo ChromaDB nếu môi trường có cài. Khi tìm kiếm, query được embed rồi tính dot product với từng embedding đã lưu, sắp xếp giảm dần theo `score` và lấy tối đa `top_k` kết quả.*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Lọc metadata trước, yêu cầu mọi cặp khóa-giá trị trong `metadata_filter` phải khớp, sau đó mới tính similarity trên tập ứng viên còn lại. `delete_document` xóa tất cả record có `metadata["doc_id"]` bằng `doc_id`; với document chưa có metadata `doc_id`, hàm cũng hỗ trợ khớp trực tiếp theo `id`. Hàm trả về `True` nếu có record bị xóa và `False` nếu không tìm thấy.*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *`answer` gọi `store.search(question, top_k)` để lấy các chunk liên quan, sau đó đánh số chunk và đưa nội dung cùng score vào phần `Context` của prompt. Prompt cũng chứa câu hỏi và yêu cầu mô hình chỉ sử dụng context, đồng thời nói rõ khi context không đủ. Cuối cùng hàm truyền prompt cho `llm_fn` và trả về câu trả lời của LLM.*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================================= test session starts ==============================================
platform win32 -- Python 3.12.5, pytest-9.1.1, pluggy-1.6.0 -- D:\AI intensive course\K4-Day07-MicroGenius\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\AI intensive course\K4-Day07-MicroGenius
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                     [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                              [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                       [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                        [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                             [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED             [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                   [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                    [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                  [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                    [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                    [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                               [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                           [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                     [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED            [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED          [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                    [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                      [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                        [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                              [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                   [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                     [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED         [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                      [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                               [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                              [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                         [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                     [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                    [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                          [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                    [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED               [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED              [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED  [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED             [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED      [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

=============================================== warnings summary ===============================================
.venv\Lib\site-packages\_pytest\cacheprovider.py:469
  D:\AI intensive course\K4-Day07-MicroGenius\.venv\Lib\site-packages\_pytest\cacheprovider.py:469: PytestCacheWarning: could not create cache path D:\AI intensive course\K4-Day07-MicroGenius\.pytest_cache\v\cache\nodeids: [WinError 5] Access is denied: 'D:\\AI intensive course\\K4-Day07-MicroGenius\\.pytest_cache\\v\\cache'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================================== 42 passed, 1 warning in 0.28s =========================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

### Cách tái lập kết quả

```powershell
cd "D:\AI intensive course\K4-Day07-MicroGenius"
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe ingest.py
.\.venv\Scripts\python.exe main.py
```

`ingest.py` self-check và pipeline `main.py` đều chạy thành công. Demo mặc định dùng `MockEmbedder`; backend này phù hợp để kiểm thử tính đúng của code nhưng không phản ánh chất lượng tương đồng ngữ nghĩa.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi chạy các cặp câu bằng local multilingual embedder `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, vector có 384 chiều. Trước khi chạy, tôi dự đoán dựa trên nội dung; sau đó so sánh với cosine similarity thực tế.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi thích học Python. | Python là ngôn ngữ lập trình tôi yêu thích. | cao | 0.871638 | Có |
| 2 | Chính sách đổi trả hàng. | Quy trình hoàn tiền cho người mua. | cao | 0.736070 | Có |
| 3 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác. | cao | 0.957029 | Có |
| 4 | Tôi thích học Python. | Hôm nay trời mưa rất to. | thấp | 0.393327 | Có, thấp hơn các cặp tương đồng |
| 5 | Sản phẩm bị cấm không được đăng bán. | Không được bán sản phẩm bị cấm. | cao | 0.747445 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Cặp 3 cho điểm cao nhất (0.957029), phù hợp với dự đoán vì hai câu gần như cùng ý nghĩa. Cặp 4 là kết quả bất ngờ: hai câu khác chủ đề hoàn toàn nhưng vẫn có điểm tới 0.393327. Điều này cho thấy embedding có thể nhận diện các từ và ngữ cảnh chung trong miền thương mại điện tử, nhưng score không nên được hiểu tuyệt đối; cần so sánh tương đối trên cùng corpus và kiểm tra kết quả retrieval thực tế.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy 5 câu hỏi nhóm trên toàn bộ corpus `data/k4_ecommerce` bằng local embedding model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Mỗi câu dùng bộ lọc `category` đúng với chủ đề tài liệu để đánh giá công bằng khả năng chunking, ví dụ `category=payment` cho câu hỏi Apple Pay và `category=shipping-policy` cho câu hỏi bồi thường vận chuyển.

### So sánh các chiến lược chunking

| Chiến lược | Số chunk | Chunk liên quan trong top-3 | Chunk liên quan ở top-1 | Nhận xét |
|---|---:|---:|---:|---|
| `FixedSizeChunker(500, overlap=50)` | 32 | 4/5 | 1/5 | Một số đáp án bị cắt khỏi phần ngữ cảnh phù hợp |
| `SentenceChunker(max_sentences_per_chunk=3)` | 36 | 5/5 | 2/5 | Giữ câu hoàn chỉnh nhưng đôi khi gom nhiều ý |
| `RecursiveChunker(chunk_size=500)` | 35 | 5/5 | 3/5 | Cân bằng tốt giữa độ dài và ngữ cảnh |
| **`MarkdownBlockChunker(chunk_size=500)`** | **104** | **5/5** | **4/5** | Tốt nhất trên bộ query này vì giữ heading và block đáp án |

=> Chọn `MarkdownBlockChunker` làm chiến lược chính cho benchmark. Chiến lược này tách theo block Markdown, gắn heading gần nhất vào block, và chỉ tách tiếp theo ranh giới câu khi block quá dài. Vì vậy các đoạn như “Apple Pay”, “Quyền của người dùng”, “Quy định hạn sử dụng” và “Mức bồi thường tối đa” được giữ thành các đơn vị có ngữ cảnh rõ ràng.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng và hoàn tiền? | `k4-returns-policy::chunk_6`: thời hạn 15 ngày; thực phẩm tươi/đông lạnh là 24 giờ | 0.694717 | Có, top-1 | Context cho đáp án: 15 ngày; riêng thực phẩm tươi/đông lạnh 24 giờ |
| 2 | Đơn hàng Apple Pay cần nằm trong khoảng giá trị nào? | `k4-payment-methods::chunk_9`: điều kiện Apple Pay từ 10.000 đến 25.000.000 VNĐ | 0.827971 | Có, top-1 | Context cho đáp án: 10.000–25.000.000 VNĐ |
| 3 | Liên hệ ai để yêu cầu truy cập/xóa dữ liệu cá nhân? | `k4-privacy-policy::chunk_11` ở top-3: Cán bộ bảo vệ dữ liệu và email dpo.vn@shopee.com | 0.621017 | Có trong top-3, hạng 3 | Context cho đáp án: liên hệ Data Protection Officer qua dpo.vn@shopee.com |
| 4 | Hạn sử dụng còn lại tối thiểu bao nhiêu khi đăng bán? | `k4-seller-listing::chunk_22`: còn ít nhất 30% thời hạn và ít nhất 30 ngày | 0.620191 | Có, top-1 | Context cho đáp án: tối thiểu 30% thời hạn sử dụng và 30 ngày |
| 5 | Mức bồi thường tối đa khi mất hàng hoàn toàn? | `k4-shipping-policy::chunk_12`: mất hàng hoàn toàn được bồi thường tối đa 70% giá trị sản phẩm | 0.606576 | Có, top-1 | Context cho đáp án: tối đa 70% giá trị sản phẩm |

`MarkdownBlockChunker` được thêm vào `src/chunking.py` như chiến lược custom.

**Tổng điểm truy xuất: 10/10**

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng metadata filter giúp giảm nhiễu bằng cách giới hạn kết quả theo đúng chủ đề, nhưng chất lượng chunk vẫn quyết định rất lớn đến thứ hạng top-k. Với tài liệu chính sách, cách chia theo block Markdown và giữ heading cùng nội dung giúp các đáp án có số liệu cụ thể được truy xuất tốt hơn, đạt 5/5 câu có chunk liên quan trong top-3.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 10 / 10 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
