# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Chí Vũ
**Nhóm:** Nhóm K4 (điền tên nhóm — xem `REPORT_NHOM.md`)
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai câu/văn bản có các vector embedding gần nhau về **hướng** trong không gian nhiều chiều, tức là chúng mang ý nghĩa tương đồng về mặt ngữ nghĩa (dù độ dài văn bản có thể khác nhau). Cosine cao phản ánh "cùng chủ đề / cùng ý", không phản ánh độ dài hay số từ trùng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua cần gửi yêu cầu đổi trả trong thời hạn quy định trên trang sản phẩm.
- Câu B: Khách hàng phải gửi yêu cầu trả hàng trong thời hạn nêu trên chính sách của sàn.
- Tại sao tương đồng: Cùng diễn đạt một ý (nghĩa vụ gửi yêu cầu đổi trả đúng hạn), chỉ khác từ ngữ như "người mua/khách hàng", "trang sản phẩm/chính sách của sàn" → embedding gần cùng hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Yêu cầu đổi trả phải kèm bằng chứng phù hợp khi hàng bị lỗi.
- Câu B: Sản phẩm bị hạn chế hoặc bị cấm không được phép đăng bán.
- Tại sao khác: Một bên nói về quy trình đổi trả của người mua, bên kia nói về quy định đăng bán của người bán — hai khía cạnh khác nhau của chính sách sàn nên góc giữa hai vector lớn hơn.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ quan tâm **góc/hướng** giữa hai vector nên bất biến với độ lớn (norm). Embedding của câu dài có norm lớn, câu ngắn có norm nhỏ; khoảng cách Euclid sẽ bị lệch do khác biệt về độ dài, trong khi cosine so sánh đúng "độ gần nghĩa" và nằm gọn trong khoảng [-1, 1] dễ đánh giá.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11) = 23`
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: `ceil((10,000 - 100) / (400)) = ceil(24.75) = 25` → nhiều chunk hơn (25 so với 23). Tăng overlap giúp mỗi vùng biên giữa hai chunk xuất hiện trong cả hai chunk, giảm nguy cơ bị "cắt đứt" giữa chừng một câu/ý quan trọng, giúp retrieval vẫn tìm thấy đủ ngữ cảnh khi câu hỏi chạm vào ranh giới chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng biểu thức chính quy `re.split(r"(?<=[.!?])\s+", text)` — split ngay sau dấu câu `.` `!` `?` (lookbehind) theo sau bởi khoảng trắng, nên văn bản tiếng Việt không có khoảng cách sau dấu chấm vẫn tách đúng. Edge cases: lọc bỏ các phần rỗng và `strip()` từng câu, xử lý text rỗng trả về `[]`, và gom tối đa `max_sentences_per_chunk` câu (mặc định 3) rồi nối bằng dấu cách.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy: nếu độ dài hiện tại `<= chunk_size` thì trả về `[current_text]` (base case). Ngược lại, thử các separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`: tách theo separator đang xét, giữ lại separator ở cuối mỗi phần, rồi gom các phần vào một buffer; nếu một phần vẫn quá lớn thì **đệ quy** xuống separator tiếp theo (`remaining_separators[1:]`), còn nếu hết separator thì `_hard_split` (cắt cứng theo `chunk_size`). Buffer được "flush" khi thêm phần mới vượt quá `chunk_size`, và gom được các mảnh nhỏ lại với nhau để không tạo chunk lẻ tẻ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `_make_record` gọi `embedding_fn(content)` (mock mặc định, hoặc embedder thật được tiêm vào) để tạo vector cho từng chunk, rồi lưu record `{id, content, metadata, embedding}` vào danh sách trong bộ nhớ (hoặc `collection.add` của ChromaDB). `_search_records` nhúng câu hỏi, tính **tích vô hướng (dot product)** giữa vector query và từng vector lưu trữ, sắp xếp giảm dần và cắt lấy `top_k` kèm trường `score` (vì các embedder đều chuẩn hoá chuẩn vector, dot product ≈ cosine similarity). Với ChromaDB dùng `collection.query(query_embeddings=..., n_results=top_k)` và đổi distance thành score bằng `1 - distance`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước**, tìm **sau**: với bộ nhớ, `search_with_filter` xây danh sách `candidates` khớp `all(metadata.get(key) == value)` của `metadata_filter` rồi mới gọi `_search_records`; với ChromaDB, truyền thẳng `where=metadata_filter` vào `query` để lọc trong cơ sở dữ liệu. `delete_document` xoá mọi chunk thuộc một doc: với bộ nhớ, lọc lại `self._store` bỏ các record có `id` hoặc `metadata["doc_id"]` trùng (trả về `True` nếu kích thước giảm); với Chroma, lấy id theo `where={"doc_id": ...}` rồi `collection.delete(ids=...)`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Theo mẫu RAG: `store.search(question, top_k=3)` để lấy 3 chunk liên quan nhất, nối nội dung bằng `"\n\n"` thành `context`, rồi build prompt tiếng Việt có cấu trúc: chỉ thị vai trò → "Ngữ cảnh:" (đưa context đã truy xuất) → "Câu hỏi:" → yêu cầu trả lời dựa trên ngữ cảnh và **nói rõ nếu không tìm thấy** thông tin. Toàn bộ prompt được truyền vào `llm_fn` (hàm LLM được tiêm), giúp dễ test và dễ thay backend LLM.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/apple/Documents/GitHub/AIInAction/Day07-2A202601274-Nguyen-Thanh-Binh
plugins: anyio-4.14.2
collecting ... collected 42 items

../tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
../tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
../tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
../tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
../tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
../tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
../tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
../tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
../tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
../tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
../tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
../tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
../tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
../tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
../tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
../tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
../tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
../tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
../tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
../tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
../tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
../tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
../tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
../tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
../tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
../tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
../tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
../tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
../tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
../tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
../tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
../tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
../tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
../tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
../tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
../tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
../tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
../tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
../tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
../tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
../tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
../tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

> Lệnh chạy trên gói `src` cá nhân (gói `Tran-Chi-Vu-2A202601044/src`):
> `LAB_SOLUTION_PACKAGE=src pytest ../tests/ -v` (dùng `--import-mode=importlib` để chắc chắn import đúng gói cá nhân).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy với embedder ngôn ngữ thật (`intfloat/multilingual-e5-small` qua `LocalEmbedder`) vì mock embedding cho kết quả gần như ngẫu nhiên và không phản ánh ngữ nghĩa tiếng Việt.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua cần gửi yêu cầu đổi trả trong thời hạn quy định trên trang sản phẩm. | Khách hàng phải gửi yêu cầu trả hàng trong thời hạn nêu trên chính sách của sàn. | cao | 0.9346 | ✅ |
| 2 | Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác. | Nhà bán hàng có trách nhiệm đăng tải mô tả sản phẩm đúng và đầy đủ. | cao | 0.9570 | ✅ |
| 3 | Yêu cầu đổi trả phải kèm bằng chứng phù hợp khi hàng bị lỗi. | Sản phẩm bị hạn chế hoặc bị cấm không được phép đăng bán. | thấp | 0.8697 | ❌ |
| 4 | Hệ thống nhúng câu hỏi rồi xếp hạng các vector theo độ tương tự. | Chính sách giao hàng quy định thời gian vận chuyển cụ thể cho từng khu vực. | thấp | 0.8541 | ❌ |
| 5 | Quy trình chia nhỏ tài liệu ảnh hưởng trực tiếp đến chất lượng truy xuất. | Chia nhỏ đệ quy giúp cân bằng giữa bảo toàn ngữ cảnh và kích thước chunk. | cao | 0.8801 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3 và cặp 4: dù tôi dự đoán "thấp" (chủ đề hoàn toàn khác nhau) nhưng cả hai đều đạt ~0.85–0.87. Điều này cho thấy cosine similarity của embedder đa ngữ có một "mức nền" khá cao: các câu cùng ngôn ngữ, cùng phong cách câu chính sách/FAQ, dù nội dung khác nhau vẫn được đặt gần nhau trong một vùng đậm đặc của không gian vector. Vì vậy giá trị tuyệt đối ~0.85 không đồng nghĩa với "cùng ý" — chỉ nên dùng độ tương đối giữa các ứng viên để xếp hạng, và cần khoảng cách chênh rõ mới kết luận liên quan. Embedding biểu diễn "sự gần gũi về mặt thống kê của ngôn ngữ" chứ không phải logic khái niệm rời rạc như con người.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`). *(Phần này liên quan đến nhóm — sẽ điền sau khi nhóm thống nhất bộ câu hỏi đánh giá.)*

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Viết 2-3 câu sau khi xem demo của các nhóm khác.)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4.5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | _ / 10 (chờ bộ câu hỏi của nhóm) |
| **Tổng phần cá nhân** | **__ / 60** |
