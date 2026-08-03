# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Trọng Đăng Khoa
**Mã sinh viên:** 2A202601964
**Nhóm:** [Tên nhóm]
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector embedding hướng gần giống nhau, cho thấy hai văn bản có cách biểu diễn ngữ nghĩa tương tự. Điểm càng gần 1 thì mức tương đồng theo hướng càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: “Người mua có thể yêu cầu hoàn tiền cho đơn hàng.”
- Câu B: “Khách hàng được gửi yêu cầu trả hàng và nhận lại tiền.”
- Tại sao tương đồng: Cả hai cùng diễn đạt quyền yêu cầu trả hàng/hoàn tiền dù dùng từ khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: “Người mua có thể yêu cầu hoàn tiền cho đơn hàng.”
- Câu B: “Ảnh sản phẩm phải do Người bán tự chụp.”
- Tại sao khác: Hai câu thuộc hai nghiệp vụ khác nhau: hoàn tiền và quy định đăng bán.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào góc giữa hai vector nên ít bị ảnh hưởng bởi độ lớn của vector. Với text embeddings, hướng thường thể hiện ngữ nghĩa hữu ích hơn khoảng cách tuyệt đối do độ dài hoặc độ lớn biểu diễn gây ra.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Theo công thức của bài: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = 23`.
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng tăng thành `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25` chunks. Overlap lớn hơn giữ thêm ngữ cảnh ở ranh giới chunk, nhưng đổi lại làm tăng số embedding, dung lượng lưu trữ và chi phí truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng sau `.`, `!`, `?`, nhờ lookbehind nên vẫn giữ dấu câu trong câu đứng trước. Văn bản rỗng hoặc chỉ có whitespace trả về `[]`; whitespace thừa trong từng câu được chuẩn hóa trước khi nhóm tối đa `max_sentences_per_chunk` câu.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự ưu tiên và chỉ gọi đệ quy với mảnh vẫn vượt `chunk_size`; các mảnh nhỏ kề nhau được ghép lại nếu còn vừa giới hạn. Base cases xử lý text rỗng, text đã đủ nhỏ, hết separator và separator rỗng; hai trường hợp cuối cắt cứng theo kích thước để không lặp vô hạn hoặc làm mất nội dung.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được embed đúng một lần và lưu thành record gồm id gốc, storage id duy nhất, content, bản sao metadata và embedding. Bộ nhớ là nguồn dữ liệu tin cậy; ChromaDB chỉ là mirror tùy chọn. Khi search, query được embed rồi tính dot product với các record, sắp xếp score giảm dần và giới hạn `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Metadata được lọc trước khi embed query và xếp hạng để kết quả không bị các record ngoài phạm vi chiếm chỗ trong top-k. `delete_document` xóa tất cả record có id gốc hoặc `metadata["doc_id"]` trùng yêu cầu, đồng thời xóa các storage id tương ứng khỏi Chroma nếu backend này đang hoạt động.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent gọi `store.search(question, top_k)` rồi đưa từng kết quả vào một khối `[CONTEXT CHUNK n]` tách biệt, kèm document id và nguồn. Prompt chứa nguyên câu hỏi và yêu cầu chỉ trả lời từ context, không thêm thông tin thiếu căn cứ, đồng thời phải nói rõ khi context không đủ trước khi gọi `llm_fn` được inject.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 42 items
============================== 42 passed in 0.09s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Người mua có thể yêu cầu hoàn tiền cho đơn hàng. | Khách hàng được gửi yêu cầu trả hàng và nhận lại tiền. | cao | Chưa đo | Chưa đánh giá |
| 2 | Người bán phải đăng ít nhất một ảnh thật tự chụp. | Sản phẩm cần có tối thiểu một hình ảnh do chính người bán chụp. | cao | Chưa đo | Chưa đánh giá |
| 3 | Người mua phải chờ phản hồi khi hủy đơn đang chờ lấy hàng. | Thực phẩm đông lạnh có thời hạn yêu cầu hoàn tiền là 24 giờ. | thấp | Chưa đo | Chưa đánh giá |
| 4 | Shopee cấm đăng bán súng và các sản phẩm có hình dạng giống vũ khí. | Vũ khí thuộc danh sách sản phẩm bị cấm hoặc hạn chế mua bán. | cao | Chưa đo | Chưa đánh giá |
| 5 | Chuyển tiền vào tài khoản ngân hàng có thể cần tối đa bốn ngày làm việc. | Sản phẩm vi phạm có thể bị xóa khỏi sàn. | thấp | Chưa đo | Chưa đánh giá |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

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
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |
