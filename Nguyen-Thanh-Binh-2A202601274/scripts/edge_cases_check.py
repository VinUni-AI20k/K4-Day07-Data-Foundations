"""
Kiểm chứng ca biên cho phần code cá nhân (ngoài 42 unit test của lab).

Trả lời 3 câu hỏi mà bộ test KHÔNG kiểm tra:
    1. Chunker có crash / đệ quy vô hạn / sinh chunk vượt chunk_size trên input xấu không?
    2. RecursiveChunker có làm MẤT ký tự (đặc biệt là dấu kết câu) khi cắt không?
    3. compute_similarity có an toàn với vector rỗng / vector 0 không?

Chạy:
    .venv/Scripts/python scripts/edge_cases_check.py
"""
from __future__ import annotations

import io
import sys
from glob import glob
from pathlib import Path

BUNDLE_ROOT = Path(__file__).resolve().parent.parent  # thư mục cá nhân của tôi
REPO_ROOT = BUNDLE_ROOT.parent  # repo chung của nhóm (chứa data/)
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BUNDLE_ROOT))  # src/ của RIÊNG tôi — ưu tiên cao hơn

from src.chunking import RecursiveChunker, SentenceChunker, compute_similarity  # noqa: E402

EDGE_INPUTS = {
    "chuỗi rỗng": "",
    "chỉ khoảng trắng": "     ",
    "một từ dài 1000 ký tự": "a" * 1000,
    "không có separator nào": "x" * 300,
    "kết thúc bằng separator": "aaa\n\nbbb\n\n",
    "nhiều separator liên tiếp": "a\n\n\n\n\n\nb",
    "tiếng Việt có dấu": "Chính sách đổi trả. Người bán phải phản hồi. Hàng lỗi được hoàn tiền. " * 20,
}


def check_chunkers() -> int:
    failures = 0
    print("--- 1. Ca biên của chunker (không lỗi, không vượt chunk_size) ---")
    print(f"{'Input':<28}{'chunk_size':<12}{'#chunk':<9}{'max len':<10}{'vượt ngưỡng'}")
    for name, text in EDGE_INPUTS.items():
        for chunk_size in (10, 50, 400):
            chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)
            over = [chunk for chunk in chunks if len(chunk) > chunk_size]
            failures += len(over)
            longest = max((len(chunk) for chunk in chunks), default=0)
            print(f"{name:<28}{chunk_size:<12}{len(chunks):<9}{longest:<10}{len(over)}")

    for separators in ([], [""], ["|"]):
        chunks = RecursiveChunker(separators=separators, chunk_size=10).chunk("x" * 100)
        assert chunks and all(len(chunk) <= 10 for chunk in chunks), separators
    assert SentenceChunker().chunk("") == []
    assert SentenceChunker().chunk("   ") == []
    assert SentenceChunker(2).chunk("khong co dau cham nao ca") == ["khong co dau cham nao ca"]
    print("Các trường hợp separator rỗng / SentenceChunker rỗng: OK")
    return failures


def check_no_text_loss() -> int:
    print("\n--- 2. RecursiveChunker có nuốt dấu kết câu không? ---")
    demo = RecursiveChunker(chunk_size=4).chunk("aaa. bbb")
    print(f"RecursiveChunker(chunk_size=4).chunk('aaa. bbb') -> {demo}")

    total = lost = 0
    data_root = REPO_ROOT / "data"  # corpus DÙNG CHUNG của nhóm, không copy vào thư mục cá nhân
    patterns = [str(data_root / "**" / "*.md"), str(data_root / "**" / "*.txt")]
    for path in sorted({p for pattern in patterns for p in glob(pattern, recursive=True)}):
        text = io.open(path, encoding="utf-8").read()
        chunks = RecursiveChunker(chunk_size=400).chunk(text)
        in_doc = text.count(".")
        in_chunks = sum(chunk.count(".") for chunk in chunks)
        total += in_doc
        lost += in_doc - in_chunks
        if in_doc != in_chunks:
            print(f"  MẤT {in_doc - in_chunks} dấu chấm ở {path}")
    print(f"Tổng dấu chấm trong corpus = {total} | bị mất sau khi chunk = {lost}")
    return lost


def check_similarity() -> int:
    print("\n--- 3. compute_similarity với vector suy biến ---")
    cases = [
        ("hai vector rỗng", [], [], 0.0),
        ("một vector rỗng", [1.0], [], 0.0),
        ("vector toàn 0", [0.0, 0.0, 0.0], [1.0, 2.0, 3.0], 0.0),
        ("hai vector giống hệt", [1.0, 0.0, 0.0], [1.0, 0.0, 0.0], 1.0),
        ("hai vector ngược nhau", [1.0, 0.0], [-1.0, 0.0], -1.0),
    ]
    failures = 0
    for name, a, b, expected in cases:
        actual = compute_similarity(a, b)
        ok = abs(actual - expected) < 1e-9
        failures += 0 if ok else 1
        print(f"{name:<24}kỳ vọng={expected:<7}thực tế={actual:<10.6f}{'OK' if ok else 'SAI'}")
    return failures


def main() -> int:
    failures = check_chunkers() + check_no_text_loss() + check_similarity()
    print("\n" + ("TẤT CẢ KIỂM CHỨNG BIÊN ĐỀU ĐẠT" if failures == 0 else f"CÓ {failures} VẤN ĐỀ"))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
