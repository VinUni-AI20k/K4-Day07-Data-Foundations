# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** MicroGenius
**Thành viên:** Nguyễn Thị Thương, Phạm Tuấn Anh, Nguyễn Đức Anh, Mai Tiến Dũng
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Toàn bộ vòng đời giao dịch trên sàn TMĐT Shopee: đổi trả/hoàn tiền, vận chuyển, thanh toán, điều kiện đăng bán, bảo mật dữ liệu và điều khoản dịch vụ.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | [help.shopee.vn/portal/4/article/77251](https://help.shopee.vn/portal/4/article/77251) | 2026-08-03 / 2026-03-04 | 2171 | customer_role: buyer, category: returns-policy, language: vi |
| 2 | Quy định về đăng bán sản phẩm trên Shopee | [help.shopee.vn/portal/4/article/77246](https://help.shopee.vn/portal/4/article/77246) | 2026-08-03 / 2024-08-14 | 3877 | customer_role: seller, category: seller-listing, language: vi |
| 3 | Chính sách vận chuyển Shopee | [help.shopee.vn/portal/4/article/77250](https://help.shopee.vn/portal/4/article/77250) | 2026-08-03 / 2026-03-20 | 2388 | customer_role: both, category: shipping-policy, language: vi |
| 4 | Các phương thức thanh toán Shopee | [help.shopee.vn/portal/4/article/79198](https://help.shopee.vn/portal/4/article/79198) | 2026-08-03 / not-stated | 1623 | customer_role: buyer, category: payment, language: vi |
| 5 | Chính sách bảo mật Shopee | [help.shopee.vn/portal/4/article/77244](https://help.shopee.vn/portal/4/article/77244) | 2026-08-03 / 2026-06-04 | 1919 | customer_role: both, category: privacy-policy, language: vi |
| 6 | Điều khoản dịch vụ Shopee | [help.shopee.vn/portal/4/article/77243](https://help.shopee.vn/portal/4/article/77243) | 2026-08-03 / 2026-04-24 | 1273 | customer_role: both, category: terms-of-service, language: vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `customer_role` | string (enum) | `buyer` / `seller` / `both` | Cho phép `search_with_filter()` lọc theo vai trò người hỏi — ví dụ chỉ tìm trong tài liệu dành cho người bán khi câu hỏi về điều kiện đăng bán. |
| `category` | string | `returns-policy`, `shipping-policy`, `payment`, `seller-listing`, `privacy-policy`, `terms-of-service` | Phân loại chủ đề con, giúp thu hẹp phạm vi tìm kiếm và đánh giá độ liên quan của top-k kết quả theo từng nhóm chính sách. |
| `language` | string | `vi` | Đảm bảo chỉ truy xuất tài liệu đúng ngôn ngữ khi corpus mở rộng đa ngôn ngữ. |
| `document_version` / `retrieved_at` | string / date | `"2026-03-04"` / `2026-08-03` | Giúp kiểm tra độ mới của chính sách và truy vết câu trả lời về đúng phiên bản nguồn tại thời điểm lấy dữ liệu. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `k4-seller-listing` (3877 ký tự) | FixedSizeChunker (`fixed_size`, chunk_size=300) | 16 | 289.2 | Trung bình — có thể cắt giữa câu ở ranh giới cố định. |
| `k4-seller-listing` (3877 ký tự) | SentenceChunker (`by_sentences`) | 8 | 482.0 | Tốt — luôn giữ trọn câu, không cắt giữa ý. |
| `k4-seller-listing` (3877 ký tự) | RecursiveChunker mặc định (`recursive`, chunk_size=300, separators mặc định `["\n\n","\n",". "," ",""]`) | 167 | 23.2 | Kém — văn bản markdown có nhiều heading/dòng ngắn nên tách theo `"\n\n"` đã tạo rất nhiều đoạn nhỏ (heading đơn lẻ, dòng ngắn), mất ngữ cảnh nặng. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Nguyễn Thị Thương**
- **Loại chiến lược:** Recursive (đã tinh chỉnh tham số)
- **Mô tả & lý do chọn cho chủ đề này:** Baseline `RecursiveChunker` mặc định (chunk_size=300, separators mặc định) vỡ vụn nghiêm trọng trên dữ liệu K4 vì tài liệu markdown có nhiều heading/dòng ngắn — tách theo `"\n\n"` đã tạo 167 chunk, trung bình chỉ 23 ký tự (gần bằng 1 heading hoặc 1 dòng). Chọn tinh chỉnh: `RecursiveChunker(separators=["\n\n", "\n", ". "], chunk_size=400)` — bỏ separator `" "` và `""` để tránh đệ quy xuống tận cấp từ đơn khi một đoạn quá dài; nếu vẫn dài hơn `chunk_size` sau khi tách theo câu, sẽ cắt cứng theo 400 ký tự liên tục (văn bản mạch lạc) thay vì tách rời từng từ. Kết quả: 29 chunk trên `k4-seller-listing`, trung bình 133.7 ký tự — giữ trọn heading + đoạn văn/gạch đầu dòng liên quan thay vì vỡ thành từng dòng/từ rời rạc.
- **Code snippet (nếu custom):**
```python
from src.chunking import RecursiveChunker

chunker = RecursiveChunker(
    separators=["\n\n", "\n", ". "],  # bỏ " " và "" để tránh tách xuống cấp từ đơn
    chunk_size=400,
)
```

**Thành viên 2 — Phạm Tuấn Anh**
- **Loại chiến lược:** custom — `StatisticalChunker` (thư viện `semantic_chunkers`)
- **Mô tả & lý do chọn cho chủ đề này:** Chọn `StatisticalChunker` vì nó dùng embedding và ngưỡng động để phát hiện thay đổi ngữ nghĩa, giúp các ý liên quan nằm trong cùng một chunk. Trên bộ benchmark K4, chiến lược này truy xuất đúng cả 5/5 câu trong top-3.
- **Code snippet (nếu custom):**
```python
from semantic_router.encoders import HuggingFaceEncoder
from semantic_chunkers import StatisticalChunker

encoder = HuggingFaceEncoder()
statistical_chunker = StatisticalChunker(encoder=encoder)
```
> Lưu ý: `semantic_router` và `semantic_chunkers` không nằm trong `requirements.txt`/`requirements-local.txt` của repo — cần `pip install semantic-router semantic-chunkers` riêng trước khi chạy thử.

**Thành viên 3 — Nguyễn Đức Anh**
- **Loại chiến lược:** `SentenceChunker` (có sẵn trong `src/chunking.py`)
- **Mô tả & lý do chọn cho chủ đề này:** Chọn `SentenceChunker` vì nó giữ được ranh giới câu tự nhiên, nên chunk đọc dễ hiểu hơn so với cắt cứng theo số ký tự. Mỗi chunk gồm vài câu trọn vẹn, nên khi truy xuất bằng RAG, agent nhận được ngữ cảnh mạch lạc hơn để trả lời.
- **Code snippet (nếu custom):**
```python
from src.chunking import SentenceChunker

chunker = SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 4 — Mai Tiến Dũng**
- **Loại chiến lược:** custom — `MarkdownBlockChunker`
- **Mô tả & lý do chọn cho chủ đề này:** Chọn `MarkdownBlockChunker` vì bộ tài liệu nhóm chủ yếu được viết bằng Markdown và có nhiều tiêu đề chính sách rõ ràng. Chiến lược này chia văn bản theo các block được ngăn cách bằng dòng trống, đồng thời giữ heading gần nhất cùng nội dung chunk. Khi block quá dài, văn bản được tách tiếp theo ranh giới câu. Cách chia này giúp giữ trọn các thông tin quan trọng như thời hạn, mức giá và phần trăm bồi thường, phù hợp với truy xuất RAG hơn cắt theo kích thước cố định. Kết quả đạt 5/5 câu có chunk liên quan trong top-3, 4/5 câu ở top-1 và 10/10 điểm truy xuất.
- **Code snippet (nếu custom):**
```python
from src.chunking import MarkdownBlockChunker

chunker = MarkdownBlockChunker(chunk_size=500)
chunks = chunker.chunk(text)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Thị Thương | Recursive (tinh chỉnh: bỏ separator từ đơn, chunk_size=400) | **8/10** — chạy thật với `EMBEDDING_PROVIDER=local`: 5/5 câu có gold doc trong top-3, 3/5 câu đúng ngay top-1 (chi tiết: `REPORT_NGUYENTHITHUONG_2A202601226.md` Phần 5) | Giữ trọn heading + đoạn văn/gạch đầu dòng thay vì vỡ thành từ đơn; số chunk (29) hợp lý hơn nhiều so với bản mặc định (167); 3/5 câu trúng top-1 | Câu hỏi về số liệu/phần trăm (vd. hạn sử dụng, mức bồi thường) dễ bị nhầm giữa các tài liệu khác nhau cùng chứa nhiều con số|
| Phạm Tuấn Anh | Custom — `StatisticalChunker` (`semantic_chunkers`) | **10/10** — benchmark K4: 5/5 câu có gold doc trong top-3 | Ngưỡng động theo embedding giúp gom đúng các câu cùng chủ đề vào một chunk; trên K4 đạt top-3 cho cả 5 câu | Tốn thời gian/tài nguyên tính embedding cho từng câu; phụ thuộc thư viện ngoài |
| Nguyễn Đức Anh | `SentenceChunker` (có sẵn) | **7/10** — 4/5 câu có gold doc trong top-3; q2-q4 đúng top-1, q5 đúng ở top-3 | Giữ trọn ranh giới câu, chunk dễ đọc, ngữ cảnh mạch lạc cho agent | Không nhận biết chủ đề/ý; q1 bị xếp sai tài liệu, q5 không đúng top-1 |
| Mai Tiến Dũng | Custom — `MarkdownBlockChunker` | 10/10 | Giữ heading cùng block nội dung, đạt 5/5 chunk liên quan trong top-3 và 4/5 ở top-1 | Tạo nhiều chunk hơn baseline, làm tăng chi phí embedding và lưu trữ |


**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `MarkdownBlockChunker` là lựa chọn phù hợp nhất cho bộ tài liệu này vì nó giữ heading cùng block chính sách chứa số liệu, điều kiện và ngoại lệ; kết quả đạt 5/5 query có chunk liên quan trong top-3 và 4/5 ngay top-1. `StatisticalChunker` cũng đạt 10/10, nhưng phụ thuộc thêm thư viện và phải tính embedding trong lúc chunking. Vì vậy, MarkdownBlockChunker là lựa chọn cân bằng hơn giữa chất lượng truy xuất, khả năng giải thích và chi phí triển khai.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng và hoàn tiền sau khi nhận hàng? | Trong vòng 15 ngày kể từ khi giao hàng thành công; riêng thực phẩm tươi/đông lạnh là 24 giờ. | `k4-returns-policy` (metadata_filter: `customer_role=buyer`) |
| 2 | Đơn hàng thanh toán bằng Apple Pay trên Shopee cần nằm trong khoảng giá trị nào? | Từ 10.000 VNĐ đến 25.000.000 VNĐ. | `k4-payment-methods` (metadata_filter: `customer_role=buyer`) |
| 3 | Người dùng liên hệ ai để yêu cầu truy cập hoặc xóa dữ liệu cá nhân trên Shopee? | Liên hệ Cán bộ bảo vệ dữ liệu (Data Protection Officer) qua email dpo.vn@shopee.com. | `k4-privacy-policy` (metadata_filter: `customer_role=buyer`) |
| 4 | Người bán phải đảm bảo hạn sử dụng còn lại tối thiểu bao nhiêu khi đăng bán sản phẩm có hạn dùng? | Chỉ được bán khi giao đi sản phẩm còn ít nhất 30% thời hạn sử dụng và ít nhất 30 ngày. | `k4-seller-listing` (metadata_filter: `customer_role=seller`) |
| 5 | Mức bồi thường tối đa khi kiện hàng bị mất hoàn toàn trong quá trình vận chuyển là bao nhiêu? | 70% giá trị sản phẩm, áp dụng khi đơn vị vận chuyển không bồi thường. | `k4-shipping-policy` (không cần lọc metadata) |

> Bộ câu hỏi đầy đủ (id, query, gold_answer, gold_doc_id, metadata_filter) ở dạng máy đọc được: xem `benchmark_queries.json`.

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn trả hàng/hoàn tiền | MarkdownBlockChunker | Có | Chunk trả hàng chứa trọn mốc 15 ngày và ngoại lệ 24 giờ, đúng top-1. |
| 2 | Khoảng giá trị Apple Pay | MarkdownBlockChunker | Có | Heading Apple Pay và khoảng 10.000-25.000.000 VNĐ nằm cùng block, đúng top-1. |
| 3 | Liên hệ truy cập/xóa dữ liệu | StatisticalChunker | Có | StatisticalChunker đưa chunk về Data Protection Officer lên top-1; MarkdownBlockChunker cũng có gold chunk ở top-3. |
| 4 | Hạn sử dụng khi đăng bán | MarkdownBlockChunker | Có | Điều kiện 30% thời hạn sử dụng và 30 ngày được giữ trọn, đúng top-1. |
| 5 | Bồi thường mất hàng hoàn toàn | MarkdownBlockChunker | Có | Block bồi thường chứa trực tiếp mức 70%, đúng top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Bộ lọc `customer_role=buyer` giúp thu hẹp kết quả cho câu hỏi về đổi trả và Apple Pay; `customer_role=seller` đặc biệt hữu ích ở câu hỏi về quy định hạn sử dụng khi đăng bán. Tuy nhiên, filter không thay thế chunking: với câu hỏi đổi trả, chiến lược SentenceChunker vẫn không đưa đúng tài liệu vào top-3, cho thấy chất lượng và cấu trúc chunk vẫn quyết định thứ hạng cuối cùng.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Cùng một corpus và embedding model, cách chia chunk khác nhau có thể thay đổi đáng kể tài liệu/chunk ở top-1.
> - Với tài liệu chính sách dạng Markdown, giữ heading cùng block nội dung giúp truy xuất tốt các mốc số liệu, điều kiện và ngoại lệ.
> - Đánh giá cần kết hợp gold chunk trong top-3 với khả năng trả lời từ context, thay vì chỉ nhìn cosine score.

**Bài học rút ra khi so sánh trong nhóm:**
> Trên cùng sáu tài liệu và năm query, MarkdownBlockChunker và StatisticalChunker đạt 10/10, Recursive tinh chỉnh đạt 8/10, còn SentenceChunker đạt 7/10. Điều này cho thấy ranh giới câu giúp context dễ đọc nhưng chưa đủ khi thông tin cần giữ gắn với heading, danh sách hoặc block điều khoản. Chunking theo cấu trúc hoặc ngữ nghĩa giúp giảm nguy cơ tách rời phần điều kiện và con số quan trọng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung nhiều câu hỏi về ngoại lệ, mốc thời gian và tình huống gần nghĩa để benchmark phân biệt rõ hơn giữa các chiến lược. Metadata vai trò cũng nên hỗ trợ ngữ nghĩa `both`, để filter cho buyer hoặc seller vẫn xem được các chính sách áp dụng cho cả hai. Cuối cùng, nhóm sẽ lưu hạng top-k và câu trả lời Agent ở cùng một log tái lập được thay vì tổng hợp thủ công.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
