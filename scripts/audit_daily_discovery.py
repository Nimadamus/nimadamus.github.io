#!/usr/bin/env python3
"""Audit daily publishing discovery, indexability, freshness, and navigation.

The audit intentionally fails on the latest generated surfaces only. It is a
deployment guard against fresh regressions, not a full historical SEO cleanup.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.betlegendpicks.com"
CURRENT_MONTH_LABEL = "May 2026"
CURRENT_MONTH_PREFIX = "2026-05"
NAV_TOKENS = ["Handicapping Hub", "Game Previews", "Resources", "Game of the Day"]
SPORT_INDEXES = {
    "mlb": "mlb-previews.html",
    "nba": "nba-previews.html",
    "nhl": "nhl-previews.html",
}
DATE_RE = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{1,2})-(\d{4})",
    re.I,
)
MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


class AuditError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Audit the public website instead of local files.")
    parser.add_argument("--max-age-days", type=int, default=7)
    parser.add_argument("--base-url", default=BASE_URL)
    return parser.parse_args()


def local_read(rel: str) -> tuple[int, dict[str, str], str]:
    if rel.startswith(BASE_URL + "/"):
        rel = rel[len(BASE_URL) + 1 :]
    path = REPO / rel
    if rel in {"", "/"}:
        path = REPO / "index.html"
    if not path.exists():
        raise AuditError(f"Missing local file: {rel}")
    return 200, {}, path.read_text(encoding="utf-8", errors="ignore")


def live_read(rel_or_url: str, base_url: str) -> tuple[int, dict[str, str], str]:
    url = rel_or_url if rel_or_url.startswith("http") else base_url.rstrip("/") + "/" + rel_or_url.lstrip("/")
    req = urllib.request.Request(url, headers={"User-Agent": "BetLegend discovery audit"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8", errors="ignore")
            headers = {k.lower(): v for k, v in response.headers.items()}
            return response.status, headers, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        headers = {k.lower(): v for k, v in exc.headers.items()}
        return exc.code, headers, body


def read(rel: str, args: argparse.Namespace) -> tuple[int, dict[str, str], str]:
    return live_read(rel, args.base_url) if args.live else local_read(rel)


def html_files() -> list[str]:
    return sorted(path.relative_to(REPO).as_posix() for path in REPO.glob("*.html"))


def date_from_filename(name: str) -> str | None:
    match = DATE_RE.search(name)
    if not match:
        return None
    month, day, year = match.groups()
    return f"{year}-{MONTHS[month.lower()]}-{int(day):02d}"


def latest_sport_page(sport: str) -> tuple[str, str]:
    candidates = []
    for rel in html_files():
        name = Path(rel).name.lower()
        if sport not in name or "archive" in name or "record" in name:
            continue
        page_date = date_from_filename(name)
        if page_date:
            candidates.append((page_date, rel))
    if not candidates:
        raise AuditError(f"No dated {sport.upper()} page candidates found")
    return max(candidates)


def featured_entries() -> list[tuple[str, str]]:
    path = REPO / "featured-games-data.js"
    if not path.exists():
        raise AuditError("Missing featured-games-data.js")
    content = path.read_text(encoding="utf-8", errors="ignore")
    entries = re.findall(r'date:\s*"(\d{4}-\d{2}-\d{2})"\s*,\s*page:\s*"([^"]+)"', content)
    if not entries:
        raise AuditError("No FEATURED_GAMES entries found")
    return entries


def latest_featured_page() -> tuple[str, str]:
    return max(featured_entries())


def sitemap_urls(args: argparse.Namespace) -> set[str]:
    status, _, content = read("sitemap.xml", args)
    if status != 200:
        raise AuditError(f"sitemap.xml returned HTTP {status}")
    root = ET.fromstring(content.encode("utf-8"))
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    child_locs = [el.text or "" for el in root.findall("sm:sitemap/sm:loc", ns)]
    urls = {el.text or "" for el in root.findall("sm:url/sm:loc", ns)}
    for loc in child_locs:
        status, _, child = read(loc, args)
        if status != 200:
            raise AuditError(f"Child sitemap {loc} returned HTTP {status}")
        child_root = ET.fromstring(child.encode("utf-8"))
        urls.update(el.text or "" for el in child_root.findall("sm:url/sm:loc", ns))
    return urls


def canonical(content: str) -> str | None:
    match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', content, re.I)
    if not match:
        match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', content, re.I)
    return match.group(1).strip() if match else None


def has_noindex(content: str, headers: dict[str, str]) -> bool:
    if "noindex" in headers.get("x-robots-tag", "").lower():
        return True
    robots = re.findall(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
    robots += re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']robots["\']', content, re.I)
    return any("noindex" in value.lower() for value in robots)


def require_page(rel: str, args: argparse.Namespace, urls: set[str], allow_canonical_target: bool = False) -> str:
    status, headers, content = read(rel, args)
    if status != 200:
        raise AuditError(f"{rel} returned HTTP {status}")
    if has_noindex(content, headers):
        raise AuditError(f"{rel} is noindexed")
    if not re.search(r"<title>\s*[^<]+", content, re.I):
        raise AuditError(f"{rel} has blank or missing title")
    if not (
        re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'][^"\']+', content, re.I)
        or re.search(r'<meta[^>]+content=["\'][^"\']+["\'][^>]+name=["\']description["\']', content, re.I)
    ):
        raise AuditError(f"{rel} is missing meta description")
    full_url = args.base_url.rstrip("/") + "/" + rel.lstrip("/")
    canon = canonical(content)
    if canon and not allow_canonical_target and canon.rstrip("/") != full_url.rstrip("/"):
        raise AuditError(f"{rel} canonical mismatch: {canon}")
    if full_url not in urls:
        raise AuditError(f"{rel} is missing from sitemap")
    if not all(token in content for token in NAV_TOKENS):
        raise AuditError(f"{rel} is missing current full navigation tokens")
    return content


def assert_linked(source_rel: str, target_rel: str, args: argparse.Namespace) -> None:
    status, _, content = read(source_rel, args)
    if status != 200:
        raise AuditError(f"{source_rel} returned HTTP {status}")
    if target_rel.lstrip("/") not in content:
        raise AuditError(f"{target_rel} is not linked from {source_rel}")


def audit(args: argparse.Namespace) -> None:
    urls = sitemap_urls(args)
    robots_status, _, robots = read("robots.txt", args)
    if robots_status != 200:
        raise AuditError(f"robots.txt returned HTTP {robots_status}")
    if f"Sitemap: {args.base_url.rstrip('/')}/sitemap.xml" not in robots:
        raise AuditError("robots.txt does not reference sitemap.xml")

    latest_featured_date, latest_featured = latest_featured_page()
    latest_date = dt.date.fromisoformat(latest_featured_date)
    today = dt.date.today()
    if (today - latest_date).days > args.max_age_days:
        raise AuditError(f"Latest featured game is stale: {latest_featured_date} {latest_featured}")
    require_page(latest_featured, args, urls)
    assert_linked("featured-game-of-the-day.html", latest_featured, args)
    assert_linked("featured-game-calendar.html", latest_featured, args)

    may_featured = [date for date, _ in featured_entries() if date.startswith(CURRENT_MONTH_PREFIX)]
    if len(may_featured) < 2:
        raise AuditError(f"Featured calendar data does not expose current month entries: {may_featured}")

    for sport, index_rel in SPORT_INDEXES.items():
        status, _, index_content = read(index_rel, args)
        if status != 200:
            raise AuditError(f"{index_rel} returned HTTP {status}")
        if CURRENT_MONTH_LABEL not in index_content:
            raise AuditError(f"{index_rel} does not show {CURRENT_MONTH_LABEL}")
        page_date, page_rel = latest_sport_page(sport)
        if not page_date.startswith(CURRENT_MONTH_PREFIX):
            raise AuditError(f"Latest {sport.upper()} page is not current month: {page_date} {page_rel}")
        require_page(page_rel, args, urls, allow_canonical_target=True)
        assert_linked(index_rel, page_rel, args)

    print("Discovery audit passed.")
    print(f"Latest featured game: {latest_featured_date} {latest_featured}")
    for sport in SPORT_INDEXES:
        page_date, page_rel = latest_sport_page(sport)
        print(f"Latest {sport.upper()} preview: {page_date} {page_rel}")


def main() -> int:
    args = parse_args()
    try:
        audit(args)
    except AuditError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
