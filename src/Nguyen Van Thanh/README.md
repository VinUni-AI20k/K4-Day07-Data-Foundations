# Hồ sơ cá nhân — Nguyễn Văn Thành

- **Họ tên:** Nguyễn Văn Thành
- **MSSV:** 2A202601030
- **Nhóm:** T-Hexa
- **Bài:** K4 Day 07 — Data Foundations, Embedding & Vector Store

Thư mục này tập hợp các file cá nhân cần nộp của Nguyễn Văn Thành theo yêu cầu đặt trong `src/Nguyen Van Thanh/`.

## Nội dung

- `REPORT_CANHAN.md`: báo cáo cá nhân hoàn chỉnh.
- `chunking.py`: phần cài đặt SentenceChunker, RecursiveChunker, cosine similarity và comparator.
- `store.py`: phần cài đặt EmbeddingStore.
- `agent.py`: phần cài đặt KnowledgeBaseAgent.
- `custom_chunking.py`: HeadingChunker — chiến lược cá nhân của Nguyễn Văn Thành.
- `embeddings.py`, `models.py`, `__init__.py`: các thành phần phụ thuộc để đối chiếu mã nguồn.
- `test_output.txt`: bằng chứng 42/42 tests pass.
- `evaluation_results.json`: kết quả benchmark truy xuất.

Mã nguồn chạy chính vẫn nằm trực tiếp trong `src/`; các file ở thư mục này là bản sao hồ sơ cá nhân để nộp và đối chiếu, tránh làm thay đổi import của test suite.
