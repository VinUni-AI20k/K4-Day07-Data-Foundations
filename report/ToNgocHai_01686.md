# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Tô Ngọc Hải

**Mã sinh viên:** 2A202601686

**Nhóm:** ARAMHONLOAN

**Ngày:** 2026-08-03

> Package bài làm: `src.K4_2A202601686_ToNgocHai`. Phần kết quả truy xuất sẽ được cập nhật sau khi nhóm thống nhất corpus thật và 5 benchmark queries.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector embedding hướng gần giống nhau. Trong trường hợp mô hình embedding biểu diễn ngữ nghĩa tốt, điều này cho thấy hai đoạn văn có nội dung hoặc ý nghĩa gần nhau, dù chúng không nhất thiết dùng cùng từ ngữ.

**Ví dụ có độ tương tự cao:**

- Câu A: “Người mua có thể yêu cầu đổi trả hàng bị lỗi.”
- Câu B: “Khách hàng được trả lại sản phẩm nếu sản phẩm có lỗi.”
- Lý do: Hai câu cùng nói về quyền đổi trả của người mua khi sản phẩm bị lỗi.

**Ví dụ có độ tương tự thấp:**

- Câu A: “Chính sách đổi trả bảo vệ quyền lợi người mua.”
- Câu B: “Hôm nay trời có mưa lớn.”
- Lý do: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

**Tại sao cosine similarity thường được ưu tiên hơn Euclidean distance cho text embeddings?**

Cosine similarity đo góc giữa hai vector nên tập trung vào hướng biểu diễn ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn của vector. Euclidean distance phụ thuộc cả hướng lẫn độ lớn, vì vậy hai vector cùng hướng nhưng khác chuẩn vẫn có thể bị xem là xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:**

```text
step = chunk_size - overlap = 500 - 50 = 450
chunk_count = ceil((document_length - overlap) / step)
            = ceil((10000 - 50) / 450)
            = ceil(22,111...)
            = 23 chunks
```

**Nếu overlap tăng lên 100:**

```text
step = 500 - 100 = 400
chunk_count = ceil((10000 - 100) / 400)
            = ceil(24,75)
            = 25 chunks
```

Số chunk tăng từ 23 lên 25 vì mỗi lần cửa sổ chỉ tiến thêm 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh nằm ở ranh giới giữa hai chunk, nhưng làm tăng dung lượng lưu trữ và chi phí embedding/tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`:**

Tôi chuẩn hóa khoảng trắng ở hai đầu rồi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng hoặc xuống dòng ngay sau dấu kết thúc câu. Các câu rỗng bị loại bỏ, sau đó danh sách được gom theo `max_sentences_per_chunk`. Giá trị cấu hình nhỏ hơn 1 được đưa về 1; văn bản rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split`:**

Thuật toán lần lượt thử các separator theo mức ưu tiên `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là ký tự. Nếu một phần vẫn dài hơn `chunk_size`, hàm tiếp tục đệ quy với separator kế tiếp; nếu không còn separator, văn bản được cắt cứng theo số ký tự. Các phần nhỏ được ghép lại tối đa đến `chunk_size`, đồng thời separator được gắn lại để hạn chế làm mất cấu trúc nội dung.

### Lớp EmbeddingStore

**`add_documents` + `search`:**

Mỗi `Document` được chuyển thành record gồm ID nội bộ duy nhất, nội dung, bản sao metadata và vector embedding. Trường `doc_id` được bổ sung từ `Document.id` nếu metadata chưa có. Khi tìm kiếm, truy vấn được embed một lần, tính dot product với từng vector đã chuẩn hóa, sắp xếp điểm giảm dần và lấy tối đa `top_k` kết quả.

**`search_with_filter` + `delete_document`:**

Metadata được lọc trước khi tính similarity để tránh xếp hạng các ứng viên không hợp lệ. Một record thỏa bộ lọc khi tất cả cặp khóa–giá trị được yêu cầu đều khớp. `delete_document` loại toàn bộ record có `metadata["doc_id"]` tương ứng và trả về `True` chỉ khi kích thước store thực sự giảm.

### Tác tử KnowledgeBaseAgent

**`answer`:**

Agent tìm `top_k` chunk liên quan, đánh số từng nguồn rồi ghép chúng vào phần “Ngữ cảnh” của prompt. Prompt yêu cầu LLM chỉ dùng thông tin đã truy xuất và thừa nhận không biết nếu context không đủ, nhằm giảm hallucination. Cuối cùng, prompt được chuyển cho `llm_fn` đã inject qua constructor để dễ kiểm thử hoặc thay thế backend.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh chạy trên Python 3.11:

```powershell
$env:LAB_SOLUTION_PACKAGE="src.K4_2A202601686_ToNgocHai"
uv run --python 3.11 --with-requirements requirements.txt python -m pytest tests -v
```

Kết quả:

```text
platform win32 -- Python 3.11.15, pytest-9.1.1
collected 51 items
======================== 51 passed, 1 warning in 0.08s ========================
```

Cảnh báo duy nhất là pytest không tạo được thư mục cache do quyền ghi; cảnh báo không liên quan đến logic bài làm.

**Số lượng bài test vượt qua:** **51 / 51** (gồm 42 test cốt lõi và 9 test được bổ sung sau khi đồng bộ benchmark).

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Tôi dự đoán theo ngữ nghĩa trước khi chạy. Điểm thực tế bên dưới dùng mô hình đa ngữ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` và `compute_similarity()` trong package cá nhân.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua có thể yêu cầu đổi trả hàng bị lỗi. | Khách hàng được trả lại sản phẩm nếu sản phẩm có lỗi. | Cao | 0,7968 | Có |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Nhà bán hàng cần cung cấp thông tin đúng về sản phẩm. | Cao | 0,8943 | Có |
| 3 | Sản phẩm bị cấm không được đăng bán. | Người bán không được niêm yết hàng hóa thuộc danh mục cấm. | Cao | 0,8739 | Có |
| 4 | Chính sách đổi trả bảo vệ người mua. | Hôm nay trời có mưa lớn. | Thấp | 0,7609 | Không |
| 5 | Người mua cần gửi bằng chứng khi hàng không đúng mô tả. | Python là một ngôn ngữ lập trình bậc cao. | Thấp | 0,1979 | Có |

**Nhận xét:**

Cặp 4 gây bất ngờ nhất: hai câu khác chủ đề nhưng vẫn đạt 0,7609. Điều này cho thấy một điểm cosine đơn lẻ không đủ để kết luận liên quan; mô hình có thể chịu ảnh hưởng bởi cách biểu diễn câu ngắn hoặc không gian embedding đa ngữ. Trong retrieval cần so sánh thứ hạng trên cùng corpus, kiểm tra nội dung top-k và dùng metadata thay vì áp một ngưỡng similarity cố định.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập benchmark

- Benchmark frozen: `aramhonloan-k4-v1`, gồm đúng 5 câu hỏi chung của nhóm.
- Corpus: 5 tài liệu trong `data/k4_ecommerce`.
- Package: `src.K4_2A202601686_ToNgocHai`.
- Chiến lược: `RecursiveChunker(chunk_size=500)`, tạo 22 chunks.
- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- Retrieval chính thức áp dụng `customer_role` và `category` của từng benchmark case trước khi xếp hạng.
- Kết quả đầy đủ: `results/ToNgocHai_recursive.json`.

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Relevant? | Câu trả lời Agent (tóm tắt) |
|---|---|---|---:|---|---|
| 1 | Người mua có bao lâu để yêu cầu trả hàng/hoàn tiền; thực phẩm tươi sống khác thế nào? | `returns-policy`, chunk 0: thời hạn 15 ngày và 24 giờ | 0,7666 | Có | Trả lời đủ 15 ngày và 24 giờ |
| 2 | Hoàn tiền thẻ tín dụng/ghi nợ mất bao lâu? | `payment-policy`, chunk 3: hoàn về thẻ trong 7–14 ngày làm việc | 0,8417 | Có | Trả lời đủ 7–14 ngày và phụ thuộc ngân hàng |
| 3 | Người bán chuẩn bị đơn thường bao lâu; trễ thì sao? | `shipping-policy`, chunk 4: tối đa 1,5 ngày, trễ bị tự động hủy | 0,8334 | Có | Trả lời đủ thời hạn và hậu quả |
| 4 | Phí xử lý giao dịch từ tháng 5/2026 là bao nhiêu? | `seller-fees`, chunk 3: phí 6%, đã gồm thuế GTGT | 0,7766 | Có | Trả lời đủ mức phí và thuế |
| 5 | Shopee xử lý sản phẩm vi phạm đăng bán thế nào? | `seller-listing`, chunk 3: xóa sản phẩm và chế tài tài khoản | 0,8114 | Có | Nêu việc xóa nhưng thiếu “tạm khóa/khóa tài khoản” |

**Số câu hỏi có chunk liên quan trong top-3:** **5 / 5**. Cả năm tài liệu mong đợi đều đứng top-1; điểm retrieval theo evaluator chung là **9 / 10**, điểm top-1 trung bình là **0,8059**.

**Phân tích lỗi:**

Q5 là trường hợp duy nhất mất điểm. Retrieval đã đưa đúng `seller-listing` chunk 3 lên top-1, nhưng hàm tạo câu trả lời extractive ưu tiên ba fragment có nhiều token trùng query nên chỉ giữ ý “tự động xóa”, bỏ hai fact “tạm khóa” và “khóa tài khoản”. Vì vậy lỗi nằm ở answer selection chứ không nằm ở Recursive Chunking hoặc retrieval. Có thể cải thiện bằng cách chọn cả cụm bullet cùng heading, tăng số fragment, hoặc rerank fragment theo coverage của các ý chưa được trả lời.

**Điều học được khi so sánh:**

Kết quả Document-Aware của thành viên Nguyễn Đức Anh cũng đạt 9/10 nhưng dùng cấu trúc heading và tạo nhiều chunk có ranh giới rõ hơn. Recursive Chunking của tôi đạt cùng điểm với 22 chunks và top-1 trung bình 0,8059; điều này cho thấy separator ưu tiên vẫn giữ đủ các đoạn chính sách cần thiết trên corpus hiện tại. Tuy nhiên cần so sánh thêm số chunk, độ dài trung bình và coherence giữa các thành viên trước khi kết luận chiến lược tốt nhất.

---

## Tự đánh giá phần cá nhân

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận của tôi | 10 / 10 |
| Hoàn thiện code — 51/51 tests | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 9 / 10 |
| **Tổng phần đã hoàn thành** | **59 / 60** |

> Điểm tự đánh giá hiện tại là 59/60; một điểm bị trừ ở Q5 do câu trả lời extractive thiếu hai fact dù retrieval đúng tài liệu ở top-1.
