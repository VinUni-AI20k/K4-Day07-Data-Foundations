# Báo Cáo Cá Nhân - Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Đức Anh  
**Mã sinh viên:** 2A202601870  
**Vai trò:** Benchmark Owner và Structure-Based / Document-Aware Chunking Owner  
**Ngày chạy benchmark:** 2026-08-03

## 1. Khởi động

### Cosine similarity

Cosine similarity cao nghĩa là hai vector embedding có hướng gần nhau, nên nội dung văn bản thường có ý nghĩa hoặc chủ đề gần nhau. Với text embeddings, hướng của vector quan trọng hơn độ dài tuyệt đối của vector.

Ví dụ similarity cao:

- Câu A: Người mua được trả hàng trong 15 ngày.
- Câu B: Khách hàng có 15 ngày để yêu cầu hoàn tiền.
- Lý do: Hai câu đều nói về thời hạn 15 ngày cho trả hàng/hoàn tiền.

Ví dụ similarity thấp:

- Câu A: Phí xử lý giao dịch là 6%.
- Câu B: Sản phẩm vi phạm sẽ bị xóa.
- Lý do: Một câu nói về phí người bán, câu còn lại nói về chế tài đăng bán.

Cosine similarity được ưu tiên hơn Euclidean distance cho text embeddings vì nó đo độ gần về hướng/ngữ nghĩa và ít bị ảnh hưởng bởi độ lớn vector. Khi embedding đã normalize, cosine cũng tương đương dot product nên phù hợp cho truy xuất nhanh.

### Tính toán chunking

Với tài liệu 10,000 ký tự, `chunk_size=500`, `overlap=50`, bước nhảy là `500 - 50 = 450`. Số chunk là `ceil((10000 - 500) / 450) + 1 = ceil(9500 / 450) + 1 = 23`.

Nếu overlap tăng lên 100, bước nhảy còn 400 nên số chunk tăng thành `ceil((10000 - 500) / 400) + 1 = 25`. Overlap lớn hơn giúp giữ ngữ cảnh qua ranh giới chunk, nhưng làm tăng số chunk và chi phí embedding/tìm kiếm.

## 2. Hướng tiếp cận triển khai

### Chunking functions

`SentenceChunker.chunk` tách câu bằng regex `(?<=[.!?])\s+`, sau đó gom tối đa `max_sentences_per_chunk` câu vào một chunk. Hàm xử lý input rỗng bằng `[]` và trả lại toàn bộ text nếu không tách được câu hợp lệ.

`RecursiveChunker.chunk` dùng danh sách separator ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nếu đoạn hiện tại đã nhỏ hơn `chunk_size` thì dừng; nếu còn quá dài, thuật toán thử separator tiếp theo và cuối cùng cắt theo ký tự khi không còn separator phù hợp.

### EmbeddingStore

`EmbeddingStore.add_documents` embed từng chunk và lưu record trong bộ nhớ cùng `id`, `content`, `metadata`, `embedding`, `index`. `search` embed query, tính dot product với từng vector đã lưu, rồi sắp xếp giảm dần theo score.

`search_with_filter` lọc metadata trước khi tính similarity, nên benchmark có thể chạy chính thức trên đúng vai trò người dùng và category của từng câu hỏi. `delete_document` xóa mọi chunk có `doc_id` tương ứng và trả về boolean cho biết có record bị xóa hay không.

### Agent answer

Không dùng `demo_llm()` cho benchmark vì hàm đó chỉ preview prompt. `scripts/run_benchmark.py` có hàm trả lời deterministic: lấy top-3 chunk đã truy xuất, tách sentence/bullet, chấm điểm theo overlap token với query, ghép tối đa 3 mảnh có nguồn `doc_id`, và trả về `Không đủ thông tin trong corpus.` nếu không có mảnh phù hợp.

## 3. Structure-Based / Document-Aware Chunking

File triển khai: `src/document_aware_chunker.py`

Chiến lược Document-Aware đọc cấu trúc Markdown thay vì chỉ cắt theo số ký tự. Chunker nhận diện heading `#`, `##`, `###`, duy trì heading stack, tạo heading path cho từng section và chèn trực tiếp vào nội dung chunk theo dạng:

```text
[Heading path: Heading 1 > Heading 2]

Nội dung section...
```

Cấu hình chính thức:

```python
DocumentAwareChunker(max_chunk_size=700)
```

Khi một section hoàn chỉnh vượt quá `max_chunk_size`, chunker mới dùng fallback đệ quy với separator `["\n\n", "\n", ". ", " ", ""]`. Nhờ vậy các bullet ngắn nằm dưới cùng một heading không bị tách khỏi heading của chúng.

Policy documents hưởng lợi từ heading-aware splitting vì mỗi điều khoản thường nằm trong một mục rõ ràng như thời hạn, kênh hoàn tiền, phí, hoặc chế tài. Nếu cắt cố định giữa bullet list, truy xuất có thể lấy mất tiêu đề hoặc lấy thiếu điều kiện áp dụng; giữ heading path giúp chunk vẫn có ngữ cảnh khi ingest pipeline chỉ lưu metadata cấp tài liệu.

## 4. Kết quả kiểm thử

Lệnh đã chạy:

```powershell
python -m pytest tests/test_document_aware_chunker.py -v
```

Kết quả:

```text
9 passed in 0.02s
```

Lệnh đã chạy:

```powershell
python -m pytest tests -v
```

Kết quả:

```text
51 passed in 0.06s
```

Repo ban đầu yêu cầu 42 test gốc; sau khi thêm 9 test cho Document-Aware Chunker, tổng số test là 51 và tất cả đều pass.

Lệnh ingest:

```powershell
python ingest.py
```

Kết quả:

```text
ingest self-check OK: parse được 4 khóa metadata, tạo 18 chunk (mỗi chunk giữ doc_id + metadata).
```

## 5. Dự đoán độ tương tự bằng LocalEmbedder

Model sử dụng: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---:|---|---|---|---:|---|
| 1 | Người mua được trả hàng trong 15 ngày. | Khách hàng có 15 ngày để yêu cầu hoàn tiền. | cao | 0.9004 | Có |
| 2 | Phí xử lý giao dịch là 6%. | Sản phẩm vi phạm sẽ bị xóa. | thấp | 0.1245 | Có |
| 3 | Tiền hoàn về thẻ mất 7 đến 14 ngày làm việc. | Hoàn tiền qua thẻ tín dụng cần 7-14 ngày làm việc. | cao | 0.9088 | Có |
| 4 | Người bán chuẩn bị đơn trong 1.5 ngày làm việc. | Thời gian giao hàng hỏa tốc là vài giờ. | thấp | 0.4271 | Có |
| 5 | Tài khoản vi phạm có thể bị tạm khóa. | Người bán vi phạm nghiêm trọng có thể bị khóa tài khoản. | cao | 0.8875 | Có |

Cặp 4 có điểm không quá thấp dù dự đoán là thấp, vì cả hai câu đều nói về thời gian trong ngữ cảnh giao hàng. Điều này cho thấy embedding bắt được chủ đề chung, nhưng vẫn cần truy xuất và lọc metadata để phân biệt câu hỏi về seller preparation với giao hàng cho người mua.

## 6. Frozen benchmark queries

Benchmark version: `aramhonloan-k4-v1`  
File cấu hình: `config/benchmark_cases.json`  
Số case: 5  
Trạng thái: `frozen=true`

| ID | Query | Expected doc | Metadata filter | Required facts |
|---|---|---|---|---|
| Q1 | Người mua có bao lâu để yêu cầu trả hàng hoặc hoàn tiền, và thời hạn đối với thực phẩm tươi sống khác thế nào? | returns-policy | buyer / returns | 15 ngày; 24 giờ |
| Q2 | Tiền hoàn cho giao dịch thanh toán bằng thẻ tín dụng hoặc thẻ ghi nợ mất bao lâu để trả về thẻ? | payment-policy | buyer / payment | 7; 14 ngày làm việc |
| Q3 | Người bán phải chuẩn bị đơn hàng thông thường trong bao lâu, và điều gì xảy ra nếu chuẩn bị trễ? | shipping-policy | both / shipping | 1.5 ngày làm việc; tự động; hủy |
| Q4 | Từ tháng 5 năm 2026, phí xử lý giao dịch Shopee áp dụng cho người bán là bao nhiêu? | seller-fees | seller / fees | 6%; thuế |
| Q5 | Shopee xử lý thế nào đối với sản phẩm vi phạm quy định đăng bán? | seller-listing | seller / listing | xóa; tạm khóa; khóa tài khoản |

## 7. Kết quả benchmark chính thức

Lệnh đã chạy:

```powershell
python scripts/run_benchmark.py --strategy document-aware --max-chunk-size 700 --data-dir data/k4_ecommerce --output results/NguyenDucAnh_document_aware.json
```

Kết quả terminal:

```text
Benchmark summary
  version: aramhonloan-k4-v1
  member: Nguyễn Đức Anh
  strategy: Structure-Based / Document-Aware Chunking
  queries: 5
  top-3 hits: 5/5
  top-1 hits: 5/5
  retrieval score: 9/10
  average top-1 score: 0.7551
  Q1: top1=returns-policy score=0.7301 point=2 rank=1
  Q2: top1=payment-policy score=0.7783 point=2 rank=1
  Q3: top1=shipping-policy score=0.7771 point=2 rank=1
  Q4: top1=seller-fees score=0.7196 point=2 rank=1
  Q5: top1=seller-listing score=0.7704 point=1 rank=1
```

| ID | Top-1 doc | Top-1 score | Relevant in top-3 | Agent answer | Points |
|---|---|---:|---|---|---:|
| Q1 | returns-policy | 0.7301 | Có | Thời hạn yêu cầu Trả hàng/Hoàn tiền; người mua có 15 ngày; thực phẩm tươi sống và đông lạnh có thời hạn 24 giờ. Nguồn: returns-policy. | 2 |
| Q2 | payment-policy | 0.7783 | Có | Hoàn tiền về thẻ tín dụng/ghi nợ trong vòng 7 - 14 ngày làm việc tùy ngân hàng. Nguồn: payment-policy. | 2 |
| Q3 | shipping-policy | 0.7771 | Có | Người bán chuẩn bị đơn tối đa 1.5 ngày làm việc; quá hạn đơn bị hệ thống tự động hủy do chuẩn bị hàng trễ. Nguồn: shipping-policy. | 2 |
| Q4 | seller-fees | 0.7196 | Có | Từ tháng 5 năm 2026, phí xử lý giao dịch cố định là 6%, đã bao gồm thuế GTGT. Nguồn: seller-fees. | 2 |
| Q5 | seller-listing | 0.7704 | Có | Sản phẩm vi phạm bị tự động xóa; answer không lấy được đầy đủ cụm tạm khóa và khóa tài khoản dù nằm trong top-1 chunk. Nguồn: seller-listing. | 1 |

Tổng kết chính thức:

- Queries run: 5
- Top-3 hits: 5/5
- Top-1 hits: 5/5
- Retrieval score: 9/10
- Average top-1 score: 0.7551

## 8. Filtered versus unfiltered

Filtered retrieval là kết quả chính thức vì mọi case đều có metadata filter. Unfiltered top-3 vẫn được lưu để so sánh.

| ID | Filtered top-1 | Unfiltered top-3 doc_ids | Quan sát |
|---|---|---|---|
| Q1 | returns-policy | returns-policy, shipping-policy, payment-policy | Filter giúp loại nhiễu shipping/payment khỏi kết quả chính thức. |
| Q2 | payment-policy | payment-policy, payment-policy, payment-policy | Filter không thay đổi đáng kể vì query rất đặc thù về thanh toán. |
| Q3 | shipping-policy | shipping-policy, returns-policy, shipping-policy | Filter loại chunk returns-policy chen vào top-3. |
| Q4 | seller-fees | seller-fees, seller-fees, returns-policy | Filter loại chunk returns-policy không thuộc seller/fees. |
| Q5 | seller-listing | seller-listing, seller-listing, seller-fees | Filter loại chunk seller-fees không thuộc listing. |

## 9. Weak case và phân tích nguyên nhân

Weak case thật là Q5. Truy xuất đúng: `seller-listing` đứng top-1 với score 0.7704 và relevant-in-top-3 là Có. Tuy nhiên grounded answer chỉ chứa required fact `xóa`, thiếu `tạm khóa` và `khóa tài khoản`, nên scoring bảo thủ cho 1 điểm.

Nguyên nhân không nằm ở retrieval mà nằm ở answer extraction heuristic. Hàm grounded answer chọn tối đa 3 fragment theo token overlap với query; fragment nói về chứng từ ngành hàng có overlap token cao hơn fragment chế tài tài khoản, nên câu chứa `tạm khóa` và `khóa tài khoản` không được chọn dù có trong top-1 chunk. Cách cải thiện sau này là ưu tiên nhiều bullet trong cùng top-1 section hoặc tăng trọng số cho fragment cùng heading "Chế tài xử lý vi phạm".

## 10. Heading preservation và bullet-list coherence

Document-Aware Chunking giữ heading path trong nội dung chunk nên mỗi kết quả có ngữ cảnh cấu trúc, ví dụ section "Chế tài xử lý vi phạm của Shopee" không bị tách khỏi document title. Với bullet list ngắn, chunker giữ các bullet cùng heading khi tổng kích thước dưới `max_chunk_size`; điều này giúp Q1, Q2, Q3 và Q4 lấy đủ facts trong cùng một section.

Fallback đệ quy chỉ được dùng cho section quá dài. Vì vậy chiến lược này vẫn kiểm soát kích thước chunk nhưng không phá cấu trúc Markdown khi không cần thiết.

## 11. Comparison-ready table

| Thành viên | Strategy | Config | Top-3 hits | Retrieval score |
|---|---|---|---:|---:|
| Nguyễn Đức Anh | Document-Aware | max=700 | 5/5 | 9/10 |
| Thành viên Fixed-size | Fixed-size | Chưa nhận kết quả | Chưa có | Chưa có |
| Thành viên Sentence | Sentence | Chưa nhận kết quả | Chưa có | Chưa có |
| Thành viên Recursive | Recursive | Chưa nhận kết quả | Chưa có | Chưa có |

Chưa có kết quả từ thành viên phụ trách chiến lược này tại thời điểm chạy benchmark.

Không có kết quả Fixed-size, Sentence hoặc Recursive nào được tự tạo hoặc gán cho Nguyễn Đức Anh.
