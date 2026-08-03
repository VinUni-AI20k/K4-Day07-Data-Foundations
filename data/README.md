# Hướng dẫn crawl dữ liệu Shopee

Chạy từ thư mục gốc repository:

```bash
uv sync
uv run python data/crawl_data.py
```

Mặc định, script tải 7 bài viết công khai về chính sách Trả hàng / Hoàn tiền từ Trung tâm trợ giúp Shopee Việt Nam.

Dữ liệu HTML và metadata nguồn được lưu tại:

```text
.crawl_cache/shopee-returns/
```

Thư mục `.crawl_cache/` đã được thêm vào `.gitignore` và không được commit lên repository.

## Crawl URL khác

Dùng `--url` nhiều lần để crawl danh sách bài viết riêng:

```bash
uv run python data/crawl_data.py \
  --url "https://help.shopee.vn/portal/4/article/ARTICLE_ID_1" \
  --url "https://help.shopee.vn/portal/4/article/ARTICLE_ID_2"
```

Các tùy chọn:

```text
--output-dir PATH   Thư mục lưu HTML và metadata
--delay SECONDS     Thời gian chờ giữa các request, tối thiểu 1 giây
--timeout SECONDS   Thời gian chờ tối đa cho mỗi request
```

Ví dụ:

```bash
uv run python data/crawl_data.py --delay 2 --timeout 45
```

Crawler kiểm tra `robots.txt`, dùng User-Agent của lớp và chỉ tải các trang công khai. Không sử dụng script cho nội dung yêu cầu đăng nhập, CAPTCHA hoặc nguồn không cho phép crawl.
