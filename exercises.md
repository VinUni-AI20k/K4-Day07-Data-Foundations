# Ngày 7 — Bài tập
## Nền tảng Dữ liệu: Embedding & Vector Store | Bài tập thực hành

---

## Phần 1 — Khởi động (Cá nhân)

### Bài tập 1.1 — Cosine Similarity (Độ tương tự Cosine) bằng ngôn ngữ đời thường

Không yêu cầu toán học — hãy giải thích về mặt khái niệm:

- Điều gì xảy ra khi hai đoạn văn bản có độ tương tự cosine cao?
- Đưa ra một ví dụ cụ thể về hai câu sẽ có độ tương tự CAO và hai câu sẽ có độ tương tự THẤP.
- Tại sao độ tương tự cosine lại được ưu tiên hơn khoảng cách Euclid (Euclidean distance) đối với text embeddings?

> **Ghi kết quả vào:** REPORT_CANHAN.md — Phần 1 (Khởi động)

---

### Bài tập 1.2 — Bài toán tính toán Chunking

- Một tài liệu có độ dài 10,000 ký tự. Bạn tiến hành chia nhỏ (chunk) với `chunk_size=500` (kích thước chunk), `overlap=50` (độ chồng chéo). Bạn dự kiến sẽ có bao nhiêu chunks?
- Công thức: `số lượng chunk = làm_tròn_lên((độ_dài_tài_liệu - độ_chồng_chéo) / (kích_thước_chunk - độ_chồng_chéo))`
- Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk sẽ thay đổi như thế nào? Tại sao bạn lại muốn tăng độ chồng chéo?

> **Ghi kết quả vào:** REPORT_CANHAN.md — Phần 1 (Khởi động)

---

## Phần 2 — Lập trình cốt lõi (Cá nhân)

Hoàn thành tất cả các TODOs trong `src/chunking.py`, `src/store.py`, và `src/agent.py`. `Document` dataclass và `FixedSizeChunker` đã được triển khai sẵn làm ví dụ — hãy đọc kỹ để hiểu cấu trúc trước khi lập trình phần còn lại.

Chạy `pytest tests/` để kiểm tra tiến độ.

### Danh sách cần làm (Checklist)
- [x] `Document` dataclass — ĐÃ TRIỂN KHAI SẴN
- [x] `FixedSizeChunker` — ĐÃ TRIỂN KHAI SẴN
- [x] `SentenceChunker` — tách dựa trên ranh giới câu, nhóm lại thành các chunks
- [x] `RecursiveChunker` — thử nghiệm các dấu phân cách (separators) theo thứ tự, thực hiện đệ quy trên các đoạn có kích thước quá lớn
- [x] `compute_similarity` — công thức tính độ tương tự cosine kèm cơ chế bảo vệ chia cho 0
- [x] `ChunkingStrategyComparator` — gọi cả ba chiến lược, tính toán các chỉ số thống kê
- [x] `EmbeddingStore.__init__` — khởi tạo store (lưu trữ trong bộ nhớ hoặc ChromaDB)
- [x] `EmbeddingStore.add_documents` — nhúng (embed) và lưu trữ từng tài liệu
- [x] `EmbeddingStore.search` — nhúng truy vấn, xếp hạng theo tích vô hướng (dot product)
- [x] `EmbeddingStore.get_collection_size` — trả về số lượng
- [x] `EmbeddingStore.search_with_filter` — lọc theo siêu dữ liệu (metadata), sau đó tìm kiếm
- [x] `EmbeddingStore.delete_document` — xóa tất cả các chunks của một doc_id
- [x] `KnowledgeBaseAgent.answer` — truy xuất (retrieve) + tạo prompt + gọi LLM

> **Nộp code:** thư mục `src/`
> **Ghi lại hướng tiếp cận vào:** REPORT_CANHAN.md — Phần 2 (Hướng tiếp cận của tôi)

---

## Phần 3 — So Sánh Chiến Lược Truy Xuất (Nhóm)

### Bài tập 3.0 — Chuẩn Bị Tài Liệu (Giờ đầu tiên)

Chủ đề Giai đoạn 2 **cố định theo lớp K4**: chính sách TMĐT / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán). Nhóm chuẩn bị bộ tài liệu trong phạm vi này:

> Đọc trước [Hướng dẫn crawl và format dữ liệu](docs/DATA_COLLECTION.md). Tài liệu này quy định nguồn được dùng, quy trình crawl an toàn, cấu trúc thư mục, metadata và `sources.csv`.
>
> **Nạp dữ liệu (đã cung cấp sẵn):** dùng `build_knowledge_base(data_dir, embedding_fn, chunker=...)` trong `ingest.py` — nó parse YAML front matter → chia chunk bằng chunker bạn chọn → gắn `doc_id` + metadata lên **từng** chunk → nạp vào `EmbeddingStore`. Bạn không phải tự viết lại pipeline này; chỉ cần tạo file `.md` đúng định dạng và chọn chunker.

**Bước 1 — Khoanh phạm vi cụ thể trong chủ đề cố định của lớp K4** (chính sách TMĐT / hỗ trợ khách hàng): ví dụ chính sách đổi trả, điều kiện người bán, quy định thanh toán, chính sách giao hàng, quyền riêng tư.

**Bước 2 — Thu thập 5-10 tài liệu.** Chỉ dùng nguồn công khai hoặc nguồn nhóm có quyền sử dụng; lưu dưới dạng `.txt` hoặc `.md` vào thư mục `data/`.

**Quy tắc dữ liệu bắt buộc:**
- Không đưa dữ liệu cá nhân, thông tin đăng nhập, hồ sơ nội bộ hoặc nội dung có quyền sử dụng không rõ ràng vào repo.
- Với mỗi tài liệu, ghi `source_url`, `retrieved_at` (ngày lấy) và `document_version` hoặc ngày hiệu lực nếu nguồn có nêu.
- Đưa ba trường trên vào siêu dữ liệu (metadata) khi nạp (ingest); chúng giúp kiểm tra độ mới và truy vết câu trả lời.

> **Mẹo chuyển PDF sang Markdown:**
> - `pip install marker-pdf` → `marker_single input.pdf output/` (chất lượng cao, giữ cấu trúc)
> - `pip install pymupdf4llm` → `pymupdf4llm.to_markdown("input.pdf")` (nhanh, đơn giản)
> - Hoặc sao chép-dán (copy-paste) nội dung từ PDF/web vào file `.txt`

Ghi vào bảng:

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | [Shopee](https://help.shopee.vn/portal/4/article/77251?seo=1) | 2026-08-03 / not-stated | 26,198 | both, returns, vi |
| 2 | Quy định về đăng bán sản phẩm | [Shopee](https://help.shopee.vn/portal/4/article/77246) | 2026-08-03 / not-stated | 28,830 | seller, listing, vi |
| 3 | Điều khoản dịch vụ | [Shopee](https://help.shopee.vn/portal/4/article/77243) | 2026-08-03 / not-stated | 110,814 | both, payment-and-escrow, vi |
| 4 | Shopee Đảm Bảo | [Shopee](https://help.shopee.vn/portal/4/article/79314-%5BMua-s%E1%BA%AFm-an-to%C3%A0n%5D-Shopee-%C4%90%E1%BA%A3m-B%E1%BA%A3o-l%C3%A0-g%C3%AC) | 2026-08-03 / not-stated | 2,146 | buyer, buyer-protection, vi |
| 5 | Phương thức gửi hàng hoàn trả và phí hoàn trả | [Shopee](https://help.shopee.vn/portal/4/article/189477-%5BTr%E1%BA%A3-h%C3%A0ng/-Ho%C3%A0n-ti%E1%BB%81n%5D-C%C3%A1c-ph%C6%B0%C6%A1ng-th%E1%BB%A9c-g%E1%BB%ADi-h%C3%A0ng-ho%C3%A0n-tr%E1%BA%A3-v%C3%A0-ph%C3%AD-ho%C3%A0n-tr%E1%BA%A3) | 2026-08-03 / not-stated | 8,439 | buyer, return-shipping, vi |
| 6 | Điều khoản dịch vụ Shopee Mall | [Shopee](https://help.shopee.vn/portal/4/article/77262) | 2026-08-03 / not-stated | 44,464 | seller, mall-returns, vi |

Corpus nằm trong `data/shopee_policy/`; URL gốc và căn cứ sử dụng từng nguồn
được ghi trong `data/shopee_policy/sources.csv`.

**Bước 3 — Thiết kế cấu trúc metadata (metadata schema):** Mỗi tài liệu cần `source_url`, `retrieved_at`, `document_version` và ít nhất 2 trường hữu ích cho việc truy xuất (ví dụ: `category`, `customer_role`, `language`, `difficulty`).

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 1 (Lựa chọn tài liệu)

---

### Bài tập 3.1 — Thiết Kế Chiến Lược Truy Xuất (Mỗi người thử riêng)

Mỗi thành viên **tự chọn chiến lược riêng** để thử nghiệm trên cùng bộ tài liệu của nhóm.

**Bước 1 — Đường cơ sở (Baseline):** Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu. Ghi lại kết quả.

**Kết quả baseline trên toàn bộ 6 tài liệu:** FixedSize (750 ký tự, overlap
100) tạo 257 chunks, trung bình 741.8 ký tự; Sentence (5 câu/chunk) tạo 218
chunks, trung bình 755.0 ký tự; Recursive (750 ký tự) tạo 305 chunks, trung
bình 540.8 ký tự.

> **Dùng embedder thật để so sánh có ý nghĩa:** đặt `EMBEDDING_PROVIDER=local` (xem README, mục *Tùy Chọn Mô Hình Nhúng*). Trình nhúng giả lập (mock) chỉ dùng cho unit test và cho điểm gần như ngẫu nhiên — **không** phản ánh chất lượng ngữ nghĩa tiếng Việt nên đừng dùng mock để kết luận chiến lược nào tốt hơn.

**Bước 2 — Chọn hoặc thiết kế chiến lược của bạn:**
- Dùng 1 trong 3 chiến lược có sẵn (built-in strategies) với tham số tối ưu, HOẶC
- Thiết kế chiến lược tùy chỉnh cho chủ đề của bạn (ví dụ: chia nhỏ theo cặp Câu hỏi-Đáp án, theo các phần (sections), theo tiêu đề (headers))
- Mỗi thành viên nên thử một chiến lược **khác nhau** để có cơ sở so sánh

```python
class CustomChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho [chủ đề của bạn].

    Lý do thiết kế: [giải thích tại sao chiến lược này phù hợp với dữ liệu của bạn]
    """

    def chunk(self, text: str) -> list[str]:
        # Viết mã nguồn của bạn ở đây
        ...
```

**Bước 3 — So sánh:** So sánh chiến lược tùy chỉnh/được tinh chỉnh (custom/tuned strategy) với đường cơ sở (baseline) trên cùng tài liệu.

**Kết quả lựa chọn:** dùng `SentenceChunker(max_sentences_per_chunk=5)` làm
chiến lược cá nhân. Khi dùng `text-embedding-3-small`, chiến lược này có đủ
evidence cho 4/5 gold answer trong top-3; tốt hơn FixedSize và Recursive (mỗi
chiến lược 3/5 theo cùng phép đo evidence).

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 2 (Thiết kế chiến lược)

---

### Bài tập 3.2 — Chuẩn Bị Câu Hỏi Đánh Giá (Benchmark Queries)

Mỗi nhóm viết **đúng 5 câu hỏi đánh giá** kèm theo **câu trả lời chuẩn (gold answers)**.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Hạn trả hàng sau khi giao thành công và ngoại lệ thực phẩm? | 15 ngày; thực phẩm tươi sống/đông lạnh: 24 giờ | `shopee-return-refund-policy`, mục 3.2 |
| 2 | Người bán phải phản hồi yêu cầu hoàn tiền trong bao lâu? | 2 ngày lịch từ khi nhận thông báo | `shopee-return-refund-policy`, mục 5 |
| 3 | Tự gửi hàng hoàn ngoài Shopee Mall được hỗ trợ bao nhiêu? | 25.000 Xu cùng tỉnh; 40.000 Xu khác tỉnh | `shopee-return-shipping`, mục 2.2; filter buyer |
| 4 | Ảnh thật khi đăng bán phải đạt yêu cầu nào? | Ảnh tự chụp, sản phẩm chiếm ít nhất 40% ảnh | `shopee-listing-regulations`, mục C.1.b; filter seller |
| 5 | Tiền thanh toán được giữ ở đâu và khi nào hoàn tiền? | Tài Khoản Đảm Bảo; hoàn khi yêu cầu được chấp thuận | `shopee-terms-of-service`, mục 11.1–11.2 |

**Yêu cầu:**
- Câu hỏi phải đa dạng (không hỏi 5 câu có nội dung/cấu trúc giống hệt nhau)
- Câu trả lời chuẩn phải cụ thể và có thể kiểm chứng (verify) từ tài liệu
- Ít nhất 1 câu hỏi yêu cầu lọc bằng metadata (metadata filtering) để trả lời tốt

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 3 (Câu hỏi đánh giá & Chất lượng truy xuất)

---

### Bài tập 3.3 — Dự Đoán Độ Tương Tự Cosine (Cá nhân)

Gọi hàm `compute_similarity()` trên 5 cặp câu. **Trước khi chạy**, hãy dự đoán xem cặp câu nào sẽ có độ tương tự cao nhất/thấp nhất. Ghi lại các dự đoán của bạn và kết quả thực tế. Suy ngẫm xem điều gì khiến bạn ngạc nhiên nhất.

> **Ghi kết quả vào:** REPORT_CANHAN.md — Phần 4 (Dự đoán độ tương tự)

---

### Bài tập 3.4 — Chạy Đánh Giá & So Sánh Trong Nhóm

**Bước 1:** Mỗi thành viên chạy 5 câu hỏi đánh giá với chiến lược riêng. Ghi lại kết quả top-3 cho mỗi câu hỏi.

**Bước 2:** So sánh kết quả trong nhóm:
- Chiến lược nào cho việc truy xuất tốt nhất? Tại sao?
- Có câu hỏi nào mà chiến lược A tốt hơn B nhưng lại ngược lại ở câu hỏi khác không?
- Lọc bằng metadata (Metadata filtering) có giúp ích không?

**Bước 3:** Thảo luận và rút ra bài học — chuẩn bị cho phần demo (thuyết trình) với các nhóm khác.

**Kết quả đánh giá:** SentenceChunker trả lời grounded đúng Q1, Q2, Q4 và Q5.
Q3 là failure case: document đúng có trong top-3 nhưng thiếu đồng thời hai mức
25.000/40.000 Xu, nên không đủ gold answer. Metadata filter hữu ích rõ ở Q4
(`seller`); ở Q3, filter `buyer` giảm nhiễu nhưng không thay thế được chunking
giữ nguyên một mục phí hoàn trả.

> **Ghi kết quả vào:** REPORT_CANHAN.md — Phần 5 (Kết quả truy xuất của tôi) + REPORT_NHOM.md — Phần 3 (Chất lượng truy xuất của nhóm)
> **Gợi ý đánh giá:** xem danh sách kiểm tra ngắn trong `README.md` mục **Cách Tự Đánh Giá Kết Quả Retrieval** hoặc chi tiết hơn trong file `docs/EVALUATION.md`.

---

### Bài tập 3.5 — Phân Tích Lỗi (Failure Analysis)

Tìm ít nhất **1 trường hợp lỗi (failure case)** trong quá trình so sánh. Mô tả:
- Câu hỏi nào mà quá trình truy xuất gặp thất bại?
- Tại sao? (do chunk quá nhỏ/quá lớn, thiếu metadata, câu hỏi mơ hồ, v.v.)
- Đề xuất cải thiện?

> **Ghi kết quả vào:** REPORT_NHOM.md — Phần 4 (Demo & Bài học nhóm)
> **Gợi ý:** phân tích lỗi nên tham chiếu từ các góc nhìn như độ chính xác (precision), tính mạch lạc của chunk (chunk coherence), tính hữu dụng của metadata, và chất lượng thông tin nền (grounding quality).

**Phân tích lỗi đã thực hiện:** Q3 thất bại vì `SentenceChunker(5)` tách các
câu chứa hai mức phí khỏi nhau trong ranking. Cải thiện đề xuất là chunk theo
heading/bảng hoặc gom toàn bộ section “phí trả hàng” vào cùng một chunk; không
chỉ tăng số câu một cách mù quáng.

---

## Danh Sách Kiểm Tra Nộp Bài (Submission Checklist)

- [x] Vượt qua tất cả các bài kiểm thử (tests): `pytest tests/ -v` — 42 / 42 pass
- [x] Cập nhật thư mục `src/` (cá nhân)
- [x] Hoàn thành báo cáo nhóm (`report/REPORT_NHOM.md` — 1 file/nhóm)
- [x] Hoàn thành báo cáo cá nhân (`report/REPORT_CANHAN.md` — 1 file/sinh viên)
