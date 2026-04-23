"""One-shot: repoint the 'News' nav link from the NBA play-in page to the
Garret Anderson tribute page across the site. Only touches the explicit
News nav-link pattern, never other internal references to the NBA page."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_TARGET = "garret-anderson-angels-legend-dies-53-pancreatitis-tribute-news.html"
SKIP_NAMES = {NEW_TARGET}  # don't rewrite the new page's self-link

# Two ordering variants for the anchor attributes
PATTERNS = [
    # href first, then class
    (
        re.compile(
            r'(<a\s+href=")(?:nba-play-in-tournament-2026-full-preview-matchups-analysis\.html|news\.html)("\s+class="nav-link">\s*News\s*</a>)'
        ),
        rf"\g<1>{NEW_TARGET}\g<2>",
    ),
    # class first, then href
    (
        re.compile(
            r'(<a\s+class="nav-link"\s+href=")(?:nba-play-in-tournament-2026-full-preview-matchups-analysis\.html|news\.html)("\s*>\s*News\s*</a>)'
        ),
        rf"\g<1>{NEW_TARGET}\g<2>",
    ),
]

changed = []
scanned = 0
for path in ROOT.glob("*.html"):
    if path.name in SKIP_NAMES:
        continue
    scanned += 1
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        continue
    new_text = text
    for pat, repl in PATTERNS:
        new_text = pat.sub(repl, new_text)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        changed.append(path.name)

print(f"Scanned: {scanned} files")
print(f"Updated: {len(changed)} files")
for name in changed[:25]:
    print(" ", name)
if len(changed) > 25:
    print(f"  ... and {len(changed)-25} more")
