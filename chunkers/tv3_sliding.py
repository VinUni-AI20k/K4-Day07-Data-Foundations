"""
chunkers/tv3_sliding.py — Chien luoc cua THANH VIEN 3: [DIEN TEN + MSSV].

Strategy: cua so truot (sliding window) overlap lon, snap ve ranh gioi cau.
Trang thai: CHUA IMPLEMENT — day la phan viec cua ban.

===========================================================================
1. NGUYEN LY
===========================================================================
Ba nguoi kia deu di theo huong "ton trong cau truc tai lieu". Ban di huong
NGUOC LAI mot cach co chu dich: khong quan tam cau truc, chi truot mot cua so
co dinh voi do chong chéo LON (vi du 500 ky tu, overlap 200 = 40%).

Vi sao huong nguoc lai dang thu: `HeadingChunker` khong co overlap, nen moi
thong tin chi co MOT co hoi lot top-k. Do la nguyen nhan truc tiep khien Q3
that bai. Cua so truot lam nguoc lai — moi cau xuat hien trong 2-3 chunk khac
nhau, tang co hoi duoc tim thay.

Cai tien so voi `FixedSizeChunker` co san (dung cat giua tu!): sau khi tinh
duoc vi tri cat tho, SNAP no ve ranh gioi cau gan nhat (dau ".", "!", "?",
hoac xuong dong). Nho vay chunk khong bat dau bang manh cau cut kieu
", chinh xac, de tim va de hieu; b) Duoc sap xep..." — chinh la thu ma
`FixedSizeChunker` dang sinh ra trong benchmark hien tai cua nhom.

===========================================================================
2. GIA THUYET CAN KIEM CHUNG
===========================================================================
Gia thuyet cua ban co HAI ve, ca hai deu phai kiem:

  (a) Overlap lon lam TANG recall: chunk chua dap an cua Q3 se lot top-3
      o moi cau hoi, ke ca khi tu khoa bi phan tan.
  (b) Overlap lon lam GIAM precision: top-3 se bi chiem boi 2-3 chunk gan
      TRUNG NHAU cua cung mot doan, thay vi 3 goc nhin khac nhau. Agent nhan
      duoc context lap lai, khong them thong tin.

Neu ca (a) va (b) deu dung -> ban chung minh duoc DANH DOI precision/recall
bang so lieu that. Do chinh xac la thu `docs/EVALUATION.md` muc 2 hoi.

Cach do (b) cho ro: voi moi query, dem xem top-3 co bao nhieu chunk den tu
CUNG mot doc_id, va bao nhieu ky tu bi trung lap giua chung.

Nen chay it nhat 3 cau hinh de thay xu huong, vi du:
    overlap = 0   / 100 / 200  (giu chunk_size = 500)
roi bao cao ca ba trong REPORT_NHOM.md. Chon MOT cau hinh lam ket qua chinh.

===========================================================================
3. THUAT TOAN GOI Y
===========================================================================
    1. text rong -> tra [].
    2. step = chunk_size - overlap. Bat buoc kiem step > 0, khong thi raise
       ValueError ngay trong __init__ (tranh vong lap vo han).
    3. start = 0. Lap:
         end_raw = start + chunk_size
         end = snap ve ranh gioi cau gan end_raw nhat
              (tim dau ".", "!", "?", "\n" trong khoang [end_raw - 80, end_raw + 80];
               khong tim thay thi giu nguyen end_raw)
         chunk = text[start:end]
         start = end - overlap        # LUU Y: tinh tu `end` da snap, khong
                                      # phai tu `start + step`, neu khong
                                      # overlap se bi troi dan
         dung khi end >= len(text)
    4. merge_short() + clean() truoc khi return.

Bay de dinh nhat: neu snap lam `end` khong tang so voi vong truoc thi vong lap
chay mai. Luon dam bao `end > start` moi vong.

Helper trong `chunkers/base.py`: merge_short(chunks, min_size), clean(chunks).

===========================================================================
4. CHECKLIST TRUOC KHI CHAY BENCHMARK
===========================================================================
    [ ] text rong -> tra []
    [ ] text ngan hon chunk_size -> tra dung 1 chunk
    [ ] vong lap luon dung (test voi overlap = chunk_size - 1)
    [ ] hai chunk lien tiep THUC SU chia se noi dung (in ra kiem bang mat)
    [ ] khong chunk nao bat dau bang manh cau cut
    [ ] KHONG sua bench.py / ingest.py / src/

Chay benchmark:
    $env:EMBEDDING_PROVIDER="lexical"; python bench.py sliding
    $env:EMBEDDING_PROVIDER="lexical"; python bench.py --all
"""
from __future__ import annotations

from .base import BaseChunker, clean, merge_short  # noqa: F401

# Cac ky tu duoc coi la ket thuc mot cau/dong.
SENTENCE_ENDINGS = ".!?\n"


class SlidingWindowChunker(BaseChunker):
    """Cua so truot co overlap lon, ranh gioi snap ve cuoi cau.

    Tham so:
        chunk_size: do dai cua so (ky tu).
        overlap:    so ky tu chong chéo giua hai chunk lien tiep.
        snap_window: ban kinh tim ranh gioi cau quanh diem cat tho.
                     Dat 0 de tat snap (lam ablation, se giong FixedSizeChunker).
    """

    name = "sliding"

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 200,
        snap_window: int = 80,
        min_chunk_size: int = 120,
    ) -> None:
        if overlap >= chunk_size:
            raise ValueError("overlap phai nho hon chunk_size, khong thi lap vo han")
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.snap_window = snap_window
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO(TV3): implement theo thuat toan o muc 3 cua docstring dau file.
        raise NotImplementedError(
            "SlidingWindowChunker.chunk() chua duoc implement — xem huong dan "
            "trong chunkers/tv3_sliding.py"
        )

    def _snap_to_sentence(self, text: str, position: int) -> int:
        """Dich `position` ve ranh gioi cau gan nhat trong ban kinh snap_window.

        TODO(TV3): implement. Tra ve `position` neu khong tim thay ranh gioi
        nao, hoac neu snap_window == 0.
        """
        raise NotImplementedError
