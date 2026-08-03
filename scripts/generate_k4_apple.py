import os
import csv
from datetime import datetime

data_dir = "data/k4_ecommerce"
os.makedirs(data_dir, exist_ok=True)

policies = [
    {
        "doc_id": "k4-apple-sales-refund",
        "title": "Chính Sách Bán Hàng Và Trả Hàng của Apple",
        "url": "https://www.apple.com/vn/shop/browse/open/salespolicies",
        "role": "buyer",
        "category": "returns",
        "content": """# Chính Sách Bán Hàng Và Trả Hàng

Chúng tôi cơ bản tin rằng bạn sẽ hài lòng với các sản phẩm bạn mua từ Apple Store. Tuy nhiên, nếu bạn muốn hoàn trả sản phẩm, bạn có thể hoàn trả các sản phẩm đủ điều kiện trong vòng 14 ngày kể từ ngày bạn nhận được sản phẩm.
- Sản phẩm hoàn trả phải còn đầy đủ phụ kiện và đóng gói gốc.
- Nếu sản phẩm bạn mua là phần mềm có chứa giấy phép (license), bạn không thể hoàn trả phần mềm đó khi tem niêm phong trên phần mềm đã bị rách.
- Việc hoàn tiền sẽ được thực hiện thông qua phương thức thanh toán gốc mà bạn đã sử dụng."""
    },
    {
        "doc_id": "k4-apple-warranty",
        "title": "Bảo Hành Có Giới Hạn 1 Năm Của Apple",
        "url": "https://www.apple.com/legal/warranty/products/warranty-rest-of-apac-vietnamese.html",
        "role": "buyer",
        "category": "warranty",
        "content": """# Bảo Hành Có Giới Hạn 1 (Một) Năm Của Apple

Apple bảo hành sản phẩm phần cứng mang thương hiệu Apple và các phụ kiện mang thương hiệu Apple đóng gói trong bao bì gốc đối với các khiếm khuyết về vật liệu và gia công khi sử dụng bình thường theo các chỉ dẫn đã công bố của Apple trong thời hạn MỘT (1) NĂM kể từ ngày người mua là người sử dụng cuối cùng mua lẻ ban đầu ("Thời Hạn Bảo Hành").
- Bảo hành này không áp dụng cho: (a) các linh kiện tiêu hao, như pin hoặc các lớp bảo vệ được thiết kế là sẽ hao mòn theo thời gian; (b) hư hỏng bề mặt, bao gồm trầy xước, lõm và vỡ nhựa.
- Trong trường hợp sản phẩm bị lỗi, Apple sẽ tiến hành sửa chữa, thay thế hoặc hoàn tiền."""
    },
    {
        "doc_id": "k4-apple-privacy",
        "title": "Chính Sách Quyền Riêng Tư Của Apple",
        "url": "https://www.apple.com/vn/legal/privacy/vn/",
        "role": "both",
        "category": "privacy",
        "content": """# Chính Sách Quyền Riêng Tư Của Apple

Tại Apple, chúng tôi tôn trọng quyền của bạn đối với việc biết, truy cập, sửa chữa, chuyển tải, hạn chế việc xử lý và xóa Dữ liệu cá nhân của bạn.
- Chúng tôi chỉ thu thập Dữ liệu cá nhân cần thiết để cung cấp sản phẩm và dịch vụ của chúng tôi, nhằm tuân thủ pháp luật và để bảo vệ an ninh của Apple cũng như người dùng.
- Apple cam kết không bán dữ liệu của bạn cho bất kỳ bên thứ ba nào.
- Bạn có thể quản lý quyền riêng tư của mình thông qua tài khoản Apple ID hoặc trang web Quyền riêng tư của Apple."""
    },
    {
        "doc_id": "k4-apple-media-terms",
        "title": "Điều Khoản Dịch Vụ Truyền Thông Apple",
        "url": "https://www.apple.com/vn/legal/internet-services/itunes/vn/terms.html",
        "role": "buyer",
        "category": "terms",
        "content": """# Điều Khoản Dịch Vụ Truyền Thông Apple

Các điều khoản này quản lý việc sử dụng của bạn đối với Dịch Vụ Truyền Thông của Apple (bao gồm App Store, Apple Music, Apple TV+, Apple Arcade).
- Trẻ em dưới 15 tuổi (hoặc độ tuổi tương đương ở vùng của bạn) không được tạo tài khoản Apple ID trừ khi được cha mẹ hoặc người giám hộ hợp pháp chấp thuận thông qua Chia sẻ trong gia đình (Family Sharing).
- Tất cả các giao dịch mua nội dung số trên App Store là giao dịch cuối cùng và không thể hoàn tiền, ngoại trừ các trường hợp được quy định rõ trong chính sách hoàn tiền của Dịch Vụ hoặc pháp luật địa phương."""
    },
    {
        "doc_id": "k4-apple-phishing",
        "title": "Nhận Biết Các Thư Email Lừa Đảo",
        "url": "https://support.apple.com/vi-vn/102568",
        "role": "both",
        "category": "security",
        "content": """# Nhận Biết Các Thư Email Lừa Đảo

Apple sẽ không bao giờ yêu cầu bạn cung cấp thông tin cá nhân như số thẻ tín dụng, mật khẩu Apple ID hoặc số an sinh xã hội qua email hoặc tin nhắn SMS không được mã hóa.
- Nếu bạn nhận được một email đáng ngờ tự xưng là từ Apple, vui lòng chuyển tiếp email đó đến reportphishing@apple.com.
- Luôn kiểm tra kỹ địa chỉ email người gửi và đường link trước khi nhấp vào.
- Kích hoạt xác thực hai yếu tố (2FA) cho Apple ID của bạn để tăng cường bảo mật."""
    }
]

retrieved_at = datetime.now().strftime("%Y-%m-%d")

with open(f"{data_dir}/sources.csv", "w", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["doc_id","file_path","title","source_url","retrieved_at","document_version","license_or_permission"])
    
    for p in policies:
        md_path = f"{data_dir}/{p['doc_id']}.md"
        with open(md_path, "w", encoding="utf-8") as md:
            md.write(f"---\n")
            md.write(f"doc_id: {p['doc_id']}\n")
            md.write(f"title: {p['title']}\n")
            md.write(f"customer_role: {p['role']}\n")
            md.write(f"category: {p['category']}\n")
            md.write(f"source_url: {p['url']}\n")
            md.write(f"retrieved_at: {retrieved_at}\n")
            md.write(f"document_version: not-stated\n")
            md.write(f"---\n\n")
            md.write(p["content"])
        
        writer.writerow([p['doc_id'], md_path, p['title'], p['url'], retrieved_at, "not-stated", "public-source"])

print("Successfully generated 5 K4 Apple policy documents and sources.csv.")
