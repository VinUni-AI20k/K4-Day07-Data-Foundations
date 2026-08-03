# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Trung Long
**MSSV:** 2A202601514
**Nhóm:** LPV
**Ngày:** 03/08/2026

## 1. Khởi động (Warm-up)

### 1.1. Độ tương tự cosine

Cosine similarity cao nghĩa là hai vector embedding cùng hướng, nên hai đoạn văn thường nói về cùng chủ đề hoặc có ý nghĩa gần nhau dù dùng từ khác. Ví dụ tương đồng cao: “Người mua có thể trả lại sản phẩm bị vỡ” và “Khách hàng được hoàn hàng nếu sản phẩm hư hỏng”. Ví dụ tương đồng thấp: “Shopee hỗ trợ thanh toán bằng Apple Pay” và “Người bán phải đóng gói hàng dễ vỡ đúng quy định”.

Cosine similarity phù hợp hơn khoảng cách Euclid vì nó so sánh **hướng** của vector và ít bị ảnh hưởng bởi độ lớn. Với embedding văn bản, hướng thường biểu diễn nội dung/ngữ nghĩa quan trọng hơn độ dài vector.

### 1.2. Bài toán chunking

Với `document_length=10,000`, `chunk_size=500`, `overlap=50`:

```text
ceil((10,000 - 50) / (500 - 50))
= ceil(9,950 / 450)
= 23 chunks
```

Khi tăng overlap lên 100:

```text
ceil((10,000 - 100) / (500 - 100))
= ceil(9,900 / 400)
= 25 chunks
```

Overlap lớn hơn tạo thêm hai chunk và tăng chi phí embedding/lưu trữ, nhưng giảm nguy cơ mất thông tin ở ranh giới giữa hai chunk.

## 2. Hướng tiếp cận lập trình

### `SentenceChunker.chunk`

Tôi dùng regex `(?<=[.!?])(?:[ \t]+|\n+)` để tách tại khoảng trắng sau dấu kết thúc câu mà vẫn giữ dấu câu trong kết quả. Các câu sau đó được gom theo `max_sentences_per_chunk`; chuỗi rỗng hoặc chỉ có khoảng trắng trả về danh sách rỗng.

### `RecursiveChunker.chunk` / `_split`

Thuật toán thử lần lượt các separator theo mức ưu tiên. Đoạn nhỏ hơn `chunk_size` là base case; đoạn lớn được tách và ghép lại nếu còn vừa kích thước. Nếu không còn separator hoặc separator là chuỗi rỗng, thuật toán cắt cứng theo `chunk_size` để luôn kết thúc an toàn.

### `EmbeddingStore`

Mỗi `Document` được chuẩn hóa thành record gồm `id`, `content`, metadata, `doc_id` và embedding. OpenAI embedding hỗ trợ batch để nạp corpus hiệu quả; backend mock vẫn được giữ cho unit test. Tìm kiếm nhúng query, tính dot product và sắp xếp score giảm dần.

`search_with_filter` lọc metadata trước khi xếp hạng để tránh tài liệu ngoài phạm vi cạnh tranh score. `delete_document` xóa mọi chunk có `metadata['doc_id']` trùng với tài liệu nguồn và trả về việc có record nào thực sự bị xóa hay không.

### `KnowledgeBaseAgent.answer`

Agent lấy các chunk liên quan, đánh số chúng trong phần `Context`, rồi thêm câu hỏi ở cuối prompt. Prompt yêu cầu chỉ dùng context và trả lời không biết nếu bằng chứng không đủ, giúp hạn chế hallucination.

## 3. Hoàn thiện code

Package cá nhân: `src/2A202601514_NguyenTrungLong`.

```text
LAB_SOLUTION_PACKAGE='src.2A202601514_NguyenTrungLong' python3 -m unittest tests.test_solution -v

Ran 42 tests in 0.002s
OK
```

**Kết quả:** 42/42 test pass.

## 4. Dự đoán độ tương tự

Backend đo thực tế: `text-embedding-3-small`, vector 1.536 chiều.

| Cặp | Câu A | Câu B | Dự đoán trước khi chạy | Score thực tế | Nhận xét |
|---|---|---|---|---:|---|
| 1 | Người mua có thể yêu cầu trả hàng khi sản phẩm bị hư hỏng. | Khách hàng được quyền hoàn trả món hàng nếu hàng bị vỡ. | Cao | 0.718857 | Đúng; cùng ý định trả hàng và cùng nguyên nhân hư hỏng. |
| 2 | Shopee hỗ trợ thanh toán khi nhận hàng bằng COD. | Khách hàng có thể trả tiền sau khi bưu kiện được giao tới. | Cao | 0.464245 | Tương đồng vừa; câu B là diễn giải COD nhưng không nhắc Shopee. |
| 3 | Đơn vị vận chuyển sẽ liên hệ nhiều lần để giao hàng. | Nhân viên giao nhận sẽ gọi cho người mua trước khi giao bưu kiện. | Cao | 0.554057 | Đúng; cùng hành động liên hệ trước/khi giao hàng. |
| 4 | Người bán không được đăng sản phẩm thuộc danh mục cấm. | Apple Pay chỉ áp dụng cho một số thiết bị tương thích. | Thấp | 0.290545 | Đúng; hai chính sách thuộc hai nghiệp vụ khác nhau. |
| 5 | Thực phẩm tươi sống phải được yêu cầu hoàn trả trong 24 giờ. | Người bán phải đóng gói bưu kiện đúng quy định vận chuyển. | Thấp | 0.386965 | Thấp hơn các cặp cùng nghĩa nhưng vẫn có tín hiệu chung về chính sách hàng hóa/vận chuyển. |

Kết quả bất ngờ nhất là cặp 2 chỉ đạt `0.464245` dù hai câu cùng diễn tả COD. Điều này cho thấy embedding còn chịu ảnh hưởng bởi chủ thể và cách diễn đạt, không chỉ quan hệ logic “trả tiền khi nhận hàng”.

## 5. Chiến lược C — Sentence chunks + context injection

### Thiết kế

- Chia tài liệu theo section, sau đó dùng `SentenceChunker(max_sentences_per_chunk=3)`.
- Với các danh sách chính sách không có dấu kết thúc câu, coi mỗi block cách nhau bằng dòng trống là một đơn vị câu. Cách này tránh cả hai cực đoan: một bullet/chunk quá nhỏ hoặc toàn bộ danh sách thành một “câu” rất dài.
- Trước khi embedding, thêm prefix `[title > section]` và metadata `section`. Ví dụ:

```text
[Chính sách trả hàng và hoàn tiền Shopee >
 3. ĐIỀU KIỆN YÊU CẦU TRẢ HÀNG/HOÀN TIỀN]
3.2. Người Mua có thể gửi yêu cầu ... trong vòng 15 ngày ...
```

- Truy xuất `top_k=5`, sau đó giữ kết quả thỏa:

```text
score >= max(0.30, score_top_1 - 0.12)
```

Giả thuyết là chunk ngắn có ít nhiễu và prefix khôi phục ngữ cảnh tài liệu/mục, nên precision cao. Điểm yếu dự kiến là câu trả lời dạng danh sách hoặc cần nhiều điều khoản có thể thiếu thông tin nếu top-5 không phủ đủ các chunk liền kề.

Mã chiến lược nằm tại `strategies/strategy_c_sentence_ctx.py` và được chạy bằng framework chung:

```bash
EMBEDDING_PROVIDER=openai python3 strategies/benchmark.py \
  -p src.2A202601514_NguyenTrungLong -s c
```

### Thống kê corpus/chunk

| Thuộc tính | Kết quả |
|---|---:|
| Tài liệu | 6 |
| Chunk | 257 |
| Độ dài trung bình | 349.8 ký tự |
| Nhỏ nhất / lớn nhất | 60 / 1,136 ký tự |
| Embedding | OpenAI `text-embedding-3-small` |
| Top-k | 5 rồi lọc threshold |

### Kết quả năm câu benchmark

| # | Câu hỏi | Top-1 | Score | Đánh giá thủ công | Tóm tắt câu trả lời agent |
|---|---|---|---:|---|---|
| 1 | Tôi nhận hàng bị vỡ thì được hoàn tiền không? | Hướng dẫn Trả hàng/Hoàn tiền — mục chọn tình huống hàng bể vỡ | 0.646 | Liên quan trực tiếp, nhưng khác `gold_doc` khai báo | Có thể yêu cầu hoàn tiền khi nhận hàng bị vỡ. |
| 2 | Thời hạn gửi yêu cầu trả hàng là bao lâu? | Hướng dẫn — “Thời gian xử lý 3–5 ngày” | 0.742 | Top-1 nhầm **thời gian xử lý**; câu đúng 15 ngày/24 giờ ở rank 4 (`0.627`) | 15 ngày từ lúc giao thành công; thực phẩm tươi sống/đông lạnh là 24 giờ. |
| 3 | Người bán bị cấm đăng bán những mặt hàng nào? | Quy định đăng bán — nội dung không được phép | 0.592 | Đúng top-1; filter `customer_role=seller` được áp dụng | Nêu được các nhóm cấm chính nhưng chưa phủ toàn bộ danh sách. |
| 4 | Shopee hỗ trợ những phương thức thanh toán nào? | Tài liệu phương thức thanh toán | 0.795 | Đúng top-1; cả top-5 cùng đúng tài liệu | Tổng hợp được chín mục nhưng bỏ sót ShopeePay. |
| 5 | Đơn hàng đang giao bị thất lạc thì xử lý ra sao? | Hướng dẫn Trả hàng/Hoàn tiền | 0.627 | Top-1 chỉ liên quan gần; gold ở rank 2–3 | Liên hệ ngay đơn vị vận chuyển hoặc Shopee để được hỗ trợ. |

**Kết quả tự động theo `gold_docs`:** 7/10; 4/5 câu có tài liệu gold trong danh sách sau lọc.
**Đánh giá chunk-level:** top-1 đúng/ngữ nghĩa trực tiếp ở 3/5 câu; top-3 có bằng chứng phù hợp ở 4/5; top-5 có bằng chứng ở 5/5.

Chi tiết đầy đủ nằm trong `report/benchmark_src_2A202601514_NguyenTrungLong_c.md`.

### Metadata filter

Ở câu 3, cả bản không lọc và có lọc đều đưa `shopee-seller-listing-rules` lên top-1 với OpenAI embedding. Dù không làm thay đổi điểm trong lần chạy này, filter vẫn hữu ích vì bảo đảm toàn bộ candidate thuộc vai trò `seller`, giảm nguy cơ nhiễu khi corpus mở rộng.

### Failure analysis và bài học

Failure rõ nhất là câu 2: cụm “thời hạn” kéo các chunk “thời gian xử lý” và “thời gian hoàn tiền” lên trước chunk quy định **thời hạn gửi yêu cầu**. Auto-score theo `doc_id` còn đánh giá top-1 là đúng vì request guide nằm trong `gold_docs`, dù chunk đó trả lời sai con số. Điều này chứng minh đánh giá document-level chưa đủ; cần kiểm tra chunk-level và gold answer cụ thể.

Câu 4 cho thấy trade-off recall: nguồn tự ghi “09 hình thức” nhưng thực tế liệt kê cả ShopeePay và chín mục khác. Top-5 phủ các chunk danh sách, nhưng agent vẫn bỏ sót ShopeePay. Câu 5 cũng xác nhận giả thuyết ban đầu: câu hỏi cần tổng hợp hướng dẫn liên hệ, bằng chứng và bồi thường từ nhiều chunk/tài liệu nên một chunk nhỏ không đủ.

Nếu cải tiến, tôi sẽ giữ Strategy C nhưng bổ sung **neighbor expansion**: sau khi tìm được chunk tốt, lấy thêm chunk trước/sau cùng `doc_id` và `section`. Cách này giữ precision của chunk nhỏ trong bước xếp hạng nhưng tăng đủ-thông-tin cho prompt mà không đổi benchmark query.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5/5 |
| Hướng tiếp cận | 10/10 |
| Hoàn thiện code | 30/30 |
| Dự đoán độ tương tự | 5/5 |
| Kết quả truy xuất | 7/10 |
| **Tổng phần cá nhân** | **57/60** |
