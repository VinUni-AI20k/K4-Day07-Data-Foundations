# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Tuấn Phong]
**Nhóm:** [B1-2]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Khi hai đoạn văn bản có độ tương tự cosine cao, điều đó có nghĩa là chúng "hướng về cùng một phía" trong không gian vector nhiều chiều — tức là chúng có ngữ nghĩa/ý nghĩa giống nhau, dù các từ cụ thể có thể khác nhau. Embedding model đã biến đổi văn bản thành các con số (vector) sao cho những văn bản cùng chủ đề sẽ có vector gần nhau theo góc đo cosine.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Cách đổi trả sản phẩm trong vòng 30 ngày"
- Câu B: "Quy trình hoàn tiền khi trả hàng hóa không phù hợp"
- Tại sao tương đồng: Cả hai đều nói về việc đổi/trả hàng và hoàn tiền — cùng chủ đề chính sách đổi trả, dù dùng từ khác nhau nhưng ý nghĩa cốt lõi giống nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Hướng dẫn thanh toán qua thẻ tín dụng Visa"
- Câu B: "Chính sách bảo mật thông tin cá nhân người dùng"
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau — một về thanh toán tài chính, một về quyền riêng tư — nên embedding vector sẽ "hướng" theo các hướng rất khác nhau trong không gian vector, dẫn đến cosine similarity thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity chỉ quan tâm đến **góc/độ hướng** giữa hai vector, không quan tâm đến **độ dài** của chúng. Với text embeddings, một câu dài và một câu ngắn có cùng ý nghĩa vẫn có thể có cosine similarity cao vì chúng cùng "hướng" về một phía trong không gian vector, dù độ dài vector khác nhau. Trong khi đó, khoảng cách Euclid bị ảnh hưởng bởi cả độ dài lẫn hướng — một câu dài gấp đôi sẽ luôn có khoảng cách Euclid lớn hơn dù ý nghĩa tương tự, điều này không mong muốn khi so sánh ý nghĩa văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:*
>
> - Công thức: `số lượng chunk = ceil((độ_dài - overlap) / (chunk_size - overlap))`
> - Thay số: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11)`
> - Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> Với overlap=100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks`
> Số chunk tăng từ **23 → 25** khi overlap tăng từ 50 lên 100.
>
> **Tại sao muốn overlap nhiều hơn?** Độ chồng chéo cao giúp **giữ nguyên ngữ cảnh** ở vùng ranh giới giữa các chunks — đặc biệt quan trọng khi một câu hoặc ý quan trọng nằm "chính giữa" hai chunk. Trade-off là số lượng chunk tăng, dẫn đến tốn bộ nhớ hơn và có thể gây trùng lặp thông tin.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Dùng regex `r'(?<=[.!?])\s+'` để tách câu trên các dấu `.`, `!`, `?` theo sau là khoảng trắng. Sau đó nhóm các câu theo `max_sentences_per_chunk` bằng cách tích lũy câu vào list, khi đủ số lượng thì join thành một chunk. Edge cases đã xử lý: text rỗng → list rỗng; câu cuối không đủ số lượng vẫn được emit.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử tách lần lượt theo danh sách separators theo thứ tự ưu tiên (`\n\n`, `\n`, `. `, ` `, `""`). Với mỗi separator, kiểm tra xem tất cả các phần sau khi tách có nhỏ hơn `chunk_size` không. Base case: nếu hết separator hoặc `len(text) <= chunk_size` → trả về `[text]`. Nếu có phần nào quá lớn → đệ quy xuống separator tiếp theo cho phần đó.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Mỗi document được embed bằng `_embedding_fn` thành vector, rồi lưu cùng content + metadata vào `_store` (list in-memory) hoặc ChromaDB collection. Khi search: embed query → tính dot product (vì vector đã normalize = cosine similarity) với tất cả records → sort giảm dần → trả về top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter`: filter metadata trước (giữ lại records thỏa mãn điều kiện), rồi chạy similarity search trên tập đã lọc. `delete_document`: lọc `_store` giữ lại records có `metadata["doc_id"] != doc_id`, trả True nếu có bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Retrieve top_k chunks từ store, ghép nối content thành ngữ cảnh (mỗi chunk 1 dòng), rồi inject vào prompt theo template: phần mở đầu → block "Ngữ cảnh:" → câu hỏi → "Trả lời:". Gọi `_llm_fn(prompt)` và trả kết quả trả về của LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
(.venv) PS D:\AI20K\K4-Day07-Data-Foundations-B1-2> $env:LAB_SOLUTION_PACKAGE="src.phongnt_01038"; pytest tests/ -v
========================================================== test session starts ==========================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\AI20K\K4-Day07-Data-Foundations-B1-2\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\AI20K\K4-Day07-Data-Foundations-B1-2
plugins: anyio-4.14.2
collected 42 items                                                                                                                     

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                              [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                       [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                 [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                      [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                      [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                            [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                             [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                           [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                             [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                             [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                        [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                    [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                              [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                     [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                         [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                   [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                         [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                             [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                               [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                 [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                       [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                            [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                              [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                  [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                               [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                        [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                       [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                  [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                              [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                         [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                             [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                   [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                             [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                          [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                        [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                       [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                           [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                      [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                               [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                     [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                         [100%]

========================================================== 42 passed in 0.14s ===========================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42 ✅

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)


| Cặp | Câu A                                                  | Câu B                                                              | Dự đoán | Điểm thực tế | Đúng? |
| ---- | ------------------------------------------------------- | ------------------------------------------------------------------- | ---------- | ---------------- | ------- |
| 1    | Cách đổi trả sản phẩm trong vòng 30 ngày        | Quy trình hoàn tiền khi trả hàng không phù hợp              | cao        | 0.5751           | Đúng  |
| 2    | Hướng dẫn thanh toán qua thẻ tín dụng Visa       | Chính sách bảo mật thông tin cá nhân người dùng           | thấp      | 0.3313           | Đúng  |
| 3    | Làm sao để liên hệ bộ phận hỗ trợ khách hàng | Số điện thoại và email của đội ngũ chăm sóc khách hàng | cao        | 0.5882           | Đúng  |
| 4    | Cách tính phí vận chuyển cho đơn hàng           | Chính sách bảo vệ dữ liệu và quyền riêng tư người dùng | thấp      | 0.2999           | Đúng  |
| 5    | Tôi muốn khiếu nại về chất lượng sản phẩm     | Hướng dẫn liên hệ bộ phận chăm sóc khách hàng            | thấp      | 0.3640           | Sai     |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Kết quả bất ngờ nhất là cặp 5: dù cả hai câu đều thuộc chủ đề hỗ trợ khách hàng, điểm chỉ là 0.36 (gần ngưỡng thấp). Nguyên nhân có thể là "khiếu nại về chất lượng sản phẩm" mang nặng ý phàn nàn tiêu cực, trong khi "hướng dẫn liên hệ" mang tính chỉ dẫn tích cực — embedding model phân biệt được sắc thái cảm xúc/tone của câu dù chủ đề giống nhau. Điều này cho thấy embeddings không chỉ học chủ đề mà còn học cả "hướng sentiment" của câu. So với MockEmbedder (toàn bộ điểm âm hoặc gần 0), OpenAI embedder hiểu ngữ nghĩa tiếng Việt rõ ràng: cặp cùng chủ đề đạt 0.57–0.59, khác chủ đề chỉ 0.30–0.33.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).


| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 |                   |                                            |              |                                   |                                       |
| 2 |                   |                                            |              |                                   |                                       |
| 3 |                   |                                            |              |                                   |                                       |
| 4 |                   |                                            |              |                                   |                                       |
| 5 |                   |                                            |              |                                   |                                       |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)


| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | / 10                   |
| **Tổng phần cá nhân**                            | **/ 60**               |
