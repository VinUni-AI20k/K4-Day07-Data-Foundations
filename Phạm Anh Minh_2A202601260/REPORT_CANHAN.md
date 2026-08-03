# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Nghĩa là 2 thông tin có ý nghĩa gần giống nhau.*

**Ví dụ có độ tương tự CAO:**
- Câu A: Chiếc xe này tiêu hao rất ít nhiên liệu.
- Câu B: Mẫu xe này rất tiết kiệm xăng.
- Tại sao tương đồng: Hai câu này đều diễn tả một đặc tính về ngữ nghĩa của chiếc xe - sử dụng ít nhiên liệu.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Con mèo đang ngủ trên ghế.
- Câu B: Chiếc ô tô đang chạy trên đường.
- Tại sao khác: 2 câu không liên quan đến nhau do đó tạo ra sự khác biệt về mặt ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Vì cosine similarity rất phù hợp với embedding, nơi hướng của vector (ý nghĩa) quan trọng hơn độ lớn.*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính: Do mỗi chunk chồng lấn 50 ký tự, nên mỗi lần dịch chuyển 500-50 = 450 ký tự. Số chunk sẽ là (10000-500)/450 + 1 =23*
> *Đáp án:23*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Độ chồng chéo tăng lên 100 thì cần lưu vào 25 chunk, làm thế sẽ tránh embedding của từng chunk sẽ thiếu ngữ cảnh.*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Dùng regex `(?<=[.!?])\s+|(?<=\.)\n` để tách câu: lookbehind cho dấu `.`/`!`/`?` theo sau bởi khoảng trắng, hoặc dấu `.` theo sau bởi xuống dòng — nhờ lookbehind nên dấu câu vẫn được giữ ở cuối mỗi câu thay vì bị regex nuốt mất. Sau khi tách, gom từng nhóm tối đa `max_sentences_per_chunk` câu liên tiếp, nối lại bằng khoảng trắng rồi `strip()`. Trường hợp ngoại lệ: chuỗi rỗng trả về `[]`, và câu cuối dù không có dấu kết thúc câu vẫn được giữ nguyên nội dung.*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Thuật toán thử tách văn bản theo thứ tự ưu tiên các dấu phân cách `["\n\n", "\n", ". ", " ", ""]`: dùng dấu đầu tiên để tách thành các đoạn con, đoạn nào vẫn dài hơn `chunk_size` thì gọi đệ quy `_split` trên đoạn đó với phần dấu phân cách còn lại. **Base case:** đoạn đã đủ ngắn (≤ `chunk_size`), hoặc đã dùng hết danh sách dấu phân cách — khi đó dấu cuối `""` sẽ cắt cứng theo ký tự để đảm bảo luôn có kết quả.*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Store chạy ở chế độ in-memory: mỗi document được embed qua `self._embedding_fn` rồi lưu thành 1 record (`id`, `content`, `metadata`, `embedding`) trong `self._store`. Khi `search`, embed câu query rồi dùng `compute_similarity`  để so với từng vector đã lưu, sắp xếp giảm dần theo score và cắt lấy `top_k` kết quả đầu.*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Lọc trước: `search_with_filter` chỉ giữ lại các record có toàn bộ cặp key/value trong `metadata_filter` khớp với `metadata` của record, rồi mới chạy đúng thuật toán similarity của `search` trên tập con đã lọc — lọc trước giúp không phải tính similarity với các chunk chắc chắn không liên quan. `delete_document` duyệt `self._store` và loại bỏ mọi record có `metadata['doc_id'] == doc_id`, trả về `True` nếu xoá được ít nhất 1 record, `False` nếu không tìm thấy.*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *`answer` gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, ghép nội dung các chunk đó thành một khối ngữ cảnh có đánh số, rồi chèn vào prompt dạng "Dựa trên ngữ cảnh sau, trả lời câu hỏi: [ngữ cảnh] ... Câu hỏi: [question]". Cuối cùng gọi `self._llm_fn(prompt)` và trả thẳng kết quả về — agent không tự sinh văn bản, chỉ đóng vai trò ghép retrieval + LLM theo đúng pattern RAG.*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python3 -m pytest tests/ -v
========================================== test session starts ==========================================
platform darwin -- Python 3.10.18, pytest-9.1.1, pluggy-1.6.0 -- /Users/phamminh/Desktop/phamminh/AIThucChien/K4-Day07-Data-Foundations/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/phamminh/Desktop/phamminh/AIThucChien/K4-Day07-Data-Foundations
plugins: anyio-4.14.2
collected 42 items                                                                                      

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED             [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                      [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED               [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                     [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED     [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED           [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED            [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED          [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                            [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED            [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                       [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                   [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                             [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED    [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED        [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED  [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED        [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                            [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED              [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                      [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED           [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED             [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED              [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                       [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                      [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                 [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED             [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED        [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED            [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                  [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED            [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED       [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED      [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED     [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

========================================== 42 passed in 0.05s ===========================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|--------|--------|----------|--------------:|:-----:|
| 1 | Tôi muốn đặt vé máy bay đi Hà Nội. | Tôi cần mua vé máy bay đến Hà Nội. | Cao | 0.967 | ✅ |
| 2 | Hôm nay trời rất nóng. | Thời tiết hôm nay có nhiệt độ cao. | Cao | 0.755 | ✅ |
| 3 | Tôi muốn đặt pizza. | Tôi muốn hủy pizza. | Thấp | 0.742 | ❌ |
| 4 | Con mèo đang ngủ trên ghế. | Chiếc ô tô đang chạy trên đường. | Thấp | 0.071 | ✅ |
| 5 | Máy tính này chạy rất nhanh. | Laptop này có hiệu năng cao. | Cao | 0.719 | ✅ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Điểm 0.742 ở câu số 3 cho thấy mô hình đánh giá hai câu có nhiều điểm tương đồng về ngữ cảnh, mặc dù ý định của chúng trái ngược nhau.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi có bao nhiêu ngày để yêu cầu trả hàng kể từ khi đơn hàng giao thành công? | "Người Mua có thể gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 (mười lăm) ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công" (doc: `chinh-sach-tra-hang-hoan-tien`) | 0.702 | ✅ Có | Nêu lại đúng ý ngữ cảnh: được gửi yêu cầu trả hàng/hoàn tiền trong vòng 15 ngày kể từ khi giao hàng thành công. |
| 2 | Thời gian xử lý bảo hành dự kiến là bao lâu? | "a. Tối đa 10 ngày làm việc kể từ thời điểm nhận được đầy đủ bằng chứng hợp lệ..." (doc: `chinh-sach-van-chuyen`, sai chủ đề) | 0.633 | ❌ Không (nhưng top-3 có chunk đúng thuộc `chinh-sach-bao-hanh`) | Trả lời lệch chủ đề vì bám theo ngữ cảnh sai — nêu thời hạn xử lý khiếu nại vận chuyển (10 ngày) thay vì thời gian xử lý bảo hành. |
| 3 | Đơn hàng nào không hỗ trợ vận chuyển? | "Nếu một trong các chiều (dài, rộng, cao) vượt quá giới hạn cho phép, đơn vị vận chuyển sẽ từ chối hỗ trợ vận chuyển." (doc: `chinh-sach-van-chuyen`) | 0.672 | ✅ Có | Trả lời đúng: đơn hàng có kích thước (dài/rộng/cao) vượt giới hạn cho phép sẽ bị từ chối vận chuyển. |
| 4 | Lịch sử trò chuyện với chăm sóc khách hàng lưu trữ tối đa bao lâu? | "Trường hợp quý khách gửi sản phẩm bảo hành về Shopee, chúng tôi sẽ gửi thông báo xác nhận..." (doc: `chinh-sach-bao-hanh`, sai chủ đề) | 0.615 | ❌ Không (nhưng top-3 có chunk đúng thuộc `lien-he-cham-soc-khach-hang`) | Trả lời lệch chủ đề vì bám theo ngữ cảnh sai — nói về xác nhận nhận sản phẩm bảo hành thay vì thời hạn lưu trữ lịch sử chat CSKH. |
| 5 | Người bán vi phạm chính sách sẽ bị áp dụng những chế tài nào? | "Việc vi phạm Chính Sách Cấm/Hạn Chế Sản Phẩm có thể dẫn đến việc Người Bán phải chịu một loạt các chế tài..." (doc: `chinh-sach-cam-han-che-san-pham`) | 0.760 | ✅ Có | Trả lời đúng: liệt kê ngữ cảnh về các chế tài áp dụng khi Người Bán vi phạm chính sách cấm/hạn chế sản phẩm. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Điều hay nhất tôi học được là đổi embedding model sang `qwen2.5-coder:1.5b`  giúp điểm retrieve cao hơn hẳn so với embedding mặc định, cho thấy chất lượng model embedding ảnh hưởng trực tiếp đến độ chính xác truy xuất chứ không chỉ nằm ở chiến lược chunking.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5/ 5 |
| Hướng tiếp cận của tôi (My Approach) | 8 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 27/ 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 7/ 10 |
| **Tổng phần cá nhân** | **51/ 60** |
