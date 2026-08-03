# Thu thập dữ liệu chính sách Shopee

## Phạm vi

Hai script trong thư mục này tạo corpus Giai đoạn 2 K4 về chính sách Trả hàng / Hoàn tiền của Trung tâm trợ giúp Shopee Việt Nam.

- `crawl_data.py`: tải các bài viết công khai dạng HTML.
- `preprocess.py`: làm sạch nội dung, gắn metadata K4 và cập nhật `sources.csv`.

Crawler kiểm tra `robots.txt`, dùng User-Agent của lớp và chờ tối thiểu một giây giữa các request. Chỉ sử dụng nguồn công khai; không đăng nhập, vượt CAPTCHA hoặc né giới hạn truy cập.

## Cách chạy

Từ thư mục gốc repository:

```bash
uv sync
uv run python data/crawl_data.py
uv run python data/preprocess.py
```

Crawler mặc định tải 7 URL bài viết `/portal/4/article/...`. Trang danh mục Shopee là ứng dụng JavaScript, nên crawler dùng các URL bài viết server-rendered được khai báo trong `crawl_data.py`.

Raw HTML và metadata được lưu trong `.crawl_cache/shopee-returns/`. Thư mục này bị ignore và không đưa vào corpus nộp bài.

## Kết quả

Preprocess tạo các file `shopee-returns-*.md` và `sources.csv` trong `data/k4_ecommerce/`. Mỗi Markdown có `doc_id`, `title`, `source_url`, `retrieved_at`, `document_version`, `customer_role`, `category` và `language`.

Kiểm tra nhanh:

```bash
uv run python - <<'PY'
from ingest import load_documents
docs = load_documents("data/k4_ecommerce")
print(f"Documents: {len(docs)}")
for doc in docs:
    print(doc.id, len(doc.content), doc.metadata.get("customer_role"))
PY
```

## Thêm nguồn

Truyền URL bài viết khác bằng cách lặp `--url`:

```bash
uv run python data/crawl_data.py \
  --url "https://help.shopee.vn/portal/4/article/ARTICLE_ID" \
  --url "https://help.shopee.vn/portal/4/article/ANOTHER_ID"
```

Sau đó chạy lại `preprocess.py`. Trước benchmark, kiểm tra corpus có 5–10 nguồn thật và không còn tài liệu mẫu `example.com`.
