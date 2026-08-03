"""
Kiểm tra corpus của NHÓM theo checklist docs/DATA_COLLECTION.md mục 6 + yêu cầu riêng K4.

Công cụ dùng chung cho cả nhóm — chạy trước khi chạy benchmark để chắc chắn không mất
điểm oan ở mục "Chất lượng Bộ Tài liệu" (10 điểm).

Chạy:
    python scripts/kiem_tra_corpus.py                      # mặc định data/k4_ecommerce
    python scripts/kiem_tra_corpus.py <thu-muc-khac>

Mã thoát: 0 nếu không còn lỗi chặn, 1 nếu còn.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ingest import parse_front_matter  # noqa: E402

BAT_BUOC = ["doc_id", "title", "source_url", "retrieved_at", "document_version", "customer_role"]
VAI_TRO_HOP_LE = {"buyer", "seller", "both"}
NGAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_GIA = re.compile(r"example\.(com|org|edu)", re.I)
DAU_HIEU_TEMPLATE = ["template mẫu", "Nhóm phải bổ sung", "Nhóm cần bổ sung", "dữ liệu khởi động"]

loi: list[str] = []
canh_bao: list[str] = []


def kiem_tra(dieu_kien: bool, thong_diep: str, chan: bool = True) -> None:
    if not dieu_kien:
        (loi if chan else canh_bao).append(thong_diep)


def main() -> int:
    thu_muc = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "data" / "k4_ecommerce"
    if not thu_muc.is_absolute():
        thu_muc = REPO_ROOT / thu_muc
    print(f"Corpus: {thu_muc}\n")

    if not thu_muc.exists():
        print(f"LỖI: không tìm thấy thư mục {thu_muc}")
        return 1

    files = sorted(list(thu_muc.glob("*.md")) + list(thu_muc.glob("*.txt")))
    print(f"{'File':<42}{'customer_role':<16}{'category':<18}{'ký tự':<8}Thiếu metadata")
    print("-" * 104)

    doc_ids: dict[str, str] = {}
    vai_tro: dict[str, int] = {}

    for path in files:
        meta, body = parse_front_matter(io.open(path, encoding="utf-8").read())
        thieu = [khoa for khoa in BAT_BUOC if not str(meta.get(khoa, "")).strip()]
        role = str(meta.get("customer_role", "—"))
        vai_tro[role] = vai_tro.get(role, 0) + 1
        print(f"{path.name:<42}{role:<16}{str(meta.get('category', '—')):<18}{len(body):<8}{','.join(thieu) or 'đủ'}")

        ten = path.name
        kiem_tra(not thieu, f"{ten}: thiếu metadata bắt buộc {thieu}")

        doc_id = str(meta.get("doc_id", "")).strip()
        if doc_id:
            kiem_tra(doc_id not in doc_ids, f"{ten}: doc_id '{doc_id}' trùng với {doc_ids.get(doc_id)}")
            doc_ids[doc_id] = ten
            # CHECKPOINT 2 của đề bài coi doc_id != tên file là THIẾU METADATA -> để mức chặn.
            kiem_tra(doc_id == path.stem, f"{ten}: doc_id '{doc_id}' phải trùng tên file '{path.stem}' (CHECKPOINT 2)")

        kiem_tra(role in VAI_TRO_HOP_LE, f"{ten}: customer_role='{role}' không thuộc {sorted(VAI_TRO_HOP_LE)}")
        kiem_tra(NGAY.match(str(meta.get("retrieved_at", ""))) is not None,
                 f"{ten}: retrieved_at phải dạng YYYY-MM-DD, đang là '{meta.get('retrieved_at')}'")
        kiem_tra(not URL_GIA.search(str(meta.get("source_url", ""))),
                 f"{ten}: source_url còn là URL mẫu example.com — phải thay bằng nguồn thật")
        kiem_tra(len([k for k in meta if k not in BAT_BUOC and k not in {"source", "chunk_index"}]) >= 1,
                 f"{ten}: cần ít nhất 1 trường metadata hữu ích ngoài nhóm bắt buộc (category/language/...)", chan=False)
        kiem_tra(len(body.strip()) >= 200, f"{ten}: nội dung quá ngắn ({len(body)} ký tự), khó tạo gold answer", chan=False)

        dau_hieu = [d for d in DAU_HIEU_TEMPLATE if d in body]
        kiem_tra(not dau_hieu, f"{ten}: nội dung còn chữ template {dau_hieu} — chưa thay bằng nguồn thật")

    print(f"\nPhân bố customer_role: {vai_tro}")

    # --- Kiểm tra cấp corpus ---
    kiem_tra(5 <= len(files) <= 10, f"Cần 5-10 tài liệu, đang có {len(files)}")
    kiem_tra(vai_tro.get("seller", 0) + vai_tro.get("both", 0) >= 1,
             "K4: phải có ít nhất 1 tài liệu customer_role=seller (hoặc both) cho câu hỏi lọc metadata")
    kiem_tra(vai_tro.get("buyer", 0) + vai_tro.get("both", 0) >= 1,
             "K4: phải có ít nhất 1 tài liệu customer_role=buyer (hoặc both)")
    # CHECKPOINT 2: nếu mọi file cùng một customer_role thì filter không loại được gì,
    # và mục 7 sẽ không chứng minh được giá trị của metadata.
    kiem_tra(len([v for v in vai_tro if v in VAI_TRO_HOP_LE]) >= 2,
             f"customer_role phải có ít nhất 2 giá trị khác nhau, đang chỉ có {sorted(vai_tro)}")

    csv_path = thu_muc / "sources.csv"
    if not csv_path.exists():
        loi.append("Thiếu sources.csv")
    else:
        with io.open(csv_path, encoding="utf-8", newline="") as fh:
            dong = list(csv.DictReader(fh))
        id_csv = {str(r.get("doc_id", "")).strip() for r in dong}
        thieu_csv = set(doc_ids) - id_csv
        thua_csv = id_csv - set(doc_ids)
        kiem_tra(not thieu_csv, f"sources.csv thiếu dòng cho doc_id: {sorted(thieu_csv)}")
        kiem_tra(not thua_csv, f"sources.csv có doc_id không tồn tại file: {sorted(thua_csv)}")
        kiem_tra(all(str(r.get("license_or_permission", "")).strip() for r in dong),
                 "sources.csv: có dòng thiếu license_or_permission", chan=False)

    print()
    for c in canh_bao:
        print(f"  [cảnh báo] {c}")
    for e in loi:
        print(f"  [LỖI]      {e}")

    if loi:
        print(f"\n❌ CÒN {len(loi)} LỖI CHẶN — sửa xong mới nên chạy benchmark.")
        return 1
    print(f"\n✅ CORPUS ĐẠT CHECKLIST ({len(canh_bao)} cảnh báo không chặn).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
