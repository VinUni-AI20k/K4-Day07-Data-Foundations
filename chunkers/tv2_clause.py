"""
chunkers/tv2_clause.py — Chien luoc cua THANH VIEN 2: [DIEN TEN + MSSV].

Strategy: chia theo KHOAN / DIEM, gan lai ca tieu de Dieu lan cau dan cua khoan.
Trang thai: CHUA IMPLEMENT — day la phan viec cua ban.

===========================================================================
1. NGUYEN LY (viet lai bang loi cua ban vao REPORT_NHOM.md muc 2)
===========================================================================
`HeadingChunker` cua Ha cat o muc DIEU. Ban cat min hon mot bac: muc KHOAN
("1.", "2.") va DIEM ("a)", "b)"). Moi khoan la mot nghia vu doc lap, nen ve
ly thuyet retrieval se tro nen chinh xac hon.

Nhung cat min co mot cai gia: khoan bi tach khoi ngu canh. Vi du Dieu 18:

    Dieu 18. Ra soat va xac nhan noi dung hop dong          <- tieu de DIEU
    Website TMDT phai co co che cho phep khach hang...      <- CAU DAN
    1. Hien thi cho khach hang nhung thong tin sau:         <- cau dan cua KHOAN
       a) Ten hang hoa hoac dich vu, so luong va chung loai;
       b) Phuong thuc va thoi han giao hang...
       c) Tong gia tri cua hop dong va cac chi tiet...      <- DAP AN Q3 o day

Neu ban cat ra ma chi giu "a) Ten hang hoa..." thi chunk do vo nghia. Vi vay
ban phai PREPEND ca hai: tieu de Dieu VA cau dan cua khoan.

===========================================================================
2. GIA THUYET CAN KIEM CHUNG (day la thu duoc cham diem, khong phai diem so)
===========================================================================
Benchmark hien tai cho thay Q3 la cau kho nhat: `heading` chi duoc 1 diem
(chunk chua dap an dung top-2), `fixed`/`recursive`/`sentence` duoc 0 diem
(dung doc_id nhung sai section).

Gia thuyet cua ban: "Cat o muc khoan + prepend day du ngu canh se dua chunk
chua 'Tong gia tri cua hop dong' len top-1, tuc Q3 = 2 diem."

Neu dung -> ban la nguoi DUY NHAT sua duoc failure case cua nhom. Neu sai ->
giai thich TAI SAO sai, cung duoc diem tuong duong. Dung sua gia thuyet sau
khi da thay ket qua.

Nho kiem ca mat trai: cat min hon nghia la nhieu chunk hon, cac chunk trong
cung mot Dieu se rat giong nhau (vi deu mang cung tieu de) -> top-3 co the bi
chiem het boi mot Dieu duy nhat. Ghi lai neu thay hien tuong nay.

===========================================================================
3. THUAT TOAN GOI Y
===========================================================================
    1. Duyet tung dong cua `text`.
    2. Gap dong tieu de (`is_heading`) -> cap nhat `current_title`, xoa
       `current_lead` (cau dan), flush buffer.
    3. Gap dong bat dau khoan (`is_clause_start`) -> flush chunk truoc do,
       mo chunk moi.
       - Neu la khoan cap 1 ("1.", "2.") -> dong nay TRO THANH `current_lead`
         cho cac diem a)/b)/c) ben duoi no.
       - Neu la diem cap 2 ("a)", "b)") -> giu nguyen `current_lead`.
    4. Khi flush: chunk = current_title + current_lead (neu khac) + noi dung.
    5. Chunk nao van dai hon `max_chunk_size` -> ha xuong `RecursiveChunker`
       roi `attach()` lai tieu de.
    6. Goi `merge_short()` de gop manh vun, roi `clean()` truoc khi return.

Helper co san trong `chunkers/base.py`, ban khong phai viet lai:
    is_heading(line)      -> bool
    is_clause_start(line)  -> bool   # khop "1." va "a)"
    attach(title, pieces, every=True)
    merge_short(chunks, min_size)
    clean(chunks)

===========================================================================
4. CHECKLIST TRUOC KHI CHAY BENCHMARK
===========================================================================
    [ ] text rong -> tra [] (khong crash)
    [ ] khong co chunk rong / chi khoang trang
    [ ] khong co chunk < 120 ky tu kieu "chi mot dong tieu de"
        (loi nay tung lam RecursiveChunker an diem gia — doc base.py)
    [ ] moi chunk deu truy nguoc duoc ve dung Dieu nao
    [ ] KHONG sua bench.py / ingest.py / src/

Chay thu:
    python -c "from chunkers.tv2_clause import ClauseChunker; from pathlib import Path; from ingest import parse_front_matter; _,b=parse_front_matter(Path('data/k4_ecommerce/nd52-quy-trinh-dat-hang-truc-tuyen.md').read_text(encoding='utf-8')); [print(f'--- {i} ({len(c)} ky tu) ---'); print(c[:200]) for i,c in enumerate(ClauseChunker().chunk(b))]"

Chay benchmark:
    $env:EMBEDDING_PROVIDER="lexical"; python bench.py clause
    $env:EMBEDDING_PROVIDER="lexical"; python bench.py --all
"""
from __future__ import annotations

from src.chunking import RecursiveChunker  # noqa: F401 - dung o buoc 5

from .base import (  # noqa: F401 - import san de ban dung ngay
    BaseChunker,
    attach,
    clean,
    is_clause_start,
    is_heading,
    merge_short,
)


class ClauseChunker(BaseChunker):
    """Chia theo khoan/diem, prepend tieu de Dieu + cau dan cua khoan.

    Tham so:
        max_chunk_size:   nguong ky tu; vuot thi ha xuong RecursiveChunker.
        min_chunk_size:   gop cac manh ngan hon nguong nay.
        keep_clause_lead: co prepend cau dan cua khoan vao cac diem a)/b)/c)
                          khong. Dat False de lam ablation, chung minh tac dung.
    """

    name = "clause"

    def __init__(
        self,
        max_chunk_size: int = 700,
        min_chunk_size: int = 120,
        keep_clause_lead: bool = True,
    ) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.keep_clause_lead = keep_clause_lead

    def chunk(self, text: str) -> list[str]:
        # TODO(TV2): implement theo thuat toan o muc 3 cua docstring dau file.
        raise NotImplementedError(
            "ClauseChunker.chunk() chua duoc implement — xem huong dan trong "
            "chunkers/tv2_clause.py"
        )
