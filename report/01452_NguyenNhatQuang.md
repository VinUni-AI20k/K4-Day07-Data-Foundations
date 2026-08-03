# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Nhật Quang\
**Nhóm:** 3HQ\
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector có hướng gần giống nhau, nên hai đối tượng mà chúng biểu diễn thường có nội dung hoặc đặc trưng tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Món đồ có giá cao nhất"
- Câu B: "Sản phẩm có mức giá cao nhất"
- Tại sao tương đồng: Cả hai câu đều nói về việc tìm kiếm một sản phẩm hoặc mặt hàng có giá trị lớn nhất trong một tập hợp.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Món đồ có giá cao nhất"
- Câu B: "Thời tiết hôm nay rất đẹp"
- Tại sao khác: Câu A nói về giá cả và sản phẩm, trong khi câu B nói về thời tiết. Hai chủ đề này hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity thường được ưu tiên cho text embeddings vì nó tập trung vào hướng của vector, tức là mức độ giống nhau về ngữ nghĩa, thay vì bị ảnh hưởng nhiều bởi độ lớn của vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
>
> Số chunk = ceil(10000 - 50) / (500 - 50) + 1 = 23 Chunk

> *Đáp án:* 23 Chunk

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk tăng lên 25 Chunk vì chunk = ceil(10000 - 100) / (500 - 100) + 1 = 25 chunk
>
> Muốn độ chồng chéo nhiều hơn để đảm bảo các câu quan trọng không bị cắt đôi giữa chừng và giữ cho các câu ít tỉ lệ bị mất ngữ cảnh (context) hơn. Tuy nhiên, overlap nhiều sẽ làm tăng số lượng chunk và tốn nhiều tài nguyên lưu trữ/tính toán hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`FixedSizeChunker.chunk`** — hướng tiếp cận:
> Thuật toán kiểm tra ký tự thứ 3 (`index = 2`) hoặc thứ 4 (`index = 3`) ở đầu đoạn văn bản xem có phải dấu cách (`' '`) hay không. Nếu thỏa mãn và khoảng cách đến ký tự xuống dòng (`\n`) ở cuối dòng nhỏ hơn `chunk_size`, văn bản sẽ được cắt từ vị trí hiện tại tới dấu xuống dòng đó. Trường hợp không thỏa mãn hoặc dòng quá dài, thuật toán phân chia theo giới hạn `chunk_size` và bước nhảy `step`.

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy (regex) `(?<=\. |\! |\? |\.\n)` với kỹ thuật lookbehind để phân tách văn bản dựa trên các dấu kết câu (`. `, `! `, `? `, `.\n`) mà vẫn giữ nguyên vẹn dấu câu trong văn bản. Sau khi tách, tôi loại bỏ khoảng trắng thừa hai đầu từng câu bằng `strip()`, bỏ qua các chuỗi rỗng và gom nhóm các câu liên tiếp lại thành từng chunk theo tham số `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Sử dụng danh sách ký tự phân cách theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Thuật toán thực hiện đệ quy qua từng mức separator để chia nhỏ văn bản. Base case là khi chuỗi đã nhỏ hơn `chunk_size` hoặc đã hết separator (thì cắt cứng theo độ dài). Sau đó, các chunk nhỏ liền kề được ghép lại sao cho không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Dữ liệu được chuẩn hóa thành các record chứa `id`, `content`, `metadata` và vector `embedding` (tạo ra từ `_embedding_fn`). Các record được lưu trữ trong danh sách `_store` (và đồng bộ vào ChromaDB collection nếu khả dụng). Khi tìm kiếm `search()`, câu hỏi được embed thành vector rồi tính Cosine Similarity với tất cả các record, sau đó sắp xếp giảm dần để chọn ra top-k kết quả có điểm cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Thực hiện **lọc trước (pre-filtering)**: đầu tiên duyệt qua `_store` để chọn ra các chunk thỏa mãn toàn bộ thuộc tính trong `metadata_filter`, sau đó mới tiến hành xếp hạng độ tương đồng Cosine trên tập đã lọc. Hàm `delete_document` lọc lại `_store` để loại bỏ mọi record có `id` hoặc `metadata['doc_id']` khớp với `doc_id` truyền vào và trả về `True` nếu có ít nhất 1 chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Phương thức `answer` gọi `store.search(question, top_k)` để lấy top-k chunk liên quan nhất. Ngữ cảnh (context) được ghép từ nội dung các chunk tìm được, sau đó đưa vào cấu trúc prompt tiêu chuẩn: `Context:\n{context}\n\nQuestion: {question}\nAnswer:`. Prompt này được gửi tới `llm_fn` để tổng hợp câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.12.4, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/raiju/K4_Day07_3HQ_DataFoundation-
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

====================== 42 passed in 0.71s ======================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng hóa | Quy định hoàn trả sản phẩm | cao | -0.1285 | SAI |
| 2 | Người bán phải công bố chính sách hoàn trả | Người bán phải công bố chính sách hoàn trả | cao | 1.0000 | Đúng |
| 3 | Thời hạn trả lời đề nghị giao kết là 12 giờ | Sàn phải thông báo trước ít nhất 5 ngày | thấp | -0.2073 | Đúng |
| 4 | Chính sách kiểm hàng là điều kiện giao dịch chung | Điều kiện giao dịch chung phải công bố chính sách hoàn trả | cao | 0.0456 | SAI |
| 5 | Thủ tục đăng ký website cung cấp dịch vụ TMĐT | Giá niêm yết được hiểu là đã bao gồm mọi chi phí | thấp | -0.0960 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp số 1 ("Chính sách đổi trả hàng hóa" và "Quy định hoàn trả sản phẩm") bất ngờ nhất vì hai câu có cùng ý nghĩa nhưng điểm thực tế lại là số âm (-0.1285). Điều này cho thấy với backend thử nghiệm `MockEmbedder` (bản chất là băm MD5), embedding chưa phản ánh được ngữ nghĩa thực sự mà chỉ đóng vai trò phân bổ chỉ số ngẫu nhiên cho mục đích kiểm thử hệ thống.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Nếu người bán không công bố rõ thời hạn trả lời, sau bao lâu đề nghị giao kết hợp đồng hết hiệu lực? | `nd52-quy-trinh-dat-hang-truc-tuyen::chunk_6` (Điều 20. Chấm dứt đề nghị giao kết hợp đồng) | 0.3833 | Có | Trả lời chính xác thời hạn là 12 (mười hai) giờ |
| 2 | Sàn giao dịch TMĐT phải thông báo trước bao nhiêu ngày khi thay đổi quy chế hoạt động? | `nd52-quy-che-hoat-dong-san::chunk_2` (Điều 38 Khoản 3) | 0.2677 | Có | Trả lời chính xác phải thông báo trước ít nhất 5 ngày |
| 3 | Cơ chế rà soát và xác nhận nội dung hợp đồng phải hiển thị những thông tin gì trước khi đặt hàng? | `nd52-quy-trinh-dat-hang-truc-tuyen::chunk_4` (Điều 18. Rà soát và xác nhận nội dung hợp đồng) | 0.3495 | Có | Hiển thị các thông tin về giá cả, phương thức thanh toán, giao hàng |
| 4 | Chính sách kiểm hàng có phải là điều kiện giao dịch chung bắt buộc không? | `nd85-2021-diem-moi-bao-ve-nguoi-tieu-dung::chunk_5` (Mục 4. Chính sách kiểm hàng) | 0.3591 | Có | Trả lời chính xác từ 01/01/2022 chính sách kiểm hàng là bắt buộc |
| 5 | Website niêm yết giá mà không nói rõ đã bao gồm thuế và phí chưa thì hiểu thế nào? | `seller-listing::chunk_3` (Điều 31. Thông tin về giá cả) | 0.2356 | Có | Trả lời chính xác được hiểu là đã bao gồm mọi chi phí |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua phần demo, bài học hay nhất tôi học được là việc áp dụng kỹ thuật **Heading-based Chunking** kết hợp với việc giữ thông tin breadcrumb (tiêu đề cha) giúp duy trì ngữ cảnh bài viết cực kỳ hiệu quả. Đồng thời, việc sử dụng metadata pre-filtering đóng vai trò quan trọng trong việc loại bỏ bớt nhiễu dữ liệu trước khi thực hiện đo độ tương đồng vector.

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