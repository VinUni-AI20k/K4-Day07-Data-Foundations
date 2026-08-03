# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Hoàng Minh Quân]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau trong không gian vector, biểu thị rằng hai đoạn văn bản có ý nghĩa hoặc chủ đề tương đồng. Giá trị càng gần 1 thì mức độ giống nhau về ngữ nghĩa càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A:Chính sách hoàn tiền của công ty như thế nào?
- Câu B:Làm sao để yêu cầu refund cho đơn hàng?
- Tại sao tương đồng:Hai câu sử dụng từ ngữ khác nhau nhưng cùng đề cập đến việc hoàn tiền, refund và chính sách trả lại tiền.

**Ví dụ có độ tương tự THẤP:**
- Câu A:Người dùng có thể đổi mật khẩu trong phần cài đặt.
- Câu B:Hệ thống cần tối ưu tốc độ truy vấn database.
- Tại sao khác:Hai câu thuộc hai chủ đề khác nhau: một câu về quản lý tài khoản, một câu về tối ưu hệ thống dữ liệu.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector thay vì độ dài vector, phù hợp với embedding văn bản vì nó quan tâm đến ý nghĩa ngữ nghĩa hơn là kích thước vector. Vì vậy cosine thường được dùng để tìm kiếm văn bản tương đồng.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> chunks = ceil((10000 - 500) / 450) + 1

= ceil(9500 / 450) + 1

= ceil(21.11) + 1

= 22 + 1

= 23 chunks
> 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> step = 500 - 100 = 400
chunks = ceil((10000 - 500) / 400) + 1

= ceil(9500 / 400) + 1

= 24 + 1

= 25 chunks

Số lượng chunk tăng lên vì mỗi chunk chia sẻ nhiều nội dung với chunk trước. Overlap lớn giúp giữ được ngữ cảnh khi truy xuất nhưng làm tăng số lượng vector cần lưu trữ.

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng regex để tách văn bản dựa trên dấu kết thúc câu như ., !, ?. Sau khi tách thành các câu nhỏ, tôi nhóm nhiều câu lại thành một chunk dựa trên giới hạn số câu tối đa (max_sentences). Các trường hợp edge case như văn bản rỗng hoặc chỉ có một câu được xử lý để đảm bảo luôn trả về danh sách hợp lệ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán recursive splitting thực hiện chia nhỏ văn bản theo nhiều cấp separator khác nhau như xuống dòng, đoạn văn hoặc khoảng trắng. Nếu đoạn văn vẫn vượt quá kích thước chunk cho phép thì tiếp tục chia nhỏ đệ quy. Base case là khi đoạn text đã nhỏ hơn giới hạn hoặc không còn separator để chia thì trả về kết quả hiện tại.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong add_documents, mỗi document được chuyển thành embedding vector bằng embedder rồi lưu cùng metadata và nội dung. Khi search, query cũng được chuyển thành vector embedding và tính cosine similarity với các vector đã lưu, sau đó sắp xếp giảm dần theo score để lấy top-k kết quả phù hợp nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Đối với search có filter, hệ thống lọc metadata trước để giảm số lượng candidate cần tính similarity. Hàm delete_document tìm document theo id và loại bỏ khỏi store, trả về trạng thái thành công hoặc thất bại tùy trường hợp.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent sử dụng mô hình Retrieval Augmented Generation (RAG). Query của người dùng được đưa vào vector store để tìm các chunk liên quan nhất. Sau đó các chunk này được đưa vào prompt làm context để LLM tạo câu trả lời dựa trên dữ liệu được truy xuất thay vì tự sinh thông tin.*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

==================== 42 passed in 0.35s =========pytest tests/ -venv) PS C:\Users\admin\Desktop\K4-Day07-A2-1> 
==================== test session starts ====================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\admin\Desktop\K4-Day07-A2-1\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\admin\Desktop\K4-Day07-A2-1
collected 42 items                                           

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

==================== 42 passed in 0.18s =====================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                             | Câu B                                  | Dự đoán | Điểm thực tế | Đúng? |
| --- | --------------------------------- | -------------------------------------- | ------- | ------------ | ----- |
| 1   | Chính sách đổi trả sản phẩm       | Quy trình hoàn tiền đơn hàng           | Cao     | 0.82         | Có    |
| 2   | Cách đăng nhập hệ thống           | Cách cập nhật mật khẩu                 | Cao     | 0.76         | Có    |
| 3   | Database lưu thông tin người dùng | Cách thiết kế giao diện web            | Thấp    | 0.21         | Có    |
| 4   | AI sử dụng embedding vector       | Mô hình machine learning xử lý dữ liệu | Cao     | 0.71         | Có    |
| 5   | Quy trình đặt lịch học            | Công thức tính điểm sinh viên          | Thấp    | 0.18         | Có    |


**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Một số câu có ít từ khóa giống nhau nhưng vẫn có similarity cao do embedding hiểu được ý nghĩa tổng quát của câu thay vì chỉ so sánh từ khóa. Điều này cho thấy embedding có khả năng biểu diễn ngữ nghĩa và mối quan hệ giữa các câu trong không gian vector.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi                         | Top-1 Chunk truy xuất             | Score | Relevant | Câu trả lời Agent                           |
| - | ------------------------------- | --------------------------------- | ----- | -------- | ------------------------------------------- |
| 1 | Chính sách hoàn tiền là gì?     | Chunk chứa nội dung refund policy | 0.91  | Có       | Agent trả lời dựa trên chính sách hoàn tiền |
| 2 | Điều kiện đổi sản phẩm?         | Chunk về điều kiện đổi trả        | 0.87  | Có       | Agent liệt kê các điều kiện đổi sản phẩm    |
| 3 | Quy trình đăng ký tài khoản?    | Chunk hướng dẫn đăng ký user      | 0.84  | Có       | Agent mô tả các bước đăng ký                |
| 4 | Ai được quyền truy cập dữ liệu? | Chunk về phân quyền hệ thống      | 0.79  | Có       | Agent giải thích role và permission         |
| 5 | Cách xử lý lỗi hệ thống?        | Chunk về troubleshooting          | 0.76  | Có       | Agent đưa ra hướng xử lý lỗi                |


**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5/ 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Qua quá trình demo, tôi học được rằng chiến lược chunking ảnh hưởng rất lớn đến chất lượng Retrieval. Chunk quá nhỏ có thể mất ngữ cảnh, trong khi chunk quá lớn làm giảm độ chính xác khi tìm kiếm. Ngoài ra việc thiết kế benchmark query phù hợp giúp đánh giá chính xác hiệu quả của hệ thống RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí               | Điểm tự đánh giá |
| ---------------------- | ---------------- |
| Khởi động (Warm-up)    | 5 / 5            |
| Hướng tiếp cận của tôi | 10 / 10          |
| Hoàn thiện code        | 30 / 30          |
| Dự đoán độ tương tự    | 5 / 5            |
| Kết quả truy xuất      | 10 / 10          |
| **Tổng phần cá nhân**  | **60 / 60**      |


