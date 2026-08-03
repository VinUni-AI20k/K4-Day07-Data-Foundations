#!/usr/bin/env python3
"""Fetch server-rendered public Shopee returns/refunds articles.

The category page is a JavaScript shell. This script therefore downloads the
public article URLs directly, checks robots.txt, waits between requests, and
stores raw HTML outside ``data/`` for reproducible preprocessing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ARTICLE_URLS = [
    "https://help.shopee.vn/portal/4/article/188931",
    "https://help.shopee.vn/portal/4/article/79233?seo=1",
    "https://help.shopee.vn/portal/4/article/79465",
    "https://help.shopee.vn/portal/4/article/79467",
    "https://help.shopee.vn/portal/4/article/79298?seo=1",
    "https://help.shopee.vn/portal/4/article/189473",
    "https://help.shopee.vn/portal/4/article/190242",
]
DEFAULT_OUTPUT_DIR = Path(".crawl_cache/shopee-returns")
USER_AGENT = "K4-Day07-Data-Foundations/1.0 (educational lab)"


def robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL phải là địa chỉ http(s) hợp lệ")
    parser = RobotFileParser(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
    try:
        parser.read()
    except (HTTPError, URLError, OSError) as exc:
        raise RuntimeError(f"Không thể xác minh robots.txt: {exc}") from exc
    return parser.can_fetch(USER_AGENT, url)


def fetch(url: str, timeout: float = 30.0) -> tuple[str, bytes, str]:
    if not robots_allowed(url):
        raise PermissionError("URL bị robots.txt từ chối; không tải trang này")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
    with urlopen(request, timeout=timeout) as response:  # noqa: S310
        content_type = response.headers.get_content_type().lower()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"Nguồn không phải HTML: {content_type}")
        charset = response.headers.get_content_charset() or "utf-8"
        return response.geturl(), response.read(), charset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", action="append", dest="urls", help="Article URL; repeat to override built-in list")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.delay < 1:
        parser.error("--delay phải >= 1 giây theo DATA_COLLECTION.md")

    urls = args.urls or ARTICLE_URLS
    args.output_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for index, url in enumerate(urls):
        if index:
            time.sleep(args.delay)
        output = args.output_dir / f"article-{index + 1:02d}.html"
        try:
            final_url, body, charset = fetch(url, args.timeout)
            output.write_bytes(body)
            metadata = {"source_url": final_url, "retrieved_at": date.today().isoformat(), "document_version": "not-stated", "charset": charset}
            output.with_suffix(".json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"[{index + 1}/{len(urls)}] Đã lưu {len(body):,} bytes: {output}")
        except (HTTPError, URLError, TimeoutError, ValueError, PermissionError, RuntimeError) as exc:
            failures += 1
            print(f"[{index + 1}/{len(urls)}] Bỏ qua {url}: {exc}", file=sys.stderr)
    print(f"Hoàn tất: {len(urls) - failures} thành công, {failures} thất bại")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
