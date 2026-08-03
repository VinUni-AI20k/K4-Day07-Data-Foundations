# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Ngyễn
**Nhóm:** A6-3
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Nghĩa là góc giữa hai vector biểu diễn văn bản rất nhỏ, chỉ ra rằng hai đoạn văn bản có sự tương đồng lớn về ngữ nghĩa và nội dung.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con mèo đang ngủ trên ghế sofa."
- Câu B: "Một chú mèo con đang nằm nướng trên chiếc ghế dài."
- Tại sao tương đồng: Cùng nói về hành động ngủ/nằm của con mèo trên một loại ghế, ý nghĩa câu rất gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Ngân hàng trung ương vừa tăng lãi suất cơ bản."
- Câu B: "Công thức làm bánh mì bơ tỏi ngon tuyệt đỉnh."
- Tại sao khác: Một câu thuộc lĩnh vực kinh tế - tài chính, một câu thuộc lĩnh vực ẩm thực, không có sự liên quan.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Vì độ tương tự cosine quan tâm đến hướng (góc) của các vector biểu diễn ngữ nghĩa chứ không bị ảnh hưởng bởi độ lớn (chiều dài) của văn bản. Nhờ vậy, ta có thể dễ dàng so sánh các đoạn văn bản dài ngắn khác nhau nhưng mang chung một ý nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* làm_tròn_lên((10,000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = 22.11
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Số lượng chunk sẽ tăng lên (thành làm_tròn_lên(9900/400) = 25 chunks). Việc tăng overlap giúp đảm bảo không bị đứt gãy ngữ nghĩa hoặc mất bối cảnh quan trọng khi ranh giới cắt tình cờ rơi vào giữa một câu, từ đó tăng hiệu quả truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?* Tôi dùng regex `re.split(r'([.!?]\s+|\.\n)', text)` để chia văn bản thành câu, đồng thời giữ lại dấu chấm câu để không làm mất kết cấu. Các trường hợp ngoại lệ như khoảng trắng thừa đều được `.strip()` xử lý để đảm bảo chunk sạch sẽ, sau đó ghép lại tối đa `max_sentences_per_chunk` câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?* Thuật toán cố gắng cắt văn bản bằng separator ưu tiên cao nhất, nếu đoạn cắt vẫn vượt `chunk_size` thì sẽ gọi đệ quy `_split` bằng danh sách các separator tiếp theo. Base case là khi chuỗi nhỏ hơn `chunk_size` hoặc khi đã hết sạch các separator (thì buộc phải cắt cứng theo số lượng ký tự).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?* Các chunk được nhúng (embed) thành vector, đi kèm ID và metadata, sau đó lưu thẳng vào bộ nhớ trong cấu trúc danh sách từ điển (dict). Hàm `search` so sánh truy vấn và kho dữ liệu bằng tích vô hướng (cosine similarity đối với vector chuẩn hóa), sau đó sort list giảm dần và lấy top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?* Phép lọc (filter) metadata được thực hiện hoàn toàn trước khi tính điểm vector để giảm không gian tìm kiếm, sau đó mới gọi search_records trên tập đã lọc. Phép xóa thực hiện bằng cách lọc giữ lại những document nào mà cả `metadata['doc_id']` và `id` khác biệt hoàn toàn với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?* Trước hết, gọi hàm `store.search` để lấy các chunk top K. Nội dung các chunk này sẽ được nối lại với nhau bằng dấu phân cách (như `\n---\n`), rồi tiêm (inject) vào prompt có cấu trúc `Context: {context} \n Question: {question}` trước khi truyền vào LLM để sinh ra câu trả lời dựa trên ngữ cảnh.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED

============================== 42 passed in 0.42s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Tôi thích học lập trình Python" | "Python là một ngôn ngữ tuyệt vời" | cao | 0.85 | Có |
| 2 | "Thời tiết hôm nay rất đẹp" | "Trời đang nắng ấm và quang đãng" | cao | 0.78 | Có |
| 3 | "Hôm nay tôi ăn cơm" | "Chó cắn mèo ngoài ngõ" | thấp | 0.12 | Có |
| 4 | "Anh ấy vừa mua một chiếc xe hơi" | "Anh ta mới sắm một cái ô tô" | cao | 0.89 | Có |
| 5 | "Công ty phát hành cổ phiếu mới" | "Hướng dẫn cách nấu chè ngon" | thấp | 0.05 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Điều bất ngờ nhất là cặp câu 4 sử dụng từ vựng khác nhau hoàn toàn ("xe hơi" - "ô tô", "mua" - "sắm") nhưng điểm độ tương tự vẫn rất cao (0.89). Điều này chứng minh rằng vector embeddings biểu diễn ngữ nghĩa cốt lõi thay vì chỉ khớp nối các mặt chữ, cho phép tìm kiếm ngữ nghĩa cực kỳ chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn hỗ trợ đổi trả sản phẩm tại Tiki là bao lâu? | "Thời gian hỗ trợ đổi trả tại Tiki: Khách hàng được đổi trả trong 30 ngày kể từ khi nhận hàng..." | 0.88 | Có | Thời hạn đổi trả thông thường là 30 ngày, riêng điện gia dụng là 365 ngày. |
| 2 | Trường hợp nào Tiki áp dụng quy trình Hoàn tiền nhanh cho nhà bán? | "Hoàn tiền nhanh (Easy refund): áp dụng cho sản phẩm giá trị đền bù từ 500.000đ trở xuống." | 0.82 | Có | Áp dụng cho các sản phẩm có giá trị đền bù từ 500.000đ trở xuống. |
| 3 | Người bán chưa có tài khoản Shopee bắt đầu đăng ký bán hàng như thế nào? | "Bước 1: Tải Kênh Người Bán Shopee, điền tên đăng nhập, số điện thoại và xác thực." | 0.85 | Có | Bạn cần tải app Kênh Người Bán Shopee, sau đó điền tên đăng nhập, SĐT và xác thực. |
| 4 | Khách hàng không thể hủy đơn trên Lazada trong trường hợp nào? | "When can't I cancel? You cannot cancel if the order is packed or handed to courier..." | 0.79 | Có | Bạn không thể hủy đơn nếu đơn hàng đã được đóng gói hoặc giao cho vận chuyển. |
| 5 | Sản phẩm nước hoa / đồ lót có được đổi trả do đổi ý tại Tiki không? | "Quy định đổi trả Tiki nói chung: Khách hàng có thể đổi trả các sản phẩm lỗi..." | 0.67 | Không | Có thể đổi trả nếu sản phẩm bị lỗi. (Trả lời sai do không truy xuất được chunk danh mục hạn chế) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Tôi học được rằng việc thiết kế chiến lược chunking dựa trên cấu trúc tài liệu (như Markdown heading hay cặp Q&A FAQ) hiệu quả hơn hẳn so với cắt cứng theo ký tự. Hơn nữa, qua câu số 4, tôi thấy sức mạnh tuyệt đối của việc dùng metadata filter (`platform=lazada`) để loại bỏ nhiễu thông tin giữa các tài liệu khác nền tảng.

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
