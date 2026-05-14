#!/usr/bin/env python3
"""Validate that homepage pick cards cannot render duplicate preview images."""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PICKS = ROOT / "homepage-picks-data.js"
SYSTEM = ROOT / "homepage-image-system.js"

BLOCKED_RE = re.compile(
    r"(?:newlogo\.png|vegas-golden-knights-(?:premium-preview|moneyline-game-5-ducks-chart|ducks-game-5-action))",
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


def main() -> int:
    errors: list[str] = []
    picks = parse_picks()
    overrides = parse_overrides()
    if not picks:
        errors.append("homepage-picks-data.js has no pick cards.")

    override_counts = Counter(overrides.values())
    for image, count in override_counts.items():
        if count > 1:
            errors.append(f"PICK_IMAGE_OVERRIDES repeats {image} {count} times.")

    rendered: list[tuple[str, str, str]] = []
    for pick in picks:
        image = overrides.get(pick["url"], pick["image"])
        rendered.append((pick["url"], pick["title"], image))
        if not image or BLOCKED_RE.search(image):
            errors.append(f"{pick['url']} uses blocked or missing image: {image}")

    rendered_counts = Counter(image for _, _, image in rendered)
    for image, count in rendered_counts.items():
        if count > 1:
            urls = ", ".join(url for url, _, rendered_image in rendered if rendered_image == image)
            errors.append(f"Rendered homepage pick image repeats {count} times: {image} ({urls})")

    if errors:
        print("Homepage pick image uniqueness validation failed:")
        for error in errors:
            print(f" - {error}")
        return 1

    print(f"Homepage pick image uniqueness validation passed for {len(picks)} cards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
