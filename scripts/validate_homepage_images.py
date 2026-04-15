#!/usr/bin/env python3
"""Validate homepage card images before publishing.

This intentionally checks the rendered-card inputs, not every image on the site:
- homepage static cards in index.html
- homepage pick archive data in homepage-picks-data.js
- the Maple Leafs article image that previously used a bad remote asset
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PICKS = ROOT / "homepage-picks-data.js"
MAPLE_LEAFS_PAGE = ROOT / "maple-leafs-plus-1-5-puck-line-battle-of-ontario-senators-nhl.html"

COMPACT_PER_PAGE = 8
STATIC_BAD_IMAGES = {
    "images/betting-strategy-arbitrage-betting-chart.png": "Only arbitrage-specific content may use the arbitrage chart.",
    "images/steph-curry-hero.png": "Homepage should not reuse the Curry hero as a generic NBA card.",
}

SPORT_IMAGE_PATTERNS = {
    "NHL": re.compile(
        r"nhl|hockey|leafs|senators|kraken|knights|mammoth|bruins|islanders|stars|oilers|wild|blues|ducks|blackhawks|devils|kings|canadiens|penguins|sharks|flames|avalanche",
        re.I,
    ),
    "MLB": re.compile(
        r"mlb|baseball|yankees|dodgers|rangers|athletics|giants|braves|mariners|red-sox|brewers|cubs|guardians|coors|playoffs",
        re.I,
    ),
    "NBA": re.compile(
        r"nba|basketball|warriors|kings|thunder|pistons|nets|draymond|allstars|sac",
        re.I,
    ),
    "NCAAB": re.compile(r"collegeban|ncaa|ncaab|kansas-state", re.I),
    "NCAAF": re.compile(r"ncaaf|college|football|penn-state|vanderbilt", re.I),
    "Soccer": re.compile(r"soccer|fifa|ucl", re.I),
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def is_local_image(src: str) -> bool:
    return bool(re.fullmatch(r"images/[^?#]+\.(png|jpe?g|webp|gif)", src, re.I))


def image_exists(src: str) -> bool:
    return (ROOT / src).exists()


def sport_matches(sport: str, src: str) -> bool:
    pattern = SPORT_IMAGE_PATTERNS.get(sport)
    if not pattern:
        return True
    return bool(pattern.search(src))


def parse_pick_objects() -> list[dict[str, str]]:
    text = PICKS.read_text(encoding="utf-8")
    object_pattern = re.compile(r"\{(?P<body>.*?)\}", re.S)
    field_pattern = re.compile(r"(?P<key>sport|title|date|result|url|image):\s*\"(?P<value>[^\"]*)\"")
    picks: list[dict[str, str]] = []
    for match in object_pattern.finditer(text):
        body = match.group("body")
        fields = {field.group("key"): field.group("value") for field in field_pattern.finditer(body)}
        if {"sport", "title", "url", "image"}.issubset(fields):
            picks.append(fields)
    return picks


def validate_pick_archive(errors: list[str]) -> None:
    picks = parse_pick_objects()
    if not picks:
        fail("No HOMEPAGE_PICKS entries found.", errors)
        return

    for pick in picks:
        image = pick["image"]
        label = f"{pick['sport']} | {pick['title']}"
        if not is_local_image(image):
            fail(f"{label}: image must be a local images/ asset, got {image}", errors)
        elif not image_exists(image):
            fail(f"{label}: image file does not exist: {image}", errors)
        elif not sport_matches(pick["sport"], image):
            fail(f"{label}: image appears mismatched for sport/category: {image}", errors)

    featured = picks[:3]
    compact = picks[3:]
    pages = [featured + compact[i : i + COMPACT_PER_PAGE] for i in range(0, len(compact), COMPACT_PER_PAGE)]
    for page_index, page in enumerate(pages, start=1):
        seen: dict[str, str] = {}
        for pick in page:
            image = pick["image"]
            if image in seen:
                fail(
                    f"Visible homepage archive page {page_index}: duplicate image {image} used by "
                    f"'{seen[image]}' and '{pick['title']}'",
                    errors,
                )
            seen[image] = pick["title"]


def static_homepage_cards(errors: list[str]) -> None:
    html = INDEX.read_text(encoding="utf-8")
    main_html = html.split("<script src=\"homepage-picks-data.js\">", 1)[0]
    image_pattern = re.compile(r"<img\b[^>]*\bsrc=\"(?P<src>images/[^\"]+)\"[^>]*\balt=\"(?P<alt>[^\"]*)\"", re.I)
    images = []
    for match in image_pattern.finditer(main_html):
        src = match.group("src")
        alt = match.group("alt")
        if src in {"newlogo.png"}:
            continue
        images.append((src, alt))

    seen: dict[str, str] = {}
    for src, alt in images:
        if not image_exists(src):
            fail(f"Homepage static card image missing: {src}", errors)
        if src in STATIC_BAD_IMAGES:
            fail(f"Homepage static card '{alt}' uses blocked image {src}: {STATIC_BAD_IMAGES[src]}", errors)
        if src in seen:
            fail(f"Homepage static card duplicate image {src}: '{seen[src]}' and '{alt}'", errors)
        seen[src] = alt

    handicapping_pattern = re.compile(
        r"href=\"sports-handicapping-hub-guide\.html\"[\s\S]{0,220}<img[^>]+src=\"([^\"]+)\"",
        re.I,
    )
    match = handicapping_pattern.search(html)
    if not match:
        fail("Could not find the Handicapping Hub homepage card image.", errors)
    elif "arbitrage" in match.group(1).lower():
        fail("Handicapping Hub card is still using an arbitrage image.", errors)


def validate_article_images(errors: list[str]) -> None:
    html = MAPLE_LEAFS_PAGE.read_text(encoding="utf-8")
    bad = "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/f_auto/prd/nddutvzzhwrmdkiociq4.jpg"
    if bad in html:
        fail("Maple Leafs page still contains the bad remote NHL image URL.", errors)
    if "images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg" not in html:
        fail("Maple Leafs page is missing the local Maple Leafs hockey image.", errors)


def main() -> int:
    errors: list[str] = []
    validate_pick_archive(errors)
    static_homepage_cards(errors)
    validate_article_images(errors)

    if errors:
        print("Homepage image validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Homepage image validation passed.")
    print("Checked: static homepage cards, pick archive visible pages, sport/category fit, local image existence, and known bad image regressions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
