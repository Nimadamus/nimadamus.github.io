#!/usr/bin/env python3
"""Link the betting data pages from the pages Google already crawls (Phase 5, Oct 1 2026).

Adds one idempotent "MLB betting data" block (between DATA-LINKS markers) to the
MLB hubs and records pages, so every team betting record page is two clicks
from the homepage. The block sits right above the Pro module when the page has
one, otherwise at the end of <main>, otherwise before the footer.

Usage: python scripts/data_links.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as mtp  # noqa: E402
import nhl_data_pages as ntp  # noqa: E402

# mlb-picks-today.html gets the block from scripts/picks_today.py, which rebuilds that page.
PAGES = {"mlb.html": "mlb", "mlb-previews.html": "mlb", "mlb-records.html": "mlb", "records.html": "both",
         "nhl.html": "nhl", "nhl-previews.html": "nhl", "nhl-records.html": "nhl", "nhl-betting-hub.html": "nhl",
         "nhl-home-away-splits.html": "nhl", "nhl-team-trends.html": "nhl", "nhl-totals-trends.html": "nhl"}
START, END = "<!-- DATA-LINKS-START (scripts/data_links.py) -->", "<!-- DATA-LINKS-END -->"
BLOCK_RE = re.compile(r"<!-- DATA-LINKS-START.*?<!-- DATA-LINKS-END -->\r?\n?", re.S)
CSS = ("<style>.blp-data-links{box-sizing:border-box;max-width:880px;margin:36px auto;padding:20px 22px;border:1px solid rgba(255,255,255,.12);"
       "border-radius:12px;background:#121620;color:#e8ecf2;text-align:left}"
       ".blp-data-links h2{margin:0 0 6px;font-size:1.2rem;color:#fff}.blp-data-links p{margin:0 0 12px;color:#c9d0da;font-size:.95rem}"
       ".blp-data-links ul{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:4px 16px;margin:0;padding:0;list-style:none}"
       ".blp-data-links a{color:#f3d77a;font-size:.92rem}.blp-data-links .all{display:inline-block;margin:0 0 10px;font-weight:700}"
       "@media(max-width:600px){.blp-data-links{margin:28px 12px;padding:16px}}</style>")


def mlb_section():
    teams = sorted(mtp.TEAMS, key=lambda t: mtp.TEAMS[t][0])
    items = "".join(f'<li><a href="/{mtp.page_file(t)}">{mtp.TEAMS[t][0]} betting record</a></li>' for t in teams)
    return ("<section class=\"blp-data-links\" aria-label=\"MLB team betting records\">"
            "<h2>MLB team betting records</h2>"
            "<p>Every team's record at closing lines: moneyline units, run line and over/under, season by season since 2016, with home, road, favorite and underdog splits.</p>"
            f"<p class=\"hubs\"><a class=\"all\" href=\"/{mtp.HUB}\">All 30 teams ranked</a> &middot; "
            "<a class=\"all\" href=\"/mlb-team-over-under-records.html\">Over/under records</a> &middot; "
            "<a class=\"all\" href=\"/mlb-run-line-records.html\">Run line records</a> &middot; "
            "<a class=\"all\" href=\"/yankees-vs-red-sox-betting-history.html\">Yankees vs Red Sox betting history</a></p>"
            f"<ul>{items}</ul></section>")


def nhl_section():
    teams = sorted(ntp.TEAMS, key=lambda t: ntp.TEAMS[t][0])
    items = "".join(f'<li><a href="/{ntp.page_file(t)}">{ntp.TEAMS[t][0]} betting record</a></li>' for t in teams)
    return ("<section class=\"blp-data-links\" aria-label=\"NHL team betting records\">"
            "<h2>NHL team betting records</h2>"
            "<p>Every team's record at closing lines: moneyline units, puck line and over/under, season by season since 2016-17, with home, road, back to back and favorite/underdog splits.</p>"
            f"<p class=\"hubs\"><a class=\"all\" href=\"/{ntp.HUB}\">All 32 teams ranked</a> &middot; "
            f"<a class=\"all\" href=\"/{ntp.PL_HUB}\">Puck line records</a> &middot; "
            f"<a class=\"all\" href=\"/{ntp.HA_HUB}\">Home and road betting records</a></p>"
            f"<ul>{items}</ul></section>")


def block(kind="mlb"):
    parts = {"mlb": [mlb_section()], "nhl": [nhl_section()], "both": [mlb_section(), nhl_section()]}[kind]
    return f"\n{START}\n{CSS}\n" + "\n".join(parts) + f"\n{END}\n"


def apply(path, kind, dry):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print("  MISSING", path)
        return False
    s = open(full, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    orig = s
    s = BLOCK_RE.sub("", s, count=1)
    b = block(kind).replace("\n", nl).lstrip()
    pro = s.find("<!-- PRO-CTA-START")
    mm = s.lower().rfind("</main>")
    m = re.search(r"<footer\b", s, re.I)
    if pro >= 0:
        s = s[:pro] + b + s[pro:]
    elif mm >= 0:
        s = s[:mm] + b + s[mm:]
    elif m:
        s = s[:m.start()] + b + s[m.start():]
    else:
        return False
    if s != orig and not dry:
        open(full, "w", encoding="utf-8", newline="").write(s)
    return s != orig


def main():
    dry = "--dry-run" in sys.argv
    n = sum(apply(p, k, dry) for p, k in PAGES.items())
    print(f"[data_links] {'would update' if dry else 'updated'} {n} of {len(PAGES)} pages")


if __name__ == "__main__":
    main()
