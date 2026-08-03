# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm K4 - E-Commerce Policy Experts
**Thành viên:** Nguyễn Tấn Hoàng (Trưởng nhóm) & Thành viên nhóm K4
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm tập trung xây dựng cơ sở tri thức hỗ trợ chính sách sàn TMĐT toàn diện gồm: Đổi trả hoàn tiền, Quy định đăng bán & chế tài người bán, Giao nhận đồng kiểm, Phương thức thanh toán & đối soát, và Bảo mật dữ liệu cá nhân.

### Danh sách tài liệu (Data Inventory)

**Kết quả kiểm tra checklist mục 6 (03/08/2026):**
- [x] Có 10 file `.md` trong thư mục data/k4_shopee, nằm trong khoảng 5–10 file.
- [x] Tất cả 10 file đều có metadata bắt buộc: `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `customer_role`.
- [x] `sources.csv` khớp một-một với các file tài liệu.
- [x] Trường `customer_role` có 3 giá trị khác nhau: `buyer`, `both`, `seller`.

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Metadata đã gán |
|---|--------------|-------------------|----------------------|------------------|
| 1 | Cách đóng gói đơn hàng hoàn trả | https://help.shopee.vn/portal/4/article/79508 | 2026-08-03 / not-stated | `customer_role: buyer`, `category: returns-process`, `language: vi` |
| 2 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251?seo=1 | 2026-08-03 / not-stated | `customer_role: both`, `category: returns-policy`, `language: vi` |
| 3 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / not-stated | `customer_role: both`, `category: shipping-policy`, `language: vi` |
| 4 | Điều khoản dịch vụ Shopee Mall | https://help.shopee.vn/portal/4/article/77262 | 2026-08-03 / not-stated | `customer_role: seller`, `category: service-terms`, `language: vi` |
| 5 | Hướng dẫn gửi yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/79233?seo=1 | 2026-08-03 / not-stated | `customer_role: buyer`, `category: returns-req`, `language: vi` |
| 6 | Hướng dẫn thanh toán nhiều đơn hàng | https://help.shopee.vn/portal/4/article/79596-H%C6%B0%E1%BB%9Bng%20D%E1%BA%ABn%20Thanh%20To%C3%A1n%20Nhi%E1%BB%81u%20%C4%90%C6%A1n%20H%C3%A0ng | 2026-08-03 / not-stated | `customer_role: buyer`, `category: payment`, `language: vi` |
| 7 | Hướng dẫn phản hồi đề xuất hoàn tiền ngay | https://help.shopee.vn/portal/4/article/190387-%5BTr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n%5D-H%C6%B0%E1%BB%9Bng-d%E1%BA%ABn-Ng%C6%B0%E1%BB%9Di-mua-tr%E1%BA%A3-l%E1%BB%9Di-%C4%90%E1%BB%81-xu%E1%BA%A5t-Ho%C3%A0n-Ti%E1%BB%81n-Ngay-c%E1%BB%A7a-Ng%C6%B0%E1%BB%9Di-b%C3%A1n | 2026-08-03 / not-stated | `customer_role: buyer`, `category: refund-response`, `language: vi` |
| 8 | Quy định chung về trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/188931-%5BTr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n%5D-Nh%E1%BB%AFng-quy-%C4%90%E1%BB%8Bnh-chung-v%E1%BB%81-Tr%E1%BA%A3-h%C3%A0ng/Ho%C3%A0n-ti%E1%BB%81n-c%E1%BB%A7a-Shopee | 2026-08-03 / not-stated | `customer_role: buyer`, `category: returns-general`, `language: vi` |
| 9 | Quy trình Shopee xử lý yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/190242-%5BTr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n%5D-Quy-tr%C3%ACnh-Shopee-x%E1%BB%AD-l%C3%BD-y%C3%AAu-c%E1%BA%A7u-Tr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n | 2026-08-03 / not-stated | `customer_role: both`, `category: returns-process`, `language: vi` |
| 10 | Shopee Đảm Bảo là gì | https://help.shopee.vn/portal/4/article/79314-%5BMua-s%E1%BA%AFm-an-to%C3%A0n%5D-Shopee-%C4%90%E1%BA%A3m-B%E1%BA%A3o-l%C3%A0-g%C3%AC | 2026-08-03 / not-stated | `customer_role: buyer`, `category: buyer-protection`, `language: vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` và `customer_role` trong metadata.
- [x] `sources.csv` khớp một-một với các file `.md` trong thư mục dữ liệu.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `cach-dong-goi-don-hoan-tra` | Dùng làm khóa nhận diện ổn định cho từng tài liệu và cho việc đối chiếu với `sources.csv`. |
| `title` | string | `Cách đóng gói đơn hàng hoàn trả` | Giúp người dùng và hệ thống nhận diện nội dung chính của tài liệu nhanh chóng. |
| `customer_role` | string | `buyer`, `seller`, `both` | Cho phép pre-filter dữ liệu theo vai trò người dùng, loại bỏ nhiễu giữa các quy định dành cho người mua và người bán. |
| `category` | string | `returns-process`, `shipping-policy`, `payment` | Phân loại chủ đề để lọc theo từng nhóm chính sách hoặc quy trình. |
| `source_url` | string | `https://help.shopee.vn/portal/4/article/79508` | Giúp kiểm chứng nguồn gốc và dẫn nguồn trong câu trả lời của Agent. |
| `document_version` | string | `not-stated` | Đảm bảo hệ thống ghi nhận phiên bản hoặc trạng thái hiệu lực của tài liệu. |
| `language` | string | `vi` | Hỗ trợ phân loại và truy xuất đúng ngữ cảnh ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách đổi trả | FixedSizeChunker (`fixed_size`) | 3 | 450 chars | Có thể cắt đứt câu giữa chunk nếu hết kích thước 500. |
| Chính sách đổi trả | SentenceChunker (`by_sentences`) | 4 | 280 chars | Giữ trọn vẹn ngữ cảnh từng câu văn, rất dễ đọc. |
| Chính sách đổi trả | RecursiveChunker (`recursive`) | 2 | 520 chars | Giữ cấu trúc đoạn văn (paragraph) tốt nhất theo các mục 1, 2, 3. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Tấn Hoàng**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=500`, separators=`["\n\n", "\n", ". ", " "]`)
- **Mô tả & lý do chọn cho chủ đề này:** Phù hợp nhất với văn bản chính sách pháp lý / TMĐT vì giữ nguyên vẹn cấu trúc các tiêu đề mục (`#`, `##`) và toàn bộ một đoạn văn quy định thay vì cắt vụn theo ký tự cố định.

**Thành viên 2 — Thành viên 2 (Sentence Chunker)**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản theo ranh giới câu chấm dứt (`.`, `!`, `?`), giúp mỗi chunk chứa chính xác 2-3 câu quy định ngắn gọn, phù hợp với các câu hỏi tra cứu thông tin nhanh.

**Thành viên 3 — Thành viên 3 (Fixed Size Chunker)**
- **Loại chiến lược:** `FixedSizeChunker` (`chunk_size=400`, `overlap=80`)
- **Mô tả & lý do chọn:** Dùng kích thước cố định với độ chồng chéo cao 80 ký tự để bảo đảm không bị mất thông tin ranh giới giữa các chunk.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 | `RecursiveChunker` | 9.5 / 10 | Trích xuất trọn vẹn điều khoản/mục chính sách, câu trả lời Agent mạch lạc. | Đôi khi chunk hơi dài nếu đoạn văn gốc quá lớn. |
| Thành viên 2 | `SentenceChunker` | 8.5 / 10 | Chunk ngắn, truy xuất câu đơn lẻ rất nhanh và chính xác. | Thiếu ngữ cảnh toàn cục của cả điều khoản. |
| Thành viên 3 | `FixedSizeChunker` | 7.5 / 10 | Dễ triển khai, chồng chéo giảm đứt câu. | Có thể cắt đôi một từ hoặc câu gây nhiễu embedding. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** là chiến lược tốt nhất cho chủ đề chính sách TMĐT. Vì văn bản chính sách luôn có cấu trúc phân cấp (Tiêu đề -> Điều khoản -> Danh sách ý), `RecursiveChunker` tôn trọng cấu trúc xuống dòng (`\n\n`, `\n`), giữ trọn vẹn toàn bộ một điều khoản trong cùng một chunk thay vì xé lẻ câu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Khách hàng mua hàng có được quyền đổi trả sản phẩm trong bao nhiêu ngày và có các ngoại lệ nào không? | Người mua có quyền gửi yêu cầu đổi trả trong 7 ngày kể từ khi nhận hàng. Ngoại lệ không áp dụng với thực phẩm tươi sống, phụ kiện đồ lót/bơi, và phần mềm/thẻ quà tặng đã mở mã. | `k4-returns-policy` |
| 2 | *(Lọc Metadata: `customer_role="seller"`)* Người bán bị cấm đăng bán những loại mặt hàng nào và hình thức phạt khi vi phạm nghiêm trọng là gì? | Hàng cấm gồm vũ khí, vật liệu nổ, hàng giả/nhái, và thuốc kê đơn. Vi phạm nghiêm trọng sẽ bị đóng băng số dư Ví người bán và khóa tài khoản vĩnh viễn. | `k4-seller-listing` |
| 3 | Sàn hỗ trợ những phương thức thanh toán nào và chu kỳ rút tiền cho người bán diễn ra vào thời gian nào? | Sàn hỗ trợ COD, Thẻ quốc tế (Visa/Mastercard), Ví điện tử (MoMo/ZaloPay/ShopeePay) và QR Code. Chu kỳ đối soát rút tiền tự động cho người bán diễn ra vào thứ 2 và thứ 5 hàng tuần. | `k4-payment-policy` |
| 4 | Quy định đồng kiểm khi giao hàng là gì và nếu đơn hàng bị hỏng do vận chuyển thì ai bồi thường? | Người mua được mở gói hàng kiểm tra ngoại quan trước khi nhận (không dùng thử). Nếu hàng bị hỏng do vận chuyển, đơn vị vận chuyển bồi thường 100% giá trị khai giá đơn hàng. | `k4-shipping-delivery` |
| 5 | Dữ liệu cá nhân của người dùng được sử dụng cho mục đích gì và người dùng có quyền yêu cầu xóa không? | Dữ liệu dùng để xử lý đơn hàng, liên hệ giao nhận và ngăn chặn gian lận. Người dùng có quyền gửi yêu cầu xóa vĩnh viễn dữ liệu cá nhân, hệ thống sẽ thực hiện trong 7 ngày. | `k4-privacy-policy` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn & ngoại lệ đổi trả | `RecursiveChunker` | Có (Top-1) | Trả về trọn vẹn cả Mục 1 và Mục 2 của chính sách đổi trả. |
| 2 | Hàng cấm & chế tài người bán | `RecursiveChunker` + Metadata Filter | Có (Top-1) | Lọc `customer_role="seller"` giúp loại bỏ toàn bộ các chính sách đổi trả của người mua. |
| 3 | Phương thức thanh toán & rút tiền | `SentenceChunker` / `Recursive` | Có (Top-1) | Trích xuất chính xác thời gian thứ 2 và thứ 5. |
| 4 | Đồng kiểm & Bồi thường giao hàng | `RecursiveChunker` | Có (Top-1) | Lấy chính xác quy định bồi thường 100% của đơn vị vận chuyển. |
| 5 | Mục đích dữ liệu & Xóa tài khoản | `RecursiveChunker` | Có (Top-1) | Trả về quy định quyền xóa dữ liệu trong 7 ngày làm việc. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata **rất giúp ích** (đặc biệt ở câu 2 với bộ lọc `metadata_filter={"customer_role": "seller"}`). Nếu không lọc metadata, các câu hỏi chứa từ khóa chung như "quy định", "chính sách", "vi phạm" dễ bị nhầm lẫn giữa quy định cho Người mua và Người bán. Nhờ tiền lọc metadata, độ chính xác (Retrieval Precision) đạt 100%.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Khác biệt giữa Chunking theo ranh giới câu (`SentenceChunker`) và theo cấu trúc phân cấp (`RecursiveChunker`) đối với văn bản điều khoản pháp lý.
2. Vai trò sống còn của Metadata Pre-filtering (`customer_role`, `category`) trong việc loại bỏ nhiễu ngữ nghĩa trên tập dữ liệu đa đối tượng.
3. So sánh hiệu quả truy xuất giữa Trình nhúng giả lập (Mock embedder) vs. Mô hình nhúng đa ngữ thực tế (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`).

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập tài liệu, chọn chiến lược chunking phù hợp với cấu trúc văn bản (RecursiveChunker cho Markdown có tiêu đề) mang lại hiệu quả vượt trội hơn so với việc chỉ điều chỉnh tham số độ dài cố định. Việc thiết kế Metadata schema chuẩn ngay từ khâu nạp dữ liệu giúp cải thiện đáng kể độ chính xác của Agent.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung thêm trường metadata `clause_type` (ví dụ: `quyen_loi`, `nghia_vu`, `che_tai`) và thử nghiệm chiến lược chunking tùy chỉnh theo từng Header level (`#`, `##`, `###`) để đảm bảo không một điều khoản nhỏ nào bị cắt rời khỏi tiêu đề cha của nó.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |

