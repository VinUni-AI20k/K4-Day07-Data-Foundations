# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trịnh Hải Đăng 

Mã học viên: 2A202601602
**Nhóm:** B7-E402
**Ngày: Thứ 2 ngày 3 tháng 8 năm 2026**

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

Hai vector embedding chỉ cùng một *hướng* trong không gian nhiều chiều, bất kể độ dài (magnitude) của chúng — nói cách khác, hai đoạn văn bản mang cùng nội dung/ý nghĩa ngữ nghĩa, dù cách diễn đạt câu chữ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Đơn hàng của tôi bị giao chậm."
- Câu B: "Đơn hàng của tôi đến trễ hơn dự kiến."
- Tại sao tương đồng: cùng diễn đạt một ý — việc giao hàng không đúng hẹn — chỉ khác từ ngữ ("giao chậm" vs "đến trễ").

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Đơn hàng của tôi bị giao chậm."
- Câu B: "Tôi muốn đổi màu sản phẩm khác."
- Tại sao khác: chủ đề hoàn toàn khác nhau — một câu về vận chuyển/giao hàng trễ, một câu về đổi thuộc tính sản phẩm.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**

Độ dài (norm) của vector embedding thường bị ảnh hưởng bởi độ dài văn bản/tần suất từ chứ không phản ánh ngữ nghĩa, nên khoảng cách Euclid có thể đánh giá sai hai văn bản cùng chủ đề nhưng độ dài khác nhau là "xa nhau". Cosine similarity chỉ quan tâm góc giữa hai vector (hướng biểu diễn ngữ nghĩa) nên không bị lệch bởi magnitude, phù hợp hơn khi so sánh ý nghĩa văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Công thức: `số lượng chunk = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))`
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> **Đáp án: 23 chunks** (đã kiểm tra khớp với `FixedSizeChunker(chunk_size=500, overlap=50)` thực tế trong `src/chunking.py`)

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks — tăng từ 23 lên **25 chunks** (đã kiểm tra khớp thực tế). Tăng overlap làm bước trượt (`chunk_size - overlap`) nhỏ lại nên cần nhiều cửa sổ hơn để phủ hết văn bản → nhiều chunk hơn. Lý do muốn overlap lớn hơn: tránh việc một câu/ý quan trọng bị cắt đúng ngay ranh giới giữa hai chunk (mất ngữ cảnh), giúp truy xuất (retrieval) không bỏ sót thông tin nằm vắt qua điểm cắt — đổi lại là tốn thêm dung lượng lưu trữ và thời gian embed do có nhiều chunk trùng lặp nội dung hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Dùng regex `(?<=[.!?])\s+` (lookbehind sau dấu `.`, `!`, `?`) để tách văn bản thành danh sách câu, sau đó strip khoảng trắng thừa và loại câu rỗng. Nhóm các câu liên tiếp thành từng chunk theo `max_sentences_per_chunk` bằng cách duyệt theo bước nhảy (`range(0, len(sentences), max_sentences_per_chunk)`) rồi nối lại bằng khoảng trắng. Trường hợp biên: văn bản rỗng trả về `[]`; văn bản không có dấu câu vẫn được coi là 1 "câu" duy nhất nhờ regex không match, tránh lỗi chia cho 0 hay list rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

`chunk()` gọi `_split(text, self.separators)`. Thuật toán đệ quy: base case là khi `len(current_text) <= chunk_size` → trả về nguyên đoạn text đó (hoặc `[]` nếu rỗng); khi hết separator để thử (`remaining_separators` rỗng) hoặc separator hiện tại là chuỗi rỗng `""`, cắt thẳng theo `chunk_size` ký tự liên tiếp. Ở bước đệ quy chính: tách `current_text` theo separator đầu tiên; nếu separator đó không xuất hiện trong text (`len(parts) == 1`) thì bỏ qua, thử separator kế tiếp; nếu có, gộp dần các `parts` vào một chunk cho tới khi vượt `chunk_size` thì chốt chunk đó lại và đệ quy tiếp với phần còn dư quá lớn bằng separator tiếp theo (rest). Cách này đảm bảo ưu tiên cắt tại ranh giới ngữ nghĩa lớn (đoạn văn `\n\n`) trước khi cắt nhỏ hơn (câu, từ, ký tự).

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

`_make_record()` chuẩn hóa mỗi `Document` thành một dict gồm `id`, `content`, `metadata` (đã gắn thêm `doc_id` nếu chưa có) và `embedding` (gọi `self._embedding_fn(doc.content)`). `add_documents()` duyệt từng doc, tạo record rồi append vào list `self._store` (đồng thời ghi qua ChromaDB nếu thư viện có sẵn — fallback về in-memory nếu không). `search()` gọi `_search_records()`: embed câu query, tính tích vô hướng (`_dot`) giữa vector query và từng vector đã lưu, sort giảm dần theo score rồi cắt lấy `top_k` phần tử đầu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

`search_with_filter()` lọc **trước khi** tìm kiếm: nếu có `metadata_filter`, chỉ giữ lại các record mà toàn bộ cặp key-value trong filter khớp với `record["metadata"]` (dùng `all(...)` để yêu cầu khớp tất cả điều kiện), sau đó mới chạy `_search_records()` trên tập đã lọc — cách này tránh phải tính similarity cho các chunk chắc chắn không thuộc phạm vi cần lọc. `delete_document()` xây list mới chỉ giữ lại các record có `metadata["doc_id"] != doc_id`, so sánh độ dài trước/sau để biết có phần tử nào bị xóa hay không rồi gán lại `self._store`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

`answer()` gọi `self._store.search(question, top_k=top_k)` để lấy các chunk liên quan nhất, nối nội dung các chunk lại bằng `"\n\n"` thành một khối `context`. Prompt được dựng theo cấu trúc cố định: hướng dẫn ngắn ("chỉ trả lời dựa trên ngữ cảnh"), rồi tới `Context:`, `Question:`, `Answer:` — buộc mô hình chỉ dùng thông tin đã truy xuất thay vì tự bịa. Cuối cùng gọi `self._llm_fn(prompt)` và trả thẳng kết quả string.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 42 items

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

============================= 42 passed in 0.13s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Chạy bằng `_mock_embed` (trình nhúng giả lập mặc định của lab, chưa cài `sentence-transformers`).

| Cặp | Câu A | Câu B | Dự đoán  | Điểm thực tế | Đúng? |
| ---- | ------ | ------ | ----------- | ---------------- | ------- |
| 1 | "Đơn hàng của tôi bị giao chậm." | "Đơn hàng của tôi đến trễ hơn dự kiến." | cao | 0.1834 | Không rõ ràng |
| 2 | "Đơn hàng của tôi bị giao chậm." | "Tôi muốn đổi màu sản phẩm khác." | thấp | 0.3224 | Sai |
| 3 | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Người bán cần mô tả đúng sự thật về hàng hóa." | cao | -0.0576 | Sai |
| 4 | "Người bán phải cung cấp thông tin sản phẩm chính xác." | "Hôm nay trời Hà Nội mưa to." | thấp | -0.0631 | Đúng (tình cờ) |
| 5 | "Shopee hỗ trợ thanh toán khi nhận hàng (COD)." | "Có thể trả tiền mặt lúc nhận hàng trên Shopee không?" | cao | -0.1109 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

Bất ngờ nhất là cặp 2: hai câu hoàn toàn không liên quan ("giao hàng chậm" vs "đổi màu sản phẩm") lại có điểm cao hơn (0.3224) so với cặp 1 vốn diễn đạt cùng một ý (0.1834) — đúng như cảnh báo trong README: `_mock_embed` sinh vector "gần như ngẫu nhiên theo cả chuỗi" (dựa trên hash MD5 của chuỗi ký tự) chứ không mã hóa ngữ nghĩa thật, nên điểm số của nó không phản ánh mức độ giống nhau về ý nghĩa — chỉ dùng được để kiểm thử code (unit test), không dùng để đánh giá chất lượng chunking/retrieval tiếng Việt. Để dự đoán có ý nghĩa thật, cần chạy lại với `EMBEDDING_PROVIDER=local` (embedder đa ngữ) — việc này em sẽ làm ở bước so sánh chiến lược cùng nhóm.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

> Nhóm **chưa hoàn tất** thống nhất 5 câu hỏi đánh giá chính thức (Bước 6, `REPORT_NHOM.md` Phần 3). Dưới đây là 5 câu hỏi **em tự đề xuất** trên bộ 10 tài liệu Shopee đã thu thập (`data/k4_ecommerce/`), dùng tạm để kiểm tra code cá nhân chạy được — **sẽ cập nhật lại bảng này khi nhóm chốt bộ câu hỏi chung**, theo đúng yêu cầu "5 câu hỏi phải trùng với các thành viên cùng nhóm". Chạy với `FixedSizeChunker(chunk_size=300, overlap=40)` + `_mock_embed`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
| - | ----------------- | ------------------------------------------ | ------------ | --------------------------------- | ------------------------------------- |
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng/hoàn tiền kể từ khi giao hàng thành công? | `seller-listing-rules`: "...giá cả/chất lượng với sản phẩm của người bán khác..." | 0.3458 | Không | Trích sai đoạn quy định đăng bán, không liên quan đến hạn trả hàng |
| 2 | Shopee hỗ trợ những phương thức thanh toán nào? | `shipping-fee-discount-program`: "...gắn nhãn Freeship, người mua được giảm phí vận chuyển..." | 0.2226 | Không | Trả lời về ưu đãi phí vận chuyển, không phải danh sách phương thức thanh toán (dù `payment-methods` có mặt ở top-3, chỉ xếp hạng 3) |
| 3 | Người bán không được đăng bán loại sản phẩm nào theo quy định? *(metadata_filter={"customer_role": "seller"})* | `shipping-fee-discount-program`: "...gắn nhãn Freeship..." | 0.2313 | Không (dù đã lọc đúng seller, top-1 vẫn sai chủ đề) | Nội dung không liên quan tới danh mục sản phẩm cấm |
| 4 | Shopee thu thập những loại dữ liệu cá nhân nào của người dùng? | `restricted-products-policy`: "...tịch thu số dư tài khoản..." | 0.2343 | Không | Trả lời về xử phạt vi phạm sản phẩm, không phải về thu thập dữ liệu cá nhân |
| 5 | Phí dịch vụ của chương trình ưu đãi phí vận chuyển dành cho người bán là bao nhiêu? *(metadata_filter={"customer_role": "seller"})* | `seller-listing-rules`: "...Đăng ngày 14/08/2024..." | 0.0501 | Không | Trả lời sai tài liệu (đúng ra phải lấy từ `shipping-fee-discount-program`) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 0 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> *Sẽ bổ sung sau buổi demo với nhóm — chưa diễn ra tại thời điểm viết báo cáo này.*

> **Ghi chú quan trọng:** Kết quả 0/5 ở trên **là hệ quả trực tiếp của việc dùng `_mock_embed`** (vector gần như ngẫu nhiên theo hash chuỗi, không mã hóa ngữ nghĩa) — đúng như cảnh báo của README/exercises.md rằng mock "không nên dùng để kết luận chiến lược nào tốt hơn". Đây là bằng chứng thực nghiệm cho thấy retrieval bằng mock hoàn toàn không dùng được để đánh giá chất lượng, và là lý do bắt buộc phải chạy lại toàn bộ bảng này với `EMBEDDING_PROVIDER=local` (embedder đa ngữ thật) trước khi nộp điểm chính thức — việc này nằm ở Bước 5 trong `PLAN.md`, thực hiện cùng lúc so sánh chiến lược chunking với nhóm.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí                                           | Điểm tự đánh giá |
| ---------------------------------------------------- | ---------------------- |
| Khởi động (Warm-up)                               | 5 / 5                    |
| Hướng tiếp cận của tôi (My Approach)           | 10 / 10                   |
| Hoàn thiện code (Core Implementation — tests)     | 30 / 30                   |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5                    |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 (đã chạy đủ quy trình, nhưng retrieval chưa đạt vì dùng mock; cần re-run với embedder thật + bộ câu hỏi chính thức của nhóm) |
| **Tổng phần cá nhân**                      | **53 / 60** (tạm tính, sẽ tăng lên sau khi cập nhật Phần 5 với embedder thật + câu hỏi nhóm) |
