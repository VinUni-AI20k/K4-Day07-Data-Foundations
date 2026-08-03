# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trương Quang Minh  
**Nhóm/Lớp:** TeamB - E402  
**Ngày hoàn thiện:** 03/08/2026

> Báo cáo này mô tả phần cài đặt cá nhân trong `src` và kết quả chạy thực tế trên bộ tài liệu Shopee tiếng Việt của lớp K4. Chiến lược cá nhân là `FixedSizeChunker(chunk_size=400, overlap=50)` và backend dùng để đánh giá là `paraphrase-multilingual-MiniLM-L12-v2` thông qua `LocalEmbedder`.

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự cosine (Bài tập 1.1)

**Độ tương tự cosine cao nghĩa là gì?**

Độ tương tự cosine cao nghĩa là hai vector có hướng gần nhau, do đó hai văn bản thường biểu diễn nội dung hoặc ngữ cảnh tương tự. Phép đo quan tâm đến góc giữa hai vector thay vì độ lớn tuyệt đối của chúng.

**Ví dụ có độ tương tự cao:**

- Câu A: “Hôm nay trời rất nóng nên tôi bật điều hòa.”
- Câu B: “Thời tiết hôm nay quá nóng, tôi phải mở máy lạnh.”
- Hai câu cùng nói về thời tiết nóng và nhu cầu làm mát; “điều hòa” và “máy lạnh” là hai cách diễn đạt gần nghĩa.

**Ví dụ có độ tương tự thấp:**

- Câu A: “Hôm nay trời rất nóng nên tôi bật điều hòa.”
- Câu B: “Tôi đang học lập trình Python để xây dựng ứng dụng AI.”
- Hai câu thuộc hai chủ đề khác nhau: thời tiết/làm mát và lập trình/trí tuệ nhân tạo.

**Tại sao cosine similarity thường được ưu tiên hơn Euclidean distance cho text embeddings?**

Với embedding văn bản, hướng vector thường mang thông tin ngữ nghĩa quan trọng hơn độ lớn. Cosine similarity chuẩn hóa theo độ dài của hai vector nên ít bị ảnh hưởng bởi chuẩn vector, trong khi khoảng cách Euclid có thể thay đổi chỉ vì độ lớn khác nhau dù hướng vẫn tương tự. Khi embedding đã được chuẩn hóa L2, xếp hạng theo tích vô hướng cũng tương đương xếp hạng theo cosine.

### Bài toán chunking (Bài tập 1.2)

Với tài liệu 10.000 ký tự, `chunk_size = 500`, `overlap = 50`, bước trượt là `500 - 50 = 450`. Số chunk là:

`ceil((10000 - 500) / 450) + 1 = 23`.

Khi tăng overlap lên 100, bước trượt còn 400 và số chunk là:

`ceil((10000 - 500) / 400) + 1 = 25`.

Overlap lớn hơn giúp giữ lại ngữ cảnh nằm sát ranh giới giữa hai chunk, giảm nguy cơ một ý hoặc một câu quan trọng bị cắt rời. Đổi lại, hệ thống tạo nhiều chunk hơn, lưu dữ liệu trùng lặp hơn và tốn thêm chi phí embedding/truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ

**Chiến lược cá nhân dùng trong benchmark:** Tôi chọn `FixedSizeChunker` với kích thước 400 ký tự và overlap 50 ký tự. Bước trượt 350 giúp các ý nằm sát biên xuất hiện ở hai chunk liên tiếp, trong khi kích thước cố định giúp số lượng và chi phí embedding dễ dự đoán; nhược điểm là vẫn có thể cắt ngang câu hoặc điều khoản.

**`SentenceChunker.chunk`**

Tôi dùng biểu thức chính quy `(?<=[.!?])\s+`: positive lookbehind giữ lại dấu kết thúc câu và tách tại một hoặc nhiều ký tự trắng theo sau dấu `.`, `!` hoặc `?`. Các câu được `strip()`, phần rỗng bị loại bỏ, sau đó ghép thành từng nhóm không vượt quá `max_sentences_per_chunk`. Chuỗi rỗng trả về danh sách rỗng và giá trị số câu tối đa được chặn tối thiểu ở 1.

**`RecursiveChunker.chunk` / `_split`**

Thuật toán ưu tiên ranh giới có cấu trúc lớn trước: đoạn văn (`\n\n`), dòng (`\n`), câu (`. `), từ (` `), rồi mới cắt cứng. Nếu toàn bộ đoạn đã ngắn hơn `chunk_size`, đây là base case và đoạn được trả về ngay. Nếu separator hiện tại không tồn tại hoặc một phần vẫn quá dài, hàm đệ quy chuyển sang separator có độ ưu tiên thấp hơn; khi hết separator, văn bản được cắt theo đúng kích thước để không lặp vô hạn.

### Lớp `EmbeddingStore`

**`add_documents` + `search`**

Mỗi `Document` được chuyển thành một record gồm id duy nhất, nội dung, metadata có `doc_id`, và vector do `embedding_fn` tạo ra. Store ưu tiên ChromaDB nếu thư viện khả dụng, nếu không sẽ lưu trong danh sách in-memory. Với backend in-memory, truy vấn được embed một lần, tính tích vô hướng với mọi record rồi dùng `heapq.nlargest` để lấy tối đa `top_k` kết quả theo điểm giảm dần; `LocalEmbedder` chuẩn hóa L2 nên tích vô hướng tương ứng cosine similarity.

**`search_with_filter` + `delete_document`**

Metadata được lọc trước khi xếp hạng: record chỉ được giữ nếu mọi cặp khóa–giá trị trong `metadata_filter` khớp chính xác. Khi xóa, toàn bộ chunk có `metadata['doc_id'] == doc_id` bị loại; hàm so sánh kích thước trước/sau để trả về `True` nếu thực sự có dữ liệu được xóa, ngược lại trả về `False`.

### Tác tử `KnowledgeBaseAgent.answer`

Agent truy xuất top-k chunk, đánh số từng nguồn và ghép chúng vào phần `Context` của prompt. Prompt yêu cầu chỉ trả lời dựa trên ngữ cảnh được cung cấp và phải nói rõ khi ngữ cảnh không đủ, sau đó đặt câu hỏi ở cuối để LLM sinh câu trả lời. Cấu trúc này hạn chế việc trả lời dựa trên kiến thức ngoài corpus và giúp truy vết nguồn theo từng chunk.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

### Kết quả kiểm thử

Lệnh đã chạy:

```text
.\.venv\Scripts\python.exe -m pytest tests -v
```

Kết quả rút gọn:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- D:\VIN\LAB07\Day07_2A202601212_TruongQuangMnv\Scripts\python.exe           
cachedir: .pytest_cache                        
rootdir: D:\VIN\LAB07\Day07_2A202601212_TruongQuangMinh
plugins: anyio-4.14.2
collected 42 items

tests/test_solution.py ..........................................       [100%]

============================= 42 passed in 0.27s ==============================
```

**Số lượng bài test vượt qua:** 42 / 42.

Các nhóm chức năng đã vượt kiểm thử gồm cấu trúc dự án, ba chunker, cosine similarity, so sánh chiến lược chunking, thêm/tìm kiếm/lọc/xóa trong `EmbeddingStore`, và `KnowledgeBaseAgent`.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Quy ước trước khi chạy: “cao” khi hai câu gần nghĩa; “thấp” khi khác chủ đề. Điểm thực tế được tính bằng `compute_similarity(LocalEmbedder()(A), LocalEmbedder()(B))` với cùng mô hình đa ngôn ngữ dùng trong benchmark.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua có thể gửi yêu cầu trả hàng trong vòng 15 ngày. | Thời hạn yêu cầu trả hàng của người mua là mười lăm ngày. | Cao | 0.8921 | Đúng |
| 2 | Bộ phận chăm sóc khách hàng Shopee hoạt động 24/7. | Khách hàng có thể liên hệ hỗ trợ Shopee vào mọi thời điểm. | Cao | 0.7283 | Đúng |
| 3 | Shopee có thể khóa vĩnh viễn tài khoản người bán gian lận. | ShopeePay hỗ trợ thanh toán bằng ví điện tử. | Thấp | 0.5001 | Không |
| 4 | Bảo hành qua Shopee dự kiến mất từ 20 đến 45 ngày làm việc. | Thời gian xử lý bảo hành tại Shopee khoảng hai mươi đến bốn mươi lăm ngày. | Cao | 0.8047 | Đúng |
| 5 | Người bán không được đăng sản phẩm vũ khí. | Lịch sử trò chuyện được lưu tối đa 180 ngày. | Thấp | -0.1145 | Đúng |

Kết quả phù hợp với dự đoán ở 4/5 cặp. Cặp 3 bất ngờ nhất vì hai câu khác ý nhưng vẫn đạt 0,5001; nguyên nhân có thể là cả hai cùng chứa các tín hiệu miền “Shopee/người bán/thanh toán”, khiến mô hình nhận ra một phần ngữ cảnh chung. Ngược lại, ba cặp diễn đạt tương đương đều có điểm trên 0,72, cho thấy LocalEmbedder phản ánh ngữ nghĩa tốt hơn backend mock.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

### Cấu hình chạy

- Corpus: 10 chính sách Shopee tiếng Việt trong `data/k4_ecommerce`.
- Các nhóm nội dung: bảo hành, bảo mật, sản phẩm cấm/hạn chế, chống gian lận, trả hàng/hoàn tiền, vận chuyển, điều khoản dịch vụ, CSKH, đăng bán và thanh toán.
- Corpus validator: **ĐẠT checklist**; có 4 tài liệu `buyer`, 3 tài liệu `seller`, 3 tài liệu `both`, và manifest `sources.csv` khớp đủ 10 file.
- Chunker cá nhân: `FixedSizeChunker(chunk_size=400, overlap=50)`.
- Số chunk đã nạp: **625**.
- Embedding: `LocalEmbedder` với `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- `top_k = 3`; chỉ câu 5 lọc trước bằng `metadata_filter={"customer_role": "seller"}` theo bộ benchmark chung của nhóm.

| # | Câu hỏi chung của nhóm | Gold answer | Top-1 chunk truy xuất được | Score | Relevant? | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---|---:|---|---|
| 1 | Tôi có bao nhiêu ngày để yêu cầu trả hàng kể từ khi đơn hàng giao thành công? | 15 ngày; thực phẩm tươi sống/đông lạnh là 24 giờ. | `chinh-sach-van-chuyen::chunk_41`: thời hạn khiếu nại tiền hàng thiếu. | 0.7260 | Không ở top-1; đúng ở top-2 | Top-2 (`chinh-sach-tra-hang-hoan-tien::chunk_8`, 0.6653) chứa đầy đủ mốc 15 ngày/24 giờ. |
| 2 | Thời gian xử lý bảo hành dự kiến là bao lâu? | 20–45 ngày làm việc kể từ lúc Shopee nhận sản phẩm, tùy linh kiện. | `chinh-sach-bao-hanh::chunk_11`: đúng đoạn thời gian bảo hành. | 0.6536 | Có | Top-1 chứa đúng 20–45 ngày và điều kiện phụ thuộc linh kiện. |
| 3 | Đơn hàng nào không hỗ trợ vận chuyển? | Đơn trên 50.000.000 VNĐ tổng giá trị hàng hóa theo cách tính của chính sách. | `chinh-sach-van-chuyen::chunk_23`: quy định đóng gói và quyền từ chối vận chuyển. | 0.6160 | Không | Cả top-3 cùng chủ đề vận chuyển nhưng không chứa ngưỡng 50 triệu đồng. |
| 4 | Lịch sử trò chuyện với chăm sóc khách hàng lưu trữ tối đa bao lâu? | Tối đa 180 ngày. | `chinh-sach-bao-hanh::chunk_11`: thời gian bảo hành 20–45 ngày. | 0.6119 | Không | Top-3 bị nhiễu bởi các đoạn có biểu thức thời gian, không chứa mốc 180 ngày. |
| 5 | Người bán vi phạm chính sách sẽ bị áp dụng những chế tài nào? | Xóa sản phẩm; giới hạn, đình chỉ/xóa tài khoản; cấn trừ số dư, phong tỏa rút tiền và các chế tài khác. | `chinh-sach-cam-han-che-san-pham::chunk_2`: đúng danh sách chế tài. | 0.7154 | Có | Filter `seller` đưa đúng mục chế tài lên top-1. |

Đối chiếu với vị trí gold answer cho thấy **3 / 5 câu có chunk liên quan trong top-3**: câu 1 ở top-2, câu 2 và 5 ở top-1. Câu 3 và 4 thất bại vì các đoạn có từ khóa gần nghĩa hoặc biểu thức thời gian được xếp cao hơn đoạn chứa con số chính xác. Do `demo_llm` trong benchmark chỉ in context preview thay vì sinh đáp án hoàn chỉnh, tôi chấm thận trọng 1 điểm cho mỗi câu có context liên quan, tổng **3/10**.

**Điều hay nhất tôi học được qua quá trình so sánh/demo:**

Chất lượng RAG phụ thuộc đồng thời vào dữ liệu, ranh giới chunk và embedding; 42/42 unit test chỉ chứng minh code tuân thủ giao diện. LocalEmbedder cải thiện rõ rệt so với mock và metadata filter giúp câu 5 trả đúng mục chế tài. Với fixed-size chunking, overlap bảo vệ phần nào ngữ cảnh ở biên nhưng query 3–4 cho thấy việc cắt theo ký tự vẫn có thể làm giảm độ chính xác ở các điều khoản ngắn hoặc thông tin rất cụ thể.

---

## Tự đánh giá (Phần cá nhân)

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — 42/42 tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 |
| **Tổng phần cá nhân** | **53 / 60** |

Điểm tự đánh giá được giữ thận trọng: phần cài đặt vượt toàn bộ kiểm thử và LocalEmbedder truy xuất đúng context cho 3/5 câu, nhưng benchmark chưa dùng LLM sinh đáp án hoàn chỉnh nên không tự chấm trọn 2 điểm cho các câu này.
