#!/usr/bin/env python3
"""Scrape factors and explanations from https://factors.directory/zh."""

from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://factors.directory/zh"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
}


@dataclass
class Factor:
    name: str
    description: str
    url: str


def fetch(session: requests.Session, url: str, *, retries: int = 3) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def is_factor_detail(path: str) -> bool:
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return False
    for marker in ("factor", "factors"):
        if marker in segments:
            index = segments.index(marker)
            return index < len(segments) - 1
    return False


def discover_factor_links(html: str, base_url: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    base_host = urlparse(base_url).netloc
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#"):
            continue
        absolute = urljoin(base_url, href)
        parsed = urlparse(absolute)
        if parsed.netloc != base_host:
            continue
        if not parsed.path.startswith("/zh/"):
            continue
        if is_factor_detail(parsed.path):
            links.add(absolute)
    return sorted(links)


def extract_description(soup: BeautifulSoup) -> str:
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()
    container = soup.find("article") or soup.find("main") or soup.body
    if not container:
        return ""
    paragraphs = [
        p.get_text(" ", strip=True)
        for p in container.find_all("p")
        if p.get_text(strip=True)
    ]
    return "\n".join(paragraphs).strip()


def parse_factor_page(html: str, url: str) -> Factor:
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url
    description = extract_description(soup)
    return Factor(name=title, description=description, url=url)


def write_json(path: Path, factors: Iterable[Factor]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump([asdict(factor) for factor in factors], handle, ensure_ascii=False, indent=2)


def write_csv(path: Path, factors: Iterable[Factor]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "description", "url"])
        writer.writeheader()
        for factor in factors:
            writer.writerow(asdict(factor))


def scrape_factors(base_url: str, *, limit: int | None, delay: float) -> list[Factor]:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    landing_html = fetch(session, base_url)
    factor_links = discover_factor_links(landing_html, base_url)
    if limit is not None:
        factor_links = factor_links[:limit]

    factors: list[Factor] = []
    for index, link in enumerate(factor_links, start=1):
        html = fetch(session, link)
        factor = parse_factor_page(html, link)
        factors.append(factor)
        print(f"[{index}/{len(factor_links)}] {factor.name}")
        time.sleep(delay)
    return factors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape factors.directory Chinese factors.")
    parser.add_argument("--base-url", default=BASE_URL, help="Base URL to crawl.")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of factors.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds.")
    parser.add_argument("--json", default="data/factors_zh.json", help="JSON output path.")
    parser.add_argument("--csv", default="data/factors_zh.csv", help="CSV output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    factors = scrape_factors(args.base_url, limit=args.limit, delay=args.delay)
    write_json(Path(args.json), factors)
    write_csv(Path(args.csv), factors)
    print(f"Saved {len(factors)} factors.")


if __name__ == "__main__":
    main()
