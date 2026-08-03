import csv
import re
from pathlib import Path

D = Path("data/k4_ecommerce")
REQ = ["doc_id", "title", "source_url", "retrieved_at", "document_version"]
KEY = "customer_role"

mds = sorted(D.glob("*.md"))

with open(D / "sources.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

ids = []
roles = {}

for p in mds:
    content = p.read_text(encoding="utf-8")
    parts = content.split("---")

    fm = (
        dict(re.findall(r"^(\w+):\s*(.+)$", parts[1], re.MULTILINE))
        if len(parts) >= 3
        else {}
    )

    doc_id = fm.get("doc_id")
    role = fm.get(KEY)

    ids.append(doc_id)
    roles[role] = roles.get(role, 0) + 1

    ok = (
        all(k in fm for k in REQ)
        and KEY in fm
        and doc_id == p.stem
    )

    status = "OK" if ok else "THIEU METADATA"
    print(f"{p.name:40} {status}")

csv_ids = sorted(r["doc_id"] for r in rows)
md_ids = sorted(doc_id for doc_id in ids if doc_id is not None)

print("so file :", len(mds), "(can 5-10)")
print("csv     :", "khop" if csv_ids == md_ids else "LECH")
print(KEY, ":", roles)
