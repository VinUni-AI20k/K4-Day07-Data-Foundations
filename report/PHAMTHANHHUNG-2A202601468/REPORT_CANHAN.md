# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [PHẠM THANH HƯNG]
**Nhóm:** [AETAODONG]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

> Độ tương tự cosine cao (gần bằng 1) có nghĩa là hai vector đại diện cho hai đoạn văn bản có hướng rất gần hoặc trùng nhau trong không gian vector. Điều này cho thấy hai đoạn văn bản đó mang ý nghĩa ngữ nghĩa (semantic) cực kỳ giống hoặc tương đồng với nhau

**Ví dụ có độ tương tự CAO:**
- Câu A: Con mèo đen đang nằm ngủ trên ghế sofa.
- Câu B: Một chú mèo có bộ lông màu đen đang nằm nghỉ trên chiếc ghế dài.
- Tại sao tương đồng: Dù sử dụng các từ vựng khác nhau ("mèo đen" - "chú mèo màu đen", "ghế sofa" - "ghế dài"), cả hai câu đều miêu tả cùng một hành động và chủ thể trong một ngữ cảnh giống hệt nhau, nên vector ý nghĩa của chúng rất gần nhau

**Ví dụ có độ tương tự THẤP:**
- Câu A: Ngân hàng nhà nước vừa công bố quyết định giảm lãi suất điều hành.
- Câu B: Trời hôm nay có rất nhiều mây và dự báo sẽ có mưa rào vào chiều nay.
- Tại sao khác: Hai câu này đề cập đến hai chủ đề hoàn toàn tách biệt (tài chính kinh tế và thời tiết), không hề chia sẻ bất kỳ điểm chung nào về ngữ nghĩa hay từ vựng

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid đo đạc khoảng cách tuyệt đối giữa các điểm nên dễ bị lệch do độ dài văn bản (một câu dài có vector dài hơn). Độ tương tự cosine chỉ quan tâm đến "hướng" của vector (sự phân bố tỷ lệ của các thuộc tính ý nghĩa), do đó nó đánh giá độ tương đồng ngữ nghĩa chính xác hơn mà không bị ảnh hưởng bởi độ dài ngắn của đoạn văn
### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước nhảy cho mỗi chunk là `step = chunk_size - overlap = 500 - 50 = 450`. Số lượng chunk bằng làm tròn lên của `(Tổng số ký tự / step)`. Cụ thể: `10000 / 450 = 22.22`. Làm tròn lên ta có 23 chunks
> *Đáp án:* 23 chunks
**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu overlap = 100, bước nhảy còn 400. Số chunk sẽ là làm tròn lên của `10000 / 400 = 25` chunks (tăng thêm 2 chunks). Ta muốn độ chồng chéo nhiều hơn để tránh việc cắt ngang một câu hoặc một ý quan trọng, giúp giữ lại được bối cảnh (context) đầy đủ ở phần ranh giới giữa các chunk khi đưa vào vector store

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng biểu thức chính quy `(\. |\! |\? |\.\n)` để tách văn bản nhưng vẫn giữ lại dấu câu. Trường hợp ngoại lệ (edge case) như khoảng trắng thừa hoặc khoảng trắng dư ở cuối được xử lý triệt để bằng cách gọi `.strip()` trên từng câu trước khi gộp nhóm

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy luôn cố gắng chia đoạn văn bằng dấu phân cách có độ ưu tiên cao nhất trước; nếu một đoạn sau khi chia vẫn vượt giới hạn, nó sẽ tiếp tục gọi đệ quy với dấu phân cách tiếp theo. Base case là khi chuỗi hiện tại có kích thước <= `chunk_size` (hoặc khi không còn dấu phân cách nào thì fall back về việc cắt ký tự cố định)

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Các tài liệu (chunks) được lưu trữ dưới dạng một danh sách (list) các dictionary chứa ID, nội dung, metadata và vector (embedding) trong biến bộ nhớ `_store`. Hàm `search` sẽ dùng phép tính tổng tích chập (dot product) giữa vector câu hỏi và vector từng đoạn văn, rồi sắp xếp danh sách theo điểm số từ cao xuống thấp để lấy ra top-k

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc (filter) được thực hiện TRƯỚC bằng cách duyệt và gom lại các đoạn văn khớp hoàn toàn với `metadata_filter` rồi mới thực hiện tính toán độ tương tự. Tính năng xóa (delete) được thi hành bằng cách tạo lại `_store` mới, giữ lại tất cả các bản ghi có khóa `doc_id` trong metadata khác với `doc_id` bị yêu cầu xóa

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Ngữ cảnh được nhúng (inject context) bằng cách nối chuỗi (`\n\n.join()`) nội dung của những đoạn tài liệu liên quan nhất do `store.search` tìm được. Cấu trúc prompt khá đơn giản: nối "Context: \n[Ngữ cảnh]\n\nQuestion: \n[Câu hỏi]\n\nAnswer:" để yêu cầu LLM sinh ra câu trả lời dựa vào ngữ cảnh đó

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.4, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Lenovo\anaconda3\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Lenovo\Documents\AITC\Day 7\K4-Day07-AETAODONG
plugins: anyio-4.12.1, dash-2.18.1, Faker-40.13.0, langsmith-0.8.7, asyncio-1.4.0
collecting ... collected 42 items

...
============================= 42 passed in 1.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

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
