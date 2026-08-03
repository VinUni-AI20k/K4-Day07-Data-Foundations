# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine cao nghĩa là hai vector embedding **chỉ về cùng một hướng** trong không gian ngữ nghĩa, tức hai đoạn text nói về cùng một chủ đề/ý — bất kể chúng dài ngắn khác nhau hay dùng từ ngữ khác nhau. Giá trị chạy từ -1 (ngược hướng) qua 0 (không liên quan) đến 1 (trùng hướng); kiểm chứng bằng code: vector giống hệt → 1.0, vuông góc → 0.0, ngược dấu → -1.0 (4 test `TestComputeSimilarity` pass).

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn đổi trả sản phẩm trong vòng 30 ngày."
- Câu B: "Chính sách hoàn hàng cho phép gửi lại đơn hàng trong vòng một tháng."
- Tại sao tương đồng: gần như không dùng chung từ nào ("đổi trả" vs "hoàn hàng", "30 ngày" vs "một tháng") nhưng cùng một **ý định**: thời hạn trả hàng. Embedding mã hoá ngữ nghĩa chứ không mã hoá mặt chữ, nên hai câu nằm gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Tôi muốn đổi trả sản phẩm trong vòng 30 ngày."
- Câu B: "Hướng dẫn cài đặt driver máy in trên Windows."
- Tại sao khác: khác hoàn toàn miền chủ đề (chính sách TMĐT vs kỹ thuật thiết bị), không chia sẻ chủ thể, hành động hay mục tiêu nào, nên hai vector gần như trực giao (cosine ≈ 0).

> **Lưu ý khi tự kiểm bằng code:** `MockEmbedder` trong `src/embeddings.py` sinh vector từ `hashlib.md5`, tức là **giả lập xác định (deterministic) chứ không mang ngữ nghĩa**. Chạy cặp câu trên với `_mock_embed` cho kết quả ~ -0.23 (cặp CAO) và ~ -0.02 (cặp THẤP) — không phản ánh ý nghĩa, đúng như thiết kế: mock chỉ để test chạy được offline. Muốn số liệu thật cho bảng ở Mục 4 phải bật `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`) hoặc `OpenAIEmbedder`.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ dài (norm) của vector embedding phần lớn phản ánh **độ dài / số token** của đoạn text chứ không phải nội dung, nên khoảng cách Euclid sẽ phạt oan một chunk dài và một câu ngắn dù chúng nói cùng một điều. Cosine chuẩn hoá norm đi và chỉ giữ lại **hướng** — tức phần ngữ nghĩa — nên phù hợp hơn khi so một câu hỏi ngắn với các chunk tài liệu dài, đúng tình huống retrieval của Lab này.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Mỗi chunk dài 500, hai chunk liền nhau chồng nhau 50 ký tự, nên mỗi bước tiến (`step`) chỉ đi được `500 - 50 = 450` ký tự. Chunk đầu tiên "tiêu thụ" trọn 500 ký tự, các chunk sau mỗi cái thêm 450 ký tự mới:
> `ceil((length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / 450) = ceil(9950 / 450) = ceil(22.11) = 23`
> *Đáp án:* **23 chunks** — đã đối chiếu bằng code: `len(FixedSizeChunker(500, 50).chunk("x" * 10000)) == 23`.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk **tăng**: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunk (kiểm bằng code: 25). Overlap lớn hơn ⇒ step nhỏ hơn ⇒ cần nhiều chunk hơn để phủ hết tài liệu. Đánh đổi: overlap nhiều giúp một câu/ý bị cắt ngang ranh giới vẫn xuất hiện nguyên vẹn trong ít nhất một chunk (đỡ mất ngữ cảnh khi truy xuất), nhưng phải trả giá bằng nhiều bản ghi hơn trong store, nhiều lần gọi embedding hơn, và kết quả top-k dễ bị trùng lặp nội dung.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

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
