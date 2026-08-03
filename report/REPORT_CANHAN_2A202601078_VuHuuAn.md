# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Hữu An
**MSSV:** 2A202601078
**Nhóm:** DOMESSIU (lớp K4)
**Ngày:** 2026-08-03
**Gói mã nguồn cá nhân:** `src/K4_2A202601078_VuHuuAn` (chạy chấm qua `LAB_SOLUTION_PACKAGE=src.K4_2A202601078_VuHuuAn`)

> **Nộp 1 bản / sinh viên.** File này là báo cáo riêng của tôi (mục 1 của `REPORT_CANHAN.md` chung đã do bạn hina dùng). Phần nhóm ở `REPORT_NHOM.md`. Thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**
> Cosine cao nghĩa là hai vector embedding **cùng hướng** trong không gian ngữ nghĩa → hai đoạn text nói về cùng một ý/chủ đề, bất kể dài ngắn hay dùng từ khác nhau. Giá trị từ -1 (ngược hướng) → 0 (không liên quan) → 1 (trùng hướng); kiểm chứng bằng `compute_similarity`: vector giống hệt → 1.0, vuông góc → 0.0, ngược dấu → -1.0 (4 test `TestComputeSimilarity` pass).

**Ví dụ CAO** (đo thật bằng BGE-M3, xem Mục 4):
- Câu A: "a warm winter coat made of soft faux fur"
- Câu B: "a fluffy synthetic-fur jacket for cold days"
- Tại sao tương đồng: gần như không dùng chung từ ("coat" vs "jacket", "faux fur" vs "synthetic-fur") nhưng **cùng một ý**: áo khoác lông giả giữ ấm. Embedding mã hoá ngữ nghĩa chứ không phải mặt chữ → cosine = **+0.822**.

**Ví dụ THẤP:**
- Câu A: "black halterneck bikini top for the beach"
- Câu B: "instructions to install a printer driver on Windows"
- Tại sao khác: khác hoàn toàn miền chủ đề (thời trang biển vs kỹ thuật máy in) → hai vector gần trực giao, cosine = **+0.292**.

**Tại sao ưu tiên cosine hơn khoảng cách Euclid cho text embeddings?**
> Norm (độ dài) của vector embedding chủ yếu phản ánh **độ dài/số token** của đoạn text chứ không phải nội dung, nên Euclid phạt oan khi so một câu hỏi ngắn với một chunk dài dù cùng nghĩa. Cosine chuẩn hoá norm, chỉ giữ **hướng** = ngữ nghĩa → hợp với retrieval (query ngắn vs chunk dài). Trong `EmbeddingStore` tôi cũng L2-normalize vector nên tích vô hướng (dot) chính là cosine.

### Bài toán Chunking (Bài tập 1.2)

**10,000 ký tự, chunk_size=500, overlap=50 → bao nhiêu chunks?**
> Mỗi bước tiến `step = 500 - 50 = 450`. Công thức:
> `ceil((length - overlap) / (chunk_size - overlap)) = ceil((10000 - 50) / 450) = ceil(22.11) = 23`
> **Đáp án: 23 chunks** — đối chiếu code: `len(FixedSizeChunker(500, 50).chunk("x"*10000)) == 23`. ✅

**Overlap tăng lên 100 thì sao? Vì sao muốn overlap nhiều hơn?**
> `ceil((10000 - 100) / (500 - 100)) = ceil(24.75) = 25` chunk (kiểm code: 25). Overlap lớn hơn ⇒ step nhỏ hơn ⇒ **nhiều chunk hơn** để phủ hết tài liệu. Lợi: một câu/ý bị cắt ngang ranh giới vẫn xuất hiện nguyên vẹn trong ít nhất một chunk → đỡ mất ngữ cảnh khi truy xuất (tăng recall). Cái giá: nhiều bản ghi hơn, nhiều lần embed hơn, top-k dễ trùng nội dung.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking)

**`SentenceChunker.chunk`**
> Tách câu bằng regex look-behind `(?<=[.!?])\s+` — cắt tại khoảng trắng **sau** dấu `.`/`!`/`?` nên giữ nguyên dấu kết câu (phủ cả `". "`, `"! "`, `"? "`, `".\n"`). Sau đó `strip` từng câu, bỏ câu rỗng, rồi gom mỗi `max_sentences_per_chunk` câu thành một chunk. Edge case: text rỗng/toàn khoảng trắng → trả `[]`.

**`RecursiveChunker.chunk` / `_split`**
> Đệ quy theo thứ tự separator `["\n\n", "\n", ". ", " ", ""]`. **Base case:** đoạn đã `<= chunk_size`, hoặc hết separator / gặp `""` → cắt cứng theo ký tự. Ngược lại: `split` theo separator hiện tại, **gộp tham lam** các mảnh nhỏ liền kề lại tới sát `chunk_size` (giữ chunk to & mạch lạc), còn mảnh nào vẫn quá lớn thì đệ quy tiếp với separator ưu tiên thấp hơn.

### Lớp `EmbeddingStore`

**`add_documents` + `search`**
> `_make_record` embed `content` của từng doc và **tiêm `doc_id` vào metadata** (để lọc/xóa theo doc hoạt động kể cả khi metadata rỗng); lưu list dict in-memory (có thêm nhánh ChromaDB dùng cosine space khi thư viện có sẵn). `search` embed query, tính **tích vô hướng** với mọi vector đã lưu (vector đã normalize nên dot = cosine), sort giảm dần, cắt `top_k`.

**`search_with_filter` + `delete_document`**
> **Lọc metadata TRƯỚC rồi mới xếp hạng** (pre-filter): giữ record thoả `all(meta[k]==v)` cho mọi cặp trong `metadata_filter`, sau đó chạy cùng hàm similarity trên tập đã lọc → chính xác hơn cho câu hỏi cần facet (vd `category_group=outerwear`). `delete_document` giữ lại các record có `doc_id` khác, trả `True` nếu số lượng giảm.

### Tác tử `KnowledgeBaseAgent.answer`
> Retrieve `top_k` chunk → ghép thành context **đánh số `[1] [2] [3]`** → dựng prompt yêu cầu "trả lời CHỈ dựa vào context, nếu không đủ thì nói không đủ thông tin" → gọi `llm_fn`. Cách đánh số giúp truy vết nguồn (grounding).

### Chiến lược riêng của tôi (điểm nhấn cá nhân)
> Ngoài 3 chunker chuẩn, tôi thêm **`HeadingChunker`** (chia theo tiêu đề `#/##/###`, giữ heading gắn vào mọi mảnh con, **loại footer nguồn/license** để giảm nhiễu) và **`BGEM3Embedder`** (BGE-M3 chạy local, dense L2-normalized). Đây là chiến lược dùng ở Mục 5.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết Quả Kiểm Thử (`LAB_SOLUTION_PACKAGE=src.K4_2A202601078_VuHuuAn pytest tests/ -v`)

```
platform win32 -- Python 3.10.11, pytest-9.1.1
collected 42 items

tests/test_solution.py::TestProjectStructure::... PASSED            (2/42)
tests/test_solution.py::TestClassBasedInterfaces::... PASSED
tests/test_solution.py::TestFixedSizeChunker::... PASSED            (7 test)
tests/test_solution.py::TestSentenceChunker::... PASSED             (4 test)
tests/test_solution.py::TestRecursiveChunker::... PASSED            (4 test)
tests/test_solution.py::TestEmbeddingStore::... PASSED              (8 test)
tests/test_solution.py::TestKnowledgeBaseAgent::... PASSED          (2 test)
tests/test_solution.py::TestComputeSimilarity::... PASSED           (4 test)
tests/test_solution.py::TestCompareChunkingStrategies::... PASSED   (3 test)
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::... PASSED (3 test)
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::... PASSED   (3 test)

============================= 42 passed in 0.28s ==============================
```

**Số lượng bài test vượt qua (pass): 42 / 42** ✅

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Đo bằng `compute_similarity()` trên embedding **BGE-M3** (không dùng mock vì mock là nhiễu).

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---|---|
| 1 | warm coat made of soft faux fur | fluffy synthetic-fur jacket for cold days | cao | **+0.822** | ✅ |
| 2 | maternity dress for pregnant women | dress designed to fit from bump to baby | cao | **+0.699** | ✅ |
| 3 | black halterneck bikini for the beach | install a printer driver on Windows | thấp | **+0.292** | ✅ |
| 4 | flare jeans in a light blue wash | straight leg jeans in a blue denim wash | cao? | **+0.800** | ✅ |
| 5 | satin maxi dress that costs £110 | cotton legging shorts that cost £6 | thấp? | **+0.552** | ~ (cao hơn dự đoán) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 4** (+0.800) và **cặp 5** (+0.552). Cặp 4: "flare" và "straight leg" là hai kiểu quần **đối lập**, nhưng embedding vẫn cho điểm rất cao vì nó bắt **chủ đề/danh mục** ("jeans/denim/blue wash") mạnh hơn nhiều so với sắc thái phân biệt kiểu dáng. Cặp 5: dù khác hẳn loại đồ và **giá £110 vs £6**, điểm vẫn 0.55 vì embedding gần như **bỏ qua con số giá** và chỉ thấy "thời trang nữ". → Bài học: embeddings mã hoá **ngữ nghĩa chủ đề/danh mục**, KHÔNG phân biệt tốt các chi tiết trái ngược (flare/straight) hay thuộc tính số (giá). Vì vậy trong hệ retrieval, những facet như `category_group`, `price` phải dùng **metadata filter** chứ không dựa vào vector (xem Mục 5, câu 3).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** (`benchmark/queries.py`, trùng với các thành viên) trên gói cá nhân của tôi, với chiến lược **HeadingChunker (max_chars=400) + BGE-M3**, 71 chunk.

| # | Câu hỏi | Top-1 Chunk (tóm tắt) | Score | Relevant? | Câu trả lời Agent (tóm tắt) |
|---|---|---|---|---|---|
| 1 | Item nào phải *dry clean only* + chất liệu? | Dorina mesh bra — bảng size (SAI) | +0.442 | ❌ | Không đúng (chunk sai → không trả lời được "Dry clean only / 100% Cotton") |
| 2 | Giá đầm ASOS EDITION satin maxi? | ASOS EDITION satin maxi — Product details | +0.744 | ✅ | **£110.00** (standard) |
| 3 | Outerwear nào làm từ faux fur? *(filter)* | Daisy Street faux fur coat | +0.574 | ✅ | **Daisy Street mid-length faux fur coat** — "Super-soft faux fur" |
| 4 | Món đen halterneck đi biển? | Hollister halterneck bikini top black | +0.628 | ✅ | Hollister bikini top + Public Desire beach dress (đều black + halterneck) |
| 5 | Có đầm bầu, thiết kế vừa vặn sao? | ASOS DESIGN maternity wrap dress | +0.643 | ✅ | **ASOS maternity cami wrap dress** — "fit you from bump to baby", £30.00 |

**Bao nhiêu câu trả về chunk liên quan trong top-3? 4 / 5** — điểm retrieval **8/10** (Q2–Q5 = TOP-1 → 2đ; Q1 = MISS → 0đ).

**Phân tích thất bại (Q1):** câu "dry clean only + chất liệu" MISS vì thông tin nằm ở hai mục rất nhỏ (`### Look After Me`: "Dry clean only" và `### About Me`: "100% Cotton") bị lu mờ giữa các chunk khác; nhiều sản phẩm cotton gây nhiễu, và cụm "dry clean" không đủ tín hiệu ngữ nghĩa nổi bật. Hướng cải thiện: gộp care+fabric vào một chunk, hoặc tăng top-k, hoặc thêm metadata `care`/`fabric` để lọc.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Cùng một corpus và cùng 5 câu hỏi nhưng chiến lược chunking + embedder khác nhau cho điểm rất khác: mock ≈ 1/10 (nhiễu) trong khi BGE-M3 + HeadingChunker đạt 8/10. Điều này cho thấy **chất lượng embedder đa ngôn ngữ và cách chia chunk theo cấu trúc tài liệu** quan trọng hơn nhiều so với việc chỉ "chạy được", và metadata filter là chìa khoá cho các câu hỏi theo facet.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — 42/42 tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition — 4/5 top-3, 8/10) | 8 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
