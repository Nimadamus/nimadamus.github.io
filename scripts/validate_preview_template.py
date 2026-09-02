"""HARD GATE: block any new preview/board/featured page that does not match
PREVIEW_PAGE_STANDARD.md (locked July 4, 2026).

Why this exists (July 5, 2026): the June-July daily automation quietly replaced
the locked game-preview format with bare text cards (no team logos, no game
headers) and nothing blocked it. The July 4 15-game MLB board shipped that way
and had to be rebuilt. The standard doc alone does not prevent drift; this
gate does.

Usage:
  python scripts/validate_preview_template.py <file> [...]   # explicit files
  python scripts/validate_preview_template.py --staged-added # git staged, added only
  python scripts/validate_preview_template.py --all          # audit whole root (report only)

Exit 1 if any checked ADDED/explicit file fails. --all never exits nonzero
(it is an audit, not a gate).
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOARD_SUFFIXES = (
    "-mlb.html", "-nhl.html", "-nba.html", "-nfl.html", "-ncaaf.html",
    "-soccer.html", "-college-basketball.html", "-ncaab.html",
)
FEATURED_SUFFIX = "-analysis-stats-preview.html"
REDIRECT_STUB = re.compile(r'http-equiv=["\']refresh', re.I)


def classify(fname):
    base = os.path.basename(fname)
    if "/" in fname.replace("\\", "/").strip("/"):
        # only root-level standalone pages are gated
        return None
    if base.endswith(FEATURED_SUFFIX):
        return "featured"
    if base.endswith(BOARD_SUFFIXES) and not base.endswith("-pick.html"):
        return "board"
    return None


def check(path, family):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
    except OSError as e:
        return [f"unreadable: {e}"]
    if REDIRECT_STUB.search(html[:2000]):
        return []  # redirect stub, not a content page

    problems = []
    n_games = len(re.findall(r'<article class="game-preview', html))
    n_logos = len(re.findall(r'class="team-logo"', html))

    if family == "board":
        if n_games < 1:
            problems.append("no <article class=\"game-preview\"> blocks (bare text-card format is BANNED)")
        elif n_logos != 2 * n_games:
            problems.append(f"team logos: found {n_logos}, expected {2 * n_games} (2 per game-preview article)")
    else:  # featured
        if n_games < 1 and "game-card" not in html:
            problems.append("no game-preview/game-card block")
        if n_logos < 2:
            problems.append(f"team logos: found {n_logos}, expected >= 2")

    if "toc-box" not in html:
        problems.append("missing toc-box (In This Preview / On Today's Board)")
    if not re.search(r'class="(slate-photo|hero-figure|feature-photo|pick-article-hero|hero-photo)', html):
        problems.append("missing hero action-photo figure")
    if "related-links" not in html:
        problems.append("missing related-links block")
    if 'id="calendar-days"' not in html:
        problems.append("missing calendar sidebar (id=\"calendar-days\")")
    if "FORCED_PAGE_DATE" not in html:
        problems.append("missing window.FORCED_PAGE_DATE")
    return problems


def staged_added():
    out = subprocess.check_output(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=A"],
        cwd=ROOT, text=True)
    return [l.strip() for l in out.splitlines() if l.strip().lower().endswith(".html")]


def main():
    args = sys.argv[1:]
    audit_all = "--all" in args
    if audit_all:
        files = [f for f in os.listdir(ROOT) if f.endswith(".html")]
    elif "--staged-added" in args:
        files = staged_added()
    else:
        files = args

    failed = 0
    checked = 0
    for f in files:
        family = classify(f)
        if not family:
            continue
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            continue
        problems = check(path, family)
        checked += 1
        if problems:
            failed += 1
            print(f"  [TEMPLATE VIOLATION] {f} ({family})")
            for p in problems:
                print(f"     - {p}")
    if failed:
        print(f"\n[BLOCKED] {failed}/{checked} preview page(s) violate PREVIEW_PAGE_STANDARD.md.")
        print("Fix the page (copy docs/templates/ skeleton) - do NOT invent a new format.")
        if not audit_all:
            sys.exit(1)
    else:
        print(f"[OK] {checked} preview page(s) match the locked template.")


if __name__ == "__main__":
    main()
