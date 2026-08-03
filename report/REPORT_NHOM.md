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

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định chung về trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/188931 | 2026-08-03 / not-stated | 8,813 | `customer_role: buyer`, `category: doi_tra` |
| 2 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251 | 2026-08-03 / not-stated | 26,171 | `customer_role: both`, `category: doi_tra` |
| 3 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / not-stated | 32,754 | `customer_role: both`, `category: giao_hang` |
| 4 | Điều khoản dịch vụ Shopee Mall | https://help.shopee.vn/portal/4/article/77262 | 2026-08-03 / not-stated | 44,441 | `customer_role: seller`, `category: shopee_mall` |
| 5 | Quy trình Shopee xử lý yêu cầu trả hàng | https://help.shopee.vn/portal/4/article/190242 | 2026-08-03 / not-stated | 11,138 | `customer_role: both`, `category: quy_trinh` |
| 6 | Cách đóng gói đơn hàng hoàn trả | https://help.shopee.vn/portal/4/article/79508 | 2026-08-03 / not-stated | 4,976 | `customer_role: buyer`, `category: dong_goi` |
| 7 | Hướng dẫn gửi yêu cầu trả hàng hoàn tiền | https://help.shopee.vn/portal/4/article/79233 | 2026-08-03 / not-stated | 3,610 | `customer_role: buyer`, `category: huong_dan` |
| 8 | Hướng dẫn thanh toán nhiều đơn hàng | https://help.shopee.vn/portal/4/article/79596 | 2026-08-03 / not-stated | 1,689 | `customer_role: buyer`, `category: thanh_toan` |
| 9 | Hướng dẫn phản hồi đề xuất hoàn tiền ngay | https://help.shopee.vn/portal/4/article/190387 | 2026-08-03 / not-stated | 2,327 | `customer_role: buyer`, `category: phan_hoi` |
| 10 | Shopee Đảm Bảo là gì | https://help.shopee.vn/portal/4/article/79314 | 2026-08-03 / not-stated | 2,124 | `customer_role: both`, `category: dam_bao` |


**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string | `buyer`, `seller`, `both` | Giúp lọc chính xác ngữ cảnh quy định cho người mua hay người bán, loại bỏ nhiễu giữa hai đối tượng. |
| `category` | string | `doi_tra`, `dieu_kien_nguoi_ban`, `giao_hang` | Phân loại chủ đề chính sách để tiền lọc (pre-filter) trước khi tính Cosine Similarity. |
| `source_url` | string | `https://example.com/chinh-sach/doi-tra` | Giúp kiểm chứng nguồn gốc thông tin và dẫn nguồn trong câu trả lời của Agent. |
| `document_version` | string | `2026.2` | Đảm bảo hệ thống RAG truy xuất phiên bản chính sách mới nhất, tránh dùng dữ liệu cũ hết hạn. |

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
| 1 | Thời hạn gửi yêu cầu Trả hàng / Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng? | Người mua có thể gửi yêu cầu Trả hàng/Hoàn tiền trong vòng 7 ngày (hoặc 15 ngày đối với sản phẩm thuộc Shopee Mall) kể từ khi đơn hàng cập nhật trạng thái Giao hàng thành công. | `quy-dinh-chung-tra-hang-hoan-tien` / `chinh-sach-tra-hang-hoan-tien` |
| 2 | *(Lọc Metadata: `customer_role="seller"`)* Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và mức bồi thường khi phát hiện bán hàng giả là bao nhiêu? | Người bán Shopee Mall cam kết 100% hàng chính hãng. Nếu phát hiện bán hàng giả/nhái, Shopee Mall phạt và hoàn 200% giá trị sản phẩm cho Người mua từ chi phí của Người bán. | `dieu-khoan-dich-vu-shopee-mall` |
| 3 | Shopee quy định như thế nào về việc đồng kiểm khi nhận hàng từ đơn vị vận chuyển? | Người mua được phép đồng kiểm (mở hộp kiểm tra số lượng, ngoại quan, không dùng thử sản phẩm) trước mặt nhân viên giao hàng khi nhận đơn hàng. | `chinh-sach-van-chuyen` |
| 4 | Tính năng "Shopee Đảm Bảo" bảo vệ Người mua như thế nào và giữ tiền thanh toán trong bao lâu? | Shopee Đảm Bảo giữ tiền thanh toán của Người mua cho đến khi Người mua xác nhận đã nhận hàng thỏa đáng hoặc hết thời hạn Trả hàng/Hoàn tiền (7-15 ngày). | `shopee-dam-bao` |
| 5 | Quy định đóng gói đơn hàng hoàn trả về cho Shopee hoặc Người bán cần đáp ứng những yêu cầu gì? | Hàng hoàn trả phải đóng gói kỹ bằng thùng carton/túi niêm phong nguyên vẹn, dán Mã trả hàng/Phiếu giao hoàn trả bên ngoài và kèm đầy đủ phụ kiện, quà tặng đi kèm. | `cach-dong-goi-don-hoan-tra` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn Trả hàng / Hoàn tiền | `RecursiveChunker` | Có (Top-1) | Truy xuất chính xác thời hạn 7 ngày / 15 ngày đối với Shopee Mall. |
| 2 | Hàng chính hãng Shopee Mall & Phạt 200% | `RecursiveChunker` + Metadata Filter | Có (Top-1) | Lọc `customer_role="seller"` trích xuất chính xác Điều khoản dịch vụ Shopee Mall. |
| 3 | Quy định đồng kiểm khi nhận hàng | `RecursiveChunker` / `Sentence` | Có (Top-1) | Lấy chính xác điều khoản đồng kiểm ngoại quan trong chính sách vận chuyển. |
| 4 | Shopee Đảm Bảo giữ tiền thanh toán | `RecursiveChunker` | Có (Top-1) | Trích xuất điều khoản bảo vệ người mua của tính năng Shopee Đảm Bảo. |
| 5 | Quy định đóng gói đơn hàng hoàn trả | `RecursiveChunker` | Có (Top-1) | Trả về quy định đóng gói thùng carton và mã trả hàng ngoài vỏ hộp. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata **rất giúp ích** (đặc biệt ở câu 2 với bộ lọc `metadata_filter={"customer_role": "seller"}`). Giữa 229 chunks trong tập tài liệu Shopee lớn (`k4_shopee`), việc lọc `customer_role="seller"` giúp loại bỏ 100% các điều hướng dành cho người mua, đưa chính xác các điều khoản chế tài của Shopee Mall lên Top-1.


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

