# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lương Hoàng Minh
**Nhóm:** K4 (hoặc điền tên nhóm cụ thể của bạn)
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:* Hai vector có hướng rất gần nhau trong không gian vector đa chiều. Trong xử lý ngôn ngữ tự nhiên (NLP), điều này có nghĩa là ngữ nghĩa (semantic meaning) của hai đoạn văn bản rất giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Cửa hàng đóng cửa lúc 9h tối."
- Câu B: "Tiệm nghỉ bán vào lúc 21h."
- Tại sao tương đồng: Hai câu khác nhau về từ vựng (cửa hàng/tiệm, 9h tối/21h) nhưng truyền tải cùng một thông điệp ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi rất thích ăn quả táo."
- Câu B: "Điện thoại Apple rất đắt tiền."
- Tại sao khác: Có chung từ vựng/khái niệm liên quan tới "Apple/táo" nhưng một câu nói về trái cây ẩm thực, một câu nói về đồ công nghệ.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:* Cosine tập trung đo lường "góc/hướng" (ngữ nghĩa) và bỏ qua "độ lớn" (độ dài văn bản). Hai văn bản cùng ý nghĩa nhưng có độ dài khác nhau vẫn có Cosine cao, trong khi khoảng cách Euclid sẽ bị sai lệch lớn do sự chênh lệch độ dài vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Sử dụng công thức `ceil((length - overlap) / (chunk_size - overlap))` -> `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 22.11`
> *Đáp án:* Làm tròn lên là 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:* Số lượng chunk sẽ TĂNG LÊN (mẫu số giảm nên kết quả chia lớn hơn). Việc tăng overlap giúp đảm bảo các ý nghĩa nằm ngay ranh giới vết cắt không bị đứt đoạn, giúp truy xuất ngữ cảnh đầy đủ hơn, nhưng đánh đổi là tốn tài nguyên (token) lưu trữ hơn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu:* Sử dụng biểu thức chính quy (regex) `(?<=[.!?])\s+` để tách câu bằng khoảng trắng nằm ngay sau các dấu ngắt câu, nhờ positive lookbehind nên không bị mất dấu chấm/hỏi ở cuối câu. Ngoại lệ chuỗi rỗng được xử lý bằng cách kết hợp `.strip()` và filter danh sách kết quả.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu:* Dùng thuật toán đệ quy thử cắt bằng các separator ưu tiên giảm dần. Base case là khi chuỗi đủ ngắn (<= chunk_size) hoặc đã cạn kiệt danh sách separator. Các chuỗi con sau khi cắt sẽ được gom nhóm liền kề với nhau cho đến khi tiệm cận giới hạn `chunk_size` để tối ưu bộ nhớ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
```

**Số lượng bài test vượt qua (pass):** __ / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | | | cao / thấp | | |
| 2 | | | cao / thấp | | |
| 3 | | | cao / thấp | | |
| 4 | | | cao / thấp | | |
| 5 | | | cao / thấp | | |

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
