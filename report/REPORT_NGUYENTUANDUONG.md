# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Tuấn Dương
**Nhóm:** B1-2
**Ngày:** 04-08-2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao thể hiện rằng vector của câu truy vấn và vector của đoạn tài liệu có mức độ tương đồng rất lớn về mặt ngữ nghĩa. Điều này giúp hệ thống dễ dàng nhận biết và ưu tiên trích xuất đúng những đoạn thông tin liên quan nhất để đưa vào mô hình sinh câu trả lời.

**Ví dụ có độ tương tự CAO:**
- Câu A: Nguồn cung cấp dầu mỏ của Việt Nam chủ yếu đến từ đâu?
- Câu B: Hãy cho biết các mỏ dầu quan trọng ở Việt Nam?
- Tại sao tương đồng: Cả hai câu đều hỏi về nguồn cung cấp dầu của Việt Nam, một câu hỏi có tính khái quát và một câu hỏi yêu cầu thông tin cụ thể hơn, do đó có độ tương đồng cao về mặt ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Nguồn cung cấp dầu mỏ của Việt Nam chủ yếu đến từ đâu?
- Câu B: Chất lượng không khí tại Hà Nội hôm nay như thế nào?
- Tại sao khác: Câu A hỏi về nguồn cung cấp dầu của Việt Nam, trong khi câu B hỏi về chất lượng không khí tại Hà Nội. Hai chủ đề này hoàn toàn khác nhau, do đó có độ tương đồng thấp.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Độ tương tự cosine được ưu tiên vì nó tập trung đo góc (hướng) giữa các vector thay vì độ lớn, giúp đánh giá chính xác sự tương đồng ngữ nghĩa mà không bị ảnh hưởng bởi độ dài hay số lượng từ của văn bản. Ngược lại, khoảng cách Euclid bị chi phối bởi chiều dài vector, dễ khiến hai đoạn văn dù có cùng nội dung nhưng khác độ dài bị đánh giá sai là ít liên quan đến nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> - Bước dịch chuyển (stride) giữa các chunk: 500 - 50 = 450 (ký tự)
> - Công thức: Số chunks = 1 + ceil((Độ dài tài liệu - chunk_size) / stride)
> - Chi tiết: 1 + ceil((10,000 - 500) / 450) = 1 + ceil(9,500 / 450) = 1 + ceil(21.11) = 1 + 22 = 23

> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100, số lượng chunk sẽ tăng lên (từ 23 thành 25 chunks) vì bước dịch chuyển giữa các chunk bị thu nhỏ lại (còn 400 ký tự). Việc tăng overlap giúp bảo toàn tốt hơn ngữ nghĩa và ngữ cảnh ranh giới giữa các đoạn, tránh việc thông tin quan trọng bị gián đoạn hoặc đứt gãy khi trích xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Sử dụng regex `(?<=[.!?])\s+|(?<=\.)\n+` để tách câu tại các dấu kết thúc (`.`, `!`, `?`) kèm khoảng trắng hoặc ký tự xuống dòng. Trường hợp ngoại lệ như câu chỉ chứa toàn khoảng trắng (whitespace) được xử lý bằng cách dùng `strip()` và lọc bỏ các đoạn trống rỗng trước khi gộp thành chunk dựa trên `max_sentences_per_chunk`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy duyệt qua mảng `separators`. Base case (trường hợp cơ sở) là khi đoạn văn bản nhỏ hơn `chunk_size` hoặc không còn `separators` nào, khi đó mảnh văn bản nguyên vẹn được trả về. Nếu một mảnh văn bản lớn hơn `chunk_size`, nó sẽ tiếp tục bị cắt bằng separator kế tiếp và gọi đệ quy, cuối cùng các mảnh nhỏ được ghép lại để có độ dài phù hợp và không vượt quá kích thước giới hạn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi tài liệu sau khi được tính vector nhúng (embedding) sẽ được đóng gói cùng với `id`, `content` và `metadata` rồi đưa vào mảng `self._store` (In-memory store). Khi tìm kiếm (`search`), hệ thống lặp qua toàn bộ mảng này và tính độ tương tự giữa vector truy vấn và vector của chunk thông qua tích vô hướng (dot-product), gán score rồi sắp xếp giảm dần.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Việc lọc (`search_with_filter`) được thực hiện **trước** (pre-filtering), chỉ giữ lại các chunk có metadata khớp với điều kiện lọc, sau đó mới tính dot-product để tăng tốc quá trình search. Việc xóa (`delete_document`) thực hiện bằng cách cập nhật lại (list comprehension) `self._store` để chỉ giữ lại các chunk có `doc_id` không bị trùng với doc_id cần xoá.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Hàm `answer` gọi `store.search` truyền vào question để lấy top-k chunk liên quan nhất. Các chunk content này được gộp lại với nhau (ngăn cách bởi dấu xuống dòng `\n`) để làm ngữ cảnh (context), sau đó ghép thành một Prompt khuôn mẫu bao gồm Context và Question, rồi gọi tới hàm `llm_fn` để lấy câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

Lệnh đã chạy để kiểm thử code trong thư mục của tôi:
```powershell
$env:LAB_SOLUTION_PACKAGE="src.duongnt-01966"; pytest tests/ -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-7.4.4, pluggy-1.0.0 -- C:\ProgramData\anaconda3\python.exe
cachedir: .pytest_cache
rootdir: D:\vin-ai\lab-07\K4-Day07-Data-Foundations-B1-2
plugins: anyio-4.14.2
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
... (Lược bỏ chi tiết các test passed) ...
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.15s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Chính sách đổi trả hàng miễn phí trong vòng 7 ngày." | "Bạn có thể hoàn trả sản phẩm mà không mất phí trong 1 tuần." | cao | 0.5917 | Đúng |
| 2 | "Khách hàng thanh toán qua thẻ tín dụng sẽ được giảm 10%." | "Phương thức thanh toán bằng thẻ tín dụng mang lại ưu đãi giảm giá 10%." | cao | 0.8032 | Đúng |
| 3 | "Sản phẩm được bảo hành 12 tháng tại các trung tâm ủy quyền." | "Cửa hàng mở cửa từ 8h sáng đến 10h tối mỗi ngày." | thấp | 0.3267 | Đúng |
| 4 | "Apple ra mắt dòng iPhone mới với camera cải tiến." | "Quả táo là một loại trái cây chứa nhiều vitamin C." | thấp | 0.3073 | Đúng |
| 5 | "Làm thế nào để thay đổi địa chỉ giao hàng?" | "Hướng dẫn cập nhật thông tin nhận hàng trên hệ thống." | cao | 0.5601 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp số 4 (Apple công nghệ vs quả táo). Dù cùng dịch ra có từ liên quan đến "táo", nhưng vector embedding vẫn đánh giá độ tương đồng rất thấp (0.3073). Điều này cho thấy các mô hình ngôn ngữ không chỉ so sánh từ khóa mà thực sự hiểu ngữ cảnh (contextual representation) của từ trong câu.

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
