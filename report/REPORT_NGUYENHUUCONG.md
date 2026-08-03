# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hữu Công
**Mã lớp/thành viên:** congnh-01732
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> Mã nguồn cá nhân đặt tại `src/congnh-01732/` (bản sao độc lập của gói `src`, tự implement các TODO).

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn bản có độ tương tự cosine cao nghĩa là hai vector embedding của chúng hướng gần như cùng một phương trong không gian vector, tức **ý nghĩa/chủ đề của hai đoạn văn bản rất gần nhau** (giá trị cosine tiến về 1). Độ dài văn bản không ảnh hưởng đến kết luận này, vì cosine chỉ đo góc giữa hai vector chứ không đo khoảng cách tuyệt đối.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn trả lại sản phẩm đã mua hôm qua."
- Câu B: "Tôi cần hoàn trả món hàng vừa đặt."
- Tại sao tương đồng: cùng ý định đổi trả/hoàn hàng, cùng ngữ cảnh mua sắm TMĐT; từ khóa tuy khác nhau ("trả lại sản phẩm" ≈ "hoàn trả món hàng") nhưng embedding đa ngữ ánh xạ chúng về gần nhau trong không gian ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi muốn trả lại sản phẩm đã mua hôm qua."
- Câu B: "Dự báo thời tiết ngày mai có mưa rào rải rác."
- Tại sao khác: hai chủ đề hoàn toàn không liên quan (đổi trả hàng hóa vs. thời tiết), hầu như không chung từ vựng lẫn ngữ nghĩa → vector gần như trực giao, cosine tiến về 0.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Ý nghĩa của embedding nằm ở **hướng** của vector, không phải độ lớn. Cosine chỉ đo hướng nên bất biến với độ dài văn bản/tần số từ (một câu ngắn và một đoạn dài cùng chủ đề vẫn có cosine cao); ngược lại Euclid bị chi phối bởi độ lớn vector, khiến hai văn bản cùng nghĩa nhưng khác độ dài bị tính là "xa nhau".

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Công thức: `số chunk = ceil((độ_dài − overlap) / (chunk_size − overlap))`
> = ceil((10000 − 50) / (500 − 50)) = ceil(9950 / 450) = ceil(22.11)
> *Đáp án:* **23 chunks**. (Bước trượt thực tế là 500 − 50 = 450 ký tự; đã kiểm chứng bằng `FixedSizeChunker(500, 50)` trên chuỗi 10,000 ký tự → ra đúng 23.)

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng thành ceil((10000 − 100) / (500 − 100)) = ceil(9900 / 400) = ceil(24.75) = **25 chunks** (đã kiểm chứng bằng code). Tăng overlap làm bước trượt giảm (450 → 400) nên cần nhiều cửa sổ hơn để phủ kín tài liệu. Lợi ích: phần ngữ cảnh ở ranh giới giữa hai chunk được lặp lại ở cả hai chunk, giúp **không mất thông tin khi một câu/ý nằm vắt ngang điểm cắt** — đổi lại là tốn bộ nhớ và tăng khả năng truy xuất trùng lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận khi lập trình (implement) các phần chính trong gói `src/congnh-01732`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex lookbehind `(?<=[.!?])\s` để tách văn bản tại vị trí ngay sau dấu `.`, `!`, `?` khi theo sau là ký tự whitespace — cách này phủ đủ các mẫu `". "`, `"! "`, `"? "` và `".\n"` trong docstring mà vẫn giữ dấu câu dính liền với câu của nó. Các trường hợp ngoại lệ được xử lý: văn bản rỗng/trắng → trả về `[]`; mảnh rỗng sinh ra sau dấu chấm cuối câu (do văn bản kết thúc bằng `". "`) bị lọc bỏ; mỗi câu được `strip()` trước khi ghép nhóm tối đa `max_sentences_per_chunk` câu thành một chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy theo chiến lược "chia theo dấu phân cách thô trước, mịn sau": lấy dấu phân cách đầu tiên trong danh sách còn lại để cắt văn bản, các mảnh đủ nhỏ được gom tham lam vào chunk hiện tại, mảnh nào vượt `chunk_size` thì đệ quy với các dấu phân cách mịn hơn (`remaining_separators[1:]`). Base case: văn bản rỗng, hoặc đã ≤ `chunk_size` (trả về nguyên khối), hoặc hết dấu phân cách / gặp `""` thì cắt cứng theo kích thước — nhờ vậy hàm không bao giờ lỗi kể cả khi `separators=[]`. Một chi tiết cố ý: dấu phân cách được giữ dính vào cuối mỗi mảnh (trừ mảnh cuối) để không mất dấu chấm/xuống dòng ở ranh giới chunk.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa thành một bản ghi `{id, content, embedding, metadata}` qua `_make_record`, trong đó `doc.id` được gắn thêm vào metadata dưới khóa `doc_id` (phục vụ lọc/xóa sau này) và `id` bản ghi có thêm số thứ tự để không đụng độ khi thêm nhiều chunk của cùng tài liệu. `search` nhúng truy vấn bằng cùng `embedding_fn`, chấm điểm bằng tích vô hướng (`_dot`) với từng embedding lưu trữ — vì mock/local embedder đều trả vector chuẩn hóa nên tích vô hướng chính là cosine — rồi sắp xếp giảm dần và lấy top-k. Store có hai backend: ChromaDB ephemeral (không gian `cosine`, điểm = `1 − distance`) nếu cài được, ngược lại fallback in-memory; mỗi instance dùng tên collection vật lý riêng (thêm số thứ tự) vì storage ephemeral của chromadb dùng chung theo tên trong cùng tiến trình.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc **trước**, tìm kiếm **sau** (pre-filter): chỉ giữ các bản ghi có metadata khớp *tất cả* cặp khóa–giá trị của `metadata_filter`, rồi chạy tìm kiếm tương tự trên tập đã lọc — tập ứng viên nhỏ hơn nên rẻ hơn và không bao giờ trả về kết quả sai vai trò; khi filter là `None` thì hành vi giống hệt `search`. `delete_document` duyệt và giữ lại mọi bản ghi có `metadata['doc_id']` khác `doc_id` cần xóa (một tài liệu gốc có thể thành nhiều chunk nên phải xóa theo `doc_id` chứ không theo `id` bản ghi), trả về `True/False` dựa trên việc kích thước bộ nhớ có giảm hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Đi đúng 3 bước RAG: (1) gọi `store.search(question, top_k)` để truy xuất các chunk liên quan nhất; (2) dựng prompt gồm chỉ dẫn "chỉ trả lời theo ngữ cảnh, không có thì nói rõ", tiếp đến là các chunk đánh số `[Đoạn 1]`, `[Đoạn 2]`… nối bằng dòng trống làm ngữ cảnh, rồi đến câu hỏi; (3) truyền prompt cho `llm_fn` và trả về kết quả. Nếu store rỗng, ngữ cảnh được thay bằng câu thông báo "không truy xuất được" để LLM không bịa câu trả lời (giảm hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

Lệnh chạy (gói cá nhân được chọn qua biến môi trường): `LAB_SOLUTION_PACKAGE="src.congnh-01732" pytest tests/ -v`

```
============================= test session starts ==============================
platform linux -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /var/home/nguyenhuucong/PycharmProjects/K4-Day07-Data-Foundations-B1-2
configfile: pyproject.toml
plugins: anyio-4.14.2
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 13%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 18%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
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

============================== 42 passed in 1.21s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

> Ghi chú: đã chạy kiểm thử trên cả hai backend của `EmbeddingStore` — khi chưa cài `chromadb` (fallback in-memory) và sau khi `uv add chromadb` (backend ChromaDB ephemeral): cả hai đều 42/42.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Dự đoán được ghi **trước khi chạy** `compute_similarity()`. Embedding dùng để chấm điểm thực tế: `text-embedding-3-small` (OpenAI) theo cấu hình `.env` (`EMBEDDING_PROVIDER=openai`), tính cosine bằng hàm `compute_similarity` tự viết trong `src/congnh-01732` (kịch bản `evaluate_congnh.py`). Ngưỡng tôi dùng để phân loại: score ≥ 0.5 = cao, < 0.5 = thấp.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn trả lại sản phẩm vì nó bị lỗi. | Sản phẩm này bị hỏng, tôi muốn hoàn hàng. | cao (cùng ý định đổi trả, từ khóa gần nghĩa) | 0.7125 | ✅ Đúng |
| 2 | Người bán phải cung cấp thông tin sản phẩm chính xác khi đăng bán. | Khi đăng bán, người bán cần mô tả hàng hóa đúng với thực tế. | cao (paraphrase cùng một quy định) | 0.7199 | ✅ Đúng |
| 3 | Tôi muốn đổi trả đơn hàng đã mua tuần trước. | Đơn hàng của tôi dự kiến khi nào được giao? | thấp (cùng TMĐT nhưng khác ý định: đổi trả vs. giao hàng) | 0.5687 | ❌ Sai (vẫn ≥ 0.5) |
| 4 | Chính sách đổi trả yêu cầu gửi kèm bằng chứng khi hàng bị lỗi. | Hôm nay thời tiết đẹp và trời không mưa. | thấp (hai chủ đề không liên quan) | 0.2502 | ✅ Đúng |
| 5 | Tôi muốn trả lại sản phẩm đã mua hôm qua. | Tôi muốn mua thêm sản phẩm này cho bạn bè. | thấp (cùng miền từ vựng nhưng ý định ngược nhau "trả" vs. "mua thêm") | 0.6320 | ❌ Sai (cao hơn cả cặp 3) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 5: hai câu có ý định **ngược nhau** ("trả lại" vs. "mua thêm") mà vẫn được 0.6320 — cao hơn cả cặp 3 và chỉ kém cặp 1 khoảng 0.08. Nguyên nhân: embedding nén câu thành một vector thiên theo **miền từ vựng/chủ đề** (sản phẩm, mua, đơn hàng… kéo hai vector lại gần), còn sắc thái ý định hay phủ định được biểu diễn yếu hơn (chúng chỉ dịch chuyển vector một đoạn nhỏ so với lực kéo của cả miền từ vựng). Bài học rút ra: trong cùng một miền chính sách TMĐT, cosine similarity dễ đánh đồng các câu "gần chủ đề nhưng khác ý định", nên retrieval thực tế phải bổ sung chunking đủ nhỏ và metadata filtering thay vì chỉ dựa vào điểm tương tự.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong `src/congnh-01732`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

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
