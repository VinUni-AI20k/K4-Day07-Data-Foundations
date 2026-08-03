"""Nạp .env trước khi pytest import bộ test.

`tests/test_solution.py` đọc `LAB_SOLUTION_PACKAGE` bằng `os.getenv` ngay lúc
import, mà pytest thì không tự đọc file `.env`. conftest.py ở thư mục gốc được
nạp TRƯỚC mọi test module, nên đây là chỗ duy nhất kịp đặt biến môi trường.

`override=False`: biến đã set sẵn trong shell vẫn thắng file `.env`, để còn chạy
tạm gói khác mà không phải sửa file:

    $env:LAB_SOLUTION_PACKAGE = "src"; python -m pytest tests -q
"""
from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env", override=False)
