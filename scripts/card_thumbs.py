#!/usr/bin/env python3
"""Small WebP thumbnails for homepage cards (Oct 1 2026 performance fix).

Homepage "Latest Analysis" cards render at about 352 to 406 px wide but used
the full 1280 to 1920 px article JPGs (250 to 700 KB each), which pushed the
homepage to 4 MB and a 15 s mobile LCP. card_thumb() returns an 800 px wide
WebP copy under images/thumbs/ (2x the largest card width), creating it once
if Pillow is available. The original image is never modified, so article
pages, og:image and schema keep using the full size file.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THUMB_DIR = os.path.join("images", "thumbs")
THUMB_W = 800


def card_thumb(src, width=THUMB_W, quality=72):
    """Return (path, w, h) for a card thumbnail, or (src, None, None) if it
    cannot be made (remote URL, missing file, no Pillow)."""
    if not src or src.startswith(("http://", "https://", "data:")):
        return src, None, None
    rel = src.lstrip("/")
    full = os.path.join(ROOT, rel)
    if not os.path.isfile(full):
        return src, None, None
    stem = os.path.splitext(os.path.basename(rel))[0]
    out_rel = f"{THUMB_DIR}/{stem}-{width}.webp".replace(os.sep, "/")
    out_full = os.path.join(ROOT, out_rel)
    try:
        from PIL import Image
    except ImportError:
        return src, None, None
    try:
        if not os.path.isfile(out_full) or os.path.getmtime(out_full) < os.path.getmtime(full):
            os.makedirs(os.path.dirname(out_full), exist_ok=True)
            with Image.open(full) as im:
                im = im.convert("RGB")
                if im.width > width:
                    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
                im.save(out_full, "WEBP", quality=quality, method=6)
        with Image.open(out_full) as im:
            return out_rel, im.width, im.height
    except Exception:
        return src, None, None
