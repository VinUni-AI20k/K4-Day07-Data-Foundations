#!/usr/bin/env python3
"""Thu thap product listing cong khai tu HuggingFace dataset ASOS -> corpus K4.

Nguon: https://huggingface.co/datasets/UniqueData/asos-e-commerce-dataset
API cong khai (datasets-server), khong can dang nhap, khong can API key.
License cua dataset: CC-BY-NC-ND-4.0 -> chi dung cho muc dich hoc thuat phi thuong mai,
ghi nguon day du trong sources.csv.

LUU Y QUAN TRONG VE CHAT LUONG DU LIEU
--------------------------------------
Cot `url` trong dataset bi LECH so voi phan con lai cua ban ghi: nhieu dong lien
tiep dung chung name/sku/description nhung moi dong lai co mot `url` khac nhau,
va chi dong CUOI trong moi nhom co url trung khop voi ten san pham.

Neu lay bua mot dong, `source_url` se tro toi mot san pham KHAC voi noi dung ->
mat provenance, gold answer khong kiem chung duoc.

Script nay vi vay chi giu lai cac dong "tu nhat quan": slug trong URL phai khop
voi slug sinh tu `name`. Cac dong lech bi bo qua va duoc bao cao o cuoi.

Cach chay (tu thu muc goc repo):

    python scripts/fetch_hf_asos_products.py --limit 10 --output-dir data/k4_asos_products
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

DATASET = "UniqueData/asos-e-commerce-dataset"
ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET_PAGE = f"https://huggingface.co/datasets/{DATASET}"
DATASET_LICENSE = "cc-by-nc-nd-4.0"
TOTAL_ROWS = 30845  # theo /info cua datasets-server (split train)
PAGE_SIZE = 100
REQUEST_DELAY_SECONDS = 1.0  # lich su voi API cong khai
USER_AGENT = "Lab7-RAG-coursework/1.0 (academic use; contact via course instructor)"

# Cac muc trong `description` duoc giu lai, theo dung thu tu hien thi tren trang ASOS.
# 'Product Details' duoc tach rieng thanh bang + bullet, phan con lai giu nguyen van.
DESCRIPTION_SECTIONS = ["Size & Fit", "Look After Me", "About Me", "Brand"]


def slugify(text: str) -> str:
    """Chuan hoa chuoi ve dang slug de so sanh url voi ten san pham."""
    text = text.lower().replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def url_slug(url: str) -> str | None:
    """Lay phan slug san pham tu URL ASOS: /<brand>/<slug>/prd/<id>."""
    match = re.search(r"asos\.com/[^/]+/([^/]+)/prd/\d+", url or "")
    return match.group(1) if match else None


def url_brand(url: str) -> str | None:
    """Lay slug thuong hieu (path segment dau tien) tu URL ASOS."""
    match = re.search(r"asos\.com/([^/]+)/[^/]+/prd/\d+", url or "")
    return match.group(1) if match else None


def shorten_doc_id(slug: str, limit: int = 80) -> str:
    """Rut gon doc_id nhung cat theo RANH GIOI TU, tranh duoi cut kieu '...in-pale-b'."""
    if len(slug) <= limit:
        return slug
    parts, out = slug.split("-"), []
    for part in parts:
        if len("-".join(out + [part])) > limit:
            break
        out.append(part)
    return "-".join(out) if out else slug[:limit].rstrip("-")


def product_id(url: str) -> str | None:
    match = re.search(r"/prd/(\d+)", url or "")
    return match.group(1) if match else None


def fetch_rows(offset: int, length: int, attempts: int = 4) -> list[dict]:
    """Goi datasets-server API cong khai, tra ve list ban ghi tho.

    API doi khi tra 502/503 tam thoi -> thu lai voi backoff thay vi bo ca lan chay.
    """
    query = urllib.parse.urlencode(
        {"dataset": DATASET, "config": "default", "split": "train",
         "offset": offset, "length": length}
    )
    request = urllib.request.Request(f"{ROWS_API}?{query}", headers={"User-Agent": USER_AGENT})

    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return [item["row"] for item in payload.get("rows", [])]
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt < attempts - 1:
                delay = REQUEST_DELAY_SECONDS * (2 ** attempt)
                print(f"  [thu lai] offset={offset} loi {error}; cho {delay:.0f}s", file=sys.stderr)
                time.sleep(delay)
    raise RuntimeError(f"that bai sau {attempts} lan thu: {last_error}")


def parse_description(raw: str) -> dict[str, str]:
    """`description` duoc luu duoi dang repr cua list[dict]; parse ve dict phang."""
    try:
        blocks = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        return {}
    sections: dict[str, str] = {}
    for block in blocks if isinstance(blocks, list) else []:
        if isinstance(block, dict):
            for key, value in block.items():
                if isinstance(value, str) and value.strip():
                    sections[key.strip()] = value.strip()
    return sections


def split_product_details(text: str, brand_slug: str, name: str = "") -> tuple[str, str, list[str]]:
    """Tach 'Coats & Jackets by Carhartt WIPSpread collar...Product Code: 123'.

    Tra ve (category, brand, list cac bullet dac diem).

    Ten thuong hieu trong nguon KHONG co dau phan cach voi bullet dau tien
    ('Carhartt WIP' + 'Spread collar' -> 'Carhartt WIPSpread collar'), nen khong the
    cat bang quy tac thuong->HOA (se ra 'WIPJacket upgrade'). Thay vao do dung
    `brand_slug` lay tu URL lam moc: an dan tung tu sau ' by ' cho toi khi slug cua
    phan da an khop voi brand_slug -> biet chinh xac ten thuong hieu ket thuc o dau.
    """
    category, brand = "", ""
    body = text

    head = re.match(r"^(.+?)\s+by\s+(.*)$", text, re.S)
    if head:
        category = head.group(1).strip()
        remainder = head.group(2)

        # An dan TUNG KY TU cho den khi slug cua phan da an khop brand_slug.
        # Phai lam o muc ky tu chu khong phai muc tu: nguon viet lien
        # 'adidas OriginalsThe in-between one', tu thu hai la 'OriginalsThe'
        # nen cat theo tu se vuot qua ten thuong hieu.
        matched_end = None
        for end in range(1, min(len(remainder), 60) + 1):
            if slugify(remainder[:end]) == brand_slug:
                matched_end = end  # giu ket qua dai nhat con khop

        # Tang 2: brand trong 'Product Details' co the khac brand slug tren URL
        # ('Maternity dress by ASOS DESIGN...' nhung URL la /asos-maternity/).
        # Khi do neo vao TEN san pham: ten cung mo dau bang ten thuong hieu,
        # nen lay prefix dai nhat cua remainder ma slug con la prefix cua slug(name).
        if matched_end is None and name:
            name_slug = slugify(name)
            for end in range(1, min(len(remainder), 60) + 1):
                candidate = slugify(remainder[:end])
                if candidate and name_slug.startswith(candidate):
                    matched_end = end

        if matched_end is not None:
            brand = remainder[:matched_end].strip()
            body = remainder[matched_end:]
        else:
            # Tang 3: ranh gioi thuong/so -> HOA. Bat buoc co [a-z0-9] ngay truoc chu HOA,
            # neu khong '.+?' se dung lai sau 1 ky tu ('ASOS' -> brand 'A', body 'SOS...').
            fallback = re.match(r"^(.+?[a-z0-9])(?=[A-Z])", remainder)
            brand = (fallback.group(1).strip() if fallback else remainder.strip())
            body = remainder[len(brand):]

    body = re.sub(r"Product Code:\s*\d+\s*$", "", body).strip()
    # Chen ranh gioi giua "...collar" va "Zip..." (thuong/so -> chu HOA)
    bullets = [b.strip() for b in re.sub(r"(?<=[a-z0-9)\"'%])(?=[A-Z])", "\n", body).split("\n")]
    return category, brand, [b for b in bullets if b]


def parse_price(raw: str) -> tuple[str, str]:
    """Tra ve (gia_so, ghi_chu). Nguon co tien to 'From '/'Now ' cho gia khong co dinh."""
    text = (raw or "").strip()
    note = "standard"
    lowered = text.lower()
    if lowered.startswith("from"):
        note, text = "from", text[4:]
    elif lowered.startswith("now"):
        note, text = "now-reduced", text[3:]
    match = re.search(r"\d+(?:\.\d+)?", text)
    return (match.group(0) if match else ""), note


# Nguon ghi danh muc khong nhat quan ('Coat', 'Coats', 'Jacket', 'Jackets',
# 'Coats & Jackets', 'Petite coat'...). De `search_with_filter()` dung duoc,
# gom them mot khoa chuan hoa `category_group`. Day chi la ANH XA co hoc tren
# chuoi da co trong nguon, khong bo sung thong tin moi.
CATEGORY_GROUPS = [
    ("outerwear", ("coat", "jacket", "gilet", "shacket", "parka", "blazer", "puffer")),
    ("tops", ("shirt", "top", "blouse", "t-shirt", "jumper", "hoodie", "sweatshirt", "knit")),
    ("dresses", ("dress", "playsuit", "jumpsuit")),
    ("bottoms", ("jean", "trouser", "short", "skirt", "legging", "jogger")),
    ("footwear", ("shoe", "boot", "trainer", "sandal", "heel")),
    ("accessories", ("bag", "hat", "scarf", "belt", "jewellery", "sunglass")),
]

# Dong san pham theo dang nguoi cua ASOS. Khoa la TOKEN trong slug (so khop tron tu)
# chu khong phai substring: 'tall' dang substring se dinh vao 'metallic', con 'plus'
# trong 'Plus three stripe bralet' lai la dong Plus-size that.
FIT_LINE_TOKENS = {
    "petite": "petite",
    "tall": "tall",
    "curve": "curve",
    "plus": "plus-size",
    "maternity": "maternity",
}


def classify_category(category_slug: str) -> str:
    for group, keywords in CATEGORY_GROUPS:
        if any(keyword in category_slug for keyword in keywords):
            return group
    return "other"


def detect_fit_line(*texts: str) -> str:
    tokens = set(slugify(" ".join(texts)).split("-"))
    for token, line in FIT_LINE_TOKENS.items():
        if token in tokens:
            return line
    return "standard"


def parse_sizes(raw: str) -> tuple[list[str], list[str]]:
    """Tra ve (sizes_con_hang, sizes_het_hang)."""
    in_stock, out_of_stock = [], []
    for chunk in (raw or "").split(","):
        label = chunk.strip()
        if not label:
            continue
        if label.lower().endswith("- out of stock"):
            out_of_stock.append(re.sub(r"\s*-\s*out of stock$", "", label, flags=re.I).strip())
        else:
            in_stock.append(label)
    return in_stock, out_of_stock


def build_record(row: dict) -> dict | None:
    """Chuyen mot dong tu nhat quan thanh record da lam sach; None neu khong dung."""
    url, name = (row.get("url") or "").strip(), (row.get("name") or "").strip()
    if not url or not name:
        return None

    # Chot provenance: url phai thuc su la trang cua san pham nay.
    slug_from_url, slug_from_name = url_slug(url), slugify(name)
    if not slug_from_url or slug_from_url != slug_from_name:
        return None

    sections = parse_description(row.get("description") or "")
    details = sections.get("Product Details", "")
    if not details:
        return None

    brand_slug = url_brand(url) or ""
    category, brand, bullets = split_product_details(details, brand_slug, name)
    in_stock, out_of_stock = parse_sizes(row.get("size") or "")
    price, price_note = parse_price(row.get("price") or "")
    sku = row.get("sku")

    return {
        "doc_id": shorten_doc_id(f"asos-{slug_from_url}"),
        "title": name,
        "source_url": url,
        "product_id": product_id(url) or "",
        "sku": str(int(sku)) if isinstance(sku, float) and sku == sku else "",
        "brand": brand,
        "brand_slug": brand_slug or "not-stated",
        "category": category,
        "category_slug": slugify(category) or "uncategorised",
        "category_group": classify_category(slugify(category)),
        "fit_line": detect_fit_line(name, category),
        "price": price,
        "price_note": price_note,
        "color": (row.get("color") or "").strip(),
        "sizes_in_stock": in_stock,
        "sizes_out_of_stock": out_of_stock,
        "bullets": bullets,
        "sections": sections,
    }


def render_markdown(record: dict, retrieved_at: str) -> str:
    """Sinh file .md dung format o docs/DATA_COLLECTION.md muc 4."""
    front_matter = [
        "---",
        f"doc_id: {record['doc_id']}",
        f"title: \"{record['title']}\"",
        f"source_url: {record['source_url']}",
        f"retrieved_at: {retrieved_at}",
        "document_version: not-stated",
        "customer_role: buyer",
        f"category: {record['category_slug']}",
        f"category_group: {record['category_group']}",
        f"fit_line: {record['fit_line']}",
        f"brand: {record['brand_slug']}",
        f"price_gbp: {record['price'] or 'not-stated'}",
        f"price_basis: {record['price_note']}",
        f"color: {slugify(record['color']) or 'not-stated'}",
        "language: en",
        "region: uk",
        "doc_type: product-listing",
        f"dataset_source: {DATASET}",
        "---",
        "",
        f"# {record['title']}",
        "",
    ]

    lines = front_matter
    lines += [
        "## Thong tin san pham (Product details)",
        "",
        f"- Thuong hieu: {record['brand'] or 'not-stated'}",
        f"- Danh muc: {record['category'] or 'not-stated'}",
        (f"- Gia niem yet: GBP {record['price']}"
         + {"from": " (gia tu)", "now-reduced": " (gia da giam)"}.get(record["price_note"], "")
         if record["price"] else "- Gia niem yet: not-stated"),
        f"- Mau: {record['color'] or 'not-stated'}",
        f"- Ma san pham (product code): {record['sku'] or 'not-stated'}",
        "",
    ]

    if record["bullets"]:
        lines += ["### Dac diem", ""] + [f"- {b}" for b in record["bullets"]] + [""]

    if record["sizes_in_stock"] or record["sizes_out_of_stock"]:
        lines += ["### Kich co (size)", ""]
        if record["sizes_in_stock"]:
            lines.append(f"- Con hang: {', '.join(record['sizes_in_stock'])}")
        if record["sizes_out_of_stock"]:
            lines.append(f"- Het hang: {', '.join(record['sizes_out_of_stock'])}")
        lines.append("")

    for key in DESCRIPTION_SECTIONS:
        value = record["sections"].get(key)
        if not value:
            continue
        lines += [f"### {key}", "", value, ""]

    lines += [
        "---",
        "",
        f"Nguon: [{record['source_url']}]({record['source_url']})",
        f"Thu thap qua dataset cong khai `{DATASET}` ({DATASET_PAGE}), license {DATASET_LICENSE}.",
        "",
    ]
    return "\n".join(lines)


def read_existing(out_dir: Path) -> tuple[list[dict], set[str], set[str]]:
    """Doc sources.csv da co -> (rows, tap doc_id, tap source_url)."""
    path = out_dir / "sources.csv"
    if not path.exists():
        return [], set(), set()
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows, {r["doc_id"] for r in rows}, {r["source_url"] for r in rows}


def read_existing_facets(out_dir: Path) -> tuple[set[str], set[str]]:
    """Lay tap category_slug / brand da dung trong corpus hien tai (tu front matter)."""
    categories, brands = set(), set()
    for path in out_dir.glob("*.md"):
        head = path.read_text(encoding="utf-8").split("---")
        if len(head) < 2:
            continue
        fields = dict(re.findall(r"^(\w+):\s*(.+)$", head[1], re.M))
        if fields.get("category"):
            categories.add(fields["category"].strip())
        if fields.get("brand"):
            brands.add(fields["brand"].strip())
    return categories, brands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=10, help="so san pham can lay (mac dinh 10)")
    parser.add_argument("--output-dir", default="data/k4_asos_products", help="thu muc dich")
    parser.add_argument("--scan", type=int, default=600, help="so dong toi da quet qua API")
    parser.add_argument("--retrieved-at", default=date.today().isoformat())
    parser.add_argument(
        "--append",
        action="store_true",
        help="bo sung them san pham vao corpus da co (khong ghi de, khong lay trung)",
    )
    parser.add_argument(
        "--offset-start", type=int, default=0,
        help="dich diem bat dau quet, dung khi --append de cham vao vung dataset khac",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Dataset duoc sap xep theo danh muc, neu doc tuan tu tu offset 0 thi ca 10 san pham
    # deu roi vao "Coats & Jackets" -> metadata filter theo category vo nghia.
    # Vi vay quet rai deu tren toan bo dataset.
    windows = max(1, args.scan // PAGE_SIZE)
    stride = max(PAGE_SIZE, TOTAL_ROWS // windows)
    offsets = [
        min(args.offset_start + index * stride, TOTAL_ROWS - PAGE_SIZE)
        for index in range(windows)
    ]

    # Che do bo sung: doc corpus da co de KHONG lay lai san pham cu va de uu tien
    # brand/category chua xuat hien.
    if args.append:
        existing_rows, existing_ids, existing_urls = read_existing(out_dir)
        seeded_categories, seeded_brands = read_existing_facets(out_dir)
        print(f"che do --append: da co {len(existing_ids)} tai lieu, se bo sung {args.limit}.")
    else:
        existing_rows, existing_ids, existing_urls = [], set(), set()
        seeded_categories, seeded_brands = set(), set()

    candidates: list[dict] = []
    seen_sku: set[str] = set()
    scanned = misaligned = 0

    for position, offset in enumerate(offsets):
        try:
            rows = fetch_rows(offset, PAGE_SIZE)
        except Exception as error:  # noqa: BLE001
            print(f"[loi] khong goi duoc API tai offset={offset}: {error}", file=sys.stderr)
            return 1
        if not rows:
            break

        for row in rows:
            scanned += 1
            record = build_record(row)
            if record is None:
                misaligned += 1
                continue
            if record["sku"] and record["sku"] in seen_sku:
                continue
            # Che do --append: loai san pham da nam trong corpus.
            if record["doc_id"] in existing_ids or record["source_url"] in existing_urls:
                continue
            seen_sku.add(record["sku"])
            candidates.append(record)

        if position < len(offsets) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    if not candidates:
        print("[loi] khong tim duoc dong nao tu nhat quan", file=sys.stderr)
        return 1

    # Chon vong tron theo category_group TRUOC (outerwear/tops/dresses/...).
    # Dataset duoc sap theo danh muc, neu vong tron theo `category_slug` thi cac khoa
    # xuat hien som (toan ao khoac) chiem het 10 suat -> filter theo category vo nghia.
    by_group: dict[str, list[dict]] = {}
    for record in candidates:
        by_group.setdefault(record["category_group"], []).append(record)
    for bucket in by_group.values():
        bucket.sort(key=lambda item: (item["category_slug"], item["brand_slug"]))

    selected: list[dict] = []
    # Nap san cac facet da dung -> vong 1 se uu tien category/brand MOI so voi corpus cu.
    seen_category: set[str] = set(seeded_categories)
    seen_brand: set[str] = set(seeded_brands)
    # Vong 1 uu tien ban ghi co category_slug + brand chua xuat hien; vong 2 lay phan con lai.
    for require_new in (True, False):
        while len(selected) < args.limit:
            progressed = False
            for bucket in by_group.values():
                if len(selected) >= args.limit:
                    break
                for index, record in enumerate(bucket):
                    if require_new and (
                        record["category_slug"] in seen_category
                        or record["brand_slug"] in seen_brand
                    ):
                        continue
                    seen_category.add(record["category_slug"])
                    seen_brand.add(record["brand_slug"])
                    selected.append(bucket.pop(index))
                    progressed = True
                    break
            if not progressed:
                break
    selected.sort(key=lambda item: (item["category_group"], item["category_slug"], item["brand_slug"]))

    # doc_id phai duy nhat (checklist muc 6): sau khi rut gon, hai san pham co the
    # trung slug -> gan them product_id tu URL de tach.
    used_ids: set[str] = set(existing_ids)
    for record in selected:
        if record["doc_id"] in used_ids and record["product_id"]:
            record["doc_id"] = f"{record['doc_id']}-{record['product_id']}"
        used_ids.add(record["doc_id"])

    for record in selected:
        path = out_dir / f"{record['doc_id']}.md"
        path.write_text(render_markdown(record, args.retrieved_at), encoding="utf-8")
        print(f"da ghi {path}")

    header = ["doc_id", "file_path", "title", "source_url", "retrieved_at",
              "document_version", "license_or_permission"]
    sources_path = out_dir / "sources.csv"
    with sources_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        # Giu nguyen cac dong cu (che do --append) roi moi noi them dong moi.
        for row in existing_rows:
            writer.writerow([row.get(column, "") for column in header])
        for record in selected:
            writer.writerow([
                record["doc_id"],
                f"{out_dir.as_posix()}/{record['doc_id']}.md",
                record["title"],
                record["source_url"],
                args.retrieved_at,
                "not-stated",
                f"{DATASET_LICENSE} via {DATASET_PAGE}",
            ])
    print(f"da ghi {sources_path} ({len(existing_rows) + len(selected)} dong)")

    distribution: dict[str, int] = {}
    for record in candidates:
        distribution[record["category_group"]] = distribution.get(record["category_group"], 0) + 1

    print(
        f"\ntong ket: quet {scanned} dong, bo {misaligned} dong lech url/name, "
        f"con {len(candidates)} ung vien tu nhat quan, chon {len(selected)} san pham."
    )
    print(f"phan bo category_group trong ung vien: {distribution}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
