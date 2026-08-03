# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đào Tùng Dương
**Nhóm:** [Tên nhóm]
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector chỉ về cùng một hướng gần như tương đồng trong không gian biểu diễn (embedding space). Điều này chỉ ra hai đoạn văn bản có sự tương đồng lớn về mặt ngữ nghĩa (semantic meaning) và ngữ cảnh, bất kể sự khác biệt về độ dài hoặc từ vựng sử dụng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi lại chiếc áo khoác này vì kích thước không vừa."
- Câu B: "Chiếc áo ấm này quá chật nên tôi cần hoàn trả để lấy cỡ khác."
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một ý định đổi/trả sản phẩm thời trang do kích thước không vừa, mặc dù từ vựng sử dụng khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả sản phẩm có hiệu lực trong vòng 30 ngày."
- Câu B: "Tổng thống vừa ký sắc lệnh mới về thương mại quốc tế."
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn khác nhau (chính sách đổi hàng của cửa hàng dịch vụ bán lẻ so với tin tức kinh tế vĩ mô quốc tế).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài của văn bản (độ dài vector), trong khi độ tương tự cosine chỉ tập trung vào góc giữa hai vector (hướng của ngữ nghĩa). Khi so sánh một câu truy vấn ngắn với một đoạn văn dài, độ tương tự cosine mang lại độ chính xác cao và ổn định hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk sẽ tăng lên (thành `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks). Việc tăng độ chồng chéo giúp hạn chế việc mất ngữ cảnh tại các điểm cắt (boundary) giữa các chunk kề nhau, hỗ trợ RAG Agent truy xuất thông tin đầy đủ và mạch lạc hơn. Đánh đổi lại là tăng chi phí tính toán, lưu trữ vector và số lượng token đầu vào của LLM.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng thư viện `re.split` với mẫu regex `(\. |! |\? |\.\n)` để phân rã văn bản tại ranh giới kết thúc câu mà vẫn giữ lại được dấu câu nguyên bản. Sau đó, làm sạch các câu bằng phương thức `.strip()` để loại bỏ khoảng trắng rỗng, rồi gom cụm tuần tự tối đa `max_sentences_per_chunk` câu nối với nhau bằng ký tự khoảng trắng để tạo thành một chunk hoàn chỉnh.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thiết kế một giải thuật đệ quy có lùi (backoff split) dựa trên thứ tự ưu tiên của danh sách `separators`. Ở mỗi lượt gọi đệ quy, nếu văn bản hiện tại nhỏ hơn `chunk_size`, nó đóng vai trò là điểm dừng (base case) trả về chính văn bản đó. Ngược lại, hàm chia nhỏ đoạn văn dựa trên separator hiện tại, chạy đệ quy sâu xuống cho các mảnh quá dài, sau đó gom các mảnh nhỏ liên tiếp lại với nhau bằng separator sao cho kích thước mỗi chunk sau gộp nằm trong giới hạn tối đa mà không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Đầu tiên, chuyển đổi nội dung của mỗi Document thành vector biểu diễn thông qua hàm nhúng `_embedding_fn`. Nếu có tích hợp thư viện `chromadb`, ta nạp chúng vào cơ sở dữ liệu Chroma; nếu không, ta lưu trữ trực tiếp trên danh sách lưu động ở RAM. Khi nhận yêu cầu tìm kiếm, truy vấn `query` được chuyển sang vector, sau đó tính tích vô hướng (dot product) hoặc truy vấn ChromaDB để tìm các chunk có điểm tương đồng lớn nhất, sắp xếp giảm dần và lấy ra top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Hàm lọc dữ liệu `search_with_filter` sử dụng kỹ thuật lọc thô trước (pre-filtering) để lọc ra các chunk thỏa mãn điều kiện khớp chính xác của `metadata_filter` trước khi tiến hành tính toán độ tương đồng cosine, giúp tối ưu hiệu năng. Hàm `delete_document` thực hiện việc loại bỏ các chunk lưu trữ có trường `metadata['doc_id'] == doc_id`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Thực hiện quy trình RAG chuẩn: Tìm kiếm và lấy ra `top_k` chunk văn bản liên quan mật thiết nhất từ `EmbeddingStore` làm ngữ cảnh (context). Nối các ngữ cảnh này lại cùng với câu hỏi của người dùng vào một prompt template được thiết kế sẵn để làm rõ câu hỏi, sau đó truyền prompt này vào hàm `llm_fn` để nhận được câu trả lời sinh ra từ mô hình.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
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

============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả này áp dụng cho tất cả khách hàng mua sắm trực tuyến. | Tất cả đơn hàng mua online đều được hưởng chính sách hoàn trả này. | cao | -0.0256 (Mock) | Không |
| 2 | Sản phẩm phải còn nguyên mác và chưa qua sử dụng. | Vui lòng giữ nguyên tem nhãn và không mặc thử sản phẩm. | cao | -0.0314 (Mock) | Không |
| 3 | Phương thức thanh toán bao gồm thẻ tín dụng và chuyển khoản ngân hàng. | Chúng tôi chấp nhận thanh toán qua thẻ ngân hàng hoặc chuyển khoản. | cao | -0.2675 (Mock) | Không |
| 4 | Đơn hàng sẽ được giao trong vòng 3 đến 5 ngày làm việc. | Chúng tôi không chấp nhận trả lại các mặt hàng đã giảm giá. | thấp | 0.0139 (Mock) | Đúng |
| 5 | Chính sách bảo mật thông tin khách hàng được cam kết tuyệt đối. | Hôm nay thời tiết Hà Nội rất đẹp và có nắng nhẹ. | thấp | 0.2512 (Mock) | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các cặp câu đồng nghĩa (Cặp 1, 2, 3) có điểm tương đồng rất thấp hoặc âm, trong khi cặp câu hoàn toàn không liên quan (Cặp 5) lại có điểm tương đối cao (0.2512). Điều này phản ánh rõ bản chất của `MockEmbedder`: nó chỉ tạo vector giả lập dựa trên hàm băm MD5 chuỗi ký tự nên hoàn toàn không hiểu ngữ nghĩa. Nhúng ngữ nghĩa thực sự (Semantic Embeddings) yêu cầu các mô hình đã qua huấn luyện (như ở Giai đoạn 2) để có thể ánh xạ các từ đồng nghĩa/cùng ngữ cảnh về gần nhau trong không gian biểu diễn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

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
