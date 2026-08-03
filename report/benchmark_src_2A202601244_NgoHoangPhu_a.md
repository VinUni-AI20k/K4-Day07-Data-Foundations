# Benchmark — chiến lược `A-fixed-500/50`

- **Package cá nhân:** `src.2A202601244_NgoHoangPhu`
- **Backend nhúng:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- **Corpus:** `data\k4_ecommerce` — 6 tài liệu
- **Chunk:** 172 chunk | dài trung bình 487.7 ký tự (min 58 / max 500)
- **top_k:** 3
- **Mô tả chiến lược:** Cắt cứng 500 ký tự, chồng lấn 50. Không xử lý ranh giới điều khoản, không làm giàu metadata — dùng làm mốc để đo xem B và C cải thiện được bao nhiêu.

## Bảng 1 — Kết quả cá nhân (dán vào REPORT_CANHAN mục 5)

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Liên quan? | Câu trả lời của agent |
|---|---------|----------------------------|-------|------------|------------------------|
| 1 | Tôi nhận hàng bị vỡ thì được hoàn tiền không? | `shopee-shipping-policy::chunk_31` — g: - Hàng bị thất lạc khi hoàn trả: trong vòng 07 ng… | 0.452 | ❌ | [STUB LLM] đã nhận 1683 ký tự ngữ cảnh |
| 2 | Thời hạn gửi yêu cầu trả hàng là bao lâu? | `shopee-return-refund-request-guide::chunk_4` — ng báo > Cập nhật đơn hàng và/hoặc Email … | 0.748 | ✅ | [STUB LLM] đã nhận 1679 ký tự ngữ cảnh |
| 3 | Người bán bị cấm đăng bán những mặt hàng nào? | `shopee-seller-listing-rules::chunk_46` — ee. Khuyến cáo: Người Bán vui lòng tôn trọng và… | 0.710 | ✅ | [STUB LLM] đã nhận 1683 ký tự ngữ cảnh |
| 4 | Shopee hỗ trợ những phương thức thanh toán nào? | `shopee-return-refund-policy::chunk_37` — lệch (được xác định bằng 100% giá trị Sản Phẩm … | 0.742 | ⚠️ | [STUB LLM] đã nhận 1685 ký tự ngữ cảnh |
| 5 | Đơn hàng đang giao bị thất lạc thì xử lý ra sao? | `shopee-shipping-policy::chunk_19` — ược bàn giao thành công cho đơn vị vận chuyển: Bưu k… | 0.560 | ✅ | [STUB LLM] đã nhận 1686 ký tự ngữ cảnh |

**Số câu có chunk liên quan trong top-3: 4/5**
**Điểm truy xuất tự chấm (chưa tính độ đúng của câu trả lời): 7/10**

## Bảng 2 — Có filter vs không filter (REPORT_NHOM mục 3)

| # | metadata_filter | Điểm khi KHÔNG lọc | Điểm khi CÓ lọc | doc_id top-1 (không lọc) | doc_id top-1 (có lọc) |
|---|-----------------|--------------------|-----------------|--------------------------|------------------------|
| 3 | `{'customer_role': 'seller'}` | 1/2 | 2/2 | shopee-return-refund-policy | shopee-seller-listing-rules |

## Bảng 3 — Chi tiết top-k từng câu (để phân tích, không cần dán hết)

**Câu 1: Tôi nhận hàng bị vỡ thì được hoàn tiền không?**
gold_docs = `['shopee-return-refund-policy']` | filter = `None` | tự chấm truy xuất: **0/2** (không có gold trong top-3) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-shipping-policy::chunk_31` | 0.452 | shopee-shipping-policy | g: - Hàng bị thất lạc khi hoàn trả: trong vòng 07 ngày sau khi đơn hàng được cậ… |
| 2 | `shopee-shipping-policy::chunk_30` | 0.345 | shopee-shipping-policy | n khiếu nại mà Shopee không nhận được bất kì khiếu nại, yêu cầu bồi thường nào … |
| 3 | `shopee-shipping-policy::chunk_32` | 0.316 | shopee-shipping-policy | 1 ngày) mà Người Bán không liên hệ với Shopee để xử lý đơn hàng, Shopee miễn tr… |

Khoảng cách score top-1 → top-3: **0.136** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 2: Thời hạn gửi yêu cầu trả hàng là bao lâu?**
gold_docs = `['shopee-return-refund-policy', 'shopee-return-refund-request-guide']` | filter = `None` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-request-guide::chunk_4` | 0.748 | shopee-return-refund-request-guide | ng báo > Cập nhật đơn hàng và/hoặc Email của bạn. Thời gian hoàn tiền Nếu yêu c… |
| 2 | `shopee-delivery-process::chunk_0` | 0.680 | shopee-delivery-process | # Cách đơn vị vận chuyển giao hàng cho Người mua [Giao/nhận hàng] Đơn vị vận ch… |
| 3 | `shopee-return-refund-policy::chunk_7` | 0.665 | shopee-return-refund-policy | lạnh, Người Mua cần gửi yêu cầu trả hàng/hoàn tiền trong vòng 24 giờ kể từ lúc … |

Khoảng cách score top-1 → top-3: **0.083** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 3: Người bán bị cấm đăng bán những mặt hàng nào?**
gold_docs = `['shopee-seller-listing-rules']` | filter = `{'customer_role': 'seller'}` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-seller-listing-rules::chunk_46` | 0.710 | shopee-seller-listing-rules | ee. Khuyến cáo: Người Bán vui lòng tôn trọng và tuân thủ quy định đăng bán sản … |
| 2 | `shopee-seller-listing-rules::chunk_25` | 0.710 | shopee-seller-listing-rules | ẩm theo đúng định dạng tại đây. - Shopee nghiêm cấm bán sách & ấn phẩm đã qua s… |
| 3 | `shopee-seller-listing-rules::chunk_44` | 0.688 | shopee-seller-listing-rules | tốt cho Người Mua và làm giảm uy tín của Người Bán thông qua việc đánh giá kém … |

Khoảng cách score top-1 → top-3: **0.022** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 4: Shopee hỗ trợ những phương thức thanh toán nào?**
gold_docs = `['shopee-payment-methods']` | filter = `None` | tự chấm truy xuất: **1/2** (gold ở top-3 nhưng không phải top-1) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-policy::chunk_37` | 0.742 | shopee-return-refund-policy | lệch (được xác định bằng 100% giá trị Sản Phẩm Hoàn Trả trừ đi số tiền đã hoàn … |
| 2 | `shopee-return-refund-policy::chunk_2` | 0.724 | shopee-return-refund-policy | ển và/hoặc các bên có liên quan trong quá trình giải quyết yêu cầu của Người Mu… |
| 3 | `shopee-payment-methods::chunk_2` | 0.720 | shopee-payment-methods | áp dụng cho đơn hàng có giá trị thanh toán (bao gồm phí vận chuyển và các chi p… |

Khoảng cách score top-1 → top-3: **0.022** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 5: Đơn hàng đang giao bị thất lạc thì xử lý ra sao?**
gold_docs = `['shopee-shipping-policy', 'shopee-delivery-process']` | filter = `None` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-shipping-policy::chunk_19` | 0.560 | shopee-shipping-policy | ược bàn giao thành công cho đơn vị vận chuyển: Bưu kiện sẽ được đơn vị vận chuy… |
| 2 | `shopee-delivery-process::chunk_2` | 0.542 | shopee-delivery-process | bất kỳ chi phí vận chuyển nào nếu đơn hàng giao không thành công ⚠️Lưu ý: - Nếu… |
| 3 | `shopee-shipping-policy::chunk_31` | 0.527 | shopee-shipping-policy | g: - Hàng bị thất lạc khi hoàn trả: trong vòng 07 ngày sau khi đơn hàng được cậ… |

Khoảng cách score top-1 → top-3: **0.032** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)
