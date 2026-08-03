# Product Finder UI

Flask UI đọc product listing thật từ `data/k4_asos_products`, sau đó dùng LLM để trả lời có căn cứ trên các sản phẩm được truy xuất. Câu trả lời được stream qua SSE, render Markdown đã sanitize ở browser, và bố cục gồm lịch sử chat, hội thoại kèm retrieved context và panel telemetry/product cards.

## Chạy ứng dụng

```powershell
python -m pip install -r ui/requirements.txt
Copy-Item ui/.env.example ui/.env
# Điền OPENAI_API_KEY, OPENAI_BASE_URL và OPENAI_MODEL vào file .env
python -m flask --app ui.app run --debug
```

`OPENAI_BASE_URL` có thể trỏ tới endpoint OpenAI-compatible. API key chỉ được đọc phía server; UI không nhận hoặc lưu key. Hai biến cost là tùy chọn và được dùng để hiển thị ước tính chi phí cho mỗi lần chat.
