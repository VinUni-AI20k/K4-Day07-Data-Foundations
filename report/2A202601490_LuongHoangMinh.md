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
Sử dụng một dictionary chuẩn hóa (`_make_record`) chứa id (đảm bảo duy nhất), nội dung, metadata và vector nhúng, sau đó đưa vào list lưu trữ. Hàm search chạy vòng lặp tính tích vô hướng (dot product) giữa vector câu hỏi và từng record, rồi sắp xếp mảng kết quả giảm dần theo score để cắt lấy `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*
Thực hiện **lọc trước, search sau** bằng cách duyệt qua `_store` và chỉ giữ lại các record khớp toàn bộ filter, sau đó mới tính độ tương tự; điều này đảm bảo không bị thiếu hụt top-k nếu có nhiều record bị loại. Hàm `delete_document` sử dụng *list comprehension* để tạo ra một list mới chỉ chứa các record có `doc_id` KHÁC với `doc_id` cần xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*
Agent tìm top-k kết quả bằng `store.search` (hoặc `search_with_filter`), sau đó ghép các chunk tìm được vào một chuỗi `context_str`. Chuỗi này được định dạng cẩn thận (có đánh số thứ tự [1], [2] và kèm Source doc_id) rồi chèn vào Prompt template bên dưới phần chỉ dẫn (Instruction) gắt gao nhằm tránh LLM ảo giác (hallucination).

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform darwin -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/hoangminh/Lab VinAI/K4-DAY07-DataFoundation-ABCXYZ
collecting ... collected 42 items

... (lược bỏ log chi tiết)
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.03s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Apple ra mắt iPhone mới | Điện thoại Apple phiên bản mới được giới thiệu | cao | 0.050 | Sai |
| 2 | Tôi thích ăn táo | Quả táo này rất ngon | cao | 0.006 | Sai |
| 3 | Chính sách hoàn tiền của Apple | Mua hàng được trả lại trong 14 ngày | cao | -0.162 | Sai |
| 4 | Trời hôm nay rất đẹp | Thời tiết hôm nay thật tuyệt vời | cao | -0.079 | Sai |
| 5 | Máy tính xách tay Mac | Pizza phô mai nướng lò | thấp | 0.028 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Bất ngờ nhất là các cặp câu đồng nghĩa hoàn toàn (cặp 1, 2, 3, 4) lại cho ra điểm số âm hoặc gần bằng 0 (rất thấp), trong khi cặp 5 hoàn toàn không liên quan thì điểm lại dương (0.028). Điều này phản ánh rõ ràng sự yếu kém của thuật toán `_mock_embed` (tính toán dựa trên ký tự/băm ngẫu nhiên), chứng tỏ rằng để mô hình thực sự hiểu "ngữ nghĩa" (semantic), ta bắt buộc phải dùng các Embedder xịn (như OpenAI, BERT, v.v) đã được huấn luyện với dữ liệu khổng lồ.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store? | k4-apple-phishing: "Apple sẽ không bao giờ yêu cầu..." | 0.129 | Không | Trả lời sai (dựa vào chunk lừa đảo, không có info hoàn trả). |
| 2 | Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không? | k4-apple-phishing: "# Nhận Biết Các Thư Email Lừa Đảo..." | 0.158 | Không | Trả lời sai (lấy nhầm chunk về email lừa đảo). |
| 3 | Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không? | k4-apple-warranty: "- Bảo hành này không áp dụng cho..." | 0.173 | Không | Trả lời sai (bảo hành linh kiện). |
| 4 | Tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không? | k4-apple-sales-refund: "# Chính Sách Bán Hàng Và Trả Hàng..." | 0.018 | Có (1 phần) | Dựa vào chính sách bán hàng nhưng chưa rõ về phần mềm. |
| 5 | Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không? | k4-apple-privacy: "Tại Apple, chúng tôi tôn trọng quyền..." | 0.126 | Không | Trả lời chung chung về quyền riêng tư. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 1 / 5 (do mock_embed)

**Phân tích Thất bại (Failure Analysis):**
- **Query thất bại:** "Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không?"
- **Bằng chứng từ Top-k:** Top-3 chunk truy xuất ra toàn là các tài liệu `k4-apple-phishing` (về lừa đảo qua email) và `k4-apple-privacy` (quyền riêng tư). Hoàn toàn không có mặt file `k4-apple-warranty` dù câu trả lời nằm ở đó.
- **Nguyên nhân:** Do sử dụng `_mock_embed` làm hàm băm giả lập, nên Cosine Similarity hoạt động hoàn toàn ngẫu nhiên và không đánh giá được sự giống nhau về ngữ nghĩa. Điểm Score cao (0.158) chỉ là con số toán học ngẫu nhiên chứ không phản ánh mật độ thông tin.
- **Đề xuất thay đổi:** Chuyển sang sử dụng `LocalEmbedder` hoặc `OpenAIEmbedder` thực thụ thì vấn đề truy xuất sai lệch này sẽ biến mất ngay lập tức.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:* Kỹ thuật cấu hình `metadata_filter` thực sự vô cùng quyền lực khi được thiết lập đúng, nó giúp loại bỏ hoàn toàn nhiễu từ các tệp tài liệu rác có từ khóa tương đồng (ví dụ loại bỏ được chính sách dành cho Seller khi Buyer đang hỏi). Việc cắt đoạn (chunking) theo Semantic (ngữ nghĩa/heading) thường tối ưu cho con người đọc hơn so với cắt cứng bằng số lượng ký tự.

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
