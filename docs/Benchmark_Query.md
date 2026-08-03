# 5 câu hỏi benchmark đề xuất (chốt chung cả nhóm)

| # | Câu hỏi | Gold nằm ở | Ghi chú |
|---|---|---|---|
| 1 | "Tôi nhận hàng bị vỡ thì được hoàn tiền không?" | shopee-return-refund-policy §3.1 | dễ, kiểm tra baseline |
| 2 | "Thời hạn gửi yêu cầu trả hàng là bao lâu?" | return-refund-policy / request-guide | có số → dễ chấm đúng/sai |
| 3 | "Người bán bị cấm đăng bán những mặt hàng nào?" | shopee-seller-listing-rules | bắt buộc `metadata_filter={"customer_role": "seller"}` — thoả quy tắc K4 |
| 4 | "Shopee hỗ trợ những phương thức thanh toán nào?" | shopee-payment-methods | kiểm tra có kéo nhầm doc giao hàng không |
| 5 | "Đơn hàng đang giao bị thất lạc thì xử lý ra sao?" | trải giữa shipping-policy + delivery-process | câu khó: gold nằm ở 2 doc → phân biệt rõ 3 chiến lược |
