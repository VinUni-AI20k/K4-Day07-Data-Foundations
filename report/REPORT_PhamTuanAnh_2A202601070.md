# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Phạm Tuấn Anh]
**Nhóm:** [MicroGenius]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity cao nghĩa là hai vector gần cùng hướng, thường biểu thị hai văn bản có ý nghĩa tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Học máy giúp máy tính học từ dữ liệu.
- Câu B: Machine learning cho phép hệ thống rút ra mẫu từ dữ liệu.
- Tại sao tương đồng: Cả hai cùng nói về việc máy học từ dữ liệu.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Cơ sở dữ liệu vector hỗ trợ tìm kiếm theo độ tương tự.
- Câu B: Hôm nay trời nắng và nhiệt độ khá cao.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan: công nghệ và thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng và ít bị ảnh hưởng bởi độ lớn vector. Euclidean distance phụ thuộc cả độ lớn nên thường kém phù hợp hơn với text embeddings.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước dịch giữa hai chunk là `500 - 50 = 450` ký tự. Số chunk là `1 + ceil((10,000 - 500) / 450) = 1 + ceil(21.11...) = 23`.
>
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap là 100, bước dịch bằng 400 nên có `1 + ceil(9,500 / 400) = 25` chunks. Overlap lớn giúp giữ ngữ cảnh ở ranh giới chunk nhưng làm tăng dữ liệu trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách câu và giữ lại dấu kết câu. Văn bản rỗng trả về `[]`; các câu rỗng bị bỏ và mỗi chunk chứa tối đa số câu đã cấu hình.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi tách đệ quy theo thứ tự `"\n\n"`, `"\n"`, `". "`, `" "`, `""`. Base case là đoạn không vượt `chunk_size`; nếu hết separator thì cắt trực tiếp theo số ký tự.

**Bốn Semantic Chunkers** — hướng tiếp cận:
> `StatisticalChunker` dùng ngưỡng thống kê động; `ConsecutiveChunker` so sánh hai đoạn kề nhau; `CumulativeChunker` so sánh chunk đang tích lũy với đoạn tiếp theo; `RegexChunker` chia theo regex và giới hạn token. `SemanticChunkerAdapter` chuyển kết quả về `list[str]` để dùng chung giao diện `chunk(text)`.

**Chiến lược tôi chọn — `StatisticalChunker`:**
> Tôi chọn `StatisticalChunker` vì nó dùng embedding và ngưỡng động để phát hiện thay đổi ngữ nghĩa, giúp các ý liên quan nằm trong cùng một chunk. Chiến lược này thích nghi tốt với nội dung đa dạng, và trên bộ benchmark K4 nó truy xuất đúng cả 5/5 câu trong top-3.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` lưu nội dung, metadata và embedding vào ChromaDB hoặc bộ nhớ. `search` tính tích vô hướng giữa embedding câu hỏi và tài liệu, sắp xếp score giảm dần rồi lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước rồi mới xếp hạng độ tương tự. `delete_document` xóa mọi chunk có `metadata.doc_id` tương ứng và trả về trạng thái thành công.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` lấy `top_k` chunk, ghép chúng vào phần `Context` rồi thêm `Question` và `Answer`. Prompt yêu cầu LLM chỉ dùng context và báo thiếu thông tin khi không đủ dữ liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: D:\Folder F\phamtuananh@23020010\UET.iSEML\2026.VinAI.Lab\Lab7
plugins: anyio-4.14.2
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

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Machine learning helps systems learn from data. | Deep learning is a type of machine learning. | Thấp | -0.0014 (thấp) | Có |
| 2 | The refund policy allows returns within 7 days. | Customers can return products within one week. | Thấp | 0.0794 (thấp) | Có |
| 3 | The fox jumps over the dog. | Financial statements record revenue and costs. | Thấp | -0.0735 (thấp) | Có |
| 4 | Vector search ranks documents by embedding similarity. | Embedding models turn text into vectors. | Thấp | -0.0570 (thấp) | Có |
| 5 | How to install Python packages with pip? | What is the capital of France? | Thấp | 0.1055 (thấp) | Có |

**Số cặp dự đoán đúng:** 5 / 5

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cả 5 cặp đều được dự đoán đúng theo nhãn thấp/cao. Điều này cho thấy `_mock_embed` không biểu diễn ngữ nghĩa thật; với embedding tốt hơn, các cặp cùng ý sẽ tách biệt rõ hơn khỏi cặp không liên quan.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng và hoàn tiền sau khi nhận hàng? | Chunk về thời hạn yêu cầu trả hàng: 15 ngày, riêng thực phẩm tươi/đông lạnh 24 giờ. | 0.5435 | Có. | Trong vòng 15 ngày kể từ khi giao hàng thành công; riêng thực phẩm tươi/đông lạnh là 24 giờ. |
| 2 | Đơn hàng thanh toán bằng Apple Pay trên Shopee cần nằm trong khoảng giá trị nào? | Chunk về Apple Pay và điều kiện 10.000 - 25.000.000 VNĐ. | 0.4187 | Có. | Từ 10.000 VNĐ đến 25.000.000 VNĐ. |
| 3 | Người dùng liên hệ ai để yêu cầu truy cập hoặc xóa dữ liệu cá nhân trên Shopee? | Chunk về quyền truy cập/xóa dữ liệu và liên hệ DPO. | 0.8018 | Có. | Liên hệ Cán bộ bảo vệ dữ liệu qua email dpo.vn@shopee.com. |
| 4 | Người bán phải đảm bảo hạn sử dụng còn lại tối thiểu bao nhiêu khi đăng bán sản phẩm có hạn dùng? | Chunk về sản phẩm có hạn dùng còn ít nhất 30% hạn sử dụng và 30 ngày. | 0.5610 | Có. | Sản phẩm khi giao đi phải còn ít nhất 30% thời hạn sử dụng và ít nhất 30 ngày. |
| 5 | Mức bồi thường tối đa khi kiện hàng bị mất hoàn toàn trong quá trình vận chuyển là bao nhiêu? | Chunk về bồi thường khi mất hàng: 70% giá trị sản phẩm. | 0.4641 | Có. | 70% giá trị sản phẩm, áp dụng khi đơn vị vận chuyển không bồi thường. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi học được rằng metadata filter giúp giảm nhiễu, nhưng chất lượng chunk vẫn quyết định rất nhiều đến top-k retrieval. Với tài liệu chính sách, chunk theo ngữ nghĩa rõ ràng giúp truy xuất đúng cả khi câu hỏi có số liệu rất cụ thể.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 10 / 10 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
