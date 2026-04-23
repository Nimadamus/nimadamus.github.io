"""Repoint every 'News' nav link to the Garret Anderson tribute page.
Catches any anchor whose visible text is exactly 'News' and whose href
matches one of the legacy targets, regardless of attribute order or
relative-path depth ('../' / '/' / bare)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_BASENAME = "garret-anderson-angels-legend-dies-53-pancreatitis-tribute-news.html"
SKIP_NAMES = {NEW_BASENAME}

OLD_BASENAMES = (
    "nba-play-in-tournament-2026-full-preview-matchups-analysis.html",
    "news.html",
)
# Build alternation that matches optional leading prefixes like ../ ../../ /
PREFIX = r"(?:\.\./)*/?"
OLD_RE = "|".join(re.escape(b) for b in OLD_BASENAMES)

# Match a full <a ...>News</a> tag where href is one of the old targets
ANCHOR_RE = re.compile(
    r"""
    (<a\b[^>]*\bhref=")     # opening + href="
    """ + PREFIX + r"(?:" + OLD_RE + r")" + r"""
    ("[^>]*>\s*News\s*</a>)
    """,
    re.IGNORECASE | re.VERBOSE,
)

def relative_target(html_path: Path) -> str:
    """Return the path from html_path's directory to NEW_BASENAME at repo root."""
    rel = Path("/".join([".."] * (len(html_path.relative_to(ROOT).parts) - 1)))
    if str(rel) == ".":
        return NEW_BASENAME
    return f"{rel.as_posix()}/{NEW_BASENAME}"

changed = []
scanned = 0
for path in ROOT.rglob("*.html"):
    if path.name in SKIP_NAMES:
        continue
    # skip vendor / archives we shouldn't touch
    rel_parts = path.relative_to(ROOT).parts
    if rel_parts and rel_parts[0] in {".git", "node_modules"}:
        continue
    scanned += 1
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        continue

    new_target = relative_target(path)
    new_text, n = ANCHOR_RE.subn(rf"\g<1>{new_target}\g<2>", text)
    if n and new_text != text:
        path.write_text(new_text, encoding="utf-8")
        changed.append((path.name, n))

print(f"Scanned: {scanned} files")
print(f"Updated: {len(changed)} files")
for name, n in changed[:25]:
    print(f"  {name}  (x{n})")
if len(changed) > 25:
    print(f"  ... and {len(changed)-25} more")
