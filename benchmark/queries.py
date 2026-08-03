"""Bộ 5 câu hỏi đánh giá (benchmark) cho corpus K4 — ASOS product listings.

Gold answer + expected_doc_ids được đối chiếu trực tiếp từ nội dung tài liệu thật
trong `data/k4_asos_products/` (giá, chất liệu, cách bảo quản, danh mục, tính năng).

Mỗi mục:
  id                : số thứ tự (1..5)
  type              : loại câu hỏi — giữ đa dạng để không hỏi 5 câu giống nhau
  query             : câu hỏi (tiếng Anh, khớp `language: en` của corpus → retrieval tốt)
  query_vi          : bản tiếng Việt để trình bày trong REPORT_NHOM
  gold_answer       : câu trả lời chuẩn, kiểm chứng được từ tài liệu
  metadata_filter   : dict truyền vào search_with_filter(), hoặc None nếu không lọc
  expected_doc_ids  : doc_id GỐC (chưa ::chunk_i) chứa thông tin trả lời — dùng chấm top-3
  evidence          : trích/căn cứ trong tài liệu (mục nào) để người chấm verify nhanh
"""

BENCHMARK = [
    {
        "id": 1,
        "type": "attribute-care-fabric",
        "query": "Which item must be dry cleaned only, and what is it made of?",
        "query_vi": "Sản phẩm nào phải giặt khô, và sản phẩm đó làm từ chất liệu gì?",
        "gold_answer": (
            "adidas Originals Plus three stripe bralet in black — 'Dry clean only', "
            "chất liệu 100% Cotton."
        ),
        "metadata_filter": None,
        "expected_doc_ids": ["asos-adidas-originals-plus-three-stripe-bralet-in-black"],
        "evidence": "Mục 'Look After Me' (Dry clean only) + 'About Me' (100% Cotton). "
                    "Là sản phẩm DUY NHẤT ghi dry clean only trong corpus.",
    },
    {
        "id": 2,
        "type": "price-lookup",
        "query": "How much does the ASOS EDITION satin cami maxi dress with full skirt cost?",
        "query_vi": "Đầm maxi ASOS EDITION satin cami (chân váy xòe, dusky blue) giá bao nhiêu?",
        "gold_answer": "£110.00",
        "metadata_filter": None,
        "expected_doc_ids": ["asos-asos-edition-satin-cami-maxi-dress-with-full-skirt-in-dusky-blue"],
        "evidence": "Front matter price_gbp: 110.00 + mục 'Product details' (Gia niem yet: GBP 110.00).",
    },
    {
        "id": 3,
        "type": "metadata-filter",  # CÂU BẮT BUỘC dùng metadata filter (yêu cầu rubric)
        "query": "Among the outerwear, which coat is made of faux fur?",
        "query_vi": "Trong nhóm áo khoác, sản phẩm nào làm từ lông giả?",
        "gold_answer": "Daisy Street mid-length faux fur coat in wavy checkerboard print.",
        "metadata_filter": {"category_group": "outerwear"},
        "expected_doc_ids": ["asos-daisy-street-mid-length-faux-fur-coat-in-wavy-checkerboard-print"],
        "evidence": "Lọc category_group=outerwear (4 doc: bershka, daisy-street, jdy, miss-selfridge); "
                    "mục 'About Me' của daisy-street ghi 'Super-soft faux fur'.",
    },
    {
        "id": 4,
        "type": "multi-attribute-multi-result",
        "query": "I want a black halterneck item for the beach — what options are there?",
        "query_vi": "Tôi muốn món màu đen, kiểu cổ yếm để đi biển — có những lựa chọn nào?",
        "gold_answer": (
            "Hai lựa chọn: Public Desire cut out midi beach dress in black (halterneck, thigh split) "
            "và Hollister co-ord halterneck bikini top in black."
        ),
        "metadata_filter": None,
        "expected_doc_ids": [
            "asos-public-desire-cut-out-midi-beach-dress-in-black",
            "asos-hollister-co-ord-halterneck-bikini-top-in-black",
        ],
        "evidence": "Cả hai đều color=black + 'Halterneck style' trong mục 'Dac diem'. "
                    "Câu multi-result: top-3 nên chứa ít nhất một trong hai.",
    },
    {
        "id": 5,
        "type": "feature-audience",
        "query": "Is there a maternity dress, and how is it designed to fit?",
        "query_vi": "Có đầm bầu không, và được thiết kế vừa vặn ra sao?",
        "gold_answer": (
            "ASOS DESIGN maternity cami wrap midi dress with lace-up back — "
            "'Designed to fit you from bump to baby', wrap front, lưng shirred co giãn, £30.00."
        ),
        "metadata_filter": None,  # tùy chọn: {"fit_line": "maternity"} (chỉ 1 doc)
        "expected_doc_ids": ["asos-asos-design-maternity-cami-wrap-midi-dress-with-lace-up-back"],
        "evidence": "Mục 'Dac diem' ('Designed to fit you from bump to baby', wrap front, shirred stretch back).",
    },
]
