# Hồ sơ cá nhân - Nguyễn Duy Khánh

**Họ tên:** Nguyễn Duy Khánh  
**MSSV:** 2A202601530  
**Nhóm:** T-Hexa  
**Bài:** K4 Day 07 - Data Foundations, Embedding & Vector Store

Thư mục này tập hợp các file cá nhân cần nộp của Nguyễn Duy Khánh theo yêu cầu đặt trong `2A202601530_NguyenDuyKhanh/`.

## Nội dung

- `REPORT_CANHAN.md`: báo cáo cá nhân hoàn chỉnh.
- `chunking.py`: phần cài đặt `SentenceChunker`, `RecursiveChunker`, cosine similarity và comparator.
- `store.py`: phần cài đặt `EmbeddingStore`.
- `agent.py`: phần cài đặt `KnowledgeBaseAgent`.
- `embeddings.py`, `models.py`, `__init__.py`: các thành phần phụ thuộc để đối chiếu mã nguồn.
- `test_output.txt`: bằng chứng 42/42 tests pass nếu cần nộp kèm log test.
- `evaluation_results.json`: kết quả benchmark truy xuất nếu nhóm/cá nhân chạy đánh giá riêng.

Mã nguồn chạy chính của bài lab vẫn nằm trực tiếp trong `src/`; các file ở thư mục này là bản sao hồ sơ cá nhân để nộp và đối chiếu, tránh làm thay đổi import mặc định của test suite.
