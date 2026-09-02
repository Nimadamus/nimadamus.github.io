#!/usr/bin/env python3
"""
Fix body off-center on desktop for pages that already shift their hero/header
right to clear the fixed calendar sidebar.

Root cause: commit 95243e46f added
  @media(min-width:1201px){.header-section{padding-left:320px;padding-right:40px}}
to 82 Featured Game / pick pages, and the same for .hero on daily sport pages.
That fixed the title clipping, but the body container (.content-wrapper or
.page-wrapper) was never included, so the title sits to the right of the
sidebar while the body stays centered on the full viewport -> visually
off-center.

Fix: extend each media query to also cover the body container.
  .header-section variant -> add .content-wrapper
  .hero variant          -> add .page-wrapper
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

REPLACEMENTS = [
    # Pattern A: Featured Game + standalone pick pages
    (
        "@media(min-width:1201px){.header-section{padding-left:320px;padding-right:40px}}",
        "@media(min-width:1201px){.header-section,.content-wrapper{padding-left:320px;padding-right:40px}}",
    ),
    # Pattern B: Daily sport pages (NBA/NHL/MLB/Soccer daily standalones)
    (
        "@media(min-width:1201px){.hero{padding-left:320px;padding-right:40px}}",
        "@media(min-width:1201px){.hero,.page-wrapper{padding-left:320px;padding-right:40px}}",
    ),
]


def process(path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return False
    new_content = content
    for old, new in REPLACEMENTS:
        if old in new_content:
            new_content = new_content.replace(old, new)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    fixed = 0
    for p in REPO.glob("*.html"):
        if process(p):
            fixed += 1
    print(f"Updated {fixed} pages")


if __name__ == "__main__":
    sys.exit(main())
