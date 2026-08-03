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
> Hai vector embedding chỉ gần như cùng một hướng trong không gian ngữ nghĩa, tức hai đoạn văn bản nói về cùng chủ đề / cùng ý định. Điểm gần 1.0 là rất giống, gần 0 là không liên quan, âm là ngược hướng ngữ nghĩa.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Tôi muốn trả lại đôi giày đã mua tuần trước."
- Câu B: "Làm thế nào để gửi yêu cầu hoàn trả sản phẩm đã đặt?"
- Tại sao tương đồng: cùng ý định "trả hàng", chia sẻ trường từ vựng (trả lại / hoàn trả, mua / đặt, sản phẩm). Cách diễn đạt khác nhau nhưng embedding bắt được ý nghĩa chứ không bắt từ khóa, nên vẫn nằm gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Thời gian nhận tiền hoàn thường là 7–14 ngày làm việc."
- Câu B: "Python là ngôn ngữ lập trình thông dịch, kiểu động."
- Tại sao khác: hai chủ đề hoàn toàn tách biệt (chính sách hoàn tiền TMĐT với đặc điểm ngôn ngữ lập trình), không có khái niệm nền chung nào để embedding kéo hai vector về cùng hướng.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc nên bỏ qua độ lớn (magnitude) của vector — một chunk dài và một câu hỏi ngắn cùng chủ đề vẫn cho điểm cao, trong khi Euclid bị phạt chỉ vì chênh lệch độ dài/chuẩn vector. Ngoài ra ở số chiều lớn, khoảng cách Euclid giữa các điểm co lại gần bằng nhau (curse of dimensionality) nên mất khả năng phân biệt, còn cosine vẫn tách được tốt.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Bước nhảy (step) của cửa sổ trượt: `step = chunk_size - overlap = 500 - 50 = 450`.
> Chunk đầu phủ từ vị trí 0 và mỗi chunk sau dịch thêm 450 ký tự, nên số chunk là:
> `n_chunks = ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = ceil(21.11) + 1 = 22 + 1 = 23`
> Kiểm tra lại theo vòng lặp trong `FixedSizeChunker.chunk`: các vị trí bắt đầu là 0, 450, 900, …, 9900 (23 giá trị); tại `start = 9900` thì `9900 + 500 ≥ 10000` nên vòng lặp cắt (break). Chunk cuối là `text[9900:10400]`, thực tế chỉ còn 100 ký tự.
> *Đáp án:* **23 chunks** (22 chunk đầy 500 ký tự + 1 chunk đuôi 100 ký tự).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 400 nên số chunk **tăng lên 25** (`ceil(9500 / 400) + 1 = 24 + 1 = 25`) — overlap lớn hơn thì cửa sổ dịch chậm hơn, tốn thêm chi phí lưu trữ và embedding. Đổi lại, overlap nhiều giúp một câu/ý nằm vắt qua ranh giới chunk vẫn xuất hiện trọn vẹn trong ít nhất một chunk, tránh mất ngữ cảnh khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:

- **Regex tách câu:** `re.split(r'(?<=[.!?])\s+', text)`.
- **Vì sao dùng lookbehind:** giữ lại dấu câu ở cuối mỗi câu thay vì nuốt mất; `\s+` bao luôn cả `". "` lẫn `".\n"`.
- **Gom nhóm:** mỗi `max_sentences_per_chunk` câu ghép thành một chunk bằng `" ".join(...)` rồi `.strip()`.
- **Edge case đã xử lý:** văn bản rỗng / chỉ có khoảng trắng trả về `[]`; loại bỏ mảnh rỗng sau khi split; nhóm cuối được phép ngắn hơn `max_sentences_per_chunk`.
- **Hạn chế đã biết:** cắt nhầm ở chữ viết tắt có dấu chấm ("TP.", "vd.").

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:

- **Phân vai:** `chunk()` chỉ là lớp vỏ gọi `self._split(text, self.separators)`; toàn bộ logic nằm ở hàm đệ quy.
- **Bước đệ quy:** cắt theo dấu phân cách ưu tiên cao nhất `remaining_separators[0]`; mảnh nào còn dài hơn `chunk_size` thì gọi lại với `remaining_separators[1:]`, tức hạ dần `"\n\n"` → `"\n"` → `". "` → `" "`.
- **Base case 1:** `len(current_text) <= chunk_size` → trả về `[current_text]`.
- **Base case 2:** hết dấu phân cách → cắt cứng theo `chunk_size`; nhánh này bảo đảm `separators=[]` vẫn trả về danh sách không rỗng.
- **Hậu xử lý:** ghép các mảnh nhỏ liền kề tới sát `chunk_size` để chunk không bị vụn, truy xuất tốt hơn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:

- **Cấu trúc lưu trữ:** `_make_record` chuẩn hóa mỗi `Document` thành bản ghi `{"id", "content", "metadata", "embedding", "index"}`, embedding tính bằng `self._embedding_fn(doc.content)`.
- **Chi tiết quan trọng:** luôn `metadata.setdefault("doc_id", doc.id)` trên một **bản sao** của metadata, để `delete_document()` và lọc theo `doc_id` vẫn chạy đúng kể cả khi tài liệu tạo với `metadata={}` — trùng quy ước `ingest.py` gắn cho từng chunk.
- **`add_documents`:** lặp và `append` bản ghi vào `self._store`.
- **`search`:** nhúng câu hỏi đúng một lần, so với embedding mọi bản ghi, sắp xếp score giảm dần, cắt `top_k`.
- **Vì sao dùng `compute_similarity` chứ không phải `_dot` thô:** vector từ `_mock_embed` chưa chuẩn hóa nên tích vô hướng bị thiên vị theo độ dài vector.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:

- **Lọc TRƯỚC rồi mới tìm kiếm (pre-filter):** thu hẹp `self._store` xuống các bản ghi khớp mọi cặp khóa-giá trị trong `metadata_filter`, rồi đưa tập con cho `_search_records` — cũng là lý do `_search_records` nhận tham số `records` thay vì đọc thẳng `self._store`.
- **Vì sao lọc trước:** rẻ hơn (chỉ tính similarity trên tập con) và bảo đảm đủ `top_k` kết quả hợp lệ; lọc sau dễ trả về ít hơn `top_k`.
- **Khi `metadata_filter=None`:** bỏ qua hoàn toàn bước lọc, kết quả trùng với `search` thường.
- **`delete_document`:** dựng lại `self._store` chỉ giữ bản ghi có `metadata["doc_id"] != doc_id` — xóa trọn mọi chunk của cùng một tài liệu trong một lượt.
- **Giá trị trả về:** so sánh số bản ghi trước/sau để trả `True`/`False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:

- **`__init__`:** chỉ giữ tham chiếu `self.store` và `self.llm_fn`, tách bạch phần truy xuất với phần sinh câu trả lời.
- **3 bước RAG:** `store.search(question, top_k)` → ghép chunk thành khối ngữ cảnh → gọi `llm_fn(prompt)`.
- **Cách inject context:** đánh số từng chunk (`[1] ...`, `[2] ...`) để câu trả lời có thể trích dẫn nguồn.
- **Cấu trúc prompt:** khối ngữ cảnh + câu hỏi người dùng + chỉ dẫn bắt buộc chỉ trả lời dựa trên ngữ cảnh và nói rõ khi ngữ cảnh không chứa thông tin (phần chống bịa / hallucination).
- **Trường hợp rỗng:** truy xuất không ra chunk nào thì trả thẳng thông báo không tìm thấy, không gọi `llm_fn` với ngữ cảnh rỗng.

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
