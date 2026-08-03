# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** TeamB - E402  
**Thành viên:** Trương Quang Minh (FixedSize + LocalEmbedder); Phạm Anh Minh (Recursive, kết quả thực tế); Phạm Ngọc Quốc Khánh (Sentence + `nomic-embed-text`/`qwen2.5-coder`); Phạm Hà Anh (FixedSize + MockEmbedder)  
**Ngày:** 03/08/2026

> **Lưu ý tính trung thực:** FixedSize, Recursive và Sentence đều đã có báo cáo thực nghiệm. Tuy nhiên các thành viên chưa dùng cùng embedding/LLM: Trương Quang Minh dùng LocalEmbedder MiniLM, Phạm Ngọc Quốc Khánh dùng `nomic-embed-text:latest` để embedding và `qwen2.5-coder:1.5b` để trả lời, còn Phạm Hà Anh dùng MockEmbedder. Vì vậy bảng hiện phản ánh kết quả hệ thống của từng người, chưa cô lập riêng ảnh hưởng của chunker.

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm xây dựng cơ sở tri thức hỗ trợ người mua và người bán trên Shopee Việt Nam, tập trung vào vòng đời giao dịch (thanh toán, vận chuyển, trả hàng/hoàn tiền, bảo hành), an toàn nền tảng (bảo mật, chống gian lận, hàng cấm) và quy định đăng bán/chăm sóc khách hàng.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách bảo hành | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79046-%5BQuy%20%C4%91%E1%BB%8Bnh%5D%20Ch%C3%ADnh%20s%C3%A1ch%20b%E1%BA%A3o%20h%C3%A0nh%20cho%20s%E1%BA%A3n%20ph%E1%BA%A9m%20mua%20t%E1%BA%A1i%20Shopee) | 03/08/2026 / không nêu | 4.204 | `buyer`, `warranty-policy`, `vi` |
| 2 | Chính sách bảo mật | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77244-CH%C3%8DNH%20S%C3%81CH%20B%E1%BA%A2O%20M%E1%BA%ACT) | 03/08/2026 / không nêu | 42.794 | `both`, `privacy-policy`, `vi` |
| 3 | Chính sách cấm/hạn chế sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77247-CH%C3%8DNH%20S%C3%81CH%20C%E1%BA%A4M%2FH%E1%BA%A0N%20CH%E1%BA%BE%20S%E1%BA%A2N%20PH%E1%BA%A8M) | 03/08/2026 / không nêu | 12.250 | `seller`, `prohibited-products`, `vi` |
| 4 | Chính sách chống gian lận người bán | [Shopee Help Center](https://help.shopee.vn/portal/4/article/140097-CH%C3%8DNH%20S%C3%81CH%20CH%E1%BB%90NG%20H%C3%80NH%20VI%20GIAN%20L%E1%BA%ACN%20TR%C3%8AN%20S%C3%80N%20SHOPEE%20V%C3%80%20C%C3%81C%20BI%E1%BB%86N%20PH%C3%81P%20X%E1%BB%AC%20L%C3%9D%20%C4%90%E1%BB%90I%20V%E1%BB%9AI%20NG%C6%AF%E1%BB%9CI%20B%C3%81N%20VI%20PH%E1%BA%A0M) | 03/08/2026 / 28/12/2023 | 6.259 | `seller`, `seller-violations`, `vi` |
| 5 | Chính sách trả hàng và hoàn tiền | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77251-CH%C3%8DNH%20S%C3%81CH%20TR%E1%BA%A2%20H%C3%80NG%20V%C3%80%20HO%C3%80N%20TI%E1%BB%80N) | 03/08/2026 / không nêu | 19.167 | `buyer`, `returns-policy`, `vi` |
| 6 | Chính sách vận chuyển | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77250-CH%C3%8DNH%20S%C3%81CH%20V%E1%BA%ACN%20CHUY%E1%BB%82N%20SHOPEE) | 03/08/2026 / không nêu | 24.051 | `buyer`, `shipping-policy`, `vi` |
| 7 | Điều khoản dịch vụ | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77243-%C4%90I%E1%BB%80U%20KHO%E1%BA%A2N%20D%E1%BB%8ACH%20V%E1%BB%A4) | 03/08/2026 / 01/05/2026 | 83.114 | `both`, `terms-of-service`, `vi` |
| 8 | Cách liên hệ chăm sóc khách hàng | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79191-%5BD%E1%BB%8Bch%20v%E1%BB%A5%5D%20C%C3%A1ch%20li%C3%AAn%20h%E1%BB%87%20Ch%C4%83m%20s%C3%B3c%20kh%C3%A1ch%20h%C3%A0ng%20Shopee) | 03/08/2026 / không nêu | 819 | `both`, `customer-support-contact`, `vi` |
| 9 | Quy định đăng bán sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77246-QUY%20%C4%90%E1%BB%8ANH%20V%E1%BB%80%20%C4%90%C4%82NG%20B%C3%81N%20S%E1%BA%A2N%20PH%E1%BA%A8M%20TR%C3%8AN%20SHOPEE) | 03/08/2026 / không nêu | 21.270 | `seller`, `seller-listing`, `vi` |
| 10 | Tổng hợp câu hỏi thường gặp về thanh toán | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79526-%5BThanh%20to%C3%A1n%5D%20T%E1%BB%95ng%20h%E1%BB%A3p%20c%C3%A1c%20c%C3%A2u%20h%E1%BB%8Fi%20th%C6%B0%E1%BB%9Dng%20g%E1%BA%B7p) | 03/08/2026 / không nêu | 3.567 | `buyer`, `payment-faq`, `vi` |

Số ký tự trong bảng được tính trên phần nội dung sau khi loại YAML front matter. Corpus có tổng cộng **217.495 ký tự nội dung**, gồm 4 tài liệu cho người mua, 3 tài liệu cho người bán và 3 tài liệu áp dụng cho cả hai vai trò.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Corpus chỉ chứa các trang trợ giúp/chính sách công khai của Shopee, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ; `sources.csv` ghi nhận quyền sử dụng là `public-page`.
- [x] Cả 10 tài liệu đều có `source_url`, `retrieved_at` và `document_version`; khi nguồn không công bố phiên bản, giá trị được ghi minh bạch là `not-stated` thay vì tự suy đoán.
- [x] `sources.csv` có 10 dòng và ánh xạ 1–1 với 10 file Markdown; script `validate_k4_corpus.py` trả về **ĐẠT checklist**.
- [x] Mỗi tài liệu có `customer_role` hợp lệ và ít nhất một trường lọc phụ (`category`, `language`).

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | Chuỗi, duy nhất | `chinh-sach-tra-hang-hoan-tien` | Định danh tài liệu nguồn, hỗ trợ truy vết chunk và xóa toàn bộ chunk của một tài liệu. |
| `title` | Chuỗi | `CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN` | Hiển thị tên nguồn dễ hiểu và hỗ trợ kiểm tra kết quả truy xuất. |
| `source_url` | URL | `https://help.shopee.vn/...` | Cho phép đối chiếu câu trả lời với trang chính sách công khai gốc. |
| `retrieved_at` | Ngày ISO (`YYYY-MM-DD`) | `2026-08-03` | Biết thời điểm thu thập và phát hiện dữ liệu cần cập nhật. |
| `document_version` | Ngày ISO hoặc chuỗi trạng thái | `2023-12-28`, `not-stated` | Phân biệt phiên bản chính sách; tránh khẳng định ngày hiệu lực khi nguồn không nêu. |
| `customer_role` | Enum chuỗi | `buyer`, `seller`, `both` | Lọc trước theo vai trò; đặc biệt hữu ích cho truy vấn chỉ dành cho người bán hoặc người mua. |
| `category` | Enum chuỗi | `returns-policy` | Thu hẹp tìm kiếm theo nghiệp vụ như đổi trả, vận chuyển, bảo hành hoặc bảo mật. |
| `language` | Mã ngôn ngữ | `vi` | Chọn đúng ngôn ngữ corpus hoặc embedding khi hệ thống mở rộng đa ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

Nhóm chọn ba tài liệu có độ dài khác nhau và chạy với `chunk_size=200`. Nội dung được đọc bằng `load_documents()` trong `ingest.py`; hàm này gọi `parse_front_matter()` và chỉ chuyển phần body cho comparator, vì vậy số liệu dưới đây **không tính khối YAML metadata**. Việc kiểm tra chuỗi đầu vào cho thấy mỗi body bắt đầu bằng tiêu đề Markdown (`# ...`), không bắt đầu bằng dấu `---`.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách bảo hành (4.204 ký tự) | FixedSizeChunker (`fixed_size`) | 28 | 198,36 | Trung bình — kích thước đều nhưng có thể cắt ngang câu/danh sách. |
| Chính sách bảo hành (4.204 ký tự) | SentenceChunker (`by_sentences`) | 5 | 839,20 | Tốt theo ranh giới câu, nhưng cả 5 chunk đều vượt 200 ký tự. |
| Chính sách bảo hành (4.204 ký tự) | RecursiveChunker (`recursive`) | 31 | 133,94 | Tốt — ưu tiên đoạn/dòng và mọi chunk đều không quá 200 ký tự. |
| Chính sách trả hàng và hoàn tiền (19.167 ký tự) | FixedSizeChunker (`fixed_size`) | 128 | 199,35 | Trung bình — dễ dự đoán nhưng nhiều điều khoản bị cắt theo vị trí ký tự. |
| Chính sách trả hàng và hoàn tiền (19.167 ký tự) | SentenceChunker (`by_sentences`) | 46 | 414,67 | Khá mạch lạc theo câu, nhưng 39/46 chunk vượt giới hạn 200 ký tự. |
| Chính sách trả hàng và hoàn tiền (19.167 ký tự) | RecursiveChunker (`recursive`) | 164 | 115,13 | Tốt — giữ ranh giới cấu trúc khi có thể; không chunk nào vượt 200 ký tự. |
| Điều khoản dịch vụ (83.114 ký tự) | FixedSizeChunker (`fixed_size`) | 554 | 199,94 | Thấp–trung bình — tài liệu dài làm tăng số lần cắt ngang điều/khoản. |
| Điều khoản dịch vụ (83.114 ký tự) | SentenceChunker (`by_sentences`) | 163 | 507,88 | Giữ câu nhưng kích thước thiếu ổn định; 147/163 chunk vượt 200, lớn nhất 5.287 ký tự. |
| Điều khoản dịch vụ (83.114 ký tự) | RecursiveChunker (`recursive`) | 654 | 125,38 | Tốt nhất trong ba baseline — bám đoạn/dòng và bảo đảm tối đa 200 ký tự. |

Kết quả cho thấy `FixedSizeChunker` kiểm soát kích thước tốt nhưng không tôn trọng cấu trúc ngôn ngữ. `SentenceChunker` giữ câu nguyên vẹn, song văn bản chính sách Shopee có nhiều điều/khoản và dòng dài không kết thúc bằng `.`, `!`, `?`, khiến chunk vượt xa mục tiêu. `RecursiveChunker` tạo nhiều chunk hơn nhưng cân bằng tốt hơn giữa giới hạn kích thước và ranh giới đoạn/dòng, nên phù hợp nhất làm baseline cho corpus này.

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Trương Quang Minh **
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=400, overlap=50)`
- **Mô tả & lý do chọn:** Chunk 400 ký tự giúp chi phí và số lượng vector dễ dự đoán; overlap 50 giữ lại một phần nội dung ở ranh giới hai chunk. Chiến lược tạo 625 chunk trên corpus và phù hợp làm đường cơ sở, dù có nguy cơ cắt ngang câu/điều khoản.
- **Kết quả:** LocalEmbedder đưa gold context vào top-3 ở 3/5 query (câu 1, 2, 5); điểm tự chấm thận trọng 3/10 vì agent demo chỉ in context preview.

**Thành viên 2 — Phạm Anh Minh (đã chạy thực tế)**
- **Loại chiến lược:** `RecursiveChunker`, ưu tiên separator `["\n\n", "\n", ". ", " ", ""]`.
- **Mô tả & lý do chọn:** Chiến lược ưu tiên đoạn, dòng và câu trước khi cắt theo từ/ký tự, phù hợp với văn bản chính sách nhiều cấp. Các phần dài tiếp tục được tách đệ quy nên vẫn kiểm soát được kích thước chunk.
- **Kết quả:** 42/42 test và tự chấm retrieval **7/10**. Câu 1 đúng top-1 (0,702), câu 5 đúng top-1 (0,760); câu 2 và 4 có gold context trong top-3 nhưng top-1 sai chủ đề. Báo cáo ghi 5/5 có chunk liên quan trong top-3, tuy nhiên câu 3 cần đối chiếu lại vì top-1 nói về giới hạn kích thước, chưa khớp gold chung là ngưỡng 50 triệu đồng.

**Thành viên 3 — Phạm Ngọc Quốc Khánh (đã chạy thực tế)**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`
- **Model:** `nomic-embed-text:latest` tạo embedding; `qwen2.5-coder:1.5b` sinh câu trả lời của agent.
- **Mô tả & lý do chọn:** Gom tối đa ba câu liên tiếp để bảo toàn ranh giới ngôn ngữ, phù hợp FAQ và đoạn văn xuôi. Trên corpus Markdown, tiêu đề và danh sách thường không có dấu kết câu nên nhiều phần khác chủ đề có thể bị dính vào cùng chunk dài.
- **Kết quả:** Tạo **149 chunk**, vượt 42/42 test và tự chấm retrieval **5/10**. Câu 2 và 3 đúng top-1 (0,800 và 0,821); câu 1, 4 và 5 top-1 bị nhiễu. Báo cáo kết luận 2/5 query có chunk liên quan trong top-3.

**Thành viên 4 — Phạm Hà Anh (đã chạy với backend mock)**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=400, overlap=50)`
- **Embedding:** `MockEmbedder(dim=64)`.
- **Mô tả & kết quả:** Cấu hình chunking giống Trương Quang Minh, tạo 625 chunk, nhưng vector mock được sinh từ hash của toàn chuỗi và không biểu diễn ngữ nghĩa tiếng Việt. Vì vậy top-3 thường chứa đoạn không liên quan hoặc đúng tài liệu nhưng sai điều khoản; kết quả được ghi nhận là **0/10** theo tiêu chí nghiêm ngặt.
- **Ý nghĩa:** Kết quả này minh họa ảnh hưởng của embedding backend, không chứng minh FixedSize kém hơn các chunker khác. Khi so sánh chiến lược chính thức, Phạm Hà Anh cần chạy lại cùng LocalEmbedder và cùng năm query.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Trương Quang Minh | Fixed size 400, overlap 50 | **3/10 (thực nghiệm)** | Đơn giản, 625 chunk, câu 2 và 5 đúng top-1 | Có thể cắt ngang điều khoản; thất bại câu 3–4 |
| Phạm Hà Anh | Fixed size 400, overlap 50 + MockEmbedder | **0/10 (thực nghiệm mock)** | Chạy offline, xác định và dễ tái lập | Không nắm bắt ngữ nghĩa; không dùng để xếp hạng chunker |
| Phạm Anh Minh | Recursive, ưu tiên đoạn/dòng/câu | **7/10 (thực nghiệm)** | Câu 1 và 5 đúng top-1; giữ cấu trúc tốt | Câu 2 và 4 top-1 sai; câu 3 cần đối chiếu gold |
| Phạm Ngọc Quốc Khánh | Sentence, 3 câu/chunk; nomic embedding | **5/10 (thực nghiệm)** | Câu 2–3 đúng top-1; giữ câu văn xuôi | Tiêu đề/list Markdown bị dính; chỉ 2/5 relevant top-3 |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Trong các kết quả hệ thống hiện có, Recursive của Phạm Anh Minh đạt điểm retrieval cao nhất (7/10), tiếp theo là Sentence của Phạm Ngọc Quốc Khánh (5/10) và FixedSize của Trương Quang Minh (3/10). Recursive phù hợp nhất với cấu trúc nhiều đoạn/điều khoản, còn Sentence hoạt động tốt ở văn xuôi nhưng kém với heading/list Markdown. Thứ hạng này vẫn cần kiểm tra lại trên cùng embedding và LLM để trở thành so sánh chunker công bằng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tôi có bao nhiêu ngày để yêu cầu trả hàng kể từ khi đơn hàng giao thành công? | 15 ngày kể từ lúc đơn hàng được cập nhật giao hàng thành công; riêng thực phẩm tươi sống/đông lạnh chỉ có 24 giờ. | `chinh-sach-tra-hang-hoan-tien.md`, mục 3.2 |
| 2 | Thời gian xử lý bảo hành dự kiến là bao lâu? | Dự kiến từ 20 đến 45 ngày làm việc kể từ lúc Shopee nhận được sản phẩm, tùy thuộc linh kiện cần thay thế. | `chinh-sach-bao-hanh.md`, phần quy trình gửi sản phẩm bảo hành về Shopee |
| 3 | Đơn hàng nào không hỗ trợ vận chuyển? | Trên 50.000.000 VNĐ tổng giá trị hàng hóa (đã tính giá khuyến mãi nếu có, không gồm mã giảm giá, Shopee Xu và phí vận chuyển). | `chinh-sach-van-chuyen.md`, mục 1.1.d |
| 4 | Lịch sử trò chuyện với chăm sóc khách hàng lưu trữ tối đa bao lâu? | Tối đa 180 ngày. | `lien-he-cham-soc-khach-hang.md`, mục "Kiểm tra lịch sử tin nhắn (Chat)" |
| 5 *(cần lọc metadata)* | Người bán vi phạm chính sách sẽ bị áp dụng những chế tài nào? | (i) Xóa sản phẩm; (ii) giới hạn quyền tài khoản; (iii) đình chỉ/xóa tài khoản; (iv) cấn trừ số dư & phong tỏa rút tiền; (v) các chế tài khác kể cả phạt hành chính/xử lý hình sự/bồi thường thiệt hại. | `chinh-sach-cam-han-che-san-pham.md`, mục 3 "HÀNH VI VI PHẠM VÀ BIỆN PHÁP XỬ LÝ" |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn yêu cầu trả hàng | Recursive (Phạm Anh Minh) | Có, top-1 | Đúng mục 15 ngày, score 0,702; FixedSize có gold ở top-2. |
| 2 | Thời gian bảo hành | Sentence (Phạm Ngọc Quốc Khánh) | Có, top-1 | Đúng chính sách bảo hành, score 0,800; FixedSize cũng đúng top-1 ở 0,6536. |
| 3 | Đơn không hỗ trợ vận chuyển | Sentence (Phạm Ngọc Quốc Khánh) | Có, top-1 theo báo cáo cá nhân | Chunk quy định giới hạn đơn hàng/vận chuyển đạt 0,821; cần bảo đảm đoạn lưu khi nộp có đúng ngưỡng 50 triệu của gold chung. |
| 4 | Lưu lịch sử Chat | Recursive (Phạm Anh Minh) | Có trong top-3 theo báo cáo cá nhân | Top-1 sai chủ đề (0,615); cần lưu rank/score của chunk 180 ngày để kiểm chứng. |
| 5 | Chế tài người bán | Recursive + filter seller (Phạm Anh Minh) | Có, top-1 | Đúng mục chế tài, score 0,760; cao hơn FixedSize 0,7154. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata filter giúp rõ nhất ở câu 5: giới hạn ứng viên ở ba tài liệu dành cho `seller`, loại các chính sách cho người mua và đưa đúng mục chế tài lên top-1. Filter không thay thế similarity search; nếu các chunk trong miền seller vẫn quá giống nhau, embedding và ranh giới chunk vẫn quyết định thứ hạng cuối cùng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Recursive của Phạm Anh Minh đưa câu 1 và 5 lên đúng top-1; Sentence của Phạm Ngọc Quốc Khánh có score cao nhất ở câu 2 và báo cáo đúng top-1 ở câu 3.
- Sentence của Phạm Ngọc Quốc Khánh đưa câu 2 và 3 lên top-1, nhưng thất bại 3 query còn lại do heading/list Markdown không có dấu câu rõ ràng.
- Cùng FixedSize và cùng corpus, kết quả LocalEmbedder 3/10 so với MockEmbedder 0/10 cho thấy embedding model là biến kiểm soát bắt buộc khi so sánh chunker.
- Overlap giúp bảo toàn biên nhưng không ngăn được việc cắt ngang từ/câu; preview của FixedSize có một số chunk bắt đầu giữa từ.
- Metadata filter hữu ích cho câu hỏi theo vai trò, nhưng câu 3–4 cho thấy cùng chủ đề chưa chắc chứa đúng con số cần trả lời.

**Bài học rút ra khi so sánh trong nhóm:**
> Recursive hiện đạt điểm tổng cao nhất và bảo toàn cấu trúc tốt. Sentence trả tốt câu bảo hành/vận chuyển nhưng dính nhiều đoạn khi Markdown dùng heading và gạch đầu dòng thay vì dấu kết câu; FixedSize dễ kiểm soát nhưng có thể cắt ngang từ/câu. Các backend khác nhau (`MiniLM`, `nomic-embed-text`, mock) vẫn là yếu tố gây nhiễu, nên nhóm chưa thể quy toàn bộ chênh lệch cho chunking.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa heading/điều khoản trước khi chunk, loại các mảnh quá ngắn và bổ sung metadata `section` hoặc `clause_id` để truy vết chính xác. Đồng thời nhóm sẽ chạy tự động cả ba strategy trên cùng model/query, lưu top-3 ra JSON/CSV và chỉ tổng hợp số liệu đã tái lập được.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **35 / 40** |

Điểm tự đánh giá dùng kết quả thật của FixedSize, Recursive và Sentence. Kết quả MockEmbedder không được xem là phép so sánh chunker hợp lệ; nhóm vẫn cần chuẩn hóa cùng embedding/LLM, xác minh lại gold câu 3 và lưu đầy đủ top-3 câu 4 trước khi nộp chính thức.
