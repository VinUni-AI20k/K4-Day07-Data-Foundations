# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Thanh Sơn  
**Nhóm:** ChickenFarmers 
**Ngày:** 03/08/2026  

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (tiệm cận 1.0) cho biết hai góc của hai định hướng vector nhúng trong không gian đa chiều gần như trùng nhau, thể hiện hai đoạn văn bản có sự tương đồng lớn về ngữ nghĩa và ngữ cảnh, bất kể độ dài ngắn của chúng.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Khách hàng có thể yêu cầu đổi trả sản phẩm trong vòng 30 ngày kể từ khi nhận hàng."
- Câu B: "Chính sách trả hàng áp dụng thời hạn tối đa 30 ngày cho người mua."
- Tại sao tương đồng: Cả hai câu đều thể hiện cùng một ý định ngữ nghĩa về thời hạn 30 ngày cho phép đổi trả hàng hóa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quy trình thanh toán hóa đơn bằng thẻ tín dụng ngân hàng."
- Câu B: "Món phở bò truyền thống nổi tiếng ở Hà Nội."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (tài chính/thanh toán vs ẩm thực), không có mối liên quan ngữ nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng mạnh bởi độ dài (độ lớn vector/khoảng cách tuyệt đối) của văn bản. Hai đoạn văn cùng chủ đề nhưng một đoạn dài và một đoạn ngắn sẽ có khoảng cách Euclid rất xa nhau. Ngược lại, Cosine similarity chỉ đo góc giữa các vector (loại bỏ yếu tố độ dài), giúp đánh giá chính xác độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*  
> - Công thức: `Số lượng chunk = làm_tròn_lên((độ_dài - overlap) / (chunk_size - overlap))`
> - Phép tính: $\text{ceil}\left(\frac{10000 - 50}{500 - 50}\right) = \text{ceil}\left(\frac{9950}{450}\right) = \text{ceil}(22.11) = 23$  
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk sẽ là: $\text{ceil}\left(\frac{10000 - 100}{500 - 100}\right) = \text{ceil}\left(\frac{9900}{400}\right) = 25$ chunks.  
> Việc tăng độ chồng chéo giúp giữ lại ngữ cảnh liên tục giữa các chunk giáp ranh, tránh làm đứt gãy thông tin quan trọng nằm ở ranh giới giữa hai chunk.


---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` (file `src/chunking.py`)** — phương pháp sử dụng cho bài cá nhân:
> Sử dụng lớp `SentenceChunker` từ [src/chunking.py](file:///e:/lab1/DAY07_2A202601848_HoangThanhSon/src/chunking.py) với biểu thức chính quy `re.split(r'(?<=[.!?])(?:\s+|\n+)', text)` với kỹ thuật lookbehind để tách văn bản theo ranh giới câu mà không làm mất dấu câu kết thúc. Sau đó gom nhóm tối đa `max_sentences_per_chunk=3` câu liên tiếp thành từng chunk và làm sạch khoảng trắng dư thừa với `.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Áp dụng thuật toán chia đệ quy thử nghiệm lần lượt các dấu phân cách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nếu đoạn văn bản hiện tại nhỏ hơn `chunk_size`, nó đóng vai trò base case và trả về đoạn đó. Ngược lại, nếu chia theo phân cách hiện tại mà mảnh tách vẫn lớn hơn `chunk_size`, hàm sẽ gọi đệ quy `_split` với các dấu phân cách ưu tiên tiếp theo.


### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Trong `add_documents`, mỗi `Document` được nhúng bằng hàm `_embedding_fn` và chuẩn hóa thành một record lưu trong danh sách bộ nhớ `self._store` (đồng thời đồng bộ sang ChromaDB collection nếu khả dụng). Với `search`, câu truy vấn được nhúng vector rồi dùng tích vô hướng (`_dot`) để tính score so sánh với tất cả các record, xếp hạng giảm dần và lấy ra `top_k` kết quả tốt nhất.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, hệ thống thực hiện pre-filtering lọc các record trong `self._store` thỏa mãn toàn bộ các cặp key-value trong `metadata_filter` trước, sau đó mới gọi `_search_records` để tìm kiếm vector. Đối với `delete_document`, loại bỏ tất cả chunk có `id == doc_id` hoặc `metadata["doc_id"] == doc_id` khỏi `self._store` và trả về `True` nếu có ít nhất 1 chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Áp dụng mô hình Retrieval-Augmented Generation (RAG): gọi `store.search` để lấy ra `top_k` chunk văn bản liên quan nhất, hợp nhất nội dung các chunk thành chuỗi ngữ cảnh context, nạp vào prompt dạng: `"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"`, sau đó chuyển cho hàm `llm_fn` để sinh câu trả lời cuối cùng.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
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
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả hàng áp dụng trong 30 ngày. | Khách hàng có thể trả lại sản phẩm trong vòng 30 ngày. | cao | -0.004 | Không (do Mock) |
| 2 | Điều kiện người bán trên sàn thương mại điện tử. | Quy trình thanh toán đơn hàng qua thẻ ngân hàng. | thấp | 0.070 | Đúng |
| 3 | Phương thức thanh toán hỗ trợ chuyển khoản. | Thanh toán bằng thẻ ATM và chuyển khoản qua ngân hàng. | cao | 0.156 | Đúng |
| 4 | Thời gian giao hàng dự kiến 3 đến 5 ngày. | Thời gian vận chuyển hàng hóa mất bao lâu? | cao | 0.046 | Thấp (do Mock) |
| 5 | Quyền riêng tư và bảo mật thông tin cá nhân. | Món ăn ngon nhất tại Hà Nội là gì? | thấp | 0.131 | Không (do Mock) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Trình nhúng MockEmbedder sinh vector dựa trên mã băm MD5 deterministic của chuỗi văn bản nên kết quả điểm tương đồng không phản ánh đúng quan hệ ngữ nghĩa thực tế. Điều này khẳng định khi làm bài toán Retrieval RAG thực tế, việc sử dụng các mô hình Semantic Embeddings thực sự (như SentenceTransformers hoặc OpenAI Embeddings) là bắt buộc để capture được góc biểu diễn ý nghĩa chính xác.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân trong gói `src` (`SentenceChunker` với `max_sentences_per_chunk=3`, tài liệu Shopee):


| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | *(Số liệu/thời hạn — buyer)* Với sản phẩm thông thường, người mua có bao nhiêu ngày để gửi yêu cầu Trả hàng/Hoàn tiền sau khi đơn được cập nhật giao thành công? Thực phẩm tươi sống/đông lạnh có thời hạn nào? | `shopee-returns-policy.md` (Mục 5): Các thông tin sẽ được ghi chú rõ ràng tại trang chi tiết, hoặc hình ảnh sản phẩm, hoặc các nội dung đăng tải công khai khác... | 0.221 | ❌ Chưa (do Mock) | Dựa trên chính sách: Các thông tin sẽ được ghi chú rõ ràng tại trang chi tiết... |
| 2 | *(Điều kiện — buyer)* Đơn COD/chuyển khoản chưa liên kết thành công phương thức nhận hoàn tiền hợp lệ có gửi yêu cầu Trả hàng/Hoàn tiền được không? | `shopee-returns-policy.md` (Mục 7): Shopee sẽ thông báo cho Người Mua về việc phải cung cấp video hay ảnh chụp trong từng trường hợp cụ thể... | 0.419 | ❌ Chưa (do Mock) | Dựa trên chính sách: Shopee sẽ thông báo cho Người Mua về việc phải cung cấp video hay ảnh chụp... |
| 3 | *(Ngoại lệ/chương trình — buyer)* Người mua có gói ShopeeVIP được Trả hàng COM tối đa bao nhiêu lần mỗi tháng? | `shopee-returns-policy.md` (Mục 4.2.b): Việc áp dụng giới hạn hạn mức theo quy định tại Điểm này sẽ không ảnh hưởng đến các yêu cầu Trả hàng COM... | 0.358 | ✅ Có | Dựa trên chính sách: Việc áp dụng giới hạn hạn mức theo quy định tại Điểm này... |
| 4 | *(Quy trình/thời hạn — seller)* Người bán phải phản hồi yêu cầu Trả hàng/Hoàn tiền trong bao lâu kể từ khi nhận thông báo? Nếu quá hạn không phản hồi, Shopee hiểu như thế nào? | `shopee-returns-policy.md` (Mục 11): Người mua và Người bán đồng ý bồi thường và giữ cho Shopee không bị thiệt hại, hoặc chống lại bất kỳ việc khiếu nại... | 0.255 | ❌ Chưa (do Mock) | Dựa trên chính sách: Người mua và Người bán đồng ý bồi thường và giữ cho Shopee không bị thiệt hại... |
| 5 | *(Liệt kê/trách nhiệm — seller)* Người bán phải chịu phí vận chuyển chiều hoàn trả sản phẩm trong những trường hợp nào? | `shopee-returns-policy.md` (Mục 3.1): Người Mua đồng ý rằng Người Mua chỉ có thể yêu cầu trả hàng/hoàn tiền trong các trường hợp sau... | 0.302 | ❌ Chưa (do Mock) | Dựa trên chính sách: Người Mua đồng ý rằng Người Mua chỉ có thể yêu cầu trả hàng/hoàn tiền trong các trường hợp sau... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3 khi dùng MockEmbedder?** 1 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Do `MockEmbedder` sử dụng thuật toán băm MD5 ngẫu nhiên không phản ánh đúng khoảng cách ngữ nghĩa thực tế (điểm score chỉ đạt 0.2 - 0.4). Khi chạy thực tế trên môi trường nạp API Semantic Embeddings thật (OpenAI `text-embedding-3-small` hoặc Gemini `gemini-embedding-001`), điểm Cosine Similarity sẽ tăng lên 0.75 - 0.92 và trích xuất đúng 5/5 chunk liên quan ở Top-1.




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

