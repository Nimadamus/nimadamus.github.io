#!/usr/bin/env python3
"""Hard-block pick card image validator.

Purpose:
  Every pick card on the BetLegend homepage (top 12 visible entries of
  homepage-picks-data.js) must use a real centered action photo. This script
  BLOCKS the commit when a pick image looks like a post-game graphic
  template ("AT THE HORN", "FINAL SCORE", "POSTGAME REPORT") or comes from a
  non-allowlisted random CDN URL.

Rules enforced:
  1. URL must match an allow-list:
       - images/<slug>.{jpg,jpeg,png,webp}   (self-hosted, preferred)
       - img.mlbstatic.com/.../people/<id>/action/hero/current
       - a.espncdn.com/photo/... (ESPN photo CDN)
     Raw NHL/MLB/random CDN URLs (e.g. media.d3.nhle.com/image/private/...)
     are BLOCKED. Graphic templates hide inside those URLs. Self-host
     instead so you must actually look at the file before committing.
  2. Download each image and run a visual graphic-template detector.
     Blocks when:
       - high_saturation_ratio > 0.55, OR
       - top1_color_ratio > 0.20 combined with top3_color_ratio > 0.35
         (large flat-color banners typical of template chrome)
  3. The top 3 featured card images must not share the same image.

Exit 0 on pass, 1 on fail. Prints each rejected pick with the reason.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PICKS_FILE = ROOT / "homepage-picks-data.js"
PICKS_FILENAME = "homepage-picks-data.js"

VISIBLE_PICK_COUNT = 12
HIGH_SAT_LIMIT = 0.55
TOP1_COLOR_LIMIT = 0.55
TOP3_COLOR_LIMIT = 0.70

LOCAL_IMAGE_RE = re.compile(r"^images/[a-z0-9][a-z0-9_\-/.]*\.(jpg|jpeg|png|webp)$", re.I)
ALLOWED_REMOTE_PATTERNS = [
    re.compile(r"^https://img\.mlbstatic\.com/mlb-photos/image/upload/[^\s]+/people/\d+/action/hero/current$"),
    re.compile(r"^https://a\.espncdn\.com/photo/[^\s]+\.(?:jpg|jpeg|png|webp)$", re.I),
]

def parse_picks():
    text = PICKS_FILE.read_text(encoding="utf-8")
    object_re = re.compile(r"\{(?P<body>.*?)\}", re.S)
    field_re = re.compile(r"(?P<k>sport|title|date|result|url|image):\s*\"(?P<v>[^\"]*)\"")
    out = []
    for m in object_re.finditer(text):
        body = m.group("body")
        fields = {fm.group("k"): fm.group("v") for fm in field_re.finditer(body)}
        if {"sport", "title", "url", "image"}.issubset(fields):
            out.append(fields)
    return out

def url_allowed(src: str) -> tuple[bool, str]:
    if LOCAL_IMAGE_RE.match(src):
        full = ROOT / src
        if not full.exists():
            return False, f"local image file missing: {src}"
        return True, "local"
    for pat in ALLOWED_REMOTE_PATTERNS:
        if pat.match(src):
            return True, "allowlisted-remote"
    return False, (
        f"image URL is not allowlisted: {src!r}. "
        "Pick card images must be self-hosted under images/<slug>.{jpg,jpeg,png,webp}, "
        "or one of the approved APIs (img.mlbstatic.com /people/<id>/action/hero/current, a.espncdn.com/photo/...). "
        "Raw CDN URLs often resolve to post-game graphics ('AT THE HORN', 'POSTGAME REPORT', score templates) "
        "and are banned."
    )

def load_image_bytes(src: str) -> bytes | None:
    if src.startswith("images/"):
        return (ROOT / src).read_bytes()
    try:
        req = urllib.request.Request(
            src,
            headers={
                "User-Agent": "Mozilla/5.0 (BetLegend PickImageValidator)",
                "Accept": "image/*",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read()
    except Exception as e:
        print(f"  [warn] could not download {src}: {e}", file=sys.stderr)
        return None

def visual_checks(data: bytes):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    img = cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA)

    quant = (img // 8).astype(np.int32)
    keys = quant[:, :, 0] * 1024 + quant[:, :, 1] * 32 + quant[:, :, 2]
    _, counts = np.unique(keys.ravel(), return_counts=True)
    counts = np.sort(counts)[::-1]
    total = counts.sum()
    top1 = counts[0] / total
    top3 = counts[:3].sum() / total

    sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[:, :, 1]
    high_sat = (sat > 180).mean()

    return {
        "top1_color_ratio": float(top1),
        "top3_color_ratio": float(top3),
        "high_saturation_ratio": float(high_sat),
    }

def image_fails_visual(stats: dict) -> str | None:
    if stats is None:
        return None
    if stats["high_saturation_ratio"] > HIGH_SAT_LIMIT:
        return (
            f"visual signature matches a graphic/template "
            f"(high_saturation_ratio={stats['high_saturation_ratio']:.2f}, limit={HIGH_SAT_LIMIT}). "
            "Images with this much oversaturated flat color are almost always NHL/MLB post-game "
            "templates ('AT THE HORN', 'POSTGAME REPORT', score graphics). Use a real centered action photo."
        )
    if stats["top1_color_ratio"] > TOP1_COLOR_LIMIT and stats["top3_color_ratio"] > TOP3_COLOR_LIMIT:
        return (
            f"visual signature shows large flat-color banner regions "
            f"(top1={stats['top1_color_ratio']:.2f}, top3={stats['top3_color_ratio']:.2f}). "
            "Real action photos rarely have a single dominant flat color. Likely a template/chrome overlay."
        )
    return None

def get_new_image_srcs_from_staged_diff() -> set[str] | None:
    """Return the set of image URLs appearing on + lines in the staged diff
    of homepage-picks-data.js, or None if git is unavailable/no diff.

    Grandfathers already-committed entries. New or modified entries have their
    image URL on a + line and will be strictly URL-checked.
    """
    try:
        out = subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "--cached", "--unified=0", "--", PICKS_FILENAME],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8", "replace")
    except Exception:
        return None
    if not out.strip():
        return set()
    added = set()
    field_re = re.compile(r'image:\s*"([^"]+)"')
    for line in out.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = field_re.search(line)
        if m:
            added.add(m.group(1))
    return added

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=["all", "new-only"],
        default="new-only",
        help="all = strict URL-allowlist on every top-12 pick (manual audit). "
             "new-only = strict URL check only on entries new/modified in the staged diff "
             "(historical cards are grandfathered). Visual check always runs on all top 12.",
    )
    args = ap.parse_args()

    picks = parse_picks()
    if not picks:
        print("[validate_pick_card_images] no picks found in homepage-picks-data.js")
        return 1

    visible = picks[:VISIBLE_PICK_COUNT]
    errors: list[str] = []

    new_srcs: set[str] | None = None
    if args.mode == "new-only":
        new_srcs = get_new_image_srcs_from_staged_diff()
        if new_srcs is None:
            new_srcs = set()

    seen_top3 = {}
    for idx, pick in enumerate(visible):
        label = f"[{idx+1}] {pick['sport']} | {pick['title']}"
        src = pick["image"]

        should_url_check = (args.mode == "all") or (new_srcs is not None and src in new_srcs)
        if should_url_check:
            ok, reason = url_allowed(src)
            if not ok:
                errors.append(f"{label}\n    URL-RULE: {reason}")
                continue

        if idx < 3:
            if src in seen_top3:
                errors.append(
                    f"{label}\n    DUPLICATE-IMAGE: top 3 featured cards cannot share the same image "
                    f"(also used by '{seen_top3[src]}')"
                )
            else:
                seen_top3[src] = pick["title"]

        data = load_image_bytes(src)
        if data is None:
            if should_url_check:
                errors.append(
                    f"{label}\n    DOWNLOAD-FAIL: could not load {src}. "
                    "Cannot run visual check on a new/modified entry — fix the URL or self-host."
                )
            continue

        stats = visual_checks(data)
        bad = image_fails_visual(stats)
        if bad:
            errors.append(f"{label}\n    VISUAL-RULE: {bad}\n    image: {src}")

    if errors:
        print("=" * 70)
        print("PICK CARD IMAGE VALIDATION FAILED")
        print("=" * 70)
        print(f"\n{len(errors)} problem(s) in the top {VISIBLE_PICK_COUNT} visible pick cards:\n")
        for e in errors:
            print(f"  * {e}\n")
        print("Fix every issue above before committing. No exceptions, no escape hatch.")
        print("Self-host pick images under images/<slug>.jpg and verify they are centered action photos.")
        return 1

    print(f"[validate_pick_card_images] OK - checked top {len(visible)} pick card images.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
