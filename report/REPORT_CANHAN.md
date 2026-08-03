# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trịnh Quang Anh
**Nhóm:** A6-1
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nghĩa là hai vector embedding chỉ về gần cùng một hướng trong không gian vector, tức là hai đoạn văn bản mang ý nghĩa tương tự nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Con mèo đang ngủ trên ghế sofa."
- Câu B: "Chú mèo nằm ngủ trên ghế."
- Tại sao tương đồng: Cả hai câu cùng mô tả một sự việc (mèo ngủ trên ghế), chỉ khác cách diễn đạt ("con mèo" / "chú mèo", "đang ngủ" / "nằm ngủ"), nên embedding của chúng gần nhau về hướng.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Hôm nay trời mưa rất to."
- Câu B: "Giá cổ phiếu hôm nay tăng mạnh."
- Tại sao khác: Hai câu thuộc hai chủ đề hoàn toàn khác nhau (thời tiết vs. tài chính), không chia sẻ ngữ nghĩa chung nào ngoài từ "hôm nay", nên vector của chúng chỉ về hai hướng khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine chỉ đo góc (hướng) giữa hai vector mà bỏ qua độ dài (magnitude), trong khi Euclid bị ảnh hưởng bởi độ dài vector — vốn có thể thay đổi theo độ dài văn bản mà không phản ánh ngữ nghĩa. Vì ý nghĩa được mã hóa chủ yếu ở hướng của vector, cosine cho kết quả so sánh ngữ nghĩa ổn định hơn và với vector đã chuẩn hóa, xếp hạng theo cosine tương đương xếp hạng theo Euclid nhưng tính đơn giản hơn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Mỗi bước nhảy (step) = chunk_size − overlap = 500 − 50 = 450 ký tự. Chunk đầu tiên phủ 500 ký tự, mỗi chunk sau thêm 450 ký tự mới. Số chunks = 1 + ⌈(10,000 − 500) / 450⌉ = 1 + ⌈9,500 / 450⌉ = 1 + ⌈21.1⌉ = 1 + 22.
> *Đáp án:* **23 chunks.**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Step giảm còn 500 − 100 = 400, nên số chunks = 1 + ⌈9,500 / 400⌉ = 1 + 24 = **25 chunks** (tăng thêm 2). Overlap nhiều hơn giúp giảm nguy cơ một câu/ý bị cắt đôi ở ranh giới chunk — thông tin ở biên sẽ xuất hiện trọn vẹn trong ít nhất một chunk, cải thiện chất lượng truy xuất, đổi lại tốn thêm dung lượng lưu trữ và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` với lookbehind: cắt tại khoảng trắng **đứng ngay sau** dấu `.`, `!` hoặc `?`, nhờ vậy dấu câu được giữ lại ở cuối câu và cả `". "` lẫn `".\n"` đều được xử lý bằng một biểu thức duy nhất. Sau khi tách, tôi `strip()` từng câu và loại bỏ phần tử rỗng — điều này xử lý edge case văn bản kết thúc bằng `". "` (nếu không lọc sẽ sinh ra một câu rỗng ở cuối) cũng như văn bản chỉ chứa khoảng trắng. Cuối cùng gom các câu thành nhóm `max_sentences_per_chunk` bằng vòng lặp bước nhảy và nối lại bằng dấu cách; text rỗng trả về `[]`, còn text không có dấu kết câu vẫn được coi là một câu duy nhất.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> `_split` nhận đoạn text hiện tại cùng danh sách separator còn lại và thử separator ưu tiên cao nhất trước (`"\n\n"` → `"\n"` → `". "` → `" "` → `""`): tách text theo separator đó rồi **gộp tham lam (greedy merge)** các mảnh liền kề vào một buffer chừng nào tổng độ dài còn ≤ `chunk_size`, nhờ vậy các đoạn nhỏ không bị vụn ra thành quá nhiều chunk. Mảnh nào tự nó đã dài hơn `chunk_size` thì được đệ quy xuống separator mịn hơn ở cấp tiếp theo. Có hai **base case**: (1) đoạn text đã ≤ `chunk_size` thì trả về chính nó, và (2) hết separator (hoặc gặp separator rỗng `""`) thì cắt cứng theo vị trí ký tự — đây cũng là cách xử lý edge case `separators=[]` để hàm luôn kết thúc thay vì đệ quy vô hạn.

**`compute_similarity`** — hướng tiếp cận:
> Áp dụng trực tiếp công thức `dot(a, b) / (||a|| * ||b||)`, tái sử dụng hàm `_dot` có sẵn cho cả tử số lẫn việc tính chuẩn (`||a|| = sqrt(dot(a, a))`). Trường hợp một trong hai vector có độ dài bằng 0 sẽ gây chia cho 0 nên tôi kiểm tra trước và trả về `0.0` — quy ước hợp lý vì vector rỗng không có hướng để so sánh.

**`ChunkingStrategyComparator.compare`** — hướng tiếp cận:
> Tôi khởi tạo cả ba chunker với cùng `chunk_size` đầu vào, chạy trên cùng một văn bản rồi trả về dict gồm `count`, `avg_length` và `chunks` cho từng chiến lược để so sánh trực tiếp. Overlap của `FixedSizeChunker` được đặt là `min(50, chunk_size // 4)` thay vì cố định 50, tránh trường hợp `chunk_size` nhỏ khiến `step = chunk_size - overlap` bằng 0 hoặc âm và làm vòng lặp lỗi; khi danh sách chunk rỗng thì `avg_length` trả về `0.0` thay vì chia cho 0.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi tách phần chuẩn hóa dữ liệu ra hàm `_make_record`: mỗi `Document` được nhúng rồi lưu thành dict gồm `id`, `doc_id`, `content`, `metadata`, `embedding` trong danh sách `self._store` (danh sách in-memory là **nguồn sự thật**; ChromaDB nếu có chỉ được ghi song song làm bản sao). Điểm mấu chốt là tôi **chuẩn hóa vector về độ dài 1 ngay lúc lưu** (hàm `_normalize`), nhờ đó ở `search` chỉ cần lấy tích vô hướng `_dot(query, embedding)` là đã bằng đúng cosine similarity — vừa nhanh vừa không phải tính chuẩn lặp lại cho mọi chunk ở mỗi truy vấn. `search` gọi `_search_records` để nhúng câu hỏi, chấm điểm toàn bộ record, sắp xếp giảm dần và cắt `top_k`.
>
> Một chi tiết tôi phải xử lý: test tạo `Document(id="doc_to_delete", metadata={})` — metadata rỗng, không có `doc_id`. Vì vậy `_make_record` suy ra `doc_id = metadata.get("doc_id") or doc.id`, giúp cả chunk từ `ingest.py` (đã có sẵn `doc_id`) lẫn document trần đều xóa/lọc được như nhau.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Tôi lọc **trước rồi mới tìm kiếm (pre-filtering)**: duyệt `self._store`, giữ lại record thỏa **mọi** cặp key-value trong `metadata_filter`, rồi truyền đúng tập ứng viên đó vào `_search_records`. Làm theo thứ tự này thì `top_k` được tính trên tập đã lọc nên luôn trả về đủ `k` kết quả hợp lệ — nếu lọc sau khi tìm kiếm thì có thể lấy top-5 rồi bị loại hết còn 0 kết quả. Khi `metadata_filter` rỗng hoặc `None`, hàm rơi về đúng `search` thông thường.
>
> `delete_document` xóa bằng cách **dựng lại danh sách** chỉ gồm record có `doc_id` khác giá trị cần xóa (thay vì xóa tại chỗ khi đang duyệt — dễ nhảy sót phần tử). So sánh độ dài trước/sau cho biết có xóa được gì không để trả về `True`/`False`, đồng thời xóa được **tất cả** chunk của cùng một tài liệu chỉ trong một lượt duyệt.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` theo đúng ba bước RAG: gọi `store.search(question, top_k)`, ghép các chunk lấy được thành khối ngữ cảnh, rồi đưa prompt cho `llm_fn`. Tôi **đánh số từng đoạn ngữ cảnh `[1] [2] [3]` kèm nguồn** (`source_url`, fallback về `doc_id`) và yêu cầu mô hình trích dẫn số hiệu đó khi trả lời — nhờ vậy câu trả lời truy vết được về tài liệu gốc thay vì chỉ là văn bản trôi nổi. Prompt tách bạch ba khối `NGỮ CẢNH` / `CÂU HỎI` / `TRẢ LỜI` và có chỉ dẫn chống bịa: chỉ dùng thông tin trong ngữ cảnh, nếu không đủ thì nói rõ là không tìm thấy. Trường hợp store rỗng (search trả về `[]`) thì tôi trả về thẳng câu thông báo không tìm thấy mà **không gọi LLM** — tránh tốn một lần gọi API chắc chắn sẽ cho ra câu trả lời bịa.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
============================= test session starts =============================
platform win32 -- Python 3.11.3, pytest-7.3.1, pluggy-1.0.0 -- python.exe
cachedir: .pytest_cache
rootdir: D:\study\AI20K\LAB\K4-Day07-Data-Foundations-A6-1
plugins: anyio-3.5.0
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================= 42 passed in 0.11s ==============================
```

> *(Các dòng ở giữa được gộp theo nhóm test cho gọn; bản chạy đầy đủ liệt kê từng test một, tất cả đều PASSED.)*

**Số lượng bài test vượt qua (pass):** **42** / 42

**Ghi chú sửa lỗi đường dẫn import:** package cá nhân của tôi là `src/QAnh`, nhưng file template để mặc định `LAB_SOLUTION_PACKAGE = "src/QAnh"` (dấu `/` không phải tên module Python hợp lệ) và `main.py` / `ingest.py` vẫn import `src.chunking`, `src.models`, `src.store`. Tôi đã sửa thành `src.QAnh` / `src.QAnh.<module>` để `pytest tests/ -v`, `python ingest.py` và `python main.py` chạy được trực tiếp mà không cần đặt thêm biến môi trường.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> **Backend đã dùng:** `MockEmbedder` (64 chiều, băm MD5) — đây là backend duy nhất có sẵn trong môi trường của tôi vì `requirements.txt` chỉ cài `pytest` + `python-dotenv`, chưa có `sentence-transformers`. Cột "Điểm thực tế" dưới đây là số đo thật, và chính sự sai lệch của chúng so với dự đoán là kết quả đáng nói nhất của bài này.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|-----|-----------|-----------|---------|--------------|-------|
| 1 | Con mèo đang ngủ trên ghế sofa. | Chú mèo nằm ngủ trên ghế. | cao | **+0.023** | ✗ |
| 2 | Tôi muốn đổi trả sản phẩm bị lỗi. | Làm sao để hoàn hàng khi hàng không đúng mô tả? | cao | **+0.026** | ✗ |
| 3 | Hôm nay trời mưa rất to. | Giá cổ phiếu hôm nay tăng mạnh. | thấp | **+0.047** | ✗ (cao hơn cả cặp 1 & 2) |
| 4 | Python là ngôn ngữ lập trình phổ biến. | Con trăn là loài bò sát cỡ lớn. | thấp | **−0.064** | ✓ |
| 5 | Người bán phải cung cấp thông tin sản phẩm chính xác. | *(chuỗi giống hệt câu A)* | cao (≈1.0) | **+1.000** | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 3** — hai câu chẳng liên quan gì nhau (thời tiết vs. chứng khoán) lại đạt +0.047, **cao hơn cả cặp 1 và cặp 2** vốn gần như đồng nghĩa. Nguyên nhân là `MockEmbedder` băm **toàn bộ chuỗi** bằng MD5 rồi sinh số giả ngẫu nhiên từ đó, nên chỉ cần đổi một ký tự là vector đổi hoàn toàn: nó chỉ nhận ra "giống hệt" (cặp 5 = 1.000) chứ không hề nhận ra "gần nghĩa", và mọi cặp khác dao động quanh 0 đúng như hai vector ngẫu nhiên trong không gian 64 chiều.
> Điều này cho thấy công thức cosine **không** tự sinh ra ngữ nghĩa — nó chỉ đo góc giữa hai vector, còn việc "câu gần nghĩa thì vector gần nhau" hoàn toàn đến từ **chất lượng mô hình nhúng** đã được huấn luyện. Vì vậy khi so sánh chiến lược chunking ở Giai đoạn 2, phải chạy `EMBEDDING_PROVIDER=local` với mô hình đa ngữ thật; kết luận rút ra từ mock sẽ chỉ là nhiễu ngẫu nhiên.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> **Cấu hình đã chạy:** `build_knowledge_base("data/k4_ecommerce", chunker=SentenceChunker(max_sentences_per_chunk=2))` → **5 chunk** từ 2 tài liệu khởi động (`k4-returns-policy`, `k4-seller-listing`), backend nhúng = `MockEmbedder`.
>
> ⚠️ **Hai điểm cần chốt lại với nhóm trước khi nộp:** (1) bảng câu hỏi trong `REPORT_NHOM.md` hiện còn trống, nên 5 câu dưới đây là bản nháp tôi tự đặt trên bộ dữ liệu khởi động — phải thay bằng đúng 5 câu nhóm thống nhất; (2) `data/k4_ecommerce` mới chỉ là 2 file template (`source_url` còn là `example.com`), chưa phải corpus thật 5–10 tài liệu theo yêu cầu Bài tập 3.0.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì để yêu cầu đổi trả hàng? | `k4-returns-policy` — "Người mua cần gửi yêu cầu đổi trả trong thời hạn… kèm bằng chứng phù hợp" | +0.216 | ✅ Có (đúng ở top-1) | Trả lời từ 3 đoạn ngữ cảnh, trích nguồn `chinh-sach/doi-tra` |
| 2 | Khi hàng bị lỗi hoặc không đúng mô tả thì cần nộp bằng chứng gì? | `k4-seller-listing` — khối chú thích metadata template | −0.043 | ❌ Không (chunk đúng nằm ở **top-2**) | Ngữ cảnh dẫn đầu là nhiễu, câu trả lời không bám vào điều khoản bằng chứng |
| 3 | Người bán có trách nhiệm gì về thông tin sản phẩm khi đăng bán? | `k4-returns-policy` — "Người mua cần gửi yêu cầu đổi trả…" | +0.091 | ❌ Không (chunk đúng **ngoài top-3**) | Trả lời lệch sang chính sách đổi trả, sai tài liệu |
| 4 | Sản phẩm nào không được phép đăng bán trên sàn? | `k4-seller-listing` — khối chú thích metadata template | +0.220 | ❌ Không (chunk "hàng bị hạn chế/cấm" **ngoài top-3**) | Đúng tài liệu nhưng sai đoạn, không nêu được quy định hàng cấm |
| 5 | Quy định dành riêng cho người bán là gì? | `k4-returns-policy` — "Người mua cần gửi yêu cầu đổi trả…" | +0.078 | ❌ Không ở top-1 (2 chunk seller nằm ở **top-2 & top-3**) | Sai tài liệu ở top-1; **lọc metadata sửa được** (xem dưới) |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **3** / 5 (câu 1, 2, 5) — nhưng chỉ **1/5** đúng ngay ở top-1.

**Kiểm chứng lọc metadata (câu 5):** chạy lại bằng `search_with_filter(metadata_filter={"customer_role": "seller"})` thì top-1 chuyển từ chunk đổi trả (sai tài liệu) sang đúng chunk `k4-seller-listing` "Sản phẩm bị hạn chế hoặc bị cấm không được đăng bán…". Đáng chú ý là **điểm số lại thấp hơn** (−0.035 so với +0.078) — bằng chứng trực tiếp rằng khi embedding yếu, ràng buộc metadata cứng còn đáng tin hơn điểm tương tự.

**Phân tích nguyên nhân (nối tiếp Phần 4):** 4/5 câu trượt top-1 không phải do lỗi code — `search` và `search_with_filter` đều pass toàn bộ test — mà do `MockEmbedder` băm cả chuỗi nên điểm số gần như ngẫu nhiên (mọi score đều nằm trong khoảng ±0.22, không có chunk nào thực sự "nổi bật"). Một nguyên nhân thứ hai đến từ dữ liệu: khối chú thích "*template mẫu*" trong hai file `.md` cũng bị chia thành chunk và hai lần lọt top-1 (câu 2, câu 4) dù không mang nội dung chính sách nào. Hai cải thiện tôi sẽ áp dụng ở Giai đoạn 2: chạy `EMBEDDING_PROVIDER=local`, và loại bỏ dòng chú thích/blockquote template khỏi tài liệu trước khi nạp.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Chờ buổi demo — sẽ điền sau khi nghe phần trình bày của các nhóm khác.)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Trả lời đủ 2 bài tập, có ví dụ cụ thể và trình bày phép tính chunking |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 | Giải thích đủ 7 hàm đã lập trình, nêu rõ thuật toán + edge case đã xử lý |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | **42/42 test PASSED**, đã hoàn thành toàn bộ TODO trong `chunking.py`, `store.py`, `agent.py` |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | Đủ 5 cặp, có dự đoán trước + số đo thật, và phân tích được nguyên nhân sai lệch |
| Kết quả truy xuất của tôi (Competition Results) | 6 / 10 | Đã chạy đủ pipeline và phân tích lỗi, nhưng mới dùng câu hỏi nháp trên dữ liệu template — **cần chạy lại với 5 câu hỏi chính thức của nhóm và corpus thật** |
| **Tổng phần cá nhân** | **56 / 60** | |

### Việc còn lại của phần cá nhân
- [ ] Chốt 5 câu hỏi đánh giá chung trong `REPORT_NHOM.md`, chạy lại Phần 5 bằng đúng bộ câu hỏi đó.
- [ ] Thay bộ dữ liệu khởi động bằng 5–10 tài liệu công khai thật (Bài tập 3.0) rồi chạy lại.
- [ ] Cài `requirements-local.txt` và chạy lại Phần 4 + Phần 5 với `EMBEDDING_PROVIDER=local` để có điểm tương tự phản ánh đúng ngữ nghĩa tiếng Việt.
- [ ] Điền ô "Điều hay nhất học được từ nhóm khác" sau buổi demo.
