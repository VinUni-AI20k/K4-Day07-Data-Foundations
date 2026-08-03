# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Thành  
**MSSV:** 2A202601030  
**Nhóm:** T-Hexa  
**Ngày:** 03/08/2026

---

## 1. Khởi động (Warm-up) — 5 điểm

### Cosine similarity

Cosine similarity đo góc giữa hai vector embedding. Điểm gần 1 cho biết hai vector hướng gần giống nhau, thường biểu diễn nội dung hoặc ý nghĩa tương tự; gần 0 là ít liên quan; gần -1 là hướng đối lập.

**Ví dụ tương tự cao:**
- A: “T-Hexa hỗ trợ thanh toán bằng ví và chuyển khoản.”
- B: “Khách hàng có thể trả tiền qua ví T-Hexa hoặc chuyển khoản trực tiếp.”
- Hai câu cùng nói về phương thức thanh toán và dùng nhiều khái niệm chung.

**Ví dụ tương tự thấp:**
- A: “T-Hexa bảo vệ dữ liệu cá nhân.”
- B: “Cây xanh hấp thụ carbon dioxide khi quang hợp.”
- Hai câu thuộc hai chủ đề hoàn toàn khác nhau.

Cosine thường phù hợp hơn Euclidean distance cho text embeddings vì nó tập trung vào hướng/ngữ nghĩa tương đối và ít bị ảnh hưởng bởi độ lớn vector. Hai văn bản có độ dài khác nhau vẫn có thể gần nhau nếu hướng biểu diễn giống nhau.

### Chunking math

Với 10.000 ký tự, `chunk_size=500`, `overlap=50`:

`ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22,11) = 23 chunks`.

Khi `overlap=100`:

`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24,75) = 25 chunks`.

Overlap lớn tạo thêm chunks nhưng giúp thông tin ở ranh giới không bị mất, đặc biệt khi một điều kiện bắt đầu ở cuối chunk trước và kết luận nằm ở đầu chunk sau.

---

## 2. Hướng tiếp cận của tôi — 10 điểm

### `SentenceChunker.chunk`

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách sau dấu kết câu nhưng giữ dấu câu trong sentence. Sau đó loại chuỗi rỗng, gom tối đa `max_sentences_per_chunk` câu và xử lý văn bản rỗng bằng danh sách rỗng.

### `RecursiveChunker.chunk` và `_split`

Thuật toán thử lần lượt `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng hard split. Base case là nội dung không vượt `chunk_size`; nếu không còn separator thì cắt theo kích thước cố định. Các đoạn nhỏ được merge lại khi tổng chiều dài chưa vượt giới hạn để tránh tạo quá nhiều chunk vụn.

### `compute_similarity` và comparator

Cosine được tính bằng dot product chia cho tích hai magnitude, có guard trả `0.0` cho zero vector và kiểm tra hai vector cùng dimension. Comparator chạy ba chunkers trên cùng text rồi trả `count`, `avg_length` và danh sách `chunks` để so sánh định lượng lẫn định tính.

### `EmbeddingStore`

`add_documents` tạo record chuẩn hóa gồm ID, content, metadata, embedding và storage ID duy nhất. `search` embed query, tính dot product với từng record, sắp xếp score giảm dần và cắt top-k. Metadata luôn có `doc_id`; điều này cho phép xóa toàn bộ chunks của một tài liệu.

`search_with_filter` lọc candidates **trước** khi tính similarity để filter thực sự thu hẹp không gian tìm kiếm. `delete_document` xóa mọi record có `metadata.doc_id` hoặc ID trùng với tài liệu cần xóa và trả boolean cho biết có xóa được hay không.

### `KnowledgeBaseAgent.answer`

Agent gọi store để lấy top-k chunks, ghép từng chunk với score và nguồn vào phần `NGỮ CẢNH`, thêm câu hỏi và chỉ dẫn “chỉ trả lời từ context”, rồi truyền prompt cho `llm_fn`. Nếu không có kết quả, prompt nói rõ thiếu thông tin thay vì tạo câu trả lời không có căn cứ.

### Strategy cá nhân

Tôi bổ sung `HeadingChunker` để chia Markdown theo heading/điều khoản. Strategy này giữ tiêu đề cùng thân mục, tạo 29 chunks và đạt top-1 đúng cho cả 5 benchmark queries.

---

## 3. Hoàn thiện code — 30 điểm

```text
collected 42 items
..........................................                               [100%]
42 passed in 0.09s
```

**Kết quả:** 42 / 42 tests pass. Bộ mã nguồn tuân theo Python 3.11 như khai báo trong `.python-version`. Trước khi nộp, chạy lại `py -3.11 -m pytest tests/ -v` trên máy cá nhân để lưu bằng chứng đúng môi trường của lớp.

---

## 4. Dự đoán độ tương tự — 5 điểm

Điểm dưới đây được tạo bởi `KeywordHashEmbedder` offline trong `evaluate_submission.py`; nó đo lexical overlap để benchmark tái lập, không thay thế embedding đa ngữ thật.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | T-Hexa hỗ trợ thanh toán bằng ví và chuyển khoản. | Khách hàng có thể trả tiền qua ví T-Hexa hoặc chuyển khoản trực tiếp. | Cao nhất | 0.3892 | Có |
| 2 | Sản phẩm lỗi in được hỗ trợ đổi trả. | Áo sai mẫu hoặc có lỗi in rõ ràng có thể yêu cầu xử lý lại. | Cao | 0.1571 | Có |
| 3 | Đơn hàng thường được giao trong 3 đến 9 ngày làm việc. | Thời gian nhận hàng phụ thuộc quá trình sản xuất và vận chuyển. | Trung bình | 0.0801 | Có |
| 4 | Người bán phải có quyền sử dụng hình ảnh. | Khách hàng chọn size áo trước khi đặt hàng. | Thấp | 0.0000 | Có |
| 5 | T-Hexa bảo vệ dữ liệu cá nhân. | Cây xanh hấp thụ khí carbon dioxide trong quá trình quang hợp. | Thấp nhất | 0.0000 | Có |

Điều đáng chú ý là cặp 2 và 3 có ý nghĩa khá gần nhưng score lexical thấp vì dùng từ khác nhau. Điều này cho thấy bag-of-words/hash embedding bỏ lỡ synonym; model đa ngữ semantic sẽ phù hợp hơn khi so sánh “đổi trả” với “xử lý lại” hoặc “giao hàng” với “vận chuyển”.

---

## 5. Kết quả truy xuất của tôi — 10 điểm

**Strategy:** `HeadingChunker(chunk_size=700, overlap=60)` + `KeywordHashEmbedder` offline.  
**Collection size:** 29 chunks.

| # | Query | Top-1 chunk (tóm tắt) | Score | Relevant? | Agent answer (tóm tắt) |
|---|---|---|---:|---|---|
| 1 | T-Hexa hỗ trợ những phương thức thanh toán nào? | ## Phương thức được hỗ trợ T-Hexa hỗ trợ ba phương thức thanh toán: ví T-Hexa, chuyển khoản trực tiếp và thanh toán khi nhận hà... | 0.5693 | Có | T-Hexa hỗ trợ ba phương thức thanh toán: ví T-Hexa, chuyển khoản trực tiếp và thanh toán khi nhận hàng (COD). Với ví T-Hexa hoặc chuyển khoản, đơn hàng được chuyển sang bước xử lý sau khi... |
| 2 | Khách hàng phải gửi yêu cầu đổi trả trong bao lâu và sản phẩm cần đáp ứng điều kiện gì? | ## Thời hạn yêu cầu Khách hàng cần gửi yêu cầu trong vòng 3 ngày kể từ thời điểm nhận hàng. Yêu cầu nên kèm mã đơn, ảnh sản phẩ... | 0.4697 | Có | Khách hàng cần gửi yêu cầu trong vòng 3 ngày kể từ thời điểm nhận hàng. Sản phẩm cần chưa qua sử dụng, chưa giặt, không có mùi lạ và còn đầy đủ phụ kiện đi kèm. |
| 3 | Tổng thời gian thông thường từ khi xác nhận đơn đến khi nhận hàng là bao lâu? | ## Thời gian vận chuyển Sau khi bàn giao cho đơn vị vận chuyển, thời gian giao dự kiến là 1 đến 5 ngày làm việc tùy khu vực. Tổ... | 0.6598 | Có | Tổng thời gian thông thường từ khi xác nhận đơn đến khi nhận hàng là khoảng 3 đến 9 ngày làm việc. Thời gian xử lý dự kiến là 2 đến 4 ngày làm việc sau khi đơn hàng được xác nhận. |
| 4 | Người bán cần đáp ứng điều kiện gì khi đăng hình ảnh và nội dung thiết kế? | # Điều kiện người bán và nội dung đăng bán | 0.6581 | Có | Điều kiện người bán và nội dung đăng bán Người bán phải có quyền sử dụng hình ảnh, logo, phông chữ và nội dung đưa lên sản phẩm. |
| 5 | T-Hexa thu thập dữ liệu cá nhân nào và sử dụng để làm gì? | ## Dữ liệu được thu thập T-Hexa có thể thu thập họ tên, email, số điện thoại, địa chỉ giao hàng, thông tin đơn hàng, mẫu thiết ... | 0.3807 | Có | T-Hexa có thể thu thập họ tên, email, số điện thoại, địa chỉ giao hàng, thông tin đơn hàng, mẫu thiết kế do người dùng tải lên và lịch sử hỗ trợ. T-Hexa không bán dữ liệu cá nhân cho nhà ... |

**Top-3 có gold chunk:** 5 / 5.  
**Điểm theo rubric:** 10 / 10 vì cả 5 gold documents đều ở top-1 và câu trả lời extractive chứa đúng thông tin cần thiết.

Điều hay nhất tôi học được là score bằng nhau không có nghĩa strategy ngang nhau về chất lượng. HeadingChunker tạo nhiều chunks hơn nhưng mỗi chunk có cấu trúc rõ và dễ cite; RecursiveChunker gọn hơn nhưng có thể gom nhiều ý. Khi xây RAG thực tế, cần đánh giá grounding, coherence và metadata utility chứ không chỉ Hit@3.

---

## Tự đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Warm-up | 5 / 5 |
| My Approach | 10 / 10 |
| Core Implementation | 30 / 30 |
| Similarity Predictions | 5 / 5 |
| Competition Results | 10 / 10 |
| **Tổng cá nhân** | **60 / 60** |
