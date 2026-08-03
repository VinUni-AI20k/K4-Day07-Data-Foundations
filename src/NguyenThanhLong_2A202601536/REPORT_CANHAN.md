# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Thành Long
**Nhóm:** C53
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Động tương tự Cosine cao có nghĩa là 2 vector embedding đang hướng về gần nhau trong không gian, tức là 2 đoạn văn bản có ý nghĩa ngữ nghĩa tương tự nhau hoặc rất giống nhau*

**Ví dụ có độ tương tự CAO:**
- Câu A: "Cửa hàng sẽ hoàn lại tiền cho khách hàng nếu sản phẩm bị lỗi"
- Câu B: "Người mua được bồi hoàn toàn bộ chi phí khi nhận phải hàng bị hỏng hóc"
- Tại sao tương đồng: Cả hai câu đều nói về một ý nghĩa cốt lõi là bồi hoàn chi phí nếu sản phẩm bị hỏng hóc dù sử dụng bộ từ vựng khác nhau. Mô hình AI sẽ hiểu được ngữ cảnh này và trả về độ tương tự Cosine rất cao."

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách đổi trả hàng được áp dụng trong vòng 7 ngày"
- Câu B: "Thời tiết hôm nay tại Hà Nội có mưa rào vào dông."
- Tại sao khác: Hai câu thuộc chủ đề riêng biệt không có bất kỳ liên hệ nào về mặt ngữ nghĩa nên 2 vector sẽ hướng về 2 phía xa nhau trong không gian vector.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Tại khoảng cách Euclid có bị ảnh hưởng bởi độ lớn của Vector trong khi đó độ tương tự Cosine thì lại không bị ảnh hưởng bởi độ lớn mà chỉ bị ảnh hưởng bởi góc (hướng) giữa 2 vector. Như vậy thì độ dài của đoạn văn không ảnh hưởng đến sự tương đồng ngữ nghĩa.*

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> *Đáp án: 23*

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Theo công thức tính số chunk = ceil((length - overlap) / (chunk_size - overlap)) như vậy overlap tăng lên thì số lượng chunk sẽ tăng lên từ 23 lên 25. Muốn độ chồng chèo (Overlap) tăng lên để bảo toàn ngữ cảnh ở rank giới giữa các chunk tốt hơn, đảm bảo một câu hay một ý tưởng không bị cắt đứt làm đôi khiến mất đi ngữ nghĩa gốc khi truy xuất thông tin.*

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Dùng các biểu thức chính quy để tách câu ngay tại khoảng trắng phía sau các dấu câu, giúp giữ lại nguyên vẹn dấu câu ở cuối phần đứng trước. Ngoại lệ văn bản rỗng được trả về list rỗng, các mảng trắng sinh ra sau khi split cũng được dọn dẹp bằng strip()*

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Thuật toán dùng để quy để cắt văn bản thành mảng theo các separator từ lớn đến nhỏ, nếu mảng nhỏ hơn chunk_size thì ưu tiên gọi đệ quy chui xuống separator mức dưới để cắt tiếp. Base casses là khi chuỗi đã ngắn hơn chunk_size hoặc khi cạn kiệt separator.*

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Lưu trữ trên bộ nhớ (in-memory) bằng cách duyệt list Documents, lấy nội dung và tự tạo Record ID rồi push vào biến list self._stor. Hàm search sẽ hoạt động bằng cách tính một lần vector embedding cho query, sau đó quét tính tích vô hướng cho từng record trong store, cuối cùng sort giảm dần theo điểm và lấy top_k*

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Hàm search_with_filteer bắt buộcp hải lọc tập metadata trước để thu hẹp tập hợp record, sau đó mới tính Similarity cho tập hẹp này, nếu làm ngược (lấy top-k trước rồi mới lọc) thì rất có thể toàn bộ top-k bị lọc sạch sinh ra kết quả rỗng. Hàm delete_document thì nhận list mới từ ListComprehension chỉ chứa các record có doc_id khác với ID truyền vào.
### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Cấu trúc prompt được thiết kế tường minh với 4 thành phần Instruction, Context,  Question và Answer. Context được inject vào bằng cách gọi hàm search lấy ra top-k records, duyệt qua kết quả để bóc nội dung và doc_id, sau đó ghép nối thành một chuỗi dài có đánh số thứ tự để đảm bảo tiêu chí Grounding cho LLM.*

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
=========================== 42 passed in 0.03s ===========================
=== Demo pipeline nạp dữ liệu (ingest.build_knowledge_base) ===
Thư mục dữ liệu: data/k4_ecommerce
Backend nhúng: mock embeddings fallback
Lưu ý: mock chỉ để chạy thử/unit test và KHÔNG phản ánh chất lượng ngữ nghĩa. Ở Giai đoạn 2, đặt EMBEDDING_PROVIDER=local để so sánh retrieval có ý nghĩa.
Đã nạp 128 chunk vào EmbeddingStore

=== Tìm kiếm (EmbeddingStore.search) ===
Câu hỏi: Chunking là gì?
1. score=0.252 source=data/k4_ecommerce/quy-trinh-xu-ly-yeu-cau.md
     -  ✔  ✔  ✔  ✔  Hàng giả, nhái  -  -  ✔  ✔  ✔  -  Hàng đã qua sử dụng  -  -  ✔  ✔  ✔  -  Hàng nguyên vẹn nhưng không cò...
2. score=0.251 source=data/k4_ecommerce/thoi-gian-nhan-tien-hoan.md
   ng quá trình xử lý nếu Người bán có khiếu nại, Shopee sẽ xem xét & thông báo kết quả cuối cùng đến bạn tại mục Thông báo...
3. score=0.220 source=data/k4_ecommerce/phuong-thuc-gui-hang-va-phi-hoan-tra.md
   ả của bạn để được hỗ trợ.  Hoặc bạn cũng có thể chủ động mang hàng ra bưu cục SPX/bưu cục Giao Hàng Nhanh (không cần tha...

=== KnowledgeBaseAgent ===
[DEMO LLM] Generated answer from prompt preview: Instruction: chỉ dùng context; nói rõ khi context không đủ. Context: [1] (Source: quy-trinh-xu-ly-yeu-cau)   -  ✔  ✔  ✔  ✔  Hàng giả, nhái  -  -  ✔  ✔  ✔  -  Hàng đã qua sử dụng  -  -  ✔  ✔  ✔  -  Hàng nguyên vẹn nhưng không còn nhu cầu  ✔  ✔  ✔  ✔  ✔  ✔  Sản phẩm hoàn trả phải còn nguyên seal, tem, hộp sản phẩm  ⚠️ Lưu ý: Lý do trả hàng “Hàng nguyên vẹn nhưng không còn nhu cầu” sẽ được áp dụng nh...
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (Local/OpenAI) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Quy trình trả hàng | Các bước hoàn trả sản phẩm | Cao | ~ 0.85 | Đúng |
| 2 | Sản phẩm này rất tuyệt vời | Tôi cực kỳ thất vọng về sản phẩm này | Thấp | ~ 0.75 | Sai |
| 3 | Tôi muốn mua một chiếc áo thun | Chính sách đổi trả của shop thế nào? | Thấp | ~ 0.12 | Đúng |
| 4 | Chiếc điện thoại này chụp ảnh đẹp | Camera của smartphone này rất sắc nét | Cao | ~ 0.88 | Đúng |
| 5 | Giao hàng nhanh, đóng gói cẩn thận | Thời gian giao hàng lâu, hộp móp méo | Thấp | ~ 0.72 | Sai |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Cặp 2 và 5 cho kết quả bất ngờ nhất vì dù mang ý nghĩa hoàn toàn trái ngược nhau (Tích cực vs Tiêu cực), điểm tương tự vẫn khá cao (trên 0.7). Điều này cho thấy Embeddings thường biểu diễn "ngữ cảnh" hoặc "chủ đề" chung (cùng nói về chất lượng sản phẩm/giao hàng) mạnh hơn là sắc thái khẳng định/phủ định của câu.*

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Quy trình xử lý yêu cầu trả hàng? | "Người Mua đã thanh toán bằng các phương thức thanh toán..." | 0.341 | Có | Trả lời dựa trên Context 1, nhắc về quy trình xử lý... |
| 2 | Thời gian nhận tiền hoàn là bao lâu? | "Bước 4: Tìm đơn hàng với trạng thái ’Đơn hàng sẽ được hoàn trả..." | 0.325 | Có | Đưa ra các mốc thời gian hoàn tiền cho người mua... |
| 3 | Hàng giả có được hoàn tiền không? | "Để đảm bảo tình trạng hàng hoàn trả nguyên vẹn hoặc không hư hỏng..." | 0.353 | Có | Có, Agent sử dụng Context để trả lời được... |
| 4 | Phí gửi hàng hoàn trả ai chịu? | "Đồ lót, Đồ bơi: không hỗ trợ khi đã mặc thử..." | 0.251 | Không rõ ràng | Context không đủ thông tin, Agent báo thiếu thông tin... |
| 5 | Có thể trả hàng vì không còn nhu cầu không? | "Thời Gian Shopee Đảm Bảo đã được quy định trong Điều Khoản Dịch Vụ..." | 0.297 | Có | Agent dựa vào thông tin ShopeeVIP để trả lời... |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Tôi thấy cách các bạn áp dụng chiến lược phân tách theo cấu trúc văn bảm vô cùng hiệu quả. Nó giúp bảo toàn trọn vẹn ngữ nghĩa của từng mục tốt hơn hẳn việc cắt cứng theo kích thước. Điều này cho thấy giai đoạn tiền xử lý văn bản và chọn chiến lược Chunking đóng vai trò quan trọng quyết định chất lượng đầu ra của hệ thống RAG không kém gì bản thân mô hình LLM.*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
