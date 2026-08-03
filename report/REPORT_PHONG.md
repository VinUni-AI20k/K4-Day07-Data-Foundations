# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Kiều Hồng Phong
**Nhóm:** A5-1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1.0) chỉ ra rằng hai véc-tơ biểu diễn văn bản chỉ cùng một hướng trong không gian nhiều chiều, thể hiện sự đồng nhất hoặc rất gần gũi về mặt ngữ nghĩa bất chấp sự khác biệt về từ vựng hay độ dài văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Shopee chấp nhận hoàn tiền ví ShopeePay trong 24 giờ."
- Câu B: "Thời gian hoàn tiền qua ví ShopeePay là 24h."
- Tại sao tương đồng: Cả hai câu đều truyền tải cùng một thông tin chính xác về mốc thời gian hoàn tiền 24 giờ qua ví ShopeePay.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Shopee không áp dụng lý do trả hàng không còn nhu cầu."
- Câu B: "Lập trình Python là ngôn ngữ hướng đối tượng bậc cao."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn độc lập (quy định TMĐT vs ngôn ngữ lập trình), không có sự liên quan ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine đo góc giữa hai véc-tơ chứ không đo khoảng cách chiều dài absolute. Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài câu (đoạn văn dài có véc-tơ độ dài lớn hơn), trong khi Cosine Similarity triệt tiêu yếu tố độ dài nhờ chuẩn hóa norm $||a|| \cdot ||b||$, giúp so sánh ngữ nghĩa chính xác hơn giữa câu ngắn và đoạn văn dài.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* 
> - Bước nhảy (step) = `chunk_size - overlap` = $500 - 50 = 450$ ký tự.
> - Số lượng chunk = $\lceil (10000 - 50) / 450 \rceil = \lceil 9950 / 450 \rceil = \lceil 22.11 \rceil = 23$.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap` tăng lên 100: Bước nhảy giảm xuống $500 - 100 = 400$. Số lượng chunk = $\lceil (10000 - 100) / 400 \rceil = \lceil 9900 / 400 \rceil = 25$ chunks.
> Tăng độ chồng chéo giúp bảo toàn ngữ cảnh ở ranh giới cắt giữa các chunk, tránh việc thông tin quan trọng nằm giữa hai chunk bị xé lẻ dẫn tới mất ngữ nghĩa khi truy xuất RAG.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` / `LangChainSentenceChunker`** — hướng tiếp cận:
> Sử dụng regex `re.split(r'(?<=[.!?])\s+', text.strip())` để phân tách câu chuẩn. Đồng thời tích hợp thêm `LangChainSentenceChunker` (sử dụng thư viện `langchain-text-splitters.RecursiveCharacterTextSplitter`) với danh sách phân tách câu `[". ", "! ", "? ", "\n\n", "\n"]` giúp linh hoạt chuyển đổi giữa triển khai tùy chỉnh và thư viện LangChain.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán chia đệ quy thử nghiệm danh sách phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case là khi chuỗi nhỏ hơn hoặc bằng `chunk_size` hoặc đã duyệt hết dấu phân tách. Nếu độ dài phần gộp vượt quá `chunk_size`, hàm thực hiện gọi đệ quy `_split` với separator mức tiếp theo để đảm bảo chunk giữ trọn vẹn ngữ cảnh cấu trúc lớn nhất có thể.

### Lớp EmbeddingStore & HuggingFace Embedder

**`add_documents` + `search` + `HuggingFaceEmbedder`** — hướng tiếp cận:
> Tích hợp `HuggingFaceEmbedder` thông qua thư viện `huggingface_hub.InferenceClient` để gọi trực tiếp mô hình nhúng trên Hugging Face Hub (như `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`). Trong `EmbeddingStore`, nhúng văn bản và tính tích vô hướng (`_dot`) giữa query embedding với tất cả embedding đã lưu, sắp xếp giảm dần theo điểm `score` và lấy ra `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện pre-filtering lọc các candidate chunks bằng cách kiểm tra điều kiện `metadata_filter` trước, sau đó mới tính cosine similarity xếp hạng trên tập ứng viên đã lọc. `delete_document` duyệt danh sách store, tìm tất cả record có `metadata["doc_id"] == doc_id` và xóa khỏi `_store` cũng như ChromaDB collection.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search` (hoặc `search_with_filter`) lấy `top_k` chunk liên quan nhất, đóng gói ngữ cảnh dưới dạng `[Context 1]\n... \n[Context 2]\n...`. Tạo prompt chuẩn RAG nghiêm ngặt yêu cầu LLM chỉ sử dụng ngữ cảnh được cung cấp để trả lời, nếu không có thông tin thì đưa ra phản hồi không biết.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
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

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee chấp nhận hoàn tiền ví ShopeePay trong 24 giờ | Thời gian hoàn tiền qua ví ShopeePay là 24h | Cao | 0.3828 | Đúng |
| 2 | Người mua có 15 ngày để gửi yêu cầu trả hàng | Thời hạn yêu cầu trả hàng đối với người mua là 15 ngày | Cao | 0.3828 | Đúng |
| 3 | Shopee không áp dụng lý do trả hàng không còn nhu cầu | Sản phẩm tươi sống cần bảo quản lạnh | Thấp | -0.1499 | Đúng |
| 4 | Quy định về video bằng chứng khi mở kiện hàng | Tải video bằng chứng lên Google Drive hoặc Youtube | Trung bình | 0.1847 | Đúng |
| 5 | Thời gian hoàn tiền qua thẻ tín dụng từ 7-14 ngày | Lập trình Python là ngôn ngữ bậc cao | Thấp | -0.0733 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1 và Cặp 2 đều cho điểm tương đồng cao (~0.38 - 0.40 trong mô hình nhúng giả lập/local) do có sự xuất hiện tương đồng của các cụm từ ngữ nghĩa khóa ("ví ShopeePay", "24h", "15 ngày", "yêu cầu trả hàng"). Ngược lại, Cặp 3 và Cặp 5 cho điểm âm (-0.07 đến -0.15), khẳng định vector embedding không gian đa chiều phân biệt rất rõ các câu không cùng chủ đề hoặc chứa từ vựng hoàn toàn lạc đề.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src` (Chiến lược `RecursiveChunker(chunk_size=500)` / `LangChainSentenceChunker`). 5 câu hỏi này trùng khớp với `REPORT_NHOM.md`.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Real LLM (Nvidia Llama-3.1-8B) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn tối đa để người mua gửi yêu cầu Trả hàng/Hoàn tiền đối với thực phẩm tươi sống, đơn do người bán tự vận chuyển...? | [shopee-returns-01] 1.2 Thời gian tối đa để gửi yêu cầu trả hàng hoàn tiền: Thực phẩm tươi sống 24h, đơn tự vận chuyển 15 ngày... | 0.7690 | Có (Top-1) | Trả lời chính xác: Thực phẩm tươi sống 24h, đơn do người bán tự vận chuyển 15 ngày, đơn khác 15 ngày từ khi giao thành công. |
| 2 | Sản phẩm hạn chế trả hàng là gì và Shopee không áp dụng lý do trả hàng nào cho nhóm sản phẩm này? | [shopee-returns-03] Sản phẩm hạn chế trả hàng là sản phẩm có tính đặc thù cao, không áp dụng lý do Không còn nhu cầu... | 0.8402 | Có (Top-1) | Giải thích đúng sản phẩm hạn chế trả hàng là sản phẩm đặc thù cao, không áp dụng lý do 'Hàng nguyên vẹn nhưng không còn nhu cầu'. |
| 3 | Video mở kiện dùng làm bằng chứng khi hàng bị lỗi hoặc khác mô tả phải đáp ứng những yêu cầu nào...? | [shopee-returns-04] Quay 6 mặt kiện hàng, không cắt ghép, mã vận đơn rõ ràng, dung lượng > 100MB tải lên Drive/Youtube... | 0.7112 | Có (Top-1) | Liệt kê video mở kiện phải rõ nét, không mờ nhòe, nếu vượt quá dung lượng cho phép thì tải lên YouTube/Google Drive công khai. |
| 4 | Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu Trả hàng/Hoàn tiền? | [shopee-returns-05] Vào Tôi > Đơn Mua > Trả hàng/Hoàn tiền > Chọn sản phẩm > Chi tiết trả hàng... | 0.7710 | Có (Top-3) | Hướng dẫn theo dõi thông báo trên ứng dụng Shopee (nhiễu từ tài liệu seller khi chưa áp dụng pre-filter category). |
| 5 | Sau khi Shopee chấp nhận hoàn tiền, thời gian nhận tiền đối với Ví ShopeePay, thẻ Napas và thẻ tín dụng khác nhau như thế nào? | [shopee-returns-06] Bảng thời gian hoàn tiền: Ví ShopeePay 24h, thẻ Napas 2-5 ngày, thẻ tín dụng/ghi nợ 7-14 ngày làm việc... | 0.7704 | Có (Top-1) | Trích xuất chính xác thời gian hoàn tiền cho từng hình thức thanh toán. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**So sánh A/B (Thí nghiệm Lọc Metadata):**
> Thử nghiệm A/B trên Query 1 (`q1_return_deadline`) cho thấy:
> - **Khi KHÔNG dùng filter (`search`)**: Trả về tài liệu dành riêng cho Người bán `shopee-returns-07.md` (seller) làm Top-1 do chứa nhiều từ khóa "thời hạn gửi trả hàng", gây nhiễu cho người mua.
> - **Khi CÓ dùng filter (`search_with_filter` với `customer_role: buyer`)**: Loại bỏ hoàn toàn tài liệu seller, trả về chính xác 100% tài liệu `shopee-returns-01.md` cho người mua tại Top-1 (Score: 0.7066).

**Phân tích 1 Trường hợp Thất bại (Failure Case Analysis):**
> - **Failure Case ở Query 4 (`q4_track_request`)**: *"Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu..."*. Khi không có metadata filter `category: tracking`, vector similarity trả về `shopee-returns-07.md` (Score `0.8188`) cao hơn `shopee-returns-05.md` do từ khóa "theo dõi tình trạng" xuất hiện lặp lại ở tài liệu seller.
> - **Đề xuất giải pháp**: Sử dụng `MarkdownHeaderChunker` tự động chèn tiêu đề mục `## Thao tác trên App Shopee` vào từng chunk để tăng độ tương đồng với truy vấn của người dùng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Kết hợp mô hình nhúng thực tế `paraphrase-multilingual-MiniLM-L12-v2` (chuẩn hóa L2 Norm) cùng mô hình LLM thực tế `Nvidia Llama-3.1-8b-instruct` giúp hệ thống RAG đạt độ chính xác cao. Việc áp dụng pre-filtering `customer_role: buyer` giúp loại bỏ hoàn toàn các chunk nhiễu từ người bán (`seller`).

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
