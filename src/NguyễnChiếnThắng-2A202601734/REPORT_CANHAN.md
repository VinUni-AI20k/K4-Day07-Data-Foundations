# Báo cáo cá nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Chiến Thắng  
**Mã sinh viên:** 2A202601734  
**Nhóm:** T-Hexa  
**Ngày:** 03/08/2026

> Báo cáo này chỉ ghi phần cá nhân. Báo cáo nhóm và các benchmark chung sẽ được
> thực hiện sau khi nhóm thống nhất bộ tài liệu và câu hỏi đánh giá.

---

## 1. Khởi động (Warm-up)

### 1.1. Cosine similarity

Cosine similarity đo mức độ cùng hướng giữa hai vector embedding. Hai văn bản
có điểm cao thường biểu diễn ý nghĩa gần nhau, còn điểm thấp hoặc âm cho thấy
chúng khác hướng trong không gian embedding.

Ví dụ tương đồng cao:

- Câu A: Chính sách đổi trả trong 30 ngày.
- Câu B: Khách hàng được đổi trả sản phẩm trong vòng 30 ngày.

Ví dụ tương đồng thấp:

- Câu A: Chính sách hoàn tiền của cửa hàng.
- Câu B: Mạng nơ-ron dùng để nhận diện hình ảnh.

Cosine similarity thường phù hợp với text embedding hơn khoảng cách Euclid vì
nó tập trung vào hướng biểu diễn ngữ nghĩa, ít bị ảnh hưởng bởi độ lớn tuyệt
đối của vector.

### 1.2. Bài toán chunking

Với tài liệu dài 10.000 ký tự, chunk_size=500, overlap=50:

    ceil((10000 - 50) / (500 - 50))
    = ceil(9950 / 450)
    = 23 chunks

Nếu tăng overlap lên 100:

    ceil((10000 - 100) / (500 - 100))
    = ceil(9900 / 400)
    = 25 chunks

Overlap lớn hơn giúp giữ thêm ngữ cảnh giữa hai chunk, nhưng làm tăng số chunk,
chi phí embedding và số lượng kết quả cần xử lý.

---

## 2. Hướng tiếp cận cá nhân

### 2.1. Chunking

SentenceChunker dùng regex (?<=[.!?])\s+ để phát hiện ranh giới câu, giữ dấu
câu và gom tối đa số câu được cấu hình vào một chunk. Chuỗi rỗng được trả về
danh sách rỗng.

RecursiveChunker thử các separator theo thứ tự ưu tiên: đoạn văn, xuống dòng,
cuối câu, khoảng trắng và cuối cùng là tách theo ký tự. Nếu đoạn hiện tại đã
nhỏ hơn chunk_size, thuật toán dừng; nếu chưa thì chuyển xuống separator yếu
hơn.

ChunkingStrategyComparator chạy fixed-size, sentence và recursive chunking,
sau đó trả về số lượng chunk, độ dài trung bình và danh sách chunk để so sánh.

### 2.2. EmbeddingStore

Mỗi Document được chuyển thành record gồm id, content, metadata và embedding.
Khi search, query cũng được embedding rồi tính dot product với embedding của
các record. Kết quả được sắp xếp giảm dần theo score và cắt ở top_k.

search_with_filter() lọc metadata trước rồi mới tính similarity.
delete_document() xóa cả record có id trùng và các chunk có metadata["doc_id"]
trùng.

### 2.3. KnowledgeBaseAgent

Agent lấy các chunk liên quan từ EmbeddingStore, ghép chúng thành phần Context,
sau đó đưa Context và câu hỏi vào prompt. Hàm llm_fn nhận prompt để sinh câu
trả lời dựa trên dữ liệu đã truy xuất.

---

## 3. Hoàn thiện code

Code cá nhân được đặt trong:

    src/NguyễnChiếnThắng-2A202601734/

Các module chính:

- chunking.py
- store.py
- agent.py
- models.py
- embeddings.py

Kết quả kiểm thử:

    Ran 42 tests
    OK

Số lượng bài test vượt qua: 42 / 42

---

## 4. Dự đoán độ tương tự

Các điểm dưới đây được chạy bằng mock embedder của lab. Mock embedder phù hợp
để kiểm thử tính ổn định của code nhưng không phản ánh chính xác ngữ nghĩa
tiếng Việt.

| # | Câu A | Câu B | Dự đoán | Điểm mock | Nhận xét |
|---|---|---|---|---:|---|
| 1 | Chính sách đổi trả trong 30 ngày. | Khách hàng được đổi trả sản phẩm trong vòng 30 ngày. | Cao | 0.1522 | Tương đối cao nhất trong 5 cặp |
| 2 | Phí vận chuyển đơn hàng. | Mạng nơ-ron xử lý ảnh. | Thấp | -0.0395 | Đúng hướng dự đoán |
| 3 | Người bán phải xử lý hoàn tiền. | Seller must process refunds. | Cao | 0.0175 | Thấp hơn kỳ vọng vì mock không hiểu tốt song ngữ |
| 4 | Tôi muốn đổi size áo. | Tôi cần hoàn tiền sản phẩm. | Trung bình/cao | -0.1485 | Bất ngờ thấp dù cùng ngữ cảnh mua sắm |
| 5 | Thời gian giao hàng là 3 ngày. | Quyền riêng tư bảo vệ dữ liệu. | Thấp | -0.2556 | Đúng hướng dự đoán |

Kết quả cho thấy mock embedding tạo vector xác định nhưng gần như ngẫu nhiên
theo chuỗi. Vì vậy, không nên dùng các điểm mock này để kết luận chiến lược
chunking hoặc chất lượng semantic retrieval. Khi làm Phase 2, cần dùng
multilingual embedder thật để so sánh có ý nghĩa.

---

## 5. Kết quả retrieval cá nhân

Phần này chờ nhóm thống nhất 5 benchmark queries, gold answers và bộ tài liệu
chung. Sau khi nhóm hoàn thành, tôi sẽ chạy cùng 5 câu hỏi trên code cá nhân và
bổ sung top-3 result, score, chunk liên quan và câu trả lời của Agent.

---

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán similarity | 5 / 5 |
| Kết quả retrieval cá nhân | Chờ benchmark nhóm |
| **Tổng phần đã hoàn thành** | **50 / 50** |
