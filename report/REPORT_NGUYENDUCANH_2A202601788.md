# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Là khi mà 2 vector cùng hướng tức là giá trị cosin tiến gần về 1

**Ví dụ có độ tương tự CAO:**
- Câu A: con chó đang chạy ở trong nhà
- Câu B: con cẩu đang chơi trong nhà
- Tại sao tương đồng: Vì 2 câu đều miêu tả chung 1 bối cảnh, tình huống, ý nghĩa, ngữ nghĩa dù dùng các từ khác nhau vì vậy vector embedding của chúng chỉ về cùng 1 hướng

**Ví dụ có độ tương tự THẤP:**
- Câu A: trời hôm nay không mưa
- Câu B: điện thoại tôi không bị hỏng
- Tại sao khác: vì 2 câu này là 2 chủ đề hoàn toàn khác nhau vì vậy vector embedding của chúng sẽ có thể gần như vuông góc với nhau

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ tập trung vào ngữ nghĩa tức là hướng của vector, nên không bị ảnh hưởng bởi độ lớn của vector gây ra do sự chênh lệch về độ dài văn bản

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
>
> ```text
> step = chunk_size - overlap
>      = 500 - 50
>      = 450
>
> Số chunks = ceil((10000 - 500) / 450) + 1
>            = ceil(9500 / 450) + 1
>            = ceil(21.11) + 1
>            = 22 + 1
>            = 23
> ```
>
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap = 100`, bước nhảy giảm còn `500 - 100 = 400`, nên số lượng chunk tăng lên **25 chunks**. Độ chồng chéo lớn hơn giúp giữ được nhiều ngữ cảnh giữa các chunk, giảm nguy cơ mất thông tin khi chia văn bản, nhưng cũng làm tăng dữ liệu trùng lặp và chi phí xử lý.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Em dùng biểu thức chính quy `(?<=[.!?])(?:\s+|\n+)` để tách văn bản tại khoảng trắng hoặc xuống dòng sau các dấu kết thúc câu như `.`, `!`, `?`. Sau khi tách, em dùng `strip()` để loại bỏ khoảng trắng thừa và bỏ qua các câu rỗng. Nếu văn bản đầu vào rỗng thì hàm trả về danh sách rỗng, còn các câu hợp lệ sẽ được gom tối đa `max_sentences_per_chunk` câu trong một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Em triển khai thuật toán chia nhỏ đệ quy theo thứ tự ưu tiên của các dấu phân cách: đoạn văn `\n\n`, dòng `\n`, câu `. `, khoảng trắng `" "`, và cuối cùng là cắt theo ký tự. Base case là khi đoạn văn bản hiện tại rỗng hoặc có độ dài nhỏ hơn hoặc bằng `chunk_size`, lúc đó hàm trả về ngay đoạn đó. Nếu một phần vẫn quá dài sau khi tách, `_split` tiếp tục gọi lại chính nó với separator tiếp theo để tạo chunk nhỏ hơn.


### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong `add_documents`, em chuyển mỗi `Document` thành một record gồm `id`, `content`, `metadata` và `embedding`, sau đó lưu vào danh sách `_store` trong bộ nhớ. Embedding được tạo bằng `embedding_fn`, mặc định là `_mock_embed` để phù hợp với môi trường lab và unit test. Khi `search`, em embed câu truy vấn, tính điểm tương tự giữa query embedding và từng document embedding bằng dot product, rồi sắp xếp kết quả theo score giảm dần và trả về `top_k`.


**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Với `search_with_filter`, em lọc metadata trước rồi mới tính similarity trên các record đã lọc, vì cách này giúp giới hạn phạm vi tìm kiếm theo các trường như `department`, `lang` hoặc `customer_role`. Nếu không truyền `metadata_filter`, hàm sẽ hoạt động giống `search` thông thường. Với `delete_document`, em xóa tất cả record có `metadata["doc_id"]` trùng với `doc_id` cần xóa và trả về `True` nếu có ít nhất một chunk bị xóa.


### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Trong `answer`, em trước tiên dùng `store.search(question, top_k)` để lấy các chunk liên quan nhất từ vector store. Sau đó em ghép các chunk này thành phần `Context`, đánh số từng chunk, rồi đưa vào prompt cùng với câu hỏi của người dùng. Cấu trúc này đi theo mô hình RAG: truy xuất thông tin liên quan trước, inject context vào prompt, rồi gọi `llm_fn` để sinh câu trả lời dựa trên ngữ cảnh đã tìm được.


---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
(.venv) PS D:\Vin\Assigment\lab007\K4-Day07-MicroGenius> python -m pytest tests -v                                    
================================================ test session starts ================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\Vin\Assigment\lab007\K4-Day07-MicroGenius\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Vin\Assigment\lab007\K4-Day07-MicroGenius
collected 42 items                                                                                                   

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED     [100%]

================================================ 42 passed in 0.10s =================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Con chó đang chạy trong sân. | Một chú cún đang chạy ngoài sân. | cao | 0.9059 | Có |
| 2 | Chính sách đổi trả yêu cầu người mua cung cấp bằng chứng. | Khách hàng cần gửi bằng chứng khi hàng bị lỗi. | cao | 0.6475 | Có |
| 3 | Người bán phải mô tả sản phẩm chính xác. | Sản phẩm bị cấm không được đăng bán. | cao | 0.2244 | Có |
| 4 | Trời hôm nay có mưa lớn. | Tôi đang học lập trình Python. | thấp | 0.0413 | Có |
| 5 | Vector database lưu trữ embeddings để tìm kiếm tương tự. | Món phở bò có nước dùng thơm và nóng. | thấp | 0.0960 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 3: hai câu nói về các quy định khác nhau của người bán nhưng vẫn có điểm 0.2244, vượt ngưỡng cao 0.2. Điều này cho thấy embedding đa ngôn ngữ vẫn nhận ra ngữ cảnh chung về quản lý sản phẩm/người bán, dù hai câu không diễn đạt cùng một ý cụ thể. Ngược lại, các cặp 4 và 5 có điểm rất thấp vì khác hẳn chủ đề.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng và hoàn tiền sau khi nhận hàng? | `payment-methods`: các phương thức và điều kiện thanh toán, không có thời hạn trả hàng. | 0.6478 | Không, không có `returns-policy` trong top-3. | Agent trích xuất chunk về phương thức thanh toán; không trả lời được thời hạn trả hàng. |
| 2 | Đơn hàng thanh toán bằng Apple Pay trên Shopee cần nằm trong khoảng giá trị nào? | `payment-methods`: Apple Pay áp dụng cho đơn từ 10.000 đến 25.000.000 VNĐ. | 0.7854 | Có, đúng ngay top-1. | Apple Pay áp dụng cho đơn hàng từ 10.000 đến 25.000.000 VNĐ. |
| 3 | Người dùng liên hệ ai để yêu cầu truy cập hoặc xóa dữ liệu cá nhân trên Shopee? | `privacy-policy`: liên hệ Data Protection Officer qua `dpo.vn@shopee.com`. | 0.6878 | Có, đúng ngay top-1. | Liên hệ Cán bộ bảo vệ dữ liệu (Data Protection Officer) qua `dpo.vn@shopee.com`. |
| 4 | Người bán phải đảm bảo hạn sử dụng còn lại tối thiểu bao nhiêu khi đăng bán sản phẩm có hạn dùng? | `seller-listing`: còn ít nhất 30% thời hạn sử dụng và ít nhất 30 ngày. | 0.6544 | Có, đúng ngay top-1. | Sản phẩm phải còn ít nhất 30% thời hạn sử dụng và ít nhất 30 ngày khi giao đi. |
| 5 | Mức bồi thường tối đa khi kiện hàng bị mất hoàn toàn trong quá trình vận chuyển là bao nhiêu? | `terms-of-service`: điều khoản chung, không nêu mức bồi thường mất hàng. | 0.6641 | Có ở top-3: `shipping-policy` đứng thứ 2. | Agent trích xuất điều khoản chung từ top-1, nên chưa nêu được mức bồi thường 70%. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Em học được rằng chunking có ảnh hưởng trực tiếp đến kết quả retrieval. `SentenceChunker` giúp chunk dễ đọc và giữ ranh giới câu, nhưng câu 1 cho thấy nếu thông tin quan trọng nằm ở chunk khác thì embedding vẫn có thể xếp sai tài liệu. Các chiến lược tinh chỉnh theo cấu trúc tài liệu hoặc ngữ nghĩa có thể cải thiện thứ hạng truy xuất, nhất là với câu hỏi chứa số liệu cụ thể.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
