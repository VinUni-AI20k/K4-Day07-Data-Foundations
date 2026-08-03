# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đăng Long
**Mã sinh viên:** 2A202601934
**Nhóm:** K4
**Ngày:** 2026-08-03

Phần implementation cá nhân được đặt trong `src/K4_2A202601934_NguyenDangLong/`.
Package này tự chứa chunkers, embedding backends, vector store, agent và chiến lược heading-recursive của tôi.

## 1. Khởi động (Warm-up) - 5 điểm

### Độ tương tự Cosine

Cosine similarity đo góc giữa hai vector embedding thay vì chỉ đo độ dài của chúng.
Giá trị càng gần 1 thì hai đoạn văn có hướng ngữ nghĩa càng giống nhau; giá trị gần 0 hoặc âm cho thấy chúng ít tương đồng trong không gian embedding.

Ví dụ có độ tương tự cao:

- Câu A: `This black cotton dress is available in several sizes.`
- Câu B: `The black dress comes in multiple sizes.`
- Hai câu cùng nói về một chiếc váy đen và nhiều kích cỡ, dù cách diễn đạt khác nhau.

Ví dụ có độ tương tự thấp:

- Câu A: `Dry clean only.`
- Câu B: `Machine wash at 40 degrees.`
- Hai câu mô tả hướng dẫn chăm sóc trái ngược nhau.

Cosine similarity phù hợp với text embedding vì nó tập trung vào hướng biểu diễn ngữ nghĩa và ít bị ảnh hưởng bởi độ dài tuyệt đối của văn bản.

### Bài toán tính toán Chunking

Với tài liệu 10,000 ký tự, `chunk_size=500` và `overlap=50`, bước dịch là `500 - 50 = 450` ký tự.
Theo công thức của đề bài, số chunk là `ceil((10,000 - 50) / 450) = ceil(22.111...) = 23`.

Khi overlap tăng lên 100, bước dịch còn `500 - 100 = 400` và số chunk là `ceil((10,000 - 100) / 400) = ceil(24.75) = 25`.
Overlap lớn giúp giữ phần ngữ cảnh nằm ở ranh giới giữa hai chunk, nhưng làm tăng số chunk và chi phí embedding.

## 2. Hướng tiếp cận của tôi (My Approach) - 10 điểm

### Các hàm chia nhỏ

`SentenceChunker.chunk` dùng regex `r"(?<=[.!?])\s+"` để tách sau dấu kết thúc câu.
Hàm loại bỏ đoạn rỗng, gom tối đa số câu cấu hình được vào một chunk và trả về danh sách rỗng khi input rỗng.

`RecursiveChunker.chunk` thử các separator theo thứ tự đoạn văn, dòng, câu, khoảng trắng rồi mới hard-split theo kích thước.
Base case là văn bản đã ngắn hơn `chunk_size`, không còn separator, hoặc input rỗng; mọi chunk trả về đều được strip để tránh whitespace rác.

`HeadingRecursiveChunker` là chiến lược riêng của tôi cho product listing.
Nó tách từng section Markdown theo heading, giữ heading trong mọi child chunk và dùng recursive fallback cho section quá dài.

### EmbeddingStore

`add_documents` sao chép metadata, bảo đảm có `doc_id`, tạo ID chunk duy nhất và lưu embedding cùng nội dung trong in-memory store.
`search` embed query một lần, tính dot product với các record, sắp xếp giảm dần theo score và trả về `top_k` kết quả.

`search_with_filter` lọc metadata trước rồi mới xếp hạng similarity trên tập record còn lại.
`delete_document` xóa toàn bộ record có cùng `doc_id`, còn `get_collection_size` trả về số chunk hiện có.

### KnowledgeBaseAgent

`answer` lấy top-k chunks, dựng context có số thứ tự và source ID, sau đó đưa context cùng câu hỏi vào prompt.
Nếu store rỗng, agent trả về thông báo thiếu context thay vì gọi LLM với dữ liệu rỗng.

### Kết quả kiểm thử

Bộ test được chạy với package cá nhân bằng cách ánh xạ package Long vào tên import `src`.

```text
..........................................                               [100%]
42 passed in 0.01s
```

## 3. Dự đoán độ tương tự (Similarity Predictions) - 5 điểm

Các điểm dưới đây được tính bằng `MockEmbedder` deterministic của package cá nhân.
Mock embedding chỉ dùng để kiểm tra kỹ thuật, không dùng để kết luận chất lượng ngữ nghĩa của product retrieval.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | This black cotton dress is available in several sizes. | The black dress comes in multiple sizes. | Cao | -0.058424 | Không |
| 2 | The item is made from 100% cotton. | The product uses a cotton main fabric. | Cao | 0.081780 | Không |
| 3 | This jacket is black. | This jacket is bright red. | Thấp | 0.025432 | Có |
| 4 | Dry clean only. | Machine wash at 40 degrees. | Thấp | 0.047879 | Có |
| 5 | The product is from adidas Originals. | This item is made by Calvin Klein. | Thấp | 0.103554 | Không |

Điều bất ngờ là các cặp có nghĩa gần nhau không nhất thiết có score cao.
Nguyên nhân là MockEmbedder sinh vector từ hash chuỗi, không hiểu synonym, phủ định hoặc quan hệ thương hiệu.
Kết quả này xác nhận benchmark semantic phải dùng local multilingual embedder thay vì mock.

## 4. Kết quả truy xuất của tôi (Competition Results) - 10 điểm

Tôi chạy đúng năm golden queries trong `benchmark/queries.py` với package cá nhân, `HeadingRecursiveChunker`, `chunk_size=400`, `top_k=3` và model `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
Kết quả đầy đủ được lưu tại `src/K4_2A202601934_NguyenDangLong/benchmark_results.json`.

| # | Câu hỏi | Top-1 | Score | Relevant | Agent answer |
|---|---|---|---:|---|---|
| 1 | Sản phẩm nào phải giặt khô và làm từ gì? | ASOS LUXE cotton corset top | 0.502600 | Không, MISS | Chưa xác nhận |
| 2 | Đầm maxi ASOS EDITION satin giá bao nhiêu? | Đúng ASOS EDITION satin cami maxi dress | 0.755084 | Có, TOP-1 | Chưa xác nhận |
| 3 | Áo khoác nào làm từ lông giả? | Đúng Daisy Street faux fur coat | 0.576306 | Có, TOP-1 | Chưa xác nhận |
| 4 | Sản phẩm đen, cổ yếm để đi biển? | Đúng Public Desire beach dress | 0.530698 | Có, TOP-1 | Chưa xác nhận |
| 5 | Có maternity dress không và fit thế nào? | Đúng ASOS DESIGN maternity dress | 0.703586 | Có, TOP-1 | Chưa xác nhận |

**Số query có chunk liên quan trong top-3:** 4 / 5.

Golden runner tính retrieval tự động là 8/10.
Tôi chưa nhận điểm cuối cho mục này vì agent answers chưa được chạy và đối chiếu với gold answers.

### Failure analysis

Q1 hỏi đồng thời về hướng dẫn chăm sóc và chất liệu của cùng một sản phẩm.
Trong tài liệu đúng, `Dry clean only` nằm dưới heading `Look After Me`, còn `100% Cotton` nằm dưới heading `About Me`; strategy heading tạo hai chunk riêng nên không có chunk nào chứa trọn hai bằng chứng.

Tôi đã thử tạo thêm một compact window cho hai sibling sections liền nhau, giữ product title một lần và không thay golden query.
Kết quả vẫn là 8/10 và Q1 vẫn MISS, vì vậy thử nghiệm không được giữ trong implementation cuối.
Hướng cải thiện tiếp theo là so sánh structured-field retrieval hoặc hybrid lexical-semantic reranking, thay vì tiếp tục tăng số chunk trùng lặp.

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận (My Approach) | 10 / 10 |
| Hoàn thiện code, 42 tests | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 0 / 10 |
| **Tổng phần cá nhân hiện tại** | **50 / 60** |
