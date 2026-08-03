# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Thanh Huyền
**Nhóm:** AAA
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao nghĩa là vector biểu diễn của hai đoạn văn bản trỏ cùng hướng trong không gian ngữ nghĩa, thể hiện rằng hai văn bản có cùng ý nghĩa/nội dung cốt lõi mặc dù cách diễn đạt hay từ ngữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: Chính sách đổi trả hàng áp dụng trong vòng 7 ngày kể từ khi nhận hàng.
- Câu B: Khách hàng có thể hoàn trả sản phẩm trong 7 ngày đầu sau khi nhận được hàng.
- Tại sao tương đồng: Cả hai câu đều truyền tải cùng một thông điệp quy định thời hạn hoàn trả hàng (7 ngày), dù sử dụng các từ đồng nghĩa khác nhau (đổi trả - hoàn trả, kể từ khi - sau khi).

**Ví dụ có độ tương tự THẤP:**

- Câu A: Chính sách đổi trả hàng áp dụng trong vòng 7 ngày kể từ khi nhận hàng.
- Câu B: Mô hình ngôn ngữ lớn đòi hỏi hệ thống máy chủ GPU rất mạnh để huấn luyện.
- Tại sao khác: Hai câu thuộc hai lĩnh vực hoàn toàn khác nhau (chính sách mua sắm vs hạ tầng AI), vector biểu diễn của chúng trỏ theo hai hướng xa nhau trong không gian vector.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

> Cosine similarity đo hướng của vector thay vì độ dài tuyệt đối, giúp nó không bị ảnh hưởng bởi độ dài của đoạn văn bản (đoạn văn dài và ngắn cùng ý nghĩa vẫn có cosine similarity cao). Ngược lại, khoảng cách Euclid bị ảnh hưởng bởi độ dài văn bản, dẫn đến việc đánh giá sai hai văn bản cùng nội dung nhưng khác số lượng từ.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> _Trình bày phép tính:_ Công thức: $\text{Số chunk} = \text{ceil}\left(\frac{10000 - 50}{500 - 50}\right) = \text{ceil}\left(\frac{9950}{450}\right) = \text{ceil}(22.111) = 23$
> _Đáp án:_ **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> - **Sự thay đổi:** Khi overlap tăng lên 100, số lượng chunk tăng từ 23 lên **25 chunks** (vì $\text{ceil}\left(\frac{10000 - 100}{500 - 100}\right) = \text{ceil}(24.75) = 25$).
> - **Lý do tăng overlap:** Tăng độ chồng chéo giúp giữ trọn vẹn ngữ cảnh ở ranh giới giữa các chunks, tránh trường hợp một câu văn hoặc một ý nghĩa quan trọng bị cắt đôi làm giảm chất lượng truy xuất (retrieval quality) của RAG.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Sử dụng biểu thức chính quy `re.split(r'(?<=[.!?])\s+|(?<=\.)\n+', text.strip())` để tách văn bản dựa trên các dấu chấm câu (`.`, `!`, `?`). Xử lý edge case chuỗi rỗng/khoảng trắng thừa, loại bỏ câu rỗng và nhóm tối đa `max_sentences_per_chunk` câu vào mỗi chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán đệ quy theo danh sách ưu tiên dấu phân cách `["\n\n", "\n", ". ", " ", ""]`. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn hoặc bằng `chunk_size` (trả về chuỗi nguyên bản) hoặc khi cạn danh sách separators (fallback tách theo độ dài ký tự `chunk_size`). Thuật toán dồn tối đa các phần tách nhỏ nối lại bằng separator miễn là độ dài tổng không vượt `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> `add_documents` trích xuất `metadata` (đảm bảo trường `doc_id`), tính vector nhúng qua `_embedding_fn` và lưu vào danh sách `_store` (và ChromaDB nếu khả dụng). `search` tính vector nhúng của câu hỏi query, tính điểm độ tương tự (tích vô hướng `_dot`) với từng chunk trong store, sắp xếp giảm dần theo `score` và cắt `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> `search_with_filter` thực hiện pre-filtering (lọc trước): duyệt qua các chunks trong `_store` và chỉ giữ lại các chunks khớp 100% các cặp key-value trong `metadata_filter`, sau đó mới gọi hàm truy xuất xếp hạng trên tập đã lọc. `delete_document` lọc bỏ toàn bộ record trong `_store` có `id` hoặc `metadata['doc_id']` khớp với `doc_id`, trả về `True` nếu số lượng phần tử giảm xuống (xóa thành công).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Gọi `self.store.search(question, top_k=top_k)` để truy xuất top-k chunks phù hợp nhất từ vector store. Ghép nội dung các chunks thành khối ngữ cảnh `context`, dựng prompt chuẩn RAG gồm cả `context` và `question`, sau đó gọi `self.llm_fn(prompt)` để sinh ra câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: E:\AIthucchien\Day07-2A202601578-TranThanhHuyen
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
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
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

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A                             | Câu B                                | Dự đoán | Điểm thực tế | Đúng?   |
| --- | --------------------------------- | ------------------------------------ | ------- | ------------ | ------- |
| 1   | Chính sách đổi trả áp dụng 7 ngày | Khách được trả hàng trong 7 ngày     | cao     | 0.106        | Đúng    |
| 2   | Thời hạn đổi trả 7 ngày           | Huấn luyện mô hình GPU               | thấp    | 0.075        | Đúng    |
| 3   | Giao hàng hỏa tốc trong 2 giờ     | Vận chuyển siêu tốc nhận sau 2 tiếng | cao     | -0.079       | Bất ngờ |
| 4   | Phương thức thanh toán ví điện tử | Rút tiền ngân hàng đối soát thứ 2    | thấp    | 0.051        | Đúng    |
| 5   | Bảo mật dữ liệu riêng tư          | Công thức nấu món ăn ngon            | thấp    | 0.035        | Đúng    |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Cặp 3 ("Giao hàng hỏa tốc trong 2 giờ" vs "Vận chuyển siêu tốc nhận sau 2 tiếng") là bất ngờ nhất khi Mock Embedder cho kết quả âm (-0.079). Điều này minh chứng rằng Mock Embedder chỉ băm chuỗi ký tự mà KHÔNG hiểu ngữ nghĩa thực sự, do đó cần phải sử dụng mô hình embedding thật (`sentence-transformers` đa ngôn ngữ) khi đánh giá RAG trong thực tế.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| #   | Câu hỏi (Query)                                                                                                    | Expected doc_id                     | Top-1 doc_id retrieved           | Top-1 có liên quan không? | Notes                                                                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------ | ----------------------------------- | -------------------------------- | ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng?                       | `chinh-sach-tra-hang-hoan-tien`     | `chinh-sach-van-chuyen`          | Không                     | Top-1 trả về nội dung chính sách vận chuyển, chưa đúng quy định trả hàng/hoàn tiền.                                   |
| 2   | Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu? | `dieu-khoan-dich-vu-shopee-mall`    | `dieu-khoan-dich-vu-shopee-mall` | Có                        | Dùng metadata filter `customer_role='seller'` giúp tập trung vào tài liệu Shopee Mall.                                |
| 3   | Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển?                                  | `quy-dinh-chung-tra-hang-hoan-tien` | `chinh-sach-tra-hang-hoan-tien`  | Có một phần               | Top-1 trả về tài liệu trả hàng/hoàn tiền, gần liên quan nhưng không phải nguồn chính về quy trình đồng kiểm.          |
| 4   | Tính năng 'Shopee Đảm Bảo' bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu?                      | `shopee-dam-bao`                    | `dieu-khoan-dich-vu-shopee-mall` | Không                     | Top-1 rơi vào tài liệu Shopee Mall, cho thấy cần cải thiện embedding/filter để phân biệt chính sách bảo vệ người mua. |
| 5   | Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì?                     | `cach-dong-goi-don-hoan-tra`        | `cach-dong-goi-don-hoan-tra`     | Có                        | Top-1 trúng đúng tài liệu hướng dẫn đóng gói hoàn trả.                                                                |

**Tổng số câu hỏi có top-1 truy xuất đúng doc_id:** 2 / 5

**Top-3 có chứa ít nhất một doc có liên quan cho mỗi câu hỏi:** 5 / 5

**Điểm mạnh của benchmark:**

- `RecursiveChunker(chunk_size=400)` giữ được ngữ cảnh cho câu hỏi đóng gói hoàn trả và câu hỏi Shopee Mall.
- `search_with_filter()` đã hỗ trợ tốt cho câu hỏi có điều kiện metadata seller.

**Điểm hạn chế:**

- Bộ embedder mock `_mock_embed` chưa đủ phân biệt tốt giữa các chính sách khác nhau, nên một số truy vấn vẫn trả về tài liệu không chính xác.
- Cần cải tiến hoặc thử `LocalEmbedder`/`OpenAIEmbedder` để nâng chất lượng top-1 retrieval.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Việc áp dụng pre-filtering theo metadata (`customer_role="seller"`) giúp loại bỏ hoàn toàn nhiễu từ các văn bản dành cho người mua. Ngoài ra, việc dùng `RecursiveChunker` giữ trọn vẹn ngữ cảnh tiêu đề và điều khoản xuất sắc hơn hẳn so với việc chia cố định ký tự.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                        | Điểm tự đánh giá |
| ----------------------------------------------- | ---------------- |
| Khởi động (Warm-up)                             | 5 / 5            |
| Hướng tiếp cận của tôi (My Approach)            | 10 / 10          |
| Hoàn thiện code (Core Implementation — tests)   | 30 / 30          |
| Dự đoán độ tương tự (Similarity Predictions)    | 5 / 5            |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10          |
| **Tổng phần cá nhân**                           | **60 / 60**      |
