# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Duy Khánh  
**Nhóm:** T-Hexa  
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm nộp chung trong `REPORT_NHOM.md`. Báo cáo này tập trung vào phần cá nhân: warm-up, hướng tiếp cận lập trình, kết quả test, dự đoán similarity và kết quả retrieval.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) - Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**

> Độ tương tự cosine cao nghĩa là hai vector biểu diễn hai đoạn văn bản đang chỉ gần cùng một hướng trong không gian embedding. Nói đơn giản, hai đoạn thường có ý nghĩa, chủ đề hoặc vai trò ngữ nghĩa gần nhau, dù độ dài câu có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua cần gửi yêu cầu đổi trả khi hàng bị lỗi.
- Câu B: Khách hàng phải tạo yêu cầu hoàn trả nếu sản phẩm bị hỏng.
- Tại sao tương đồng: Hai câu cùng nói về hành động của người mua khi sản phẩm lỗi và đều thuộc chủ đề đổi trả.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người bán phải cung cấp mô tả sản phẩm chính xác.
- Câu B: Hôm nay thời tiết nắng nhẹ và có gió.
- Tại sao khác: Hai câu thuộc hai chủ đề khác hẳn nhau: một câu về chính sách thương mại điện tử, một câu về thời tiết.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**

> Cosine similarity tập trung vào hướng của vector nên phù hợp để so sánh ý nghĩa/ngữ nghĩa của văn bản. Euclidean distance bị ảnh hưởng nhiều bởi độ dài vector, nên đôi khi hai câu cùng nghĩa nhưng khác độ lớn embedding có thể bị đánh giá xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

> Phép tính:
step = chunk_size - overlap = 500 - 50 = 450
số chunk = ceil((10000 - 50) / 450)
         = ceil(9950 / 450)
         = ceil(22.11)
         = 23


> Đáp án: **23 chunks**.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

> Khi `overlap=100`, `step = 500 - 100 = 400`, nên số chunk là `ceil((10000 - 100) / 400) = ceil(24.75) = 25`. Số chunk tăng vì mỗi lần trượt ít hơn; đổi lại overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa hai chunk, giảm khả năng làm mất ý khi câu hoặc đoạn bị cắt ngang.

---

## 2. Hướng tiếp cận của tôi (My Approach) - Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` - hướng tiếp cận:**

> Tôi xử lý text rỗng trước để trả về `[]`. Sau đó dùng regex `r"(?<=[.!?])\s+"` để tách tại khoảng trắng sau dấu `.`, `!`, hoặc `?`, nhờ vậy dấu câu vẫn nằm ở cuối câu phía trước. Các câu được `strip()`, bỏ phần rỗng, rồi gom tối đa `self.max_sentences_per_chunk` câu bằng `" ".join(...)`.

**`RecursiveChunker.chunk` / `_split` - hướng tiếp cận:**

> `chunk()` chỉ làm phần điều phối: nếu text rỗng thì trả `[]`, còn lại gọi `_split(text, self.separators)` rồi strip và bỏ chunk rỗng. `_split()` ưu tiên ranh giới tự nhiên theo thứ tự đoạn `\n\n`, dòng `\n`, câu `. `, từ `" "`, cuối cùng là ký tự. Base case là text đã ngắn hơn `chunk_size`, hoặc hết separator / separator rỗng thì cắt cố định theo `chunk_size`; nếu một phần sau khi split vẫn quá dài thì đệ quy xuống separator ưu tiên thấp hơn.

### Lớp EmbeddingStore

**`add_documents` + `search` - hướng tiếp cận:**

> Mỗi `Document` được chuyển thành một record chuẩn gồm `id`, `content`, bản sao `metadata` và `embedding`. `metadata` luôn có `doc_id`; nếu document là chunk dạng `doc_id::chunk_0` thì `doc_id` vẫn trỏ về file gốc. Khi search, query được embed đúng một lần, sau đó tính dot product giữa query embedding và từng record embedding, sort giảm dần theo `score` rồi cắt `top_k`.

**`search_with_filter` + `delete_document` - hướng tiếp cận:**

> `search_with_filter` lọc metadata trước, rank sau. Một record chỉ được giữ lại nếu mọi cặp `key/value` trong filter đều khớp metadata của record; sau đó tập đã lọc được đưa vào `_search_records`. Không nên lấy top-k trước rồi mới filter, vì có thể top-k ban đầu không chứa record đúng metadata dù trong store vẫn có tài liệu hợp lệ. `delete_document` xóa mọi record có `metadata["doc_id"] == doc_id` và trả `True` nếu có ít nhất một record bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer` - hướng tiếp cận:**

> Agent không tự tính embedding mà gọi `self.store.search(question, top_k=top_k)` để lấy context. Tôi ghép các chunk theo dạng đánh số `[1]`, `[2]`, kèm `doc_id` và `source/source_url` để dễ truy vết về file gốc khi debug. Prompt gồm instruction chỉ dùng context, phần context, câu hỏi và nhãn `Answer:`; nếu store rỗng thì trả thông báo rõ ràng thay vì gọi LLM.

---

## 3. Hoàn thiện code (Core Implementation) - Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

```text
$env:LAB_SOLUTION_PACKAGE="2A202601530_NguyenDuyKhanh"
python -m pytest tests -v
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) - Cá nhân (5 điểm)

Các điểm thực tế dưới đây được tính bằng `compute_similarity(_mock_embed(câu A), _mock_embed(câu B))`. Vì `_mock_embed` là embedding giả lập phục vụ unit test, điểm số không phản ánh ngữ nghĩa tốt như embedding thật.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua cần gửi yêu cầu đổi trả kèm bằng chứng. | Khách hàng phải cung cấp bằng chứng khi hàng lỗi hoặc sai mô tả. | cao | 0.0157 | Không |
| 2 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Seller cần ghi đúng giá, mô tả và tình trạng hàng. | cao | -0.0592 | Không |
| 3 | Sản phẩm bị cấm không được đăng bán trên sàn. | Người bán không được đăng các mặt hàng bị hạn chế hoặc bị cấm. | cao | -0.0847 | Không |
| 4 | Chính sách đổi trả áp dụng cho hàng lỗi. | Hôm nay thời tiết nắng nhẹ ở Hà Nội. | thấp | -0.0482 | Đúng |
| 5 | Vector store dùng embedding để tìm kiếm. | Người mua gửi yêu cầu đổi trả theo thời hạn của sàn. | thấp | 0.2461 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**

> Bất ngờ nhất là cặp 5 có điểm cao nhất dù hai câu khác chủ đề rõ ràng. Điều này cho thấy mock embedding chỉ hữu ích để kiểm tra code chạy đúng, không nên dùng để kết luận chất lượng ngữ nghĩa. Khi đánh giá retrieval thật, cần dùng embedding model có học ngữ nghĩa, ví dụ local multilingual embedding như README gợi ý.

---

## 5. Kết quả truy xuất của tôi (Competition Results) - Cá nhân (10 điểm)

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì khi muốn đổi trả hàng lỗi hoặc không đúng mô tả? | `k4-returns-policy`, chunk 2: người bán phản hồi theo quy trình của sàn; cần bổ sung nguồn, điều kiện và ngoại lệ. | -0.0435 | Không | Context top-1 chưa trả lời đúng hành động của người mua; agent nên nói context chưa đủ hoặc chỉ nêu phần người bán phản hồi. |
| 2 | Người bán có trách nhiệm gì khi nhận yêu cầu đổi trả? | `k4-seller-listing`, chunk 1: người bán cung cấp thông tin sản phẩm chính xác, giá, mô tả, tình trạng hàng. | 0.1544 | Không ở top-1, có liên quan trong top-3 | Agent có thể lấy được ý đúng nếu xem chunk `k4-returns-policy` trong top-3: người bán phản hồi theo quy trình của sàn. |
| 3 | Người bán phải cung cấp những thông tin nào khi đăng bán sản phẩm? | `k4-returns-policy`, chunk 0: phần template metadata cho chính sách đổi trả. | 0.1311 | Không | Agent nên báo context top-1 không đủ; kết quả bị nhiễu do mock embedding. |
| 4 | Sản phẩm bị hạn chế hoặc bị cấm có được đăng bán không? | `k4-seller-listing`, chunk 0: template metadata và tiêu đề đăng bán sản phẩm. | 0.1210 | Có trong top-3, top-1 chưa đủ | Agent có thể trả lời nếu dùng chunk top-3: sản phẩm bị hạn chế hoặc bị cấm không được đăng bán. |
| 5 | Lọc metadata `customer_role=seller` thì câu hỏi về đăng bán nên lấy tài liệu nào? | `k4-seller-listing`, chunk 1: người bán cung cấp thông tin sản phẩm chính xác; hàng hạn chế/cấm không được đăng bán. | 0.0784 | Có | Agent trả lời dựa trên tài liệu `k4-seller-listing`, đúng vì filter đã giới hạn vào tài liệu dành cho seller. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**

> Điều quan trọng nhất là filter metadata phải diễn ra trước khi rank bằng embedding, đặc biệt với các câu hỏi chỉ áp dụng cho một nhóm người dùng như buyer hoặc seller. Tôi cũng thấy chất lượng retrieval phụ thuộc mạnh vào chất lượng dữ liệu và embedding; code đúng chưa đủ nếu chunk bị nhiễu bởi phần template hoặc embedding không hiểu ngữ nghĩa tiếng Việt.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation - tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
