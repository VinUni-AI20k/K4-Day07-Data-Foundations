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
> Hai vector embedding chỉ gần như cùng một hướng trong không gian ngữ nghĩa, tức hai đoạn văn bản nói về cùng chủ đề / cùng ý định. Điểm gần 1.0 là rất giống, gần 0 là không liên quan, âm là ngược hướng ngữ nghĩa.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn trả lại đôi giày đã mua tuần trước."
- Câu B: "Làm thế nào để gửi yêu cầu hoàn trả sản phẩm đã đặt?"
- Tại sao tương đồng: cùng ý định "trả hàng", chia sẻ trường từ vựng (trả lại / hoàn trả, mua / đặt, sản phẩm). Cách diễn đạt khác nhau nhưng embedding bắt được ý nghĩa chứ không bắt từ khóa, nên vẫn nằm gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thời gian nhận tiền hoàn thường là 7–14 ngày làm việc."
- Câu B: "Python là ngôn ngữ lập trình thông dịch, kiểu động."
- Tại sao khác: hai chủ đề hoàn toàn tách biệt (chính sách hoàn tiền TMĐT với đặc điểm ngôn ngữ lập trình), không có khái niệm nền chung nào để embedding kéo hai vector về cùng hướng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc nên bỏ qua độ lớn (magnitude) của vector — một chunk dài và một câu hỏi ngắn cùng chủ đề vẫn cho điểm cao, trong khi Euclid bị phạt chỉ vì chênh lệch độ dài/chuẩn vector. Ngoài ra ở số chiều lớn, khoảng cách Euclid giữa các điểm co lại gần bằng nhau (curse of dimensionality) nên mất khả năng phân biệt, còn cosine vẫn tách được tốt.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy (step) của cửa sổ trượt: `step = chunk_size - overlap = 500 - 50 = 450`.
> Chunk đầu phủ từ vị trí 0 và mỗi chunk sau dịch thêm 450 ký tự, nên số chunk là:
> `n_chunks = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.11) + 1 = 22 + 1 = 23`
> Kiểm tra lại theo vòng lặp trong `FixedSizeChunker.chunk`: các vị trí bắt đầu là 0, 450, 900, …, 9900 (23 giá trị); tại `start = 9900` thì `9900 + 500 ≥ 10000` nên vòng lặp cắt (break). Chunk cuối là `text[9900:10400]`, thực tế chỉ còn 100 ký tự.
> *Đáp án:* **23 chunks** (22 chunk đầy 500 ký tự + 1 chunk đuôi 100 ký tự).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 400 nên số chunk **tăng lên 25** (`ceil(9500 / 400) + 1 = 24 + 1 = 25`) — overlap lớn hơn thì cửa sổ dịch chậm hơn, tốn thêm chi phí lưu trữ và embedding. Đổi lại, overlap nhiều giúp một câu/ý nằm vắt qua ranh giới chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, tránh mất ngữ cảnh khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

- **Regex tách câu:** `re.split(r'(?<=[.!?])\s+', text)`.
- **Vì sao dùng lookbehind:** giữ lại dấu câu ở cuối mỗi câu thay vì nuốt mất; `\s+` bao luôn cả `". "` lẫn `".\n"`.
- **Gom nhóm:** mỗi `max_sentences_per_chunk` câu ghép thành một chunk bằng `" ".join(...)` rồi `.strip()`.
- **Edge case đã xử lý:** văn bản rỗng / chỉ có khoảng trắng trả về `[]`; loại bỏ mảnh rỗng sau khi split; nhóm cuối được phép ngắn hơn `max_sentences_per_chunk`.
- **Hạn chế đã biết:** cắt nhầm ở chữ viết tắt có dấu chấm ("TP.", "vd.").

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

- **Phân vai:** `chunk()` chỉ là lớp vỏ gọi `self._split(text, self.separators)`; toàn bộ logic nằm ở hàm đệ quy.
- **Bước đệ quy:** cắt theo dấu phân cách ưu tiên cao nhất `remaining_separators[0]`; mảnh nào còn dài hơn `chunk_size` thì gọi lại với `remaining_separators[1:]`, tức hạ dần `"\n\n"` → `"\n"` → `". "` → `" "`.
- **Base case 1:** `len(current_text) <= chunk_size` → trả về `[current_text]`.
- **Base case 2:** hết dấu phân cách → cắt cứng theo `chunk_size`; nhánh này bảo đảm `separators=[]` vẫn trả về danh sách không rỗng.
- **Hậu xử lý:** ghép các mảnh nhỏ liền kề tới sát `chunk_size` để chunk không bị vụn, truy xuất tốt hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

- **Cấu trúc lưu trữ:** `_make_record` chuẩn hóa mỗi `Document` thành bản ghi `{"id", "content", "metadata", "embedding", "index"}`, embedding tính bằng `self._embedding_fn(doc.content)`.
- **Chi tiết quan trọng:** luôn `metadata.setdefault("doc_id", doc.id)` trên một **bản sao** của metadata, để `delete_document()` và lọc theo `doc_id` vẫn chạy đúng kể cả khi tài liệu tạo với `metadata={}` — trùng quy ước `ingest.py` gắn cho từng chunk.
- **`add_documents`:** lặp và `append` bản ghi vào `self._store`.
- **`search`:** nhúng câu hỏi đúng một lần, so với embedding mọi bản ghi, sắp xếp score giảm dần, cắt `top_k`.
- **Vì sao dùng `compute_similarity` chứ không phải `_dot` thô:** `MockEmbedder` có chuẩn hóa vector nên với backend mock thì tích vô hướng đúng bằng cosine, nhưng điều đó không được bảo đảm cho mọi backend embedding. Gọi cosine tường minh giúp `search` cho điểm số nhất quán khi đổi sang `LocalEmbedder`/`OpenAIEmbedder` hoặc khi truyền `embedding_fn` tùy ý.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

- **Lọc TRƯỚC rồi mới tìm kiếm (pre-filter):** thu hẹp `self._store` xuống các bản ghi khớp mọi cặp khóa-giá trị trong `metadata_filter`, rồi đưa tập con cho `_search_records` — cũng là lý do `_search_records` nhận tham số `records` thay vì đọc thẳng `self._store`.
- **Vì sao lọc trước:** rẻ hơn (chỉ tính similarity trên tập con) và bảo đảm đủ `top_k` kết quả hợp lệ; lọc sau dễ trả về ít hơn `top_k`.
- **Khi `metadata_filter=None`:** bỏ qua hoàn toàn bước lọc, kết quả trùng với `search` thường.
- **`delete_document`:** dựng lại `self._store` chỉ giữ bản ghi có `metadata["doc_id"] != doc_id` — xóa trọn mọi chunk của cùng một tài liệu trong một lượt.
- **Giá trị trả về:** so sánh số bản ghi trước/sau để trả `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

- **`__init__`:** chỉ giữ tham chiếu `self.store` và `self.llm_fn`, tách bạch phần truy xuất với phần sinh câu trả lời.
- **3 bước RAG:** `store.search(question, top_k)` → ghép chunk thành khối ngữ cảnh → gọi `llm_fn(prompt)`.
- **Cách inject context:** đánh số từng chunk (`[1] ...`, `[2] ...`) để câu trả lời có thể trích dẫn nguồn.
- **Cấu trúc prompt:** khối ngữ cảnh + câu hỏi người dùng + chỉ dẫn bắt buộc chỉ trả lời dựa trên ngữ cảnh và nói rõ khi ngữ cảnh không chứa thông tin (phần chống bịa / hallucination).
- **Trường hợp rỗng:** truy xuất không ra chunk nào thì trả thẳng thông báo không tìm thấy, không gọi `llm_fn` với ngữ cảnh rỗng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: $env:LAB_SOLUTION_PACKAGE = "src.ChuQuangHieu_2A202601344"; python -m pytest tests/ -v

================================================================== test session starts ==================================================================
platform win32 -- Python 3.12.7, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\SVSTORE\Desktop\git-repos\K4-Day07-Data-Foundations-C53\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\SVSTORE\Desktop\git-repos\K4-Day07-Data-Foundations-C53
collected 42 items                                                                                                                                       

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                              [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                       [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                 [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                      [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                      [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                            [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                             [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                           [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                             [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                             [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                        [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                    [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                              [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                     [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                         [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                   [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                         [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                             [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                               [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                 [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                       [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                            [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                              [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                  [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                               [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                        [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                       [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                  [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                              [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                         [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                             [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                   [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                             [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                          [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                        [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                       [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                           [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                      [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                               [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                     [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                         [100%]

================================================================== 42 passed in 0.16s ===================================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Backend đo:** `MockEmbedder` (mặc định của lab, 64 chiều, băm MD5). Máy chưa cài `requirements-local.txt` nên chưa chạy được `LocalEmbedder`; ngưỡng phân loại đặt ở `score >= 0.5` là "cao".

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn trả lại đôi giày đã mua tuần trước. | Làm thế nào để gửi yêu cầu hoàn trả sản phẩm đã đặt? | cao | +0.117 | ❌ Sai |
| 2 | Bao lâu thì tôi nhận được tiền hoàn? | Thời gian nhận tiền hoàn là 7 - 14 ngày làm việc tùy theo ngân hàng. | cao | −0.094 | ❌ Sai |
| 3 | Thời hạn gửi yêu cầu Trả hàng/Hoàn tiền là 15 ngày. | Thời hạn yêu cầu trả hàng hoàn tiền là mười lăm ngày. | cao | −0.047 | ❌ Sai |
| 4 | Phí trả hàng do ai chịu? | Sản phẩm nào không được phép trả hàng? | thấp | +0.072 | ✅ Đúng (nhưng trùng hợp) |
| 5 | Cách đóng gói hàng hoàn trả đúng quy định. | Python là ngôn ngữ lập trình thông dịch, kiểu động. | thấp | +0.044 | ✅ Đúng (nhưng trùng hợp) |

**Số dự đoán đúng: 2/5** — và cả 2 lần đúng đều không phải vì mô hình hiểu ngữ nghĩa, mà vì mọi cặp đều ra điểm quanh 0.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 3: hai câu diễn đạt **cùng một quy định** ("15 ngày" và "mười lăm ngày") lại cho điểm **âm** (−0.047), thấp hơn cả cặp 5 vốn hoàn toàn khác chủ đề (+0.044). Kiểm tra thêm còn thấy `"trả hàng hoàn tiền"` với `"trả hàng hoàn tiền."` — chỉ khác đúng một dấu chấm — cho điểm **−0.263**, trong khi một chuỗi so với chính nó cho đúng 1.0.
> Điều này cho thấy `MockEmbedder` **không biểu diễn ý nghĩa gì cả**: nó băm MD5 toàn bộ chuỗi rồi sinh vector giả ngẫu nhiên, nên chỉ có tính **xác định** (cùng input thì cùng output) chứ không có tính **liên tục về ngữ nghĩa** — đổi một ký tự là ra một vector hoàn toàn khác. Vì vậy điểm số ở bảng trên chỉ dùng để kiểm chứng công thức cosine đã cài đúng, tuyệt đối không dùng để kết luận chiến lược chunking nào tốt hơn (đúng như cảnh báo trong `README.md`).
> Bài học rút ra: embedding thật (như `paraphrase-multilingual-MiniLM-L12-v2`) đặt các câu cùng ý định gần nhau vì được huấn luyện trên ngữ cảnh sử dụng của từ, chứ bản thân phép cosine không hề tạo ra ngữ nghĩa. Chất lượng truy xuất phụ thuộc vào mô hình nhúng trước, rồi mới tới độ đo.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình chạy:** `RecursiveChunker(chunk_size=500)` + `MockEmbedder` trên `data/k4_ecommerce` (10 tài liệu → **139 chunk**). Câu 4 chạy bằng `search_with_filter(metadata_filter={"customer_role": "seller"})`, 4 câu còn lại dùng `search` thường. `llm_fn` là hàm giả lập trả về nguyên khối ngữ cảnh đầu tiên (chưa gắn LLM thật).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Bao nhiêu ngày để gửi yêu cầu Trả hàng/Hoàn tiền? | `chinh-sach-tra-hang-hoan-tien` — "Shopee khuyến khích Người Mua chủ động liên hệ với Người Bán để thương lượng…" | +0.3215 | ❌ Sai tài liệu (cần `quy-dinh-chung-tra-hang-hoan-tien`), top-3 cũng không có | Lặp lại đoạn thương lượng với Người Bán — không trả lời được mốc 15 ngày |
| 2 | Thẻ tín dụng bao lâu nhận được tiền hoàn? | `quan-ly-don-tra-hang-hoan-tien` — "Nhấn chọn Nhập tồn kho nhanh để hoàn tất quá trình nhập hàng…" | +0.3402 | ❌ Sai tài liệu (cần `thoi-gian-nhan-tien-hoan`), top-3 cũng không có | Nói về nhập tồn kho — lạc đề hoàn toàn |
| 3 | Cây cảnh / thực phẩm đông lạnh còn nguyên vẹn có trả được không? | `phuong-thuc-gui-hang-va-phi-hoan-tra` — "Sau khi bạn đã gửi yêu cầu hoàn tiền và chọn hình thức trả hàng…" | +0.3162 | ⚠️ Top-1 sai, nhưng `san-pham-han-che-tra-hang` **có** ở hạng 3 | Nói về hình thức gửi trả tại bưu cục — không trả lời được câu hỏi |
| 4 | **(lọc `customer_role: seller`)** Người bán phải phản hồi trong bao lâu? | `quan-ly-don-tra-hang-hoan-tien` — "Nhấn chọn Nhập tồn kho nhanh…" | +0.1357 | ⚠️ Đúng tài liệu nhưng **hiển nhiên**: bộ lọc chỉ còn đúng 1 tài liệu nên mọi kết quả đều là nó; sai đoạn (cần mục C, mốc 2 ngày) | Trả về đoạn về các loại bể vỡ — sai đoạn, và **không dùng bộ lọc** (xem ghi chú dưới) |
| 5 | Hình thức trả hàng nào phải tự trả phí trước? | `phuong-thuc-gui-hang-va-phi-hoan-tra` — "Bước 4: Đơn vị vận chuyển sẽ đến lấy hàng… Trả hàng tại bưu cục (Miễn phí…)" | +0.3359 | ⚠️ Đúng tài liệu, sai đoạn (cần mục "Tự sắp xếp") | Nói về ĐVVC đến lấy hàng — gần chủ đề nhưng không nêu được "Tự sắp xếp" |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **3 / 5** (đúng ở mức *tài liệu*: câu 3, 4, 5). Chặt hơn: top-1 đúng tài liệu chỉ **2/5**, và **0/5** nếu tính ở mức *đoạn văn thực sự chứa câu trả lời chuẩn*.

**Phân tích kết quả:**
- **Điểm số dồn cục quanh 0.32** cho cả kết quả đúng lẫn sai (0.3162 vs 0.3215 vs 0.3402) — score **không phân biệt được** tín hiệu với nhiễu, đúng như dự đoán ở Phần 4 về `MockEmbedder`.
- **Câu 4 cho thấy metadata filter thật sự có tác dụng**: chỉ 1 trong 10 tài liệu có `customer_role: seller`, nên bộ lọc loại sạch nhiễu và ép top-3 về đúng tài liệu — đây là trường hợp duy nhất mà việc "trúng" không phụ thuộc vào chất lượng embedding.
- **Hạn chế phát hiện được ở `KnowledgeBaseAgent`:** `answer()` chỉ gọi `store.search()`, chưa có đường truyền `metadata_filter` xuống. Vì vậy ở câu 4, phần truy xuất có lọc nhưng câu trả lời của agent thì không — hai con số trong bảng lệch nhau. Nếu làm tiếp, tôi sẽ thêm tham số `metadata_filter` cho `answer()`.
- **Kết luận:** con số 3/5 ở trên **không** phản ánh chất lượng chiến lược chunking. Muốn đánh giá thật phải cài `requirements-local.txt` rồi chạy lại với `EMBEDDING_PROVIDER=local`, đúng như `README.md` cảnh báo.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu sau buổi demo:*

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
