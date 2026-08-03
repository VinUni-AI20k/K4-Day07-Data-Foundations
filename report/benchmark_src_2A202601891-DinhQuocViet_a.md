# Benchmark — chiến lược `A-fixed-500/50`

- **Package cá nhân:** `src.2A202601891-DinhQuocViet`
- **Backend nhúng:** `mock embeddings fallback`
- **Corpus:** `data\k4_ecommerce` — 6 tài liệu
- **Chunk:** 172 chunk | dài trung bình 487.7 ký tự (min 58 / max 500)
- **top_k:** 3
- **Mô tả chiến lược:** Cắt cứng 500 ký tự, chồng lấn 50. Không xử lý ranh giới điều khoản, không làm giàu metadata — dùng làm mốc để đo xem B và C cải thiện được bao nhiêu.

> ⚠️ Đang chạy MOCK embedding — điểm số bên dưới KHÔNG phản ánh ngữ nghĩa. Đặt `EMBEDDING_PROVIDER=local` trong `.env` trước khi lấy số cho báo cáo.

## Bảng 1 — Kết quả cá nhân (dán vào REPORT_CANHAN mục 5)

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Liên quan? | Câu trả lời của agent |
|---|---------|----------------------------|-------|------------|------------------------|
| 1 | Tôi nhận hàng bị vỡ thì được hoàn tiền không? | `shopee-shipping-policy::chunk_43` — ẩm tại thời điểm Người Mua đặt hàng là giá bán đã ba… | 0.396 | ❌ | [STUB LLM] đã nhận 1795 ký tự ngữ cảnh |
| 2 | Thời hạn gửi yêu cầu trả hàng là bao lâu? | `shopee-shipping-policy::chunk_45` — 1. Dịch vụ vận chuyển được hỗ trợ trên Sàn TMĐT … | 0.268 | ⚠️ | [STUB LLM] đã nhận 1791 ký tự ngữ cảnh |
| 3 | Người bán bị cấm đăng bán những mặt hàng nào? | `shopee-seller-listing-rules::chunk_2` — n hành. c. Tất cả chứng từ mà Người Bán được yêu… | 0.214 | ✅ | [STUB LLM] đã nhận 1668 ký tự ngữ cảnh |
| 4 | Shopee hỗ trợ những phương thức thanh toán nào? | `shopee-delivery-process::chunk_1` — n thoại/ từ chối nhận hàng hoặc hẹn lại thời gian nh… | 0.366 | ⚠️ | [STUB LLM] đã nhận 1797 ký tự ngữ cảnh |
| 5 | Đơn hàng đang giao bị thất lạc thì xử lý ra sao? | `shopee-return-refund-policy::chunk_32` — uộc một trong các trường hợp sau: Người Bán xác… | 0.305 | ❌ | [STUB LLM] đã nhận 1798 ký tự ngữ cảnh |

**Số câu có chunk liên quan trong top-3: 3/5**
**Điểm truy xuất tự chấm (chưa tính độ đúng của câu trả lời): 4/10**

## Bảng 2 — Có filter vs không filter (REPORT_NHOM mục 3)

| # | metadata_filter | Điểm khi KHÔNG lọc | Điểm khi CÓ lọc | doc_id top-1 (không lọc) | doc_id top-1 (có lọc) |
|---|-----------------|--------------------|-----------------|--------------------------|------------------------|
| 3 | `{'customer_role': 'seller'}` | 0/2 | 2/2 | shopee-return-refund-request-guide | shopee-seller-listing-rules |

## Bảng 3 — Chi tiết top-k từng câu (để phân tích, không cần dán hết)

**Câu 1: Tôi nhận hàng bị vỡ thì được hoàn tiền không?**
gold_docs = `['shopee-return-refund-policy']` | filter = `None` | tự chấm truy xuất: **0/2** (không có gold trong top-3) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-shipping-policy::chunk_43` | 0.396 | shopee-shipping-policy | ẩm tại thời điểm Người Mua đặt hàng là giá bán đã bao gồm mã giảm giá của Người… |
| 2 | `shopee-shipping-policy::chunk_50` | 0.347 | shopee-shipping-policy | (trong trường hợp gửi trả hàng) khiến hàng hóa bên trong bị hư hại. - Trường hợ… |
| 3 | `shopee-shipping-policy::chunk_0` | 0.267 | shopee-shipping-policy | # Chính sách vận chuyển Shopee CHÍNH SÁCH VẬN CHUYỂN SHOPEE A. PHẠM VI VÀ ĐỐI T… |

Khoảng cách score top-1 → top-3: **0.129** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 2: Thời hạn gửi yêu cầu trả hàng là bao lâu?**
gold_docs = `['shopee-return-refund-policy', 'shopee-return-refund-request-guide']` | filter = `None` | tự chấm truy xuất: **1/2** (gold ở top-3 nhưng không phải top-1) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-shipping-policy::chunk_45` | 0.268 | shopee-shipping-policy | 1. Dịch vụ vận chuyển được hỗ trợ trên Sàn TMĐT Shopee không cho phép Người… |
| 2 | `shopee-return-refund-policy::chunk_26` | 0.212 | shopee-return-refund-policy | g do lỗi của Người Mua hoặc đơn vị vận chuyển, đơn giao không thành công, và cá… |
| 3 | `shopee-seller-listing-rules::chunk_6` | 0.207 | shopee-seller-listing-rules | h vi không được thực hiện a. Sử dụng thông tin, hình ảnh, âm thanh vi phạm pháp… |

Khoảng cách score top-1 → top-3: **0.060** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 3: Người bán bị cấm đăng bán những mặt hàng nào?**
gold_docs = `['shopee-seller-listing-rules']` | filter = `{'customer_role': 'seller'}` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ❌

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-seller-listing-rules::chunk_2` | 0.214 | shopee-seller-listing-rules | n hành. c. Tất cả chứng từ mà Người Bán được yêu cầu cung cấp thì Người Bán phả… |
| 2 | `shopee-seller-listing-rules::chunk_21` | 0.209 | shopee-seller-listing-rules | g các quy định dưới đây: + Về nhãn hàng hóa theo quy định của Nghị định 43/2017… |
| 3 | `shopee-seller-listing-rules::chunk_40` | 0.167 | shopee-seller-listing-rules | anh sách các sản phẩm bắt buộc phải có hạn sử dụng trên bao bì a. Dược phẩm b. … |

Khoảng cách score top-1 → top-3: **0.048** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 4: Shopee hỗ trợ những phương thức thanh toán nào?**
gold_docs = `['shopee-payment-methods']` | filter = `None` | tự chấm truy xuất: **1/2** (gold ở top-3 nhưng không phải top-1) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-delivery-process::chunk_1` | 0.366 | shopee-delivery-process | n thoại/ từ chối nhận hàng hoặc hẹn lại thời gian nhận hàng quá xa, đơn vị vận … |
| 2 | `shopee-payment-methods::chunk_8` | 0.262 | shopee-payment-methods | ua sắm trên ứng dụng Shopee, đơn hàng phải có giá trị thanh toán cuối cùng (đã … |
| 3 | `shopee-shipping-policy::chunk_9` | 0.252 | shopee-shipping-policy | hiệm nếu có hư hỏng, tổn thất khi vận chuyển. Shopee được miễn trừ mọi trách nh… |

Khoảng cách score top-1 → top-3: **0.114** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 5: Đơn hàng đang giao bị thất lạc thì xử lý ra sao?**
gold_docs = `['shopee-shipping-policy', 'shopee-delivery-process']` | filter = `None` | tự chấm truy xuất: **0/2** (không có gold trong top-3) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-policy::chunk_32` | 0.305 | shopee-return-refund-policy | uộc một trong các trường hợp sau: Người Bán xác nhận đã nhận được Sản Phẩm Hoàn… |
| 2 | `shopee-seller-listing-rules::chunk_45` | 0.264 | shopee-seller-listing-rules | sử dụng hàng hóa, dịch vụ; (iv) cấn trừ tiền từ Số dư Tài Khoản Shopee, (v) khó… |
| 3 | `shopee-seller-listing-rules::chunk_1` | 0.260 | shopee-seller-listing-rules | ề hàng hóa, dịch vụ để giới thiệu với khách hàng về hàng hóa, dịch vụ đó. b. Kh… |

Khoảng cách score top-1 → top-3: **0.045** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)
