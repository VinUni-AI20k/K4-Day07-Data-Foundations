# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thị Thương
**Nhóm:** MicroGenius
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Là hai đoạn có ý nghĩa rất giống nhau, dù có thể sử dụng từ ngữ hoặc cách diễn đạt khác nhau. Giá trị cosine càng gần 1 thì mức độ tương đồng về ngữ nghĩa càng cao.*

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi muốn đặt lịch khám bác sĩ vào chiều mai.
- Câu B: Tôi cần hẹn bác sĩ khám bệnh vào chiều ngày mai.
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một nhu cầu là đặt lịch khám bác sĩ vào chiều hôm sau, chỉ khác cách dùng từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hôm nay trời mưa rất lớn.
- Câu B: Tôi đang học lập trình Python.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác nhau nên ý nghĩa không liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Cosine similarity đo mức độ giống nhau về hướng của các vector, nên phản ánh tốt sự tương đồng về ý nghĩa giữa các văn bản. Trong khi đó, Euclidean distance bị ảnh hưởng bởi độ lớn của vector nên thường kém phù hợp hơn khi so sánh text embeddings.*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính: Bước dịch sau mỗi chunk = 500 - 50 = 450 ký tự. Số chunk = ⌈(10.000 - 500) / 450⌉ + 1 = 23 chunk* 

> *Đáp án: 23 chunk*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Khi overlap = 100, bước dịch còn 500 - 100 = 400 ký tự nên sẽ tạo nhiều chunk hơn (25 chunk). Độ chồng chéo lớn giúp giữ được ngữ cảnh giữa các chunk, giảm nguy cơ mất thông tin ở phần ranh giới khi truy xuất hoặc trả lời câu hỏi.*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *`_split` là hàm đệ quy: thử tách văn bản theo separator ưu tiên đầu tiên trong danh sách (`\n\n` → `\n` → `. ` → ` ` → `""`), phần nào sau khi tách vẫn dài hơn `chunk_size` thì tiếp tục đệ quy với separator kế tiếp. Base case là khi đoạn văn bản đã đủ ngắn (`len <= chunk_size`) hoặc đã hết separator để thử — lúc đó cắt cứng theo từng đoạn `chunk_size` ký tự để đảm bảo luôn trả về kết quả hợp lệ, kể cả khi `separators=[]`.*

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Dùng `re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)` với lookbehind để tách câu mà vẫn giữ nguyên dấu câu ở cuối mỗi câu. Sau khi tách, loại bỏ các câu rỗng và `strip()` khoảng trắng thừa, rồi gom từng nhóm `max_sentences_per_chunk` câu liên tiếp thành một chunk. Edge case: text rỗng thì trả về `[]` ngay từ đầu.*


### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *`add_documents` chuẩn hoá mỗi `Document` qua `_make_record` thành một dict gồm `content`, `embedding` (sinh từ `embedding_fn`) và `metadata` (có gắn thêm `doc_id`), rồi append vào danh sách `self._store`. `search` embed câu truy vấn, tính cosine similarity (`compute_similarity`) giữa embedding truy vấn và embedding từng record, sắp xếp giảm dần theo điểm rồi lấy `top_k` kết quả đầu.*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *`search_with_filter` lọc metadata trước: giữ lại các record có mọi key/value khớp với `metadata_filter`, sau đó mới chạy similarity search trên tập đã lọc (tái sử dụng hàm `_search_records` dùng chung với `search`). `delete_document` xoá bằng cách loại bỏ khỏi `self._store` mọi record có `metadata['doc_id']` trùng `doc_id` truyền vào, trả về `True` nếu có ít nhất một record bị xoá, `False` nếu không tìm thấy.*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk lại bằng `"\n\n"` thành đoạn `context`. Prompt được dựng theo mẫu `f"Context:\n{context}\n\nQuestion: {question}"` để đưa ngữ cảnh truy xuất vào trước câu hỏi, sau đó gọi `llm_fn(prompt)` và trả thẳng kết quả về.*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
======================================================================= test session starts =======================================================================
platform linux -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0 -- /home/thuongg/Downloads/AI_in_Action/K4-Day07-MicroGenius/venv/bin/python
cachedir: .pytest_cache
rootdir: /home/thuongg/Downloads/AI_in_Action/K4-Day07-MicroGenius
collected 42 items                                                                                                                                                

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                       [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                         [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                          [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                               [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                               [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                     [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                      [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                    [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                      [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                      [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                 [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                             [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                       [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                              [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                  [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                            [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                  [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                      [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                        [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                          [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                     [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                       [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                           [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                        [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                 [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                           [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                       [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                  [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                      [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                            [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                      [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                   [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                 [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                    [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                               [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                        [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                              [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                  [100%]

======================================================================= 42 passed in 0.04s ========================================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi trong vòng 15 ngày. | Tôi cần trả lại hàng bị hư hỏng trong vòng 15 ngày kể từ khi nhận. | cao | 0.8846 | Đúng |
| 2 | Người bán phải cung cấp hóa đơn và nguồn gốc xuất xứ sản phẩm. | Nhà cung cấp cần đính kèm chứng từ chứng minh nguồn gốc hàng hóa. | cao | 0.6422 | Đúng |
| 3 | Shopee hỗ trợ thanh toán qua ví ShopeePay và thẻ tín dụng. | Hôm nay tôi đi học lập trình Python ở trung tâm. | thấp | 0.0971 | Đúng |
| 4 | Chính sách bảo mật quy định cách Shopee thu thập dữ liệu cá nhân. | Người bán không được đăng sản phẩm giả mạo thương hiệu. | thấp | 0.2519 | Đúng |
| 5 | Đơn hàng thanh toán qua Apple Pay tối đa 25 triệu đồng. | Giới hạn thanh toán Apple Pay trên Shopee là từ 10.000 đến 25.000.000 VNĐ. | cao | 0.7843 | Đúng |

> Ngưỡng phân loại "cao/thấp": coi thực tế là "cao" nếu điểm > 0.5, ngược lại là "thấp". Chạy bằng `LocalEmbedder()` (`EMBEDDING_PROVIDER=local`, model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) 

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Điều bất ngờ nhất là mức chênh lệch điểm giữa 2 cặp cùng dự đoán "cao": cặp 1 (đổi trả, gần như dịch nguyên câu) đạt 0.88, trong khi cặp 2 (hóa đơn/nguồn gốc, diễn đạt khác nhau nhiều hơn dù cùng ý) chỉ đạt 0.64 — cho thấy embedder thật không chỉ phân biệt được "liên quan/không liên quan" mà còn phản ánh đúng *mức độ* gần nghĩa, càng diễn đạt lại xa cấu trúc câu gốc thì điểm càng giảm dù ý nghĩa vẫn tương đương.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chiến lược dùng để chạy: `RecursiveChunker(separators=["\n\n", "\n", ". "], chunk_size=400)` — xem lý do chọn ở `REPORT_NHOM.md` Phần 2, mục "Thành viên 1". `EmbeddingStore` nạp bằng `build_knowledge_base("data/k4_ecommerce", LocalEmbedder(), chunker=...)` (model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, `EMBEDDING_PROVIDER=local`) → 122 chunk. Chấm điểm theo `docs/SCORING.md`: gold ở top-1 = 2đ, gold ở top-3 nhưng không phải top-1 = 1đ, không có trong top-3 = 0đ.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng và hoàn tiền? | `k4-terms-of-service`: "Người mua có thể hủy đơn... Được yêu cầu trả hàng và hoàn tiền theo chính sách..." | 0.7191 | Một phần (gold `k4-returns-policy` ở top-3, không phải top-1) — 1/2đ | "Người mua có thể hủy đơn ở giai đoạn 'Chờ Xác Nhận'... Được yêu cầu trả hàng và hoàn tiền theo chí..." |
| 2 | Đơn hàng Apple Pay cần nằm trong khoảng giá trị nào? | `k4-payment-methods`: "## 7. Apple Pay — Điều kiện: 10.000-25.000.000 VNĐ..." | 0.8278 | Có, đúng top-1 — 2/2đ | "## 7. Apple Pay Điều kiện: 10.000 - 25.000.000 VNĐ. Không áp dụng cho..." |
| 3 | Liên hệ ai để yêu cầu truy cập/xóa dữ liệu cá nhân? | `k4-privacy-policy`: "Shopee thu thập dữ liệu cá nhân khi người dùng đăng ký tài khoản..." | 0.7405 | Có, đúng top-1 — 2/2đ | "Shopee thu thập dữ liệu cá nhân khi người dùng đăng ký tài khoản, điền biểu mẫu..." |
| 4 | Hạn sử dụng còn lại tối thiểu bao nhiêu khi đăng bán? | `k4-shipping-policy`: "Chỉ được bán khi giao đi sản phẩm còn ít nhất 30% thời hạn sử dụng và ít nhất 30 ngày." | 0.7146 | Có, đúng top-1 — 2/2đ | "Hạn sử dụng : - ít nhất 30% thời hạn sử dụng..." |
| 5 | Mức bồi thường tối đa khi mất hàng hoàn toàn? | `k4-returns-policy`: "## Chi phí vận chuyển hoàn trả" | 0.7068 | Một phần (gold `k4-shipping-policy` ở top-3, không phải top-1) — 1/2đ | "## Chi phí vận chuyển hoàn trả ... Mức bồi thường tối đa: Hư hại bao bì nhẹ..." |

**Tổng điểm truy xuất: 8/10**

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

> **Nhận xét:** với `EMBEDDING_PROVIDER=local`, retrieval đã có ý nghĩa — 5/5 câu tìm đúng tài liệu gốc trong top-3, 3/5 câu đúng ngay top-1.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Qua phần demo của các thành viên khác, em học được rằng việc lựa chọn chunking strategy (chunk size, overlap và separators) ảnh hưởng rất lớn đến chất lượng truy xuất. Em cũng nhận thấy việc so sánh nhiều mô hình embedding và đánh giá bằng các chỉ số như Top-1 và Top-3 giúp lựa chọn cấu hình phù hợp thay vì chỉ dựa vào cảm nhận.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | ** 58/ 60** |
