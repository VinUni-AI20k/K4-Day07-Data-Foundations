# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phạm Hà Anh
**Nhóm:** TeamB
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding của văn bản hướng về cùng một hướng trong không gian đa chiều, thể hiện sự tương đồng lớn về ngữ nghĩa (semantic similarity) giữa hai văn bản đó mà không phụ thuộc vào độ dài của chúng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Làm thế nào để tôi có thể đổi trả hàng hóa đã mua trên sàn?
- Câu B: Quy trình hoàn trả sản phẩm và nhận lại tiền như thế nào?
- Tại sao tương đồng: Dù sử dụng các từ ngữ khác nhau ("đổi trả hàng hóa" vs "hoàn trả sản phẩm", "mua trên sàn" vs "nhận lại tiền"), cả hai câu đều biểu đạt cùng một ý định của người dùng (user intent) là hoàn trả hàng và nhận lại tiền.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Chính sách bảo mật thông tin khách hàng của cửa hàng là gì?
- Câu B: Thời gian giao hàng tiêu chuẩn cho khu vực ngoại thành là bao lâu?
- Tại sao khác: Hai câu đề cập đến hai khía cạnh nghiệp vụ hoàn toàn khác nhau trong thương mại điện tử (Quyền riêng tư/bảo mật thông tin khách hàng vs Logistics/thời gian giao nhận).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài của văn bản (văn bản dài hơn sẽ có độ lớn vector lớn hơn, kéo theo khoảng cách Euclid lớn ngay cả khi có cùng ngữ nghĩa). Độ tương tự cosine đo góc giữa hai vector nên đã chuẩn hóa độ lớn vector về 1, giúp đo lường sự tương đồng ngữ nghĩa khách quan hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
> `số lượng chunk = làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11)`
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Phép tính:* `làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25` chunks.
> Số lượng chunk tăng từ 23 lên 25. Ta muốn tăng độ chồng chéo để bảo toàn ngữ cảnh liên tục giữa các chunk liền kề, tránh việc thông tin hoặc câu văn quan trọng bị chia cắt làm đôi tại ranh giới phân tách chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng `re.split(r"(\. |\! |\? |\.\n)", text)` để tách văn bản thành câu nhưng vẫn giữ lại các dấu câu và khoảng trắng phân cách. Sau đó gộp cặp các phần tử text và dấu câu phân cách lại, dùng `.strip()` để làm sạch. Cuối cùng, gom nhóm các câu này thành từng khối với số lượng tối đa là `max_sentences_per_chunk` và nối lại bằng khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy kiểm tra nếu chiều dài đoạn văn bản nhỏ hơn `chunk_size` hoặc không còn dấu phân cách nào thì trả về đoạn văn bản đó làm base case. Với văn bản dài, thuật toán dùng dấu phân cách có độ ưu tiên cao nhất trong danh sách `["\n\n", "\n", ". ", " ", ""]` để tách ra, đệ quy chia nhỏ các đoạn còn quá lớn, rồi gộp các đoạn nhỏ lại sao cho tổng độ dài của mỗi chunk tối ưu nhất và không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> - `add_documents`: Vector hóa văn bản bằng cách gọi hàm `_embedding_fn` để nhận vector embedding dạng danh sách float. Trong in-memory store, mỗi document được biểu diễn bằng một dict chứa `id`, `content`, `metadata`, `embedding` rồi thêm vào list `self._store`. Với ChromaDB, ta gọi directement phương thức `self._collection.add`.
> - `search`: Vector hóa câu truy vấn bằng `_embedding_fn`, sau đó duyệt qua toàn bộ các tài liệu trong kho lưu trữ để tính cosine similarity giữa vector truy vấn và vector tài liệu bằng hàm `compute_similarity`, sắp xếp giảm dần theo điểm số similarity và lấy ra top_k tài liệu có điểm số cao nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> - `search_with_filter`: Thực hiện lọc trước (pre-filtering) bằng cách duyệt qua `self._store` và chỉ giữ lại những bản ghi có metadata thỏa mãn tất cả các cặp khóa-giá trị trong `metadata_filter`. Sau đó chạy tìm kiếm tương đồng trên danh sách bản ghi đã lọc. Với ChromaDB, truyền trực tiếp `metadata_filter` vào tham số `where`.
> - `delete_document`: Trong in-memory store, loại bỏ toàn bộ các bản ghi mà `metadata['doc_id'] == doc_id` hoặc trường `id` của bản ghi trùng với `doc_id` (hoặc là tiền tố trước dấu `::`). Trong ChromaDB, thực hiện xóa bằng `collection.delete` với điều kiện lọc theo `doc_id` và xóa theo `ids` trực tiếp để tương thích tốt nhất với cả document thô và chunk document.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Truy xuất top-k chunks liên quan nhất từ `store` thông qua phương thức `search`, ghép nội dung các chunks này lại thành một khối văn bản làm ngữ cảnh (context). Đưa ngữ cảnh này vào một prompt mẫu được thiết kế sẵn để làm thông tin nền kèm theo câu hỏi của người dùng, rồi truyền cho hàm gọi LLM (`llm_fn`) để sinh ra câu trả lời chính xác dựa trên tài liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- D:\Vin_AI\Day07_2A202601212_TruongQuangMinh\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Vin_AI\Day07_2A202601212_TruongQuangMinh
collecting ... collected 42 items

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

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Làm thế nào để trả lại sản phẩm? | Làm thế nào để đổi trả hàng đã mua? | cao | 0.0413 | Sai |
| 2 | Quy trình thanh toán bằng thẻ tín dụng như thế nào? | Tôi có thể thanh toán đơn hàng bằng thẻ visa không? | cao | 0.0099 | Sai |
| 3 | Tôi muốn hủy tài khoản người bán. | Thời gian giao hàng dự kiến là bao lâu? | thấp | -0.1087 | Đúng |
| 4 | Người mua được phép đổi trả hàng trong vòng 7 ngày. | Người bán không được phép đổi trả hàng trong vòng 7 ngày. | thấp/vừa | -0.0053 | Đúng |
| 5 | Chính sách hoàn tiền của sàn là gì? | What is the refund policy of the platform? | cao | -0.1133 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các câu có ý nghĩa cực kỳ tương đồng (Cặp 1 và Cặp 5) lại nhận điểm số cosine gần như bằng 0 hoặc âm. Điều này xảy ra vì MockEmbedder băm văn bản ngẫu nhiên dựa trên các ký tự thô chứ không hề có khả năng biểu diễn ngữ nghĩa. Embeddings thực thụ trong AI (như sentence-transformers) sẽ biểu diễn ngữ nghĩa của các từ tương đồng gần nhau trong không gian đa chiều, giúp các câu đồng nghĩa nhận điểm số rất cao bất kể sự khác biệt về ngôn ngữ hay từ vựng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có được trả hàng hoàn tiền khi đổi ý không? | ask for a price reduction or refund. Remember that you always have a 2-year minimum guarantee at no cost... | 0.3952 | No | Tôi không biết. Thông tin trong ngữ cảnh được cung cấp không đề cập... |
| 2 | Người bán chịu trách nhiệm gì khi bán sản phẩm bị cấm trên Shopee? | cordings, video recordings or software which the customer unsealed - newspapers or magazines (but... | 0.4215 | No | Tôi không biết. Thông tin này không được đề cập trong ngữ cảnh bạn... |
| 3 | Chính sách bảo hành cho sản phẩm mua tại Shopee như thế nào? | vận chuyển có điều kiện, quy định về đóng gói hàng hóa, các quyền, nghĩa vụ của các Bên liên quan đến việc vận chuyển... | 0.3062 | No | Xin lỗi, tôi không tìm thấy thông tin về chính sách bảo hành... |
| 4 | Shopee thu thập dữ liệu cá nhân nào từ người dùng? | ủa chúng tôi hoặc hoạt động của Shopee để ngăn chặn hoặc điều tra bất kỳ hoạt động gian lận thực tế hoặc bị nghi ngờ... | 0.4637 | Yes | Xin lỗi, thông tin bạn cung cấp trong ngữ cảnh trên không đề cập... |
| 5 | Thời hạn giao hàng quy định dành cho người bán là bao lâu? | hopee và cho Người Dùng chân chính. 2. Tổn hại Đối Với Hành Vi Gian Lận Trên của Người Bán: Hành Vi Gian Lận Trên... | 0.2936 | No | Tôi không biết. Nội dung được cung cấp không đề cập đến... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 1 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua buổi thảo luận và demo, tôi học được rằng việc thiết kế cấu trúc siêu dữ liệu (metadata schema) có vai trò vô cùng lớn trong việc lọc thông tin, giúp giảm tải đáng kể không gian tìm kiếm vector và tăng độ chính xác. Đồng thời, do Mock Embedder sinh vector ngẫu nhiên dựa trên hash chuỗi nên hiệu quả truy xuất ngữ nghĩa thực tế cực kỳ thấp, đòi hỏi nhóm phải cấu hình Local Embedder thật (EMBEDDING_PROVIDER=local) để có chất lượng tìm kiếm chuẩn xác.

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
