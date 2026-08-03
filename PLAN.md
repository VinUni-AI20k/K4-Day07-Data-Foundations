# PLAN.md — Kế hoạch làm Lab 07 (K4: Embedding & Vector Store — Chính sách TMĐT)

> File kế hoạch cá nhân, tổng hợp từ README.md, exercises.md, K4_VARIANT.md, docs/SCORING.md, docs/DATA_COLLECTION.md, docs/EVALUATION.md.
> Sinh viên: Trịnh Hải Đăng — MSSV 2A202601602 — Lớp K4
> Nộp bài trong: `Trinh-Hai-Dang-2A202601602/`

---

## 0. Việc cần làm ngay: chuẩn bị folder nộp bài — ĐÃ XONG

- [x] Tạo folder `Trinh-Hai-Dang-2A202601602/` ở root repo
- [x] Copy `src/`, `tests/`, `ingest.py`, `main.py`, `data/`, `report/`, `requirements.txt`, `requirements-local.txt`, `.env.example` vào đó

```
Trinh-Hai-Dang-2A202601602/
├── src/                  ← chunking.py, store.py, agent.py, embeddings.py, models.py (đã hoàn thành TODO)
├── tests/                ← test_solution.py — KHÔNG sửa file test
├── ingest.py             ← pipeline đã cung cấp sẵn
├── main.py
├── data/                 ← dữ liệu mẫu có sẵn; cần thêm data/<ten-chu-de>/ của nhóm (Bước 4)
├── report/
│   ├── REPORT_NHOM.md    ← chưa điền
│   └── REPORT_CANHAN.md  ← chưa điền (phần của Đăng)
├── requirements.txt
├── requirements-local.txt
└── .env.example          ← đổi tên thành .env khi cần EMBEDDING_PROVIDER=local (Bước 5)
```

Toàn bộ code TODO viết trực tiếp trong `Trinh-Hai-Dang-2A202601602/src/`. Chạy test bằng:

```bash
cd Trinh-Hai-Dang-2A202601602
python -m pytest tests/ -v
```

---

## 1. Tổng quan cấu trúc điểm (100đ)

| Phần | Điểm | Nộp ở đâu |
|---|---|---|
| Code core (`src/`) pass test | 30 | `Trinh-Hai-Dang-2A202601602/src/` |
| Hướng tiếp cận (giải thích code) | 10 | `REPORT_CANHAN.md` §2 |
| Kết quả truy xuất (5 câu benchmark) | 10 | `REPORT_CANHAN.md` §5 |
| Khởi động (cosine + chunking math) | 5 | `REPORT_CANHAN.md` §1 |
| Dự đoán similarity (5 cặp câu) | 5 | `REPORT_CANHAN.md` §4 |
| **Cá nhân** | **60** | |
| Thiết kế chiến lược (nhóm) | 15 | `REPORT_NHOM.md` §2 |
| Chất lượng bộ tài liệu (nhóm) | 10 | `REPORT_NHOM.md` §1 |
| Chất lượng truy xuất (nhóm) | 10 | `REPORT_NHOM.md` §3 |
| Demo | 5 | `REPORT_NHOM.md` §4 |
| **Nhóm** | **40** | |

---

## 2. Thứ tự công việc (làm theo đúng thứ tự này)

### Bước 1 — Setup môi trường — ĐÃ XONG
- [x] Cài `pytest`, `python-dotenv` trong `Trinh-Hai-Dang-2A202601602/`
- [x] Chạy `pytest tests/ -v` baseline (TODO chưa làm → nhiều test fail, đúng kỳ vọng)

### Bước 2 — Khởi động lý thuyết (Bài 1.1, 1.2 — 5đ) — ĐÃ XONG
- [x] Giải thích cosine similarity (khái niệm, ví dụ cao/thấp, vì sao ưu tiên hơn Euclidean) → `REPORT_CANHAN.md` Phần 1
- [x] Bài toán chunk: `ceil((10000-50)/(500-50))=23`, `overlap=100 → 25` — đã verify khớp `FixedSizeChunker` thật

### Bước 3 — Lập trình cốt lõi cá nhân (30đ) — CODE XONG, REPORT CHƯA
1. [x] `src/chunking.py`
   - [x] `SentenceChunker` (tách theo câu, gộp lại thành chunk)
   - [x] `RecursiveChunker` (thử separator theo thứ tự, đệ quy nếu đoạn còn quá lớn)
   - [x] `compute_similarity` (cosine, có guard chia-cho-0)
   - [x] `ChunkingStrategyComparator` (gọi cả 3 chiến lược + tính thống kê)
2. [x] `src/store.py` — `EmbeddingStore`
   - [x] `__init__` (khởi tạo in-memory, fallback nếu không có ChromaDB)
   - [x] `add_documents` (embed + lưu)
   - [x] `search` (embed query, rank theo dot product)
   - [x] `get_collection_size`
   - [x] `search_with_filter` (lọc metadata trước, search sau)
   - [x] `delete_document`
3. [x] `src/agent.py` — `KnowledgeBaseAgent.answer` (retrieve → build prompt → gọi LLM)
4. [x] `pytest tests/ -v` → **42/42 PASS**
- [x] Viết `REPORT_CANHAN.md` Phần 2 (hướng tiếp cận từng phần)

### Bước 4 — Chuẩn bị dữ liệu nhóm (song song với nhóm, Bài 3.0) — DỮ LIỆU XONG, REPORT CHƯA
- [x] Đọc `docs/DATA_COLLECTION.md` + `K4_VARIANT.md` (bắt buộc: `customer_role`, `source_url`, `retrieved_at`, `document_version`)
- [x] Phạm vi đã chọn: **1 nguồn duy nhất — Shopee (help.shopee.vn)**, kết hợp 3 mảng đổi trả + người bán + thanh toán/giao hàng (đã cân nhắc và loại phương án trộn nhiều sàn vì không nhất quán)
- [x] Thu thập đủ **10 tài liệu** (đề cho khoảng 5-10 → luôn làm mức tối đa) vào `data/k4_ecommerce/`, kèm `sources.csv` đủ 10 dòng:
  1. `return-refund-policy` (buyer) — Chính sách trả hàng và hoàn tiền
  2. `return-refund-general-rules` (buyer) — Quy định chung trả hàng/hoàn tiền
  3. `return-shipping-fee` (buyer) — Phương thức gửi hàng hoàn trả & phí hoàn trả
  4. `seller-listing-rules` (seller) — Quy định đăng bán sản phẩm
  5. `marketplace-operating-regulation` (both) — Quy chế hoạt động sàn TMĐT
  6. `restricted-products-policy` (seller) — Chính sách cấm/hạn chế sản phẩm
  7. `payment-methods` (buyer) — Các phương thức thanh toán
  8. `shipping-fee-discount-program` (seller) — Điều khoản ưu đãi phí vận chuyển
  9. `delivery-process` (buyer) — Quy trình giao hàng cho người mua
  10. `privacy-policy` (both) — Chính sách bảo mật
- [x] Đã verify nạp bằng `build_knowledge_base()` trong `ingest.py`: 10 doc → 31 chunk, metadata `customer_role`/`category` đầy đủ; `pytest tests/ -v` vẫn 42/42 pass
- [ ] Ghi bảng tài liệu vào `REPORT_NHOM.md` Phần 1 — còn lại

### Bước 5 — Thiết kế chiến lược cá nhân (Bài 3.1 — 15đ nhóm) — CHƯA LÀM
- [ ] Đặt `EMBEDDING_PROVIDER=local` trong `.env` (bắt buộc để so sánh có ý nghĩa, KHÔNG dùng mock)
- [ ] Chạy baseline: `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu, ghi kết quả
- [ ] Chọn 1 chiến lược riêng (built-in tuned hoặc `CustomChunker` — vd chia theo Q&A pair/heading/điều khoản, theo yêu cầu K4 ít nhất 1 thành viên nhóm phải thử kiểu này)
- [ ] So sánh với baseline, ghi vào `REPORT_NHOM.md` Phần 2

### Bước 6 — Câu hỏi đánh giá (Bài 3.2, làm chung cả nhóm 1 lần) — CHƯA LÀM
- [ ] Thống nhất đúng 5 benchmark queries + gold answers
- [ ] Bắt buộc theo K4: ít nhất 1 câu cần `metadata_filter={"customer_role": "seller"|"buyer"}`
- [ ] Ghi vào `REPORT_NHOM.md` Phần 3

### Bước 7 — Dự đoán cosine similarity (Bài 3.3 — 5đ cá nhân) — ĐÃ XONG (bằng mock, cần re-run với local embedder)
- [x] Chọn 5 cặp câu, dự đoán similarity cao/thấp trước
- [x] Chạy `compute_similarity()` thật với `_mock_embed`, ghi vào `REPORT_CANHAN.md` Phần 4 — kết quả cho thấy rõ mock gần như ngẫu nhiên (4/5 dự đoán sai), đúng cảnh báo của README
- [ ] **Việc còn lại:** chạy lại bằng `EMBEDDING_PROVIDER=local` khi cài xong embedder thật (gộp chung với Bước 5)

### Bước 8 — Chạy benchmark & so sánh (Bài 3.4) — NHÁP XONG (bằng mock + câu hỏi tự đề xuất), CHỜ NHÓM CHỐT CHÍNH THỨC
- [x] Đã chạy nháp 5 câu hỏi tự đề xuất (2 câu có `metadata_filter={"customer_role":"seller"}`) trên `FixedSizeChunker(300,40)` + `_mock_embed`, ghi top-1/score/relevant vào `REPORT_CANHAN.md` Phần 5 — kết quả 0/5 relevant, đúng như dự kiến vì dùng mock
- [ ] Thay bằng **5 câu hỏi chính thức của nhóm** (Bước 6) khi có
- [ ] Chạy lại toàn bộ với `EMBEDDING_PROVIDER=local`
- [ ] So sánh trong nhóm: chiến lược nào tốt hơn, có đảo ngược giữa câu hỏi không, metadata filter có giúp không
- [ ] Cập nhật `REPORT_CANHAN.md` Phần 5 + `REPORT_NHOM.md` Phần 3

### Bước 9 — Phân tích lỗi (Bài 3.5) — CHƯA LÀM
- [ ] Tìm ít nhất 1 failure case, giải thích nguyên nhân (chunk sai kích thước/thiếu metadata/câu hỏi mơ hồ), đề xuất cải thiện
- [ ] Ghi vào `REPORT_NHOM.md` Phần 4

### Bước 10 — Hoàn thiện & nộp bài (làm cuối cùng) — CHƯA LÀM
- [x] `pytest tests/ -v` toàn bộ pass trong `Trinh-Hai-Dang-2A202601602/` (42/42 — nhưng cần chạy lại lần cuối trước khi nộp)
- [ ] Rà lại `REPORT_CANHAN.md` đủ 5 phần, `REPORT_NHOM.md` đủ 4 phần
- [ ] Kiểm tra `data/` không chứa dữ liệu nhạy cảm/đăng nhập
- [x] Đảm bảo mọi thứ nằm trong `Trinh-Hai-Dang-2A202601602/`

---

## 3. Checklist tổng (đối chiếu README/exercises)

- [x] Vượt tất cả test: `pytest tests/ -v` (42/42, cần re-check lần cuối sau khi thêm data/report)
- [x] `src/` hoàn thành TODO cá nhân
- [ ] `REPORT_NHOM.md` đầy đủ (1 file/nhóm)
- [ ] `REPORT_CANHAN.md` đầy đủ (1 file/sinh viên — của Đăng)
- [x] Toàn bộ code + báo cáo nằm trong `Trinh-Hai-Dang-2A202601602/`

---

## 4. Đang làm tiếp theo (next action)

**Toàn bộ phần cá nhân (60đ) đã hoàn thiện ở mức "chạy được, có số liệu thật"**: code (30/30), khởi động (5/5), hướng tiếp cận (10/10), dự đoán similarity (5/5), kết quả truy xuất nháp (Phần 5, hiện 0/5 relevant vì dùng mock — tự đánh giá tạm 3/10). Điểm cần cải thiện trước khi nộp thật:
1. Cài `EMBEDDING_PROVIDER=local` (Bước 5) rồi chạy lại Phần 4 + Phần 5 của `REPORT_CANHAN.md` với embedder thật.
2. Chờ nhóm chốt 5 câu hỏi benchmark chính thức (Bước 6) rồi thay vào Phần 5 thay vì bộ câu hỏi tự đề xuất hiện tại.
3. Sau đó mới sang `REPORT_NHOM.md` (thiết kế chiến lược, chất lượng truy xuất nhóm, demo, phân tích lỗi).
