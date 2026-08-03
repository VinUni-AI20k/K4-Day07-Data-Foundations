# Bộ benchmark — Chính sách Shopee Việt Nam

Corpus này gồm 6 trang chính sách công khai của Trung tâm trợ giúp Shopee,
được thu thập ngày 2026-08-03. Mỗi câu dưới đây chỉ được chấm theo thông tin
có trong các file Markdown tại `data/shopee_policy/`; không bổ sung kiến thức
ngoài corpus.

| # | Câu hỏi | Metadata filter | Gold answer | Tài liệu/chunk kỳ vọng |
|---|---|---|---|---|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng/hoàn tiền sau khi đơn giao thành công? Trường hợp thực phẩm tươi sống hoặc đông lạnh thì sao? | Không | Với sản phẩm thông thường là 15 ngày; thực phẩm tươi sống và đông lạnh là 24 giờ kể từ khi đơn được cập nhật giao hàng thành công. | `shopee-return-refund-policy.md`, mục 3.2 |
| 2 | Khi không đồng ý với quyết định hoàn tiền hoặc có vấn đề với hàng hoàn, người bán phải phản hồi trong bao lâu? | Không | Người bán phải phản hồi trong vòng 2 ngày lịch kể từ ngày nhận thông báo của Shopee; quá hạn được hiểu là đồng ý với quyết định xử lý. | `shopee-return-refund-policy.md`, mục 5 |
| 3 | Nếu người mua tự sắp xếp gửi hàng hoàn cho đơn không thuộc Shopee Mall, mức hỗ trợ phí là bao nhiêu? | `{"customer_role": "buyer"}` | Sau khi yêu cầu được chấp nhận và đáp ứng điều kiện hỗ trợ, hoàn 25.000 Shopee Xu nếu cùng tỉnh/thành phố với người bán, hoặc 40.000 Shopee Xu nếu khác tỉnh/thành phố. | `shopee-return-shipping.md`, mục 2.2 |
| 4 | Người bán cần bảo đảm gì về ảnh thật của sản phẩm khi đăng bán? | `{"customer_role": "seller"}` | Phải có ít nhất một ảnh thật do chính người bán tự chụp; diện tích sản phẩm thật phải chiếm ít nhất 40% diện tích toàn ảnh. | `shopee-listing-regulations.md`, mục C.1.b |
| 5 | Khoản tiền người mua đã thanh toán được lưu ở đâu trước khi chuyển cho người bán, và một trường hợp nào khiến tiền được hoàn cho người mua? | Không | Tiền được lưu trong Tài Khoản Đảm Bảo Shopee. Nếu yêu cầu trả hàng/hoàn tiền được Shopee chấp thuận, Shopee hoàn tiền cho người mua và chuyển phần còn lại (nếu có) cho người bán. | `shopee-terms-of-service.md`, mục 11.1–11.2 |

## Quy tắc chấm

- **2 điểm:** top-3 có chunk đúng và câu trả lời nêu đủ gold answer.
- **1 điểm:** có chunk đúng nhưng câu trả lời thiếu ý quan trọng, hoặc chunk đúng không ở top-1.
- **0 điểm:** không có chunk đúng trong top-3.

Khi chạy câu 3 hoặc 4, dùng `search_with_filter()` với đúng filter trong bảng.
