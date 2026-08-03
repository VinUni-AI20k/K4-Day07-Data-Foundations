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
> *1 câu — ví dụ: đổi trả + điều kiện người bán.*

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính Sách Bán Hàng Và Trả Hàng | [Apple Store VN](https://www.apple.com/vn/shop/browse/open/salespolicies) | 2026-08-03 / not-stated | ~600 | role: buyer, category: returns |
| 2 | Bảo Hành Có Giới Hạn 1 Năm | [Apple Legal](https://www.apple.com/legal/warranty/products/warranty-rest-of-apac-vietnamese.html) | 2026-08-03 / not-stated | ~600 | role: buyer, category: warranty |
| 3 | Chính Sách Quyền Riêng Tư | [Apple Privacy](https://www.apple.com/vn/legal/privacy/vn/) | 2026-08-03 / not-stated | ~600 | role: both, category: privacy |
| 4 | Điều Khoản Dịch Vụ Truyền Thông | [Apple iTunes](https://www.apple.com/vn/legal/internet-services/itunes/vn/terms.html) | 2026-08-03 / not-stated | ~600 | role: buyer, category: terms |
| 5 | Nhận Biết Thư Email Lừa Đảo | [Apple Support](https://support.apple.com/vi-vn/102568) | 2026-08-03 / not-stated | ~600 | role: both, category: security |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [ ] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [ ] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| customer_role | string | buyer, both | Hữu ích để lọc riêng các tài liệu liên quan đến người mua hoặc áp dụng chung, tránh đưa ra các chính sách sai đối tượng. |
| category | string | returns, warranty, privacy | Giúp phân loại rõ ràng từng nhóm chủ đề chính sách (đổi trả, bảo hành, bảo mật), hỗ trợ việc lọc chính xác hơn nếu quy mô tài liệu lớn lên. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| k4-apple-sales-refund | FixedSizeChunker (`fixed_size`) | 4 | 177.2 | Tương đối — cắt theo ký tự cố định (chunk_size=200) nên có thể chia đôi một câu/điều khoản |
| k4-apple-sales-refund | SentenceChunker (`by_sentences`) | 2 | 278.0 | Tốt — mỗi chunk gồm trọn câu, không bị cắt giữa ý |
| k4-apple-sales-refund | RecursiveChunker (`recursive`) | 6 | 91.7 | Khá — tách theo `\n`/`. ` nên chunk ngắn hơn nhưng vẫn trọn câu/điều khoản |
| k4-apple-warranty | FixedSizeChunker (`fixed_size`) | 5 | 174.4 | Tương đối — như trên, có nguy cơ cắt giữa câu dài |
| k4-apple-warranty | SentenceChunker (`by_sentences`) | 1 | 670.0 | Kém — toàn bộ tài liệu gộp thành 1 chunk duy nhất vì `max_sentences_per_chunk` mặc định gộp hết các câu ngắn, mất khả năng truy xuất chi tiết theo điều khoản |
| k4-apple-warranty | RecursiveChunker (`recursive`) | 78 | 7.6 | **Rất kém — xem Failure Case bên dưới** |
| k4-apple-privacy | FixedSizeChunker (`fixed_size`) | 4 | 173.8 | Tương đối — tương tự các tài liệu khác |
| k4-apple-privacy | SentenceChunker (`by_sentences`) | 2 | 271.0 | Tốt — mỗi chunk trọn câu |
| k4-apple-privacy | RecursiveChunker (`recursive`) | 5 | 107.6 | Khá — chunk ngắn nhưng vẫn giữ trọn ý |

> **Failure case đáng chú ý (RecursiveChunker trên `k4-apple-warranty`):** văn bản này có câu mở đầu rất dài (~370 ký tự) và không chứa dấu `. ` ở giữa câu (chỉ có 1 câu duy nhất, dài, không dấu chấm giữa câu). Vì `RecursiveChunker` thử tách theo thứ tự ưu tiên `\n\n → \n → ". " → " " → ""`, khi không tìm thấy `\n\n`, `\n`, hay `". "` để chia nhỏ câu dài này xuống dưới `chunk_size`, nó rơi xuống tách theo dấu cách `" "` — bẻ câu thành từng cụm 2-3 từ (78 chunk, trung bình chỉ 7.6 ký tự/chunk). Kết quả: ngữ nghĩa bị vỡ vụn hoàn toàn, không chunk nào còn đủ thông tin để trả lời câu hỏi liên quan đến bảo hành. Đây là lý do `BulletPointChunker` (chunker tùy chỉnh, xem mục "Chiến lược của từng thành viên") được thiết kế để giữ trọn câu chủ đề + từng điều khoản thay vì cắt theo ký tự/khoảng trắng mù quáng.

### Chiến lược của từng thành viên

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

**Thành viên 3 — Dương Văn Kiên (2A202601724)**
- **Loại chiến lược:** Custom — `BulletPointChunker` (chunk theo điều/khoản)
- **Mô tả & lý do chọn cho chủ đề này:** Cả 5 tài liệu Apple VN đều có cấu trúc cố định: 1 câu chủ đề (nêu quy định chung) + các dòng gạch đầu dòng `-` (mỗi dòng là MỘT điều khoản/ngoại lệ độc lập, đã trọn nghĩa). `BulletPointChunker` giữ mỗi điều khoản đi kèm câu chủ đề thành 1 chunk riêng, đảm bảo mỗi chunk tự đủ nghĩa để trả lời câu hỏi mà không cần chunk khác — khắc phục đúng lỗi mà `RecursiveChunker` gặp phải trên tài liệu `k4-apple-warranty` (xem Failure Case ở trên).
- **Code snippet (nếu custom):**
```python
class BulletPointChunker:
    """Chiến lược chia nhỏ tùy chỉnh cho chính sách TMĐT dạng "câu chủ đề + gạch đầu dòng".

    Lý do thiết kế: các tài liệu chính sách Apple VN đều có cấu trúc cố định: một đoạn
    mở đầu (câu chủ đề nêu quy định chung), theo sau bởi các dòng bắt đầu bằng "-" (mỗi
    dòng là MỘT điều khoản/ngoại lệ độc lập, đã trọn nghĩa). Chunker này giữ mỗi điều
    khoản đi kèm câu chủ đề, đảm bảo mỗi chunk luôn tự đủ nghĩa.
    """

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]

        heading = ""
        intro = ""
        bullets: list[str] = []
        for line in lines:
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
            elif line.startswith("-"):
                bullets.append(line.lstrip("-").strip())
            else:
                intro = f"{intro} {line}".strip() if intro else line

        if not bullets:
            return [" ".join(filter(None, [heading, intro]))] if (heading or intro) else []

        return [
            " ".join(filter(None, [heading, intro, bullet])).strip()
            for bullet in bullets
        ]
```

**Kết quả benchmark (5 câu hỏi, `EMBEDDING_PROVIDER=local`, 13 chunk từ 5 tài liệu):**

| # | Top-1 đúng tài liệu? | Ghi chú |
|---|---|---|
| 1 | Đúng (sales-refund, "14 ngày") | 2/2 |
| 2 | Đúng (warranty, đúng câu loại trừ pin/lớp bảo vệ) | 2/2 |
| 3 | Sai — top-1 lấy nhầm `privacy`, chunk đúng (`media-terms`, "trẻ dưới 15 tuổi") rơi xuống top-2 | 1/2 |
| 4 | Retrieve nhầm tài liệu — cả top-3 đều thuộc `sales-refund`, không chunk nào nói về "App Store"/nội dung số; thông tin đúng nằm ở `media-terms` | 0/2 |
| 5 | Đúng (phishing, đúng câu cảnh báo số thẻ tín dụng) | 2/2 |

**Tổng điểm truy xuất của tôi: 7/10**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Thành viên 1 | RecursiveChunker(chunk_size=400) | | | |
| Thành viên 2 | SentenceChunker(max_sentences_per_chunk=2) | | | |
| Dương Văn Kiên | BulletPointChunker (custom) | 7 | Mỗi chunk tự đủ nghĩa (câu chủ đề + 1 điều khoản), tránh vỡ vụn như RecursiveChunker trên văn bản không có dấu chấm giữa câu | Câu hỏi đa-tài-liệu (câu 4) vẫn retrieve nhầm vì embedding đánh giá cả `sales-refund` liên quan đến "hoàn tiền/mua hàng" dù nội dung đúng nằm ở tài liệu khác — cần thêm metadata `category` để lọc mới xử lý được |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Tôi có bao nhiêu ngày để hoàn trả sản phẩm mua từ Apple Store? | Bạn có thể hoàn trả các sản phẩm đủ điều kiện trong vòng 14 ngày kể từ ngày nhận được sản phẩm. | k4-apple-sales-refund.md |
| 2 | Các lớp bảo vệ hoặc pin bị chai theo thời gian có được Apple bảo hành không? | Không. Bảo hành không áp dụng cho các linh kiện tiêu hao, như pin hoặc các lớp bảo vệ được thiết kế là sẽ hao mòn theo thời gian. | k4-apple-warranty.md |
| 3 | Trẻ em dưới 15 tuổi có được tự do tạo tài khoản Apple ID không? | Trẻ em dưới 15 tuổi không được tạo tài khoản trừ khi được cha mẹ hoặc người giám hộ hợp pháp chấp thuận thông qua Chia sẻ trong gia đình. | k4-apple-media-terms.md |
| 4 | (Filter role: buyer) Là người mua, tôi có được hoàn tiền khi lỡ mua ứng dụng trên App Store không? | Tất cả các giao dịch mua nội dung số trên App Store là giao dịch cuối cùng và không thể hoàn tiền (trừ khi pháp luật quy định khác). | k4-apple-media-terms.md |
| 5 | (Filter role: both) Tôi nhận được email yêu cầu cung cấp số thẻ tín dụng từ Apple, tôi có nên làm theo không? | Không. Apple sẽ không bao giờ yêu cầu cung cấp số thẻ tín dụng qua email. Bạn nên chuyển tiếp email đó đến reportphishing@apple.com. | k4-apple-phishing.md |

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
> *Viết 2-3 câu:*

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
