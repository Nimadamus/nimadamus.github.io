#!/usr/bin/env python3
"""Fail the build if Featured Game of the Day data or routing is stale."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATA_FILE = REPO / "featured-games-data.js"
TITLE_GUARD_START_DATE = dt.date(2026, 5, 8)
DAILY_CONTINUITY_START_DATE = dt.date(2026, 5, 14)
ENTRY_RE = re.compile(
    r"""\{\s*date:\s*["'](?P<date>\d{4}-\d{2}-\d{2})["']\s*,\s*page:\s*["'](?P<page>[^"']+)["']\s*,\s*title:\s*["'](?P<title>[^"']+)["']\s*\}"""
)
H1_RE = re.compile(r"""<h1[^>]*class=["'][^"']*\bmain-title\b[^"']*["'][^>]*>(?P<title>.*?)</h1>""", re.IGNORECASE | re.DOTALL)
ANY_H1_RE = re.compile(r"""<h1[^>]*>(?P<title>.*?)</h1>""", re.IGNORECASE | re.DOTALL)
NEWS_HEADLINE_RE = re.compile(r'''"headline"\s*:\s*"(?P<title>(?:\\.|[^"\\])*)"''')
ODDS_RE = re.compile(r"""(?:\b[A-Z]{2,4}\s*)?[+-]\d+(?:\.\d+)?\b|\b\d+(?:\.\d+)?-point\b""", re.IGNORECASE)
TOTAL_RE = re.compile(r"""\b(?:total|over/under|o/u)\b|\b[OU]\s*\d{3}(?:\.\d+)?\b""", re.IGNORECASE)
INJURY_LIST_RE = re.compile(
    r"""\b(?:questionable|doubtful|out|return|returns|set to return|injur(?:y|ies)|injury report)\b.*\b[A-Z][a-z]+,\s+[A-Z][a-z]+,\s+(?:and\s+)?[A-Z][a-z]+""",
    re.IGNORECASE,
)
VENUE_RE = re.compile(r"""\b(?:arena|center|centre|stadium|field|garden|park|coliseum|dome)\b""", re.IGNORECASE)
SERIES_RE = re.compile(r"""\b(?:leads?|up|trails?|tied)\s+(?:series\s+)?\d-\d\b|\bseries\b""", re.IGNORECASE)
INJURY_RE = re.compile(r"""\b(?:questionable|doubtful|out|injur(?:y|ies)|return|returns|set to return)\b""", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--today", default=dt.date.today().isoformat(), help="Override today's date for deterministic checks.")
    parser.add_argument("--max-age-days", type=int, default=3, help="Maximum allowed age for the latest featured-game entry.")
    parser.add_argument(
        "--allow-missing-latest-page",
        action="store_true",
        help="Allow the latest page file to be absent locally. Use only when validating a partial local checkout.",
    )
    return parser.parse_args()


def load_entries() -> list[dict[str, str]]:
    if not DATA_FILE.exists():
        raise SystemExit(f"Missing {DATA_FILE.relative_to(REPO)}")
    entries: list[dict[str, str]] = []
    for match in ENTRY_RE.finditer(DATA_FILE.read_text(encoding="utf-8", errors="ignore")):
        entries.append(match.groupdict())
    if not entries:
        raise SystemExit("No FEATURED_GAMES entries found")
    return entries


def clean_html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_main_title(content: str, page: str) -> str:
    match = H1_RE.search(content)
    if not match:
        match = ANY_H1_RE.search(content)
    if not match:
        raise SystemExit(f"Featured Game page is missing a main hero title: {page}")
    return clean_html_text(match.group("title"))


def extract_news_headline(content: str) -> str | None:
    match = NEWS_HEADLINE_RE.search(content)
    if not match:
        return None
    return match.group("title").replace(r"\"", '"').replace(r"\/", "/")


def validate_featured_title(title: str, page: str, label: str) -> list[str]:
    issues: list[str] = []
    lower = title.lower()

    if len(title) > 110:
        issues.append(f"{label} exceeds 110 characters ({len(title)}): {title}")
    if lower.count("with") > 1:
        issues.append(f"{label} uses more than one 'with' clause: {title}")
    if ODDS_RE.search(title) and TOTAL_RE.search(title):
        issues.append(f"{label} contains both odds/spread and total context: {title}")
    if INJURY_LIST_RE.search(title):
        issues.append(f"{label} contains a comma-separated injury/return list: {title}")

    stacked_metadata = [
        bool(VENUE_RE.search(title)),
        bool(SERIES_RE.search(title)),
        bool(ODDS_RE.search(title)),
        bool(INJURY_RE.search(title)),
    ]
    if all(stacked_metadata):
        issues.append(f"{label} stacks venue, series status, betting line, and injury context: {title}")

    return [f"{page}: {issue}" for issue in issues]


def check_featured_title_quality(entries: list[dict[str, str]], allow_missing_latest_page: bool) -> None:
    issues: list[str] = []
    guarded_entries = [
        entry for entry in entries
        if dt.date.fromisoformat(entry["date"]) >= TITLE_GUARD_START_DATE
    ]

    for entry in guarded_entries:
        page = entry["page"].lstrip("/")
        page_path = REPO / page
        if not page_path.exists():
            if allow_missing_latest_page:
                continue
            issues.append(f"{page}: guarded Featured Game page is missing locally")
            continue

        content = page_path.read_text(encoding="utf-8", errors="ignore")
        hero_title = extract_main_title(content, page)
        issues.extend(validate_featured_title(hero_title, page, "hero title"))

        news_headline = extract_news_headline(content)
        if news_headline:
            issues.extend(validate_featured_title(news_headline, page, "NewsArticle headline"))

    if issues:
        raise SystemExit("Featured Game title quality check failed:\n- " + "\n- ".join(issues))


def check_homepage_widget_sync() -> None:
    sync_script = REPO / "scripts" / "sync_featured_game_preview.py"
    if not sync_script.exists():
        raise SystemExit("Missing homepage Featured Game sync script: scripts/sync_featured_game_preview.py")

    spec = importlib.util.spec_from_file_location("sync_featured_game_preview", sync_script)
    if not spec or not spec.loader:
        raise SystemExit("Could not load scripts/sync_featured_game_preview.py for homepage widget verification")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not module.verify_sync():
        raise SystemExit(
            "Homepage Featured Game widget is stale or mismatched. "
            "Run python scripts/sync_featured_game_preview.py and publish index.html."
        )


def check_recent_daily_continuity(entries: list[dict[str, str]], today: dt.date) -> None:
    if today < DAILY_CONTINUITY_START_DATE:
        return
    dates = {dt.date.fromisoformat(entry["date"]) for entry in entries}
    cursor = DAILY_CONTINUITY_START_DATE
    missing: list[str] = []
    while cursor <= today:
        if cursor not in dates:
            missing.append(cursor.isoformat())
        cursor += dt.timedelta(days=1)
    if missing:
        raise SystemExit(
            "Featured Game daily continuity check failed. Missing dates since "
            f"{DAILY_CONTINUITY_START_DATE.isoformat()}: {', '.join(missing)}"
        )


def check_featured_calendar_static_links(entries: list[dict[str, str]]) -> None:
    calendar = REPO / "featured-game-calendar.html"
    if not calendar.exists():
        raise SystemExit("Missing Featured Game calendar page: featured-game-calendar.html")
    content = calendar.read_text(encoding="utf-8", errors="ignore")
    required_tokens = [
        "featured-games-data.js",
        "FEATURED-GAME-STATIC-LINKS-START",
        "FEATURED-GAME-STATIC-LINKS-END",
    ]
    missing_tokens = [token for token in required_tokens if token not in content]
    if missing_tokens:
        raise SystemExit(f"Featured Game calendar is missing required tokens: {', '.join(missing_tokens)}")

    missing_pages = [
        entry["page"].lstrip("/")
        for entry in entries
        if entry["page"].lstrip("/") not in content
    ]
    if missing_pages:
        raise SystemExit(
            "Featured Game calendar static archive links are incomplete. "
            "Run python scripts/generate_discovery_artifacts.py. Missing: "
            + ", ".join(missing_pages[:20])
        )


def check_entrypoint_calendar_position() -> None:
    entrypoint = REPO / "featured-game-of-the-day.html"
    content = entrypoint.read_text(encoding="utf-8", errors="ignore")
    main_pos = content.find('<main class="main-content">')
    aside_pos = content.find('<aside class="calendar-sidebar">')
    if main_pos == -1 or aside_pos == -1:
        raise SystemExit("Featured Game entrypoint must include main content and calendar sidebar landmarks")
    if aside_pos < main_pos:
        raise SystemExit(
            "Featured Game entrypoint calendar sidebar appears before the article. "
            "Keep the article first and the calendar as the right rail."
        )


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today)
    entries = load_entries()
    latest = max(entries, key=lambda entry: entry["date"])
    latest_date = dt.date.fromisoformat(latest["date"])
    age_days = (today - latest_date).days

    spec = importlib.util.spec_from_file_location("sync_featured_game_preview", sync_script)
    if not spec or not spec.loader:
        raise SystemExit("Could not load scripts/sync_featured_game_preview.py for homepage widget verification")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not module.verify_sync():
        raise SystemExit(
            "Homepage Featured Game widget is stale or mismatched. "
            "Run python scripts/sync_featured_game_preview.py and publish index.html."
        )


def check_recent_daily_continuity(entries: list[dict[str, str]], today: dt.date) -> None:
    if today < DAILY_CONTINUITY_START_DATE:
        return
    dates = {dt.date.fromisoformat(entry["date"]) for entry in entries}
    cursor = DAILY_CONTINUITY_START_DATE
    missing: list[str] = []
    while cursor <= today:
        if cursor not in dates:
            missing.append(cursor.isoformat())
        cursor += dt.timedelta(days=1)
    if missing:
        raise SystemExit(
            "Featured Game daily continuity check failed. Missing dates since "
            f"{DAILY_CONTINUITY_START_DATE.isoformat()}: {', '.join(missing)}"
        )


def check_featured_calendar_static_links(entries: list[dict[str, str]]) -> None:
    calendar = REPO / "featured-game-calendar.html"
    if not calendar.exists():
        raise SystemExit("Missing Featured Game calendar page: featured-game-calendar.html")
    content = calendar.read_text(encoding="utf-8", errors="ignore")
    required_tokens = [
        "featured-games-data.js",
        "FEATURED-GAME-STATIC-LINKS-START",
        "FEATURED-GAME-STATIC-LINKS-END",
    ]
    missing_tokens = [token for token in required_tokens if token not in content]
    if missing_tokens:
        raise SystemExit(f"Featured Game calendar is missing required tokens: {', '.join(missing_tokens)}")

    missing_pages = [
        entry["page"].lstrip("/")
        for entry in entries
        if entry["page"].lstrip("/") not in content
    ]
    if missing_pages:
        raise SystemExit(
            "Featured Game calendar static archive links are incomplete. "
            "Run python scripts/generate_discovery_artifacts.py. Missing: "
            + ", ".join(missing_pages[:20])
        )


def check_entrypoint_calendar_position() -> None:
    entrypoint = REPO / "featured-game-of-the-day.html"
    content = entrypoint.read_text(encoding="utf-8", errors="ignore")
    main_pos = content.find('<main class="main-content">')
    aside_pos = content.find('<aside class="calendar-sidebar">')
    if main_pos == -1 or aside_pos == -1:
        raise SystemExit("Featured Game entrypoint must include main content and calendar sidebar landmarks")
    if aside_pos < main_pos:
        raise SystemExit(
            "Featured Game entrypoint calendar sidebar appears before the article. "
            "Keep the article first and the calendar as the right rail."
        )


def main() -> int:
    args = parse_args()
    today = dt.date.fromisoformat(args.today)
    entries = load_entries()
    latest = max(entries, key=lambda entry: entry["date"])
    latest_date = dt.date.fromisoformat(latest["date"])
    age_days = (today - latest_date).days

    if age_days < 0:
        raise SystemExit(f"Latest featured game is dated in the future: {latest['date']} {latest['page']}")
    if age_days > args.max_age_days:
        raise SystemExit(
            f"Featured Game of the Day is stale: latest entry is {latest['date']} "
            f"({latest['page']}), {age_days} days old; max allowed is {args.max_age_days}."
        )

    latest_page = REPO / latest["page"].lstrip("/")
    if not latest_page.exists() and not args.allow_missing_latest_page:
        raise SystemExit(f"Latest featured game page is missing locally: {latest['page']}")

    stale_alias = REPO / "wolves-vs-nuggets-nba-analysis-stats-preview.html"
    if stale_alias.exists():
        alias_content = stale_alias.read_text(encoding="utf-8", errors="ignore")
        if "April 27 Wolves vs Nuggets alias has been retired" not in alias_content:
            raise SystemExit(f"Stale Featured Game alias is not retired: {stale_alias.name}")

    entrypoint = REPO / "featured-game-of-the-day.html"
    if not entrypoint.exists():
        raise SystemExit("Missing stable Featured Game entrypoint: featured-game-of-the-day.html")
    entrypoint_content = entrypoint.read_text(encoding="utf-8", errors="ignore")
    required = [latest["page"], "featured-games-data.js", "/featured-game-of-the-day.html"]
    missing = [token for token in required if token not in entrypoint_content]
    if missing:
        raise SystemExit(f"Featured Game entrypoint is missing required current routing tokens: {', '.join(missing)}")

    check_featured_title_quality(entries, args.allow_missing_latest_page)
    check_homepage_widget_sync()
    check_recent_daily_continuity(entries, today)
    check_featured_calendar_static_links(entries)
    check_entrypoint_calendar_position()

    print(f"Featured Game freshness OK: {latest['date']} -> {latest['page']} ({age_days} days old)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
