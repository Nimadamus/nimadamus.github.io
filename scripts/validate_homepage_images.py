#!/usr/bin/env python3
"""Validate homepage preview images before publishing.

The homepage image policy is intentionally strict:
- pick archive cards must use the approved per-card image from homepage-image-audit.json
- static homepage cards must use approved homepage-preview assets
- bad legacy sources must not appear in homepage rendering files
- visible archive pages must not reuse the same image for unrelated cards
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - local dev may not have pillow
    Image = None

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PICKS = ROOT / "homepage-picks-data.js"
SYSTEM = ROOT / "homepage-image-system.js"
AUDIT = ROOT / "homepage-image-audit.json"
MAPLE_LEAFS_PAGE = ROOT / "maple-leafs-plus-1-5-puck-line-battle-of-ontario-senators-nhl.html"

COMPACT_PER_PAGE = 8

BLOCKED_REFS = [
    "images/allstars.png",
    "images/warriors-kings-kuminga-over-nov5-2025.png",
    "images/proof-bet-screenshot-1000079685.jpg",
    "images/proof-bet-screenshot-1000079686.jpg",
    "images/betting-strategy-arbitrage-betting-chart.png",
    "images/steph-curry-hero.png",
    "images/utah-hockey-club-san-jose-sharks-nhl-betting-pick-prediction-november-18-2025.png",
    "images/sharks-mammoth-nhl-picks-december-1-2025.png",
    "nddutvzzhwrmdkiociq4.jpg",
    "aryux4ugjbkoycl7bzth.jpg",
]

REQUIRED_STATIC_IMAGES = {
    "Bayern Munich vs Real Madrid Champions League preview": "images/homepage-preview/bayern-real-madrid-ucl-preview.png",
    "NBA Play-In elimination pressure preview": "images/homepage-preview/nba-play-in-elimination-pressure.png",
    "MLB daily preview hub": "images/homepage-preview/mlb-daily-preview-hub.png",
    "NBA Play-In Tournament preview": "images/homepage-preview/nba-play-in-full-preview.png",
    "2026 FIFA World Cup betting guide": "images/homepage-preview/world-cup-betting-guide.png",
    "Sports handicapping research dashboard": "images/homepage-preview/handicapping-hub-guide.png",
    "Live daily picks board": "images/homepage-preview/best-bets-today.png",
    "Sports betting pick archive": "images/homepage-preview/pick-archive.png",
    "Moneyline parlay betting card": "images/homepage-preview/moneyline-parlay.png",
    "Pro betting tools and model dashboard": "images/homepage-preview/pro-tools-dashboard.png",
    "NHL betting preview": "images/homepage-preview/nhl-preview-hub.png",
    "NFL betting preview": "images/homepage-preview/nfl-picks-hub.png",
    "Soccer betting board": "images/homepage-preview/soccer-board.png",
    "Betting calculator tools": "images/homepage-preview/betting-tools.png",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def is_homepage_preview(src: str) -> bool:
    return bool(re.fullmatch(r"images/homepage-preview/[a-z0-9][a-z0-9-]*\.(png|jpe?g|webp)", src, re.I))


def image_exists(src: str) -> bool:
    return (ROOT / src).exists()


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


def validate_no_blocked_refs(errors: list[str]) -> None:
    for path in (INDEX, PICKS, SYSTEM):
        text = path.read_text(encoding="utf-8")
        for ref in BLOCKED_REFS:
            if ref in text:
                fail(f"{path.name} still contains blocked image/reference: {ref}", errors)


def validate_pick_archive(errors: list[str]) -> None:
    manifest = json.loads(AUDIT.read_text(encoding="utf-8"))
    approved_by_url = {item["url"]: item for item in manifest["picks"]}
    picks = parse_pick_objects()
    if not picks:
        fail("No HOMEPAGE_PICKS entries found.", errors)
        return

    if len(picks) != len(approved_by_url):
        fail(f"Pick count mismatch: data has {len(picks)}, audit has {len(approved_by_url)}.", errors)

    for pick in picks:
        label = f"{pick['sport']} | {pick['title']}"
        approved = approved_by_url.get(pick["url"])
        if not approved:
            fail(f"{label}: missing approved image manifest entry for {pick['url']}", errors)
            continue
        if pick["title"] != approved["title"] or pick["sport"] != approved["sport"]:
            fail(f"{label}: title/sport does not match approved manifest entry.", errors)
        if pick["image"] != approved["image"]:
            fail(f"{label}: image must be approved per-card asset {approved['image']}, got {pick['image']}", errors)
        if not is_homepage_preview(pick["image"]):
            fail(f"{label}: image must live under images/homepage-preview/: {pick['image']}", errors)
        elif not image_exists(pick["image"]):
            fail(f"{label}: image file does not exist: {pick['image']}", errors)

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


def validate_static_homepage_cards(errors: list[str]) -> None:
    html = INDEX.read_text(encoding="utf-8")
    for alt, src in REQUIRED_STATIC_IMAGES.items():
        pattern = re.compile(rf"<img[^>]+src=\"{re.escape(src)}\"[^>]+alt=\"{re.escape(alt)}\"", re.I)
        if not pattern.search(html):
            fail(f"Homepage static card missing approved image/alt pair: {alt} -> {src}", errors)
        if not image_exists(src):
            fail(f"Homepage static approved image file missing: {src}", errors)

    main_html = html.split("<script src=\"homepage-picks-data.js\">", 1)[0]
    image_pattern = re.compile(r"<img\b[^>]*\bsrc=\"(?P<src>images/[^\"]+)\"[^>]*\balt=\"(?P<alt>[^\"]*)\"", re.I)
    seen: dict[str, str] = {}
    for match in image_pattern.finditer(main_html):
        src = match.group("src")
        alt = match.group("alt")
        if src == "newlogo.png":
            continue
        if not image_exists(src):
            fail(f"Homepage static card image missing: {src}", errors)
        if src in seen:
            fail(f"Homepage static card duplicate image {src}: '{seen[src]}' and '{alt}'", errors)
        seen[src] = alt


def validate_image_dimensions(errors: list[str]) -> None:
    if Image is None:
        return
    manifest = json.loads(AUDIT.read_text(encoding="utf-8"))
    images = set(manifest["static"].values())
    images.update(item["image"] for item in manifest["picks"])
    for src in sorted(images):
        path = ROOT / src
        if not path.exists():
            continue
        with Image.open(path) as image:
            if image.size != (1200, 675):
                fail(f"{src}: expected 1200x675 approved thumbnail, got {image.size[0]}x{image.size[1]}", errors)


def validate_article_images(errors: list[str]) -> None:
    html = MAPLE_LEAFS_PAGE.read_text(encoding="utf-8")
    if "nddutvzzhwrmdkiociq4.jpg" in html:
        fail("Maple Leafs page still contains the bad remote NHL image URL.", errors)
    if "images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg" not in html:
        fail("Maple Leafs page is missing the local Maple Leafs hockey image.", errors)


def main() -> int:
    errors: list[str] = []
    validate_no_blocked_refs(errors)
    validate_pick_archive(errors)
    validate_static_homepage_cards(errors)
    validate_image_dimensions(errors)
    validate_article_images(errors)

    if errors:
        print("Homepage image validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Homepage image validation passed.")
    print("Checked approved static cards, approved pick-card mapping, visible-page duplicate images, blocked legacy refs, local files, and thumbnail dimensions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
