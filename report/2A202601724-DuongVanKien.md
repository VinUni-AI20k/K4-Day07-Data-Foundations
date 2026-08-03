# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Dương Văn Kiên - 2A202601724
**Nhóm:** ABCXYZ
**Ngày:** 08/03/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding trỏ gần như cùng hướng trong không gian nhiều chiều, nghĩa là hai đoạn văn bản mang ý nghĩa/ngữ cảnh gần giống nhau, dù cách diễn đạt (từ ngữ) có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Chính sách đổi trả hàng trong vòng 7 ngày kể từ khi nhận hàng."
- Câu B: "Khách hàng có thể trả lại sản phẩm trong 7 ngày sau khi nhận."
- Tại sao tương đồng: cùng diễn đạt một ý nghĩa (thời hạn đổi trả 7 ngày), chỉ khác cách dùng từ và cấu trúc câu.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng trong vòng 7 ngày kể từ khi nhận hàng."
- Câu B: "Người bán cần cung cấp giấy tờ xác minh danh tính khi đăng ký gian hàng."
- Tại sao khác: hai câu nói về hai chủ đề hoàn toàn khác nhau (đổi trả vs. điều kiện đăng ký người bán), không chia sẻ ngữ cảnh ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ quan tâm đến **hướng** của vector (ngữ nghĩa) chứ không quan tâm đến **độ lớn** (magnitude), vốn có thể bị ảnh hưởng bởi độ dài văn bản hay cách chuẩn hóa embedding. Euclidean distance nhạy cảm với độ lớn này, nên hai văn bản cùng nghĩa nhưng độ dài khác nhau có thể bị Euclidean distance đánh giá là "xa nhau" một cách sai lệch.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Trình bày phép tính: số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23
> Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> số lượng chunk = làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = **25 chunks** — tăng overlap làm bước trượt (step = chunk_size - overlap) nhỏ hơn nên số chunk tăng lên. Overlap lớn hơn giúp giữ ngữ cảnh liên tục giữa các chunk liền kề (câu/ý bị cắt ở ranh giới chunk trước vẫn xuất hiện đầy đủ ở chunk sau), giảm nguy cơ mất thông tin quan trọng nằm vắt qua điểm cắt.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text.strip())` để tách câu dựa trên lookbehind sau dấu `.`, `!`, `?` theo sau bởi khoảng trắng — tránh làm mất dấu câu ở cuối mỗi câu (khác với `str.split`). Sau khi tách, lọc bỏ chuỗi rỗng và strip khoảng trắng thừa, rồi nhóm theo từng `max_sentences_per_chunk` câu liên tiếp, nối lại bằng dấu cách. Edge case: văn bản rỗng trả về `[]` ngay từ đầu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy: thử tách văn bản theo separator ưu tiên cao nhất (`\n\n` → `\n` → `. ` → `" "` → `""`); nếu một phần sau khi tách vẫn dài hơn `chunk_size`, tiếp tục đệ quy phần đó với danh sách separator còn lại (bỏ separator vừa dùng). Base case: khi `len(current_text) <= chunk_size` thì trả về `[current_text]` luôn; khi hết separator (`remaining_separators` rỗng) hoặc separator là chuỗi rỗng `""`, dùng cắt cứng theo `chunk_size` ký tự làm phương án cuối để đảm bảo luôn kết thúc.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` gọi `_make_record` cho mỗi `Document` — embed nội dung bằng `self._embedding_fn`, lưu `id`, `content`, `metadata` (đảm bảo có `doc_id`) và `embedding` vào list `self._store` (in-memory). `search` embed câu query rồi tính dot product giữa vector query và từng vector đã lưu (`_dot`), sắp xếp giảm dần theo `score` và cắt lấy `top_k` kết quả đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước** khi tìm kiếm: `search_with_filter` duyệt `self._store`, chỉ giữ lại các record có `metadata` khớp toàn bộ điều kiện trong `metadata_filter` (dùng `dict.get` để so khớp từng cặp key-value), rồi mới gọi `_search_records` để tính similarity trên tập đã lọc — tránh tính embedding similarity cho các bản ghi chắc chắn không liên quan. `delete_document` dùng list comprehension để giữ lại mọi record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để trả về `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `__init__` lưu tham chiếu đến `store` và `llm_fn`. `answer` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan, nối nội dung (`content`) của chúng bằng hai dòng trống làm phần "Context", rồi chèn vào một prompt template có 3 phần rõ ràng: hướng dẫn (chỉ trả lời dựa trên context), Context, và Question — cuối cùng gọi `llm_fn(prompt)` và trả về kết quả string.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
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

============================= 42 passed in 0.10s ==============================
```

> Lưu ý: kết quả trên chạy khi các file `.py` còn ở `src/` (trước khi chuyển vào `src/2A202601724-DuongVanKien/` để nộp). Trước khi chấm bài, cần tạm chuyển các file trở lại `src/` để `pytest`/`ingest.py` chạy được (do import cố định `from src.chunking import ...`).

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Bạn có thể hoàn trả sản phẩm trong 14 ngày." | "Thời hạn đổi trả là 14 ngày kể từ ngày nhận hàng." | cao | 0.5987 | Đúng |
| 2 | "Apple không bảo hành pin bị chai theo thời gian." | "Linh kiện tiêu hao như pin không nằm trong diện bảo hành." | cao | 0.3528 | **Sai** |
| 3 | "Apple sẽ không bao giờ hỏi số thẻ tín dụng qua email." | "Trẻ em dưới 15 tuổi cần được cha mẹ đồng ý mới tạo được Apple ID." | thấp | 0.6366 | **Sai** |
| 4 | "Chính sách quyền riêng tư của Apple." | "Hôm nay trời rất đẹp và nắng." | thấp | 0.4334 | Đúng (nhưng cao hơn kỳ vọng) |
| 5 | "Kích hoạt xác thực hai yếu tố để bảo mật tài khoản." | "Bật 2FA giúp Apple ID an toàn hơn." | cao | 0.2315 | **Sai** |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 5** (0.2315 — thấp nhất trong 5 cặp) dù về mặt ý nghĩa hai câu gần như đồng nhất ("xác thực hai yếu tố" = "2FA", cùng nói về bảo mật Apple ID). Điều này cho thấy embedding không đơn thuần "hiểu nghĩa" như con người mà nhạy cảm với **bề mặt từ vựng và cấu trúc câu** — viết tắt "2FA" và cụm đầy đủ "xác thực hai yếu tố" có thể được biểu diễn khác xa nhau trong không gian vector nếu mô hình không được huấn luyện đủ với các viết tắt tiếng Anh trong ngữ cảnh tiếng Việt. Ngược lại, cặp 3 (hai câu nói về hai chủ đề khác nhau: bảo mật email vs. quy định độ tuổi) lại có score cao bất thường (0.6366) — có thể vì cả hai đều thuộc "văn phong chính sách Apple" (nhắc đến "Apple", "Apple ID", cấu trúc câu quy định), khiến mô hình multilingual MiniLM bắt được sự tương đồng về *thể loại văn bản* hơn là về *nội dung cụ thể*. Bài học: cosine similarity phản ánh sự gần gũi trong không gian embedding của mô hình cụ thể, không phải một chuẩn mực tuyệt đối về "ý nghĩa giống nhau" theo trực giác con người.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Bao nhiêu ngày để hoàn trả sản phẩm? | sales-refund: "...hoàn trả trong vòng 14 ngày kể từ ngày nhận sản phẩm..." | 0.6966 | Có, đúng top-1 | Đúng, trích được "14 ngày" |
| 2 | Pin/lớp bảo vệ chai theo thời gian có được bảo hành? | warranty: "...không áp dụng cho: (a) linh kiện tiêu hao như pin..." | 0.3531 | Có, đúng top-1 | Đúng, trích được lý do loại trừ |
| 3 | Trẻ dưới 15 tuổi có tự do tạo Apple ID? | privacy: "...tôn trọng quyền biết, truy cập, sửa chữa dữ liệu cá nhân..." | 0.5085 | **Không** — chunk đúng (media-terms, "trẻ dưới 15 tuổi cần cha mẹ chấp thuận") chỉ đứng top-2 | Sai/lạc đề vì context top-1 không liên quan đến câu hỏi |
| 4 | Có hoàn tiền khi lỡ mua app trên App Store? | sales-refund: "...phần mềm có giấy phép... không thể hoàn trả khi tem niêm phong bị rách..." | 0.4707 | **Không** — thông tin đúng (giao dịch App Store là "final, non-refundable") nằm ở `media-terms`, không xuất hiện trong top-3 | Sai — agent sẽ trả lời dựa trên chính sách hoàn trả sản phẩm vật lý, không phải chính sách App Store |
| 5 | Email đòi số thẻ tín dụng, có nên làm theo? | phishing: "...Apple sẽ không bao giờ yêu cầu cung cấp số thẻ tín dụng qua email..." | 0.4012 | Có, đúng top-1 | Đúng, trích được khuyến cáo và hướng dẫn báo cáo |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5 (câu 3, 4 retrieve nhầm tài liệu dù embedding score vẫn cao)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chunker của tôi (`BulletPointChunker`) tốt ở việc giữ trọn từng điều khoản không bị vỡ vụn, nhưng thất bại ở các câu hỏi cần thông tin nằm rải rác ở nhiều tài liệu khác chủ đề gần nhau (ví dụ câu 4: "App Store" vs "sản phẩm vật lý" đều thuộc phạm trù "mua hàng/hoàn tiền" nên embedding dễ nhầm). Điều này cho thấy chunking tốt chỉ giải quyết được vấn đề *coherence*, còn vấn đề *độ đặc thù chủ đề giữa các tài liệu* cần thêm metadata filtering (`category`) mới xử lý triệt để — đúng như phần "Tiện ích Metadata" trong `docs/EVALUATION.md`.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
