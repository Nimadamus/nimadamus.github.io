#!/usr/bin/env python3
"""Contextual Bet Legend Pro module on the first ~30 pages (Nima, Oct 1 2026).

Rules (approved): one module per page, never above the fold (it sits at the end of
the page content), no popups, copy about what the visitor is reading, and only
claims the live product supports. Verified Oct 1 2026 against the BLP query
engine (backend/app/services/filter_registry.py) and the live dataset endpoint
(trustmyrecord-api /api/betlegend-pro/dataset-stats: 132,316 graded games,
NFL/MLB/NBA/NHL only): team and opponent (head to head), home or road, favorite
or underdog, moneyline/spread/total ranges, MLB starting pitcher, rest days and
back to backs, previous result, over/under results, date ranges. No college or
soccer data, so those pages get no module.

Every link goes to the one purchase destination, trustmyrecord.com/betlegend-pro/,
with UTM tags, and /blp-events.js sends a GA4 `pro_cta_click` event with
page_type, sport, source_url and cta_variant.

Idempotent: the block lives between <!-- PRO-CTA-START --> and <!-- PRO-CTA-END -->.
Usage: python scripts/pro_cta.py [--dry-run]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = "https://trustmyrecord.com/betlegend-pro/"
GAMES = "132,000+"

COPY = {
    "records-all": ("Go past our picks", "Research any betting situation yourself",
                    f"Our record shows what we bet. Bet Legend Pro lets you test your own ideas against {GAMES} graded NFL, MLB, NBA and NHL games, filtered by team, opponent, home or road, favorite or underdog price, rest and the previous result.",
                    "Explore Bet Legend Pro"),
    "records-mlb": ("Beyond our MLB record", "Pull the history behind any MLB spot",
                    "Every MLB pick we post is graded above. In Bet Legend Pro you can look up the history behind a spot yourself: a team against one opponent, home or road, a moneyline range, the starting pitcher, and how teams did after a win or a loss.",
                    "Research MLB in Pro"),
    "records-nfl": ("Beyond our NFL record", "Ask any NFL betting question",
                    "Road favorites after a loss? A team against a division rival? Totals in a certain range? Bet Legend Pro answers with the graded history, filtered by spread and total ranges, home or road, rest and the previous result.",
                    "Research NFL in Pro"),
    "records-nba": ("Beyond our NBA record", "Look up any NBA situation",
                    "Home underdogs on the second night of a back to back, a team against one opponent, totals in a range: Bet Legend Pro returns the graded record for the exact spot you describe.",
                    "Research NBA in Pro"),
    "records-nhl": ("Beyond our NHL record", "Ask Pro any NHL betting question",
                    "Home underdogs on a back to back, totals after a loss, one team against one opponent. Filter the graded NHL history by price, rest, venue and the previous result in Bet Legend Pro.",
                    "Research NHL in Pro"),
    "stats-nhl": ("Go deeper than league splits", "Filter these NHL numbers your way",
                  "This page shows league-wide splits. Bet Legend Pro lets you narrow them to one team, one opponent, a price range, rest days or the previous result, with the graded record for that exact spot.",
                  "Research NHL in Pro"),
    "calc-ev": ("Found positive EV?", "Check how the spot has actually played",
                f"Your number says the bet has an edge. Bet Legend Pro shows how teams in the same situation have done historically, filtered by price range, venue, rest and the previous result, across {GAMES} graded games.",
                "Research the situation"),
    "calc-sizing": ("Size bets on real numbers", "Look up the spot before you stake it",
                    f"A staking plan is only as good as the edge behind it. Before you size a play, look up how the same spot has gone in Bet Legend Pro: the graded record for any team, price range and situation across {GAMES} NFL, MLB, NBA and NHL games.",
                    "Explore Bet Legend Pro"),
    "hub-mlb": ("Before you bet today's slate", "Look up any MLB game on this board",
                "Pick a game above and pull its history in Bet Legend Pro: the head-to-head record, home and road splits, moneyline ranges and the starting pitcher.",
                "Open Bet Legend Pro"),
    "hub-nfl": ("Before you bet this week", "Look up any NFL game on this board",
                "Pick a game above and pull its history in Bet Legend Pro: the head-to-head record, spread and total ranges, home or road and rest.",
                "Open Bet Legend Pro"),
    "hub-nba": ("Before you bet the slate", "Look up any NBA game on this board",
                "Pick a game above and pull its history in Bet Legend Pro: the head-to-head record, back to backs, rest days and price ranges.",
                "Open Bet Legend Pro"),
    "hub-nhl": ("Before you bet the slate", "Look up any NHL game on this board",
                "Pick a game above and pull its history in Bet Legend Pro: the head-to-head record, back to backs, home and road splits and price ranges.",
                "Open Bet Legend Pro"),
}

# path -> (page_type, sport, variant)
PAGES = {
    "records.html": ("records", "all", "records-all"),
    "mlb-records.html": ("records", "MLB", "records-mlb"),
    "nfl-records.html": ("records", "NFL", "records-nfl"),
    "nba-records.html": ("records", "NBA", "records-nba"),
    "nhl-records.html": ("records", "NHL", "records-nhl"),
    "nhl-home-away-splits.html": ("stats", "NHL", "stats-nhl"),
    "nhl-team-trends.html": ("stats", "NHL", "stats-nhl"),
    "nhl-totals-trends.html": ("stats", "NHL", "stats-nhl"),
    "nhl-betting-hub.html": ("stats", "NHL", "stats-nhl"),
    "ev-calculator.html": ("calculator", "all", "calc-ev"),
    "ev-calculator/how-to-calculate-ev.html": ("calculator", "all", "calc-ev"),
    "ev-calculator/positive-ev-guide.html": ("calculator", "all", "calc-ev"),
    "kelly-criterion.html": ("calculator", "all", "calc-sizing"),
    "kelly-criterion/simple-guide.html": ("calculator", "all", "calc-sizing"),
    "kelly-criterion/examples.html": ("calculator", "all", "calc-sizing"),
    "betting-calculators.html": ("calculator", "all", "calc-sizing"),
    "parlay-calculator.html": ("calculator", "all", "calc-sizing"),
    "risk-of-ruin-calculator.html": ("calculator", "all", "calc-sizing"),
    "bankroll-simulator.html": ("calculator", "all", "calc-sizing"),
    "bankroll.html": ("calculator", "all", "calc-sizing"),
    "odds-converter.html": ("calculator", "all", "calc-sizing"),
    "mlb.html": ("hub", "MLB", "hub-mlb"),
    "mlb-previews.html": ("hub", "MLB", "hub-mlb"),
    "nfl.html": ("hub", "NFL", "hub-nfl"),
    "nba.html": ("hub", "NBA", "hub-nba"),
    "nba-previews.html": ("hub", "NBA", "hub-nba"),
    "nhl.html": ("hub", "NHL", "hub-nhl"),
    "nhl-previews.html": ("hub", "NHL", "hub-nhl"),
}

START, END = "<!-- PRO-CTA-START (scripts/pro_cta.py) -->", "<!-- PRO-CTA-END -->"
BLOCK_RE = re.compile(r"<!-- PRO-CTA-START.*?<!-- PRO-CTA-END -->\r?\n?", re.S)
CSS = ("<style>.blp-pro-cta{box-sizing:border-box;max-width:880px;margin:40px auto;padding:22px 24px;border:1px solid rgba(232,184,92,.45);"
       "border-radius:12px;background:linear-gradient(160deg,#16140f,#0f1116);color:#e8ecf2;font-family:inherit;text-align:left}"
       ".blp-pro-cta .k{margin:0 0 6px;font-size:.72rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#e8b85c}"
       ".blp-pro-cta h2{margin:0 0 8px;font-size:1.3rem;line-height:1.25;color:#fff}"
       ".blp-pro-cta p{margin:0 0 14px;color:#c9d0da;line-height:1.55;font-size:.98rem}"
       ".blp-pro-cta a.b{display:inline-block;padding:11px 18px;border-radius:7px;background:#e8b85c;color:#16120c;font-weight:700;text-decoration:none}"
       ".blp-pro-cta a.b:focus-visible{outline:2px solid #fff;outline-offset:2px}"
       ".blp-pro-cta .s{display:block;margin-top:10px;font-size:.8rem;color:#9aa3af}"
       "@media(max-width:600px){.blp-pro-cta{margin:28px 12px;padding:18px 16px}}</style>")


def block(path, page_type, sport, variant):
    kicker, head, body, btn = COPY[variant]
    url = (f"{DEST}?utm_source=betlegendpicks&amp;utm_medium=pro_cta&amp;utm_campaign={page_type}"
           f"&amp;utm_content={variant}")
    depth = path.count("/")
    js = "../" * depth + "blp-events.js"
    e = lambda s: html.escape(s, quote=True)
    return (f"\n{START}\n{CSS}\n<aside class=\"blp-pro-cta\" aria-label=\"Bet Legend Pro\">"
            f"<p class=\"k\">{e(kicker)}</p><h2>{e(head)}</h2><p>{e(body)}</p>"
            f"<a class=\"b\" href=\"{url}\" data-pro-cta=\"{e(variant)}\" data-page-type=\"{e(page_type)}\" data-sport=\"{e(sport)}\">{e(btn)}</a>"
            f"<span class=\"s\">Monthly $49, annual $99 or lifetime $349.</span></aside>\n"
            f"<script src=\"{js}\" defer></script>\n{END}\n")


def apply(path, cfg, dry):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"  MISSING {path}")
        return False
    with open(full, encoding="utf-8", newline="") as f:
        s = f.read()
    nl = "\r\n" if "\r\n" in s else "\n"
    orig = s
    s = BLOCK_RE.sub("", s, count=1)
    b = block(path, *cfg).replace("\n", nl)
    # Inside <main> when the page has one (hub pages offset <main> for the fixed
    # calendar sidebar), otherwise before the footer, otherwise before </body>.
    mm = s.lower().rfind("</main>")
    m = re.search(r"<footer\b", s, re.I)
    if mm >= 0:
        s = s[:mm] + b.lstrip() + s[mm:]
    elif m:
        s = s[:m.start()] + b.lstrip() + s[m.start():]
    else:
        i = s.lower().rfind("</body>")
        if i < 0:
            print(f"  NO </body> {path}")
            return False
        s = s[:i] + b.lstrip() + s[i:]
    if s == orig:
        return False
    if not dry:
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(s)
    return True


def main():
    dry = "--dry-run" in sys.argv
    changed = [p for p, cfg in PAGES.items() if apply(p, cfg, dry)]
    print(f"[pro_cta] {'would update' if dry else 'updated'} {len(changed)} of {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
