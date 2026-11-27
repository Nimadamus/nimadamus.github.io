"""Fail when a BetLegend meta description decodes longer than 160 characters."""
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
META = re.compile(r"<meta\b[^>]*>", re.I | re.S)
KIND = re.compile(
    r"""\bname\s*=\s*(['"])description\1""",
    re.I,
)
CONTENT = re.compile(r"""\bcontent\s*=\s*(['"])(.*?)\1""", re.I | re.S)
bad = []
for path in ROOT.rglob("*.html"):
    if any(part.startswith(".") for part in path.parts):
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    for tag in META.findall(text):
        if not KIND.search(tag):
            continue
        content = CONTENT.search(tag)
        if not content:
            continue
        desc = re.sub(r"\s+", " ", html.unescape(content.group(2))).strip()
        if len(desc) > 160:
            bad.append(f"{len(desc)} {path.relative_to(ROOT)}")
if bad:
    print(f"{len(bad)} meta descriptions over 160")
    print("\n".join(bad[:20]))
    sys.exit(1)
print("ok, no meta description over 160")
