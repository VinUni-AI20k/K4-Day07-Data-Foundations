# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Duy Thái

**Mã sinh viên:** 2A202601552

**Nhóm:** Sigmoid

**Ngày:** 2026-08-03

**Nhánh cá nhân:** `member/nguyen-duy-thai-sentence`

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự cosine

Cosine similarity cao nghĩa là hai vector embedding có hướng gần nhau, thường biểu diễn nội dung hoặc ý nghĩa gần nhau. Điểm gần 1 là rất tương tự, gần 0 là ít liên hệ, và gần -1 là ngược hướng.

**Ví dụ độ tương tự cao**

- Câu A: “Người mua có thể yêu cầu trả hàng trong vòng 15 ngày.”
- Câu B: “Khách hàng được phép hoàn trả sản phẩm trong thời hạn mười lăm ngày.”
- Hai câu diễn đạt cùng một quyền và cùng thời hạn bằng từ ngữ khác nhau.

**Ví dụ độ tương tự thấp**

- Câu A: “Shopee chuyển tiền cho người bán sau khi giao hàng thành công.”
- Câu B: “Mỹ phẩm phải có thông tin nguồn gốc và hạn sử dụng.”
- Hai câu thuộc hai nghiệp vụ khác nhau: thanh toán và quy định đăng bán mỹ phẩm.

Cosine được ưu tiên hơn Euclidean cho text embeddings vì nó tập trung vào hướng của vector, ít bị ảnh hưởng bởi độ lớn. Với embedding đã chuẩn hóa, cosine cũng cho phép xếp hạng bằng dot product hiệu quả.

### Bài toán chunking

Với tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`, bước dịch là `500 - 50 = 450`:

`ceil((10000 - 500) / 450) + 1 = ceil(21.111...) + 1 = 23 chunks`.

Nếu overlap tăng lên 100, bước dịch còn 400:

`ceil((10000 - 500) / 400) + 1 = ceil(23.75) + 1 = 25 chunks`.

Overlap lớn hơn tạo thêm chunk và chi phí embedding/storage, nhưng giảm nguy cơ một ý quan trọng bị cắt đúng tại biên chunk.

## 2. Hướng tiếp cận của tôi — Cá nhân (10 điểm)

### Các hàm chunking

**`SentenceChunker.chunk`:** Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết câu và giữ lại dấu câu. Hàm loại bỏ chuỗi rỗng, chuẩn hóa khoảng trắng, trả `[]` cho input rỗng, và ép `max_sentences_per_chunk` tối thiểu là 1. Benchmark cũng chỉ ra giới hạn thực tế: heading, bảng Markdown và mệnh đề dài không có `. ! ?` có thể tạo chunk vượt xa độ dài mong muốn.

**`RecursiveChunker.chunk` / `_split`:** Thuật toán thử separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng rồi ký tự. Base case là text đã nhỏ hơn `chunk_size`; nếu hết separator, hàm cắt cứng theo kích thước. Các phần nhỏ được ghép vào buffer cho tới khi thêm phần tiếp theo sẽ vượt giới hạn.

### `EmbeddingStore`

**`add_documents` + `search`:** Mỗi document được gắn ID duy nhất, metadata và embedding; một bản in-memory được giữ làm nguồn chuẩn, còn ChromaDB là backend tùy chọn. Vì `MockEmbedder` và local SentenceTransformer đều trả vector chuẩn hóa, dot product dùng khi search tương đương cosine similarity; kết quả được sắp giảm dần theo score.

**`search_with_filter` + `delete_document`:** Metadata được lọc trước để chỉ embed query và xếp hạng trên tập ứng viên hợp lệ. Xóa document bằng cách tìm toàn bộ record có `document_id` hoặc metadata `doc_id` tương ứng, xóa khỏi memory mirror và đồng bộ sang Chroma khi backend này khả dụng.

### `KnowledgeBaseAgent.answer`

Agent lấy top-k chunk, gắn nhãn từng context kèm source, rồi đưa question và toàn bộ retrieved context vào prompt. Prompt yêu cầu chỉ dùng ngữ cảnh đã lấy và phải nói thiếu thông tin thay vì bịa. Benchmark dùng một `llm_fn` extractive minh bạch, trả nguyên Context 1 để kiểm tra đường đi RAG mà không tuyên bố đã đánh giá một production LLM.

## 3. Hoàn thiện code — Cá nhân (30 điểm)

Chạy trong `.venv` bằng Python 3.11.15:

```text
> python -m pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 42 items
tests/test_solution.py::TestProjectStructure ... PASSED
tests/test_solution.py::TestClassBasedInterfaces ... PASSED
tests/test_solution.py::TestFixedSizeChunker ... PASSED
tests/test_solution.py::TestSentenceChunker ... PASSED
tests/test_solution.py::TestRecursiveChunker ... PASSED
tests/test_solution.py::TestEmbeddingStore ... PASSED
tests/test_solution.py::TestKnowledgeBaseAgent ... PASSED
tests/test_solution.py::TestComputeSimilarity ... PASSED
tests/test_solution.py::TestCompareChunkingStrategies ... PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter ... PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument ... PASSED
============================= 42 passed in 0.07s ==============================
```

**Số lượng test vượt qua:** 42 / 42.

## 4. Dự đoán độ tương tự — Cá nhân (5 điểm)

Các nhãn dự đoán dưới đây được ghi cố định trong script trước khi model tính score. Backend là `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`; quy ước kiểm tra là cao nếu cosine `>= 0.5`.

| Cặp | Câu A | Câu B | Dự đoán trước | Score thực tế | Đúng? |
|---:|---|---|:---:|---:|:---:|
| 1 | Người mua có thể yêu cầu trả hàng và hoàn tiền trong vòng 15 ngày. | Khách hàng được phép hoàn trả sản phẩm trong thời hạn mười lăm ngày. | Cao | 0.798324 | Có |
| 2 | Đơn hàng ở trạng thái Chờ lấy hàng cần người bán đồng ý mới hủy được. | Muốn hủy đơn đang chờ lấy hàng, người mua phải đợi phản hồi của người bán. | Cao | 0.594621 | Có |
| 3 | Người bán phải đăng ảnh thật của sản phẩm. | Shopee bảo vệ dữ liệu cá nhân của người dùng. | Thấp | 0.409490 | Có |
| 4 | Sản phẩm bị cấm có thể khiến tài khoản người bán bị đình chỉ. | Vi phạm danh mục hàng cấm có thể dẫn đến khóa tài khoản. | Cao | 0.668036 | Có |
| 5 | Shopee chuyển tiền cho người bán vào ngày thứ tư sau khi giao hàng thành công. | Mỹ phẩm phải có thông tin nguồn gốc và hạn sử dụng. | Thấp | -0.072076 | Có |

Kết quả bất ngờ nhất là cặp 3 vẫn đạt 0.409490 dù khác nghiệp vụ. Hai câu cùng nằm trong miền Shopee/e-commerce và cùng nói về chủ thể người dùng/người bán, cho thấy embedding giữ cả tín hiệu chủ đề rộng chứ không chỉ quan hệ nghiệp vụ chính xác. Vì vậy threshold 0.5 chỉ là quy ước cho bài thử này, không phải ngưỡng phổ quát.

## 5. Kết quả truy xuất của tôi — Cá nhân (10 điểm)

Tôi chạy đúng 5 query trong `REPORT_NHOM.md` trên cùng corpus. Kết quả đo ba cấu hình:

| `max_sentences_per_chunk` | Số chunk | Độ dài TB | Dài nhất | Relevant top-3 | Relevant top-1 |
|---:|---:|---:|---:|---:|---:|
| 3 | 329 | 418.62 | 3,659 | 3/5 | 2/5 |
| 5 | 199 | 692.74 | 5,919 | 3/5 | 2/5 |
| **8** | **124** | **1,112.34** | **6,327** | **4/5** | **4/5** |

Tôi chọn **`max_sentences_per_chunk=8`** vì có top-3 hit rate và top-1 hit rate cao nhất. Biên câu giúp giữ danh sách chế tài và điều khoản thanh toán liền mạch, nhưng cấu hình 8 cũng tạo chunk quá dài và nhiễu. Cấu hình 3 gọn hơn nhưng có thể quá vụn: ở câu 1, nội dung SPX đứng top-1 trong khi bảng “Chờ lấy hàng” đúng nằm rank 2.

| # | Query (rút gọn) | Top-1 chunk | Score | Relevant? | Câu trả lời/evidence của agent (tóm tắt) |
|---:|---|---|---:|:---:|---|
| 1 | ĐVVC không phải SPX, “Chờ lấy hàng”, hủy ngay? | `shopee-order-cancellation`, chunk 0 | 0.746921 | Có | Không hủy ngay; phải chờ Người bán. Chấp nhận thì hủy, từ chối thì tiếp tục giao. |
| 2 | Thời hạn thường và thực phẩm tươi/đông lạnh? | `shopee-product-listing-rules`, chunk 26 | 0.672790 | Không | Context 1 nói hạn sử dụng 30%/30 ngày của hàng thực phẩm; không đủ bằng chứng để trả lời 15 ngày/24 giờ. |
| 3 | Yêu cầu ảnh thật và tỷ lệ diện tích? | `shopee-product-listing-rules`, chunk 7 | 0.852447 | Có | Ít nhất một ảnh thật do Người bán tự chụp; sản phẩm thật chiếm ít nhất 40% diện tích ảnh. |
| 4 | Các nhóm chế tài khi vi phạm hàng cấm? | `shopee-prohibited-products-policy`, chunk 1 | 0.754894 | Có | Xóa sản phẩm; giới hạn/đình chỉ/xóa tài khoản; cấn trừ số dư hoặc phong tỏa rút tiền; chế tài khác theo chính sách/pháp luật. |
| 5 | Shopee chuyển tiền sớm nhất khi nào? | `shopee-terms-of-service`, chunk 24 | 0.719140 | Có | Sớm nhất ngày thứ 4 sau khi giao thành công; có thể muộn hơn nếu nghi ngờ gian lận. |

**Số query có chunk liên quan trong top-3:** 4 / 5.

### So sánh filtered và unfiltered cho câu hủy đơn

Với cấu hình 8, lượt không filter có top-3 lần lượt từ `shopee-order-cancellation`, `shopee-terms-of-service`, `shopee-return-refund-policy`. Filter `{"customer_role": "buyer"}` giữ nguyên đúng top-1 và score 0.746921 nhưng loại hai tài liệu metadata `both`; chỉ còn hai chunk buyer-only của tài liệu hủy đơn. Như vậy filter không cải thiện rank 1 trong lần đo này, nhưng làm sạch phần còn lại của candidate set.

### Bài học từ đối chiếu benchmark giữa các thành viên

Qua benchmark chung, tôi học được từ chiến lược `FixedSizeChunker(chunk_size=800, overlap=100)` của Nguyễn Đức Anh rằng giới hạn độ dài và overlap có thể quan trọng hơn việc chỉ giữ nguyên biên câu. FixedSize đạt relevant top-3 **5/5** và đủ evidence **5/5**, trong khi `SentenceChunker(8)` của tôi đạt top-3 **4/5** nhưng có top-1 tốt hơn (**4/5** so với **3/5**). SentenceChunker tạo ít chunk hơn và thường đưa kết quả đúng lên đầu, nhưng chunk dài nhất trong benchmark chung tới **6.301 ký tự** và bỏ lỡ câu hỏi thời hạn trả hàng; FixedSize giữ tối đa **800 ký tự** và overlap giúp bảo toàn evidence qua biên. Nếu cải tiến tiếp, tôi sẽ kết hợp biên câu với giới hạn ký tự cứng và overlap nhỏ để giữ tính mạch lạc mà tránh chunk quá dài.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |

## Tái lập kết quả

```powershell
$env:HF_HOME = Join-Path $env:TEMP 'day07-huggingface'
$env:PYTHONUTF8 = '1'
$env:HF_HUB_OFFLINE = '1'
.\.venv\Scripts\python.exe experiments\nguyen_duy_thai_sentence_benchmark.py
```

Chi tiết machine-readable: `report/member_handoffs/2A202601552-benchmark.json`.
