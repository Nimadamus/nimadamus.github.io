#!/usr/bin/env python3
"""Fail the build if Featured Game of the Day data or routing is stale."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DATA_FILE = REPO / "featured-games-data.js"
ENTRY_RE = re.compile(
    r"""\{\s*date:\s*["'](?P<date>\d{4}-\d{2}-\d{2})["']\s*,\s*page:\s*["'](?P<page>[^"']+)["']\s*,\s*title:\s*["'](?P<title>[^"']+)["']\s*\}"""
)


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

    print(f"Featured Game freshness OK: {latest['date']} -> {latest['page']} ({age_days} days old)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
