#!/usr/bin/env python3
"""
Sitewide image-centering normalizer.

Goal: every cropped image (object-fit:cover) gets a face-safe object-position so
faces/players/logos are not awkwardly cut; logos stay object-fit:contain (no crop).

Canonical standard (matches pick-hero.css): object-fit:cover + object-position:center 20%
(top-biased center keeps heads/faces in frame for action photos).

What it does (idempotent):
  - For every CSS declaration block ({...}) in repo *.html + the shared CSS files
    that contains 'object-fit:cover' but NO 'object-position', insert
    'object-position:center 20%' right after the object-fit:cover declaration.
  - Leaves object-fit:contain (logos) untouched.

Modes:
  --audit  : report files + how many cover-without-position rules each has (no writes)
  --apply  : perform the insert and report what changed
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STANDARD = "object-position:center 20%"

# shared CSS that many pages link
CSS_FILES = ["mobile-optimize.css", "pick-hero.css"]

BLOCK_RE = re.compile(r"\{[^{}]*\}")
COVER_RE = re.compile(r"(object-fit\s*:\s*cover)")


def targets():
    files = sorted(REPO.glob("*.html"))
    files += [REPO / c for c in CSS_FILES if (REPO / c).exists()]
    return files


def fix_text(text: str):
    """Return (new_text, n_rules_fixed)."""
    count = 0

    def repl(m):
        nonlocal count
        blk = m.group(0)
        if "object-fit:cover" in blk.replace(" ", "") and "object-position" not in blk:
            count += 1
            # insert standard right after the cover declaration
            return COVER_RE.sub(r"\1;" + STANDARD, blk, count=1)
        return blk

    new = BLOCK_RE.sub(repl, text)
    return new, count


def main() -> int:
    apply = "--apply" in sys.argv
    total_files = 0
    total_rules = 0
    changed = []
    for f in targets():
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  skip {f.name}: {e}")
            continue
        # normalize: count cover-without-position blocks
        new, n = fix_text(text)
        if n:
            total_files += 1
            total_rules += n
            changed.append((f.relative_to(REPO).as_posix(), n))
            if apply and new != text:
                f.write_text(new, encoding="utf-8")
    verb = "FIXED" if apply else "WOULD FIX"
    for rel, n in changed:
        print(f"  {n}\t{rel}")
    print(f"[{verb}] {total_rules} cover-without-position rule(s) across {total_files} file(s); "
          f"standard = '{STANDARD}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
