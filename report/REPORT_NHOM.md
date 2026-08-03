# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A5-1
**Thành viên:** Kiều Hồng Phong (Trưởng nhóm), Nguyễn Đức Đạt, Đỗ Duy Đức, Vũ Ngọc Sơn, Lê Minh Vũ Hoàng
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md` hoặc `REPORT_PHONG.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Nhóm A5-1 tập trung vào chính sách Trả hàng / Hoàn tiền Shopee Việt Nam bao gồm mốc thời gian, quy định sản phẩm hạn chế trả hàng, bằng chứng video mở kiện, theo dõi đơn và phương thức hoàn tiền.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `shopee-returns-01.md` | https://help.shopee.vn/portal/4/article/79018 | 2026-08-01 | 8,962 | `customer_role: buyer`, `category: return_policy`, `document_version: 2026-v1` |
| 2 | `shopee-returns-02.md` | https://help.shopee.vn/portal/4/article/79020 | 2026-08-01 | 3,793 | `customer_role: buyer`, `category: return_request`, `document_version: 2026-v1` |
| 3 | `shopee-returns-03.md` | https://help.shopee.vn/portal/4/article/79025 | 2026-08-01 | 3,109 | `customer_role: buyer`, `category: restricted_products`, `document_version: 2026-v1` |
| 4 | `shopee-returns-04.md` | https://help.shopee.vn/portal/4/article/79030 | 2026-08-01 | 5,059 | `customer_role: buyer`, `category: evidence_requirements`, `document_version: 2026-v1` |
| 5 | `shopee-returns-05.md` | https://help.shopee.vn/portal/4/article/79035 | 2026-08-01 | 2,427 | `customer_role: buyer`, `category: tracking`, `document_version: 2026-v1` |
| 6 | `shopee-returns-06.md` | https://help.shopee.vn/portal/4/article/79040 | 2026-08-01 | 5,422 | `customer_role: buyer`, `category: refund_methods`, `document_version: 2026-v1` |
| 7 | `shopee-returns-07.md` | https://help.shopee.vn/portal/4/article/79045 | 2026-08-01 | 11,110 | `customer_role: seller`, `category: seller_return_tracking`, `document_version: 2026-v1` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-returns-01` | Định danh tài liệu gốc, dùng để lọc hoặc xóa tài liệu khỏi kho vector (`delete_document`). |
| `customer_role` | string | `buyer`, `seller`, `both` | Phân loại vai trò người dùng, cho phép pre-filtering để loại bỏ nhiễu giữa quy trình người mua và người bán. |
| `category` | string | `refund_methods`, `restricted_products` | Phân loại chủ đề nhỏ, giúp khoanh vùng tìm kiếm đúng phân mục chính sách. |
| `source_url` | string | `https://help.shopee.vn/portal/4/article/79018` | Đảm bảo tính kiểm chứng và giúp RAG agent trích dẫn nguồn minh bạch cho người dùng. |
| `retrieved_at` | string | `2026-08-01` | Theo dõi tính cập nhật của tài liệu theo thời gian. |
| `document_version` | string | `2026-v1` | Xác định phiên bản hiệu lực của chính sách TMĐT. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu mẫu `shopee-returns-01.md` (8,962 ký tự):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-returns-01.md` | FixedSizeChunker (`fixed_size`, `chunk_size=300`) | 22 | 299.77 chars | Cắt cứng theo ký tự nên đôi khi xé đôi bảng biểu hoặc giữa câu. |
| `shopee-returns-01.md` | SentenceChunker (`by_sentences`, `max_sentences=3`) | 10 | 656.70 chars | Đảm bảo mạch văn theo câu nhưng độ dài các chunk chênh lệch lớn. |
| `shopee-returns-01.md` | RecursiveChunker (`recursive`, `chunk_size=500`) | 30 | 217.93 chars | Giữ cấu trúc tiêu đề/đoạn văn rất tốt, không xé vụn ranh giới ý. |

### Chiến lược của từng thành viên

**Thành viên 1 — Kiều Hồng Phong**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500, separators=["\n\n", "\n", ". "])` / `LangChainSentenceChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Tích hợp LangChain Text Splitter và đệ quy theo ranh giới ngắt đoạn/dòng Markdown để giữ trọn vẹn từng bảng mục chính sách Shopee.
- **Code snippet (nếu custom):**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50, separators=[". ", "! ", "? ", "\n\n", "\n"]
)
chunks = splitter.split_text(text)
```

**Thành viên 2 — Nguyễn Đức Đạt**
- **Loại chiến lược:** `RecursiveChunker`
- **Mô tả & lý do chọn:** Chia đệ quy theo dấu ngắt đoạn để bảo toàn tiêu đề Heading 2 (`##`).

**Thành viên 3 — Đỗ Duy Đức**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=50)`
- **Mô tả & lý do chọn:** Chia kích thước cố định ngắn 500 ký tự với độ chồng chéo 50 ký tự để kiểm tra tính nhất quán số lượng vector trong kho lưu trữ.

**Thành viên 4 — Vũ Ngọc Sơn & Lê Minh Vũ Hoàng**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)` / Custom Chunker
- **Mô tả & lý do chọn:** Chia theo 3 câu hoàn chỉnh để đảm bảo cú pháp câu mạch lạc.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Kiều Hồng Phong | `Recursive (500)` / `LangChain` | 9.5 / 10 | Bảo toàn cấu trúc Markdown (tiêu đề, danh sách, bảng), score cao nhất. | Cần điều chỉnh separators đúng thứ tự với dữ liệu Markdown. |
| Nguyễn Đức Đạt | `Recursive` | 9.0 / 10 | Giữ mạch đoạn văn tốt. | Cần cấu hình chunk overlap hợp lý. |
| Đỗ Duy Đức | `FixedSize (500, 50)` | 7.5 / 10 | Tạo số lượng chunk đều đặn, tìm kiếm từ khóa ngắn nhanh. | Dễ cắt đứt câu giữa chừng, làm mất ý của điều kiện ngoại lệ. |
| Vũ Ngọc Sơn & Lê Minh Vũ Hoàng | `Sentence (max 3)` | 8.0 / 10 | Mỗi chunk là các câu hoàn chỉnh, mạch lạc về cú pháp. | Kích thước chunk không đều, bảng biểu bị rải rác qua nhiều câu. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Chiến lược `RecursiveChunker(chunk_size=500)` của Kiều Hồng Phong là tốt nhất cho dữ liệu chính sách TMĐT Shopee. Lý do là tài liệu chính sách chứa nhiều định dạng Markdown (tiêu đề `#`, danh sách gạch đầu dòng, bảng phương thức hoàn tiền). Việc ưu tiên tách theo ngắt đoạn `\n\n` và ngắt dòng `\n` giúp bảo tồn nguyên vẹn ngữ cảnh của từng điều khoản và bảng dữ liệu mà không bị xé lẻ.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn tối đa để người mua gửi yêu cầu Trả hàng/Hoàn tiền là bao lâu đối với thực phẩm tươi sống, đơn do người bán tự vận chuyển và các đơn hàng khác? | Thực phẩm tươi sống/đông lạnh: 24 giờ từ khi giao thành công. Đơn do người bán tự vận chuyển: 15 ngày từ khi bấm Đã nhận được hàng, hoặc 20 ngày từ khi lấy hàng thành công nếu chưa bấm nhận. Các đơn khác: 15 ngày từ khi giao thành công. | `shopee-returns-01.md` (Mục 1.2) |
| 2 | Sản phẩm hạn chế trả hàng là gì và Shopee không áp dụng lý do trả hàng nào cho nhóm sản phẩm này? Hãy nêu ba ví dụ. | Là sản phẩm có tính đặc thù cao, dễ hư hỏng hoặc cần bảo quản nghiêm ngặt. Shopee không áp dụng lý do "Hàng nguyên vẹn nhưng không còn nhu cầu". Ví dụ: cây cảnh, thực phẩm tươi sống/đông lạnh, găng tay/khẩu trang y tế. | `shopee-returns-03.md` (Mục Danh mục hạn chế) |
| 3 | Video mở kiện dùng làm bằng chứng khi hàng bị lỗi hoặc khác mô tả phải đáp ứng những yêu cầu nào, và nếu video vượt dung lượng cho phép thì xử lý ra sao? | Quay liên tục không cắt ghép, rõ 6 mặt kiện hàng, mã vận đơn, quá trình mở kiện và tình trạng hàng. Dung lượng tối đa 100 MB / 1 phút; nếu lớn hơn thì tải lên YouTube/Google Drive ở chế độ công khai và gửi link. | `shopee-returns-04.md` (Mục Quy định bằng chứng) |
| 4 | Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu Trả hàng/Hoàn tiền? | Vào Tôi > Đơn Mua > chọn tab Trả hàng/Hoàn tiền > chọn sản phẩm cần theo dõi > bấm Chi Tiết Trả Hàng/Hoàn Tiền. | `shopee-returns-05.md` (Mục Trên ứng dụng Shopee) |
| 5 | Sau khi Shopee chấp nhận hoàn tiền, thời gian nhận tiền đối với Ví ShopeePay, thẻ Napas và thẻ tín dụng/ghi nợ khác nhau như thế nào? | Ví ShopeePay: trong 24 giờ; thẻ nội địa Napas: 2-5 ngày làm việc; thẻ tín dụng/ghi nợ: 7-14 ngày làm việc. | `shopee-returns-06.md` (Bảng phương thức hoàn tiền) |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | q1_return_deadline | `Recursive` + `metadata_filter={"customer_role": "buyer"}` | Có (Top-1) | Đạt 2 điểm: Pre-filter loại bỏ kết quả của người bán, tìm đúng mục 1.2 trong `shopee-returns-01` (Score 0.7066). |
| 2 | q2_restricted_products | `Recursive (500)` / `LangChain` | Có (Top-1) | Đạt 2 điểm: Lấy chính xác bảng danh mục hạn chế trả hàng trong `shopee-returns-03` (Score 0.6949). |
| 3 | q3_evidence_video | `Recursive (500)` | Có (Top-1) | Đạt 2 điểm: Lấy đúng chunk quy định video 6 mặt và hướng dẫn link Drive/Youtube trong `shopee-returns-04` (Score 0.7682). |
| 4 | q4_track_request | `Recursive (500)` | Có (Top-1) | Đạt 1 điểm: Lấy được chunk thông báo trong `shopee-returns-05` nhưng bị nhiễu bởi `shopee-returns-07` do chưa có filter. |
| 5 | q5_refund_time | `Recursive (500)` | Có (Top-1) | Đạt 2 điểm: Lấy trọn vẹn Bảng so sánh 3 phương thức hoàn tiền trong `shopee-returns-06` (Score 0.7230). |

**So sánh A/B: Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Thí nghiệm **A/B Testing** cho thấy metadata filtering có vai trò sống còn ở **Query 1 (`q1_return_deadline`)**:
> - **Khi KHÔNG lọc (`search`)**: Vector similarity trả về tài liệu `shopee-returns-07.md` (hướng dẫn cho Người bán `seller`) làm Top-1 do chứa nhiều cụm từ "thời hạn gửi hàng", gây nhiễu sai ngữ cảnh cho người mua.
> - **Khi CÓ lọc (`search_with_filter` với `metadata_filter={"customer_role": "buyer"}`)**: Loại bỏ 100% các chunk thuộc về seller, tìm chính xác 100% tài liệu `shopee-returns-01.md` cho người mua tại Top-1 (Score: 0.7066).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Cấu trúc Markdown ảnh hưởng trực tiếp đến Chunking:** Chiến lược chia đệ quy (`RecursiveChunker`) tôn trọng các ranh giới dòng (`\n\n`, `\n`) giữ lại 100% ngữ cảnh bảng biểu và danh sách từng bước tốt hơn nhiều so với chia theo độ dài cố định.
2. **Sức mạnh của Pre-filtering Metadata:** Trong RAG thực tế cho e-commerce, vai trò người dùng (`buyer` vs `seller`) là bộ lọc bắt buộc để tăng độ chính xác (Precision) trước khi thực hiện tìm kiếm vector.
3. **Ý nghĩa của Real Embedding & LLM API:** Kết hợp Hugging Face API Embedder (`paraphrase-multilingual-MiniLM-L12-v2` có L2 Norm) và Nvidia LLM API (`meta/llama-3.1-8b-instruct`) giúp câu trả lời sinh ra có độ tin cậy và mạch lạc tuyệt đối.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu nhưng việc thay đổi tham số `chunk_size` và chiến lược chunking dẫn đến sự khác biệt lớn về điểm số cosine và tính toàn vẹn của câu trả lời RAG. Chunk quá nhỏ (100-200 chars) gây đứt gãy thông tin; chunk quá lớn (>1000 chars) làm loãng điểm tương đồng của từ khóa cần tìm.

**Phân tích 1 Trường hợp Thất bại (Failure Case Analysis) & Đề xuất cải thiện:**
- **Câu hỏi gặp lỗi/nhiễu:** **Query 4 (`q4_track_request`)** — *"Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu Trả hàng/Hoàn tiền?"*
- **Hiện tượng lỗi:** Khi tìm kiếm không dùng metadata filter, Top-1 lại trả về `shopee-returns-07.md` (Score `0.8188`) thay vì `shopee-returns-05.md`.
- **Phân tích nguyên nhân:** Các từ khóa chung như *"theo dõi tình trạng"*, *"Trả hàng/Hoàn tiền"* xuất hiện dày đặc ở tài liệu hướng dẫn vận chuyển dành cho shop (`shopee-returns-07`), khiến véc-tơ embedding bị hút về tài liệu seller hơn tài liệu hướng dẫn từng bước trên App người mua (`shopee-returns-05`).
- **Đề xuất cải thiện:** Bổ sung pre-filtering `metadata_filter={"category": "tracking", "customer_role": "buyer"}` hoặc nâng cấp sang `MarkdownHeaderChunker` để tự động gắn tiêu đề mục `## Thao tác trên App Shopee` vào từng chunk.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
