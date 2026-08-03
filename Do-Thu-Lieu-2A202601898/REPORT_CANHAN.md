# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Đỗ Thu Liễu]
**Nhóm:** [B7]
**Ngày:** [3/8/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> *Hai đoạn văn bản có độ tương tự cosine cao nghĩa là các vector embedding của chúng gần cùng hướng, thể hiện nội dung hoặc ý nghĩa của chúng rất giống nhau.*

**Ví dụ có độ tương tự CAO:**

- Câu A: Hôm nay trời rất nóng
- Câu B: Thời tiết hôm nay khá oi bức.
- Tại sao tương đồng: Cả hai câu đều nói về thời tiết nóng trong ngày hôm nay nên có ý nghĩa gần giống nhau.

**Ví dụ có độ tương tự THẤP:**

- Câu A: Tôi đang học lập trình Python.
- Câu B: Con mèo đang ngủ trên ghế.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn không liên quan (lập trình vs. con vật), không chia sẻ từ vựng hay ngữ cảnh nào nên vector embedding sẽ gần như vuông góc/khác hướng nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Cosine similarity đo mức độ giống nhau về hướng của các vector nên phản ánh tốt sự tương đồng ngữ nghĩa. Euclidean distance bị ảnh hưởng bởi độ lớn của vector, trong khi độ lớn không phải lúc nào cũng quan trọng đối với text embeddings

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> *Trình bày phép tính:
> `ceil((10000-50)/(500-50))` = `ceil(9950/450)` = `23`
> *Đáp án: **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

> *Khi overlap tăng lên 100, bước nhảy giảm còn 400 nên số lượng chunk sẽ tăng lên. Độ chồng chéo lớn hơn giúp giữ được ngữ cảnh giữa các chunk, giảm nguy cơ mất thông tin ở ranh giới khi truy xuất hoặc tạo embedding*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

> Tôi dùng regex `(?<=[.!?])\s+` để tách câu — tách tại vị trí ngay sau `.`, `!` hoặc `?` và theo sau bởi khoảng trắng (bao gồm cả `\n`), khớp với cả 4 dạng ranh giới câu (". ", "! ", "? ", ".\n"). Sau khi tách, tôi lọc bỏ chuỗi rỗng, `strip()` từng câu rồi gộp từng nhóm tối đa `max_sentences_per_chunk` câu lại thành một chunk bằng `" ".join(...)`. Edge case xử lý: văn bản rỗng trả về `[]`, và văn bản không có dấu câu vẫn được coi là 1 câu duy nhất.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

> Thuật toán thử lần lượt từng dấu phân tách theo thứ tự ưu tiên (`"\n\n"` → `"\n"` → `". "` → `" "` → `""`): tách văn bản theo separator hiện tại rồi gộp tham lam (greedy) các phần lại thành từng chunk sao cho không vượt quá `chunk_size`; nếu một phần vẫn lớn hơn `chunk_size` sau khi tách, `_split` gọi đệ quy chính nó với danh sách separator còn lại (bỏ separator vừa dùng). Base case gồm 2 trường hợp: (1) đoạn văn bản hiện tại đã nhỏ hơn hoặc bằng `chunk_size` → trả về nguyên đoạn, hoặc (2) hết separator để thử → cắt cứng theo `chunk_size` ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

> Tôi lưu trữ danh sách văn bản, metadata và embedding tương ứng trong bộ nhớ. Khi thêm tài liệu, embedding được tạo trước rồi lưu cùng dữ liệu. Khi tìm kiếm, tôi tạo embedding cho câu truy vấn và tính cosine similarity giữa embedding truy vấn với tất cả embedding đã lưu, sau đó sắp xếp theo độ tương tự giảm dần.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

> Tôi lọc trước: `search_with_filter` duyệt `self._store` giữ lại các record có `metadata.get(key) == value` cho mọi cặp key/value trong `metadata_filter`, rồi mới chạy cosine similarity trên tập con đã lọc — giúp giảm số lượng cần tính và tránh trả về kết quả sai chủ đề. `delete_document` xóa bằng cách so khớp `metadata["doc_id"] == doc_id` (mỗi record luôn có `doc_id` do `_make_record` tự gán mặc định bằng `doc.id` nếu Document gốc không khai báo metadata), giữ lại các record còn lại và trả về `True`/`False` tùy có xóa được gì không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

> Prompt gồm 2 phần: khối "Context" (nối các `content` của top-k chunk truy xuất được từ `store.search`, cách nhau bằng dòng trống) và khối "Question" là câu hỏi gốc, kèm chỉ dẫn "chỉ trả lời dựa trên ngữ cảnh trên". Ngữ cảnh được đưa vào bằng cách chèn trực tiếp (string interpolation) trước khi gọi `llm_fn(prompt)`, giúp câu trả lời bám vào tài liệu truy xuất được (RAG) thay vì chỉ dựa vào kiến thức sẵn có của mô hình.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\CODEVIN\Day7\K4-Day07-Data-Foundations
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

| Cặp | Câu A                                             | Câu B                                                                         | Dự đoán | Điểm thực tế | Đúng? |
| ---- | -------------------------------------------------- | ------------------------------------------------------------------------------ | ---------- | ---------------- | ------- |
| 1    | "Tôi thích ăn phở bò vào buổi sáng."       | "Phở bò là món ăn tôi thích vào buổi sáng." (diễn đạt lại)       | cao        | -0.002           | Sai     |
| 2    | "Con mèo đang ngủ trên ghế sofa."             | "Con chó đang chạy ngoài sân." (khác chủ thể)                          | thấp      | 0.083            | Sai     |
| 3    | "Máy tính xách tay này có pin rất bền."     | "Chiếc laptop này dùng pin được rất lâu." (đồng nghĩa)              | cao        | -0.041           | Sai     |
| 4    | "Hôm nay trời mưa rất to."                     | "Giá cổ phiếu hôm nay tăng mạnh." (chủ đề khác hẳn)                 | thấp      | -0.096           | Đúng  |
| 5    | "Chính sách đổi trả áp dụng trong 7 ngày." | "Người mua được đổi trả hàng trong vòng 7 ngày." (diễn đạt lại) | cao        | 0.307            | Đúng  |

> Đo bằng `compute_similarity(_mock_embed(a), _mock_embed(b))` (`_mock_embed` là backend mặc định của lab).

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là cặp 1 và cặp 3: hai câu gần như đồng nghĩa 100% lại có điểm gần 0 hoặc âm, thấp hơn cả cặp 2 vốn không liên quan gì (mèo/chó). Điều này cho thấy điểm số chỉ có ý nghĩa khi *bản thân embedding* được huấn luyện để nắm bắt ngữ nghĩa — `_mock_embed` chỉ băm (hash MD5) chuỗi ký tự thành vector giả ngẫu nhiên nên công thức cosine similarity vẫn đúng về toán học nhưng vector đầu vào không mang thông tin ngữ nghĩa gì, dẫn tới kết quả gần như nhiễu. Để dự đoán "cao/thấp" thực sự có ý nghĩa, cần dùng embedder ngữ nghĩa thật (ví dụ `LocalEmbedder`) thay vì mock.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query)                                                                                                                      | Top-1 Chunk truy xuất được (tóm tắt)                                                                            | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt)                                             |
| - | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------ | --------------------------------- | --------------------------------------------------------------------------------- |
| 1 | Người mua phải gửi yêu cầu đổi trả trong thời hạn nào?Người mua cần làm gì khi muốn đổi trả hàng lỗ             | "Đổi trả hàng: Người mua cần gửi yêu cầu đổi trả trong thời hạn được nêu trên trang sản phẩm…" | 0.8122       | Không                            | Trả lời dựa trên đoạn disclaimer, không phải nội dung chính sách thật |
| 2 | Khi hàng bị lỗi hoặc không đúng mô tả thì yêu cầu đổi trả cần kèm theo gì?                                           | "Đổi trả hàng: Yêu cầu phải kèm bằng chứng phù hợp khi hàng bị lỗi…"                                  | 0.7007       | Không                            | Lấy nhầm ngữ cảnh từ returns-policy dù câu hỏi thuộc seller-listing      |
| 3 | Người bán phải cung cấp những thông tin gì khi đăng bán sản phẩm?*(có `metadata_filter={"customer_role":"seller"}`)* | "Đăng bán sản phẩm: Người bán chịu trách nhiệm cung cấp thông tin sản phẩm chính xác…"              | 0.8274       | Không                            | Sai nguồn, dù điểm số cao nhất trong 3 kết quả                            |
| 4 | Những sản phẩm nào không được phép đăng bán trên sàn?                                                                    | "Đăng bán sản phẩm: Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán.                          | 0.7328       | Có                               | Nội dung đúng chủ đề (trách nhiệm người bán)                           |
| 5 | Người bán có trách nhiệm gì khi người mua gửi yêu cầu đổi trả?                                                          | "Đổi trả hàng: Người bán có trách nhiệm phản hồi theo quy trình của sàn."                              | 0.8144       | Có                               | Có nhắc đúng quy trình đổi trả                                            |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Bài học rút ra: chất lượng retrieval phụ thuộc rất nhiều vào (1) embedder có ngữ nghĩa thật (không phải mock) và (2) chunk không nên để lẫn các đoạn text meta/disclaimer với nội dung chính — cần cân nhắc lọc hoặc tách riêng các đoạn đó trước khi ingest.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                  |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                  |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10                |
| **Tổng phần cá nhân**                      | **60 / 60**      |
