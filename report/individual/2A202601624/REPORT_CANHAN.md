# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Anh

**Mã sinh viên:** 2A202601624

**Nhóm:** Sigmoid

**Vai trò:** Team lead

**Nhánh cá nhân:** `member/nguyen-duc-anh-fixed`

**Chiến lược được giao:** tuned `FixedSizeChunker`

**Ngày thực hiện:** 2026-08-03

## 1. Khởi động (Warm-up)

### Độ tương tự cosine

Cosine similarity cao nghĩa là hai vector embedding có hướng gần nhau, thường cho thấy hai đoạn văn gần nhau về ý nghĩa dù cách dùng từ có thể khác. Điểm gần 1 biểu thị tương tự cao, gần 0 là ít liên quan, còn điểm âm biểu thị hướng đối lập trong không gian vector.

Ví dụ tương tự cao:

- A: “Người mua có thể yêu cầu hoàn tiền trong 15 ngày.”
- B: “Thời hạn gửi yêu cầu trả hàng là mười lăm ngày.”
- Hai câu cùng nói về thời hạn trả hàng/hoàn tiền; mô hình local đo được `0.7195`.

Ví dụ tương tự thấp:

- A: “Shopee có thể phong tỏa quyền rút tiền khi có vi phạm.”
- B: “Thời tiết hôm nay có nhiều mây và mưa.”
- Hai câu thuộc hai chủ đề khác nhau; mô hình local đo được `-0.1493`.

Cosine similarity thường phù hợp hơn khoảng cách Euclid cho text embedding vì nó tập trung vào hướng biểu diễn (ngữ nghĩa tương đối) thay vì độ lớn của vector. Điều này làm phép so sánh ít bị ảnh hưởng bởi scale của embedding.

### Bài toán chunking

Với tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50`:

`ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = 23` chunks.

Khi tăng overlap lên 100:

`ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25` chunks.

Số chunk tăng từ 23 lên 25 vì bước trượt giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ thông tin nằm sát ranh giới chunk, nhưng làm tăng dữ liệu trùng lặp, chi phí embedding và khả năng nhiều kết quả gần giống nhau xuất hiện trong top-k.

## 2. Hướng tiếp cận của tôi

### Chunking và similarity

`SentenceChunker.chunk` dùng regex `(?<=[.!?])\s+` để tách sau dấu kết câu mà vẫn giữ dấu câu, loại phần rỗng và nhóm tối đa số câu được cấu hình. Văn bản rỗng trả về danh sách rỗng; `max_sentences_per_chunk` được chặn tối thiểu là 1.

`RecursiveChunker` thử separator theo thứ tự ưu tiên. Đoạn vừa kích thước là base case; đoạn quá dài được tách bằng separator hiện tại và chỉ đệ quy phần vẫn quá dài với các separator còn lại. Khi hết separator hoặc gặp separator rỗng, hàm cắt cứng theo `chunk_size`; delimiter có ý nghĩa được giữ lại để không làm mất dấu câu.

`compute_similarity` tính tích vô hướng chia cho tích hai chuẩn L2. Nếu một vector có độ lớn bằng 0, hàm trả `0.0` để tránh chia cho 0.

`ChunkingStrategyComparator` chạy `FixedSizeChunker`, `SentenceChunker` và `RecursiveChunker`, rồi trả về danh sách chunk, số lượng và độ dài trung bình cho từng chiến lược.

### EmbeddingStore

Mỗi `Document` được chuyển thành record gồm ID gốc, ID lưu trữ nội bộ duy nhất, content, bản sao metadata và embedding. Store duy trì một bản in-memory đáng tin cậy; nếu ChromaDB có mặt thì khởi tạo collection tạm thời và đồng bộ thêm, còn mọi lỗi Chroma đều chuyển an toàn về memory.

`search` embedding query, tính dot product với các record, sắp xếp score giảm dần và giới hạn `top_k`. `search_with_filter` lọc metadata trước khi xếp hạng để tránh kết quả ngoài phạm vi cạnh tranh với ứng viên hợp lệ. `delete_document` xóa mọi record có ID tài liệu hoặc `metadata.doc_id` khớp và trả boolean chính xác.

### KnowledgeBaseAgent

`answer` lấy top-k chunk từ store, đánh dấu rõ từng context chunk và tạo prompt chứa riêng phần câu hỏi, context và chỉ dẫn chỉ trả lời từ dữ liệu được truy xuất. Nếu context không đủ, prompt yêu cầu nói rõ thay vì thêm khẳng định không được hỗ trợ; hàm sau đó gọi `llm_fn` được inject, không hardcode câu trả lời.

## 3. Hoàn thiện code

Môi trường kiểm thử bắt buộc:

```text
Python 3.11.9
pytest 9.1.1
Command: .venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
..........................................                               [100%]
42 passed in 0.07s
```

**Kết quả:** 42 / 42 tests passed. Không sửa `tests/test_solution.py`.

## 4. Dự đoán độ tương tự

Backend đo thực tế: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều). Tôi dùng ngưỡng giải thích định tính: khoảng `>= 0.5` là cao đối với các cặp đã chọn, còn gần 0 hoặc âm là thấp.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua có thể yêu cầu hoàn tiền trong 15 ngày. | Thời hạn gửi yêu cầu trả hàng là mười lăm ngày. | Cao | 0.7195 | Có |
| 2 | Người bán phải dùng ảnh thật của sản phẩm. | Ảnh đăng bán cần do chính người bán chụp. | Cao | 0.7318 | Có |
| 3 | Đơn hàng đang chờ lấy hàng có thể cần người bán phản hồi. | Yêu cầu hủy đơn phụ thuộc phản hồi của người bán. | Cao | 0.6555 | Có |
| 4 | Shopee có thể phong tỏa quyền rút tiền khi có vi phạm. | Thời tiết hôm nay có nhiều mây và mưa. | Thấp | -0.1493 | Có |
| 5 | Thực phẩm đông lạnh có thời hạn khiếu nại 24 giờ. | Người bán cần tuân thủ quy định về tên sản phẩm. | Thấp | 0.1075 | Có |

Cặp 3 thấp hơn hai cặp tương tự còn lại dù cùng ý, cho thấy mô hình vẫn nhạy với cách diễn đạt và lượng từ khóa chung. Cặp 5 còn dương nhẹ vì cả hai câu cùng nằm trong miền chính sách thương mại điện tử, nhưng khác nghiệp vụ nên điểm vẫn thấp.

## 5. Thí nghiệm tuned FixedSizeChunker

### Thiết kế đo lường

Tôi chạy đúng 5 query chung trong `REPORT_NHOM.md` trên cùng corpus `data/k4_ecommerce/`, dùng local multilingual embedder và `top_k=3`. Query 1 dùng `metadata_filter={"customer_role": "buyer"}` theo yêu cầu K4.

Một kết quả được đánh dấu relevant khi `doc_id` khớp tài liệu gold **và** chunk chứa các evidence term được xác định trước từ vị trí kiểm chứng trong corpus. Quy tắc chọn cấu hình cũng được cố định trước: tối đa Hit@3, sau đó số evidence chunk trong 15 vị trí top-3, sau đó MRR@3; chỉ ưu tiên ít chunk hơn khi các metric retrieval hòa nhau.

Script tái lập: `scripts/benchmark_fixed_size.py`. Raw results: `report/NGUYEN_DUC_ANH_FIXED_RESULTS.json`.

### Kết quả ba cấu hình

| `chunk_size/overlap` | Số chunk | Hit@3 | Evidence chunks / 15 | Precision@3 | MRR@3 |
|---|---:|---:|---:|---:|---:|
| `500/50` | 311 | 4/5 | 4/15 | 0.2667 | 0.6000 |
| **`800/100`** | **199** | **5/5** | **5/15** | **0.3333** | **0.8000** |
| `1200/150` | 134 | 1/5 | 1/15 | 0.0667 | 0.2000 |

**Cấu hình được chọn: `chunk_size=800`, `overlap=100`.** Đây là cấu hình duy nhất đưa evidence đúng vào top-3 cho cả 5 query và cũng có MRR@3 cao nhất.

### Chi tiết retrieval của cấu hình 800/100

| # | Top-1 retrieval | Score | Evidence đúng trong top-3? | Hạng evidence đầu tiên | Đánh giá câu trả lời |
|---|---|---:|---|---:|---|
| 1 | `shopee-order-cancellation`, chunk 0 — bảng trạng thái hủy đơn “Chờ lấy hàng” | 0.734612 | Có | 1 | Context chứa đầy đủ: cần chờ Người bán; chấp nhận thì hủy, từ chối thì tiếp tục giao. |
| 2 | `shopee-return-refund-policy`, chunk 4 — Điều 3.2 về 15 ngày và 24 giờ | 0.807848 | Có | 1 | Context chứa cả thời hạn 15 ngày và ngoại lệ thực phẩm tươi sống/đông lạnh 24 giờ. |
| 3 | `shopee-return-refund-policy`, chunk 16 — nội dung ảnh/video khi hoàn trả (nhiễu) | 0.685522 | Có | 2 | Evidence đúng nằm ở `shopee-product-listing-rules`, chunk 7, score 0.684522: ảnh tự chụp và tỷ lệ 40%. |
| 4 | `shopee-prohibited-products-policy`, chunk 1 — danh sách chế tài | 0.774781 | Có | 1 | Context chứa các nhóm xóa sản phẩm, hạn chế/đình chỉ tài khoản, phong tỏa rút tiền và chế tài pháp luật. |
| 5 | `shopee-terms-of-service`, chunk 62 — điều kiện giải phóng tiền khác (nhiễu) | 0.797588 | Có | 2 | Evidence đúng ở chunk 56, score 0.795756: sớm nhất ngày thứ 04 và có thể chậm hơn khi nghi ngờ gian lận. |

**Kết quả tổng:** 5/5 query có evidence đúng trong top-3; 3/5 query có evidence ở top-1.

Repo chỉ cung cấp `demo_llm`, không phải mô hình sinh câu trả lời thật. Vì vậy tôi không ghi một “agent answer” giả: bảng trên đánh giá trực tiếp mức grounding của context truy xuất so với gold answer. `KnowledgeBaseAgent` đã được kiểm thử bằng `llm_fn` inject trong unit test, nhưng chất lượng sinh câu trả lời cần một LLM thật để chấm riêng.

### Context preservation, số chunk và retrieval noise

- `500/50` tạo nhiều nhất (311 chunks). Chunk ngắn giúp định vị chi tiết, nhưng overlap 50 không luôn giữ trọn evidence qua ranh giới: query 1 có đúng tài liệu ở top-1 nhưng evidence đầy đủ chỉ ở hạng 2; query 4 không có evidence trong top-3. Nhiều chunk hơn cũng tăng ứng viên gần giống nhau và retrieval noise.
- `800/100` giảm còn 199 chunks nhưng vẫn giữ trọn các đoạn chính sách quan trọng. Overlap 100 đủ nối ngữ cảnh biên trong corpus này, trong khi chunk chưa quá dài; đây là điểm cân bằng tốt nhất giữa context và nhiễu.
- `1200/150` chỉ tạo 134 chunks và nhìn bề ngoài giữ nhiều context nhất, nhưng nội dung dài pha nhiều chủ đề làm embedding kém đặc hiệu. Ngoài ra model đo thực tế có `max_seq_length=128` tokens, nên phần cuối của chunk 1.200 ký tự có thể bị truncate khi embedding; cấu hình này chỉ đạt Hit@3 1/5.

Điểm số cũng cho thấy top-1 score cao không đảm bảo relevance: ở query 5, chunk nhiễu đạt `0.797588`, chỉ nhỉnh hơn evidence đúng `0.795756`. Vì vậy việc kiểm tra evidence trong top-3 quan trọng hơn chỉ chọn score cao nhất.

## 6. Ghi chú vai trò team lead

Tôi không sửa `REPORT_NHOM.md` trên nhánh cá nhân này và không merge bất kỳ implementation `src/` nào của thành viên khác. Sau khi nhận đủ kết quả đo của mọi thành viên, phần tích hợp chỉ lấy các phát hiện chung và phải thực hiện trên nhánh riêng `team/report-integration`.

## Tự đánh giá phần cá nhân

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận | 10 / 10 |
| Hoàn thiện code | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất | 9 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |

Tôi tự trừ 1 điểm retrieval vì chưa chấm được chất lượng câu trả lời sinh bởi một LLM thật; các metric retrieval và grounding đều được đo và lưu raw result để kiểm chứng.
