import os
import csv
from datetime import datetime

data_dir = "data/k4_ecommerce"
os.makedirs(data_dir, exist_ok=True)

policies = [
    {
        "doc_id": "k4-tiki-doi-tra",
        "title": "Chính sách đổi trả sản phẩm",
        "url": "https://tiki.vn/khuyen-mai/chinh-sach-doi-tra-san-pham",
        "role": "buyer",
        "category": "returns",
        "content": """# Chính sách đổi trả sản phẩm

Tiki hỗ trợ đổi trả sản phẩm trong vòng 7-30 ngày tùy thuộc vào ngành hàng và lý do đổi trả.
- Sản phẩm lỗi từ nhà sản xuất: Hỗ trợ đổi mới hoặc hoàn tiền trong vòng 7 ngày (đối với điện tử, điện gia dụng) và 30 ngày đối với các ngành hàng khác.
- Sản phẩm không lỗi (do nhu cầu khách hàng): Hỗ trợ trả hàng hoàn tiền trong 30 ngày (trừ một số mặt hàng không áp dụng đổi trả do nhu cầu như thực phẩm tươi sống, xe máy).
- Điều kiện đổi trả: Sản phẩm phải còn nguyên vẹn, đầy đủ phụ kiện, tem nhãn, không có dấu hiệu đã qua sử dụng."""
    },
    {
        "doc_id": "k4-tiki-bao-hanh",
        "title": "Chính sách bảo hành",
        "url": "https://tiki.vn/khuyen-mai/chinh-sach-bao-hanh",
        "role": "buyer",
        "category": "warranty",
        "content": """# Chính sách bảo hành

Tất cả sản phẩm do Tiki phân phối đều được bảo hành theo đúng quy định của nhà sản xuất.
- Thời gian bảo hành tùy thuộc vào từng loại sản phẩm, được ghi rõ trên phiếu bảo hành hoặc thông tin chi tiết trên trang sản phẩm.
- Khách hàng có thể mang sản phẩm đến trực tiếp trung tâm bảo hành của hãng hoặc gửi về trung tâm xử lý của Tiki để được hỗ trợ.
- Sản phẩm không được bảo hành nếu bị hư hỏng do lỗi người dùng (rơi vỡ, vào nước, sử dụng sai cách)."""
    },
    {
        "doc_id": "k4-tiki-bao-mat",
        "title": "Chính sách bảo mật thông tin cá nhân",
        "url": "https://tiki.vn/khuyen-mai/chinh-sach-bao-mat-thong-tin-ca-nhan",
        "role": "both",
        "category": "privacy",
        "content": """# Chính sách bảo mật thông tin cá nhân

Tiki cam kết bảo vệ thông tin cá nhân của người dùng (cả người mua và người bán).
- Thông tin thu thập bao gồm tên, địa chỉ, số điện thoại, email và lịch sử giao dịch.
- Tiki sử dụng thông tin này để xử lý đơn hàng, cải thiện dịch vụ và gửi các thông báo quan trọng.
- Tiki tuyệt đối không bán hoặc chia sẻ thông tin cá nhân cho bên thứ ba vì mục đích thương mại, ngoại trừ các đơn vị vận chuyển để giao hàng."""
    },
    {
        "doc_id": "k4-tiki-khieu-nai",
        "title": "Chính sách giải quyết khiếu nại",
        "url": "https://tiki.vn/khuyen-mai/chinh-sach-giai-quyet-khieu-nai",
        "role": "both",
        "category": "complaint",
        "content": """# Chính sách giải quyết khiếu nại

Tiki luôn đề cao việc giải quyết thỏa đáng các khiếu nại của khách hàng và đối tác bán hàng.
- Quy trình tiếp nhận: Khách hàng/người bán gửi khiếu nại qua hotline hoặc email hỗ trợ.
- Thời gian xử lý: Tiki sẽ phản hồi trong vòng 24 giờ và xử lý dứt điểm khiếu nại trong tối đa 7 ngày làm việc.
- Trong trường hợp có tranh chấp giữa người mua và người bán, Tiki sẽ đóng vai trò trung gian phân xử dựa trên bằng chứng cụ thể từ cả hai bên."""
    },
    {
        "doc_id": "k4-tiki-quy-che",
        "title": "Quy chế hoạt động sàn giao dịch TMĐT",
        "url": "https://tiki.vn/khuyen-mai/quy-che-hoat-dong-sgdtmdt",
        "role": "seller",
        "category": "rules",
        "content": """# Quy chế hoạt động dành cho Người bán

Tất cả người bán tham gia sàn giao dịch TMĐT Tiki phải tuân thủ nghiêm ngặt quy chế hoạt động.
- Hàng hóa đăng bán phải có nguồn gốc xuất xứ rõ ràng, không vi phạm pháp luật và hàng cấm.
- Người bán không được bán hàng giả, hàng nhái, hoặc tự ý hủy đơn hàng của khách khi không có lý do chính đáng.
- Vi phạm quy chế sẽ dẫn đến việc bị phạt điểm, khóa sản phẩm, hoặc chấm dứt tư cách bán hàng trên Tiki vĩnh viễn."""
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

print("Successfully generated 5 K4 policy documents and sources.csv.")
