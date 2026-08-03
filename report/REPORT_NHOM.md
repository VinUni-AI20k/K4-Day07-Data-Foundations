# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Tên nhóm:** K4 — Nhóm Nguyễn Đức Anh

**Ngày hoàn thiện:** 2026-08-03

| Thành viên | MSSV | Vai trò |
|---|---|---|
| Nguyễn Đức Anh | 2A202601624 | Team lead, tuned FixedSizeChunker |
| Nguyễn Trọng Đăng Khoa | 2A202601964 | Markdown heading/clause chunking |
| Nguyễn Duy Thái | 2A202601552 | Sentence chunking |
| Nguyễn Hoàng Long | 2A202601134 | Recursive chunking |

Hình thức hoàn thành của nhóm là nộp project trên GitHub, không tổ chức demo trực tiếp. Các phân tích kỹ thuật, so sánh strategy và kết quả retrieval được trình bày bằng văn bản trong báo cáo và benchmark artifacts.

## 1. Bộ tài liệu

### Phạm vi

Corpus gồm chính sách công khai của Shopee Việt Nam về vòng đời đơn hàng và quy tắc marketplace: hủy đơn, trả hàng/hoàn tiền, đăng bán, hàng cấm/hạn chế và điều khoản dịch vụ. Cả năm gold answer đều kiểm chứng được trực tiếp từ corpus.

### Document inventory

| # | Tài liệu | Source URL | Retrieved/version | Ký tự body | Metadata chính |
|---:|---|---|---|---:|---|
| 1 | Chính sách trả hàng và hoàn tiền | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77251?seo=1) | 2026-08-03 / 2026-03-11 | 19,420 | `both`, `returns-refunds`, `vi` |
| 2 | Tôi có thể hủy đơn hàng không? | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79182?seo=1) | 2026-08-03 / `not-stated` | 1,872 | `buyer`, `order-cancellation`, `vi` |
| 3 | Quy định đăng bán sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77246?seo=1) | 2026-08-03 / 2024-08-21 | 21,279 | `seller`, `product-listing`, `vi` |
| 4 | Chính sách cấm/hạn chế sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77247?seo=1) | 2026-08-03 / 2025-05-05 | 12,653 | `seller`, `prohibited-products`, `vi` |
| 5 | Điều khoản dịch vụ | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77243?seo=1) | 2026-08-03 / 2026-05-01 | 83,183 | `both`, `payments-and-orders`, `vi` |

### Metadata schema

| Field | Kiểu/giá trị | Công dụng retrieval |
|---|---|---|
| `doc_id` | string duy nhất | Truy vết, filter và xóa toàn bộ chunks của tài liệu |
| `title` | string | Hiển thị và kiểm chứng nguồn |
| `source_url` | URL | Đối chiếu với trang công khai gốc |
| `retrieved_at` | `YYYY-MM-DD` | Ghi thời điểm thu thập |
| `document_version` | date hoặc `not-stated` | Phân biệt phiên bản chính sách |
| `customer_role` | `buyer`, `seller`, `both` | Filter bắt buộc của biến thể K4 |
| `category` | enum nghiệp vụ | Thu hẹp theo loại chính sách |
| `language` | `vi` | Xác định ngôn ngữ corpus/query |
| `chunk_index` | integer | Truy vết vị trí chunk trong document |

Corpus chỉ chứa nội dung công khai, không có dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. `sources.csv` ánh xạ đủ năm file với URL và căn cứ sử dụng `public-page`.

## 2. Phương pháp kiểm chứng

Nhóm chạy `git fetch origin`, kiểm tra branch/commit, `REPORT_CANHAN.md`, handoff, experiment, code `src` và raw artifact. Không dùng số liệu chỉ dựa trên tin nhắn. Tests và `ingest.py` của ba branch remote được chạy lại độc lập từ archive commit; branch Đức Anh được kiểm tra trong Python 3.11 trước khi commit.

### Báo cáo cá nhân và provenance

| Thành viên | Branch | Commit | Artifact có trên branch |
|---|---|---|---|
| Nguyễn Đức Anh | `member/nguyen-duc-anh-fixed` | `c282d74` | Báo cáo, JSON raw và script FixedSize |
| Nguyễn Trọng Đăng Khoa | `member/nguyen-trong-dang-khoa-heading` | `b345446` | Báo cáo semantic; không có handoff/benchmark script machine-readable |
| Nguyễn Duy Thái | `member/nguyen-duy-thai-sentence` | `66c1415` | Báo cáo, handoff Markdown/JSON và script Sentence |
| Nguyễn Hoàng Long | `member/nguyen-hoang-long-recursive` | `283e835` | Báo cáo, `bench.py`, `bench_results.json`; không có handoff trong `report/member_handoffs/` |

Báo cáo cá nhân chính thức tiếp tục nằm trên branch cá nhân. `report/REPORT_CANHAN.md` của nhánh tích hợp chỉ là chỉ mục để một thành viên không ghi đè báo cáo của người khác.

### Benchmark chung

`experiments/team_strategy_benchmark.py` chạy cùng 5 query, corpus và backend `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 chiều). Raw output nằm tại `report/team_benchmark.json`.

Lệnh tái lập sau khi cài `requirements-local.txt`:

```powershell
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe experiments\team_strategy_benchmark.py --quiet
```

Một result được tính relevant khi đúng `doc_id` và chứa evidence term của gold answer. Metric “đủ evidence” yêu cầu hợp của các gold chunks trong top-3 chứa toàn bộ mốc/điều kiện chính. Thứ tự chọn strategy:

1. Số query relevant trong top-3.
2. Số query relevant ở top-1.
3. Số query có đủ evidence cho gold answer trong top-3.
4. Retrieval noise và max/avg chunk length.
5. Số chunk và chi phí.
6. Khả năng bảo trì.

Không so sánh raw cosine score từ benchmark `MockEmbedder` của Long với score multilingual của các thành viên khác.

## 3. Baseline comparison

Comparator đã kiểm chứng của Thái dùng FixedSize 500/50, Sentence(3) và Recursive(500) trên ba tài liệu. Ô thể hiện `số chunks / avg chars`.

| Tài liệu | Fixed 500/50 | Sentence(3) | Recursive(500) |
|---|---:|---:|---:|
| Hủy đơn | 5 / 414.40 | 6 / 310.67 | 5 / 372.60 |
| Trả hàng/hoàn tiền | 44 / 490.23 | 42 / 460.29 | 60 / 321.82 |
| Điều khoản dịch vụ | 185 / 499.37 | 149 / 556.23 | 251 / 329.63 |

Fixed tạo độ dài dự đoán được nhưng có thể cắt giữa ý. Sentence dễ đọc nhưng Markdown bảng/dòng không có dấu kết câu làm chunk quá dài. Recursive chuẩn repack theo separator giữ cấu trúc tốt hơn fixed; riêng implementation trong commit của Long không repack nên tạo nhiều mảnh cực ngắn. Heading giữ đường dẫn section/clause nhưng danh sách hoặc bảng dài vẫn có thể bị tách khỏi evidence continuation.

## 4. Bảng tổng hợp thành viên

Các cột số lượng/độ dài và relevance dưới đây dùng benchmark chung để so sánh công bằng. Handoff riêng ghi thêm số liệu gốc và phần thiếu của từng branch.

| Thành viên | MSSV | Branch | Commit | Strategy | Cấu hình thử nghiệm | Cấu hình tốt nhất | Embedding backend | Số chunk | Avg length | Max length | Top-1 relevant | Top-3 relevant | Filter impact | Tests | Điểm mạnh | Hạn chế |
|---|---|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|
| Nguyễn Đức Anh | 2A202601624 | `member/nguyen-duc-anh-fixed` | `c282d74` | FixedSize | 500/50; 800/100; 1200/150 | **800/100** | multilingual MiniLM | 199 | 793.00 | 800 | 3/5 | **5/5** | Rank 1 giữ nguyên; top-3 từ `cancellation, terms, cancellation` thành ba chunk `cancellation` | 42/42 | Đủ evidence 5/5, độ dài kiểm soát, chi phí vừa | Cắt theo ký tự; query 3 và 5 evidence ở rank 2 |
| Nguyễn Trọng Đăng Khoa | 2A202601964 | `member/nguyen-trong-dang-khoa-heading` | `b345446` | Markdown heading/clause | Chỉ có 500 trong artifact gốc | **500** | multilingual MiniLM | 517 | 330.86 | 500 | 3/5 | 3/5 | Loại nhiễu theo role nhưng evidence query 1 vẫn ngoài top-3 | 42/42 | Context heading/clause, max length chặt, truy vết tốt | Đủ evidence 2/5; thiếu script/handoff và chưa tune nhiều config |
| Nguyễn Duy Thái | 2A202601552 | `member/nguyen-duy-thai-sentence` | `66c1415` | Sentence | 3; 5; 8 câu/chunk | **8** | multilingual MiniLM | 124 | 1108.27 | 6301 | **4/5** | 4/5 | Rank 1 giữ nguyên; loại `both` noise, chỉ còn hai buyer chunks | 42/42 | Top-1 tốt nhất, giữ danh sách/điều khoản liền mạch | Bỏ lỡ query 2; chunk rất dài, dễ truncate/nhiễu |
| Nguyễn Hoàng Long | 2A202601134 | `member/nguyen-hoang-long-recursive` | `283e835` | Recursive theo commit | 500; 800; 1200 | **500** | Gốc: Mock; rerun: multilingual MiniLM | 2856 | 47.12 | 500 | 2/5 | 2/5 | Làm sạch doc IDs nhưng evidence query 1 vẫn không vào top-3 | 42/42 | Dùng separator tự nhiên; có script/JSON gốc | Không repack, mất context/delimiter, quá nhiều chunk; agent gốc chỉ là chuỗi demo |

### Số liệu các cấu hình

| Strategy/config | Chunks | Avg | Max | Top-1 | Top-3 | Đủ evidence top-3 |
|---|---:|---:|---:|---:|---:|---:|
| Fixed 500/50 | 311 | 494.23 | 500 | 3/5 | 4/5 | 4/5 |
| **Fixed 800/100** | **199** | **793.00** | **800** | **3/5** | **5/5** | **5/5** |
| Fixed 1200/150 | 134 | 1177.29 | 1200 | 1/5 | 2/5 | 1/5 |
| Sentence 3 | 329 | 417.08 | 3644 | 2/5 | 3/5 | 3/5 |
| Sentence 5 | 199 | 690.20 | 5893 | 2/5 | 3/5 | 3/5 |
| Sentence 8 | 124 | 1108.27 | 6301 | 4/5 | 4/5 | 4/5 |
| Heading 500 | 517 | 330.86 | 500 | 3/5 | 3/5 | 2/5 |
| Long Recursive 500 | 2856 | 47.12 | 500 | 2/5 | 2/5 | 2/5 |
| Long Recursive 800 | 1295 | 105.18 | 785 | 2/5 | 2/5 | 2/5 |
| Long Recursive 1200 | 790 | 173.10 | 1195 | 2/5 | 2/5 | 2/5 |

## 5. Strategy được chọn

Nhóm chọn **FixedSizeChunker `chunk_size=800`, `overlap=100`**.

Đây là strategy duy nhất đạt relevant top-3 và đủ evidence **5/5**. Sentence(8) có top-1 tốt hơn (4/5) nhưng bỏ lỡ hoàn toàn query thời hạn hoàn tiền và tạo chunk tối đa 6.301 ký tự; model có `max_seq_length=128`, nên chunk dài có nguy cơ truncate. Fixed 800 giữ max 800 ký tự, chỉ tạo 199 chunks và overlap 100 bảo toàn evidence ở biên tốt hơn 500/50. Fixed 1200 giảm số chunk nhưng làm embedding kém đặc hiệu/truncate và chỉ đạt top-3 2/5.

## 6. Kết quả đúng 5 query với Fixed 800/100

| # | Query rút gọn | Relevant rank | Source/chunk | Evidence/answer được kiểm chứng |
|---:|---|---:|---|---|
| 1 | Đơn không phải SPX ở “Chờ lấy hàng” có hủy ngay? | 1 | `shopee-order-cancellation`, chunk 0 | Không hủy ngay; cần chờ Người bán. Chấp nhận thì hủy, từ chối thì đơn tiếp tục giao. |
| 2 | Thời hạn trả hàng thường và thực phẩm tươi/đông lạnh? | 1 | `shopee-return-refund-policy`, chunk 4 | Hàng thường: 15 ngày từ khi giao thành công; thực phẩm tươi sống/đông lạnh: 24 giờ. |
| 3 | Yêu cầu ảnh thật và tỷ lệ diện tích? | 2 | `shopee-product-listing-rules`, chunk 7 | Ít nhất một ảnh thật do Người bán tự chụp; sản phẩm thật chiếm tối thiểu 40% diện tích ảnh. |
| 4 | Các nhóm chế tài hàng cấm/hạn chế? | 1 | `shopee-prohibited-products-policy`, chunk 1 | Xóa sản phẩm; giới hạn/đình chỉ/xóa tài khoản; cấn trừ/phong tỏa rút tiền; chế tài chính sách/pháp luật gồm hành chính, hình sự, bồi thường. |
| 5 | Chuyển tiền sớm nhất khi không nhấn hai nút? | 2 | `shopee-terms-of-service`, chunk 56 | Sớm nhất ngày thứ 04 sau khi giao thành công; có thể chậm hơn nếu nghi ngờ gian lận. |

**Relevant top-3:** 5/5. **Relevant top-1:** 3/5. **Đủ evidence cho gold answer trong top-3:** 5/5.

Repo không có production LLM hoặc API key hợp lệ để đánh giá generation. Vì vậy bảng ghi extractive evidence/gold-grounded answer, không tuyên bố chuỗi demo là câu trả lời LLM thật. `KnowledgeBaseAgent` và đường đi RAG vẫn được kiểm tra bằng injected `llm_fn` trong 42 unit tests.

## 7. Filtered và unfiltered

Query 1 được chạy A/B trên cùng Fixed 800/100:

- Không filter: top-3 doc IDs là `shopee-order-cancellation`, `shopee-terms-of-service`, `shopee-order-cancellation`; relevant rank = 1.
- Filter `{"customer_role": "buyer"}`: cả ba kết quả là `shopee-order-cancellation`; relevant rank vẫn = 1.
- Tác động: filter không tăng rank top-1 nhưng loại tài liệu role `both` khỏi candidate set, tăng precision theo chủ đề ở phần còn lại. Filter không nên được xem là thay thế cho chunking tốt vì ở Heading và Recursive, evidence đầy đủ vẫn nằm ngoài top-3 dù doc IDs đã sạch hơn.

## 8. Bài học kỹ thuật và đề xuất cải thiện

1. Top-1 score cao không đồng nghĩa đủ evidence. Query 5 có chunk nhiễu cùng tài liệu ở rank 1 và evidence ở rank 2; phải kiểm tra nội dung top-3 với gold answer.
2. Overlap vừa phải giúp Fixed 800 giữ evidence qua biên mà không nhân quá nhiều chunk. Overlap hoặc chunk quá lớn làm tăng trùng lặp/truncate.
3. Sentence boundaries phù hợp prose nhưng không đủ cho bảng Markdown, heading và danh sách không có dấu kết câu. Cần parser cấu trúc hoặc giới hạn ký tự phụ.
4. Heading context tăng traceability nhưng bảng/danh sách nên được xử lý như đơn vị nguyên tử; continuation cần overlap có kiểm soát.
5. Recursive splitter phải repack các mảnh nhỏ. Chỉ đệ quy rồi emit từng phần tạo hàng nghìn chunk 47 ký tự trung bình, làm mất ngữ cảnh và tăng chi phí.
6. Metadata filter hữu ích để loại role/category noise, nhưng có thể giảm recall nếu schema hoặc giá trị `both` không được xử lý theo ý nghĩa bao hàm.

Đề xuất tiếp theo: thêm table/list-aware chunker; batch embedding trong pipeline; cache theo content hash; đo latency/storage; thêm Recall@k, MRR và evidence coverage; hỗ trợ filter role theo quan hệ `buyer` khớp cả `buyer` và `both` khi nghiệp vụ yêu cầu.

## 9. Hình thức nộp project

**Demo/Presentation:** `Không áp dụng — project được nộp và đánh giá qua GitHub`.

Nhóm không chuẩn bị lời nói 5–7 phút, không phân công thuyết trình, không chờ buổi demo và không ghi bài học giả định “sau demo”. Toàn bộ bằng chứng nằm trong commit, handoff, benchmark JSON, script tái lập và báo cáo này.

## 10. Tự đánh giá trung thực

| Tiêu chí | Tự đánh giá | Căn cứ |
|---|---:|---|
| Document set quality | 10/10 | 5 tài liệu công khai, đủ metadata bắt buộc và nguồn truy vết |
| Strategy design | 15/15 | 4 strategy, config tuning, benchmark chung và failure analysis |
| Retrieval quality | 8/10 | Best strategy có evidence top-3 5/5, nhưng top-1 chỉ 3/5 và không có production LLM generation |
| Demo/Presentation | Không áp dụng | Project nộp qua GitHub; rubric chưa xác nhận quy đổi 5 điểm demo |
| **Tổng phần áp dụng** | **33/35** | Không tự cộng 5 điểm demo vào tổng /40 |

### Dữ liệu còn thiếu đã ghi nhận

- Khoa: không có handoff/benchmark script machine-readable và không có thử nghiệm nhiều `chunk_size` trên branch cá nhân.
- Long: không có handoff trong `report/member_handoffs/`; benchmark gốc dùng MockEmbedder, thiếu avg/max/filter A/B và không có agent answer thật.
- Không có production LLM evaluation cho bất kỳ thành viên nào; nhóm dùng evidence kiểm chứng thay vì bịa generation output.
