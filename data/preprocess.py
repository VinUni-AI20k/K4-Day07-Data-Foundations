#!/usr/bin/env python3
"""Clean crawled HTML and create a K4-compatible Markdown document."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


BLOCK_TAGS = {"p", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "article", "section"}
SKIP_TAGS = {"script", "style", "nav", "footer", "header", "noscript", "svg", "iframe", "form"}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title: list[str] = []
        self.skip_depth = 0
        self.in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_title:
            self.title.append(data)
        self.parts.append(data)


def clean_text(raw: str) -> str:
    lines = []
    for line in raw.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line and (not lines or line != lines[-1]):
            lines.append(line)
    return "\n\n".join(lines).strip()


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(".crawl_cache/shopee-returns"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/k4_ecommerce"))
    args = parser.parse_args()

    inputs = [args.input] if args.input.is_file() else sorted(args.input.glob("article-*.html"))
    if not inputs:
        parser.error(f"Không tìm thấy HTML: {args.input}. Hãy chạy data/crawl_data.py trước.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest = args.output_dir / "sources.csv"
    rows = []
    if manifest.exists():
        with manifest.open(encoding="utf-8", newline="") as handle:
            rows = [
                row for row in csv.DictReader(handle)
                if not row.get("doc_id", "").startswith("shopee-returns-")
            ]
    fields = ["doc_id", "file_path", "title", "source_url", "retrieved_at", "document_version", "license_or_permission"]
    for input_path in inputs:
        parser_html = VisibleTextParser()
        parser_html.feed(input_path.read_text(encoding="utf-8", errors="replace"))
        parser_html.close()
        content = clean_text("".join(parser_html.parts))
        if len(content) < 200:
            print(f"Bỏ qua {input_path}: nội dung quá ngắn, có thể là trang JavaScript shell")
            continue

        metadata_file = input_path.with_suffix(".json")
        source = json.loads(metadata_file.read_text(encoding="utf-8")) if metadata_file.exists() else {}
        title = " ".join("".join(parser_html.title).split()) or f"Shopee returns/refunds article {input_path.stem}"
        doc_id = f"shopee-returns-{input_path.stem.replace('article-', '')}"
        metadata = {
            "doc_id": doc_id,
            "title": title,
            "source_url": source.get("source_url", ""),
            "retrieved_at": source.get("retrieved_at", date.today().isoformat()),
            "document_version": source.get("document_version", "not-stated"),
            "customer_role": "buyer",
            "category": "returns-refunds",
            "language": "vi",
        }
        output = args.output_dir / f"{doc_id}.md"
        front_matter = "\n".join(f"{key}: {yaml_quote(value)}" for key, value in metadata.items())
        output.write_text(f"---\n{front_matter}\n---\n\n# {metadata['title']}\n\n{content}\n", encoding="utf-8")
        rows.append({**metadata, "file_path": str(output), "license_or_permission": "public-page"})
        print(f"Đã tạo {output} ({len(content):,} ký tự)")
    with manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    print(f"Đã cập nhật {manifest}")


if __name__ == "__main__":
    main()
