#!/usr/bin/env python3
"""Generate sitemap index, split sitemaps, and RSS discovery feed.

This script is intentionally content-neutral: it does not edit page canonicals,
titles, robots meta tags, or article content. It only publishes discovery
artifacts from the current checkout.
"""

from __future__ import annotations

import datetime as dt
import html
import os
import re
import subprocess
import sys
from email.utils import format_datetime
from pathlib import Path
from xml.etree import ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.betlegendpicks.com"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
RSS_LIMIT = 200
STATIC_FEATURED_LINK_LIMIT = None

EXCLUDED_DIRS = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    "scripts",
    "data",
    "logs",
    "verification-screenshots",
    "preview-screenshots",
    "chrome-proof-profile",
    "edge-profile",
    "edge-sel-profile",
    "tools",
    "Desktop",
}
EXCLUDED_SUFFIXES = (".bak.html", ".tmp.html")
EXCLUDED_EXACT = {
    "404.html",
    "preview.html",
    "preview-endgame-daily-card.html",
    "index-hero-preview.html",  # gitignored staging artifact; 404s live, must not enter sitemap
}
_GIT_LASTMOD_CACHE: dict[str, str] | None = None
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


def relpath(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def run_git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=REPO, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


_TRACKED_HTML: set[str] | None = None


def tracked_html() -> set[str]:
    """Set of git-tracked .html paths (repo-relative posix). Untracked/gitignored
    files can never be live, so they must never enter the sitemap."""
    global _TRACKED_HTML
    if _TRACKED_HTML is not None:
        return _TRACKED_HTML
    out = run_git(["ls-files", "*.html"])
    _TRACKED_HTML = set(out.splitlines()) if out else set()
    return _TRACKED_HTML


def git_lastmod_cache() -> dict[str, str]:
    global _GIT_LASTMOD_CACHE
    if _GIT_LASTMOD_CACHE is not None:
        return _GIT_LASTMOD_CACHE
    cache: dict[str, str] = {}
    try:
        output = subprocess.check_output(
            ["git", "log", "--name-only", "--format=@@%cs", "--", "*.html", "*.xml", "*.txt", "*.js"],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        _GIT_LASTMOD_CACHE = cache
        return cache
    current_date = ""
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("@@"):
            current_date = line[2:]
            continue
        if current_date and line not in cache:
            cache[line] = current_date
    _GIT_LASTMOD_CACHE = cache
    return cache


def file_lastmod(path: Path) -> str:
    rel = relpath(path)
    filename_date = date_from_filename(rel)
    if filename_date:
        return filename_date
    content_date = published_date_from_content(path)
    if content_date:
        return content_date
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).date().isoformat()


def date_from_filename(rel: str) -> str | None:
    match = DATE_RE.search(rel)
    if not match:
        return None
    month, day, year = match.groups()
    return f"{year}-{MONTHS[month.lower()]}-{int(day):02d}"


def published_date_from_content(path: Path) -> str | None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    iso = re.search(r'(?:datePublished|FORCED_PAGE_DATE)[^0-9]*(\d{4}-\d{2}-\d{2})', content)
    if iso:
        return iso.group(1)
    text = re.search(
        r'(?:Published|Updated)?\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})',
        content,
        re.I,
    )
    if text:
        month, day, year = text.groups()
        return f"{year}-{MONTHS[month.lower()]}-{int(day):02d}"
    return None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def is_redirect_stub(content: str) -> bool:
    # A stub is an immediate meta-refresh, a top-level location.replace(), or a
    # "Redirecting to ..." shell. Plain `window.location.href =` inside calendar
    # click handlers is NOT a stub (false-positived mlb-calendar.html etc.).
    return bool(
        re.search(r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']\s*0\s*;', content, re.I)
        or re.search(r"window\.location\.replace\(", content[:4000])
        or re.search(r">\s*Redirecting to\b", content, re.I)
    )


def is_noindex(content: str) -> bool:
    robots = re.findall(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)["\']', content, re.I)
    robots += re.findall(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']robots["\']', content, re.I)
    return any("noindex" in value.lower() for value in robots)


def canonical_path(content: str) -> str | None:
    match = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']', content, re.I)
    if not match:
        match = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', content, re.I)
    if not match:
        return None
    href = match.group(1).strip()
    if href.startswith(BASE_URL + "/"):
        return href[len(BASE_URL) + 1 :]
    if href == BASE_URL + "/":
        return "index.html"
    if href.startswith("/"):
        return href.lstrip("/")
    return None


def is_public_html(path: Path) -> bool:
    if path.suffix.lower() != ".html":
        return False
    rel = relpath(path)
    tracked = tracked_html()
    if tracked and rel not in tracked:
        return False
    parts = set(rel.split("/")[:-1])
    if parts & EXCLUDED_DIRS:
        return False
    if path.name in EXCLUDED_EXACT or path.name.endswith(EXCLUDED_SUFFIXES):
        return False
    content = read_text(path)
    if is_noindex(content) or is_redirect_stub(content):
        return False
    canon = canonical_path(content)
    if canon and canon not in {rel, "index.html" if rel == "index.html" else rel}:
        return False
    return True


def url_for(rel: str) -> str:
    if rel == "index.html":
        return BASE_URL + "/"
    return BASE_URL + "/" + rel


def classify(rel: str, featured_pages: set[str]) -> str:
    name = Path(rel).name
    if rel in featured_pages or name in featured_pages:
        return "featured-games"
    if name.startswith("featured-game") or "featured-games" in name:
        return "featured-games"
    if name in {
        "featured-game-of-the-day.html",
        "featured-game-calendar.html",
    }:
        return "featured-games"
    if date_from_filename(name) and re.search(r"(?:^|-)(mlb|nba|nhl|nfl|ncaaf|ncaab|soccer)(?:-|$)", name):
        return "previews"
    if re.search(r"(mlb|nba|nhl|nfl|ncaaf|ncaab|soccer|college-basketball).*(preview|previews|analysis-stats|slate|board)", name):
        return "previews"
    if "record" in name or name in {"records.html", "betlegend-verified-records.html"}:
        return "records"
    if any(token in name for token in ("pick", "prediction", "blog", "news", "archive")):
        return "posts"
    return "main"


def changefreq_priority(category: str, rel: str) -> tuple[str, str]:
    if rel == "index.html":
        return "daily", "1.0"
    if category in {"previews", "featured-games", "posts"}:
        return "daily", "0.8"
    if category == "records":
        return "weekly", "0.7"
    return "weekly", "0.6"


def build_entries() -> dict[str, list[dict[str, str]]]:
    groups = {name: [] for name in ("main", "previews", "featured-games", "posts", "records")}
    featured_pages = {page for _, page, _ in featured_game_entries()}
    for path in sorted(REPO.rglob("*.html")):
        if not is_public_html(path):
            continue
        rel = relpath(path)
        category = classify(rel, featured_pages)
        changefreq, priority = changefreq_priority(category, rel)
        groups[category].append(
            {
                "rel": rel,
                "loc": url_for(rel),
                "lastmod": file_lastmod(path),
                "changefreq": changefreq,
                "priority": priority,
            }
        )
    return groups


def write_urlset(filename: str, entries: list[dict[str, str]]) -> None:
    ET.register_namespace("", SITEMAP_NS)
    root = ET.Element(f"{{{SITEMAP_NS}}}urlset")
    for entry in sorted(entries, key=lambda item: item["loc"]):
        url = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
        ET.SubElement(url, f"{{{SITEMAP_NS}}}loc").text = entry["loc"]
        ET.SubElement(url, f"{{{SITEMAP_NS}}}lastmod").text = entry["lastmod"]
        ET.SubElement(url, f"{{{SITEMAP_NS}}}changefreq").text = entry["changefreq"]
        ET.SubElement(url, f"{{{SITEMAP_NS}}}priority").text = entry["priority"]
    tree = ET.ElementTree(root)
    tree.write(REPO / filename, encoding="utf-8", xml_declaration=True)


def write_sitemap_index(files: list[str]) -> None:
    ET.register_namespace("", SITEMAP_NS)
    root = ET.Element(f"{{{SITEMAP_NS}}}sitemapindex")
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    for filename in files:
        sitemap = ET.SubElement(root, f"{{{SITEMAP_NS}}}sitemap")
        ET.SubElement(sitemap, f"{{{SITEMAP_NS}}}loc").text = BASE_URL + "/" + filename
        ET.SubElement(sitemap, f"{{{SITEMAP_NS}}}lastmod").text = today
    ET.ElementTree(root).write(REPO / "sitemap.xml", encoding="utf-8", xml_declaration=True)


def title_for(path: Path) -> str:
    content = read_text(path)
    match = re.search(r"<title>(.*?)</title>", content, re.I | re.S)
    if match:
        return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
    return path.stem.replace("-", " ").title()


def description_for(path: Path) -> str:
    content = read_text(path)
    match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', content, re.I | re.S)
    if not match:
        match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', content, re.I | re.S)
    if match:
        return re.sub(r"\s+", " ", html.unescape(match.group(1))).strip()
    return title_for(path)


def write_feed(entries: list[dict[str, str]]) -> None:
    latest = sorted(entries, key=lambda item: (date_from_filename(item["rel"]) or item["lastmod"], item["lastmod"]), reverse=True)[:RSS_LIMIT]
    now = dt.datetime.now(dt.timezone.utc)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "<channel>",
        "<title>BetLegend Picks Latest Content</title>",
        f"<link>{BASE_URL}/</link>",
        "<description>Latest BetLegend featured games, previews, picks, and news.</description>",
        f"<lastBuildDate>{format_datetime(now)}</lastBuildDate>",
    ]
    for entry in latest:
        path = REPO / entry["rel"]
        pub_date = dt.datetime.fromisoformat(entry["lastmod"]).replace(tzinfo=dt.timezone.utc)
        lines.extend(
            [
                "<item>",
                f"<title>{html.escape(title_for(path))}</title>",
                f"<link>{entry['loc']}</link>",
                f"<guid>{entry['loc']}</guid>",
                f"<pubDate>{format_datetime(pub_date)}</pubDate>",
                f"<description>{html.escape(description_for(path))}</description>",
                "</item>",
            ]
        )
    lines.extend(["</channel>", "</rss>", ""])
    (REPO / "feed.xml").write_text("\n".join(lines), encoding="utf-8")


def ensure_robots() -> None:
    robots = REPO / "robots.txt"
    sitemap_line = f"Sitemap: {BASE_URL}/sitemap.xml"
    if robots.exists():
        content = robots.read_text(encoding="utf-8", errors="ignore")
        if sitemap_line in content:
            return
        content = re.sub(r"(?im)^Sitemap:.*$", sitemap_line, content)
        if sitemap_line not in content:
            content = content.rstrip() + "\n\n" + sitemap_line + "\n"
    else:
        content = f"User-agent: *\nAllow: /\n\n{sitemap_line}\n"
    robots.write_text(content, encoding="utf-8")


def featured_game_entries() -> list[tuple[str, str, str]]:
    path = REPO / "featured-games-data.js"
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8", errors="ignore")
    entries = re.findall(
        r'\{\s*date:\s*"(\d{4}-\d{2}-\d{2})"\s*,\s*page:\s*"([^"]+)"\s*,\s*title:\s*"([^"]+)"',
        content,
    )
    return sorted(entries, key=lambda item: item[0], reverse=True)


def update_featured_calendar_static_links() -> None:
    page = REPO / "featured-game-calendar.html"
    entries = featured_game_entries()
    if STATIC_FEATURED_LINK_LIMIT is not None:
        entries = entries[:STATIC_FEATURED_LINK_LIMIT]
    if not page.exists() or not entries:
        return
    links = [
        '<section id="featured-game-static-links" style="max-width:1100px;margin:40px auto;padding:24px;border:1px solid rgba(0,224,255,.18);border-radius:12px;background:rgba(0,0,0,.24)">',
        '<h2 style="font-family:Orbitron,Arial,sans-serif;color:#00e0ff;margin:0 0 16px">Latest Featured Game Archive Links</h2>',
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px">',
    ]
    for date, page_name, title in entries:
        label = f"{date} - {html.escape(title)}"
        links.append(
            f'<a href="/{html.escape(page_name)}" style="display:block;color:#FFD700;text-decoration:none;padding:10px 12px;border:1px solid rgba(255,215,0,.18);border-radius:8px;background:rgba(255,215,0,.06)">{label}</a>'
        )
    links.extend(["</div>", "</section>"])
    block = "\n".join(
        [
            "<!-- FEATURED-GAME-STATIC-LINKS-START -->",
            *links,
            "<!-- FEATURED-GAME-STATIC-LINKS-END -->",
        ]
    )
    content = page.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"<!-- FEATURED-GAME-STATIC-LINKS-START -->.*?<!-- FEATURED-GAME-STATIC-LINKS-END -->", re.S)
    if pattern.search(content):
        content = pattern.sub(block, content)
    else:
        content = content.replace("</body>", block + "\n</body>", 1)
    page.write_text(content, encoding="utf-8")


def main() -> int:
    groups = build_entries()
    files = []
    for category, filename in [
        ("main", "sitemap-main.xml"),
        ("previews", "sitemap-previews.xml"),
        ("featured-games", "sitemap-featured-games.xml"),
        ("posts", "sitemap-posts.xml"),
        ("records", "sitemap-records.xml"),
    ]:
        write_urlset(filename, groups[category])
        files.append(filename)
    write_sitemap_index(files)
    all_entries = [entry for entries in groups.values() for entry in entries]
    write_feed(all_entries)
    ensure_robots()
    update_featured_calendar_static_links()
    print(f"Generated sitemap index with {len(files)} child sitemaps and {len(all_entries)} URLs.")
    print("Generated feed.xml.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
