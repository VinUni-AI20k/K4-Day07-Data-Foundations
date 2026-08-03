# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Dương Văn Duy
**Nhóm:** A6 - Tam Thái Tử
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần giống nhau. Trong xử lý văn bản, điều này thường cho thấy hai câu hoặc hai đoạn văn có nội dung và ý nghĩa ngữ nghĩa tương đồng, ngay cả khi chúng không dùng chính xác cùng một từ ngữ.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền khi sản phẩm nhận được bị lỗi.
- Câu B: Người mua được phép nhận lại tiền nếu hàng hóa giao đến có khiếm khuyết.
- Tại sao tương đồng: Cả hai câu đều diễn đạt quyền được hoàn tiền của người mua khi sản phẩm có lỗi, chỉ khác nhau về cách dùng từ.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Khách hàng có thể yêu cầu hoàn tiền khi sản phẩm nhận được bị lỗi.
- Câu B: Cây xanh hấp thụ khí carbon dioxide.
- Tại sao khác: Hai câu thuộc hai chủ đề không liên quan; câu đầu nói về chính sách hoàn tiền trong thương mại điện tử, còn câu sau nói về quá trình sinh học của thực vật.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào góc giữa hai vector, tức là hướng biểu diễn ngữ nghĩa, nên ít bị ảnh hưởng bởi độ lớn của vector. Trong khi đó, khoảng cách Euclid phụ thuộc cả hướng và độ lớn, vì vậy có thể đánh giá hai văn bản cùng ý nghĩa là cách xa nhau chỉ do vector của chúng có độ lớn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.11...) = 23`.
>
> Đáp án: Tài liệu được chia thành **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số chunk là `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = ceil(24.75) = 25`, tức tăng từ 23 lên **25 chunks**. Overlap lớn hơn giúp giữ lại ngữ cảnh ở ranh giới giữa các chunk, hạn chế việc một ý quan trọng bị chia tách và có thể cải thiện kết quả truy xuất; đổi lại, nó làm tăng nội dung trùng lặp, chi phí embedding và dung lượng lưu trữ.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách câu nhưng vẫn giữ lại dấu kết thúc, sau đó gom tối đa `max_sentences_per_chunk` câu vào mỗi chunk. Hàm loại phần rỗng và trả về danh sách rỗng nếu đầu vào không có nội dung.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi chia văn bản theo thứ tự `"\n\n"`, `"\n"`, `". "`, `" "` và tiếp tục đệ quy với dấu phân cách kế tiếp nếu đoạn vẫn quá dài. Base case là đoạn không vượt `chunk_size`; nếu hết dấu phân cách thì cắt cứng theo số ký tự.

### Các hàm hỗ trợ tính toán và so sánh

**`compute_similarity` + `ChunkingStrategyComparator.compare`** — hướng tiếp cận:
> `compute_similarity` tính cosine từ tích vô hướng và độ lớn hai vector, đồng thời trả về `0.0` nếu có vector không để tránh chia cho 0. `compare` chạy ba chiến lược fixed-size, sentence và recursive trên cùng văn bản rồi trả về số chunk, độ dài trung bình và danh sách chunk để đối chiếu.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` nhúng mỗi tài liệu rồi lưu ID, nội dung, metadata và vector vào ChromaDB hoặc `_store` trong bộ nhớ. `search` nhúng truy vấn, tính tích vô hướng với các vector tài liệu, sắp xếp điểm giảm dần và trả về tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc các record khớp metadata trước rồi mới tính điểm và xếp hạng. `delete_document` xóa mọi chunk có `metadata["doc_id"]` tương ứng và trả về trạng thái cho biết có xóa được dữ liệu hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` lấy `top_k` chunk liên quan từ store rồi ghép chúng vào phần `Context` cùng câu hỏi trong prompt. Prompt yêu cầu mô hình chỉ dựa trên ngữ cảnh và nói không biết khi thiếu thông tin, sau đó được truyền cho `llm_fn` để tạo câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform win32 -- Python 3.11.9, pytest-8.4.2
collected 42 items

============================= 42 passed in 0.49s =============================
```

============================= test session starts ==============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\ADMIN\Downloads\LAB - Thực chiến AI\LAB DAY 7\K4-DAY07-DATA-FOUNDATION-TAM_THAI_TU\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\ADMIN\Downloads\LAB - Thực chiến AI\LAB DAY 7\K4-DAY07-DATA-FOUNDATION-TAM_THAI_TU
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
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED    [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED     [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED    [ 45%]
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

============================== 42 passed in 0.96s ==============================

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi trả sản phẩm bị lỗi trong vòng bảy ngày. | Người mua được phép trả lại hàng có khiếm khuyết trong thời hạn bảy ngày. | Cao | 0.547105 | Có |
| 2 | Đơn hàng sẽ được giao đến khách hàng trong ba đến năm ngày làm việc. | Thời gian vận chuyển dự kiến là từ ba đến năm ngày làm việc. | Cao | 0.518572 | Có |
| 3 | Người bán phải cung cấp thông tin sản phẩm chính xác. | Người bán không cần cung cấp thông tin sản phẩm chính xác. | Thấp | 0.920975 | Không |
| 4 | Khách hàng được hoàn tiền khi sản phẩm bị lỗi. | Cây xanh tạo ra oxy trong quá trình quang hợp. | Thấp | 0.385046 | Có |
| 5 | Nền tảng phải bảo vệ dữ liệu cá nhân của khách hàng. | Thông tin riêng tư của người mua cần được bảo mật. | Cao | 0.458293 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 3 bất ngờ nhất vì hai câu trái nghĩa do từ “không”, nhưng lại có điểm cao nhất là 0.920975. Điều này cho thấy embeddings nhận diện rất mạnh chủ đề và các từ ngữ chung, nhưng có thể chưa phản ánh tốt quan hệ phủ định hoặc mâu thuẫn logic. Vì vậy, điểm tương đồng cao chỉ cho biết hai câu gần nhau về ngữ nghĩa tổng quát, không bảo đảm nội dung của chúng hoàn toàn đồng ý với nhau.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

**Chiến lược cá nhân:** `RecursiveChunker(chunk_size=500)`, embedding `text-embedding-3-small`, chạy trên 10 tài liệu thật (401 chunks). Câu 3 áp dụng `metadata_filter={"customer_role": "seller"}`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Đổi sản phẩm Apple bị lỗi thì phải gửi lại trong bao nhiêu ngày và cần kèm theo gì? | Sản phẩm đủ điều kiện phải gửi trong 14 ngày, kèm biên lai/biên nhận quà tặng và bao bì gốc. | 0.772094 | Có | Chưa đầy đủ: Agent nêu đúng giấy tờ và bao bì nhưng không xác định được thời hạn 14 ngày. |
| 2 | Phát hiện giao dịch trái phép trên Google Play thì phải báo cáo trong thời hạn bao lâu? | Khoản phí trái phép phải được báo cáo trong vòng 120 ngày từ ngày giao dịch. | 0.694644 | Có | Trong vòng 120 ngày kể từ ngày giao dịch. |
| 3 | Quy định về thanh toán áp dụng cho tôi là gì? | Sau khi lọc vai trò `seller`, top-1 nêu nhà phát triển phải dùng hệ thống thanh toán Google Play. | 0.542882 | Có | Phải dùng hệ thống thanh toán Google Play, trừ các chương trình/ngoại lệ đủ điều kiện. |
| 4 | Hủy đơn hàng sau khi đã chuẩn bị vận chuyển hoặc giao hàng thất bại nhiều lần thì bị tính phí gì? | Hủy sau khi chuẩn bị vận chuyển hoặc đã vận chuyển sẽ chịu phí hoàn kho 20%. | 0.695108 | Có | Bị tính phí hoàn kho 20%. |
| 5 | Tạm dừng gói thuê bao trên Google Play được tối đa bao lâu? | Gói tạm dừng từ cuối kỳ hiện tại, thời gian từ 1 tuần đến 3 tháng. | 0.680637 | Có | Tối đa 3 tháng. |

**So sánh metadata filter ở câu 3:** Khi không lọc, top-3 lần lượt thuộc các tài liệu dành cho `buyer` (`gplay-phuong-thuc-thanh-toan` hai kết quả và `apple-vn-dieu-khoan-ban-hang`), nên không có chunk chứa gold answer dành cho người bán. Khi lọc `customer_role="seller"`, `gplay-npt-thanh-toan` lên top-1 với score `0.542768` và cả ba kết quả đầu đều thuộc đúng tài liệu này; bộ lọc vì vậy cải thiện rõ độ chính xác theo vai trò.

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Điều hữu ích nhất tôi rút ra khi so sánh các hướng tiếp cận là không có một chiến lược chunking phù hợp cho mọi loại tài liệu; cần đánh giá trên cùng corpus và cùng bộ câu hỏi mới có thể kết luận công bằng. Metadata filter cũng rất quan trọng với câu hỏi mơ hồ về vai trò, còn kết quả câu 1 cho thấy retrieval đúng chưa bảo đảm Agent sẽ sử dụng đầy đủ thông tin trong context.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 4 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 8 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 9 / 10 |
| **Tổng phần cá nhân** | **55 / 60** |
