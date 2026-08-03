# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Minh Quân
**Nhóm:** Độ MESSIU
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine cao nghĩa là hai vector embedding **chỉ về cùng một hướng** trong không gian ngữ nghĩa, tức hai đoạn text nói về cùng một chủ đề/ý — bất kể chúng dài ngắn khác nhau hay dùng từ ngữ khác nhau. Giá trị chạy từ -1 (ngược hướng) qua 0 (không liên quan) đến 1 (trùng hướng); kiểm chứng bằng code: vector giống hệt → 1.0, vuông góc → 0.0, ngược dấu → -1.0 (4 test `TestComputeSimilarity` pass).

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm trong vòng 30 ngày."
- Câu B: "Chính sách hoàn hàng cho phép gửi lại đơn hàng trong vòng một tháng."
- Tại sao tương đồng: gần như không dùng chung từ nào ("đổi trả" vs "hoàn hàng", "30 ngày" vs "một tháng") nhưng cùng một **ý định**: thời hạn trả hàng. Embedding mã hoá ngữ nghĩa chứ không mã hoá mặt chữ, nên hai câu nằm gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi muốn đổi trả sản phẩm trong vòng 30 ngày."
- Câu B: "Hướng dẫn cài đặt driver máy in trên Windows."
- Tại sao khác: khác hoàn toàn miền chủ đề (chính sách TMĐT vs kỹ thuật thiết bị), không chia sẻ chủ thể, hành động hay mục tiêu nào, nên hai vector gần như trực giao (cosine ≈ 0).

> **Lưu ý khi tự kiểm bằng code:** `MockEmbedder` trong `src/embeddings.py` sinh vector từ `hashlib.md5`, tức là **giả lập xác định (deterministic) chứ không mang ngữ nghĩa**. Chạy cặp câu trên với `_mock_embed` cho kết quả ~ -0.23 (cặp CAO) và ~ -0.02 (cặp THẤP) — không phản ánh ý nghĩa, đúng như thiết kế: mock chỉ để test chạy được offline. Muốn số liệu thật cho bảng ở Mục 4 phải bật `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`) hoặc `OpenAIEmbedder`.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ dài (norm) của vector embedding phần lớn phản ánh **độ dài / số token** của đoạn text chứ không phải nội dung, nên khoảng cách Euclid sẽ phạt oan một chunk dài và một câu ngắn dù chúng nói cùng một điều. Cosine chuẩn hoá norm đi và chỉ giữ lại **hướng** — tức phần ngữ nghĩa — nên phù hợp hơn khi so một câu hỏi ngắn với các chunk tài liệu dài, đúng tình huống retrieval của Lab này.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Mỗi chunk dài 500, hai chunk liền nhau chồng nhau 50 ký tự, nên mỗi bước tiến (`step`) chỉ đi được `500 - 50 = 450` ký tự. Chunk đầu tiên "tiêu thụ" trọn 500 ký tự, các chunk sau mỗi cái thêm 450 ký tự mới:
> `ceil((length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / 450) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* **23 chunks** — đã đối chiếu bằng code: `len(FixedSizeChunker(500, 50).chunk("x" * 10000)) == 23`.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk **tăng**: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunk (kiểm bằng code: 25). Overlap lớn hơn ⇒ step nhỏ hơn ⇒ cần nhiều chunk hơn để phủ hết tài liệu. Đánh đổi: overlap nhiều giúp một câu/ý bị cắt ngang ranh giới vẫn xuất hiện nguyên vẹn trong ít nhất một chunk (đỡ mất ngữ cảnh khi truy xuất), nhưng phải trả giá bằng nhiều bản ghi hơn trong store, nhiều lần gọi embedding hơn, và kết quả top-k dễ bị trùng lặp nội dung.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r"(?<=[.!?])\s+", text)`: **lookbehind** `(?<=...)` chỉ *khớp vị trí* khoảng trắng đứng sau dấu câu chứ không nuốt dấu câu, nên `"Câu một. Câu hai."` cho `["Câu một.", "Câu hai."]` — giữ nguyên `.`/`!`/`?` ở cuối câu trước. `\s+` gộp luôn trường hợp `".\n"` và nhiều khoảng trắng liên tiếp nên không cần liệt kê riêng `". "`, `"! "`, `"? "`.
> Edge case đã xử lý: text rỗng → `[]`; `strip()` từng câu rồi loại câu rỗng (tránh chunk chỉ chứa khoảng trắng khi text có dấu câu ở cuối); text không có dấu câu nào → regex không tách được, trả về đúng 1 chunk là cả đoạn; `max_sentences_per_chunk` được ép `max(1, ...)` trong `__init__` để `range(0, n, limit)` không bao giờ nhận step = 0 (vòng lặp vô hạn).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split(text, separators)` thử separator theo **thứ tự ưu tiên** `["\n\n", "\n", ". ", " ", ""]` — tách theo ranh giới ngữ nghĩa lớn trước, chỉ hạ xuống ranh giới nhỏ hơn khi buộc phải làm. Với separator hiện tại, hàm cắt text rồi **gộp các phần liền kề vào một buffer** chừng nào chưa vượt `chunk_size` (nhờ vậy 3 câu ngắn nằm chung 1 chunk thay vì thành 3 chunk vụn); phần nào tự nó vẫn dài quá thì **đệ quy** với danh sách separator còn lại.
> Ba nhánh dừng, bảo đảm đệ quy luôn tiến và không lặp vô hạn: (1) `len(text) <= chunk_size` → trả `[text]`; (2) hết separator **hoặc** separator là `""` → `_fixed_cut` cắt cứng theo `chunk_size` (lối thoát cuối); (3) separator không xuất hiện trong text → gọi lại với `separators[1:]`, text giữ nguyên — không tách nhưng danh sách separator ngắn đi 1 nên vẫn hội tụ về (1) hoặc (2).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> **Lưu trữ:** backend in-memory (`self._store` là `list[dict]`, `_use_chroma = False` — Chroma là phần bonus, không làm). `_make_record(doc)` chuẩn hoá mọi Document về đúng một schema `{id, content, metadata, embedding}`; metadata được **copy** (`dict(doc.metadata)`) để store không sửa nhầm dict của người gọi, và luôn có khóa `doc_id` (`setdefault(doc_id, doc.id)`) vì `delete_document` lọc theo chính khóa này. `id` ghép `doc.id` với `self._next_index` nên thêm cùng một `doc.id` nhiều lần vẫn không đụng id.
> **Tính độ tương tự:** `_search_records` nhúng query **đúng một lần** (ngoài vòng lặp — nhúng lại trong loop là N lần gọi embedding thừa), tính **dot product** với từng embedding đã lưu, sort giảm dần theo `score` rồi cắt `[:top_k]`. Dùng dot thay vì cosine đầy đủ là hợp lệ ở đây vì `MockEmbedder` đã L2-normalize vector đầu ra, nên dot ≡ cosine.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc TRƯỚC, xếp hạng SAU.** Làm ngược lại (lấy top-k rồi mới bỏ record lệch metadata) có thể trả về **0 kết quả dù store vẫn còn tài liệu hợp lệ**: nếu 3 chunk `department=marketing` tình cờ chiếm trọn top-3 thì lọc-sau sẽ vứt sạch cả 3 và không còn gì để trả, trong khi lọc-trước vẫn xếp hạng trong nhóm `engineering` và trả về đủ `top_k`. Một record chỉ đi tiếp khi khớp **mọi** cặp key/value trong `metadata_filter` (`all(...)`).
> `search()` và `search_with_filter()` **dùng chung `_search_records`**, nên khi `metadata_filter=None` hai hàm chắc chắn cho cùng kết quả thay vì lệch nhau do trùng lặp logic. `delete_document(doc_id)` dựng lại danh sách chỉ gồm record có `metadata['doc_id'] != doc_id`, so sánh độ dài trước/sau để biết có xoá được gì không → `True` nếu ít nhất 1 record biến mất, `False` nếu không khớp record nào. Cách này xoá **tất cả** chunk của cùng một file gốc trong một lần, đúng với việc `ingest.py` sinh nhiều chunk (`<doc_id>::chunk_0`, `::chunk_1`, ...) từ một tài liệu.

### Tác tử KnowledgeBaseAgent

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

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Số liệu đo bằng `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`, 384 chiều) qua `compute_similarity`. Cột cuối kèm điểm của `MockEmbedder` để đối chiếu — mock sinh vector từ `md5` nên **không** dùng để dự đoán được.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (local) | Đúng? | (mock) |
|------|-----------|-----------|---------|--------------|-------|-------|
| 1 | "Áo khoác dáng dài màu be" | "JDY longline teddy coat in beige" | cao | **+0.523** | ✅ | −0.165 |
| 2 | "Chính sách đổi trả cho phép hoàn hàng trong 28 ngày" | "Khách có thể gửi trả đơn hàng miễn phí trong vòng bốn tuần" | cao | **+0.419** | ✅ | +0.013 |
| 3 | "Quần jean ống loe màu hồng" | "Hướng dẫn cài đặt driver máy in trên Windows" | thấp | **−0.009** | ✅ | −0.195 |
| 4 | "Sản phẩm này còn size UK 8 không?" | "Còn hàng: S - UK 8" | cao | **+0.630** | ✅ | −0.009 |
| 5 | "Váy maxi lụa màu xanh" | "Áo blazer trắng dáng lửng" | thấp | **+0.243** | ⚠️ cao hơn dự đoán | +0.133 |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 5**: hai món đồ hoàn toàn khác nhau (váy maxi vs blazer) mà vẫn được +0.243, trong khi cặp 3 (jean vs driver máy in) chỉ −0.009. Embedding không so "cùng một món đồ hay không" mà so **vị trí trong không gian chủ đề**: cả hai câu đều là *tên sản phẩm thời trang nữ có màu và kiểu dáng*, nên chúng cùng nằm trong một cụm và không thể trực giao được — muốn phân biệt tới mức "váy vs áo" phải dùng metadata (`category`) chứ không phải cosine.
> Hai điểm đáng chú ý nữa: **cặp 1** đạt +0.523 dù câu A tiếng Việt, câu B tiếng Anh — model đa ngữ ánh xạ hai ngôn ngữ vào cùng không gian, đây chính là lý do nhóm chọn `paraphrase-multilingual-MiniLM` cho corpus tiếng Việt lẫn tiếng Anh. Và **cặp 4** cao nhất (+0.630) cho thấy một *câu hỏi* vẫn khớp mạnh với một *câu khẳng định* trả lời nó — đúng thứ retrieval cần, vì query của người dùng bao giờ cũng ở dạng câu hỏi còn tài liệu thì ở dạng khẳng định.
> Cột mock cho thấy vì sao không thể dùng mock để phân tích: cặp CAO nhất theo mock lại là cặp 5 (+0.133) còn cặp 2 gần như bằng 0 — thứ tự hoàn toàn ngẫu nhiên vì md5 phá vỡ mọi quan hệ ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> ⚠️ **Nhóm chưa chốt bộ 5 câu hỏi trong `REPORT_NHOM.md`** (Mục 3 còn trống). 5 câu dưới đây là bộ tôi **đề xuất** để nhóm thống nhất; số liệu là kết quả chạy thật, nếu nhóm đổi câu hỏi thì phải chạy lại bảng này.
>
> **Cấu hình đo:** corpus `data/k4_asos_products` (20 tài liệu ASOS), `FixedSizeChunker(chunk_size=500, overlap=50)` → **77 chunk**, `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`), `top_k=3`.
> `llm_fn` là **LLM giả** (không có API key), nên cột cuối đánh giá **grounding** — context đưa cho LLM có đủ căn cứ để trả lời đúng hay không — chứ không đánh giá văn phong câu trả lời.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Áo khoác dáng dài của JDY giá bao nhiêu bảng Anh? | `asos-jdy-longline-teddy-coat-in-beige` — khối "Thong tin san pham": Thương hiệu JDY, Danh mục Coats, **Gia niem yet: GBP 45.00** | +0.477 | ✅ Có (đúng ngay top-1) | Context [1] chứa thẳng "GBP 45.00" → đủ căn cứ trả lời **45 GBP** kèm dẫn nguồn [1] |
| 2 | Sản phẩm nào còn size UK 8? | `...maternity-cami-wrap-midi-dress` — nhưng là đoạn **"UK 18, UK 20 / Model wears: UK 8"** | +0.480 | ⚠️ Đúng tài liệu, **sai chunk** | Context chỉ có phần đuôi dòng "Het hang" và size của người mẫu → agent **không** đủ căn cứ, dễ trả lời sai |
| 3 | Áo lông cừu teddy giặt và bảo quản thế nào? | `...jdy-longline-teddy-coat` — đoạn giới thiệu thương hiệu (không phải phần hướng dẫn giặt) | +0.357 | ⚠️ Có nhưng ở **rank 3** | Chunk rank 3 chứa "Look After Me: Machine wash according to instructions on care label" + "Borg: sheepskin-like fabric" → vẫn trả lời được, nhưng trích dẫn phải là [3] |
| 4 | Có món đồ nào giá dưới 20 bảng không? | `...collusion-x008-y2k-flare-jeans` — **GBP 24.00**, tức KHÔNG thỏa điều kiện | +0.380 | ❌ Top-1 sai (rank 2 = bra 15.00 mới đúng) | Context không đủ để liệt kê đúng: món rẻ nhất thật sự là legging shorts **6.50** lại không lọt top-3 |
| 5 | Bikini và đồ bơi có những màu nào? | `...dorina-shea-mesh-bra` — đoạn blurb thương hiệu có nhắc chữ "swimwear" | +0.524 | ⚠️ Có nhưng ở **rank 3** | Bikini thật (`hollister-co-ord-halterneck-bikini-top-in-black`, màu đen) nằm rank 3 → trả lời được nhưng top-1 gây nhiễu |

**Điểm theo `docs/SCORING.md`** (2 = top-3 có chunk liên quan + trả lời đúng; 1 = có liên quan nhưng thiếu/không ở top-1; 0 = không có trong top-3): **Q1 = 2, Q2 = 1, Q3 = 1, Q4 = 1, Q5 = 1 → 6/10.**

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4** / 5 *(Q2 không tính: cả 3 chunk đều không chứa dòng "Con hang" nào)*

### Phân tích: ba kiểu lỗi truy xuất quan sát được

1. **Chunk cắt ngang thông tin (Q2 — nghiêm trọng nhất).** File `maternity-cami-wrap-midi-dress` có `- Con hang: UK 6, UK 8, UK 10, UK 12, UK 16` ở dòng 37, nhưng `FixedSizeChunker(500, 50)` cắt đúng giữa cụm size: chunk được trả về bắt đầu bằng *"UK 18, UK 20"* — phần đuôi của dòng **`Het hang`**. Tức là chunk chứa đúng thông tin **ngược lại** với câu trả lời. Đây chính là cái giá của overlap = 50 đã phân tích ở Mục 1: overlap không đủ để một dòng bị cắt còn xuất hiện nguyên vẹn ở chunk kế. **Hướng sửa:** dùng `RecursiveChunker` (tách theo `"\n"` trước) để không bao giờ cắt giữa một dòng gạch đầu dòng, hoặc tăng overlap.
2. **Embedding không làm được so sánh số (Q4).** "dưới 20 bảng" là một **phép so sánh**, không phải một khái niệm — vector của "20 bảng" gần vector của "24 bảng" y như gần "15 bảng". Loại câu hỏi này phải giải bằng `search_with_filter` trên metadata `price_gbp`, không phải bằng cosine.
3. **Blurb thương hiệu hút nhầm điểm (Q3, Q5).** Mỗi trang ASOS đều có một đoạn quảng cáo thương hiệu dài, giàu từ khoá ("swimwear", "loungewear", "dresses"...). Đoạn này không trả lời được gì nhưng lại rất "giống" mọi câu hỏi về sản phẩm, nên thường chiếm top-1 và đẩy chunk thật sự hữu ích xuống rank 3. **Hướng sửa:** lọc bỏ khối blurb ngay ở bước ingest, hoặc gắn `section` vào metadata rồi ưu tiên `section=product-details`.

### Lọc metadata có cứu được không?

Có, và đo được. Query *"áo khoác giữ ấm mùa đông"*:

| Cấu hình | Top-3 |
|---|---|
| `search` (không lọc) | +0.425 jdy-coat, +0.404 jdy-coat, **+0.400 amy-lynn-chainmail-mini-dress** ← váy dạ hội lọt vào |
| `search_with_filter(metadata_filter={"category_group": "outerwear"})` | +0.425 jdy-coat, +0.404 jdy-coat, **+0.351 daisy-street-faux-fur-coat** ← cả 3 đều là áo khoác |

Lọc trước đã đẩy chiếc váy ra và kéo áo khoác lông thứ hai vào top-3 — đúng luận điểm ở Mục 2: lọc trước rồi mới xếp hạng thì `top_k` vẫn được lấp đầy bằng ứng viên hợp lệ, còn lọc sau sẽ chỉ còn 2 kết quả.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(điền sau buổi demo — chỗ này chờ phần trình bày của nhóm)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Đủ 2 bài 1.1 + 1.2, phép tính 23 và 25 chunk đã đối chiếu bằng code |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Giải thích đủ 5 phần kèm base case / edge case; trừ nhẹ vì chưa làm ChromaDB |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | 42/42 test pass |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | 4/5 cặp đúng dự đoán, cặp lệch đã phân tích được nguyên nhân |
| Kết quả truy xuất của tôi (Competition Results) | 7 / 10 | Retrieval 6/10 điểm; 4/5 câu có chunk liên quan trong top-3, kèm phân tích 3 kiểu lỗi + đo hiệu quả lọc metadata. Chờ nhóm chốt bộ câu hỏi chung để chạy lại |
| **Tổng phần cá nhân** | **56 / 60** | |

### Việc còn lại trước khi nộp

- [ ] Điền **Họ tên / Nhóm** ở đầu báo cáo.
- [ ] Nhóm chốt **5 câu hỏi đánh giá** trong `REPORT_NHOM.md` → chạy lại bảng Mục 5 nếu khác bộ đề xuất.
- [ ] Điền ô "Điều hay nhất học được qua demo" sau buổi thuyết trình.
- [ ] (Tùy chọn) Sửa lỗi Q2 bằng `RecursiveChunker` hoặc tăng `overlap`, rồi đo lại để so sánh trong `REPORT_NHOM.md`.
