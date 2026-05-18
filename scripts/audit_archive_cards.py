#!/usr/bin/env python3
"""Audit BetLegend archive and homepage card coverage without writing files."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

EXCLUDED_DIRS = {
    ".git",
    ".github",
    ".gh-api-tmp",
    ".gh-cache",
    ".gh-config",
    ".npm-cache",
    ".playwright-browsers",
    "__pycache__",
    "archives",
    "bankroll-management",
    "browser-live-proof-profile",
    "chrome-cli-profile",
    "chrome-cli-profile3",
    "chrome-grid-proof-profile",
    "chrome-headless-proof-profile",
    "chrome-live-homepage-proof",
    "chrome-live-homepage-proof2",
    "data",
    "edge-headless-proof-profile",
    "edge-live-homepage-proof",
    "images",
    "pro",
    "scripts",
    "tmp_vegas_imgs",
    "verification-screenshots",
    "videos",
}

EXCLUDED_FILES = {
    "404.html",
    "about-us.html",
    "about.html",
    "archive.html",
    "bankroll.html",
    "betlegend-verified-records.html",
    "betting-101.html",
    "betting-calculators.html",
    "betting-education.html",
    "betting-glossary.html",
    "blog.html",
    "classic-odds.html",
    "contact.html",
    "crosssport-parlays-records.html",
    "daily-picks.html",
    "email.html",
    "ev-calculator.html",
    "feed.xml",
    "google-sheet-pick-page-template.html",
    "handicapping-hub.html",
    "index.html",
    "latest.html",
    "llms.txt",
    "mlb-calendar.html",
    "moneyline-calculator.html",
    "news.html",
    "nfl.html",
    "nhl-betting-hub.html",
    "nhl-home-away-splits.html",
    "nhl-team-trends.html",
    "nhl-totals-trends.html",
    "podcast.html",
    "point-spread-betting-explained.html",
    "preview-endgame-daily-card.html",
    "privacy.html",
    "proofofpicks.html",
    "records.html",
    "risk-of-ruin-calculator.html",
    "sitemap.html",
    "smartbets.html",
    "social.html",
    "sportsbook.html",
    "subscribe.html",
    "terms.html",
    "track-record.html",
    "upcomingpicks.html",
    "verified-trends.html",
    "what-does-minus-110-mean.html",
}

EXCLUDED_FILE_RE = re.compile(
    r"^(?:handicapping-hub-\d{4}-\d{2}-\d{2}|"
    r"(?:mlb|nba|nhl|soccer|college-basketball)-previews(?:-archive-[a-z]+-\d{4})?|"
    r".+-records)\.html$",
    re.I,
)

DATED_PREVIEW_ROUTE_RE = re.compile(
    r"^(?:mlb|nba|nhl|soccer|college-basketball)-previews(?:-archive-[a-z]+-\d{4})?\.html$",
    re.I,
)

FILENAME_DATE_RE = re.compile(
    r"(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{1,2})-(\d{4})",
    re.I,
)
ISO_DATE_RE = re.compile(r"(?:datePublished|dateModified|FORCED_PAGE_DATE)[^0-9]*(\d{4}-\d{2}-\d{2})", re.I)
TEXT_DATE_RE = re.compile(
    r"(?:Published|Posted|Updated|Last Updated)?[^A-Za-z0-9]{0,25}"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),?\s+(\d{4})",
    re.I,
)
ARCHIVE_HREF_RE = re.compile(r'<li><a href="([^"]+)">', re.I)
ARCHIVE_CARD_HREF_RE = re.compile(r'<article class="archive-card">.*?<a href="([^"]+)"', re.I | re.S)
PICK_URL_RE = re.compile(r"url:\s*[\"']([^\"']+)[\"']")

SUPPLEMENTAL_POSTS = [
    {
        "url": "college-basketball-previews-archive-may-2026.html#2026-05-16",
        "date": "2026-05-16",
        "title": "NCAAB Analysis Archive: May 16, 2026",
    },
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def skip(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if DATED_PREVIEW_ROUTE_RE.match(path.name):
        return path.name.endswith((".bak.html", ".tmp.html")) or any(part in EXCLUDED_DIRS for part in rel.parts[:-1])
    return (
        path.name in EXCLUDED_FILES
        or EXCLUDED_FILE_RE.match(path.name) is not None
        or path.name.endswith((".bak.html", ".tmp.html"))
        or any(part in EXCLUDED_DIRS for part in rel.parts[:-1])
    )


def date_from_filename(path: Path) -> dt.date | None:
    match = FILENAME_DATE_RE.search(path.name)
    if not match:
        return None
    month, day, year = match.groups()
    return dt.date(int(year), MONTHS[month.lower()], int(day))


def date_from_content(content: str) -> dt.date | None:
    match = ISO_DATE_RE.search(content)
    if match:
        try:
            return dt.date.fromisoformat(match.group(1))
        except ValueError:
            pass
    match = TEXT_DATE_RE.search(content)
    if match:
        month, day, year = match.groups()
        return dt.date(int(year), MONTHS[month.lower()], int(day))
    return None


def title_for(path: Path, content: str) -> str:
    for pattern in (
        r"<h1[^>]*>(.*?)</h1>",
        r"<title[^>]*>(.*?)</title>",
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)["\']',
    ):
        match = re.search(pattern, content, re.I | re.S)
        if match:
            title = clean(match.group(1))
            title = re.sub(r"\s*\|\s*BetLegend(?:Picks)?\s*$", "", title, flags=re.I)
            if title:
                return title
    return path.stem.replace("-", " ").title()


def is_redirect_or_noindex(content: str) -> bool:
    return bool(
        re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', content, re.I)
        or re.search(r"window\.location\.(?:replace|href)\s*=", content, re.I)
        or re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', content, re.I)
    )


def collect_posts() -> list[dict[str, str]]:
    posts = []
    for path in ROOT.glob("*.html"):
        if skip(path):
            continue
        content = read(path)
        if is_redirect_or_noindex(content):
            continue
        published = date_from_filename(path) or date_from_content(content)
        if not published:
            continue
        posts.append(
            {
                "url": path.name,
                "date": published.isoformat(),
                "title": title_for(path, content),
            }
        )
    existing_urls = {post["url"] for post in posts}
    posts.extend(post for post in SUPPLEMENTAL_POSTS if post["url"] not in existing_urls)
    posts.sort(key=lambda item: (item["date"], item["url"]), reverse=True)
    return posts


def archive_urls() -> set[str]:
    path = ROOT / "archive.html"
    if not path.exists():
        return set()
    content = read(path)
    return set(ARCHIVE_HREF_RE.findall(content)) | set(ARCHIVE_CARD_HREF_RE.findall(content))


def latest_urls() -> set[str]:
    path = ROOT / "latest.html"
    if not path.exists():
        return set()
    return set(ARCHIVE_HREF_RE.findall(read(path)))


def homepage_pick_urls() -> set[str]:
    path = ROOT / "homepage-picks-data.js"
    if not path.exists():
        return set()
    return set(PICK_URL_RE.findall(read(path)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="Only list missing posts on or after YYYY-MM-DD.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text.")
    args = parser.parse_args()

    posts = collect_posts()
    archive = archive_urls()
    latest = latest_urls()
    picks = homepage_pick_urls()
    missing_archive = [p for p in posts if p["url"] not in archive]
    missing_latest = [p for p in posts if p["url"] not in latest]
    if args.since:
        cutoff = dt.date.fromisoformat(args.since).isoformat()
        listed_missing_archive = [p for p in missing_archive if p["date"] >= cutoff]
        listed_missing_latest = [p for p in missing_latest if p["date"] >= cutoff]
    else:
        listed_missing_archive = missing_archive
        listed_missing_latest = missing_latest

    report = {
        "post_files_found": len(posts),
        "archive_entries": len(archive),
        "latest_entries": len(latest),
        "homepage_pick_cards": len(picks),
        "missing_from_archive": len(missing_archive),
        "missing_from_latest": len(missing_latest),
        "listed_missing_from_archive": listed_missing_archive,
        "listed_missing_from_latest": listed_missing_latest,
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Post/article files found: {report['post_files_found']}")
        print(f"Archive entries before/now: {report['archive_entries']}")
        print(f"Latest entries before/now: {report['latest_entries']}")
        print(f"Homepage pick cards before/now: {report['homepage_pick_cards']}")
        print(f"Missing from archive: {report['missing_from_archive']}")
        print(f"Missing from latest: {report['missing_from_latest']}")
        print("\nMissing from archive list:")
        for item in listed_missing_archive:
            line = f"{item['date']} | {item['url']} | {item['title']}"
            print(line.encode("ascii", "xmlcharrefreplace").decode("ascii"))
        print("\nMissing from latest list:")
        for item in listed_missing_latest:
            line = f"{item['date']} | {item['url']} | {item['title']}"
            print(line.encode("ascii", "xmlcharrefreplace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
