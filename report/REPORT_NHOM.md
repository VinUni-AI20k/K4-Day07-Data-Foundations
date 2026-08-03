# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4 — E-Commerce Policy Experts

**Thành viên:** Nguyễn Tấn Hoàng (trưởng nhóm), Nguyễn Minh Đức, Nguyễn Minh Hiếu, Trần Thanh Huyền, Đỗ Tú Anh

**Ngày:** 03/08/2026

> Báo cáo này tổng hợp yêu cầu Bài 3.0–3.5 trong `exercises.md` và kết quả benchmark của 5 thành viên trong thư mục `report/`. Khi output cá nhân dùng gold answer cũ hoặc mâu thuẫn với corpus, báo cáo nhóm ưu tiên nội dung kiểm chứng trực tiếp từ `data/k4_shopee/`.

---

## 1. Lựa chọn tài liệu (Document Set Quality)

### 1.1. Phạm vi

Nhóm xây dựng cơ sở tri thức về **chính sách thương mại điện tử và hỗ trợ khách hàng của Shopee Việt Nam**, tập trung vào trả hàng/hoàn tiền, vận chuyển và đồng kiểm, điều kiện người bán Shopee Mall, thanh toán, bảo vệ người mua và quy trình đóng gói hàng hoàn trả.

Corpus gồm đúng **10 tài liệu công khai**, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ. Mỗi tài liệu có YAML front matter để pipeline `build_knowledge_base()` gắn metadata lên từng chunk.

### 1.2. Danh sách tài liệu

Số ký tự dưới đây được đo trên toàn bộ file UTF-8 hiện có, bao gồm front matter.

| # | Tên tài liệu | Nguồn | Ngày lấy / phiên bản | Số ký tự | Metadata phân loại |
|---:|---|---|---|---:|---|
| 1 | Cách đóng gói đơn hàng hoàn trả | https://help.shopee.vn/portal/4/article/79508 | 2026-08-03 / `not-stated` | 4.009 | `buyer`, `returns-process`, `vi` |
| 2 | Chính sách trả hàng và hoàn tiền | https://help.shopee.vn/portal/4/article/77251?seo=1 | 2026-08-03 / `not-stated` | 20.096 | `both`, `returns-policy`, `vi` |
| 3 | Chính sách vận chuyển Shopee | https://help.shopee.vn/portal/4/article/77250 | 2026-08-03 / `not-stated` | 25.214 | `both`, `shipping-policy`, `vi` |
| 4 | Điều khoản dịch vụ Shopee Mall | https://help.shopee.vn/portal/4/article/77262 | 2026-08-03 / `not-stated` | 34.437 | `seller`, `seller-terms`, `vi` |
| 5 | Hướng dẫn gửi yêu cầu trả hàng/hoàn tiền | https://help.shopee.vn/portal/4/article/79233?seo=1 | 2026-08-03 / `not-stated` | 2.883 | `buyer`, `returns-process`, `vi` |
| 6 | Hướng dẫn thanh toán nhiều đơn hàng | https://help.shopee.vn/portal/4/article/79596 | 2026-08-03 / `not-stated` | 1.404 | `buyer`, `payments`, `vi` |
| 7 | Hướng dẫn phản hồi đề xuất hoàn tiền ngay | https://help.shopee.vn/portal/4/article/190387 | 2026-08-03 / `not-stated` | 1.877 | `buyer`, `returns-process`, `vi` |
| 8 | Quy định chung về trả hàng/hoàn tiền | https://help.shopee.vn/portal/4/article/188931 | 2026-08-03 / `not-stated` | 6.887 | `buyer`, `returns-policy`, `vi` |
| 9 | Quy trình Shopee xử lý yêu cầu trả hàng/hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 2026-08-03 / `not-stated` | 8.824 | `both`, `returns-process`, `vi` |
| 10 | Shopee Đảm Bảo là gì | https://help.shopee.vn/portal/4/article/79314 | 2026-08-03 / `not-stated` | 1.697 | `buyer`, `buyer-protection`, `vi` |

Danh mục nguồn đầy đủ, bao gồm đường dẫn dài và trường quyền sử dụng `public-page`, được lưu trong `data/k4_shopee/sources.csv`.

### 1.3. Cấu trúc metadata

| Trường | Kiểu | Bắt buộc | Ví dụ | Công dụng truy xuất |
|---|---|:---:|---|---|
| `doc_id` | string | Có | `dieu-khoan-dich-vu-shopee-mall` | Nhận diện tài liệu chuẩn và tính `DocHit@3`. |
| `title` | string | Có | `Điều khoản dịch vụ Shopee Mall` | Hiển thị và truy vết kết quả. |
| `source_url` | string | Có | URL trang trợ giúp Shopee | Kiểm chứng và trích dẫn nguồn. |
| `retrieved_at` | date string | Có | `2026-08-03` | Kiểm tra độ mới của dữ liệu. |
| `document_version` | string | Có | `not-stated` | Quản lý phiên bản; ghi rõ khi nguồn không công bố. |
| `customer_role` | enum | Có | `buyer`, `seller`, `both` | Pre-filter theo đối tượng áp dụng. |
| `category` | enum | Có | `seller-terms`, `returns-policy` | Thu hẹp không gian tìm kiếm theo chủ đề. |
| `language` | string | Có | `vi` | Chọn model và lọc ngôn ngữ. |
| `chunk_index` | integer | Khi ingest | `17` | Truy vết chính xác vị trí chunk trong tài liệu. |

### 1.4. Kiểm tra quản trị dữ liệu

- [x] Có 10 tài liệu, nằm trong giới hạn 5–10 tài liệu.
- [x] Tất cả là trang công khai và được ghi trong `sources.csv`.
- [x] Không có dữ liệu cá nhân, thông tin đăng nhập hoặc nội dung nội bộ.
- [x] Tất cả tài liệu có `source_url`, `retrieved_at`, `document_version` và ít nhất ba trường hữu ích cho retrieval (`customer_role`, `category`, `language`).

---

## 2. Thiết kế và so sánh chiến lược (Strategy Design)

### 2.1. Đường cơ sở trên ba tài liệu

Nhóm chạy `ChunkingStrategyComparator().compare(text, chunk_size=500)` trên phần thân tài liệu sau khi bỏ YAML front matter. Cấu hình gồm `FixedSizeChunker(size=500, overlap=50)`, `SentenceChunker(max_sentences_per_chunk=3)` và `RecursiveChunker(size=500)`.

| Tài liệu (độ dài thân bài) | Fixed-size | By-sentences | Recursive |
|---|---:|---:|---:|
| Quy định chung trả hàng/hoàn tiền (6.225 ký tự) | 14 chunk; TB 491,1 ký tự | 10 chunk; TB 617,6 ký tự | 14 chunk; TB 442,8 ký tự |
| Chính sách trả hàng và hoàn tiền (19.609 ký tự) | 44 chunk; TB 494,5 ký tự | 48 chunk; TB 405,6 ký tự | 62 chunk; TB 314,3 ký tự |
| Điều khoản dịch vụ Shopee Mall (33.732 ký tự) | 75 chunk; TB 499,1 ký tự | 57 chunk; TB 587,5 ký tự | 101 chunk; TB 332,1 ký tự |

Nhận xét:

- **Fixed-size** có số chunk dễ dự đoán và overlap giúp giữ một phần ngữ cảnh, nhưng có thể cắt giữa câu hoặc giữa điều khoản.
- **By-sentences** giữ nguyên câu, nhưng ba câu có thể thuộc các mục pháp lý khác nhau; một chunk cũng có thể vượt 500 ký tự vì chiến lược này giới hạn theo số câu.
- **Recursive** ưu tiên ranh giới đoạn, dòng, câu và từ nên tạo chunk mạch lạc hơn. Đổi lại, văn bản pháp lý nhiều dòng sinh nhiều chunk nhỏ và vẫn có thể tách tiêu đề khỏi nội dung.

### 2.2. Cấu hình benchmark của từng thành viên

| Thành viên | Cấu hình ghi nhận từ output | Backend embedding | Số chunk | Mức đầy đủ của bằng chứng |
|---|---|---|---:|---|
| Nguyễn Tấn Hoàng | `RecursiveChunker(chunk_size=400)` | Voyage AI `voyage-multilingual-2` | 371 | Có top-3, score và preview cho đủ 5 câu. |
| Nguyễn Minh Hiếu | `RecursiveChunker(chunk_size=400)` | Mock fallback | 375 | Có top-3, score, preview và agent answer cho đủ 5 câu. |
| Trần Thanh Huyền | `RecursiveChunker(chunk_size=400)` | Mock fallback | 371 | Có top-3, score và preview cho đủ 5 câu. |
| Đỗ Tú Anh | `RecursiveChunker(chunk_size=450)` | Mock fallback | 324 | Có top-3, score và preview cho đủ 5 câu. |
| Nguyễn Minh Đức | Không nêu cấu hình trong phần benchmark cá nhân | Không nêu | Không nêu | Chỉ có bảng tóm tắt 5/5; không có raw output để tái kiểm tra. |

**Giới hạn so sánh:** output hiện có chưa đáp ứng trọn vẹn khuyến nghị “mỗi thành viên thử một chiến lược khác nhau”: bốn output có cấu hình đều dùng Recursive, còn output Nguyễn Minh Đức không ghi cấu hình. Ngoài ra backend và phiên bản corpus/code không đồng nhất (371, 375 và 324 chunk), nên không thể quy toàn bộ chênh lệch chất lượng cho chunking.

### 2.3. Đánh giá thiết kế

Trong corpus hiện tại, Recursive là lựa chọn an toàn hơn Fixed-size vì tôn trọng các ranh giới tự nhiên. Tuy nhiên, cấu trúc tài liệu có nhiều mục đánh số như `1.9.4`, `2.7.1`, `2.7.2`; phương án phù hợp hơn cho vòng tiếp theo là **Section-aware Recursive Chunker**:

1. Tách trước theo heading Markdown và dòng mở đầu bằng số mục.
2. Chỉ dùng Recursive để chia tiếp khi một section vượt giới hạn.
3. Gắn lại tiêu đề section vào mọi mảnh con để không mất ngữ cảnh.
4. Bổ sung `section_title`, `clause_number` và `clause_type` vào metadata của chunk.

Chưa thể tuyên bố chiến lược này tốt nhất nếu chưa chạy cùng một embedder, corpus và bộ metric; đây là giả thuyết thiết kế rút ra từ failure analysis.

---

## 3. Câu hỏi đánh giá và chất lượng truy xuất (Retrieval Quality)

### 3.1. Bộ 5 câu hỏi và gold answer đã kiểm chứng

| # | Câu hỏi | Câu trả lời chuẩn (Gold Answer) | Chunk/tài liệu chứa bằng chứng |
|---:|---|---|---|
| 1 | Thời hạn gửi yêu cầu Trả hàng/Hoàn tiền trên Shopee là bao nhiêu ngày kể từ khi nhận hàng? | Thông thường là **15 ngày** kể từ khi đơn cập nhật “Giao hàng thành công”. Với người bán tự vận chuyển: 15 ngày từ khi người mua bấm “Đã nhận được hàng”, hoặc 20 ngày từ trạng thái “Lấy hàng thành công” nếu chưa bấm nhận. Thực phẩm tươi sống/đông lạnh có thời hạn 24 giờ, trừ lý do chưa nhận được hàng. | `quy-dinh-chung-tra-hang-hoan-tien`, đoạn “Thời gian để Shopee tiếp nhận yêu cầu…”. |
| 2 | *(Metadata filter: `customer_role="seller"`)* Người bán Shopee Mall có nghĩa vụ gì về hàng chính hãng và chế tài khi bán hàng giả? | Người bán cam kết sản phẩm là hàng chính hãng, chưa qua sử dụng và hợp pháp. Khi phát hiện hàng giả/nhái/không rõ xuất xứ hoặc phân phối bất hợp pháp, Shopee có thể thu **9.818.180 VNĐ hoặc 100% giá trị sản phẩm, tùy mức nào cao hơn**, cho mỗi sản phẩm; thanh toán trong 7 ngày lịch. Hai lần vi phạm có thể bị loại khỏi Shopee Mall. | `dieu-khoan-dich-vu-shopee-mall`, mục 2.7.1–2.7.2. |
| 3 | Shopee quy định thế nào về đồng kiểm khi nhận hàng từ đơn vị vận chuyển? | Theo tài liệu trong corpus, dịch vụ vận chuyển Shopee **không cho phép kiểm tra hàng trước khi thanh toán và nhận hàng**, trừ các đơn thuộc chương trình đồng kiểm. Chi tiết thao tác đồng kiểm nằm ở điều khoản riêng được trang nguồn dẫn tới nhưng chưa có trong corpus. | `chinh-sach-van-chuyen`, mục E.1. |
| 4 | Shopee Đảm Bảo bảo vệ Người mua thế nào và giữ tiền thanh toán trong bao lâu? | Corpus xác nhận quyền Trả hàng/Hoàn tiền trong **15 ngày**; đơn chưa giao đúng hạn được phản hồi trong 3–5 ngày làm việc. Tài liệu `shopee-dam-bao` **không nêu thời gian/cơ chế giữ tiền escrow**, vì vậy không được suy diễn thời hạn giữ tiền. | `shopee-dam-bao`, đoạn mở đầu và các trường hợp chưa nhận/nhận hàng lỗi. |
| 5 | Đóng gói đơn hàng hoàn trả cần đáp ứng yêu cầu gì? | Chuẩn bị hộp/bao bì, băng dính, vật liệu chèn và phiếu gửi; quay video toàn bộ quá trình; hoàn trả cả hộp nhà sản xuất, giấy tờ, phụ kiện, quà tặng nếu có; dùng hộp vận chuyển bên ngoài; dán/in mã vận đơn đúng hình thức. Hàng dễ vỡ/chất lỏng phải đóng chặt nắp và dùng vật liệu đệm. | `cach-dong-goi-don-hoan-tra`, phần “Các bước đóng gói hàng hoàn trả”. |

Các con số “7 ngày/15 ngày cho Shopee Mall”, “hoàn 200%” và mô tả escrow xuất hiện trong một số báo cáo cá nhân là phiên bản gold cũ, không khớp corpus ngày 03/08/2026 nên không được dùng để chấm bảng dưới đây.

### 3.2. Quy ước chấm

- **✓:** top-3 có chunk chứa bằng chứng đủ để trả lời phần cốt lõi.
- **△:** có chunk đúng chủ đề/tài liệu nhưng bằng chứng chỉ trả lời một phần.
- **✗:** không có chunk trả lời được câu hỏi.
- **BC:** chỉ là số liệu thành viên tự báo cáo, thiếu raw output để xác minh.

Đánh giá ưu tiên **chunk liên quan**, không tính đúng chỉ vì top-3 có cùng `doc_id` nhưng sai điều khoản.

### 3.3. Ma trận kết quả 5 thành viên

| Thành viên | Q1 | Q2 | Q3 | Q4 | Q5 | Hit@3 bằng chứng | Ghi chú |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| Nguyễn Tấn Hoàng | ✓ | ✓ | ✓ | △ | ✓ | **5/5 theo mức liên quan** | Voyage tìm đúng nguồn/chunk cho cả 5; Q4 chỉ được trả lời trong giới hạn corpus. Agent answer trong output bị rút gọn nên chưa chấm độ chính xác câu trả lời. |
| Nguyễn Minh Hiếu | ✗ | ✗ | ✗ | ✗ | ✓ | **1/5** | Q2 lọc đúng tài liệu seller nhưng sai mục 2.7; Q5 có bằng chứng về phiếu/mã vận đơn. |
| Trần Thanh Huyền | ✗ | ✗ | ✗ | ✗ | △ | **1/5 một phần** | Q5 top-1 đúng tài liệu và hướng dẫn dán/viết mã vận đơn, chưa bao quát toàn bộ yêu cầu đóng gói. |
| Đỗ Tú Anh | ✗ | ✗ | ✗ | ✗ | ✗ | **0/5** | Cờ “marker” ở Q1 là false positive vì từ “Shopee Mall” xuất hiện trong chunk không trả lời thời hạn. |
| Nguyễn Minh Đức | BC | BC | BC | BC | BC | **Tự báo cáo 5/5** | Thiếu raw output, backend, chunker và chunk count; gold answer trong bảng cá nhân cũng là bản cũ. Không đưa vào kết luận định lượng đã xác minh. |

Q4 được tính “liên quan” với Nguyễn Tấn Hoàng vì top-1 là bài `shopee-dam-bao` chứa thời hạn bảo vệ 15 ngày; không có hệ thống nào được xem là trả lời đúng phần “giữ tiền bao lâu” vì corpus không cung cấp dữ kiện đó.

### 3.4. Top-3 của cấu hình có bằng chứng tốt nhất

Kết quả Nguyễn Tấn Hoàng — `RecursiveChunker(400)` + `voyage-multilingual-2`:

| Câu | Hạng 1 | Hạng 2 | Hạng 3 | Nhận xét |
|---:|---|---|---|---|
| Q1 | `quy-dinh-chung...` (0,753) | `quy-dinh-chung...` (0,722) | `shopee-dam-bao` (0,698) | Hạng 2 chứa trực tiếp mốc 15 ngày; cả hai nguồn đều hữu ích. |
| Q2 | `dieu-khoan...mall` (0,727) | `dieu-khoan...mall` (0,657) | `dieu-khoan...mall` (0,652) | Filter seller và semantic embedding đưa đúng mục hàng giả lên top-1. |
| Q3 | `chinh-sach-van-chuyen` (0,654) | `chinh-sach-van-chuyen` (0,611) | `quy-dinh-chung...` (0,606) | Top-1 chứa nguyên tắc “không cho phép… trừ đơn đồng kiểm”. |
| Q4 | `shopee-dam-bao` (0,670) | `chinh-sach-tra-hang...` (0,654) | `chinh-sach-tra-hang...` (0,603) | Đúng nguồn bảo vệ người mua, nhưng không thể bổ sung thông tin escrow không có trong nguồn. |
| Q5 | `cach-dong-goi...` (0,712) | `cach-dong-goi...` (0,701) | `chinh-sach-tra-hang...` (0,701) | Hai hạng đầu chứa hướng dẫn và vật liệu đóng gói. |

### 3.5. Kết quả top-1 của các output Mock có raw log

| Câu | Nguyễn Minh Hiếu — Recursive 400 | Trần Thanh Huyền — Recursive 400 | Đỗ Tú Anh — Recursive 450 |
|---:|---|---|---|
| Q1 | `chinh-sach-van-chuyen` (0,334) — sai | `chinh-sach-van-chuyen` (0,334) — sai | `chinh-sach-van-chuyen` (0,422) — sai |
| Q2, sau filter | `dieu-khoan...mall` (0,311) — đúng doc, sai mục | `dieu-khoan...mall` (0,330) — đúng doc, sai mục | `dieu-khoan...mall` (0,311) — đúng doc, sai mục |
| Q3 | `chinh-sach-tra-hang...` (0,307) — sai | `chinh-sach-tra-hang...` (0,307) — sai | `chinh-sach-van-chuyen` (0,341) — đúng doc, sai đoạn |
| Q4 | `chinh-sach-tra-hang...` (0,322) — sai | `dieu-khoan...mall` (0,314) — sai | `chinh-sach-van-chuyen` (0,313) — sai |
| Q5 | `cach-dong-goi...` (0,341) — liên quan | `cach-dong-goi...` (0,341) — liên quan một phần | `chinh-sach-tra-hang...` (0,314) — sai |

### 3.6. Chiến lược nào tốt nhất và metadata có giúp không?

Trong các **output có thể kiểm chứng**, cấu hình Nguyễn Tấn Hoàng đạt chất lượng tốt nhất. Tuy nhiên, kết quả này cho thấy lợi thế rõ nhất của **semantic embedding thật so với Mock**, chưa chứng minh Recursive 400 tốt hơn mọi chiến lược chunking khác, vì các biến chưa được giữ cố định.

Metadata filtering có ích rõ ở Q2:

- Không filter, các output Mock thường đưa tài liệu vận chuyển hoặc trả hàng lên cao vì cùng chứa từ “Người bán”, “hàng giả” hoặc “phí”.
- Với `customer_role="seller"`, top-3 được giới hạn vào `dieu-khoan-dich-vu-shopee-mall`.
- Filter đúng tài liệu vẫn chưa bảo đảm đúng **điều khoản**: ba output Mock đều bỏ lỡ mục 2.7. Điều này cho thấy cần kết hợp semantic embedding và metadata chi tiết như `clause_number=2.7` hoặc `clause_type=che_tai`.

### 3.7. Trường hợp chiến lược tốt ở câu này nhưng kém ở câu khác

- Recursive 400 + Mock của Nguyễn Minh Hiếu/Huyền lấy được Q5 vì từ khóa “đóng gói”, “phiếu gửi”, “mã vận đơn” xuất hiện trực tiếp, nhưng thất bại Q1 và Q4 khi nhiều tài liệu dùng chung từ khóa trả hàng/hoàn tiền.
- Recursive 450 + Mock của Đỗ Tú Anh cho score Q1 cao hơn các output Mock 400 (0,422 so với 0,334) nhưng vẫn sai bằng chứng; score giữa các lần chạy/backend không phải thước đo có thể so sánh trực tiếp.
- Voyage xử lý tốt câu diễn đạt ngữ nghĩa (Q1–Q5), nhưng Q4 vẫn bộc lộ giới hạn grounding: retrieval không thể tìm một sự thật không có trong corpus.

---

## 4. Failure Analysis, demo và bài học nhóm

### 4.1. Failure case 1 — Mock embedding không hiểu ngữ nghĩa

**Câu thất bại:** Q1 và Q4 ở toàn bộ output Mock có raw log.

**Biểu hiện:** Q1 trả về đoạn “cung cấp bằng chứng trong 24 giờ” của chính sách vận chuyển; Q4 trả về điều khoản phí hoặc khiếu nại, dù score cosine tương đối cao.

**Nguyên nhân:** Mock embedder chủ yếu phục vụ unit test, không biểu diễn tốt ngữ nghĩa tiếng Việt. Corpus cũng có nhiều tài liệu lặp từ “Trả hàng/Hoàn tiền”, làm độ chính xác thấp.

**Cải thiện:** Dùng cùng một model semantic đa ngữ cho tất cả thành viên; cố định corpus và seed/cấu hình trước khi so sánh chunker.

### 4.2. Failure case 2 — Đúng tài liệu nhưng sai chunk

**Câu thất bại:** Q2 với filter seller trong ba output Mock.

**Biểu hiện:** top-3 đều thuộc đúng `dieu-khoan-dich-vu-shopee-mall`, nhưng top-1 nói về phí 2.12 hoặc hủy đơn thay vì hàng chính hãng 2.7.

**Nguyên nhân:** `customer_role` chỉ lọc ở cấp tài liệu; tài liệu Mall dài 33.732 ký tự và chứa nhiều loại nghĩa vụ/phí. Chunk không mang số mục và loại điều khoản trong metadata.

**Cải thiện:** Chunk theo section, giữ tiêu đề mục trong nội dung, gắn `clause_number`, `section_title`, `clause_type`, rồi áp dụng hybrid filter + vector search.

### 4.3. Failure case 3 — Câu hỏi yêu cầu thông tin ngoài corpus

**Câu thất bại:** phần “giữ tiền thanh toán trong bao lâu” của Q4.

**Biểu hiện:** một số gold/agent answer cũ tự suy diễn rằng Shopee giữ tiền 7–15 ngày hoặc tới khi người mua xác nhận.

**Nguyên nhân:** tài liệu `shopee-dam-bao.md` chỉ nói về quyền trả hàng/hoàn tiền trong 15 ngày và thời gian phản hồi 3–5 ngày; không mô tả thời gian escrow. Đây là lỗi **grounding quality/evaluation design**, không chỉ là lỗi retrieval.

**Cải thiện:** hoặc đổi câu hỏi thành “Shopee Đảm Bảo cho phép trả hàng/hoàn tiền trong bao lâu?”, hoặc bổ sung một nguồn công khai có mô tả cơ chế thanh toán trước khi giữ nguyên câu hỏi.

### 4.4. Failure case 4 — Gold answer và phiên bản benchmark không đồng nhất

Một số báo cáo cá nhân dùng “7 ngày/15 ngày với Shopee Mall”, “hoàn 200%” và expected doc của Q3 là `quy-dinh-chung-tra-hang-hoan-tien`; các dữ kiện này không khớp corpus hiện tại. Điều này làm metric sai ngay cả khi retrieval tốt. Nhóm đã sửa gold answer ở mục 3.1 và khuyến nghị lưu bộ câu hỏi trong một file dùng chung thay vì sao chép vào từng script.

### 4.5. Bài học rút ra

1. Chỉ so sánh chunking khi **giữ cố định** corpus, embedding model, query, filter và tiêu chí relevance.
2. `DocHit@3` không đủ; cần kiểm tra chunk có thực sự chứa bằng chứng và agent answer có bám nguồn hay không.
3. Metadata filter giảm nhiễu giữa buyer/seller nhưng cần metadata cấp section để chọn đúng điều khoản trong tài liệu dài.
4. Semantic embedding ảnh hưởng lớn hơn việc đổi 400 thành 450 ký tự trong bộ kết quả hiện có.
5. Không được để agent “điền vào chỗ trống” khi corpus thiếu thông tin; câu trả lời đúng phải nói rõ giới hạn nguồn.

### 4.6. Nội dung demo đề xuất

1. Giới thiệu corpus 10 tài liệu và schema metadata.
2. Cho xem Q2 trước/sau `customer_role="seller"` để minh họa metadata filtering.
3. So sánh cùng `RecursiveChunker(400)` giữa Mock và Voyage trên Q1/Q4/Q5.
4. Trình bày failure “đúng doc, sai điều khoản” và thiết kế Section-aware Recursive.
5. Kết thúc bằng Q4 để minh họa nguyên tắc grounding: retrieval tốt không thể thay thế dữ liệu nguồn bị thiếu.

### 4.7. Nếu làm lại

- Đóng băng một bản corpus và tạo checksum trước khi benchmark.
- Dùng chung một script, một semantic embedder và một file gold answer đã được kiểm chứng.
- Phân công đủ năm cấu hình khác nhau: Fixed-size, Sentence, Recursive, Section-aware Recursive và một cấu hình hybrid metadata + semantic search.
- Báo cáo đồng thời `Hit@3`, `MRR`, độ chính xác agent answer và failure theo từng câu.
- Bổ sung tài liệu điều khoản chương trình đồng kiểm và nguồn mô tả escrow nếu muốn giữ nguyên Q3/Q4 hiện tại.

---

## 5. Mức độ hoàn thành yêu cầu nhóm

| Yêu cầu trong `exercises.md` | Trạng thái | Bằng chứng trong báo cáo |
|---|:---:|---|
| 5–10 tài liệu công khai, nguồn và phiên bản rõ ràng | Đạt | Mục 1.2–1.4 |
| Metadata bắt buộc + ít nhất hai trường retrieval | Đạt | Mục 1.3 |
| Baseline trên 2–3 tài liệu | Đạt | Mục 2.1 (3 tài liệu) |
| Mỗi thành viên có chiến lược riêng | Chưa đủ bằng chứng | Bốn raw output đều dùng Recursive; một output không ghi cấu hình. |
| Đúng 5 câu hỏi, đa dạng và có gold answer | Đạt sau hiệu chỉnh | Mục 3.1 |
| Ít nhất một câu cần metadata filter | Đạt | Q2 |
| So sánh top-3 của 5 thành viên | Đạt có điều kiện | Mục 3.3–3.5; Nguyễn Minh Đức thiếu raw output. |
| Thảo luận chiến lược tốt nhất và tác dụng metadata | Đạt | Mục 3.6–3.7 |
| Ít nhất một failure case và đề xuất cải thiện | Đạt | Mục 4.1–4.4 |
| Bài học và nội dung demo | Đạt | Mục 4.5–4.7 |

**Việc cần hoàn thiện trước khi nộp nếu còn thời gian:** Nguyễn Minh Đức bổ sung raw benchmark và cấu hình; các thành viên chạy lại năm chiến lược khác nhau trên cùng semantic embedder/corpus. Báo cáo hiện tại không tự tạo số liệu để che hai khoảng trống này.
