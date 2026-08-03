# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đăng Long
**Mã sinh viên:** 2A202601934
**Nhóm:** K4
**Ngày:** 2026-08-03

Phần implementation cá nhân được đặt trong `src/K4_2A202601934_NguyenDangLong/`.
Package này tự chứa chunkers, embedding backends, vector store, agent và chiến lược heading-recursive của tôi.

## 1. Khởi động (Warm-up) - 5 điểm

### Độ tương tự Cosine

Cosine similarity đo góc giữa hai vector embedding thay vì chỉ đo độ dài của chúng.
Giá trị càng gần 1 thì hai đoạn văn có hướng ngữ nghĩa càng giống nhau; giá trị gần 0 hoặc âm cho thấy chúng ít tương đồng trong không gian embedding.

Ví dụ có độ tương tự cao:

- Câu A: `This black cotton dress is available in several sizes.`
- Câu B: `The black dress comes in multiple sizes.`
- Hai câu cùng nói về một chiếc váy đen và nhiều kích cỡ, dù cách diễn đạt khác nhau.

Ví dụ có độ tương tự thấp:

- Câu A: `Dry clean only.`
- Câu B: `Machine wash at 40 degrees.`
- Hai câu mô tả hướng dẫn chăm sóc trái ngược nhau.

Cosine similarity phù hợp với text embedding vì nó tập trung vào hướng biểu diễn ngữ nghĩa và ít bị ảnh hưởng bởi độ dài tuyệt đối của văn bản.

### Bài toán tính toán Chunking

Với tài liệu 10,000 ký tự, `chunk_size=500` và `overlap=50`, bước dịch là `500 - 50 = 450` ký tự.
Theo công thức của đề bài, số chunk là `ceil((10,000 - 50) / 450) = ceil(22.111...) = 23`.

Khi overlap tăng lên 100, bước dịch còn `500 - 100 = 400` và số chunk là `ceil((10,000 - 100) / 400) = ceil(24.75) = 25`.
Overlap lớn giúp giữ phần ngữ cảnh nằm ở ranh giới giữa hai chunk, nhưng làm tăng số chunk và chi phí embedding.

## 2. Hướng tiếp cận của tôi (My Approach) - 10 điểm

### Các hàm chia nhỏ

`SentenceChunker.chunk` dùng regex `r"(?<=[.!?])\s+"` để tách sau dấu kết thúc câu.
Hàm loại bỏ đoạn rỗng, gom tối đa số câu cấu hình được vào một chunk và trả về danh sách rỗng khi input rỗng.

`RecursiveChunker.chunk` thử các separator theo thứ tự đoạn văn, dòng, câu, khoảng trắng rồi mới hard-split theo kích thước.
Base case là văn bản đã ngắn hơn `chunk_size`, không còn separator, hoặc input rỗng; mọi chunk trả về đều được strip để tránh whitespace rác.

`HeadingRecursiveChunker` là chiến lược riêng của tôi cho product listing.
Nó tách từng section Markdown theo heading, giữ heading trong mọi child chunk và dùng recursive fallback cho section quá dài.

<<<<<<< HEAD
**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text)`: **lookbehind** `(?<=...)` chỉ *khớp vị trí* khoảng trắng đứng sau dấu câu chứ không nuốt dấu câu, nên `"Câu một. Câu hai."` cho `["Câu một.", "Câu hai."]` — giữ nguyên `.`/`!`/`?` ở cuối câu trước. `\s+` gộp luôn trường hợp `".\n"` và nhiều khoảng trắng liên tiếp nên không cần liệt kê riêng `". "`, `"! "`, `"? "`.
> Edge case đã xử lý: text rỗng → `[]`; `strip()` từng câu rồi loại câu rỗng (tránh chunk chỉ chứa khoảng trắng khi text có dấu câu ở cuối); text không có dấu câu nào → regex không tách được, trả về đúng 1 chunk là cả đoạn; `max_sentences_per_chunk` được ép `max(1, ...)` trong `__init__` để `range(0, n, limit)` không bao giờ nhận step = 0 (vòng lặp vô hạn).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split(text, separators)` thử separator theo **thứ tự ưu tiên** `["\n\n", "\n", ". ", " ", ""]` — tách theo ranh giới ngữ nghĩa lớn trước, chỉ hạ xuống ranh giới nhỏ hơn khi buộc phải làm. Với separator hiện tại, hàm cắt text rồi **gộp các phần liền kề vào một buffer** chừng nào chưa vượt `chunk_size` (nhờ vậy 3 câu ngắn nằm chung 1 chunk thay vì thành 3 chunk vụn); phần nào tự nó vẫn dài quá thì **đệ quy** với danh sách separator còn lại.
> Ba nhánh dừng, bảo đảm đệ quy luôn tiến và không lặp vô hạn: (1) `len(text) <= chunk_size` → trả `[text]`; (2) hết separator **hoặc** separator là `""` → `_fixed_cut` cắt cứng theo `chunk_size` (lối thoát cuối); (3) separator không xuất hiện trong text → gọi lại với `separators[1:]`, text giữ nguyên — không tách nhưng danh sách separator ngắn đi 1 nên vẫn hội tụ về (1) hoặc (2).
=======
### EmbeddingStore

`add_documents` sao chép metadata, bảo đảm có `doc_id`, tạo ID chunk duy nhất và lưu embedding cùng nội dung trong in-memory store.
`search` embed query một lần, tính dot product với các record, sắp xếp giảm dần theo score và trả về `top_k` kết quả.
>>>>>>> cd9427de4f9d4d7d9db94152ba1da3adf96d0db3

`search_with_filter` lọc metadata trước rồi mới xếp hạng similarity trên tập record còn lại.
`delete_document` xóa toàn bộ record có cùng `doc_id`, còn `get_collection_size` trả về số chunk hiện có.

<<<<<<< HEAD
**`add_documents` + `search`** — hướng tiếp cận:
> **Lưu trữ:** backend in-memory (`self._store` là `list[dict]`, `_use_chroma = False` — Chroma là phần bonus, không làm). `_make_record(doc)` chuẩn hoá mọi Document về đúng một schema `{id, content, metadata, embedding}`; metadata được **copy** (`dict(doc.metadata)`) để store không sửa nhầm dict của người gọi, và luôn có khóa `doc_id` (`setdefault(doc_id, doc.id)`) vì `delete_document` lọc theo chính khóa này. `id` ghép `doc.id` với `self._next_index` nên thêm cùng một `doc.id` nhiều lần vẫn không đụng id.
> **Tính độ tương tự:** `_search_records` nhúng query **đúng một lần** (ngoài vòng lặp — nhúng lại trong loop là N lần gọi embedding thừa), tính **dot product** với từng embedding đã lưu, sort giảm dần theo `score` rồi cắt `[:top_k]`. Dùng dot thay vì cosine đầy đủ là hợp lệ ở đây vì `MockEmbedder` đã L2-normalize vector đầu ra, nên dot ≡ cosine.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc TRƯỚC, xếp hạng SAU.** Làm ngược lại (lấy top-k rồi mới bỏ record lệch metadata) có thể trả về **0 kết quả dù store vẫn còn tài liệu hợp lệ**: nếu 3 chunk `department=marketing` tình cờ chiếm trọn top-3 thì lọc-sau sẽ vứt sạch cả 3 và không còn gì để trả, trong khi lọc-trước vẫn xếp hạng trong nhóm `engineering` và trả về đủ `top_k`. Một record chỉ đi tiếp khi khớp **mọi** cặp key/value trong `metadata_filter` (`all(...)`).
> `search()` và `search_with_filter()` **dùng chung `_search_records`**, nên khi `metadata_filter=None` hai hàm chắc chắn cho cùng kết quả thay vì lệch nhau do trùng lặp logic. `delete_document(doc_id)` dựng lại danh sách chỉ gồm record có `metadata['doc_id'] != doc_id`, so sánh độ dài trước/sau để biết có xoá được gì không → `True` nếu ít nhất 1 record biến mất, `False` nếu không khớp record nào. Cách này xoá **tất cả** chunk của cùng một file gốc trong một lần, đúng với việc `ingest.py` sinh nhiều chunk (`<doc_id>::chunk_0`, `::chunk_1`, ...) từ một tài liệu.
=======
### KnowledgeBaseAgent

`answer` lấy top-k chunks, dựng context có số thứ tự và source ID, sau đó đưa context cùng câu hỏi vào prompt.
Nếu store rỗng, agent trả về thông báo thiếu context thay vì gọi LLM với dữ liệu rỗng.
>>>>>>> cd9427de4f9d4d7d9db94152ba1da3adf96d0db3

### Kết quả kiểm thử

<<<<<<< HEAD
**`answer`** — hướng tiếp cận:
> Agent **không tự nhúng gì cả**: nó gọi `self.store.search(question, top_k=top_k)` và tái sử dụng toàn bộ phần retrieval đã hoàn thành. Store rỗng / không có kết quả → trả thẳng thông báo thiếu căn cứ, **không gọi LLM** (gọi lúc đó chỉ tạo cơ hội cho model bịa).
> **Cấu trúc prompt** gồm 4 phần: *instruction* (chỉ dùng Context, nói rõ khi không đủ thông tin, trích dẫn bằng `[n]`) → *Context* → *Question* → nhãn `Answer:` để model biết chỗ bắt đầu sinh. **Inject context** bằng cách đánh số từng chunk `[1] (nguồn: <doc_id>) <nội dung>` ngăn cách bởi dòng trống — nhờ số hiệu + `doc_id` mà mỗi ý trong câu trả lời truy vết được về đúng chunk và đúng file gốc, đây chính là tiêu chí *grounding* trong `docs/EVALUATION.md`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-8.4.2, pluggy-1.6.0 -- C:\Python314\python.exe
cachedir: .pytest_cache
rootdir: E:\Labs\DAY07-2A202601934-NGUYENDANGLONG
plugins: anyio-4.13.0, hydra-core-1.3.4
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

============================= 42 passed in 0.15s ==============================
```

> Bộ test chấm gói cá nhân `src.K4_2A202601308_LuongMinhQuan` qua biến `LAB_SOLUTION_PACKAGE` (khai trong `.env`, được `conftest.py` ở thư mục gốc nạp trước khi pytest import test module). Toàn bộ code nộp nằm trong gói cá nhân; gói dùng chung `src/` giữ nguyên, không sửa.
>
> Demo end-to-end chạy bằng entrypoint của gói cá nhân (`main.py` ở thư mục gốc import thẳng `src.chunking`/`src.store`/`src.agent` nên phụ thuộc gói chung):
>
> ```
> $ python -m src.K4_2A202601308_LuongMinhQuan.main "Chunking là gì?"
> Đã nạp 77 chunk vào EmbeddingStore   (data/k4_asos_products, FixedSizeChunker mặc định)
> ```

**Số lượng bài test vượt qua (pass):** **42** / 42
=======
Bộ test được chạy với package cá nhân bằng cách ánh xạ package Long vào tên import `src`.

```text
..........................................                               [100%]
42 passed in 0.01s
```

## 3. Dự đoán độ tương tự (Similarity Predictions) - 5 điểm
>>>>>>> cd9427de4f9d4d7d9db94152ba1da3adf96d0db3

Các điểm dưới đây được tính bằng `MockEmbedder` deterministic của package cá nhân.
Mock embedding chỉ dùng để kiểm tra kỹ thuật, không dùng để kết luận chất lượng ngữ nghĩa của product retrieval.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | This black cotton dress is available in several sizes. | The black dress comes in multiple sizes. | Cao | -0.058424 | Không |
| 2 | The item is made from 100% cotton. | The product uses a cotton main fabric. | Cao | 0.081780 | Không |
| 3 | This jacket is black. | This jacket is bright red. | Thấp | 0.025432 | Có |
| 4 | Dry clean only. | Machine wash at 40 degrees. | Thấp | 0.047879 | Có |
| 5 | The product is from adidas Originals. | This item is made by Calvin Klein. | Thấp | 0.103554 | Không |

Điều bất ngờ là các cặp có nghĩa gần nhau không nhất thiết có score cao.
Nguyên nhân là MockEmbedder sinh vector từ hash chuỗi, không hiểu synonym, phủ định hoặc quan hệ thương hiệu.
Kết quả này xác nhận benchmark semantic phải dùng local multilingual embedder thay vì mock.

## 4. Kết quả truy xuất của tôi (Competition Results) - 10 điểm

Tôi chạy đúng năm golden queries trong `benchmark/queries.py` với package cá nhân, `HeadingRecursiveChunker`, `chunk_size=400`, `top_k=3` và model `BAAI/bge-m3`.
Kết quả đầy đủ được lưu tại `src/K4_2A202601934_NguyenDangLong/benchmark_results.json`.

| # | Câu hỏi | Top-1 | Score | Relevant | Agent answer |
|---|---|---|---:|---|---|
| 1 | Sản phẩm nào phải giặt khô và làm từ gì? | Đúng adidas Originals bralet | 0.532 | Có, TOP-1 | Chưa xác nhận |
| 2 | Đầm maxi ASOS EDITION satin giá bao nhiêu? | Đúng ASOS EDITION satin cami maxi dress | 0.747 | Có, TOP-1 | Chưa xác nhận |
| 3 | Áo khoác nào làm từ lông giả? | Đúng Daisy Street faux fur coat | 0.607 | Có, TOP-1 | Chưa xác nhận |
| 4 | Sản phẩm đen, cổ yếm để đi biển? | Đúng Hollister halterneck bikini top | 0.626 | Có, TOP-1 | Chưa xác nhận |
| 5 | Có maternity dress không và fit thế nào? | Đúng ASOS DESIGN maternity dress | 0.642 | Có, TOP-1 | Chưa xác nhận |

**Số query có chunk liên quan trong top-3:** 5 / 5.

Golden runner tính retrieval tự động là 10/10.
Tôi chưa nhận điểm cuối cho mục này vì agent answers chưa được chạy và đối chiếu với gold answers.

### Failure analysis

Với MiniLM baseline, Q1 từng MISS vì `Dry clean only` và `100% Cotton` nằm ở hai subsection khác nhau.
Khi giữ nguyên strategy và chuyển sang BGE-M3, Q1 vào TOP-1 với score 0.532.
Điều này cho thấy embedding model có ảnh hưởng trực tiếp đến retrieval quality; không nên sửa chunker chỉ để bù cho một embedding model yếu hơn.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận (My Approach) | 10 / 10 |
| Hoàn thiện code, 42 tests | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 0 / 10 |
| **Tổng phần cá nhân hiện tại** | **50 / 60** |
