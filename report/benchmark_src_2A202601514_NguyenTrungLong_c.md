# Benchmark — chiến lược `C-sentence-3-context`

- **Package cá nhân:** `src.2A202601514_NguyenTrungLong`
- **Backend nhúng:** `text-embedding-3-small`
- **Corpus:** `data/k4_ecommerce` — 6 tài liệu
- **Chunk:** 257 chunk | dài trung bình 349.8 ký tự (min 60 / max 1136)
- **top_k:** 5
- **Mô tả chiến lược:** Chia tối đa 3 câu/đơn vị danh sách theo từng section, rồi prepend [title > section] trước khi embed. Lấy top-5 và bỏ kết quả yếu bằng ngưỡng score >= max(0.30, top-1 - 0.12).

## Bảng 1 — Kết quả cá nhân (dán vào REPORT_CANHAN mục 5)

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Liên quan? | Câu trả lời của agent |
|---|---------|----------------------------|-------|------------|------------------------|
| 1 | Tôi nhận hàng bị vỡ thì được hoàn tiền không? | `shopee-return-refund-request-guide::chunk_2::78` — [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn … | 0.646 | ❌ | [STUB LLM] đã nhận 1433 ký tự ngữ cảnh |
| 2 | Thời hạn gửi yêu cầu trả hàng là bao lâu? | `shopee-return-refund-request-guide::chunk_7::83` — [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn … | 0.742 | ✅ | [STUB LLM] đã nhận 1369 ký tự ngữ cảnh |
| 3 | Người bán bị cấm đăng bán những mặt hàng nào? | `shopee-seller-listing-rules::chunk_5::92` — [Quy định đăng bán sản phẩm trên Shopee > 2.… | 0.592 | ✅ | [STUB LLM] đã nhận 2787 ký tự ngữ cảnh |
| 4 | Shopee hỗ trợ những phương thức thanh toán nào? | `shopee-payment-methods::chunk_5::13` — [Shopee hiện đang có những phương thức thanh toán… | 0.795 | ✅ | [STUB LLM] đã nhận 1380 ký tự ngữ cảnh |
| 5 | Đơn hàng đang giao bị thất lạc thì xử lý ra sao? | `shopee-return-refund-request-guide::chunk_2::78` — [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn … | 0.627 | ⚠️ | [STUB LLM] đã nhận 2836 ký tự ngữ cảnh |

**Số câu có chunk liên quan trong top-5: 4/5**
**Điểm truy xuất tự chấm (chưa tính độ đúng của câu trả lời): 7/10**

## Bảng 2 — Có filter vs không filter (REPORT_NHOM mục 3)

| # | metadata_filter | Điểm khi KHÔNG lọc | Điểm khi CÓ lọc | doc_id top-1 (không lọc) | doc_id top-1 (có lọc) |
|---|-----------------|--------------------|-----------------|--------------------------|------------------------|
| 3 | `{'customer_role': 'seller'}` | 2/2 | 2/2 | shopee-seller-listing-rules | shopee-seller-listing-rules |

## Bảng 3 — Chi tiết top-k từng câu (để phân tích, không cần dán hết)

**Câu 1: Tôi nhận hàng bị vỡ thì được hoàn tiền không?**
gold_docs = `['shopee-return-refund-policy']` | filter = `None` | tự chấm truy xuất: **0/2** (không có gold trong top-3) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-request-guide::chunk_2::78` | 0.646 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > Bước 3: Chọn tình huống bạn đang gặ… |
| 2 | `shopee-return-refund-request-guide::chunk_9::85` | 0.607 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > 2. Lưu ý] Để tìm hiểu thêm về thời … |
| 3 | `shopee-return-refund-request-guide::chunk_10::86` | 0.584 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > 2. Lưu ý] Sản phẩm sẽ được Người bá… |
| 4 | `shopee-shipping-policy::chunk_61::232` | 0.577 | shopee-shipping-policy | [Chính sách vận chuyển Shopee > 3. Bằng chứng khiếu nại:] a. Khiếu nại với đơn … |
| 5 | `shopee-shipping-policy::chunk_55::226` | 0.570 | shopee-shipping-policy | [Chính sách vận chuyển Shopee > 1. Thời hạn khiếu nại:] Khiếu nại với đơn trả h… |

Khoảng cách score top-1 → top-5: **0.076** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 2: Thời hạn gửi yêu cầu trả hàng là bao lâu?**
gold_docs = `['shopee-return-refund-policy', 'shopee-return-refund-request-guide']` | filter = `None` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-request-guide::chunk_7::83` | 0.742 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > 2. Lưu ý] Thời gian xử lý. Yêu cầu … |
| 2 | `shopee-return-refund-request-guide::chunk_9::85` | 0.659 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > 2. Lưu ý] Để tìm hiểu thêm về thời … |
| 3 | `shopee-return-refund-request-guide::chunk_8::84` | 0.653 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > 2. Lưu ý] Shopee sẽ thông báo kết q… |
| 4 | `shopee-return-refund-policy::chunk_6::34` | 0.627 | shopee-return-refund-policy | [Chính sách trả hàng và hoàn tiền Shopee > 3. ĐIỀU KIỆN YÊU CẦU TRẢ HÀNG/HOÀN T… |

Khoảng cách score top-1 → top-4: **0.115** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 3: Người bán bị cấm đăng bán những mặt hàng nào?**
gold_docs = `['shopee-seller-listing-rules']` | filter = `{'customer_role': 'seller'}` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-seller-listing-rules::chunk_5::92` | 0.592 | shopee-seller-listing-rules | [Quy định đăng bán sản phẩm trên Shopee > 2. Các nội dung không được phép đăng … |
| 2 | `shopee-seller-listing-rules::chunk_9::96` | 0.573 | shopee-seller-listing-rules | [Quy định đăng bán sản phẩm trên Shopee > 2. Các nội dung không được phép đăng … |
| 3 | `shopee-seller-listing-rules::chunk_17::104` | 0.563 | shopee-seller-listing-rules | [Quy định đăng bán sản phẩm trên Shopee > 3. Các hành vi không được thực hiện] … |
| 4 | `shopee-seller-listing-rules::chunk_81::168` | 0.560 | shopee-seller-listing-rules | [Quy định đăng bán sản phẩm trên Shopee > E. XỬ LÝ VI PHẠM] Người Bán vi phạm m… |
| 5 | `shopee-seller-listing-rules::chunk_12::99` | 0.556 | shopee-seller-listing-rules | [Quy định đăng bán sản phẩm trên Shopee > 3. Các hành vi không được thực hiện] … |

Khoảng cách score top-1 → top-5: **0.035** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 4: Shopee hỗ trợ những phương thức thanh toán nào?**
gold_docs = `['shopee-payment-methods']` | filter = `None` | tự chấm truy xuất: **2/2** (top-1 đúng tài liệu gold) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-payment-methods::chunk_5::13` | 0.795 | shopee-payment-methods | [Shopee hiện đang có những phương thức thanh toán nào? > 2. Thẻ Tín dụng/Ghi nợ… |
| 2 | `shopee-payment-methods::chunk_1::9` | 0.790 | shopee-payment-methods | [Shopee hiện đang có những phương thức thanh toán nào? > Shopee hiện đang có nh… |
| 3 | `shopee-payment-methods::chunk_3::11` | 0.778 | shopee-payment-methods | [Shopee hiện đang có những phương thức thanh toán nào? > Shopee hiện đang có nh… |
| 4 | `shopee-payment-methods::chunk_2::10` | 0.776 | shopee-payment-methods | [Shopee hiện đang có những phương thức thanh toán nào? > Shopee hiện đang có nh… |
| 5 | `shopee-payment-methods::chunk_0::8` | 0.775 | shopee-payment-methods | [Shopee hiện đang có những phương thức thanh toán nào? > Shopee hiện đang có nh… |

Khoảng cách score top-1 → top-5: **0.021** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)

**Câu 5: Đơn hàng đang giao bị thất lạc thì xử lý ra sao?**
gold_docs = `['shopee-shipping-policy', 'shopee-delivery-process']` | filter = `None` | tự chấm truy xuất: **1/2** (gold ở top-3 nhưng không phải top-1) | agent nhét ngữ cảnh: ✅

| # | chunk_id | score | doc_id | trích 80 ký tự |
|---|----------|-------|--------|----------------|
| 1 | `shopee-return-refund-request-guide::chunk_2::78` | 0.627 | shopee-return-refund-request-guide | [Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền > Bước 3: Chọn tình huống bạn đang gặ… |
| 2 | `shopee-shipping-policy::chunk_62::233` | 0.590 | shopee-shipping-policy | [Chính sách vận chuyển Shopee > 3. Bằng chứng khiếu nại:] Khiếu nại vận chuyển … |
| 3 | `shopee-delivery-process::chunk_3::3` | 0.582 | shopee-delivery-process | [Cách đơn vị vận chuyển giao hàng cho Người mua > 1. Đơn vị vận chuyển giao hàn… |
| 4 | `shopee-shipping-policy::chunk_56::227` | 0.567 | shopee-shipping-policy | [Chính sách vận chuyển Shopee > 1. Thời hạn khiếu nại:] Đơn được cập nhật trạng… |
| 5 | `shopee-delivery-process::chunk_7::7` | 0.566 | shopee-delivery-process | [Cách đơn vị vận chuyển giao hàng cho Người mua > 2. Người mua có được kiểm hàn… |

Khoảng cách score top-1 → top-5: **0.061** (càng lớn càng dễ phân biệt tín hiệu / nhiễu)
