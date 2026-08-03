# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Quang Hà
**MSSV:** 2A202601424
**Lớp:** K4 — biến thể Chính sách thương mại điện tử
**Nhóm:** [điền tên nhóm]
**Ngày:** 03/08/2026
**Strategy cá nhân:** `HeadingChunker` (chunk theo Điều/heading, có gắn lại breadcrumb tiêu đề) — file `strategies.py`

---

## 1. Khởi động (Warm-up) — 5 điểm

### Độ tương tự Cosine (Bài tập 1.1)

**Cosine similarity cao nghĩa là gì?**

> Hai vector chỉ về **cùng một hướng** trong không gian embedding, tức là mô hình cho rằng hai đoạn text có phân bố ngữ nghĩa gần nhau. Nó nói về *hướng*, không nói về *độ dài* — nên một câu ngắn và một đoạn dài cùng chủ đề vẫn có thể đạt cosine cao.

**Ví dụ có độ tương tự CAO:**

- Câu A: "Người bán phải công bố chính sách hoàn trả trên website."
- Câu B: "Website thương mại điện tử phải nêu rõ quy định đổi trả hàng."
- Tại sao tương đồng: cùng nói về nghĩa vụ công bố chính sách đổi/trả, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**

- Câu A: "Thời hạn trả lời đề nghị giao kết hợp đồng là 12 giờ."
- Câu B: "Sàn phải thông báo trước ít nhất 5 ngày khi đổi quy chế hoạt động."
- Tại sao khác: cùng là con số thời gian nhưng khác chủ thể, khác nghĩa vụ, khác Điều luật.

**Tại sao cosine được ưu tiên hơn khoảng cách Euclid cho text embedding?**

> Vì độ dài vector của text embedding phần lớn phản ánh **độ dài / tần suất từ** của đoạn text chứ không phản ánh nội dung. Euclid phạt sự chênh lệch độ dài đó, còn cosine chuẩn hoá nó đi và chỉ so hướng — nên "một câu" và "một đoạn 5 câu" cùng chủ đề vẫn được coi là gần nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10.000 ký tự, `chunk_size=500`, `overlap=50` → bao nhiêu chunk?**

> Công thức: `ceil((length - overlap) / (chunk_size - overlap))`
> = `ceil((10000 - 50) / (500 - 50))` = `ceil(9950 / 450)` = `ceil(22.11)`
> **Đáp án: 23 chunk.**

**Nếu overlap tăng lên 100 thì sao?**

> `ceil((10000 - 100) / 400) = ceil(24.75) = 25` chunk → **số chunk TĂNG**.
> Đánh đổi: mỗi thông tin có nhiều "cơ hội" lọt top-k hơn (recall tốt hơn, ít bị cắt giữa câu điều kiện), nhưng phải embed và lưu nhiều vector hơn → tốn chi phí, và top-k dễ bị chiếm bởi nhiều chunk gần trùng nhau của cùng một đoạn (giảm đa dạng kết quả).

---

## 2. Hướng tiếp cận của tôi — 10 điểm

### `SentenceChunker.chunk`

Dùng lookbehind `re.compile(r"(?<=[.!?])\s+")` để cắt tại **khoảng trắng đứng sau** dấu kết câu. Lookbehind quan trọng vì nó giữ nguyên dấu chấm ở cuối câu trước — nếu dùng `re.split(r"[.!?]\s+")` thì dấu câu bị nuốt mất và khi ghép lại các câu sẽ dính vào nhau. Edge case xử lý: `text` rỗng → `[]`; strip từng câu và loại chuỗi rỗng trước khi gộp nhóm; luôn trả `list[str]` chứ không phải generator.

### `RecursiveChunker.chunk` / `_split`

`chunk()` chỉ lo vỏ ngoài (text rỗng → `[]`, strip/lọc kết quả), toàn bộ đệ quy nằm trong `_split(current_text, remaining_separators)`. Hai base case rõ ràng: (a) text đã ngắn hơn `chunk_size` → trả về nguyên; (b) hết separator **hoặc** separator là chuỗi rỗng → `_hard_split` cắt cứng theo `chunk_size`. Nếu separator hiện tại không xuất hiện thì gọi lại với `remaining_separators[1:]` — **mỗi lần gọi đệ quy đều phải hoặc bớt separator hoặc thu nhỏ text**, đó là điều kiện để không lặp vô hạn. Bước dễ bỏ sót là **gom**: sau khi split phải nối các phần liền nhau tới sát `chunk_size` (dùng biến `buffer`), nếu không sẽ ra hàng loạt chunk vụn vài ký tự.

### `EmbeddingStore.add_documents` + `search`

Chọn in-memory (`_use_chroma = False`) để mọi method đi qua đúng một đường code. Viết hai helper trước: `_make_record(doc)` chuẩn hoá một `Document` thành record `{id, doc_id, content, metadata, embedding}` — **copy** metadata (`dict(doc.metadata)`) để không sửa nhầm dict của người gọi, và `metadata.setdefault("doc_id", doc.id)` để `delete_document` luôn có khoá; id record ghép `doc.id` với `_next_index` nên không bao giờ trùng. `_search_records(query, records, top_k)` embed query **một lần** ngoài vòng lặp, tính dot product với từng record, sort giảm dần rồi cắt `top_k`.

### `search_with_filter` + `delete_document`

**Filter TRƯỚC, rank SAU.** Nếu làm ngược (lấy top-k rồi loại cái không khớp) thì có thể còn 0 kết quả dù store vẫn còn tài liệu hợp lệ — ví dụ 3 chunk `seller` chiếm hết top-3, lọc `buyer` xong còn rỗng. Khi `metadata_filter` là `None` thì gọi thẳng `_search_records` trên toàn bộ `_store`, nên `search()` và `search_with_filter(..., None)` **dùng chung một hàm** và không thể lệch nhau (đây chính là test `test_no_filter_returns_all_candidates`). `delete_document` lọc lại `_store` bỏ mọi record có `metadata['doc_id'] == doc_id`, so sánh độ dài trước/sau để return `True`/`False`.

### `KnowledgeBaseAgent.answer`

`__init__` lưu `store` và `llm_fn`. `answer()` gọi `store.search(question, top_k)`; **store rỗng → trả thông báo rõ ràng, không gọi LLM vô ích**. Context được đánh số `[1] (nguồn: doc_id::chunk_N | url: ...)` — phần đánh số này là thứ đáng đầu tư nhất vì nó cho phép truy vết câu trả lời về đúng chunk và đúng file khi debug (tiêu chí grounding). Prompt gồm: instruction "chỉ dùng context, nói rõ khi không đủ" → Context → Question → nhãn `Answer:`. Tôi tách `build_prompt()` và `format_context()` thành method riêng để `bench.py` tái sử dụng được mà không phải copy code.

---

## 3. Hoàn thiện code — 30 điểm

### Kết Quả Kiểm Thử

```
$ python -m pytest tests -v
============================= test session starts ==============================
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::* (7 test) PASSED
tests/test_solution.py::TestSentenceChunker::* (4 test) PASSED
tests/test_solution.py::TestRecursiveChunker::* (4 test) PASSED
tests/test_solution.py::TestEmbeddingStore::* (8 test) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::* (4 test) PASSED
tests/test_solution.py::TestCompareChunkingStrategies::* (3 test) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.14s ===============================
```

**Số lượng bài test vượt qua: 42 / 42**

`python main.py "Chunking là gì?"` chạy được từ đầu đến cuối trên `data/k4_ecommerce`.

---

## 4. Dự đoán độ tương tự — 5 điểm

Đo bằng `src.chunking.compute_similarity`. Cột `mock` = `MockEmbedder` mặc định; cột `lexical` = `LexicalEmbedder` TF-IDF tôi tự viết (`lexical_embedding.py`) để có số liệu có nghĩa mà không cần tải PyTorch.

| Cặp | Câu A | Câu B | Dự đoán | mock | lexical | Đúng? |
|-----|-------|-------|---------|------|---------|-------|
| 1 | "Chính sách đổi trả hàng hóa" | "Quy định hoàn trả sản phẩm" | cao | 0.0958 | 0.0491 | **SAI cả hai** |
| 2 | "Người bán phải công bố chính sách hoàn trả" | (chính nó) | cao | 1.0000 | 1.0000 | Đúng |
| 3 | "Thời hạn trả lời đề nghị giao kết là 12 giờ" | "Sàn phải thông báo trước ít nhất 5 ngày" | thấp | 0.1884 | 0.0000 | Đúng (lexical rõ hơn) |
| 4 | "Chính sách kiểm hàng là điều kiện giao dịch chung" | "Điều kiện giao dịch chung phải công bố chính sách hoàn trả" | cao | 0.0456 | 0.4124 | mock SAI, lexical Đúng |
| 5 | "Thủ tục đăng ký website cung cấp dịch vụ TMĐT" | "Giá niêm yết được hiểu là đã bao gồm mọi chi phí" | thấp | −0.0960 | 0.0572 | Đúng |

**Kết quả nào bất ngờ nhất?**

> **Cặp 1.** Hai câu gần như đồng nghĩa hoàn toàn ("đổi trả hàng hóa" ↔ "hoàn trả sản phẩm") nhưng cả hai backend đều cho điểm rất thấp. Lý do khác nhau và đều đáng ghi: `MockEmbedder` là hash MD5 nên mọi cặp đều là nhiễu ngẫu nhiên; `LexicalEmbedder` là TF-IDF nên nó **chỉ đo trùng từ**, hai câu không chia sẻ token nào ngoài "chính sách/quy định" nên gần như bằng 0.
>
> Điều này nói lên đúng bản chất: embedding **không phải** bản thân câu văn, nó là input để xếp hạng, và chất lượng xếp hạng bị chặn trên bởi chất lượng của mô hình nhúng. Cặp 2 (giống hệt → 1.0) và cặp 5 (mock ra số **âm** cho hai câu chỉ đơn giản là không liên quan) cho thấy score cao/thấp là **tín hiệu xếp hạng, không phải bằng chứng nội dung đúng**.

---

## 5. Kết quả truy xuất của tôi — 10 điểm

Strategy: **`HeadingChunker(max_chunk_size=900, min_chunk_size=120, keep_breadcrumb=True)`**
Corpus: `data/k4_ecommerce` (9 tài liệu) → **50 chunk**
Embedder: `LexicalEmbedder` (dùng chung cho mọi thành viên để so sánh công bằng)
Output đầy đủ: `report/bench_output_lexical.txt`

| # | Câu hỏi | Top-1 chunk truy xuất được | Score | Liên quan? | Câu trả lời của Agent |
|---|---------|---------------------------|-------|-----------|----------------------|
| 1 | Không công bố thời hạn trả lời thì sau bao lâu đề nghị hết hiệu lực? | `nd52-quy-trinh-dat-hang-truc-tuyen::chunk_6` — Điều 20 | 0.3833 | ✅ chứa "12 (mười hai) giờ" | Trích đúng Điều 20, dẫn `[1]` |
| 2 | Sàn phải báo trước bao nhiêu ngày khi đổi quy chế? | `nd52-quy-che-hoat-dong-san::chunk_2` — Điều 38 khoản 3 | 0.2677 | ✅ chứa "ít nhất 5 ngày" | Trích đúng Điều 38 |
| 3 | Cơ chế rà soát phải hiển thị thông tin gì? | `nd52-quy-trinh-dat-hang-truc-tuyen::chunk_4` — Điều 18 **khoản 3** | 0.3495 | ⚠️ đúng Điều nhưng **sai khoản**; chunk chứa đáp án nằm ở top-2 | Thiếu danh sách a/b/c ở top-1 |
| 4 | Chính sách kiểm hàng có bắt buộc không? (**có filter** `customer_role=buyer`) | `nd85-2021-...::chunk_5` — mục 4 | 0.3591 | ✅ chứa "chính sách kiểm hàng" | Trả lời đúng theo bản 2021 |
| 5 | Giá niêm yết không nói rõ đã gồm thuế/phí thì hiểu sao? | `seller-listing::chunk_3` — Điều 31 | 0.2356 | ✅ chứa "được hiểu là đã bao gồm mọi chi phí" | Trích đúng khoản 2 Điều 31 |

**Bao nhiêu câu trả về chunk liên quan trong top-3? 5 / 5.**
**Điểm chunk-level theo rubric: 9 / 10** (Q3 chỉ được 1 vì chunk chứa đáp án đứng top-2 chứ không phải top-1).

### Phân tích theo 5 tiêu chí

| Câu hỏi phân tích | Ghi nhận từ số liệu của tôi |
|---|---|
| **Precision** | 5/5 query có chunk chứa đáp án trong top-3. Nhưng chỉ 4/5 ở top-1 → precision@1 = 80%. |
| **Chunk coherence** | Chunk theo Điều giữ được cả điều kiện lẫn ngoại lệ trong cùng ngữ cảnh. Ví dụ Q5: khoản 1 và khoản 2 Điều 31 nằm chung một chunk, nên "trừ trường hợp các bên có thỏa thuận khác" không bị tách khỏi quy tắc mặc định. Với `fixed`/`recursive` thì Điều 31 bị cắt giữa hai khoản. |
| **Metadata utility** | Xem A/B bên dưới — filter **giảm nhiễu thật**, không loại nhầm đáp án. |
| **Grounding** | Mọi câu trả lời đều truy vết được về `doc_id::chunk_N` + `source_url` nhờ context đánh số. Tôi cố tình dùng mock LLM trả lại chính context để **nhìn thấy** agent được cho ăn gì, thay vì để LLM "nói trơn tru" che mất lỗi retrieval. |
| **Failure case** | Xem mục dưới. |

### A/B metadata filter (Q4)

| | Top-1 | Top-2 | Top-3 |
|---|---|---|---|
| **Không filter** | `nd85-2021::chunk_5` (buyer) 0.3591 | `returns-policy::chunk_2` (seller, **bản 2013**) 0.2388 | `nd52-dang-ky-thong-bao-website::chunk_5` (seller) 0.1417 |
| **Có filter** `{"customer_role":"buyer"}` | `nd85-2021::chunk_5` 0.3591 | `nd85-2021::chunk_2` 0.1221 | `nd52-quy-trinh...::chunk_8` 0.1178 |

**Kết quả A/B: KHÁC NHAU.** Không filter thì 2/3 slot bị chiếm bởi tài liệu `seller`, trong đó top-2 là **bản 2013** — cùng chủ đề "điều kiện giao dịch chung", cùng từ vựng, nhưng **đáp án ngược lại** (bản 2013 không liệt kê chính sách kiểm hàng). Nếu chunk top-1 vô tình rớt hạng, agent sẽ tự tin trả lời "không bắt buộc" và trích đúng một văn bản có thật — đây là kiểu sai nguy hiểm nhất vì nó **có nguồn**. Filter `customer_role=buyer` loại sạch nhóm 2013 khỏi tập ứng viên trước khi xếp hạng, nên context không còn mâu thuẫn.

Đánh đổi phải ghi nhận: filter là **precision đổi lấy recall**. Nếu người dùng là `seller` hỏi đúng câu này, filter `buyer` sẽ giấu mất câu trả lời đúng. Cách sửa là gắn `customer_role: both` cho tài liệu áp dụng cho cả hai bên, hoặc filter theo tập giá trị (`role in {buyer, both}`) thay vì so bằng tuyệt đối.

### Failure case có bằng chứng — Q3

**Query:** "Cơ chế rà soát và xác nhận nội dung hợp đồng phải hiển thị những thông tin gì cho khách hàng trước khi đặt hàng?"
**Gold:** Điều 18 khoản 1 — tên hàng hóa/số lượng/chủng loại; phương thức và thời hạn giao hàng; **tổng giá trị hợp đồng** và chi tiết phương thức thanh toán.

**Bằng chứng top-3 (strategy của tôi, `heading`):**

```
1. score=+0.3495  doc_id=nd52-quy-trinh-dat-hang-truc-tuyen  chunk=4
   ## Điều 18. Rà soát và xác nhận nội dung hợp đồng
   3. Cho phép khách hàng sau khi rà soát những thông tin nói trên được lựa chọn hủy giao dịch...
2. score=+0.3067  doc_id=nd52-quy-trinh-dat-hang-truc-tuyen  chunk=3   <-- chunk CHỨA đáp án
3. score=+0.2313  doc_id=seller-listing  chunk=5
-> điểm chunk-level: 1 — anchor nằm ở top-2, không phải top-1
```

**Bằng chứng cùng query với `fixed` (chunk_size=500, overlap=50):**

```
1. score=+0.3691  doc_id=nd52-quy-trinh-dat-hang-truc-tuyen  chunk=2
   "sử dụng chức năng đặt hàng trực tuyến được coi là đề nghị giao kết hợp đồng..."  (Điều 17!)
2. score=+0.2122  doc_id=seller-listing  chunk=7
3. score=+0.2064  doc_id=seller-listing  chunk=1
-> điểm chunk-level: 0 — không chunk nào chứa anchor (ĐÚNG doc_id nhưng SAI section)
```

**Trường hợp còn rõ hơn — `fixed` ở Q2:** cả **3/3 slot đều là tài liệu gold** `nd52-quy-che-hoat-dong-san`, nhưng **không slot nào chứa "ít nhất 5 ngày"**:

```
1. score=+0.2860  doc_id=nd52-quy-che-hoat-dong-san  chunk=0   # tiêu đề + khoản 1-2
2. score=+0.2604  doc_id=nd52-quy-che-hoat-dong-san  chunk=3   # "...tại Điều 69 Nghị định này; k) Biện pháp..."
3. score=+0.2266  doc_id=nd52-trach-nhiem-nguoi-ban-tren-san  chunk=1
-> điểm chunk-level: 0 — không chunk nào chứa anchor (ĐÚNG doc_id nhưng SAI section)
```

Đây chính xác là hiện tượng lab cảnh báo: chiếm trọn slot bằng đúng tài liệu gold mà không chunk nào chứa câu trả lời. Chấm theo `doc_id` thì `fixed` được 2/2 ở câu này; chấm theo chunk thì 0.

**Nguyên nhân:**

1. Chunk chứa câu trả lời (danh sách a/b/c của khoản 1) là **danh sách gạch đầu dòng ngắn, mật độ từ khóa "rà soát/xác nhận" thấp**, trong khi chunk khoản 3 lặp lại nguyên cụm "sau khi rà soát những thông tin nói trên" → cosine đo **độ giống chủ đề**, không đo **mật độ thông tin trả lời được**. Chunk nói *về* câu hỏi thắng chunk *trả lời* câu hỏi.
2. Với `fixed`, ranh giới 500 ký tự rơi vào giữa Điều 17 và Điều 18, tách phần dẫn của Điều 18 khỏi danh sách a/b/c → không chunk nào còn đủ ngữ cảnh.
3. Không có overlap ở `heading` nên mỗi thông tin chỉ có **một cơ hội** lọt top-k.

**Đề xuất sửa (chưa áp dụng để giữ so sánh công bằng trong buổi lab):**

- Chunk ở mức **khoản** thay vì mức **Điều** cho các Điều có danh sách liệt kê, và gắn lại cả tiêu đề Điều **lẫn câu dẫn của khoản** vào từng mảnh — mở rộng đúng cơ chế `keep_breadcrumb` đang có.
- Thêm overlap ~15% giữa các khoản liền nhau trong cùng một Điều.
- Ở tầng retrieval: lấy top-8 rồi rerank, hoặc "chunk mở rộng" — retrieve ở mức khoản nhưng nạp vào context cả Điều chứa nó.

### Phát hiện đáng giá nhất: chấm doc_id vs chấm chunk

Tôi chấm cả hai cách trên đúng cùng một lần chạy:

| Strategy | Doc-level (gold `doc_id` có trong top-3) | Chunk-level (chunk có chứa anchor) |
|---|---|---|
| heading | **10 / 10** | **9 / 10** |
| heading_nobreadcrumb | **10 / 10** | 7 / 10 |
| llm_semantic | **10 / 10** | **9 / 10** |
| fixed | **10 / 10** | **6 / 10** |
| recursive | **10 / 10** | 7 / 10 |
| sentence | **10 / 10** | 7 / 10 |

Chấm theo `doc_id` thì **mọi strategy đều hoàn hảo 10/10 và không phân biệt được gì**. Chấm ở mức chunk thì khoảng cách hiện ra ngay. Đúng hiện tượng lab cảnh báo: các section trong cùng một tài liệu nói về cùng chủ đề nên điểm sát nhau, section nào lọt top-3 gần như ngẫu nhiên — một strategy có thể chiếm trọn cả ba slot bằng đúng tài liệu gold mà **không chunk nào chứa câu trả lời**.

### Ablation: breadcrumb có thực sự cần không?

`heading` và `heading_nobreadcrumb` khác nhau đúng một biến (`keep_breadcrumb`, kèm `max_chunk_size` nhỏ hơn để buộc phải cắt nhỏ section): **9/10 → 7/10**, và số chunk nhảy từ 50 lên 108. Khi một Điều dài bị cắt thành nhiều mảnh mà không gắn lại tiêu đề, mảnh thứ hai trở đi mất hoàn toàn ngữ cảnh "đây là Điều nào" — nhìn thấy rõ trong output: chunk top-1 của `fixed`/`nobreadcrumb` thường bắt đầu bằng một mảnh câu cụt như `", chính xác, dễ tìm và dễ hiểu; b) Được sắp xếp..."`.

### Giới hạn phải ghi rõ

- **42 test đều dùng `MockEmbedder`**, và tôi chạy benchmark thêm một lần bằng mock để đối chứng: kết quả là **heading 0/10, fixed 0/10, sentence 0/10, recursive 2/10** — gần như nhiễu (`report/bench_output_mock.txt`). Mock là hash MD5, không mang ngữ nghĩa, nên **không thể dùng để kết luận strategy nào tốt hơn**.
- `LexicalEmbedder` của tôi là TF-IDF: đo **trùng từ**, không đo ngữ nghĩa. Nó hợp với văn bản pháp luật vì câu hỏi thường dùng lại đúng thuật ngữ của văn bản, nhưng sẽ hỏng với câu hỏi diễn đạt lại (xem cặp 1 mục 4). Con số 9/10 ở trên là **9/10 với embedder lexical**, không phải 9/10 tuyệt đối.
- `LLMSemanticChunker` trong buổi lab này **chưa gọi LLM thật** (không có `OPENAI_API_KEY`) nên nó rơi về `HeadingChunker` — đó là lý do hai dòng có kết quả trùng nhau. Fallback được thiết kế để không bao giờ crash; trạng thái fallback được in ra ở dòng `LLM :` trong output.
- Tôi không cài được `requirements-local.txt` (PyTorch) trong thời lượng lab, nên chưa có số liệu với embedding đa ngữ thật.

**Điều hay nhất tôi học được từ nhóm:** [điền sau demo]

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi | 9 / 10 |
| Hoàn thiện code (42/42 test pass) | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất của tôi | 9 / 10 |
| **Tổng phần cá nhân** | **58 / 60** |
