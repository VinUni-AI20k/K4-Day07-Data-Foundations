# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Hải
**Nhóm:** T-Hexa
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*

**Ví dụ có độ tương tự CAO:**
- Câu A: What is your age?
- Câu B: How old are you?
- Tại sao tương đồng: cả hai đều liên quan đến việc hỏi tuổi, về mặt ngữ nghĩa sẽ gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: I agree with you
- Câu B: I agree to you
- Tại sao khác: Vì 2 câu này khác nhau về mặt ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* cosine sẽ tốt hơn Euclidean vì chỉ quan tâm đến góc, do đó không bị ảnh hưởng bởi độ dài vector. Ngoài ra, khi vector cao chiều, Euclidean sẽ khiến tất cả vector đều xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* làm tròn lên((doc-overlap)/(chunk-overlap))
> *Đáp án:* 23

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* 25. Độ chồng chéo cao hơn thì mỗi câu sẽ giữ nhiều context của các câu trước và sau nó, đồng thời cũng giảm được các chunk bị cắt dẫn đến mất nghĩa

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split(r'\.\s|!\s|\?\s|\.\n', text)` để tách văn bản thành từng câu riêng lẻ, sau đó `strip()` và loại bỏ chuỗi rỗng. Sau khi có danh sách câu, gom từng nhóm `max_sentences_per_chunk` câu liên tiếp lại thành một chunk bằng cách duyệt theo bước nhảy (`range(0, len(sentences), max_sentences_per_chunk)`) và nối lại bằng khoảng trắng. Edge case xử lý: text rỗng trả về `[]`; nếu số câu không chia hết cho `max_sentences_per_chunk` thì chunk cuối chứa phần dư ít câu hơn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử lần lượt các separator theo thứ tự ưu tiên (`\n\n` → `\n` → `. ` → ` ` → `""`). Base case: nếu `len(current_text) <= chunk_size` thì trả về `[current_text]` luôn (không cần tách nữa). Nếu tách bằng separator hiện tại không tìm thấy dấu phân cách (`len(parts) == 1`), chuyển sang thử separator tiếp theo trên cùng đoạn văn bản. Nếu tìm thấy, các phần được gộp dần vào một chunk cho tới khi vượt `chunk_size`, phần nào bản thân nó vẫn quá dài thì tiếp tục đệ quy với danh sách separator còn lại; separator `""` (rỗng) là fallback cuối cùng, cắt cứng theo số ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa qua `_make_record()` thành một dict gồm `id`, `content`, `metadata` và `embedding` (embedding tính ngay bằng `embedding_fn` khi thêm vào, không tính lại lúc search). Bản ghi được append vào `self._store` (in-memory); nếu ChromaDB có sẵn thì đồng thời ghi thêm sang collection (best-effort, không bắt buộc để hoạt động đúng). `search()` embed câu truy vấn rồi tính dot product (`_dot`) giữa vector truy vấn và từng embedding đã lưu, sắp xếp giảm dần theo điểm số và cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc metadata trước, search sau: `search_with_filter` duyệt `self._store`, chỉ giữ lại các record thỏa mọi cặp key-value trong `metadata_filter`, rồi mới chạy hàm tính similarity dùng chung (`_search_records`) trên tập đã lọc — tránh việc phải tính điểm cho toàn bộ store rồi mới loại bỏ. `delete_document(doc_id)` coi một record thuộc về `doc_id` nếu `record["id"] == doc_id` HOẶC `record["metadata"].get("doc_id") == doc_id` (để vừa xóa được document gốc, vừa xóa được các chunk đã gắn `doc_id` qua `ingest.py`); trả về `True`/`False` tùy có record nào khớp hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer()` gọi `store.search(question, top_k=top_k)` để lấy các chunk liên quan, đánh số từng chunk (`[1]`, `[2]`, ...) rồi nối thành một khối "Ngữ cảnh". Prompt cuối cùng gồm 3 phần rõ ràng: hướng dẫn cho LLM (trả lời dựa trên ngữ cảnh, nói rõ nếu thiếu thông tin), khối ngữ cảnh, và câu hỏi gốc — sau đó prompt này được truyền cho `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.10.12, pytest-9.1.1, pluggy-1.6.0
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

============================== 42 passed in 0.32s ===============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn đổi trả sản phẩm vì không đúng như mô tả. | Tôi cần hoàn trả hàng do sản phẩm sai với thông tin quảng cáo. | cao (paraphrase) | 0.6162 | Đúng |
| 2 | Đơn hàng của tôi khi nào được giao? | Bao lâu thì tôi nhận được hàng đã đặt? | cao (paraphrase) | 0.7284 | Đúng |
| 3 | Chính sách bảo mật thông tin khách hàng được quy định như thế nào? | Con mèo của tôi thích ngủ trên ghế sofa vào buổi chiều. | thấp (khác chủ đề hoàn toàn) | -0.0112 | Đúng |
| 4 | Người bán phải xác nhận đơn hàng trong 24 giờ. | Người mua có thể hủy đơn hàng trong 24 giờ đầu tiên. | thấp/trung bình (trùng từ khóa "đơn hàng", "24 giờ" nhưng khác chủ thể & hành động) | 0.8067 | Sai — điểm lại cao hơn cả 2 cặp paraphrase (1, 2) |
| 5 | Phương thức thanh toán được chấp nhận gồm thẻ tín dụng và ví điện tử. | Sản phẩm lỗi được đổi mới trong vòng 30 ngày kể từ ngày mua. | thấp (cùng chủ đề TMĐT nhưng khác chủ đề con: thanh toán vs đổi trả) | 0.1767 | Đúng |

> Kết quả trên chạy bằng `LocalEmbedder` (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, qua `EMBEDDING_PROVIDER=local`).

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 4: dự đoán điểm thấp/trung bình vì hai câu khác chủ thể (người bán xác nhận đơn vs người mua hủy đơn) và khác hành động, nhưng điểm thực tế (0.8067) lại cao hơn cả hai cặp paraphrase (1, 2). Điều này cho thấy embedding ngữ nghĩa vẫn thiên nhiều về cấu trúc câu và từ vựng chung ("đơn hàng", "24 giờ", cùng khuôn mẫu "X có thể/phải Y trong 24 giờ") hơn là phân biệt chính xác vai trò chủ thể (người bán vs người mua) hay bản chất hành động (xác nhận vs hủy). Điều này củng cố lý do vì sao K4 yêu cầu thêm metadata `customer_role` (buyer/seller) — vì bản thân embedding không đủ để tách hai câu chính sách áp dụng cho hai vai trò khác nhau, cần lọc metadata mới đảm bảo đúng ngữ cảnh.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

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
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | — / 10 |
| **Tổng phần cá nhân** | **60 / 60 ** |
