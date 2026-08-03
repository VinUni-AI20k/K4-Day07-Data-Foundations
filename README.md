# K4 Day 07 — Data Foundations (Bản hoàn thiện T-Hexa)

Bộ nộp này hoàn thành phần code cá nhân, corpus K4, metadata, custom chunker, benchmark và hai báo cáo.

## Kết quả đã kiểm chứng

- 42/42 tests pass.
- 7 tài liệu chính sách/hỗ trợ khách hàng (yêu cầu: 5–10).
- Mỗi tài liệu có `customer_role`, `category`, `source_url`, `retrieved_at`, `document_version`, `language`, `permission`.
- Đúng 5 benchmark queries; câu 4 dùng `metadata_filter={"customer_role": "seller"}`.
- Có custom `HeadingChunker` theo heading/điều khoản.
- Năm cấu hình theo năm thành viên: Heading 29, Recursive 17, Sentence-3 14, FixedSize 14 và Sentence-2 19 chunks; cả năm đạt 10/10 trên benchmark offline.

## Chạy trên Windows bằng Python 3.11

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest tests/ -v
python evaluate_submission.py
python validate_submission.py
```

Kết quả mong đợi: `42 passed` và `SUBMISSION VALID`.

## Demo RAG

Chạy nhanh không cần model thật:

```powershell
copy .env.example .env
python main.py "T-Hexa hỗ trợ phương thức thanh toán nào?"
```

Để demo retrieval semantic tiếng Việt có ý nghĩa hơn:

```powershell
pip install -r requirements-local.txt
$env:EMBEDDING_PROVIDER="local"
python main.py "Khách hàng được đổi trả trong bao lâu?"
```

Lần đầu model đa ngữ sẽ được tải về. Không dùng mock embedding để kết luận strategy nào tốt hơn.

## File quan trọng

- `src/chunking.py`: SentenceChunker, RecursiveChunker, cosine, comparator.
- `src/store.py`: add/search/filter/delete; optional Chroma mirror.
- `src/agent.py`: RAG prompt có context và nguồn.
- `src/custom_chunking.py`: HeadingChunker cho yêu cầu riêng K4.
- `data/k4_ecommerce/`: 7 tài liệu và `sources.csv`.
- `evaluate_submission.py`: benchmark tái lập và tạo `evaluation_results.json`.
- `report/REPORT_CANHAN.md`: báo cáo cá nhân Nguyễn Văn Thành — 2A202601030.
- `report/REPORT_NHOM.md`: báo cáo nhóm đã có đủ 5 thành viên và MSSV.
- `src/Nguyen Van Thanh/`: bộ file cá nhân của Nguyễn Văn Thành để nộp theo cấu trúc yêu cầu.

## Thông tin nhóm 

- Nguyễn Hoàng Hải — 2A202601426
- Nguyễn Văn Thành — 2A202601030
- Nguyễn Duy Khánh — 2A202601530
- Ngô Xuân Ninh — 2A202601068
- Nguyễn Chiến Thắng — 2A202601734

Các nội dung thời hạn đổi trả, xử lý và giao hàng trong corpus là **dữ liệu lab do chủ dự án cho phép**, cần duyệt lại trước khi dùng như chính sách pháp lý chính thức trên website.
