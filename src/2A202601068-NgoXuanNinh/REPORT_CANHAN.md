# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngô Xuân Ninh
**Nhóm:** T-Hexa
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> có nghĩa là từ khóa của 2 câu dạng vector có gốc cosin nhỏ khi mang ý nghĩa có sự tương đồng nhau

**Ví dụ có độ tương tự CAO:**
- Câu A: con hổ
- Câu B: con sư tử
- Tại sao tương đồng: đều là động vật và thường được nhắc tới cạnh nhau từ các nguồn mà AI học

**Ví dụ có độ tương tự THẤP:**
- Câu A: chính sách đổi trả
- Câu B: thời tiết hôm nay
- Tại sao khác: vì mang ý nghĩa không tương đồng nhau

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ so sánh **hướng** của vector chứ không phụ thuộc độ dài (magnitude), nên hai câu cùng ý nghĩa nhưng độ dài văn bản khác nhau vẫn cho điểm tương tự cao. Euclidean distance lại nhạy với độ lớn vector, nên hai văn bản cùng nghĩa nhưng dài ngắn khác nhau có thể bị đánh giá sai là "khác xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* số lượng chunk = làm_tròn_lên((10000 − 50) / (500 − 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23
> *Đáp án:* 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Overlap tăng lên 100 thì bước nhảy giữa các chunk giảm (500−100=400 thay vì 450), nên số lượng chunk **tăng** lên: làm_tròn_lên((10000−100)/(500−100)) = làm_tròn_lên(9900/400) = 25 chunk. Muốn overlap nhiều hơn vì nó giữ lại ngữ cảnh liền mạch qua ranh giới giữa hai chunk, tránh việc một câu/ý bị cắt đứt giữa chừng và mất thông tin khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+|(?<=\.)\n", text)` để tách câu dựa trên ranh giới ". "/"! "/"? " hoặc dấu chấm cuối dòng, dùng lookbehind để giữ lại dấu câu ở cuối mỗi câu thay vì bị cắt mất. Sau khi tách, lọc bỏ chuỗi rỗng và `.strip()` từng câu, rồi gom mỗi `max_sentences_per_chunk` câu liên tiếp thành một chunk bằng cách duyệt theo bước nhảy (`range(0, len(sentences), max_sentences_per_chunk)`). Trường hợp ngoại lệ: text rỗng trả về `[]`, và nếu `max_sentences_per_chunk` được truyền `<1` thì `__init__` đã chặn bằng `max(1, ...)`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `chunk()` chỉ gọi `_split(text, self.separators)`. `_split` là đệ quy: base case là khi `current_text` rỗng (trả `[]`) hoặc đã đủ ngắn (`len <= chunk_size`, trả `[current_text]`); nếu hết separator để thử thì rơi về cắt cứng theo `chunk_size` (giống `FixedSizeChunker` không overlap). Ở mỗi tầng đệ quy, tách văn bản theo separator đầu tiên còn lại, rồi gộp dần các phần lại thành chunk cho tới khi gần đầy `chunk_size`; nếu một phần đơn lẻ vẫn còn quá lớn thì gọi đệ quy `_split(part, rest)` với danh sách separator còn lại (ưu tiên `"\n\n" → "\n" → ". " → " " → ""`).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hoá qua `_make_record` thành một dict `{id, content, metadata, embedding}` (embedding tính bằng `self._embedding_fn(doc.content)`) rồi append vào danh sách in-memory `self._store`; nếu ChromaDB khởi tạo được thì đồng thời gọi `collection.add(...)` để lưu song song. `search` nhúng câu query rồi tính **dot product** (`_dot`) giữa vector query và embedding của từng record đã lưu (embedding được chuẩn hoá về norm 1 nên dot product tương đương cosine similarity), sắp xếp giảm dần theo score và trả về `top_k` kết quả đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc trước, tìm kiếm sau**: duyệt `self._store`, giữ lại các record mà mọi cặp key/value trong `metadata_filter` đều khớp với `record["metadata"]`, sau đó chạy cùng logic similarity search (`_search_records`) chỉ trên tập đã lọc — cách này giúp thu hẹp không gian tìm kiếm trước khi tính điểm tương tự. `delete_document` xoá bằng cách tạo lại `self._store` chỉ giữ những record có `metadata["doc_id"] != doc_id`, rồi so sánh độ dài trước/sau để trả về `True`/`False` (không cần index riêng vì mỗi chunk đã mang `doc_id` trong metadata).

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` chỉ lưu lại tham chiếu `self.store` và `self.llm_fn`. `answer()` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan, nối nội dung các chunk (`"\n\n".join(...)`) thành khối "Context", rồi dựng một prompt cố định gồm hướng dẫn ("dùng context để trả lời, nếu không có thông tin thì nói không biết") + Context + câu hỏi, và trả về kết quả của `self.llm_fn(prompt)`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$env:LAB_SOLUTION_PACKAGE = "src.2A202601068-NgoXuanNinh"; pytest tests/ -v

============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.6.0
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED

============================= 42 passed in 0.20s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả sản phẩm bị lỗi. | Làm sao để hoàn trả hàng khi sản phẩm hư hỏng? | cao | -0.1884 | Sai |
| 2 | Người bán cần cung cấp thông tin sản phẩm chính xác. | Nhà cung cấp phải mô tả đúng tình trạng hàng hoá. | cao | -0.0424 | Sai |
| 3 | Chính sách đổi trả áp dụng trong 7 ngày. | Hôm nay trời nắng đẹp. | thấp | 0.1318 | Sai |
| 4 | Thanh toán bằng thẻ tín dụng có an toàn không? | Đơn hàng của tôi khi nào được giao? | thấp | -0.1122 | Đúng |
| 5 | Sản phẩm này còn hàng không? | Sản phẩm này đã hết hàng. | cao | -0.1539 | Sai |

> Chạy bằng `_mock_embed` (embedder mặc định cho unit test) — như README đã cảnh báo, đây là hàm băm gần-ngẫu-nhiên theo chuỗi, **không** phản ánh ngữ nghĩa thật.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 1 và cặp 5: hai câu gần như đồng nghĩa (đổi trả hàng lỗi / còn hàng hay hết hàng) lại nhận điểm cosine **âm**, thấp hơn cả cặp 3 vốn hoàn toàn không liên quan (chính sách đổi trả vs. thời tiết). Điều này cho thấy điểm số chỉ có ý nghĩa khi embedding thực sự học được ngữ nghĩa (semantic) — với `_mock_embed` (băm MD5 theo từng ký tự chuỗi), hai câu na ná nhau về mặt chữ nhưng khác nhau ở vài từ vẫn cho ra vector gần như độc lập, nên phải dùng `LocalEmbedder`/`OpenAIEmbedder` thật thì kết quả truy xuất mới đáng tin.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **[CHƯA HOÀN THÀNH — chờ nhóm]** `REPORT_NHOM.md` (Phần 1 & 3) và bộ tài liệu thật trong `data/k4_ecommerce/` chưa được nhóm hoàn thiện — hiện `returns-policy.md`/`seller-listing.md` vẫn là dữ liệu khởi động mẫu (chưa có nguồn công khai thật), và nhóm chưa chốt 5 câu hỏi đánh giá chung. Mục này cần chạy **sau khi** nhóm chốt bộ tài liệu + 5 câu hỏi, để đảm bảo trùng khớp với các thành viên khác. Bảng dưới đây sẽ điền lại khi có dữ liệu chính thức.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5 *(chờ 5 câu hỏi chính thức của nhóm)*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu — điền sau buổi demo với nhóm.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 0 / 10 *(chờ nhóm chốt tài liệu + câu hỏi)* |
| **Tổng phần cá nhân** | **50 / 60** |
