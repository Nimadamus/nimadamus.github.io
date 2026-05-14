#!/usr/bin/env python3
"""Restore recent article discovery surfaces after accidental omissions."""

from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.betlegendpicks.com"
START_DATE = dt.date(2026, 4, 27)
END_DATE = dt.date(2026, 5, 14)
RECENT_SECTION_START = "<!-- RECENT-ARTICLE-RESTORE-START -->"
RECENT_SECTION_END = "<!-- RECENT-ARTICLE-RESTORE-END -->"
BAD_VEGAS_IMAGE = "images/vegas-golden-knights-moneyline-game-5-ducks-chart.svg"
OLD_VEGAS_ACTION_IMAGE = "images/vegas-golden-knights-ducks-game-5-action.webp"
GOOD_VEGAS_IMAGE = "images/vegas-golden-knights-premium-preview.webp"
CURRENT_NAV_LINKS = (
    '<div class="nav-links">'
    '<a href="index.html">Home</a>'
    '<a href="handicapping-hub.html">Handicapping Hub</a>'
    '<a href="blog.html">Blog</a>'
    '<a href="betlegend-picks-analysis-march-2026.html">Picks</a>'
    '<a href="records.html">Records</a>'
    '<a href="mlb-previews.html">Game Previews</a>'
    '<a href="bankroll.html">Resources</a>'
    '<a href="featured-game-of-the-day.html">Game of the Day</a>'
    '<a href="nba.html">NBA</a>'
    '<a href="nhl.html">NHL</a>'
    '<a href="mlb.html">MLB</a>'
    '<a href="nfl.html">NFL</a>'
    '<a href="ncaab.html">NCAAB</a>'
    '<a href="soccer.html">Soccer</a>'
    '<a href="news.html">News</a>'
    '</div>'
)

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
    "scripts",
    "tmp_vegas_imgs",
    "verification-screenshots",
    "videos",
}

EXCLUDED_FILES = {
    "404.html",
    "archive.html",
    "blog.html",
    "feed.xml",
    "latest.html",
    "preview-endgame-daily-card.html",
}

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


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def date_from_filename(path: Path) -> dt.date | None:
    match = FILENAME_DATE_RE.search(path.name)
    if not match:
        return None
    month, day, year = match.groups()
    return dt.date(int(year), MONTHS[month.lower()], int(day))


def date_from_content(content: str) -> dt.date | None:
    iso = ISO_DATE_RE.search(content)
    if iso:
        try:
            return dt.date.fromisoformat(iso.group(1))
        except ValueError:
            pass
    text = TEXT_DATE_RE.search(content)
    if text:
        month, day, year = text.groups()
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
            title = clean_text(match.group(1))
            title = re.sub(r"\s*\|\s*BetLegend(?:Picks)?\s*$", "", title, flags=re.I)
            if title:
                return title
    return path.stem.replace("-", " ").title()


def description_for(content: str, fallback: str) -> str:
    match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', content, re.I | re.S)
    if not match:
        match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']description["\']', content, re.I | re.S)
    if match:
        return clean_text(match.group(1))
    paragraph = re.search(r"<p[^>]*>(.*?)</p>", content, re.I | re.S)
    if paragraph:
        return clean_text(paragraph.group(1))
    return fallback


def is_redirect_or_noindex(content: str) -> bool:
    return bool(
        re.search(r'<meta[^>]+http-equiv=["\']refresh["\']', content, re.I)
        or re.search(r"window\.location\.(?:replace|href)\s*=", content, re.I)
        or re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', content, re.I)
    )


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(REPO).parts
    return (
        path.name in EXCLUDED_FILES
        or path.name.endswith((".bak.html", ".tmp.html"))
        or any(part in EXCLUDED_DIRS for part in rel_parts[:-1])
    )


def collect_articles() -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in REPO.rglob("*.html"):
        if should_skip(path):
            continue
        rel = path.relative_to(REPO).as_posix()
        content = read(path)
        if is_redirect_or_noindex(content):
            continue
        published = date_from_filename(path) or date_from_content(content)
        if not published or not (START_DATE <= published <= END_DATE):
            continue
        title = title_for(path, content)
        if rel in seen:
            continue
        seen.add(rel)
        articles.append(
            {
                "rel": rel,
                "date": published.isoformat(),
                "title": title,
                "description": description_for(content, title),
            }
        )
    return sorted(articles, key=lambda item: (item["date"], item["rel"]), reverse=True)


def display_date(iso_date: str) -> str:
    date = dt.date.fromisoformat(iso_date)
    return f"{date.strftime('%B')} {date.day}, {date.year}"


def write_archive(articles: list[dict[str, str]]) -> None:
    all_existing = []
    archive = REPO / "archive.html"
    if archive.exists():
        old = read(archive)
        for href, title, span in re.findall(
            r'<li><a href="([^"]+)">(.+?)</a>(?:\s*<span>(.+?)</span>)?</li>',
            old,
            re.I | re.S,
        ):
            if href not in {article["rel"] for article in articles} and href not in {"latest.html"}:
                all_existing.append((href, clean_text(title), clean_text(span)))

    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{BASE_URL}/archive.html">',
        "<title>Full Content Archive | BetLegendPicks</title>",
        '<meta name="description" content="Full crawlable archive of published pages from BetLegendPicks.">',
        "</head>",
        "<body>",
        "<main>",
        "<h1>Full Content Archive</h1>",
        "<p>Static archive regenerated May 14, 2026 with restored April 27-May 14 article coverage.</p>",
        '<p><a href="/">Home</a> | <a href="latest.html">Latest published pages</a></p>',
        "<ul>",
    ]
    for article in articles:
        lines.append(
            f'<li><a href="{html.escape(article["rel"])}">{html.escape(article["title"])}</a> '
            f"<span>{display_date(article['date'])}</span></li>"
        )
    for href, title, span in all_existing:
        suffix = f" <span>{html.escape(span)}</span>" if span else ""
        lines.append(f'<li><a href="{html.escape(href)}">{html.escape(title)}</a>{suffix}</li>')
    lines.extend(["</ul>", "</main>", "</body>", "</html>", ""])
    write(archive, "\n".join(lines))


def write_latest(articles: list[dict[str, str]]) -> None:
    lines = [
        "<!doctype html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="index, follow">',
        f'<link rel="canonical" href="{BASE_URL}/latest.html">',
        "<title>Latest Published Pages | BetLegendPicks</title>",
        '<meta name="description" content="Latest crawlable published pages from BetLegendPicks.">',
        "</head>",
        "<body>",
        "<main>",
        "<h1>Latest Published Pages</h1>",
        "<p>Static crawl links regenerated May 14, 2026.</p>",
        "<ul>",
    ]
    for article in articles[:120]:
        lines.append(
            f'<li><a href="{html.escape(article["rel"])}">{html.escape(article["title"])}</a> '
            f"<span>{display_date(article['date'])}</span></li>"
        )
    lines.extend(["</ul>", "</main>", "</body>", "</html>", ""])
    write(REPO / "latest.html", "\n".join(lines))


def restore_blog_section(articles: list[dict[str, str]]) -> None:
    blog = REPO / "blog.html"
    content = read(blog)
    cards = [
        RECENT_SECTION_START,
        '<section class="blog-post" id="restored-recent-articles">',
        '<h2 style="text-align:center !important; color:#d4af37 !important;">Restored Recent Articles</h2>',
        '<div class="post-time">Restored: May 14, 2026 | April 27-May 14 archive coverage</div>',
        '<div class="analysis-content" style="line-height:1.7;font-size:17px;">',
        "<p>Recent BetLegend picks and previews are restored below so the blog page again exposes the full current publishing run.</p>",
        '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin:22px 0;">',
    ]
    for article in articles:
        desc = article["description"]
        if len(desc) > 170:
            desc = desc[:167].rsplit(" ", 1)[0] + "..."
        cards.append(
            '<article style="border:1px solid rgba(212,175,55,.28);border-radius:8px;padding:14px;background:rgba(255,255,255,.03);">'
            f'<div style="color:#9ca3af;font-size:13px;margin-bottom:8px;">{display_date(article["date"])}</div>'
            f'<h3 style="font-size:18px;line-height:1.3;margin:0 0 8px;color:#fff;"><a href="{html.escape(article["rel"])}" style="color:#fff;text-decoration:none;">{html.escape(article["title"])}</a></h3>'
            f'<p style="margin:0 0 10px;color:#d1d5db;">{html.escape(desc)}</p>'
            f'<a href="{html.escape(article["rel"])}" style="color:#d4af37;font-weight:700;text-decoration:none;">Read article</a>'
            "</article>"
        )
    cards.extend(["</div>", "</div>", "</section>", "<hr/>", RECENT_SECTION_END])
    block = "\n".join(cards)
    pattern = re.compile(re.escape(RECENT_SECTION_START) + r".*?" + re.escape(RECENT_SECTION_END), re.S)
    if pattern.search(content):
        content = pattern.sub(block, content)
    else:
        marker = '<div class="blog-post" id="post-20260512-vegas-ml">'
        content = content.replace(marker, block + "\n" + marker, 1)
    content = content.replace(BAD_VEGAS_IMAGE, GOOD_VEGAS_IMAGE)
    content = content.replace(OLD_VEGAS_ACTION_IMAGE, GOOD_VEGAS_IMAGE)
    content = content.replace(
        "Vegas Golden Knights moneyline minus 150 Game 5 betting dashboard against Anaheim Ducks",
        "Premium black and gold hockey preview image for Golden Knights vs Ducks playoff betting analysis",
    )
    content = content.replace(
        "Vegas Golden Knights skater driving the puck against Anaheim Ducks in playoff action",
        "Premium black and gold hockey preview image for Golden Knights vs Ducks playoff betting analysis",
    )
    write(blog, content)


def replace_vegas_image() -> None:
    for filename in (
        "vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.html",
        "ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.html",
        "blog.html",
    ):
        path = REPO / filename
        if not path.exists():
            continue
        content = read(path)
        content = content.replace(BAD_VEGAS_IMAGE, GOOD_VEGAS_IMAGE)
        content = content.replace(OLD_VEGAS_ACTION_IMAGE, GOOD_VEGAS_IMAGE)
        content = content.replace(
            "Vegas Golden Knights moneyline minus 150 Game 5 betting dashboard against Anaheim Ducks",
            "Premium black and gold hockey preview image for Golden Knights vs Ducks playoff betting analysis",
        )
        content = content.replace(
            "Vegas Golden Knights skater driving the puck against Anaheim Ducks in playoff action",
            "Premium black and gold hockey preview image for Golden Knights vs Ducks playoff betting analysis",
        )
        write(path, content)


def restore_current_nav_tokens() -> None:
    for filename in (
        "brewers-moneyline-minus-139-padres-canning-harrison-mlb-pick-may-14-2026.html",
        "ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.html",
        "vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.html",
    ):
        path = REPO / filename
        if not path.exists():
            continue
        content = read(path)
        content = re.sub(r'<div class="nav-links">.*?</div>', CURRENT_NAV_LINKS, content, count=1, flags=re.S)
        write(path, content)


def ensure_index_links() -> None:
    index_links = {
        "mlb-previews.html": [
            (
                "brewers-moneyline-minus-139-padres-canning-harrison-mlb-pick-may-14-2026.html",
                "Brewers Moneyline -139 vs Padres Pick",
            )
        ],
        "nhl-previews.html": [
            (
                "ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.html",
                "Ducks Team Total Under 3.5 vs Golden Knights Game 6 Pick",
            ),
            (
                "canadiens-sabres-golden-knights-ducks-nhl-playoff-preview.html",
                "Canadiens-Sabres and Golden Knights-Ducks Full Preview",
            ),
        ],
        "nba-previews.html": [
            (
                "knicks-76ers-spurs-wolves-game-4-east-west-semis-nba-may-10-2026.html",
                "Knicks-76ers and Spurs-Wolves Game 4 Preview",
            ),
            (
                "nba-playoff-reset-cavaliers-pistons-spurs-timberwolves-game-six.html",
                "NBA Playoff Reset for May 14",
            ),
        ],
    }
    for filename, links in index_links.items():
        path = REPO / filename
        if not path.exists():
            continue
        content = read(path)
        cards = [
            "<!-- RESTORED-CURRENT-PICKS-START -->",
            '<section class="internal-links restored-current-picks">',
            "<h3>Current May 14 Picks and Articles</h3>",
        ]
        for href, label in links:
            cards.append(f'<a href="{html.escape(href)}">{html.escape(label)}</a>')
        cards.extend(["</section>", "<!-- RESTORED-CURRENT-PICKS-END -->"])
        block = "\n".join(cards)
        pattern = re.compile(r"<!-- RESTORED-CURRENT-PICKS-START -->.*?<!-- RESTORED-CURRENT-PICKS-END -->", re.S)
        if pattern.search(content):
            content = pattern.sub(block, content)
        elif '<div class="archive-link">' in content:
            content = content.replace('<div class="archive-link">', block + "\n\n" + '<div class="archive-link">', 1)
        else:
            content = content.replace("</main>", block + "\n</main>", 1)
        write(path, content)


def main() -> int:
    articles = collect_articles()
    if not articles:
        raise SystemExit("No April 27-May 14 articles found to restore.")
    write_archive(articles)
    write_latest(articles)
    restore_blog_section(articles)
    replace_vegas_image()
    restore_current_nav_tokens()
    ensure_index_links()
    print(f"Restored {len(articles)} articles from {START_DATE.isoformat()} through {END_DATE.isoformat()}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
