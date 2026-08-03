"""
Chiến lược A — ĐƯỜNG CƠ SỞ (baseline): fixed-size + overlap, metadata phẳng.

Đây cũng là ví dụ mẫu cho hợp đồng `Strategy` trong common.py: một file chiến lược
chỉ cần khai báo đúng một biến tên `STRATEGY`.

Không có `decorate` -> chunk giữ nguyên text, metadata đúng những gì front matter cho.
Mục đích: làm mốc so sánh cho chiến lược B (theo điều/khoản) và C (câu + chèn ngữ cảnh).
"""
from __future__ import annotations

from strategies.common import Strategy

CHUNK_SIZE = 500
OVERLAP = 50

STRATEGY = Strategy(
    name=f"A-fixed-{CHUNK_SIZE}/{OVERLAP}",
    build_chunker=lambda package: package.FixedSizeChunker(chunk_size=CHUNK_SIZE, overlap=OVERLAP),
    description=(
        f"Cắt cứng {CHUNK_SIZE} ký tự, chồng lấn {OVERLAP}. Không xử lý ranh giới điều khoản, "
        "không làm giàu metadata — dùng làm mốc để đo xem B và C cải thiện được bao nhiêu."
    ),
)
