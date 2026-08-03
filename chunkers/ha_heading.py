"""
chunkers/ha_heading.py — Chien luoc cua NGUYEN QUANG HA (2A202601424).

Strategy: chia theo TIEU DE (Dieu / heading Markdown), gan lai breadcrumb.
Trang thai: DA HOAN THANH.

Nguyen ly
---------
Corpus cua nhom la van ban quy pham phap luat, bien soan theo Dieu/Khoan. Moi
Dieu DA LA mot don vi ngu nghia tron ven do con nguoi tao ra. Chunker khong can
tu nghi ra ranh gioi — chi can TON TRONG ranh gioi co san.

Chi tiet quyet dinh ket qua: khi mot Dieu dai hon `max_chunk_size` va buoc phai
cat nho, phai GAN LAI tieu de Dieu vao TUNG manh con. Khong lam vay thi manh
thu hai tro di mat ngu canh "day la Dieu nao".

Gia thuyet da kiem chung
------------------------
Ablation `keep_breadcrumb=True/False` cho 9/10 vs 7/10 (embedder lexical).
=> Phan lon loi the den tu viec gan lai tieu de, khong phai tu "chunk theo
heading" noi chung. Ky thuat nay tai dung duoc o moi domain co tieu de.

Diem yeu da biet
----------------
Khong co overlap: moi thong tin chi co MOT co hoi lot top-k. Thay ro o Q3 —
chunk chua dap an (danh sach a/b/c cua khoan 1 Dieu 18) chi dat top-2 vi chunk
khoan 3 lap lai nguyen cum tu khoa cua cau hoi.
"""
from __future__ import annotations

import re

from src.chunking import RecursiveChunker

from .base import BaseChunker, attach, clean, is_heading


class HeadingChunker(BaseChunker):
    """Cat theo don vi tieu de; section qua dai thi ha xuong RecursiveChunker.

    Tham so:
        max_chunk_size:  nguong ky tu cua mot chunk.
        min_chunk_size:  section ngan hon nguong nay se duoc gop voi section ke
                         tiep (tranh chunk vun chi co moi dong tieu de).
        keep_breadcrumb: khi phai cat nho mot section dai, gan lai chuoi tieu de
                         vao TUNG manh con.
    """

    name = "heading"

    def __init__(
        self,
        max_chunk_size: int = 900,
        min_chunk_size: int = 120,
        keep_breadcrumb: bool = True,
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.keep_breadcrumb = keep_breadcrumb

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = self._merge_tiny_sections(self._split_sections(text))

        chunks: list[str] = []
        for title, body in sections:
            block = f"{title}\n{body}".strip() if title else body.strip()
            if not block:
                continue

            if len(block) <= self.max_chunk_size:
                chunks.append(block)
                continue

            # Section qua dai -> ha xuong recursive, roi GAN LAI tieu de.
            budget = self.max_chunk_size - (len(title) + 1 if title else 0)
            pieces = RecursiveChunker(chunk_size=max(120, budget)).chunk(body)
            chunks.extend(attach(title, pieces, every=self.keep_breadcrumb))

        return clean(chunks)

    # ------------------------------------------------------------------
    def _split_sections(self, text: str) -> list[tuple[str, str]]:
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

    def _merge_tiny_sections(
        self, sections: list[tuple[str, str]]
    ) -> list[tuple[str, str]]:
        """Gop section qua ngan (vd. tieu de H1 don doc) vao section ke tiep."""
        merged: list[tuple[str, str]] = []
        carry_body = ""

        for title, body in sections:
            if len(title) + len(body) < self.min_chunk_size:
                carry_body = f"{carry_body}\n{title}\n{body}".strip()
                continue

            if carry_body:
                # carry_body DA chua dong tieu de cua cac section nho, nen tra
                # ve title rong de khong in lap tieu de hai lan.
                merged.append(("", f"{carry_body}\n{title}\n{body}".strip()))
                carry_body = ""
            else:
                merged.append((title, body))

        if carry_body:
            merged.append(("", carry_body))
        return merged


class LLMSemanticChunker(BaseChunker):
    """Bonus: nho LLM de xuat ranh gioi ngu nghia, co fallback an toan.

    Cach lam: danh so tung dong cua tai lieu, hoi LLM "nhung dong nao la ranh
    gioi bat dau mot y mach lac?", parse ra list so nguyen, roi cat tai do.
    Bat ky loi nao (khong co llm_fn, khong co API key, output khong parse duoc)
    deu quay ve HeadingChunker.

    LLM chi duoc dung o buoc TIEN XU LY (offline, mot lan khi ingest). Retrieval
    va 42 test khong phu thuoc vao no.
    """

    name = "llm_semantic"

    PROMPT = (
        "Ban la cong cu chia nho van ban phap luat de lam RAG.\n"
        "Duoi day la tai lieu, moi dong da duoc danh so.\n"
        "Hay chon cac so dong la NOI BAT DAU mot don vi ngu nghia mach lac "
        "(mot Dieu, mot Khoan tron ven, mot muc FAQ).\n"
        "Nguyen tac: KHONG tach dieu kien khoi ngoai le cua no; khong tach "
        "cau dan khoi danh sach gach dau dong ben duoi.\n"
        "Chi tra ve cac so, cach nhau bang dau phay. Khong giai thich.\n\n"
        "{numbered}\n\nCac so dong bat dau chunk:"
    )

    def __init__(
        self,
        llm_fn=None,
        max_chunk_size: int = 900,
        fallback: HeadingChunker | None = None,
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self._llm_fn = llm_fn
        self._fallback = fallback or HeadingChunker(max_chunk_size=max_chunk_size)
        self.used_llm = False
        self.fallback_reason = "chua chay"

    def params(self) -> str:
        return (
            f"max_chunk_size={self.max_chunk_size}, "
            f"llm_fn={'co' if self._llm_fn else 'khong'}, fallback=heading"
        )

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        if self._llm_fn is None:
            self.fallback_reason = "khong co llm_fn -> dung HeadingChunker"
            return self._fallback.chunk(text)

        lines = text.splitlines()
        numbered = "\n".join(f"{index}: {line}" for index, line in enumerate(lines))

        try:
            raw = self._llm_fn(self.PROMPT.format(numbered=numbered))
            cuts = sorted({int(value) for value in re.findall(r"\d+", str(raw))})
            cuts = [cut for cut in cuts if 0 < cut < len(lines)]
            if not cuts:
                raise ValueError("LLM khong tra ve ranh gioi hop le")
        except Exception as error:  # noqa: BLE001 - fallback phai bao trum moi loi
            self.fallback_reason = f"LLM loi ({error}) -> dung HeadingChunker"
            return self._fallback.chunk(text)

        self.used_llm = True
        self.fallback_reason = "da dung LLM"

        chunks: list[str] = []
        boundaries = [0] + cuts + [len(lines)]
        for start, end in zip(boundaries, boundaries[1:]):
            piece = "\n".join(lines[start:end]).strip()
            if not piece:
                continue
            if len(piece) <= self.max_chunk_size:
                chunks.append(piece)
            else:
                chunks.extend(self._fallback.chunk(piece))
        return clean(chunks)
