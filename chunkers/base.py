"""
chunkers/base.py — Hop dong chung cho MOI chunker cua nhom.

MOI THANH VIEN DOC FILE NAY TRUOC KHI VIET CHUNKER CUA MINH.

Hop dong (contract)
-------------------
Mot chunker chi can hai thu:

    class MyChunker(BaseChunker):
        name = "ten_ngan_khong_dau"

        def chunk(self, text: str) -> list[str]:
            ...

`ingest.build_knowledge_base(data_dir, embedding_fn, chunker=...)` chi goi
`chunker.chunk(text)` va mong doi mot `list[str]`. Khong hon.

Quy tac bat buoc de so sanh giua 4 nguoi CONG BANG
---------------------------------------------------
1. KHONG sua `bench.py`, `ingest.py`, `lexical_embedding.py`, hay bat cu file
   nao trong `src/`. Bon nguoi dung chung corpus, chung 5 query, chung embedder.
   Bien duy nhat duoc thay doi la CHUNKER.
2. Chunker cua ban nam trong file rieng cua ban duoi `chunkers/`. Khong sua file
   cua nguoi khac.
3. Dang ky ten strategy cua ban trong `chunkers/__init__.py` (mot dong).
4. Chien luoc khong duoc trung nhau (yeu cau CP7 cua Lab).

Ba dieu de sai nhat, kiem lai truoc khi chay benchmark
------------------------------------------------------
- `text` rong -> phai tra `[]`, khong duoc crash.
- Khong duoc tra chunk rong hoac chunk chi co khoang trang.
- Chunk vun (chi vai chuc ky tu, kieu "mot dong tieu de tro tron") se an diem
  cao gia tao khi dung TF-IDF, vi vector ngan ma toan tu hiem thi cosine bi
  thoi len. Day la loi that da quan sat duoc trong benchmark cua nhom:
  `RecursiveChunker` sinh ra mot chunk 64 ky tu chi chua dong tieu de va no
  dat score 0.6109 — cao nhat toan bo benchmark — trong khi khong chua mot
  chu nao cua cau tra loi. Hay gop cac manh qua ngan lai (xem `merge_short`).
"""
from __future__ import annotations

import re

# Dong tieu de Markdown: "# ...", "## Dieu 32. ..."
MD_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
# Dong tieu de kieu van ban phap luat: "Dieu 32.", "Chuong V", "Muc 2"
LEGAL_HEADING = re.compile(r"^(Điều|Chương|Mục)\s+\d+[.:]?\s*(.*)$", re.IGNORECASE)
# Dau khoan: "1.", "2." hoac diem: "a)", "b)", "đ)"
CLAUSE_START = re.compile(r"^\s*(\d+\.|[a-zđ]\))\s+")


class BaseChunker:
    """Lop cha. Ke thua no de co san `params()` va cac helper."""

    name = "base"

    def chunk(self, text: str) -> list[str]:
        raise NotImplementedError(
            f"{self.__class__.__name__}.chunk() chua duoc implement."
        )

    def params(self) -> str:
        """In tham so ra bang benchmark. Tu dong doc cac thuoc tinh cua object."""
        items = [
            f"{key}={value!r}"
            for key, value in sorted(vars(self).items())
            if not key.startswith("_")
        ]
        return ", ".join(items) if items else "(khong co tham so)"


# ---------------------------------------------------------------------------
# Helper dung chung — moi nguoi deu goi duoc, khong ai phai viet lai
# ---------------------------------------------------------------------------
def is_heading(line: str) -> bool:
    """Dong nay co phai tieu de khong (Markdown hoac 'Dieu N.')?"""
    stripped = line.strip()
    return bool(MD_HEADING.match(stripped)) or bool(LEGAL_HEADING.match(stripped))


def is_clause_start(line: str) -> bool:
    """Dong nay co bat dau mot khoan/diem khong ('1.', 'a)')?"""
    return bool(CLAUSE_START.match(line))


def split_sections(text: str) -> list[tuple[str, str]]:
    """Cat text thanh list ``(tieu_de, than_section)``.

    Phan mo dau truoc tieu de dau tien co `tieu_de` la chuoi rong.
    """
    sections: list[tuple[str, str]] = []
    current_title = ""
    buffer: list[str] = []

    for line in text.splitlines():
        if is_heading(line):
            if current_title or "".join(buffer).strip():
                sections.append((current_title, "\n".join(buffer).strip()))
            current_title = line.strip()
            buffer = []
        else:
            buffer.append(line)

    if current_title or "".join(buffer).strip():
        sections.append((current_title, "\n".join(buffer).strip()))
    return sections


def merge_short(chunks: list[str], min_size: int = 120) -> list[str]:
    """Gop chunk ngan hon `min_size` vao chunk KE TIEP.

    Chan loi chunk-vun-diem-cao mo ta o docstring dau file. Dung ham nay o
    buoc cuoi cua `chunk()` neu chien luoc cua ban co the sinh manh ngan.
    """
    merged: list[str] = []
    carry = ""
    for chunk in chunks:
        candidate = f"{carry}\n{chunk}".strip() if carry else chunk.strip()
        if len(candidate) < min_size:
            carry = candidate
            continue
        merged.append(candidate)
        carry = ""
    if carry:
        if merged:
            merged[-1] = f"{merged[-1]}\n{carry}".strip()
        else:
            merged.append(carry)
    return merged


def clean(chunks: list[str]) -> list[str]:
    """Strip tung chunk va bo chunk rong. Luon goi truoc khi return."""
    return [chunk.strip() for chunk in chunks if chunk and chunk.strip()]


def attach(title: str, pieces: list[str], every: bool = True) -> list[str]:
    """Gan `title` vao dau cac manh con.

    `every=True`  -> gan vao TAT CA cac manh (giu ngu canh, khuyen dung).
    `every=False` -> chi gan vao manh dau (de lam ablation, chung minh tac dung).
    """
    if not title:
        return list(pieces)
    return [
        f"{title}\n{piece}".strip() if (every or index == 0) else piece.strip()
        for index, piece in enumerate(pieces)
    ]
