# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Mai Việt Hoàng
**Nhóm:** A5-1
**Ngày:** 03/08/2026

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine

Cosine similarity cao nghĩa là hai vector gần cùng hướng, cho thấy hai văn bản có biểu diễn tương đồng. Giá trị gần 1 là tương đồng cao, gần 0 là ít liên quan và gần -1 là ngược hướng.

**Ví dụ tương tự cao:**
- Câu A: “Thời hạn trả hàng là 15 ngày.”
- Câu B: “Người mua có 15 ngày để yêu cầu trả hàng.”
- Hai câu cùng diễn đạt một quy định và một mốc thời gian.

**Ví dụ tương tự thấp:**
- Câu A: “Video mở kiện là bằng chứng quan trọng.”
- Câu B: “Hôm nay thời tiết rất đẹp.”
- Hai câu thuộc hai chủ đề không liên quan.

Cosine similarity được ưu tiên hơn Euclidean distance vì nó so sánh hướng và ít bị ảnh hưởng bởi độ lớn vector. Điều này phù hợp với embedding văn bản, nơi cần quan tâm quan hệ ngữ nghĩa hơn độ dài tuyệt đối.

### Bài toán Chunking

Với 10,000 ký tự, `chunk_size=500`, `overlap=50`:

```text
ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23 chunks
```

Khi overlap tăng lên 100:

```text
ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25 chunks
```

Số chunk tăng vì bước nhảy giảm từ 450 xuống 400. Overlap lớn hơn giúp giữ ngữ cảnh ở biên chunk nhưng làm tăng số vector và chi phí lưu/tìm kiếm.

## 2. Hướng tiếp cận của tôi — Cá nhân (10 điểm)

### Chunking

`SentenceChunker` dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết câu, loại chuỗi rỗng rồi gom tối đa `max_sentences_per_chunk` câu. Văn bản rỗng được trả về danh sách rỗng.

`RecursiveChunker` thử separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng và ký tự. Base case là đoạn không vượt `chunk_size`; nếu không còn separator phù hợp, đoạn được cắt cứng theo ký tự. Chiến lược cá nhân của tôi là `RecursiveChunker(chunk_size=500)` để giữ cấu trúc đoạn/câu của chính sách.

### EmbeddingStore

`add_documents` sao chép metadata, bảo đảm có `doc_id`, tạo embedding và lưu record vào bộ nhớ; nếu ChromaDB khả dụng thì đồng bộ thêm sang collection. `search` embed truy vấn, tính dot product với các vector đã lưu, sắp xếp score giảm dần và trả về Top-K.

`search_with_filter` lọc metadata trước khi tính similarity, giúp giảm ứng viên nhiễu. `delete_document` tìm toàn bộ chunk có cùng `metadata.doc_id`, xóa khỏi store và đồng bộ thao tác xóa sang ChromaDB nếu đang dùng.

### KnowledgeBaseAgent

`answer` truy xuất Top-K chunk, đánh số từng context rồi tạo prompt yêu cầu LLM chỉ trả lời dựa trên context. Nếu retrieval rỗng, prompt thông báo không có ngữ cảnh để hạn chế câu trả lời không có căn cứ.

## 3. Hoàn thiện code — Cá nhân (30 điểm)

Chạy bằng Python 3.11 trong môi trường `uv`:

```text
uv run pytest tests/ -q
.......................................... [100%]
42 passed
```

**Số test vượt qua:** 42 / 42.

## 4. Dự đoán độ tương tự — Cá nhân (5 điểm)

Các điểm dưới đây dùng `MockEmbedder`, chỉ để kiểm tra code và không phản ánh ngữ nghĩa thực.

| Cặp | Câu A | Câu B | Dự đoán | Điểm mock | Kết luận |
|---|---|---|---|---:|---|
| 1 | Thời hạn trả hàng là 15 ngày. | Người mua có 15 ngày để yêu cầu trả hàng. | Cao | 0.042408 | Sai với dự đoán |
| 2 | Shopee hoàn tiền qua Ví ShopeePay. | Tiền được chuyển về ví điện tử ShopeePay. | Cao | 0.235946 | Thấp hơn kỳ vọng |
| 3 | Video mở kiện là bằng chứng quan trọng. | Hôm nay thời tiết rất đẹp. | Thấp | 0.073210 | Phù hợp tương đối |
| 4 | Sản phẩm tươi sống bị hạn chế trả hàng. | Thực phẩm đông lạnh thuộc nhóm hạn chế trả hàng. | Cao | -0.182513 | Sai với dự đoán |
| 5 | Theo dõi yêu cầu trong mục Thông báo. | Người bán phải đăng ảnh sản phẩm rõ ràng. | Thấp | -0.004736 | Phù hợp |

Kết quả bất ngờ nhất là cặp 4 có ý nghĩa gần nhau nhưng score âm. Nguyên nhân là MockEmbedder sinh vector xác định từ hash của toàn chuỗi chứ không được huấn luyện để biểu diễn ngữ nghĩa; benchmark retrieval chính thức phải dùng embedder đa ngữ thật.

## 5. Kết quả truy xuất của tôi — Cá nhân (10 điểm)

**Chiến lược:** `RecursiveChunker(chunk_size=500)` trên 7 tài liệu Shopee thật. Kết quả dưới đây dùng cùng phép cosine trên vector tần suất từ để so sánh các branch; score không được so trực tiếp với Hugging Face embedding.

| # | Câu hỏi | Top-1 document | Score | Liên quan? | Agent answer |
|---|---|---|---:|---|---|
| 1 | Thời hạn gửi yêu cầu theo loại đơn | `shopee-returns-01` | 0.4922 | Có | Chưa chấm bằng LLM chung |
| 2 | Sản phẩm hạn chế trả hàng | `shopee-returns-03` | 0.7448 | Có | Chưa chấm bằng LLM chung |
| 3 | Yêu cầu đối với video bằng chứng | `shopee-returns-04` | 0.3573 | Có | Chưa chấm bằng LLM chung |
| 4 | Các bước theo dõi yêu cầu | `shopee-returns-05` | 0.5509 | Có | Chưa chấm bằng LLM chung |
| 5 | Thời gian hoàn tiền theo phương thức | `shopee-returns-06` | 0.4831 | Có | Chưa chấm bằng LLM chung |

**Top-3 chứa gold document:** 5 / 5. Tổng cộng chiến lược tạo 69 chunk, độ dài trung bình 401.93 ký tự, ngắn nhất 55 và dài nhất 499 ký tự.

Bài học chính từ so sánh nhóm là CustomChunker theo heading có thể giảm số chunk đáng kể, còn Recursive 500 giữ giới hạn context chặt chẽ hơn. Đánh giá cuối cần chấm thêm việc một chunk có chứa đủ điều kiện/ngoại lệ cho câu trả lời hay không, thay vì chỉ kiểm tra đúng document.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 5 / 10 (chưa chấm LLM chung) |
| **Tổng tạm tính** | **55 / 60** |
