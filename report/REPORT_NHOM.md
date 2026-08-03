# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A6-3
**Thành viên:** Trần Lương Hoàng Anh (2A202601572), Trần Thế Ninh (2A202602001), Nguyễn Trung Đức (2A202601750), Nguyễn Thị Thu Trang (2A202601634)
**Ngày:** 03-08-2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:** **Chính sách đổi trả** (returns policy) + điều kiện người bán (đăng ký tài khoản bán hàng Shopee) — vì có nhiều nguồn công khai dễ tìm, cấu trúc rõ (điều kiện/thời hạn/ngoại lệ/quy trình) dễ viết gold answer và dễ tạo câu hỏi cần lọc metadata (theo platform / customer_role).

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu (file) | Nguồn (Source URL) | Ngày lấy / Phiên bản | customer_role | platform | category | Số ký tự |
|---|--------------|------------|--------------------|----------|----------|----------|----------|
| 1 | returns-policy.md (template mẫu do lab cung cấp) | N/A — template lab, không phải nguồn crawl thật | n/a / n/a | buyer | — | returns | 634 |
| 2 | seller-listing.md (template mẫu do lab cung cấp) | N/A — template lab, không phải nguồn crawl thật | n/a / n/a | seller | — | listing | 476 |
| 3 | tiki-seller-return-faq.md | https://hocvien.tiki.vn/faq/cau-hoi-thuong-gap-ve-xu-ly-doi-tra-bao-hanh/ | 2026-08-03 / n/a | seller | tiki | return_policy | 11995 |
| 4 | tiki-buyer-return-policy.md | https://hotro.tiki.vn/knowledge-base/post/802-chinh-sach-doi-tra-san-pham | 2026-08-03 / 2026-07-01 | buyer | tiki | return_policy | 10301 |
| 5 | shopee-seller-registration.md | https://banhang.shopee.vn/edu/article/3243 | 2026-08-03 / 2026-06-01 | seller | shopee | seller_onboarding | 2217 |
| 6 | lazada-order-cancellation-refund.md | https://www.lazada.vn/helpcenter/want-to-cancel-your-order-heres-how | 2026-08-03 / 2026-07-29 | buyer | lazada | return_policy | 1558 |
| 7 | tiktok-shop-return-refund-policy.md | https://seller-vn.tiktok.com/university/essay?knowledge_id=6837773789234946 | 2026-08-03 / 2026-10-06 | buyer | tiktok_shop | return_policy | 12317 |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.
- [x] `sources.csv` khớp 1-1 với các file (7 dòng).
- [⚠️] 2 file `returns-policy.md`, `seller-listing.md` là template khởi động của lab — **không phải nguồn crawl thật** (source_url = `N/A — template lab`), chỉ dùng để chạy thử pipeline.
- [⚠️] Tài liệu Lazada và TikTok Shop là **tiếng Anh** — ghi nhận là **giới hạn corpus** (không đồng nhất ngôn ngữ), không thay thế.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | str (kebab-case) | `tiki-buyer-return-policy` | Nhận diện duy nhất; dùng cho `delete_document` / lọc theo doc_id |
| `title` | str | `Chính sách về đổi trả hàng và hoàn tiền (Tiki)` | Hiển thị, truy vết câu trả lời |
| `source_url` | str (URL gốc) | `https://hotro.tiki.vn/...` | Truy vết nguồn (bắt buộc K4) |
| `retrieved_at` | `YYYY-MM-DD` | `2026-08-03` | Kiểm tra độ mới của dữ liệu |
| `document_version` | str / `not-stated` | `2026-07-01` | Phiên bản/ngày hiệu lực (truy vết) |
| `customer_role` | `buyer` \| `seller` \| `both` | `seller` | **Lọc metadata** — câu hỏi benchmark cần `{"customer_role": "seller"}` |
| `platform` | kebab-case | `tiki`, `shopee`, `lazada` | **Lọc theo sàn** — hữu ích nhất trong thử nghiệm này |
| `category` | kebab-case | `return_policy`, `seller_onboarding` | Nhóm chủ đề, mở rộng sau |
| `doc_type` | kebab-case | `platform-policy` | Phân biệt chính sách sàn vs nguồn pháp lý |
| `language` | `vi` \| `en` | `vi` | Lọc ngôn ngữ; tài liệu Lazada dùng `en` |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên toàn bộ 7 tài liệu (chunk_size=500), thêm chiến lược tùy chỉnh `SectionChunker` và `FAQChunker`:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| tiki-buyer-return-policy | `fixed_size` | 23 | 495.70 | Không — cắt ngang mục |
| | `by_sentences` | 23 | 445.78 | Khá — theo câu |
| | `recursive` | 32 | 343.84 | Khá |
| | **`section`** | **36** | **307.67** | **Tốt — theo heading** |
| tiki-seller-return-faq | `fixed_size` | 27 | 492.41 | Không |
| | `by_sentences` | 42 | 283.17 | Khá |
| | `recursive` | 37 | 356.00 | Khá |
| | **`section`** | **42** | **291.02** | **Tốt — 1 câu FAQ/chunk** |
| shopee-seller-registration | `fixed_size` | 5 | 483.40 | Không |
| | `by_sentences` | 6 | 367.67 | Khá |
| | `recursive` | 8 | 292.00 | Khá |
| | **`section`** | **9** | **267.00** | **Tốt — theo bước** |
| lazada-order-cancellation-refund | `fixed_size` | 4 | 427.00 | Không |
| | `by_sentences` | 9 | 171.22 | Khá |
| | `recursive` | 4 | 388.00 | Khá |
| | **`section`** | **4** | **388.00** | Tốt (fallback recursive — ít heading) |
| tiktok-shop-return-refund-policy | `fixed_size` | 28 | 488.11 | Không |
| | `by_sentences` | 33 | 371.39 | Khá |
| | `recursive` | 45 | 314.09 | Khá |
| | **`section`** | **51** | **268.49** | **Tốt — theo mục (4.1–4.6)** |
| returns-policy (template) | `fixed_size` | 2 | 342.00 | Không |
| | `by_sentences` | 2 | 315.50 | Khá |
| | `recursive` | 2 | 316.00 | Khá |
| | **`section`** | **2** | **316.00** | Tốt (fallback recursive) |
| seller-listing (template) | `fixed_size` | 1 | 476.00 | — |
| | `by_sentences` | 2 | 236.50 | Khá |
| | `recursive` | 1 | 476.00 | — |
| | **`section`** | **1** | **476.00** | — (fallback recursive) |

**Tổng toàn corpus 7 tài liệu (chunk_size=500):**

| Chiến lược | Tổng count | avg_length (weighted) |
|-----------|-----------|------------------------|
| fixed_size | 90 | 484.98 |
| by_sentences | 117 | 335.50 |
| recursive | 129 | 335.70 |
| **section** | **145** | **290.03** |
| faq_pair | 136 | (chỉ tách Q&A trên tài liệu FAQ — tiki-faq 44/277.7; phần còn lại fallback recursive) |

### Chiến lược của từng thành viên
**Thành viên 1 — Trần Thế Ninh (2A202602001) — `SectionChunker`**
- **Loại chiến lược:** Custom — chia theo Markdown heading `#`/`##`/`###`.
- **Mô tả & lý do chọn:** Văn bản chính sách có cấu trúc điều khoản rõ ràng (Thời hạn / Điều kiện / Danh mục hạn chế / Quy trình / Hoàn tiền). Mỗi chunk = một heading + nội dung của nó, giữ trọn ý (chunk coherence), thay vì cắt cơ học theo độ dài. Section quá dài hoặc không có heading → fallback qua `RecursiveChunker`.
- **Code snippet:**
```python
class SectionChunker:
    HEADING_RE = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    def __init__(self, chunk_size: int = 800) -> None:
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(chunk_size=chunk_size)
    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        matches = list(self.HEADING_RE.finditer(text))
        if not matches:
            return self._recursive.chunk(text)
        boundaries = [m.start() for m in matches] + [len(text)]
        sections = []
        leading = text[0:boundaries[0]].strip()
        if leading:
            sections.append(leading)
        for i in range(len(matches)):
            section = text[boundaries[i]:boundaries[i+1]].strip()
            if section:
                sections.append(section)
        chunks, current = [], ""
        for section in sections:
            if len(section) > self.chunk_size:
                if current:
                    chunks.append(current); current = ""
                chunks.extend(self._recursive.chunk(section)); continue
            if not current:
                current = section
            elif len(current) + 2 + len(section) <= self.chunk_size:
                current = current + "\n\n" + section
            else:
                chunks.append(current); current = section
        if current:
            chunks.append(current)
        return chunks
```
- **Kết quả baseline (chunk_size=500):** tiki-buyer 36/307.67, tiki-faq 42/291.02, shopee 9/267, lazada 4/388, tiktok 51/268.49, returns 2/316, seller 1/476 → tổng **145 chunk / 290.03 avg**.
- **Điểm truy xuất (5 query, SCORING):** **3 / 10 unfiltered** (Q1=2, Q3=1, Q4=0, Q2=0, Q5=0) — **4 / 10** khi Q4 có filter `platform=lazada`.

**Thành viên 2 — Trần Lương Hoàng Anh (2A202601572) — `SentenceChunker`**
- **Loại chiến lược:** Built-in — chia theo ranh giới câu (`. `, `! `, `? `, `.\n`), gom tối đa 3 câu/chunk.
- **Mô tả & lý do chọn:** Mỗi chunk giữ nguyên câu hoàn chỉnh; phù hợp để kiểm tra xem chia theo câu có giữ được cặp "câu hỏi – câu trả lời" trong FAQ hay không.
- **Kết quả baseline:** 117 chunk / 335.50 avg (toàn corpus).
- **Điểm truy xuất:** **5 / 10 unfiltered** (Q1=2, Q2=2 — bắt đúng cặp Q&A "Hoàn tiền nhanh 500.000đ", Q3=1, Q4=0, Q5=0) — **6 / 10** khi Q4 có filter.

**Thành viên 3 — Nguyễn Trung Đức (2A202601750) — `RecursiveChunker`**
- **Loại chiến lược:** Built-in — đệ quy theo separator ưu tiên `["\n\n", "\n", ". ", " ", ""]`.
- **Mô tả & lý do chọn:** Chuẩn mực phổ dụng cho văn bản hỗn hợp; so sánh với các chiến lược có cấu trúc (section/FAQ) để xem giá trị của việc khai thác cấu trúc tài liệu.
- **Kết quả baseline:** 129 chunk / 335.70 avg (toàn corpus).
- **Điểm truy xuất:** **4 / 10 unfiltered** (Q1=2, Q2=0, Q3=2 — top-1 đúng câu trả lời đăng ký, Q4=0, Q5=0) — **5 / 10** khi Q4 có filter.

**Thành viên 4 — Nguyễn Thị Thu Trang (2A202601634) — `FAQChunker`**
- **Loại chiến lược:** Custom — chia theo cặp câu hỏi–trả lời (dòng kết thúc bằng `?`), mỗi chunk = một câu hỏi + nội dung trả lời tới câu hỏi kế tiếp; văn bản không có câu hỏi → fallback `RecursiveChunker`.
- **Mô tả & lý do chọn:** Khai thác cấu trúc FAQ của tài liệu Học viện Tiki (câu hỏi → trả lời), giữ trọn cặp Q&A để truy xuất trả về đơn vị thông tin hoàn chỉnh.
- **Code snippet:**
```python
class FAQChunker:
    def __init__(self, chunk_size: int = 800) -> None:
        self.chunk_size = chunk_size
        self._recursive = RecursiveChunker(chunk_size=chunk_size)
    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        lines = text.splitlines()
        q_indices = [i for i, line in enumerate(lines)
                     if line.strip().endswith("?") and len(line.strip()) < 200]
        if not q_indices:
            return self._recursive.chunk(text)
        chunks, leading = [], "\n".join(lines[:q_indices[0]]).strip()
        if leading:
            chunks.append(leading)
        for j, qi in enumerate(q_indices):
            end = q_indices[j+1] if j+1 < len(q_indices) else len(lines)
            section = "\n".join(lines[qi:end]).strip()
            if not section:
                continue
            chunks.extend(self._recursive.chunk(section)) if len(section) > self.chunk_size else chunks.append(section)
        return chunks
```
- **Kết quả baseline:** 136 chunk / ~avg thấp hơn recursive trên FAQ (44/277.7 cho tiki-faq) — toàn corpus 136 chunk.
- **Điểm truy xuất:** **4 / 10 unfiltered** (Q1=2, Q2=0, Q3=2, Q4=0, Q5=0) — **5 / 10** khi Q4 có filter.

### So Sánh Giữa Các Thành Viên

> **Ghi chú:** cột "Điểm truy xuất" = kết quả **unfiltered** trên 5 query (SCORING); cột "với filter Q4" = thêm `platform=lazada` cho riêng Q4.

| Thành viên | Chiến lược | Điểm (/10) unfiltered | Với filter Q4 | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|---------------|-----------|----------|
| 1 | `section` | **3** | **4** | Chunk theo heading, avg thấp nhất (290); Q1 top-1 chính xác | Q2, Q5 fail; Q4 cần filter |
| 2 | `by_sentences` | **5** | **6** | **Bắt đúng cặp Q&A "Hoàn tiền nhanh" (Q2)** — điểm cao nhất | Q5 fail; Q4 cần filter |
| 3 | `recursive` | **4** | **5** | Q3 top-1 đúng câu trả lời đăng ký | Q2, Q5 fail; Q4 cần filter |
| 4 | `faq_pair` | **4** | **5** | Q3 top-1 đúng; giữ trọn cặp Q&A trên FAQ | Q2, Q5 fail; Q4 cần filter |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **`SentenceChunker` đạt điểm cao nhất (5/10, 6/10 có filter)** — vì nó vô tình giữ nguyên cặp "câu hỏi → câu trả lời" trong FAQ (bắt đúng chunk Hoàn tiền nhanh mà các chiến lược khác bỏ lỡ). `SectionChunker` cho **avg_length thấp nhất (290.03)** và chunk gọn 1 điều khoản — tốt nhất về chunk coherence, nhưng chưa thắng về retrieval trên bộ query này. Cả 4 đều fail Q4 (nhiễu TikTok, cần metadata filter) và Q5 (phủ định). Kết luận cuối nên dựa trên thảo luận nhóm với đầy đủ 4 thành viên.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? | Metadata filter đề xuất |
|---|-------|-------------------------------|--------------------------|------------------|
| 1 | Thời hạn hỗ trợ đổi trả sản phẩm tại Tiki là bao lâu? | Trong vòng **30 ngày** kể từ lúc nhận hàng thành công (đơn từ 15/04/2024); riêng Thiết bị số – Phụ kiện số, Điện gia dụng do Tiki Trading cung cấp được đổi trả **365 ngày** nếu lỗi kỹ thuật. | `tiki-buyer-return-policy.md` — mục "Thời gian hỗ trợ đổi trả tại Tiki" | `customer_role=buyer`, `platform=tiki` |
| 2 | Trường hợp nào Tiki áp dụng quy trình Hoàn tiền nhanh cho nhà bán? | Sản phẩm có giá trị đền bù **từ 500.000đ trở xuống** (từ 15/04/2024): thiếu phụ kiện, bể vỡ/trầy xước, hết hạn sử dụng, rách/mất tem niêm phong. | `tiki-seller-return-faq.md` — mục III.10 "Hoàn tiền nhanh (Easy refund)" | `customer_role=seller` |
| 3 | Người bán chưa có tài khoản Shopee bắt đầu đăng ký bán hàng như thế nào? | Tải app Kênh Người Bán Shopee, Bước 1: điền **Tên đăng nhập chưa được đăng ký** → Đồng ý → SĐT Việt Nam → mã xác thực → mật khẩu → Face ID/vân tay. | `shopee-seller-registration.md` — mục 1 "chưa có tài khoản Shopee" | `customer_role=seller`, `platform=shopee` |
| 4 | Khách hàng không thể hủy đơn trên Lazada trong trường hợp nào? | Khi đơn đã đóng gói/đã giao cho courier; hủy một phần đơn gộp/voucher; thanh toán trả góp sau khi xác nhận. | `lazada-order-cancellation-refund.md` — mục "When can't I cancel?" | `customer_role=buyer`, `platform=lazada` |
| 5 | Sản phẩm nước hoa / đồ lót có được đổi trả do đổi ý tại Tiki không? | **Không** — thuộc Danh mục hạn chế đổi trả (Làm đẹp: Nước hoa; Thời trang & Đồ chơi-Mẹ&Bé: Đồ lót, đồ bơi); chỉ được từ chối nhận hàng. | `tiki-buyer-return-policy.md` — mục "Danh mục hạn chế đổi trả" (record #28 trong store) | `customer_role=buyer`, `platform=tiki` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).
>
> Bảng dưới so sánh **điểm từng query** theo 4 chiến lược (đều đã thực thi thật trên corpus 7 doc, unfiltered). Điểm Q4 khi thêm `platform=lazada` được ghi trong ngoặc.

| # | Câu hỏi | `section` (TV1) | `by_sentences` (TV2) | `recursive` (TV3) | `faq_pair` (TV4) |
|---|---------|:---:|:---:|:---:|:---:|
| 1 | Thời hạn đổi trả Tiki | **2** | **2** | **2** | **2** |
| 2 | Hoàn tiền nhanh | **0** | **2** | **0** | **0** |
| 3 | Đăng ký Shopee | **1** | **1** | **2** | **2** |
| 4 | Hủy đơn Lazada | **0** (1) | **0** (1) | **0** (1) | **0** (1) |
| 5 | Hạn chế đổi trả Tiki | **0** | **0** | **0** | **0** |
| **Tổng** | | **3** (4) | **5** (6) | **4** (5) | **4** (5) |

> Số trong ngoặc = điểm khi Q4 chạy kèm `search_with_filter(platform=lazada)`. Chi tiết top-3 từng chiến lược ghi ở bảng dưới.

**Điểm mấu chốt:** `by_sentences` đạt cao nhất (5/10) vì **bắt đúng cặp Q&A "Hoàn tiền nhanh 500.000đ"** (Q2) — các chiến lược còn lại đều bỏ lỡ chunk này. Cả 4 đều fail Q4 (nhiễu TikTok) và Q5 (phủ định).

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

So sánh filtered vs unfiltered (đã chạy thật, corpus 7 doc):

| Query | Filter | Kết quả thay đổi? | Kết luận |
|-------|--------|-------------------|----------|
| Q3 | `customer_role=seller` | **Không đổi** — top-3 vốn đã là shopee seller | Lọc thừa ở trường hợp top-3 đã đúng |
| Q4 | `platform=lazada` | **Cải thiện rõ** — unfiltered top-3 bị chiếm bởi TikTok (cùng chủ đề hủy đơn); filtered khôi phục đúng 3 chunk Lazada (mục "When can't I cancel?" ở #2) | **Lọc bắt buộc** sau khi thêm TikTok: loại nhiễu chéo sàn — cả 4 chiến lược đều +1 điểm nhờ filter Q4 |
| Q5 | `platform=tiki` | **Không đổi** — top-3 vẫn như cũ | Lọc không cứu được failure (xem Bài 3.5) |

→ **Metadata filtering có giá trị rõ rệt nhất ở Q4** sau khi thêm TikTok Shop: cả 4 chiến lược đều fail Q4 khi không lọc (top-3 toàn TikTok) và đều được +1 điểm khi lọc `platform=lazada`. Q3 không cần lọc. Q5 không cứu được vì vấn đề nằm ở nội dung chunk/quan hệ phủ định.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Phân tích lỗi (Failure Analysis) — Bài 3.5

> **Ghi chú trung thực:** cả 4 chiến lược đều được thực thi thật trên cùng 5 query; mỗi chiến lược có ít nhất 1 failure case (Q4 hoặc Q5). Bảng dưới tổng hợp failure chung quan sát được từ kết quả thật, không gán cho người không chạy.

| Chiến lược | Câu hỏi thất bại | Nguyên nhân (từ kết quả thật) | Đề xuất cải thiện |
|-----------|------------------|------------------------------|-------------------|
| `section` | Q5 (nước hoa/đồ lót Tiki) | Chunk đúng (record #28) ngoài top-3; chunk danh mục cô đọng thiếu ngữ nghĩa phủ định; query phủ định | Ghép câu dẫn vào chunk; viết lại query khẳng định; thêm metadata product_category |
| `by_sentences` | Q5 (giống) | Top-3 toàn chunk "đổi trả nói chung" (không phải danh mục hạn chế) | Cần chunk giữ nguyên câu dẫn + danh sách mặt hàng |
| `recursive` | Q5 (giống) | Chunk danh mục bị lấn át bởi chunk "hoàn tiền nhanh" | Tăng trọng số từ khóa mặt hàng; metadata |
| `faq_pair` | Q4 (Lazada, unfiltered) + Q5 | Q4: top-3 toàn TikTok (nhiễu chéo sàn); Q5: chunk danh mục không phải Q&A nên fallback recursive | Q4: bắt buộc filter `platform=lazada`; Q5: như trên |

**Chi tiết failure case chung (Q5):**

**Câu hỏi thất bại:** *"Sản phẩm nước hoa hoặc đồ lót có được đổi trả do đổi ý tại Tiki không?"* (Q5)

**Điều đã xảy ra (bằng chứng từ kết quả thật):**
- Chunk chứa câu trả lời chính xác **tồn tại trong store** (record #28, doc `tiki-buyer-return-policy`, nội dung: "Thời trang nam/nữ: Đồ lót... Làm đẹp - Sức khỏe: Nước hoa") nhưng **không lọt vào top-3** — ở **cả 4 chiến lược** (section 0.680, by_sentences 0.671, recursive 0.680, faq_pair 0.680) và cả khi lọc `platform=tiki`.
- Top-1 bị chiếm bởi chunk "Hoàn tiền nhanh 500.000đ" hoặc các chunk "quy định khác" — các chunk này cùng nói về đổi trả/hoàn tiền Tiki nên embedding coi là tương đồng hơn chunk danh mục hạn chế.
- Cùng thất bại với `fixed_size` baseline (top-1 0.709 cũng là chunk sai).

**Nguyên nhân (từ output, không suy đoán):**
1. **Chunk danh mục quá cô đọng/thiếu cụm từ khớp query:** chunk #28 liệt kê dạng bullet ngắn ("Nước hoa", "Đồ lót, đồ bơi") — không chứa cụm "được đổi trả" hay "không được đổi trả" trong chính chunk đó (câu dẫn "không hỗ trợ đổi trả do đổi ý" nằm ở mục dẫn). Câu trả lời cần suy luận **phủ định** — embeddings khó bắt quan hệ "không".
2. **Query dạng phủ định mơ hồ:** cụm "có được đổi trả... không" khiến vector query gần với các chunk nói *về việc đổi trả nói chung* hơn là chunk danh mục liệt kê mặt hàng.
3. **Metadata filter không cứu được:** `platform=tiki` chỉ loại doc khác sàn; trong cùng doc Tiki vẫn có nhiều chunk về đổi trả cạnh tranh điểm hơn chunk danh mục.

**Đề xuất cải thiện cụ thể:**
1. **Ghép câu dẫn vào chunk danh mục:** gộp câu "Các sản phẩm... sẽ **không hỗ trợ đổi trả** do đổi ý..." vào cùng chunk với danh sách mặt hàng để chunk mang đầy đủ ngữ nghĩa phủ định.
2. **Viết lại query khẳng định:** thay vì hỏi phủ định, dùng *"các mặt hàng hạn chế đổi trả theo nhu cầu của Tiki gồm những gì"* — thử nghiệm cho top-1 `tiki-buyer` 0.797.
3. **Metadata bổ sung `product_category` cho từng chunk** (vd `limited_return: true`) để dùng `search_with_filter` chính xác hơn thay vì chỉ dựa vào `platform`.
4. **Thêm từ khóa mặt hàng cụ thể vào query** ("nước hoa", "đồ lót") — hiện query đã có nhưng chunk danh mục vẫn bị lấn át bởi các chunk "đổi trả nói chung".

---

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Chunk coherence ≠ điểm retrieval**: `SectionChunker` cho avg_length thấp nhất (290.03) và chunk gọn 1 điều khoản, nhưng điểm retrieval (3/10) thấp hơn `SentenceChunker` (5/10) — vì câu hỏi benchmark của chúng tôi phần lớn cần **đơn vị Q&A**, không phải đơn vị mục.
> 2. **`SentenceChunker` thắng nhờ vô tình giữ cặp Q&A**: nó bắt đúng chunk "Hoàn tiền nhanh 500.000đ" (Q2) — điểm số duy nhất tách biệt rõ (2 điểm) giữa 4 chiến lược.
> 3. **Metadata filter là chìa khóa khi corpus đa sàn**: sau khi thêm TikTok Shop, Q4 fail hoàn toàn ở cả 4 chiến lược khi không lọc, và đều +1 điểm khi lọc `platform=lazada` — minh chứng rõ nhất cho giá trị của metadata filtering trong bài 3.4.
> 4. **Failure chung Q5**: chunk danh mục cô đọng + câu hỏi phủ định làm cả 4 chiến lược đều fail — vấn đề nằm ở nội dung chunk và dạng câu hỏi, không phải chiến lược chia nhỏ.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng 5 câu hỏi, cùng corpus, khác chiến lược → điểm từ 3/10 (section) đến 5/10 (by_sentences). Khác biệt quyết định không nằm ở avg_length hay số chunk, mà ở **việc chiến lược có giữ được đơn vị thông tin mà câu hỏi cần** (cặp Q&A) hay không. `SectionChunker` tốt nhất về cấu trúc (avg 290) nhưng không tự động tốt nhất về truy xuất trên bộ query này.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> 1. **Thay 2 template lab (`returns-policy.md`, `seller-listing.md`)** bằng nguồn thật để corpus đồng nhất chất lượng (hiện chúng chỉ dùng để chạy thử pipeline).
> 2. **Thống nhất ngôn ngữ corpus (tiếng Việt)** — tài liệu Lazada và TikTok Shop hiện là tiếng Anh gây nhiễu chéo và làm giảm độ chính xác embedding tiếng Việt.
> 3. **Bổ sung metadata `product_category`/`limited_return`** cho từng chunk để `search_with_filter` xử lý được Q5 thay vì chỉ dựa vào `platform`.
> 4. **Chọn chunker theo loại tài liệu** thay vì một chiến lược duy nhất: dùng FAQChunker cho tài liệu FAQ, SectionChunker cho policy có heading — tận dụng điểm mạnh của từng loại.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **33 / 40** |

> **Lý do tự chấm:**
> - **Lựa chọn tài liệu (9/10):** có 5 nguồn thật với đủ metadata bắt buộc (`source_url`, `retrieved_at`, `document_version`, `customer_role`, `platform`, `category`…) và `sources.csv` khớp 1-1. 
> - **Thiết kế chiến lược (13/15):** cả 4 chiến lược đều được thực thi thật trên cùng corpus + cùng 5 query, có baseline so sánh (count/avg_length), code snippet và ghi chú trung thực về phân công nhóm.
> - **Chất lượng truy xuất (7/10):** chiến lược tốt nhất đạt 5/10 (6/10 khi lọc metadata); đã phân tích rõ giá trị metadata filter (Q4) và failure case Q5. 
> - **Thuyết trình (4/5):** đã soạn sẵn 4 insights từ kết quả thật.