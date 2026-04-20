#!/usr/bin/env python3
"""
Rewrite the "Game Previews" nav dropdown on every HTML page so each sport
points to its preview hub instead of a dated standalone page.

Dated links (e.g. tatum-returns-sixers-celtics-nba-april-19-2026.html) rot
the moment tomorrow's SLATE runs - users clicking Game Previews -> NBA from
any old page land on yesterday's content. Preview hubs always show today.

Mapping:
  NBA    -> nba-previews.html
  NHL    -> nhl-previews.html
  NCAAB  -> college-basketball-previews.html
  MLB    -> mlb-previews.html
  Soccer -> soccer-previews.html
  NFL    -> nfl.html (no hub exists)
  NCAAF  -> ncaaf.html (no hub exists)
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

HUB_MAP = {
    "NBA": "nba-previews.html",
    "NHL": "nhl-previews.html",
    "NCAAB": "college-basketball-previews.html",
    "MLB": "mlb-previews.html",
    "Soccer": "soccer-previews.html",
    "NFL": "nfl.html",
    "NCAAF": "ncaaf.html",
}

# Match <a href="ANYTHING">LABEL</a> where LABEL is one of our sport labels.
# We only rewrite the link if its href doesn't already equal the hub target
# AND we only do the rewrite inside Game Previews dropdowns to avoid touching
# contextual links in article bodies.
DROPDOWN_RE = re.compile(
    r'(Game Previews\s*</button>\s*<div class="dropdown-content">)(.*?)(</div>\s*</div>)',
    re.DOTALL | re.IGNORECASE,
)
LINK_RE = re.compile(r'<a\s+href="([^"]+)">([^<]+)</a>')


def rewrite_dropdown(match):
    prefix, inner, suffix = match.group(1), match.group(2), match.group(3)

    def replace_link(link_match):
        href, label = link_match.group(1), link_match.group(2).strip()
        target = HUB_MAP.get(label)
        if target and href != target:
            return f'<a href="{target}">{label}</a>'
        return link_match.group(0)

    new_inner = LINK_RE.sub(replace_link, inner)
    return prefix + new_inner + suffix


def process_file(path: Path):
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return 0

    if "Game Previews" not in content:
        return 0

    new_content, n = DROPDOWN_RE.subn(rewrite_dropdown, content)
    if new_content != content:
        path.write_text(new_content, encoding="utf-8")
        return 1
    return 0


def main():
    fixed = 0
    scanned = 0
    for path in REPO.glob("*.html"):
        scanned += 1
        fixed += process_file(path)
    print(f"Scanned {scanned} HTML files, updated {fixed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
