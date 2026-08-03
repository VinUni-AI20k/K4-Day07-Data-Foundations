# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Hoàng Xuân Quân
**Nhóm:** C53
**Ngày:** 02/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là góc giữa 2 vector embedding rất nhỏ, phản ánh rằng 2 đoạn văn bản có nội dung và ý nghĩa ngữ nghĩa (semantic meaning) rất tương đồng với nhau, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Chính sách đổi trả hàng hoàn tiền của Shopee như thế nào?
- Câu B: Shopee quy định quy trình trả hàng và nhận lại tiền ra sao?
- Tại sao tương đồng: Cả hai câu có từ ngữ khác nhau nhưng cùng hỏi về quy trình và chính sách trả hàng hoàn tiền.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Hướng dẫn đóng gói sản phẩm hoàn trả an toàn.
- Câu B: Thời gian giao hàng dự kiến của đơn đồ ăn ShopeeFood.
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn khác nhau (đóng gói hàng trả vs vận chuyển đồ ăn).

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity chỉ tập trung đo góc (hướng ngữ nghĩa) của vector mà không bị ảnh hưởng bởi độ dài văn bản. Trong khi đó, khoảng cách Euclid bị tác động bởi độ dài vector, khiến 2 câu cùng ý nghĩa nhưng khác độ dài lại có khoảng cách Euclid rất xa nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.111) = 23`
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số lượng chunk sẽ **TĂNG** lên (từ 23 lên 25 chunks, vì `ceil((10000-100)/(500-100)) = 25`). Ta muốn tăng độ chồng chéo để giữ nguyên ngữ cảnh nối liền giữa ranh giới các đoạn văn, tránh làm mất thông tin quan trọng khi câu bị ngắt đôi. Đánh đổi lại là tăng số lượng chunk cần nhúng và tăng chi phí lưu trữ/tính toán.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex `re.split(r"(?<=[.!?])\s+", text)` để tách các câu sau dấu `.`, `!`, `?` mà không làm mất dấu câu. Sau đó gom nhóm tối đa `max_sentences_per_chunk` câu lại thành 1 chunk bằng list comprehension `sentences[i:i+limit]`. Xử lý edge case văn bản rỗng hoặc khoảng trắng bằng `.strip()`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy `_split` duyệt danh sách `separators` theo thứ tự ưu tiên (`\n\n` -> `\n` -> `. ` -> ` ` -> `""`). Base case là khi chuỗi nhỏ hơn `chunk_size` hoặc hết separator (fallback về cắt cố định). Khi một đoạn vẫn vượt kích thước sau khi split, gọi đệ quy với cấp separator tiếp theo.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ in-memory dưới dạng danh sách dict gồm `id`, `content`, `metadata`, và `embedding`. Khi `search`, tính tích vô hướng (dot product) giữa vector query embedding và embedding của từng record, sau đó sắp xếp giảm dần theo điểm `score` để lấy `top_k` kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc (pre-filtering) danh sách record thỏa mãn tất cả cặp key/value trong `metadata_filter` trước, rồi mới đưa vào hàm `_search_records` để xếp hạng. `delete_document` lọc bỏ tất cả record có `metadata['doc_id']` khớp với `doc_id` được yêu cầu xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Gọi `store.search` lấy `top_k` chunk, ghép thành khối context có đánh số `[1]`, `[2]` kèm tên tài liệu trích dẫn (`doc_id`). Prompt đóng gói gồm yêu cầu LLM chỉ trả lời dựa vào context được cấp và nêu rõ nếu thiếu thông tin, sau đó gọi `llm_fn(prompt)`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
python3 -m unittest tests/test_solution.py
..........................................
----------------------------------------------------------------------
Ran 42 tests in 0.002s

OK
```

**Số lượng bài test vượt qua (pass):** **42** / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả Shopee thế nào? | Quy định hoàn tiền của Shopee ra sao? | cao | 0.0024 | Có |
| 2 | Thời gian giao hàng dự kiến | Cách đóng gói sản phẩm hoàn trả | thấp | -0.0019 | Có |
| 3 | Hàng bị vỡ khi vận chuyển | Sản phẩm móp vỡ khi nhận hàng | cao | 0.1599 | Có |
| 4 | Thanh toán bằng thẻ Visa | Lập trình Python cơ bản | thấp | 0.1778 | Bất ngờ |
| 5 | Người bán hủy đơn hàng | Shop tự hủy đơn của khách | cao | -0.1411 | Bất ngờ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là với mock embedder, điểm số giữa các cặp từ ngữ đồng nghĩa đôi khi ra thấp hoặc âm do mock dựa trên hash xác định ngẫu nhiên của chuỗi. Điều này cho thấy mock chỉ hợp cho unit test, còn để đánh giá ngữ nghĩa thực tế thì bắt buộc phải chuyển sang trình nhúng thật (`LocalEmbedder` / `sentence-transformers`).

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

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5** / 5

### Phân tích lỗi & Thử nghiệm A/B Filter (Failure Analysis)

1. **Thử nghiệm A/B Metadata Filter (Câu hỏi 4):**
   - **Không lọc (No Filter):** Tìm ra top-1 chunk thuộc quy trình dành cho Người mua (score = 0.281), dẫn đến Agent trả lời nhầm hạn thời gian của Buyer.
   - **Có lọc (`customer_role: seller`):** Loại bỏ hoàn bộ dữ liệu Buyer, giữ lại đúng tài liệu Kênh Quản Lý Shop với top-1 score = 0.1712, Agent trả lời chính xác mốc **2 ngày**.
   - **Đánh giá Metadata Utility:** Lọc siêu dữ liệu trước (pre-filtering) rất quan trọng giúp nâng cao Precision và loại bỏ nhiễu trùng từ vựng.

2. **Phân tích trường hợp lỗi điển hình (Failure Case):**
   - **Query gặp lỗi xếp hạng:** Câu 1 (*Tôi có bao nhiêu ngày để gửi yêu cầu Trả hàng/Hoàn tiền...*).
   - **Bằng chứng Top-k:** Top-1 trả về file `cach-dong-goi-hang-hoan-tra` (score = 0.2771) chỉ chứa hướng dẫn đóng gói thay vì file gốc chứa mốc 15 ngày (`quy-dinh-chung-tra-hang-hoan-tien`).
   - **Nguyên nhân (Root cause):** Cosine similarity đo độ tương đồng chủ đề chung ("trả hàng/hoàn tiền") chứ không đo mật độ thông tin con số.
   - **Đề xuất cải thiện:** Thêm kỹ thuật Hybrid Search (kết hợp BM25 keyword search + Vector Embedding) và prepend tên tiêu đề phần (`section_heading`) vào từng chunk.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc tách chunk đệ quy (RecursiveChunker) kết hợp lọc siêu dữ liệu (`customer_role`) giúp hệ thống truy xuất chính xác các quy định riêng cho Người bán (seller) mà không bị nhầm lẫn với hướng dẫn của Người mua (buyer).

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


