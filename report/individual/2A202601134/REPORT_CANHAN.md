# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Hoàng Long
**MSSV:** 2A202601134
**Nhóm:** Sigmoid
**Personal branch:** member/nguyen-hoang-long-recursive
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
**Trả lời:** Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau trong không gian đặc trưng — tức là hai đoạn văn bản mang ý nghĩa (semantics) tương tự nhau, bất kể độ dài tuyệt đối của vector.

**Ví dụ có độ tương tự CAO:**
**Ví dụ có độ tương tự CAO:**
- Câu A: "Làm thế nào để hủy đơn hàng?"
- Câu B: "Tôi muốn hủy đơn hàng"
- Tại sao tương đồng: cùng biểu đạt ý định hủy đơn, nghĩa của câu tương tự nhau.

**Ví dụ có độ tương tự THẤP:**
**Ví dụ có độ tương tự THẤP:**
- Câu A: "Ảnh sản phẩm phải rõ ràng"
- Câu B: "Chính sách bảo mật thông tin cá nhân"
- Tại sao khác: hai câu khác chủ đề, embedding kỳ vọng cách ly nghĩa.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
**Trả lời:** Cosine đo góc giữa hai vector, bỏ qua tỉ lệ/độ lớn, nên phù hợp khi độ dài vector không phản ánh mức độ liên quan (ví dụ embedding đã chuẩn hoá). Euclidean bị ảnh hưởng bởi chuẩn scale nên kém phù hợp cho text embeddings.

### Sigmoid (Sigmoid Activation / Score Calibration)
**Trả lời:** Sigmoid là hàm $\sigma(x)=1/(1+e^{-x})$, dùng để biến một giá trị thực thành một giá trị trong khoảng $(0,1)$. Trong hệ thống retrieval, nó có thể dùng để chuyển raw similarity score sang dạng “độ tin cậy” hoặc “xác suất” dễ diễn giải hơn, dù trong bài này mình chủ yếu dùng cosine similarity trực tiếp để xếp hạng kết quả.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

**Phép tính:**
Số chunk = ceil((length - overlap) / (chunk_size - overlap)).

Với length=10000, chunk_size=500, overlap=50:

 (10000 - 50) / (500 - 50) = 9950 / 450 = 22.111... → làm tròn lên → **23 chunks**.


**Nếu overlap = 100:**

 (10000 - 100) / (500 - 100) = 9900 / 400 = 24.75 → làm tròn lên → **25 chunks**.

Tăng overlap giúp bảo toàn ngữ cảnh giữa các chunk (giảm khả năng cắt ngang ý), nhưng tăng số chunk (chi phí lưu trữ và truy vấn).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
Tăng độ chồng chéo làm tăng số chunk (do mỗi chunk chia sẻ nhiều nội dung với chunk kế tiếp) nhưng giúp bảo toàn ngữ cảnh khi câu bị cắt qua biên. Overlap lớn hữu ích khi thông tin quan trọng có thể nằm gần ranh giới chunk, mặc đổi lại chi phí lưu trữ và truy vấn tăng.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

Sử dụng `re.split` với mẫu tách sau dấu câu cuối cùng như `(?<=[.!?])\s+` và xử lý `\.\n` để bắt trường hợp xuống dòng. Sau khi split, `strip()` từng câu và gom tối đa `max_sentences_per_chunk` câu bằng cách join bằng một khoảng trắng; trả `[]` nếu input rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

`RecursiveChunker` thử tách văn bản theo thứ tự separator ưu tiên (ví dụ `"\n\n", "\n", ". ", " ", ""`). Nếu một phần vẫn lớn hơn `chunk_size`, gọi `_split` với danh sách separator còn lại. Base case: đoạn rỗng, đoạn có độ dài ≤ `chunk_size`, hoặc danh sách separator rỗng (fallback chia theo fixed-size). Thiết kế tránh lặp vô hạn và bảo toàn nội dung.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

Mỗi `Document` được embed một lần và lưu làm record `{"id","content","metadata","embedding","index"}`. `search()` embed query một lần, tính tích vô hướng (dot product) giữa query embedding và record embedding, sort giảm dần và trả top-k record với `content`, `metadata`, `score`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

`search_with_filter` lọc records theo `metadata_filter` trước, rồi chạy _search_records trên tập con; `delete_document(doc_id)` loại mọi record có `id == doc_id` hoặc `metadata['doc_id'] == doc_id` và trả True nếu có thay đổi kích thước collection.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

Agent dựng prompt ngắn gọn: hướng dẫn LLM chỉ dùng context, danh sách context được đánh số `[1] ... [k] source=...` kèm `content`, sau đó `Question: ... Answer:`. Việc đánh số và ghi `source`/`doc_id` giúp truy vết và kiểm chứng grounding.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** 42 / 42

Test run (unittest): Ran 42 tests — OK

```
Ran 42 tests in 0.003s

OK
```

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Tôi muốn hủy đơn hàng | Làm sao để hủy đơn? | cao | -0.0535 | Không |
| 2 | Chính sách đổi trả áp dụng trong 15 ngày | Bạn có thể trả hàng trong vòng 15 ngày | cao | -0.1521 | Không |
| 3 | Sản phẩm cấm: thuốc phiện | Hàng cấm gồm ma túy và vũ khí | cao | -0.0537 | Không |
| 4 | Giao hàng chậm 3 ngày | Đơn hàng có thể bị giao muộn | cao | -0.1001 | Không |
| 5 | Ảnh sản phẩm phải rõ ràng | Hình ảnh sản phẩm cần chiếm 40% diện tích ảnh | cao | 0.2042 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
**Nhận xét:** Kết quả bất ngờ là nhiều cặp tôi dự đoán "cao" nhưng điểm thực tế (theo `MockEmbedder`) là âm hoặc rất thấp, chỉ 1/5 có điểm dương mạnh. Điều này cho thấy `MockEmbedder` trong môi trường kiểm thử không phản ánh tốt ngữ nghĩa tự nhiên — nó cho kết quả ổn định và có tính quy ước cho unit tests nhưng không nên dùng làm thước đo ngữ nghĩa thực nghiệm. Khi đánh giá thật, cần dùng embedder thực tế (sentence-transformers hoặc API) và kiểm tra phân phối điểm trước khi rút ra kết luận.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Đơn hàng do đơn vị vận chuyển không phải SPX đang ở trạng thái “Chờ lấy hàng” thì Người mua có thể hủy ngay không? | `shopee-order-cancellation` — "# Tôi có thể hủy đơn hàng không?" | 0.254 | Yes (gold in top-3) | [DEMO LLM] Answer generated.
| 2 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền... | `shopee-terms-of-service` — preview | 0.430 | No | [DEMO LLM] Answer generated.
| 3 | Ảnh sản phẩm đăng bán trên Shopee phải đáp ứng... | `shopee-terms-of-service` / fallback preview | 0.542 | Yes (gold in top-3: `shopee-product-listing-rules`) | [DEMO LLM] Answer generated.
| 4 | Vi phạm Chính sách Cấm/Hạn chế Sản phẩm... | `shopee-terms-of-service` — preview | 0.339 | No | [DEMO LLM] Answer generated.
| 5 | Nếu Người mua không nhấn “Đã nhận được hàng”... | `shopee-product-listing-rules` — preview | 0.400 | Yes (gold in top-3: `shopee-terms-of-service`) | [DEMO LLM] Answer generated.

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 3 / 5

Top-3 coverage của cấu hình được chọn là **3/5 câu hỏi**: câu 1, 3 và 5 có chunk liên quan xuất hiện trong top-3. Kết quả benchmark đầy đủ cho các cấu hình 500, 800 và 1200 được lưu trong `bench_results.json`.

**Chọn cấu hình:** `RecursiveChunker(chunk_size=500)` — selected because it maximized gold-document presence in top-3 (3/5) versus 2/5 for 800 and 1200.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Qua benchmark chung, tôi học được từ FixedSizeChunker 800/100 của Nguyễn Đức Anh rằng việc ghép lại các mảnh nhỏ và kiểm soát độ dài chunk rất quan trọng. FixedSize đạt relevant top-3 5/5, trong khi RecursiveChunker 500 trên implementation của tôi chỉ đạt 2/5, tạo 2.856 chunk với độ dài trung bình 47,12 ký tự. Điều này cho thấy RecursiveChunker không chỉ cần chọn separator tự nhiên mà còn phải repack các phần nhỏ để tránh mất ngữ cảnh và tăng chi phí retrieval.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **56 / 60** |
