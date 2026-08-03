# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Tạ Quốc Tuấn
**Nhóm:** B1-2
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine được coi là cao khi giá trị tương đồng cosine giữa 2 vecto ngữ cảnh của 2 câu tiến gần đến 1. Điều này thể hiện rằng 2 câu có sự tương đồng về mặt ngữ nghĩa.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi rất thích ăn phở bò Hà Nội."
- Câu B: "Món phở bò ở Hà Nội là món khoái khẩu của tôi."
- Tại sao tương đồng: Cả hai câu sử dụng từ ngữ và cấu trúc khác nhau nhưng diễn đạt cùng một ý niệm (sự yêu thích đối với phở bò Hà Nội). Vì vậy, giá trị tương đồng cosine dự đoán sẽ rất cao (0.85 - 0.95)

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi rất thích ăn phở bò Hà Nội."
- Câu B: "Thị trường chứng khoán hôm nay biến động rất mạnh."
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn độc lập (ẩm thực và tài chính). Do không chia sẻ ngữ cảnh hay các trường từ vựng liên quan, vector biểu diễn của chúng hướng về các phía khác nhau trong không gian ngữ nghĩa .

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity được ưu tiên vì nó tập trung vào hướng của vector ngữ cảnh thay vì độ dài văn bản, giúp so sánh chính xác sự tương đồng giữa các đoạn văn ngắn và dài mà không bị lệch do số lượng từ.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Chunks = ceil((10000 - 50) / (500 - 50)) = 21
> Đáp án : 21 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, theo công thức, số luọng chunk sẽ tăng từ 21 -> 25 chunks. Tăng độ overlap giúp bảo toàn nguyên vẹn ngữ cảnh tại các điểm cắt giữa hai chunk kế tiếp. Điều này tránh việc thông tin quan trọng bị ngắt đoạn, từ đó nâng cao độ chính xác khi truy xuất cho hệ thống RAG.
 
---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*
Sử dụng biểu thức chính quy re.split(r'(?<=[.!?])\s+|\n+', text) hoặc pattern match các ký tự kết thúc câu [.!?] theo sau bởi khoảng trắng/xuống dòng để tách văn bản thành danh sách câu hoàn chỉnh. Cần xử lý các trường hợp ngoại lệ như chuỗi rỗng, khoảng trắng thừa giữa các câu (dùng .strip()), và gom các câu lại thành nhóm sao cho số lượng câu không vượt quá max_sentences_per_chunk.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*
Thuật toán hoạt động theo cơ chế chia để trị đệ quy: duyệt qua danh sách phân tách ["\n\n", "\n", ". ", " ", ""] từ cấu trúc lớn đến nhỏ. Base case là khi độ dài đoạn văn bản nhỏ hơn hoặc bằng chunk_size thì dừng đệ quy và trả về đoạn đó. Nếu chưa thỏa mãn, hàm dùng phân tách hiện tại để chia nhỏ, gộp các phần phù hợp, và tiếp tục đệ quy _split() với phân tách tiếp theo trên những phần vẫn vượt quá độ dài cho phép.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*
Sử dụng kiến trúc hai lớp: thử khởi tạo ChromaDB trước, nếu thư viện không có sẵn thì fallback về lưu trữ trong-memory bằng list of dicts. Với add_documents, mỗi Document được chạy qua embedding_fn để tạo vector, rồi lưu kèm id, content, embedding, và metadata đầy đủ. Với search, câu hỏi được nhóm cũng qua embedding_fn, sau đó tính dot product giữa query vector và mỗi stored vector — vì mock embedder đã chuẩn hóa magnitude về 1, nên dot product tương đương cosine similarity. Kết quả được sort giảm dần theo điểm và lấy top-k trả về kèm content, score, và metadata để agent hoặc người dùng có thể truy vết nguồn.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
search_with_filter thực hiện lọc trước, tìm kiếm sau — đầu tiên duyệt qua toàn bộ store, chỉ giữ lại các record có metadata khớp hoàn toàn với metadata_filter truyền vào, rồi chạy similarity search trên tập đã lọc. Cách này đảm bảo kết quả cuối cùng đều thỏa mãn điều kiện lọc, đồng thời khi metadata_filter=None thì tương đương search thông thường. delete_document xóa bằng cách lọc tất cả record có metadata['doc_id'] trùng với doc_id truyền vào, gọi pop() theo index ngược để tránh lỗi thứ tự khi xóa, rồi trả True nếu có bản ghi bị xóa, False nếu không tìm thấy — giúp caller biết được thao tác có thực sự tác động hay không.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
Cấu trúc prompt tuân theo mẫu RAG classique: lấy top-k chunks từ store, đặt vào một hệ thống prompt rõ ràng — phần hệ thống (system) yêu cầu agent chỉ trả lời dựa trên ngữ cảnh được cung cấp, không tự bịa thông tin; phần ngữ cảnh (context) liệt kê từng chunk kèm metadata để LLM có thể trích dẫn nguồn; phần câu hỏi (question) là input của người dùng. Ngữ cảnh được inject bằng cách nối các chunk thành một khối text có định dạng nhất quán (ví dụ: [Source: ...]\n{content}), rồi truyền toàn bộ string đó vào llm_fn. Nếu truy xuất yếu (trả về điểm thấp hoặc không có chunk nào), agent có thể phát hiện qua ngưỡng điểm và trả lời rõ ràng là không tìm thấy thông tin, thay vì tự bịa

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```
(.venv) PS F:\Day07-2A202601114-TaQuocTuan> pytest tests/ -v
=================================================== test session starts ===================================================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- F:\Day07-2A202601114-TaQuocTuan\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: F:\Day07-2A202601114-TaQuocTuan
plugins: anyio-4.14.2
collected 42 items                                                                                                         

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                         [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                  [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                   [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                        [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                        [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                              [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                               [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                             [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                               [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                               [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                          [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                      [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                       [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                           [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                     [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                           [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                               [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                 [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                   [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                         [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                              [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                    [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                 [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                          [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                         [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                    [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                           [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                               [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                     [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                               [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED            [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                          [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                         [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED             [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                        [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                 [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED       [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED           [100%]

=================================================== 42 passed in 3.19s ====================================================


**Số lượng bài test vượt qua (pass):** _42_ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Hôm nay trời mưa rất lớn. | Trời đang có mưa to. | cao | 0.7391 | Đúng |
| 2 | Tôi thích uống cà phê vào buổi sáng. | Mỗi sáng tôi thường uống một tách cà phê. | cao | 0.7705 | Đúng |
| 3 | Con mèo đang ngủ trên ghế. | Con chó đang chạy ngoài sân. | thấp | 0.3935 | Đúng |
| 4 | Tôi không thích bộ phim này. | Trời hôm nay nắng đẹp. | Thấp | 0.3094 | Đúng |
| 5 | Chiếc điện thoại này có giá khá rẻ. | Sản phẩm này không quá đắt. | tương đối tương đồng (0.6 - 0.7) | 0.4869 | Thấp hơn kì vọng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*
Kết quả bất ngờ nhất là Cặp 5, khi hai câu mang ngữ nghĩa rất tương đồng nhưng điểm tương đồng Cosine thực tế chỉ đạt 0.4869, thấp hơn so với kì vọng. Điều này cho thấy các mô hình Embeddings đơn giản thường phụ thuộc nhiều vào tương đồng từ vựng/ngữ pháp bề mặt thay suy luận logic. Khi gặp các cấu trúc phủ định hoặc từ đồng nghĩa/trái nghĩa phức tạp (như "không quá đắt" = "rẻ", "điện thoại" = "sản phẩm"), mô hình chưa thực sự "hiểu" được ngữ nghĩa logic hoàn chỉnh mà chỉ biểu diễn dựa trên ngữ cảnh từ xuất hiện chung.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 |  Mất bao lâu để tôi nhận được tiền hoàn vào ví ShopeePay nếu hủy đơn? | Hạn mức Ngân hàng liên kết Mỗi Ngân hàng liên kết sẽ có hạn mức giao dịch hàng ngày khác nhau. | 0.3004 | Có | Hãy đảm bảo rằng tổng giá trị các đơn hàng cần thanh toán trong ngày của bạn không vượt quá hạn mức này.[reference:14] (nguồn: thanh-toan-shopee-pay::chunk_8)  |
| 2 | Phí thanh toán cố định hiện tại trên mỗi đơn hàng thành công là bao nhiêu phần trăm? | 2. PHẠM VI ÁP DỤNG Chính sách này áp dụng đối với việc đăng bán sản phẩm, hàng hóa, dịch vụ trên Sàn Shopee. Mỗi khi đăng bán sản phẩm, Người Bán có trách nhiệm đảm b... | 0.1950 | Không đảm bảo | Chính sách này áp dụng đối với việc đăng bán sản phẩm, hàng hóa, dịch vụ trên Sàn Shopee. Mỗi khi đăng bán sản phẩm, Người Bán có trách nhiệm đảm bảo hàng hóa của mình tuân thủ Luật pháp hiện hành đồng thời không vi phạm các Điều Khoản Sử Dụng và Chính Sách Shopee.[reference:40] (nguồn: cam-ban-hang-gia::chunk_1) |
| 3 | Làm thế nào để áp dụng mã miễn phí vận chuyển Extra? | doc_id=phi-van-chuyen-thoi-gian-giao-hang chunk=10 preview=rence:21 ## B. QUY ĐỊNH VỀ HÀNG HÓA KHÔNG HỖ TRỢ VẬN CHUYỂN, VẬN CHUYỂN CÓ ĐIỀU KIỆN ### 1. Quy định về các loại hàng hóa không hỗ trợ vận chuyển trên Shopee Các loại hàng hóa ... | 0.1956 | Có |  B. QUY ĐỊNH VỀ HÀNG HÓA KHÔNG HỖ TRỢ VẬN CHUYỂN, VẬN CHUYỂN CÓ ĐIỀU KIỆN |
| 4 | Nếu tôi phát hiện shop gửi hàng fake thì Shopee có đền bù không? | u nại, Shopee khuyến khích giải pháp thương lượng, hòa giải giữa các bên để đạt được sự đồng thuận về phương án giải quyết.[reference:50] Nếu Người Bán, Người Mua và các bên có ... | 0.2100 | Tương đối không  | Nạp thẻ & Dịch Vụ  1K Xu/ngày, 5K Xu/tuần (không quá 1% giá trị đơn hàng/lần thanh toán) |
| 5 | Shopee Xu của tôi sẽ hết hạn vào ngày nào? |  preview=ợc sử dụng tối đa Các sản phẩm bán tại Shopee 800K Xu/ngày, 2 triệu Xu/tuần (không quá 50% giá trị đơn hàng/lần thanh toán)[reference:59] | 0.1960 | Tương đối không | Các sản phẩm bán tại Shopee 800K Xu/ngày, 2 triệu Xu/tuần (không quá 50% giá trị đơn hàng/lần thanh toán)[reference:59] (nguồn: shopee-xu::chunk_4)|

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** _2_ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Điều hay nhất tôi học được qua demo là mỗi chiến lược chunking đều có đánh đổi riêng: FixedSizeChunker dễ cài và ổn để làm baseline nhưng hay cắt đứt ngữ cảnh, trong khi RecursiveChunker và SentenceChunker giữ câu/đoạn tự nhiên hơn nên provenance dễ đọc hơn. MarkdownHeadingChunker phù hợp nhất với tài liệu chính sách vì giữ được cấu trúc mục, nhưng nếu một section quá dài hoặc nhiều ý gần nhau thì top-3 vẫn có thể đúng tài liệu mà sai đoạn chứa đáp án.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** |  60 / 60** |
