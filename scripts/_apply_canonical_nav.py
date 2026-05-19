"""Apply the canonical BetLegend nav + calendar layout to a list of HTML pages.

Reads the canonical nav CSS block + the <header class="nav">...</header> block
from a known-good source page and injects them into each target page.

For pages that still use the grid-based `.page-wrapper{display:grid;...}`
calendar layout, also rewrites that block to the position:fixed style used by
all other SLATE/preview pages.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SOURCE = REPO / "cavaliers-pistons-game-7-eastern-semis-nba-may-17-2026.html"

TARGETS = [
    "featured-game-of-the-day.html",
    "cavaliers-vs-knicks-eastern-conference-finals-game-1-analysis-stats-preview-may-19-2026.html",
    "knicks-host-cavaliers-eastern-conference-finals-game-1-brunson-mitchell-nba-may-19-2026.html",
    "yankees-blue-jays-dodgers-padres-brewers-cubs-fifteen-game-tuesday-mlb-may-19-2026.html",
    "europa-league-final-eve-aston-villa-freiburg-istanbul-soccer-may-19-2026.html",
    "mlb-previews.html",
    "nba-previews.html",
    "soccer-previews.html",
]


def extract(src: str, start_marker: str, end_marker: str) -> str:
    si = src.index(start_marker)
    ei = src.index(end_marker, si) + len(end_marker)
    return src[si:ei]


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")

    nav_style = extract(
        source,
        '<style id="betlegend-homepage-nav">',
        "</style>",
    )
    nav_block = extract(source, "<header class=\"nav\">", "</header>")

    fixed_calendar_css = (
        ".page-wrapper{box-sizing:border-box;max-width:900px;margin:0 auto;padding:0 24px 80px}"
        "@media(min-width:1201px){"
        ".hero{width:calc(100% - 340px);margin-left:320px;margin-right:20px;padding-left:40px;padding-right:40px}"
        ".page-wrapper{width:calc(100% - 340px);max-width:none;margin-left:320px;margin-right:20px;padding-left:40px;padding-right:40px}"
        ".main-content{max-width:900px;margin:0 auto}}"
        ".calendar-sidebar{position:fixed;left:20px;top:120px;width:280px;z-index:100}"
        "@media(max-width:1200px){.calendar-sidebar{display:none}}"
        ".mobile-archive{display:none;background:#12151c;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px 20px;margin-bottom:32px}"
        ".mobile-archive-title{font-family:Orbitron,sans-serif;font-size:14px;color:#fd5000;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}"
        ".mobile-archive-select{width:100%;background:#181c25;color:#fff;border:1px solid rgba(255,255,255,0.08);padding:12px 16px;font-size:14px;border-radius:8px}"
        "@media(max-width:1200px){.mobile-archive{display:block}}"
    )

    grid_layout_re = re.compile(
        r"\.page-wrapper\{display:grid;[^}]*\}\.main-content\{min-width:0\}@media\(max-width:950px\)\{\.page-wrapper\{display:block\}\}"
    )

    for name in TARGETS:
        path = REPO / name
        if not path.exists():
            print(f"  SKIP {name} (not found)")
            continue
        html = path.read_text(encoding="utf-8")

        if "<style id=\"betlegend-homepage-nav\">" in html:
            html = re.sub(
                r'<style id="betlegend-homepage-nav">.*?</style>',
                nav_style,
                html,
                count=1,
                flags=re.DOTALL,
            )
        else:
            html = re.sub(r"</head>", nav_style + "\n</head>", html, count=1)

        new_html, count = re.subn(
            r'<(?:header|nav)\b[^>]*class="nav"[^>]*>.*?</(?:header|nav)>',
            nav_block,
            html,
            count=1,
            flags=re.DOTALL,
        )
        if count == 0:
            new_html, count = re.subn(
                r'<nav class="nav">.*?</nav>',
                nav_block,
                html,
                count=1,
                flags=re.DOTALL,
            )
        if count == 0:
            print(f"  WARN {name}: nav block not matched, header injected at top of <body>")
            new_html = re.sub(r"<body[^>]*>", lambda m: m.group(0) + "\n" + nav_block, html, count=1)
        html = new_html

        if grid_layout_re.search(html):
            html = grid_layout_re.sub(fixed_calendar_css, html, count=1)

        path.write_text(html, encoding="utf-8")
        print(f"  OK   {name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
