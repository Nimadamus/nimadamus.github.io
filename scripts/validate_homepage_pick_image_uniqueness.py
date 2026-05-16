#!/usr/bin/env python3
"""Validate homepage pick-card image quality and feed sequencing.

This is intentionally strict. The homepage should never ship duplicate card
images, placeholder/text thumbnails, overstacked same-day cards, or obvious
recent-date gaps again.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PICKS = ROOT / "homepage-picks-data.js"
SYSTEM = ROOT / "homepage-image-system.js"
ARCHIVE = ROOT / "archive.html"

MAX_CARDS_PER_DATE = 2
RECENT_CONTIGUOUS_DAYS = 19

BLOCKED_IMAGE_RE = re.compile(
    r"(?:"
    r"newlogo\.png|"
    r"data:image/|"
    r"homepage-preview/|"
    r"teamlogos/|"
    r"logos?/|"
    r"fallback/|"
    r"proof-bet-screenshot|"
    r"arbitrage|"
    r"ai-moneyball|"
    r"moneyview|"
    r"money-logo|"
    r"allstars|"
    r"collegeban|"
    r"mlb-picks-team-logos|"
    r"vegas-golden-knights-(?:premium-preview|moneyline-game-5-ducks-chart|ducks-game-5-action)"
    r")",
    re.I,
)


def parse_picks() -> list[dict[str, str]]:
    text = PICKS.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\{\s*sport:\s*\"(?P<sport>[^\"]+)\".*?"
        r"title:\s*\"(?P<title>(?:\\\"|[^\"])*)\".*?"
        r"date:\s*\"(?P<date>[^\"]+)\".*?"
        r"url:\s*\"(?P<url>[^\"]+)\".*?"
        r"image:\s*\"(?P<image>[^\"]*)\"\s*\}",
        re.S,
    )
    return [match.groupdict() for match in pattern.finditer(text)]


def parse_overrides() -> dict[str, str]:
    text = SYSTEM.read_text(encoding="utf-8")
    match = re.search(r"var PICK_IMAGE_OVERRIDES = \{(?P<body>.*?)\};", text, re.S)
    if not match:
        return {}
    entry_pattern = re.compile(r"'(?P<url>[^']+)':\s*'(?P<image>[^']+)'")
    return {entry.group("url"): entry.group("image") for entry in entry_pattern.finditer(match.group("body"))}


def parse_date(value: str):
    return datetime.strptime(value, "%B %d, %Y").date()


def parse_archive_urls() -> set[str]:
    if not ARCHIVE.exists():
        return set()
    text = ARCHIVE.read_text(encoding="utf-8")
    return set(re.findall(r'<li>\s*<a\s+href="([^"]+\.html)"', text))


def main() -> int:
    errors: list[str] = []
    picks = parse_picks()
    overrides = parse_overrides()
    if not picks:
        errors.append("homepage-picks-data.js has no pick cards.")

    archive_urls = parse_archive_urls()
    if archive_urls:
        for pick in picks:
            if pick["url"] not in archive_urls:
                errors.append(
                    f"Homepage pick {pick['url']} is missing from archive.html. "
                    "Every homepage URL must also be linked in archive.html so the "
                    "curated/capped homepage never orphans a published page."
                )
    else:
        errors.append("archive.html not found or empty; cannot run no-orphan check.")

    override_counts = Counter(overrides.values())
    for image, count in override_counts.items():
        if count > 1:
            errors.append(f"PICK_IMAGE_OVERRIDES repeats {image} {count} times.")

    rendered: list[tuple[str, str, str]] = []
    for pick in picks:
        image = overrides.get(pick["url"], pick["image"])
        rendered.append((pick["url"], pick["title"], image))
        if not image or BLOCKED_IMAGE_RE.search(image):
            errors.append(
                f"{pick['url']} uses blocked, placeholder, logo, text-card, or non-action image: {image}"
            )

    rendered_counts = Counter(image for _, _, image in rendered)
    for image, count in rendered_counts.items():
        if count > 1:
            urls = ", ".join(url for url, _, rendered_image in rendered if rendered_image == image)
            errors.append(f"Rendered homepage pick image repeats {count} times: {image} ({urls})")

    date_counts = Counter(pick["date"] for pick in picks)
    for date, count in date_counts.items():
        if count > MAX_CARDS_PER_DATE:
            errors.append(
                f"Homepage feed has {count} cards dated {date}; maximum allowed is {MAX_CARDS_PER_DATE}."
            )

    parsed_dates = [parse_date(pick["date"]) for pick in picks]
    for index in range(1, len(parsed_dates)):
        if parsed_dates[index] > parsed_dates[index - 1]:
            errors.append(
                "Homepage feed is out of sequence: "
                f"{picks[index - 1]['date']} appears before newer {picks[index]['date']} "
                f"at {picks[index]['url']}"
            )

    if parsed_dates:
        latest = parsed_dates[0]
        required_dates = {latest - timedelta(days=offset) for offset in range(RECENT_CONTIGUOUS_DAYS)}
        present_dates = set(parsed_dates)
        missing_recent = sorted(required_dates - present_dates, reverse=True)
        if missing_recent:
            missing = ", ".join(date.isoformat() for date in missing_recent)
            errors.append(
                f"Homepage feed has recent date gaps inside the required {RECENT_CONTIGUOUS_DAYS}-day window: {missing}"
            )

    if errors:
        print("Homepage pick image/feed validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print(
        "Homepage pick image/feed validation passed: "
        f"{len(picks)} cards, {len(rendered_counts)} unique images, "
        f"max {MAX_CARDS_PER_DATE} cards/date, no recent gaps."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
