# Bài làm CÁ NHÂN — Nguyễn Thanh Bình

**Họ tên:** Nguyễn Thanh Bình
**Mã sinh viên:** 2A202601274
**Lớp:** K4 — chủ đề cố định: chính sách TMĐT / hỗ trợ khách hàng
**Ngày:** 03/08/2026

> Thư mục này chứa **phần cá nhân (60 điểm)** của riêng tôi trong repo chung của nhóm.
> Nhóm có 5 thành viên → 5 thư mục tương tự, mỗi người một thư mục.
> Phần nhóm (40 điểm) nằm ở `report/REPORT_NHOM.md` tại gốc repo.

---

## 1. Nguyên tắc tổ chức: cái gì riêng, cái gì chung

```
<gốc repo — DÙNG CHUNG cả nhóm>
├── data/                    ← corpus chung (KHÔNG copy vào thư mục cá nhân)
├── tests/                   ← 42 unit test chung
├── ingest.py, main.py       ← pipeline lab cung cấp
├── report/REPORT_NHOM.md    ← báo cáo nhóm, 1 bản/nhóm
│
├── Nguyen-Thanh-Binh-2A202601274/   ← ★ THƯ MỤC NÀY
│   ├── README_NOP_BAI.md
│   ├── src/                 ← code của RIÊNG tôi (13 TODO)
│   ├── report/REPORT_CANHAN.md
│   ├── scripts/             ← script tôi tự viết để lấy số liệu
│   └── ket-qua-chay/        ← output thật đã chạy
├── <Ho-Ten-2-MSSV>/         ← thư mục bạn thứ 2
├── ...                      ← 5 thư mục tất cả
```

**Vì sao KHÔNG copy `data/` vào đây:** đề bài Giai đoạn 2 yêu cầu cả 5 thành viên chạy **cùng một bộ
tài liệu và cùng 5 câu hỏi** thì mới so sánh được chiến lược của nhau. Nếu mỗi người giữ một bản copy
riêng, chỉ cần một người bổ sung tài liệu là 4 bản kia thành cũ và **mọi kết quả hết so sánh được** —
mất điểm ở cả "Thiết kế chiến lược" (15đ) lẫn "Chất lượng truy xuất" (10đ) của phần nhóm.

Script trong `scripts/` tự trỏ về `data/` ở gốc repo bằng đường dẫn tuyệt đối, nên **không thể chạy nhầm
corpus cũ**.

---

## 2. Đối chiếu thang điểm → file

| Hạng mục (`docs/SCORING.md`) | Điểm | Nằm ở đâu |
|---|---|---|
| Hoàn thiện code (Core Implementation) | 30 | `src/chunking.py`, `src/store.py`, `src/agent.py` — 13/13 TODO |
| Hướng tiếp cận (My Approach) | 10 | `report/REPORT_CANHAN.md` — Mục 2 |
| Khởi động (Warm-up) | 5 | `report/REPORT_CANHAN.md` — Mục 1 |
| Dự đoán độ tương tự | 5 | `report/REPORT_CANHAN.md` — Mục 4 + `scripts/similarity_predictions.py` |
| Kết quả truy xuất (Competition Results) | 10 | `report/REPORT_CANHAN.md` — Mục 5 + `scripts/retrieval_benchmark.py` |

### File nào là bài làm của tôi

| File | Nội dung |
|---|---|
| `src/chunking.py` | `SentenceChunker`, `RecursiveChunker` (+`_split`, `_hard_split`), `compute_similarity`, `ChunkingStrategyComparator`, và **`ClauseChunker`** — chunker tuỳ chỉnh tôi tự thiết kế cho K4 |
| `src/store.py` | 7 phương thức `EmbeddingStore` + `_matches()`, `_chroma_safe_metadata()` |
| `src/agent.py` | `KnowledgeBaseAgent.__init__` / `.answer` + `PROMPT_TEMPLATE` |
| `report/REPORT_CANHAN.md` | Báo cáo cá nhân, đủ 5 mục |
| `scripts/similarity_predictions.py` | Bài tập 3.3 — dự đoán ghi cứng **trước khi chạy** |
| `scripts/retrieval_benchmark.py` | Bài tập 3.1 + 3.4 — baseline, so sánh chiến lược, top-3 + agent |
| `scripts/strategy_sweep.py` | Quét 12 cấu hình chunking và **tự chấm theo rubric** |
| `scripts/edge_cases_check.py` | Kiểm chứng ca biên **ngoài** 42 unit test |

`src/models.py`, `src/embeddings.py`, `src/__init__.py` do lab cung cấp (tôi chỉ thêm 2 dòng export
`ClauseChunker` vào `__init__.py`).

---

## 3. Cách chạy

Chạy **từ gốc repo** — cài môi trường một lần cho cả nhóm:

```bash
py -3.11 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt          # pytest + dotenv
.venv/Scripts/python -m pip install -r requirements-local.txt    # embedder đa ngữ (Mục 4, 5)
```

### Chấm 42 unit test trên code của RIÊNG tôi

Bộ test hỗ trợ sẵn biến `LAB_SOLUTION_PACKAGE`, nên chạy từ gốc repo và trỏ vào package của tôi:

```bash
# PowerShell
$env:LAB_SOLUTION_PACKAGE="Nguyen-Thanh-Binh-2A202601274.src"
.venv/Scripts/python -m pytest tests/ -v
```

Mỗi thành viên đổi tên thư mục của mình trong biến này là chấm được code riêng, **không ai đè lên ai**.

### Chạy các script của tôi

Chạy **từ trong thư mục này**:

```bash
cd Nguyen-Thanh-Binh-2A202601274
$env:PYTHONIOENCODING="utf-8"
$env:EMBEDDING_PROVIDER="local"        # Mục 4 & 5 PHẢI dùng embedder thật

../.venv/Scripts/python scripts/edge_cases_check.py
../.venv/Scripts/python scripts/similarity_predictions.py
../.venv/Scripts/python scripts/retrieval_benchmark.py
../.venv/Scripts/python scripts/strategy_sweep.py
```

Script tự nạp `src/` **của thư mục này** (ưu tiên cao hơn `src/` ở gốc), còn `ingest.py`, `main.py`,
`data/` thì lấy bản dùng chung ở gốc repo.

---

## 4. Kết quả đã chạy (lưu trong `ket-qua-chay/`)

| File | Nội dung | Kết quả |
|---|---|---|
| `01-pytest.txt` | 42 test, trỏ vào `src/` của tôi | **42 passed** |
| `02-edge-cases.txt` | Ca biên ngoài bộ test | **TẤT CẢ KIỂM CHỨNG BIÊN ĐỀU ĐẠT** |
| `03-ingest-selfcheck.txt` | Pipeline nạp dữ liệu | **OK — 18 chunk, mỗi chunk giữ doc_id** |
| `04-similarity-local.txt` | Mục 4 — embedder thật | Dự đoán đúng **4.5/5** |
| `05-benchmark-local.txt` | Mục 5 — embedder thật | **5/5 gold ở top-1**, agent đúng 5/5 |
| `06-strategy-sweep.txt` | Quét 12 chiến lược | Cao nhất: `clause(1 câu)` — **10/10** |

Backend nhúng: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (không phải mock).

---

## 5. Ba lỗi tôi tự tìm ra và sửa — cả ba đều **pass hết 42 test** ở bản trước khi sửa

1. **`RecursiveChunker` xoá dấu chấm câu** ở mọi ranh giới chunk (`split(". ")` nuốt separator). Đo trên corpus: mất 9 dấu chấm → sau khi sửa **0/108**.
2. **Lọc metadata hỏng tuỳ môi trường:** `ingest.py` dùng pyyaml nếu có, nên `retrieved_at: 2026-08-02` ra `datetime.date` (có pyyaml) hoặc `str` (không có). Lọc bằng `==` cứng sẽ **âm thầm trả rỗng**. Đã tách hàm `_matches()`.
3. **ChromaDB từ chối cả lô** khi metadata có kiểu không vô hướng, rồi im lặng rơi về in-memory. Đã thêm `_chroma_safe_metadata()` + `warnings.warn`.

Chi tiết và bằng chứng nằm ở Mục 2 của `report/REPORT_CANHAN.md`.

---

## 6. Hướng dẫn cho 4 thành viên còn lại

Mỗi bạn tự tạo thư mục theo đúng mẫu này:

1. Tạo thư mục `<Ho-Ten>-<MSSV>/` ở gốc repo (không dấu, dùng gạch ngang — để tránh lỗi đường dẫn).
2. Copy `src/` **bản gốc còn nguyên TODO** vào thư mục của mình rồi tự làm 13 TODO.
   - Lấy bản gốc: `git show 82b2330:src/chunking.py > <thư-mục-của-bạn>/src/chunking.py` (làm tương tự cho `store.py`, `agent.py`, và copy thẳng `__init__.py`, `models.py`, `embeddings.py`).
3. Copy `report/REPORT_CANHAN.md` (template) vào `<thư-mục-của-bạn>/report/` rồi điền.
4. Chấm test riêng: đặt `LAB_SOLUTION_PACKAGE="<thư-mục-của-bạn>.src"` rồi `pytest tests/ -v`.
5. **Không copy `data/`** — dùng chung ở gốc để 5 người so sánh được với nhau.
6. Mỗi người chọn **một chiến lược chunking khác nhau** (yêu cầu của đề), và nhóm phải có **ít nhất 1 người**
   chunk theo điều/khoản / heading / cặp FAQ (yêu cầu riêng của K4 — tôi đã làm phần này bằng `ClauseChunker`).

---

## 7. Còn thiếu (cần thông tin từ nhóm / buổi demo)

- `report/REPORT_CANHAN.md` dòng 5 — **tên nhóm**
- `report/REPORT_CANHAN.md` cuối Mục 5 — **"Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo)"**

5 câu hỏi benchmark hiện là **bản đề xuất của tôi**. Khi nhóm chốt bộ chính thức, sửa danh sách `BENCHMARK`
trong `scripts/retrieval_benchmark.py` rồi chạy lại — bảng Mục 5 tự cập nhật.

**Lưu ý cho báo cáo nhóm:** `ClauseChunker` trong `src/chunking.py` là chiến lược riêng của tôi cho Bài tập 3.1
— cần chép mã + lý do thiết kế sang `REPORT_NHOM.md` mục 2 (Thiết kế chiến lược, 15 điểm).
