# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [Tên nhóm]
**Thành viên:** [Họ tên từng thành viên]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Vòng đời đơn hàng và quy tắc marketplace trên Shopee Việt Nam, từ đăng bán và sản phẩm bị cấm đến thanh toán, hủy đơn, trả hàng và hoàn tiền.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77251?seo=1) | 2026-08-03 / 2026-03-11 | 19,420 | `customer_role=both`, `category=returns-refunds`, `language=vi` |
| 2 | Tôi có thể hủy đơn hàng không? | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79182?seo=1) | 2026-08-03 / `not-stated` | 1,872 | `customer_role=buyer`, `category=order-cancellation`, `language=vi` |
| 3 | Quy định về đăng bán sản phẩm trên Shopee | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77246?seo=1) | 2026-08-03 / 2024-08-21 | 21,279 | `customer_role=seller`, `category=product-listing`, `language=vi` |
| 4 | Chính sách cấm/hạn chế sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77247?seo=1) | 2026-08-03 / 2025-05-05 | 12,653 | `customer_role=seller`, `category=prohibited-products`, `language=vi` |
| 5 | Điều khoản dịch vụ | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77243?seo=1) | 2026-08-03 / 2026-05-01 | 83,183 | `customer_role=both`, `category=payments-and-orders`, `language=vi` |

Số ký tự được tính trên phần nội dung đã làm sạch, không gồm YAML front matter.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-order-cancellation` | Định danh duy nhất, trùng tên file và dùng để truy vết/xóa toàn bộ chunk của một tài liệu. |
| `title` | string | `Tôi có thể hủy đơn hàng không?` | Hiển thị nguồn dễ đọc trong kết quả retrieval. |
| `source_url` | URL | `https://help.shopee.vn/...` | Đối chiếu câu trả lời với nguồn công khai gốc. |
| `retrieved_at` | date | `2026-08-03` | Xác định thời điểm nhóm thu thập dữ liệu. |
| `document_version` | string/date | `2026-03-11`, `not-stated` | Phân biệt phiên bản chính sách; không suy đoán khi nguồn không nêu. |
| `customer_role` | enum | `buyer`, `seller`, `both` | Lọc tài liệu theo vai trò khách hàng; đây là field filter bắt buộc của K4. |
| `category` | enum | `order-cancellation`, `product-listing` | Thu hẹp retrieval theo nghiệp vụ cụ thể. |
| `language` | string | `vi` | Xác nhận ngôn ngữ corpus và query. |
| `effective_date` | date, optional | `2026-05-01` | Cho biết ngày chính sách có hiệu lực khi nguồn công bố rõ ràng. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

Khoa chạy cùng `chunk_size=500` trên phần body đã bỏ YAML front matter. Bảng ghi `số chunk / độ dài trung bình`; đây là thống kê cấu trúc thực tế, chưa phải điểm chất lượng semantic retrieval.

| Tài liệu | Fixed-size | By-sentences | Recursive | Heading/clause-aware |
|-----------|----------:|-------------:|----------:|---------------------:|
| Hủy đơn hàng | 4 / 468.0 | 6 / 308.5 | 5 / 374.4 | 9 / 264.9 |
| Trả hàng/hoàn tiền | 39 / 497.9 | 42 / 458.6 | 69 / 281.4 | 76 / 332.5 |
| Quy định đăng bán | 43 / 494.9 | 77 / 272.8 | 53 / 401.5 | 80 / 348.2 |

Sentence-based không nhận tham số kích thước ký tự nên chunk dài nhất trên ba tài liệu lần lượt là 525, 1,015 và 1,051 ký tự. Custom giữ chunk dài nhất không quá 500 ký tự trong cả ba lần chạy.

### Chiến lược của từng thành viên

**Nguyễn Trọng Đăng Khoa — 2A202601964**
- **Loại chiến lược:** custom `MarkdownHeadingChunker` trong `src/chunking.py`.
- **Cách hoạt động:** Nhận diện cây heading Markdown từ `#` đến `######` và cây nhãn điều khoản như `3.`, `3.1.`, `3.1.2.`. Mỗi chunk bắt đầu bằng đường dẫn heading/nhãn đang hoạt động. Nếu nội dung section quá lớn, phần body được chia đệ quy theo `\n\n`, `\n`, `. `, khoảng trắng rồi cắt cứng; đường dẫn context được lặp lại trên mọi continuation chunk.
- **Vì sao phù hợp với chính sách Shopee:** Các quy định Shopee tổ chức nghĩa vụ, ngoại lệ, đối tượng áp dụng và chế tài dưới các mục/điều đánh số. Một đoạn như thời hạn “15 ngày” dễ mất phạm vi nếu tách khỏi tiêu đề “Điều kiện yêu cầu trả hàng/hoàn tiền” hoặc nhãn `3.2.`; lặp context giúp retriever trả về đoạn tự giải thích và có vị trí điều khoản để kiểm chứng.
- **Kiểm tra bảo toàn context:** Điều `3.2.` của chính sách trả hàng/hoàn tiền được chia thành 2 chunks; cả 2 đều giữ `# Chính sách trả hàng và hoàn tiền`, heading mục 3 và nhãn `3.2.`.
- **So với ba baseline:** Fixed-size kiểm soát độ dài tốt nhưng có thể cắt giữa điều khoản và không hiểu heading. Sentence-based giữ câu nguyên vẹn nhưng có chunk vượt xa 500 ký tự và không tự mang tên section. Recursive ưu tiên ranh giới đoạn/câu và kiểm soát kích thước tốt hơn, nhưng continuation chunk không tự lặp heading. Custom tạo nhiều chunk hơn và tốn thêm token do lặp context, đổi lại giữ được phạm vi chính sách và khả năng truy vết điều/khoản.

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Metadata filter | Câu trả lời chuẩn (Gold Answer) | Vị trí kiểm chứng trong corpus |
|---|-------|-----------------|-------------------------------|-------------------------------|
| 1 | Đơn hàng do đơn vị vận chuyển không phải SPX đang ở trạng thái “Chờ lấy hàng” thì Người mua có thể hủy ngay không? | `{"customer_role": "buyer"}` | Không. Người mua phải chờ phản hồi của Người bán: nếu Người bán chấp nhận thì đơn được hủy ngay; nếu từ chối thì đơn không bị hủy và tiếp tục được giao. | `shopee-order-cancellation`, mục 1, dòng “Chờ lấy hàng” trong bảng trạng thái. |
| 2 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn được giao thành công, và thời hạn riêng cho thực phẩm tươi sống hoặc đông lạnh là bao lâu? | Không | Hàng thông thường: 15 ngày kể từ khi đơn được cập nhật giao thành công. Thực phẩm tươi sống hoặc đông lạnh: 24 giờ. | `shopee-return-refund-policy`, mục 3 “Điều kiện yêu cầu trả hàng/hoàn tiền”, Điều 3.2. |
| 3 | Ảnh sản phẩm đăng bán trên Shopee phải đáp ứng yêu cầu tối thiểu nào về ảnh thật và tỷ lệ diện tích sản phẩm? | Không | Phải có ít nhất một ảnh thật của sản phẩm do chính Người bán tự chụp; sản phẩm thật phải chiếm ít nhất 40% diện tích ảnh đó. | `shopee-product-listing-rules`, mục C.1 “Hình ảnh sản phẩm”, điểm b. |
| 4 | Vi phạm Chính sách Cấm/Hạn chế Sản phẩm có thể khiến Người bán chịu những nhóm chế tài nào? | Không | Sản phẩm có thể bị xóa; tài khoản bị giới hạn quyền; tài khoản bị đình chỉ hoặc xóa; số dư bị cấn trừ hoặc quyền rút tiền bị phong tỏa; và có thể chịu chế tài khác theo chính sách hoặc pháp luật như phạt hành chính, xử lý hình sự hay bồi thường thiệt hại. | `shopee-prohibited-products-policy`, mục 3 “Hành vi vi phạm và biện pháp xử lý”. |
| 5 | Nếu Người mua không nhấn “Đã nhận được hàng” hoặc “Trả hàng/Hoàn tiền”, Shopee chuyển tiền cho Người bán sớm nhất khi nào? | Không | Sớm nhất vào ngày thứ 4 kể từ khi đơn được cập nhật trạng thái giao hàng thành công; Shopee có thể thanh toán muộn hơn nếu đơn hàng bị nghi ngờ gian lận. | `shopee-terms-of-service`, mục 10 “Số dư tài khoản Shopee”, Điều 10.3(a). |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Trong lượt chạy của Khoa ở câu 1, không filter chỉ có top-1 thuộc tài liệu hủy đơn; top-2 và top-3 là nhiễu từ Điều khoản dịch vụ và Chính sách trả hàng/hoàn tiền. Filter `customer_role=buyer` làm cả ba kết quả thuộc tài liệu hủy đơn, nên tăng precision theo chủ đề, nhưng bảng có đáp án vẫn ở hạng 4 và top-3 vẫn chưa trả lời được câu hỏi. Kết quả của các thành viên khác cần được bổ sung sau khi nhóm chạy chung.

### Kết quả cá nhân của Nguyễn Trọng Đăng Khoa

Khoa chạy custom heading/clause-aware với mô hình `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` trên 517 chunks. Câu 2 và 3 có chunk đáp án đầy đủ ở top-1; câu 4 có phần đầu danh sách chế tài ở top-1 nhưng continuation chứa mục (v) chỉ xếp hạng 6. Câu 1 có bảng đáp án ở hạng 4 dù đã lọc `customer_role=buyer`; câu 5 không có chunk đáp án trong top-30. Theo rubric: **5/10**, và **3/5** câu có ít nhất một chunk liên quan trong top-3 nếu tính câu 4 là liên quan nhưng chưa đầy đủ.

**Failure case:** Query 1 minh họa điểm yếu do tách bảng khỏi đoạn dẫn: heading được bảo toàn nhưng query gần đoạn mô tả tổng quát hơn bảng trạng thái, khiến bảng đúng rơi xuống hạng 4. Query 4 cho thấy danh sách chế tài dài bị tách giữa mục (iv) và (v), còn query 5 cho thấy chỉ giữ heading/nhãn chưa đủ khi cách diễn đạt query khác mạnh với clause dài. Hướng cải thiện là nhận diện bảng/danh sách như đơn vị nguyên tử, thêm overlap có kiểm soát giữa continuation chunks, và thử tăng `chunk_size` cho section dạng danh sách trước khi đánh giá lại trên cùng năm query.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
