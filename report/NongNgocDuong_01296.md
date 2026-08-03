# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nông Ngọc Dương
**Nhóm:** ARAMHONLOAN
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
Hai vector embedding cùng hướng hoặc gần cùng hướng, nghĩa là hai đoạn văn được mô hình biểu diễn với nội dung/ngữ nghĩa tương tự nhau. Điểm càng gần 1 thì mức tương đồng càng cao.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua cần gửi yêu cầu đổi trả khi sản phẩm bị lỗi.
- Câu B: Khách hàng có thể yêu cầu trả lại hàng nếu hàng bị hỏng.
- Tại sao tương đồng: Cả hai cùng nói về hành động yêu cầu đổi trả do sản phẩm có lỗi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người bán phải mô tả chính xác tình trạng sản phẩm.
- Câu B: Hôm nay thời tiết có mưa lớn.
- Tại sao khác: Hai câu thuộc hai chủ đề và mục đích hoàn toàn khác nhau.

**Tại sao độ tương tự cosine được ưu tiên hơn khoảng cách Euclid cho text embeddings?**
Cosine tập trung vào hướng của vector, nên ít bị ảnh hưởng bởi độ lớn vector hoặc độ dài văn bản. Khoảng cách Euclid đo cả độ lớn, do đó hai văn bản gần nghĩa vẫn có thể bị xem là xa nhau nếu norm của vector khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`. Bao nhiêu chunks?**

```text
step = chunk_size - overlap = 500 - 50 = 450
số chunk = ceil((10.000 - 50) / 450)
          = ceil(9.950 / 450)
          = ceil(22,11...) = 23
```

**Đáp án:** 23 chunks.

**Nếu overlap tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn overlap nhiều hơn?**

```text
step mới = 500 - 100 = 400
số chunk = ceil((10.000 - 100) / 400)
          = ceil(24,75) = 25
```

Số chunk tăng từ 23 lên 25 vì mỗi lần dịch cửa sổ chỉ tiến 400 ký tự. Overlap lớn hơn giúp bảo toàn ý nằm ở ranh giới hai chunk và tăng khả năng truy xuất đủ ngữ cảnh, nhưng đổi lại tốn thêm lưu trữ và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk` — hướng tiếp cận:**
Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng hoặc xuống dòng đứng sau dấu kết thúc câu, đồng thời giữ dấu câu trong nội dung. Sau khi loại chuỗi rỗng và khoảng trắng thừa, các câu được nhóm tuần tự theo `max_sentences_per_chunk`; văn bản rỗng trả về danh sách rỗng.

**`RecursiveChunker.chunk` / `_split` — hướng tiếp cận:**
Thuật toán thử lần lượt các separator từ cấu trúc lớn đến nhỏ: đoạn văn, dòng, câu, từ và cuối cùng là ký tự. Các mảnh vừa kích thước được ghép lại đến sát `chunk_size`; mảnh quá dài được đệ quy với separator tiếp theo. Base case là nội dung đã không vượt `chunk_size`; nếu hết separator, hàm cắt cứng theo số ký tự để luôn kết thúc.

### Lớp EmbeddingStore

**`add_documents` + `search` — hướng tiếp cận:**
Mỗi `Document` được chuẩn hóa thành bản ghi gồm id, nội dung, bản sao metadata có `doc_id`, embedding và storage id duy nhất. Store luôn duy trì bản in-memory để hành vi ổn định; nếu ChromaDB có sẵn thì đồng bộ thêm sang collection. Khi tìm kiếm, query được embed một lần, tính dot product với từng bản ghi, sắp xếp giảm dần và lấy tối đa `top_k`.

**`search_with_filter` + `delete_document` — hướng tiếp cận:**
Metadata được lọc chính xác theo tất cả cặp khóa-giá trị trước khi tính similarity, tránh để kết quả không đúng phạm vi chiếm top-k. `delete_document` tìm tất cả chunk có cùng `metadata["doc_id"]`, xóa chúng khỏi bộ nhớ và backend tùy chọn, trả về `True` chỉ khi thực sự có bản ghi bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer` — hướng tiếp cận:**
Agent truy xuất top-k chunk, đánh số từng nguồn rồi đưa chúng vào phần `Ngữ cảnh` của prompt cùng câu hỏi. System instruction yêu cầu chỉ dùng ngữ cảnh đã cung cấp và nói rõ khi thiếu thông tin, nhờ đó giảm hallucination; prompt cuối cùng được chuyển nguyên vẹn cho `llm_fn` để dễ thay thế mô hình thật hoặc mock trong test.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (Test Results)

Môi trường hiện tại chưa cài executable `pytest`. Vì `tests/test_solution.py` dùng hoàn toàn `unittest.TestCase`, tôi chạy trực tiếp cùng bộ 42 test bằng lệnh tương đương:

```text
$ python3 -m unittest -v tests.test_solution
...
----------------------------------------------------------------------
Ran 42 tests in 0.006s

OK
```

Ngoài ra, `python3 -m py_compile src/chunking.py src/store.py src/agent.py ingest.py main.py` không phát hiện lỗi cú pháp và `python3 ingest.py` trả về `ingest self-check OK`.

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Do môi trường chưa có `sentence-transformers`, tôi dùng feature-hashing embedding offline 512 chiều: tách token chữ thường, bỏ stopword phổ biến, hash token vào vector, chuẩn hóa L2 rồi gọi đúng hàm `compute_similarity()`. Phép đo này tái lập được nhưng chủ yếu phản ánh tương đồng từ vựng; cần chạy lại bằng local multilingual embedder trước khi dùng để kết luận về ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-------|-------|---------|--------------|-------|
| 1 | Người mua cần gửi yêu cầu đổi trả khi hàng bị lỗi. | Người mua gửi yêu cầu trả hàng nếu sản phẩm bị lỗi. | cao | 0,8040 | Có |
| 2 | Người bán phải cung cấp giá và mô tả chính xác. | Thông tin đăng bán phải có giá và mô tả chính xác. | cao | 0,6667 | Có |
| 3 | Sản phẩm bị cấm không được đăng bán. | Hôm nay thời tiết có mưa lớn. | thấp | 0,0000 | Có |
| 4 | Yêu cầu đổi trả cần kèm bằng chứng phù hợp. | Đổi trả hàng lỗi phải có bằng chứng. | cao | 0,5443 | Có |
| 5 | Người bán phản hồi yêu cầu đổi trả. | Người mua cung cấp thông tin sản phẩm. | thấp | 0,1250 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
Cặp 5 vẫn có điểm 0,1250 dù khác hành động và vai trò, do còn token chung mang tính miền như “người” và có thể có va chạm hash. Kết quả cho thấy một embedding dựa trên từ vựng có thể đánh giá cao các từ chung nhưng bỏ sót quan hệ ngữ nghĩa; mô hình multilingual đã huấn luyện sẽ phù hợp hơn cho benchmark chính thức.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Thiết lập benchmark

- Corpus hiện có: 2 tài liệu khởi động trong `data/k4_ecommerce`, tạo thành 5 chunks.
- Chunker: `RecursiveChunker(chunk_size=300)`.
- Embedding: feature hashing offline 512 chiều như Phần 4.
- Agent: bộ sinh câu trả lời extractive offline, chọn câu trong top-3 có nhiều token nội dung trùng câu hỏi nhất.
- Câu 5 lọc trước với `metadata_filter={"customer_role": "buyer"}`.

> **Giới hạn dữ liệu:** `REPORT_NHOM.md` chưa có bộ 5 câu hỏi chung và hai URL trong corpus vẫn là `example.com`. Vì vậy đây là benchmark cá nhân tạm thời, không được xem là kết quả nhóm chính thức. Khi nhóm chốt corpus và gold answers, cần chạy lại đúng năm câu chung và thay bảng này.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? | Câu trả lời của Agent (tóm tắt) |
|---|-----------------|--------------------------------------|------------|---------------------|---------------------------------|
| 1 | Người mua cần làm gì khi hàng bị lỗi hoặc không đúng mô tả? | Gửi yêu cầu đúng thời hạn và kèm bằng chứng phù hợp | 0,5231 | Có | Cần kèm bằng chứng; còn thiếu ý về thời hạn |
| 2 | Ai có trách nhiệm phản hồi yêu cầu đổi trả? | Quy trình người mua gửi yêu cầu và thời hạn đổi trả | 0,3487 | Một phần; bằng chứng đúng có trong top-3 | Agent trả lời về thời hạn gửi yêu cầu, chưa trả lời đúng chủ thể là người bán |
| 3 | Người bán phải cung cấp những thông tin sản phẩm nào? | Thông tin chính xác gồm giá, mô tả và tình trạng hàng | 0,5417 | Có | Giá, mô tả và tình trạng hàng |
| 4 | Sản phẩm bị hạn chế hoặc bị cấm có được đăng bán không? | Sản phẩm hạn chế hoặc cấm không được đăng bán | 0,6250 | Có | Không được đăng bán |
| 5 | Yêu cầu đổi trả hàng lỗi cần kèm theo gì? | Yêu cầu phải kèm bằng chứng phù hợp | 0,5592 | Có | Bằng chứng phù hợp |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

Theo rubric 2 điểm/câu, tôi tự chấm 8/10 cho benchmark tạm: câu 1 và 2 mỗi câu 1 điểm vì agent trả lời thiếu/sai trọng tâm; ba câu còn lại mỗi câu 2 điểm.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
Repository chưa ghi kết quả của thành viên khác nên tôi chưa thể đưa ra so sánh có bằng chứng. Bài học rút ra ở thời điểm này là mọi thành viên phải dùng cùng corpus, cùng năm query và cùng gold answer; nếu không, chênh lệch điểm có thể đến từ dữ liệu hoặc embedder chứ không phải chiến lược chunking.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
