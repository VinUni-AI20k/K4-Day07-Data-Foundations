# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** T-Hexa  
**Thành viên:**  
1. Nguyễn Hoàng Hải — 2A202601426  
2. Nguyễn Văn Thành — 2A202601030  
3. Nguyễn Duy Khánh — 2A202601530  
4. Ngô Xuân Ninh — 2A202601068  
5. Nguyễn Chiến Thắng — 2A202601734  

**Ngày:** 03/08/2026

> Báo cáo này bám biến thể K4: chính sách thương mại điện tử / hỗ trợ khách hàng, 7 tài liệu, metadata truy vết, đúng 5 benchmark queries và có truy vấn lọc `customer_role=seller`.

---

## 1. Lựa chọn tài liệu (Document Set Quality) — 10 điểm

### Phạm vi bộ tài liệu

Nhóm xây dựng corpus về quy trình mua áo thiết kế tại T-Hexa, tập trung vào thanh toán, giao hàng, đổi trả, quyền riêng tư, điều kiện người bán, quy trình thiết kế và đơn số lượng lớn. Bộ dữ liệu là phiên bản dùng cho lab, được chủ sở hữu dự án cho phép sử dụng; không nên coi là văn bản pháp lý chính thức nếu chưa duyệt nghiệp vụ lần cuối.

### Danh sách tài liệu

| # | Tên tài liệu | Nguồn | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|---|---|---|---:|---|
| 1 | Hỗ trợ đơn hàng số lượng lớn | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 464 | `customer_role=both`, `category=bulk_order`, `language=vi` |
| 2 | Hướng dẫn thiết kế và đặt áo | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 568 | `customer_role=buyer`, `category=order_guide`, `language=vi` |
| 3 | Chính sách thanh toán T-Hexa | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 565 | `customer_role=buyer`, `category=payment`, `language=vi` |
| 4 | Chính sách quyền riêng tư T-Hexa | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 573 | `customer_role=both`, `category=privacy`, `language=vi` |
| 5 | Chính sách đổi trả T-Hexa | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 551 | `customer_role=buyer`, `category=returns`, `language=vi` |
| 6 | Điều kiện người bán và nội dung đăng bán | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 642 | `customer_role=seller`, `category=seller_rules`, `language=vi` |
| 7 | Chính sách giao hàng T-Hexa | https://www.t-hexa.vn/ | 2026-08-03 / 2026.08 | 570 | `customer_role=buyer`, `category=shipping`, `language=vi` |

**Data governance checklist:**
- [x] Có 7 tài liệu, nằm trong yêu cầu 5–10 tài liệu.
- [x] Không chứa dữ liệu cá nhân, mật khẩu, OTP hoặc tài liệu sau đăng nhập.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version`, `customer_role`, `category`, `language`, `permission`.
- [x] `sources.csv` ánh xạ đầy đủ giữa `doc_id`, đường dẫn file và nguồn.

### Metadata schema

| Trường | Kiểu | Ví dụ | Giá trị khi retrieval |
|---|---|---|---|
| `doc_id` | string | `t-hexa-returns-policy` | Xác định tài liệu gốc, hỗ trợ delete và đánh giá gold document. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Lọc chính sách theo vai trò; đáp ứng yêu cầu riêng K4. |
| `category` | string | `payment`, `returns` | Thu hẹp không gian tìm kiếm theo nghiệp vụ. |
| `source_url` | URL | `https://www.t-hexa.vn/` | Truy vết nguồn công khai. |
| `retrieved_at` | date | `2026-08-03` | Biết thời điểm thu thập. |
| `document_version` | string | `2026.08` | Kiểm soát phiên bản corpus. |
| `language` | string | `vi` | Chọn embedder đa ngữ và lọc ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — 15 điểm

### Phân tích baseline trên 3 tài liệu

| Tài liệu | Strategy | Số chunk | Độ dài trung bình | Giữ ngữ cảnh? |
|---|---|---:|---:|---|
| t-hexa-bulk-order-support | FixedSizeChunker | 2 | 231.5 | Trung bình; có thể cắt giữa ý |
| t-hexa-bulk-order-support | SentenceChunker | 2 | 230.0 | Tốt; giữ câu hoàn chỉnh |
| t-hexa-bulk-order-support | RecursiveChunker | 2 | 230.5 | Tốt; ưu tiên đoạn/tiêu đề |
| t-hexa-design-order-guide | FixedSizeChunker | 2 | 283.5 | Trung bình; có thể cắt giữa ý |
| t-hexa-design-order-guide | SentenceChunker | 2 | 281.5 | Tốt; giữ câu hoàn chỉnh |
| t-hexa-design-order-guide | RecursiveChunker | 3 | 187.7 | Tốt; ưu tiên đoạn/tiêu đề |
| t-hexa-payment-policy | FixedSizeChunker | 2 | 282.0 | Trung bình; có thể cắt giữa ý |
| t-hexa-payment-policy | SentenceChunker | 2 | 280.5 | Tốt; giữ câu hoàn chỉnh |
| t-hexa-payment-policy | RecursiveChunker | 3 | 186.7 | Tốt; ưu tiên đoạn/tiêu đề |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Hoàng Hải (2A202601426)**
- **Strategy:** `RecursiveChunker(chunk_size=350)`.
- **Lý do:** Ưu tiên đoạn văn, xuống dòng rồi mới đến câu/từ, phù hợp tài liệu chính sách có độ dài phần không đồng đều. Cách này giới hạn kích thước chunk nhưng vẫn cố giữ ranh giới tự nhiên.
- **Kết quả:** 17 chunks, 10/10 điểm retrieval; cả 5 gold documents đứng top-1.

**Thành viên 2 — Nguyễn Văn Thành (2A202601030)**
- **Strategy:** `HeadingChunker(chunk_size=700, overlap=60)` trong `src/custom_chunking.py`.
- **Lý do:** Chính sách Markdown được tổ chức theo tiêu đề/điều khoản. Chia tại heading giữ tiêu đề cùng nội dung, giúp chunk dễ hiểu, dễ trích dẫn và đáp ứng yêu cầu K4 phải có ít nhất một thành viên thử chunk theo heading/điều khoản.
- **Kết quả:** 29 chunks, 10/10 điểm retrieval; cả 5 gold documents đứng top-1.

**Thành viên 3 — Nguyễn Duy Khánh (2A202601530)**
- **Strategy:** `SentenceChunker(max_sentences_per_chunk=3)`.
- **Lý do:** Gom tối đa ba câu giúp giữ các điều kiện liên tiếp trong cùng ngữ cảnh, đồng thời tạo ít chunk hơn biến thể hai câu.
- **Kết quả:** 14 chunks, 10/10 điểm retrieval; cả 5 gold documents đứng top-1.

**Thành viên 4 — Ngô Xuân Ninh (2A202601068)**
- **Strategy:** `FixedSizeChunker(chunk_size=450, overlap=75)`.
- **Lý do:** Cửa sổ cố định dễ kiểm soát chi phí embedding; overlap 75 ký tự giảm nguy cơ mất thông tin tại ranh giới chunk.
- **Kết quả:** 14 chunks, 10/10 điểm retrieval; cả 5 gold documents đứng top-1.

**Thành viên 5 — Nguyễn Chiến Thắng (2A202601734)**
- **Strategy:** `SentenceChunker(max_sentences_per_chunk=2)`.
- **Lý do:** Chunk ngắn hơn biến thể ba câu, tập trung hơn vào từng quy định và hạn chế trộn nhiều ý trong một kết quả.
- **Kết quả:** 19 chunks, 10/10 điểm retrieval; cả 5 gold documents đứng top-1.

### So sánh giữa các thành viên

| Thành viên | Strategy | Số chunk | Điểm (/10) | Điểm mạnh | Điểm yếu |
|---|---|---:|---:|---|---|
| Nguyễn Hoàng Hải | RecursiveChunker 350 | 17 | 10 | Linh hoạt, ưu tiên ranh giới tự nhiên, kiểm soát kích thước | Chunk có thể chứa nhiều ý nếu một section dài. |
| Nguyễn Văn Thành | HeadingChunker 700/60 | 29 | 10 | Mạch lạc, dễ trích dẫn, phù hợp cấu trúc policy | Nhiều chunk hơn; heading ngắn có thể tách rời ngữ cảnh liên quan. |
| Nguyễn Duy Khánh | SentenceChunker 3 câu | 14 | 10 | Giữ câu hoàn chỉnh và ngữ cảnh liền mạch | Có thể gộp nhiều quy định trong cùng chunk. |
| Ngô Xuân Ninh | FixedSizeChunker 450/75 | 14 | 10 | Đơn giản, dễ dự đoán chi phí, có overlap | Có thể cắt giữa câu hoặc giữa điều khoản. |
| Nguyễn Chiến Thắng | SentenceChunker 2 câu | 19 | 10 | Chunk tập trung, không cắt giữa câu | Có thể tách tiêu đề khỏi phần giải thích; số chunk tăng. |

**Kết luận:** Cả năm cấu hình đều đạt 10/10 trên corpus nhỏ và có chủ đề rõ. Nhóm chọn `HeadingChunker` của Nguyễn Văn Thành cho demo vì cấu trúc chunk mạch lạc, dễ kiểm tra grounding và dễ chỉ ra điều khoản hỗ trợ câu trả lời. Kết quả ngang điểm cho thấy cần đánh giá thêm coherence, khả năng trích nguồn và độ ổn định trên câu hỏi khó, không chỉ nhìn Hit@3.

> Benchmark đính kèm dùng `KeywordHashEmbedder` offline để số liệu tái lập trong mọi máy. Khi demo trên máy có Internet, nên cài `requirements-local.txt` và dùng model đa ngữ để kiểm tra semantic retrieval; không dùng `_mock_embed` để kết luận chất lượng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất — 10 điểm

### Đúng 5 benchmark queries và gold answers

| # | Query | Gold Answer | Gold chunk/document |
|---|---|---|---|
| 1 | T-Hexa hỗ trợ những phương thức thanh toán nào? | Ví T-Hexa, chuyển khoản trực tiếp và COD. | `t-hexa-payment-policy` |
| 2 | Khách hàng phải gửi yêu cầu đổi trả trong bao lâu và sản phẩm cần đáp ứng điều kiện gì? | Trong 3 ngày; sản phẩm chưa dùng, chưa giặt, không mùi lạ và đủ phụ kiện. | `t-hexa-returns-policy` |
| 3 | Tổng thời gian thông thường từ khi xác nhận đơn đến khi nhận hàng là bao lâu? | Khoảng 3–9 ngày làm việc. | `t-hexa-shipping-policy` |
| 4 | Người bán cần đáp ứng điều kiện gì khi đăng hình ảnh và nội dung thiết kế? | Phải có quyền sử dụng; không vi phạm bản quyền, giả mạo, thù ghét, lừa đảo hoặc trái luật. | `t-hexa-seller-listing-policy (lọc customer_role=seller)` |
| 5 | T-Hexa thu thập dữ liệu cá nhân nào và sử dụng để làm gì? | Thông tin liên hệ, giao hàng, đơn hàng, thiết kế và hỗ trợ; dùng để xử lý giao dịch, hỗ trợ, chống gian lận, cải thiện dịch vụ và tuân thủ pháp luật. | `t-hexa-privacy-policy` |

### Tổng hợp kết quả nhóm

| # | Query | Strategy tốt nhất | Chunk liên quan trong top-3? | Ghi chú |
|---|---|---|---|---|
| 1 | T-Hexa hỗ trợ những phương thức thanh toán nào? | HeadingChunker | Có, ở top-1 | Top-1 `t-hexa-payment-policy`, score=0.5693; agent trả lời đúng ý chính |
| 2 | Khách hàng phải gửi yêu cầu đổi trả trong bao lâu và sản phẩm cần đáp ứng điều kiện gì? | HeadingChunker | Có, ở top-1 | Top-1 `t-hexa-returns-policy`, score=0.4697; agent trả lời đúng ý chính |
| 3 | Tổng thời gian thông thường từ khi xác nhận đơn đến khi nhận hàng là bao lâu? | HeadingChunker | Có, ở top-1 | Top-1 `t-hexa-shipping-policy`, score=0.6598; agent trả lời đúng ý chính |
| 4 | Người bán cần đáp ứng điều kiện gì khi đăng hình ảnh và nội dung thiết kế? | HeadingChunker | Có, ở top-1 | Top-1 `t-hexa-seller-listing-policy`, score=0.6581; agent trả lời đúng ý chính |
| 5 | T-Hexa thu thập dữ liệu cá nhân nào và sử dụng để làm gì? | HeadingChunker | Có, ở top-1 | Top-1 `t-hexa-privacy-policy`, score=0.3807; agent trả lời đúng ý chính |

**Metadata filtering:** Có ích rõ nhất ở câu 4. Khi dùng `metadata_filter={"customer_role": "seller"}`, chỉ các chunk dành cho người bán được xếp hạng, loại bỏ chính sách dành cho buyer và làm cho điều kiện đăng nội dung đứng top-1. Nếu lọc sai thành `buyer`, gold document sẽ bị loại hoàn toàn; đây là ví dụ filter quá chặt làm mất kết quả đúng.

---

## 4. Demo & Bài học nhóm — 5 điểm

**Demo đề xuất:**
1. Chạy `python -m pytest tests/ -v` và cho thấy 42/42 tests pass.
2. Chạy `python evaluate_submission.py`, mở `evaluation_results.json` và so sánh 29/17/14/14/19 chunks của năm cấu hình.
3. Demo câu hỏi seller hai lần: không filter và có `customer_role=seller`.
4. Mở top-1 chunk để chứng minh agent được grounding từ corpus.

**Bài học:** Retrieval không chỉ phụ thuộc model. Cấu trúc tài liệu, metadata và cách chunk quyết định khả năng tìm đúng đoạn và giải thích nguồn. Với corpus chính sách có heading rõ, chunk theo heading dễ đọc và dễ kiểm chứng hơn dù điểm top-3 có thể ngang các strategy khác.

**Nếu làm lại:** Nhóm sẽ bổ sung dữ liệu chính sách đã được nghiệp vụ/pháp lý duyệt, thêm negative queries không có câu trả lời, thử nhiều `chunk_size`, đo MRR/Hit@3 và chạy embedder đa ngữ thật thay cho lexical benchmark offline.

---

## Tự đánh giá

| Tiêu chí | Điểm |
|---|---:|
| Document Set Quality | 10 / 10 |
| Strategy Design | 15 / 15 |
| Retrieval Quality | 10 / 10 |
| Demo | 5 / 5 |
| **Tổng nhóm** | **40 / 40** |
