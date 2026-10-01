#!/usr/bin/env python3
"""MLB team betting record pages (Phase 5 SEO data program, Oct 1 2026).

Builds /mlb-team-betting-records.html (all 30 teams) and one page per team,
/<team-slug>-betting-record.html, from the Bet Legend game dataset: final
scores plus the closing moneyline, run line and total for every regular season
game. Every figure on a page is computed from the same list of games.

The dataset itself is paid data and never enters this public repo. Run this
locally against a refreshed copy of it:

    python scripts/mlb_team_pages.py --db PATH/universal_games.sqlite [--dry-run]

Definitions (also printed on every page):
  * Moneyline units: 1 unit risked on the team in every game at the closing
    moneyline. A win at -150 returns +0.667u, a win at +130 returns +1.30u, a
    loss is -1u.
  * Run line: the team covers when its margin plus its closing run line is above
    zero. MLB lines are +/-1.5, so there are no run line pushes.
  * Over/under: final total runs against the closing total; equal is a push.
  * Regular season only. Postseason games are excluded.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import os
import pickle
import re
import sqlite3
import statistics
import sys
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.betlegendpicks.com/"
PT = ZoneInfo("America/Los_Angeles")
FIRST_SEASON = 2016
HUB = "mlb-team-betting-records.html"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# franchise -> (current name, short name, slug, league, division)
TEAMS = {
    "Arizona Diamondbacks": ("Diamondbacks", "arizona-diamondbacks", "NL", "West"),
    "Atlanta Braves": ("Braves", "atlanta-braves", "NL", "East"),
    "Baltimore Orioles": ("Orioles", "baltimore-orioles", "AL", "East"),
    "Boston Red Sox": ("Red Sox", "boston-red-sox", "AL", "East"),
    "Chicago Cubs": ("Cubs", "chicago-cubs", "NL", "Central"),
    "Chicago White Sox": ("White Sox", "chicago-white-sox", "AL", "Central"),
    "Cincinnati Reds": ("Reds", "cincinnati-reds", "NL", "Central"),
    "Cleveland Guardians": ("Guardians", "cleveland-guardians", "AL", "Central"),
    "Colorado Rockies": ("Rockies", "colorado-rockies", "NL", "West"),
    "Detroit Tigers": ("Tigers", "detroit-tigers", "AL", "Central"),
    "Houston Astros": ("Astros", "houston-astros", "AL", "West"),
    "Kansas City Royals": ("Royals", "kansas-city-royals", "AL", "Central"),
    "Los Angeles Angels": ("Angels", "los-angeles-angels", "AL", "West"),
    "Los Angeles Dodgers": ("Dodgers", "los-angeles-dodgers", "NL", "West"),
    "Miami Marlins": ("Marlins", "miami-marlins", "NL", "East"),
    "Milwaukee Brewers": ("Brewers", "milwaukee-brewers", "NL", "Central"),
    "Minnesota Twins": ("Twins", "minnesota-twins", "AL", "Central"),
    "New York Mets": ("Mets", "new-york-mets", "NL", "East"),
    "New York Yankees": ("Yankees", "new-york-yankees", "AL", "East"),
    "Athletics": ("Athletics", "athletics", "AL", "West"),
    "Philadelphia Phillies": ("Phillies", "philadelphia-phillies", "NL", "East"),
    "Pittsburgh Pirates": ("Pirates", "pittsburgh-pirates", "NL", "Central"),
    "San Diego Padres": ("Padres", "san-diego-padres", "NL", "West"),
    "San Francisco Giants": ("Giants", "san-francisco-giants", "NL", "West"),
    "Seattle Mariners": ("Mariners", "seattle-mariners", "AL", "West"),
    "St. Louis Cardinals": ("Cardinals", "st-louis-cardinals", "NL", "Central"),
    "Tampa Bay Rays": ("Rays", "tampa-bay-rays", "AL", "East"),
    "Texas Rangers": ("Rangers", "texas-rangers", "AL", "West"),
    "Toronto Blue Jays": ("Blue Jays", "toronto-blue-jays", "AL", "East"),
    "Washington Nationals": ("Nationals", "washington-nationals", "NL", "East"),
}
ALIASES = {"Cleveland Indians": "Cleveland Guardians", "Oakland Athletics": "Athletics"}
ESPN_ABBR = {"Arizona Diamondbacks": "ari", "Atlanta Braves": "atl", "Baltimore Orioles": "bal", "Boston Red Sox": "bos",
             "Chicago Cubs": "chc", "Chicago White Sox": "chw", "Cincinnati Reds": "cin", "Cleveland Guardians": "cle",
             "Colorado Rockies": "col", "Detroit Tigers": "det", "Houston Astros": "hou", "Kansas City Royals": "kc",
             "Los Angeles Angels": "laa", "Los Angeles Dodgers": "lad", "Miami Marlins": "mia", "Milwaukee Brewers": "mil",
             "Minnesota Twins": "min", "New York Mets": "nym", "New York Yankees": "nyy", "Athletics": "ath",
             "Philadelphia Phillies": "phi", "Pittsburgh Pirates": "pit", "San Diego Padres": "sd",
             "San Francisco Giants": "sf", "Seattle Mariners": "sea", "St. Louis Cardinals": "stl", "Tampa Bay Rays": "tb",
             "Texas Rangers": "tex", "Toronto Blue Jays": "tor", "Washington Nationals": "wsh"}


def e(s):
    return html.escape(str(s), quote=True)


def page_file(team):
    return f"{TEAMS[team][1]}-betting-record.html"


def logo(team):
    return f"https://a.espncdn.com/i/teamlogos/mlb/500/{ESPN_ABBR[team]}.png"


# ---------------------------------------------------------------- data

def load_games(db):
    con = sqlite3.connect(db)
    out = []
    for season, blob in con.execute("SELECT season, blob FROM games WHERE sport='MLB' AND season >= ?", (str(FIRST_SEASON),)):
        g = pickle.loads(blob)
        h = ALIASES.get(g["HomeTeam"], g["HomeTeam"]); a = ALIASES.get(g["AwayTeam"], g["AwayTeam"])
        if h not in TEAMS or a not in TEAMS:
            continue
        if g.get("HomeScore") is None or g.get("AwayScore") is None:
            continue
        out.append({"season": int(season), "date": g["Date"], "home": h, "away": a, "hs": int(g["HomeScore"]),
                    "as": int(g["AwayScore"]), "hml": g.get("HomeMoneyline"), "aml": g.get("AwayMoneyline"),
                    "line": g.get("Spread"), "total": g.get("Total"), "id": g.get("GameID"),
                    "dn": g.get("_mlb_day_night"), "gt": g.get("GameTime"),
                    "est": bool(g.get("_ml_estimated") or g.get("_spread_estimated") or g.get("_total_estimated"))})
    # A stored row can repeat another game under a later date (same teams, same start time).
    # Keep the copy whose date matches its start time; found 2026-10-01 on SF at ATL, June 16/17 2026.
    seen = {}
    for g in out:
        if not g["gt"]:
            continue
        k = (g["home"], g["away"], g["gt"])
        if k in seen:
            a = seen[k]
            keep = a if a["date"] == a["gt"][:10] else g
            drop = g if keep is a else a
            drop["dup"] = True
            seen[k] = keep
        else:
            seen[k] = g
    dropped = [g for g in out if g.get("dup")]
    for g in dropped:
        print(f"  dropped duplicate row {g['id']} ({g['date']}, start {g['gt']})")
    return [g for g in out if not g.get("dup")]


def regular_season(games):
    """Drop postseason games. The regular season ends on the date most teams play game 162 (60 in 2020)."""
    by_season = collections.defaultdict(list)
    for g in games:
        by_season[g["season"]].append(g)
    keep, report = [], {}
    for season, gs in by_season.items():
        n = 60 if season == 2020 else 162
        gs.sort(key=lambda g: g["date"])
        nth = {}
        count = collections.Counter()
        for g in gs:
            for t in (g["home"], g["away"]):
                count[t] += 1
                if count[t] == n:
                    nth[t] = g["date"]
        if len(nth) < 25:  # season still in progress
            reg = list(gs)
            end = "9999-12-31"
        else:
            # The last scheduled day is the date most teams play game n. Later games count only
            # when both teams are still short of n (a makeup game), which leaves the postseason out.
            end = collections.Counter(nth.values()).most_common(1)[0][0]
            played = collections.Counter()
            reg = []
            for g in gs:
                if g["date"] <= end or (played[g["home"]] < n and played[g["away"]] < n):
                    reg.append(g); played[g["home"]] += 1; played[g["away"]] += 1
        per = collections.Counter()
        for g in reg:
            per[g["home"]] += 1; per[g["away"]] += 1
        report[season] = (end, min(per.values()), max(per.values()), len(reg), len(gs) - len(reg))
        keep += reg
    return keep, report


def verify_against_espn(cur_games, season):
    """Every team's regular season games (count and final scores) must match ESPN's team schedule."""
    import urllib.request
    bad = []
    for t in TEAMS:
        url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{ESPN_ABBR[t]}/schedule?season={season}&seasontype=2"
        d = json.load(urllib.request.urlopen(url, timeout=30))
        espn = collections.Counter()
        for x in d.get("events", []):
            c = x["competitions"][0]
            if not c.get("status", {}).get("type", {}).get("completed"):
                continue
            sc = {}
            for cp in c["competitors"]:
                v = cp.get("score"); v = v.get("value") if isinstance(v, dict) else v
                sc[cp["homeAway"]] = int(float(v))
            espn[(sc["home"], sc["away"])] += 1
        mine = collections.Counter((g["hs"], g["as"]) for g in cur_games if t in (g["home"], g["away"]))
        if mine != espn:
            bad.append((t, sum(mine.values()), sum(espn.values())))
    return bad


COVERAGE = {}  # (team, season) -> (kept, espn_games, dropped_rows, missing_games), filled by verified_games()


def verified_games(db, cur, check=True):
    """Load the dataset and keep only games ESPN records identically (regular season, same teams and score).
    The current season must match ESPN game for game or the build stops."""
    import espn_verify
    games = load_games(db)
    if not check:
        g2, _ = regular_season(games)
        return g2, {}, True
    kept, dropped, report, cur_bad, finished = espn_verify.verify(
        games, "mlb", ESPN_ABBR, ALIASES, lambda s: s, cur, TEAMS)
    if cur_bad:
        sys.exit(f"ABORT: {cur} games disagree with ESPN: {cur_bad}")
    COVERAGE.clear(); COVERAGE.update(report)
    by = collections.defaultdict(lambda: [0, 0])
    for (t, s), (k, n, dr, mi) in report.items():
        by[s][0] += dr; by[s][1] += mi
    for s in sorted(by):
        print(f"  {s}: verified against ESPN; team rows dropped {by[s][0]}, team games missing {by[s][1]}")
    print(f"  {cur}: every team matches ESPN game for game; season finished={finished}")
    return kept, report, finished


def ml_profit(ml, won):
    if not won:
        return -1.0
    return ml / 100.0 if ml > 0 else 100.0 / abs(ml)


def team_rows(games, team):
    """One row per game from the team's side."""
    rows = []
    for g in games:
        if team not in (g["home"], g["away"]):
            continue
        home = g["home"] == team
        rf, ra = (g["hs"], g["as"]) if home else (g["as"], g["hs"])
        ml = g["hml"] if home else g["aml"]
        oml = g["aml"] if home else g["hml"]
        # MLB run lines are 1.5 runs; any other stored value is not a run line, so it is left out
        line = None if g["line"] is None or abs(g["line"]) != 1.5 else (g["line"] if home else -g["line"])
        r = {"season": g["season"], "date": g["date"], "home": home, "opp": g["away"] if home else g["home"],
             "rf": rf, "ra": ra, "won": rf > ra, "ml": ml, "oml": oml, "line": line, "total": g["total"], "dn": g["dn"], "id": g["id"]}
        r["units"] = ml_profit(ml, r["won"]) if ml else None
        r["fav"] = (ml is not None and oml is not None and ml < oml)
        if line is not None:
            m = rf - ra + line
            r["cover"] = None if m == 0 else m > 0
        else:
            r["cover"] = None
        if g["total"] is not None:
            t = rf + ra
            r["ou"] = "O" if t > g["total"] else ("U" if t < g["total"] else "P")
        else:
            r["ou"] = None
        rows.append(r)
    rows.sort(key=lambda r: r["date"])
    return rows


def agg(rows):
    w = sum(r["won"] for r in rows); l = len(rows) - w
    priced = [r for r in rows if r["units"] is not None]
    units = sum(r["units"] for r in priced)
    cov = sum(r["cover"] is True for r in rows); ncov = sum(r["cover"] is False for r in rows)
    o = sum(r["ou"] == "O" for r in rows); u = sum(r["ou"] == "U" for r in rows); p = sum(r["ou"] == "P" for r in rows)
    totals = [r["total"] for r in rows if r["total"] is not None]
    return {"n": len(rows), "w": w, "l": l, "units": units, "priced": len(priced),
            "roi": (100.0 * units / len(priced)) if priced else 0.0, "cov": cov, "ncov": ncov,
            "o": o, "u": u, "p": p, "avg_total": (sum(totals) / len(totals)) if totals else None,
            "rpg": (sum(r["rf"] for r in rows) / len(rows)) if rows else 0, "rapg": (sum(r["ra"] for r in rows) / len(rows)) if rows else 0}


# ---------------------------------------------------------------- formatting

def fu(x):
    x = 0.0 if abs(x) < 0.005 else x
    return f"{x:+.2f}u"


def froi(x):
    x = 0.0 if abs(x) < 0.05 else x
    return f"{x:+.1f}%"


def pct(a, b):
    return f"{100.0 * a / (a + b):.1f}%" if (a + b) else "none"


def fodds(x):
    if x is None:
        return "no line"
    x = int(round(x))
    return f"+{x}" if x > 0 else str(x)


def fdate(iso, year=True):
    d = dt.date.fromisoformat(iso)
    return f"{d:%b} {d.day}, {d.year}" if year else f"{d:%b} {d.day}"


def cls(x):
    return "w" if x > 0 else ("l" if x < 0 else "")


def ordinal(n):
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


CSS = """body{margin:0;background:#0d0f14;color:#e8ecf2;font-family:Inter,Manrope,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.6}
.tr{max-width:1000px;margin:0 auto;padding:28px 18px 60px;box-sizing:border-box}
.tr a{color:#f3d77a}
.tr .crumbs{font-size:.85rem;color:#9aa3af;margin:0 0 10px}.tr .crumbs a{color:#9aa3af}
.tr .head{display:flex;gap:16px;align-items:center}
.tr .head img{width:64px;height:64px;flex:0 0 auto;background:#f2f3f5;border-radius:50%;padding:6px;box-sizing:border-box}
.tr h1{font-size:2rem;line-height:1.2;margin:0;color:#fff;text-wrap:balance}
.tr .lead{color:#c9d0da;margin:14px 0 6px;max-width:72ch}
.tr .upd{color:#8b94a1;font-size:.85rem;margin:0 0 22px}
.tr h2{font-size:1.3rem;margin:36px 0 10px;color:#fff}
.tr h3{font-size:1.02rem;margin:22px 0 8px;color:#fff}
.tr p{max-width:76ch}
.tr .note{color:#9aa3af;font-size:.88rem}
.tr-jump{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.88rem;margin:0 0 6px;padding:0;list-style:none}
.tr-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;width:0;min-width:100%}
.tr table{width:100%;border-collapse:collapse;font-size:.9rem;min-width:560px}
.tr th{text-align:right;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;color:#d4af37;padding:8px;border-bottom:1px solid rgba(212,175,55,.35);white-space:nowrap}
.tr td{padding:8px;border-bottom:1px solid rgba(255,255,255,.08);text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.tr th:first-child,.tr td:first-child{text-align:left}
.tr td.t{white-space:normal;text-align:left}
.tr .w{color:#6fd08f}.tr .l{color:#ef7d6f}
.tr-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin:8px 0 4px}
.tr-stats div{background:#141821;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:14px}
.tr-stats b{display:block;font-size:1.4rem;color:#fff;font-variant-numeric:tabular-nums}
.tr-stats span{color:#9aa3af;font-size:.82rem}
.tr details{border-bottom:1px solid rgba(255,255,255,.08);padding:10px 0}
.tr summary{cursor:pointer;font-weight:600;color:#fff}
.tr details p{color:#c9d0da;margin:8px 0 0}
.tr .links{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px 18px;padding:0;list-style:none}
.tr .pill{display:inline-block;font-size:.72rem;padding:2px 7px;border-radius:4px;background:#1c2230;color:#c9d0da}
@media(max-width:600px){.tr h1{font-size:1.55rem}.tr .head img{width:48px;height:48px}}"""


def shell(file, title, desc, h1, body, ld, crumbs, now_pt, head_img=None):
    url = SITE + file
    upd = f"{now_pt:%B} {now_pt.day}, {now_pt.year}"
    img = f'<img src="{e(head_img)}" alt="" width="64" height="64" loading="eager">' if head_img else ""
    crumb_html = " / ".join(f'<a href="{e(h)}">{e(n)}</a>' if h else e(n) for n, h in crumbs)
    ld_all = ld + [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + (h or file).lstrip("/")} for i, (n, h) in enumerate(crumbs)]}]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(h1)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}newlogo.png">
<meta property="og:site_name" content="BetLegend Picks">
<meta name="twitter:card" content="summary">
<link rel="icon" href="/images/newlogo-64.png" type="image/png">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-QS8L5TDNLY');</script>
{"".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + '</script>' for x in ld_all)}
<link rel="stylesheet" href="/site-navbar.css">
<link rel="stylesheet" href="/mobile-optimize.css">
<style>
{CSS}
</style>
</head>
<body>
<script src="/scripts/site-navbar.js" defer></script>
<main class="tr">
<p class="crumbs">{crumb_html}</p>
<div class="head">{img}<h1>{e(h1)}</h1></div>
{body.replace("{UPDATED}", e(upd))}
</main>
<script src="/blp-events.js" defer></script>
</body>
</html>
"""


def season_table(rows, seasons):
    trs = []
    for s in seasons:
        rs = [r for r in rows if r["season"] == s]
        if not rs:
            continue
        a = agg(rs)
        trs.append(f"<tr><td>{s}</td><td>{a['w']}-{a['l']}</td><td class=\"{cls(a['units'])}\">{fu(a['units'])}</td>"
                   f"<td>{froi(a['roi'])}</td><td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td>"
                   f"<td>{a['avg_total']:.2f}</td><td>{a['rpg']:.2f}</td><td>{a['rapg']:.2f}</td></tr>")
    a = agg([r for r in rows if r["season"] in seasons])
    trs.append(f"<tr><td><strong>All {len(seasons)} seasons</strong></td><td><strong>{a['w']}-{a['l']}</strong></td>"
               f"<td class=\"{cls(a['units'])}\"><strong>{fu(a['units'])}</strong></td><td>{froi(a['roi'])}</td>"
               f"<td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{a['avg_total']:.2f}</td><td>{a['rpg']:.2f}</td><td>{a['rapg']:.2f}</td></tr>")
    return ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Record</th><th>ML units</th><th>ML ROI</th>'
            '<th>Run line</th><th>O/U/P</th><th>Avg total</th><th>Runs/G</th><th>Allowed/G</th></tr></thead><tbody>'
            + "".join(trs) + "</tbody></table></div>")


def split_table(splits):
    trs = []
    for name, rs in splits:
        if not rs:
            continue
        a = agg(rs)
        trs.append(f"<tr><td class=\"t\">{e(name)}</td><td>{a['n']}</td><td>{a['w']}-{a['l']}</td>"
                   f"<td class=\"{cls(a['units'])}\">{fu(a['units'])}</td><td>{froi(a['roi'])}</td>"
                   f"<td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td></tr>")
    return ('<div class="tr-wrap"><table><thead><tr><th>Situation</th><th>Games</th><th>Record</th><th>ML units</th>'
            '<th>ML ROI</th><th>Run line</th><th>O/U/P</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")


def splits_for(rows, team, prev_rows_map):
    div = TEAMS[team][3]; lg = TEAMS[team][2]
    out = [("Home", [r for r in rows if r["home"]]), ("Road", [r for r in rows if not r["home"]]),
           ("As favorite", [r for r in rows if r["fav"]]), ("As underdog", [r for r in rows if r["ml"] is not None and not r["fav"]]),
           ("Favorite of -150 or shorter", [r for r in rows if r["ml"] is not None and r["ml"] <= -150]),
           ("Underdog of +130 or longer", [r for r in rows if r["ml"] is not None and r["ml"] >= 130]),
           ("After a win", [r for r in rows if prev_rows_map.get(r["date"] + r["opp"]) is True]),
           ("After a loss", [r for r in rows if prev_rows_map.get(r["date"] + r["opp"]) is False]),
           (f"vs {lg} {div} rivals", [r for r in rows if TEAMS[r["opp"]][2] == lg and TEAMS[r["opp"]][3] == div]),
           (f"vs {'NL' if lg == 'AL' else 'AL'} (interleague)", [r for r in rows if TEAMS[r["opp"]][2] != lg])]
    dn = [r for r in rows if r["dn"] in ("D", "N")]
    if len(dn) >= 0.9 * len(rows) and rows:
        out += [("Day games", [r for r in rows if r["dn"] == "D"]), ("Night games", [r for r in rows if r["dn"] == "N"])]
    return out


def prev_map(rows):
    """date+opp -> did the team win its previous game (same season)."""
    m = {}
    for i, r in enumerate(rows):
        if i and rows[i - 1]["season"] == r["season"]:
            m[r["date"] + r["opp"]] = rows[i - 1]["won"]
    return m


def build_team(team, games, all_teams_season, cur, now_pt, rank):
    short, slug, lg, div = TEAMS[team]
    rows = team_rows(games, team)
    seasons = sorted({r["season"] for r in rows}, reverse=True)
    cur_rows = [r for r in rows if r["season"] == cur]
    a = agg(cur_rows)
    pm = prev_map(rows)
    file = page_file(team)
    last_date = cur_rows[-1]["date"]
    import espn_verify
    cov_note = espn_verify.coverage_note(COVERAGE, team, str)
    span = f"{seasons[-1]} to {seasons[0]}"
    allr = agg(rows)

    # opponents this season
    opp_rows = collections.defaultdict(list)
    for r in cur_rows:
        opp_rows[r["opp"]].append(r)
    h2h = []
    for opp, rs in sorted(opp_rows.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        o = agg(rs)
        h2h.append(f"<tr><td class=\"t\"><a href=\"{page_file(opp)}\">{e(opp)}</a></td><td>{o['n']}</td><td>{o['w']}-{o['l']}</td>"
                   f"<td class=\"{cls(o['units'])}\">{fu(o['units'])}</td><td>{o['cov']}-{o['ncov']}</td><td>{o['o']}-{o['u']}-{o['p']}</td></tr>")
    h2h_html = ('<div class="tr-wrap"><table><thead><tr><th>Opponent</th><th>Games</th><th>Record</th><th>ML units</th>'
                '<th>Run line</th><th>O/U/P</th></tr></thead><tbody>' + "".join(h2h) + "</tbody></table></div>")

    # last 15 games
    l15 = []
    for r in cur_rows[-15:][::-1]:
        res = "W" if r["won"] else "L"
        ou = {"O": "Over", "U": "Under", "P": "Push", None: "no line"}[r["ou"]]
        rl = "no line" if r["line"] is None else f"{r['line']:+.1f}"
        tot = "no line" if r["total"] is None else f"{r['total']:g}"
        l15.append(f"<tr><td>{fdate(r['date'], False)}</td><td class=\"t\">{'vs' if r['home'] else 'at'} {e(TEAMS[r['opp']][0])}</td>"
                   f"<td class=\"{'w' if r['won'] else 'l'}\">{res} {r['rf']}-{r['ra']}</td><td>{fodds(r['ml'])}</td>"
                   f"<td>{rl}</td><td>{tot}</td><td>{ou}</td>"
                   f"<td class=\"{cls(r['units'] or 0)}\">{'' if r['units'] is None else fu(r['units'])}</td></tr>")
    l15_html = ('<div class="tr-wrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Close ML</th>'
                '<th>Run line</th><th>Total</th><th>O/U</th><th>ML units</th></tr></thead><tbody>' + "".join(l15) + "</tbody></table></div>")

    # monthly
    months = collections.OrderedDict()
    for r in cur_rows:
        months.setdefault(dt.date.fromisoformat(r["date"]).strftime("%B"), []).append(r)
    month_html = split_table([(m, rs) for m, rs in months.items()])

    sp = splits_for(cur_rows, team, pm)
    sp_agg = {n: agg(rs) for n, rs in sp if rs}
    home, road = sp_agg["Home"], sp_agg["Road"]
    fav = sp_agg.get("As favorite"); dog = sp_agg.get("As underdog")

    # league ranks this season
    ranks = sorted(all_teams_season.items(), key=lambda kv: -kv[1]["units"])
    unit_rank = [t for t, _ in ranks].index(team) + 1
    over_rank = [t for t, _ in sorted(all_teams_season.items(), key=lambda kv: -(kv[1]["o"] / max(1, kv[1]["o"] + kv[1]["u"])))].index(team) + 1

    best_season = max(seasons, key=lambda s: agg([r for r in rows if r["season"] == s])["units"])
    worst_season = min(seasons, key=lambda s: agg([r for r in rows if r["season"] == s])["units"])
    bs, ws = agg([r for r in rows if r["season"] == best_season]), agg([r for r in rows if r["season"] == worst_season])

    lean = "over" if a["o"] > a["u"] else ("under" if a["u"] > a["o"] else "neither side")
    finished = rank.get("finished", False)
    when = f"the {cur} regular season" if finished else f"{cur} so far (through {fdate(last_date)})"
    lead = (f"The {short} went {a['w']}-{a['l']} in {when}. A bettor who put 1 unit on them at the closing moneyline in every game "
            f"finished {fu(a['units'])} ({froi(a['roi'])} ROI), {ordinal(unit_rank)} of 30 MLB teams. "
            f"They were {a['cov']}-{a['ncov']} on the run line and {a['o']}-{a['u']}-{a['p']} against the total, "
            f"so their games leaned {lean}" + (f" ({ordinal(over_rank)} in over percentage)." if lean != "neither side" else "."))
    stats = (f'<div class="tr-stats"><div><b>{a["w"]}-{a["l"]}</b><span>{cur} record</span></div>'
             f'<div><b class="{cls(a["units"])}">{fu(a["units"])}</b><span>moneyline units, {ordinal(unit_rank)} in MLB</span></div>'
             f'<div><b>{a["cov"]}-{a["ncov"]}</b><span>run line ({pct(a["cov"], a["ncov"])})</span></div>'
             f'<div><b>{a["o"]}-{a["u"]}-{a["p"]}</b><span>over, under, push ({pct(a["o"], a["u"])} overs)</span></div></div>')

    rivals = [t for t in TEAMS if t != team and TEAMS[t][2] == lg and TEAMS[t][3] == div]
    faq = [
        (f"What is the {short} betting record in {cur}?",
         f"{a['w']}-{a['l']} straight up, {fu(a['units'])} betting 1 unit on every game at the closing moneyline, {a['cov']}-{a['ncov']} on the run line and {a['o']}-{a['u']}-{a['p']} on totals ({when})."),
        (f"Are the {short} profitable to bet at home or on the road?",
         f"At home they were {home['w']}-{home['l']} for {fu(home['units'])}; on the road {road['w']}-{road['l']} for {fu(road['units'])} in {cur}."),
        (f"How do the {short} do as a favorite and as an underdog?",
         (f"As a favorite: {fav['w']}-{fav['l']}, {fu(fav['units'])}. " if fav else "") + (f"As an underdog: {dog['w']}-{dog['l']}, {fu(dog['units'])}." if dog else "")),
        (f"Do {short} games go over or under?",
         f"In {cur} their games were {a['o']}-{a['u']}-{a['p']} against the closing total, with an average total of {a['avg_total']:.2f} runs and {a['rpg'] + a['rapg']:.2f} actual runs per game."),
        (f"What was the {short}' best betting season since {seasons[-1]}?",
         f"{best_season}: {bs['w']}-{bs['l']} for {fu(bs['units'])}. The worst was {worst_season}: {ws['w']}-{ws['l']} for {fu(ws['units'])}. Over all {len(seasons)} seasons they are {allr['w']}-{allr['l']}, {fu(allr['units'])}."),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)

    def rivalry(t):
        for x, y in ((team, t), (t, team)):
            f = f"{TEAMS[x][0].lower().replace(' ', '-')}-vs-{TEAMS[y][0].lower().replace(' ', '-')}-betting-history.html"
            if os.path.isfile(os.path.join(ROOT, f)):
                return f
        return None
    related = [(f"{short} vs {TEAMS[t][0]} betting history", rivalry(t)) for t in rivals if rivalry(t)]
    related += [(f"{t} betting record", page_file(t)) for t in rivals]
    related += [("MLB over/under records by team", "mlb-team-over-under-records.html"), ("MLB run line records by team", "mlb-run-line-records.html")]
    related += [("All 30 MLB team betting records", HUB), ("MLB picks today", "mlb-picks-today.html"),
                ("MLB slate, odds and analysis", "mlb.html"), ("BetLegend MLB picks record", "mlb-records.html"),
                ("How to bet MLB totals", "how-to-bet-mlb-totals.html"), ("Moneyline vs run line explained", "spread-vs-moneyline-betting.html")]
    related_html = '<ul class="links">' + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in related if os.path.isfile(os.path.join(ROOT, h))) + "</ul>"

    pro = ('<aside class="blp-pro-cta" aria-label="Bet Legend Pro" style="box-sizing:border-box;margin:40px 0;padding:22px 24px;border:1px solid rgba(232,184,92,.45);border-radius:12px;background:linear-gradient(160deg,#16140f,#0f1116)">'
           f'<p style="margin:0 0 6px;font-size:.72rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#e8b85c">Go deeper on the {e(short)}</p>'
           f'<h2 style="margin:0 0 8px;font-size:1.3rem">Filter every {e(short)} game yourself</h2>'
           f'<p style="color:#c9d0da">This page covers fixed splits. Bet Legend Pro lets you filter the full MLB history by opponent, starting pitcher, moneyline range, rest and the previous result, and returns the graded record for that exact spot.</p>'
           f'<a href="https://trustmyrecord.com/betlegend-pro/?utm_source=betlegendpicks&amp;utm_medium=pro_cta&amp;utm_campaign=team_record&amp;utm_content={slug}" data-pro-cta="team-record" data-page-type="data" data-sport="MLB" '
           'style="display:inline-block;padding:11px 18px;border-radius:7px;background:#e8b85c;color:#16120c;font-weight:700;text-decoration:none">Explore Bet Legend Pro</a></aside>')

    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing lines, regular season games only, {span}. <a href="#method">How these numbers are calculated</a>.</p>
<ul class="tr-jump"><li><a href="#season">{cur} summary</a></li><li><a href="#history">Season by season</a></li><li><a href="#splits">Splits</a></li><li><a href="#opponents">vs every opponent</a></li><li><a href="#recent">Last 15 games</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="season"><h2>{e(short)} {cur} betting summary</h2>
{stats}
<p>At home the {e(short)} were {home['w']}-{home['l']} ({fu(home['units'])}); on the road {road['w']}-{road['l']} ({fu(road['units'])}). {e(f"As a favorite they went {fav['w']}-{fav['l']} ({fu(fav['units'])}), and as an underdog {dog['w']}-{dog['l']} ({fu(dog['units'])})." if fav and dog else "")}</p>
</section>
<section id="history"><h2>{e(short)} betting record by season, {span}</h2>
<p>Each row is one regular season. Moneyline units assume 1 unit on the {e(short)} in every game at the closing price. Their best year for a moneyline bettor in this span was {best_season} ({fu(bs['units'])}); the worst was {worst_season} ({fu(ws['units'])}).</p>
{season_table(rows, seasons)}
</section>
<section id="splits"><h2>{e(short)} betting splits, {cur}</h2>
{split_table(sp)}
<h3>By month</h3>
{month_html}
</section>
<section id="opponents"><h2>{e(short)} record against every opponent, {cur}</h2>
<p>Sorted by number of meetings. Each opponent links to its own betting record page.</p>
{h2h_html}
</section>
<section id="recent"><h2>Last 15 {e(short)} games with closing lines</h2>
{l15_html}
<p class="note">Close ML is the {e(short)}' closing moneyline. The run line is shown from the {e(short)}' side.</p>
</section>
{pro}
<section id="faq"><h2>{e(short)} betting FAQ</h2>
{faq_html}
</section>
<section id="method"><h2>Methodology</h2>
<p>Results and closing lines come from the Bet Legend game database: final scores for every regular season game since {seasons[-1]}, with the closing moneyline, run line and total. Every game is checked against ESPN's official schedule and final score; postseason games are excluded. Moneyline units risk 1 unit per game at the close, so a win at -150 pays +0.67u and a win at +130 pays +1.30u. The run line record compares the final margin with the closing line (MLB run lines are 1.5 runs, so there are no pushes). Over and under results compare total runs with the closing total; an exact match is a push. {e(f"{cur} figures run through {fdate(last_date)}.")}</p>
{('<p class="note">' + e(cov_note) + '</p>') if cov_note else ''}
<p class="note">These are market results for the team, not BetLegend picks. Our own graded picks are on the <a href="mlb-records.html">MLB betting record page</a>.</p>
</section>
<section id="related"><h2>Related MLB betting data</h2>
{related_html}
</section>"""

    title = f"{team} Betting Record {cur}: Moneyline, Run Line, O/U"
    desc = (f"{team} {cur} betting record: {a['w']}-{a['l']}, {fu(a['units'])} on the moneyline, {a['cov']}-{a['ncov']} run line, "
            f"{a['o']}-{a['u']}-{a['p']} over/under, with home/road, favorite/underdog splits and every season since {seasons[-1]}.")
    h1 = f"{team} Betting Record {cur}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + file, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat(), "about": {"@type": "SportsTeam", "name": team, "sport": "Baseball"},
           "isPartOf": {"@type": "WebSite", "name": "BetLegend Picks", "url": SITE}},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", HUB), (f"{short} Betting Record", None)]
    page = shell(file, title, desc, h1, body, ld, crumbs, now_pt, head_img=logo(team))
    ids = [r["id"] for r in rows]
    return file, page, {"team": team, "games": len(rows), "cur_games": len(cur_rows), "ids": len(set(ids)), "title": title, "units": a["units"]}


def build_hub(games, cur, season_aggs, now_pt, finished, last_date):
    ranked = sorted(season_aggs.items(), key=lambda kv: -kv[1]["units"])
    trs = []
    for i, (t, a) in enumerate(ranked, 1):
        trs.append(f"<tr><td>{i}</td><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td><td>{a['w']}-{a['l']}</td>"
                   f"<td class=\"{cls(a['units'])}\">{fu(a['units'])}</td><td>{froi(a['roi'])}</td><td>{a['cov']}-{a['ncov']}</td>"
                   f"<td>{pct(a['cov'], a['ncov'])}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{pct(a['o'], a['u'])}</td></tr>")
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>Record</th><th>ML units</th><th>ROI</th>'
             '<th>Run line</th><th>RL %</th><th>O/U/P</th><th>Over %</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")
    # home / road / fav / dog league-wide
    lg = []
    for name, f in (("Home teams", lambda g: True), ):
        pass
    homes = [r for t in TEAMS for r in team_rows([g for g in games if g["season"] == cur], t) if r["home"]]
    favs = [r for t in TEAMS for r in team_rows([g for g in games if g["season"] == cur], t) if r["fav"]]
    ha, fa = agg(homes), agg(favs)
    tot = agg([r for r in homes])  # every game once (home side)
    top, bottom = ranked[0], ranked[-1]
    over_top = max(season_aggs.items(), key=lambda kv: kv[1]["o"] / max(1, kv[1]["o"] + kv[1]["u"]))
    under_top = min(season_aggs.items(), key=lambda kv: kv[1]["o"] / max(1, kv[1]["o"] + kv[1]["u"]))
    when = f"the {cur} regular season" if finished else f"{cur} through {fdate(last_date)}"
    lead = (f"Every MLB team's betting record for {when}, at closing lines: moneyline units, run line and over/under. "
            f"The {top[0]} were the most profitable moneyline bet ({fu(top[1]['units'])}) and the {bottom[0]} the least ({fu(bottom[1]['units'])}).")
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Regular season games only. Click any team for its season by season history, splits and results against every opponent.</p>
<section id="table"><h2>MLB team betting records, {cur}</h2>
<p>Sorted by moneyline units: 1 unit risked on the team in every game at the closing price.</p>
{table}
</section>
<section id="league"><h2>League results, {cur}</h2>
<div class="tr-stats"><div><b>{ha['w']}-{ha['l']}</b><span>home teams ({pct(ha['w'], ha['l'])})</span></div>
<div><b>{fa['w']}-{fa['l']}</b><span>moneyline favorites ({pct(fa['w'], fa['l'])}), {fu(fa['units'])}</span></div>
<div><b>{tot['o']}-{tot['u']}-{tot['p']}</b><span>over, under, push in all games ({pct(tot['o'], tot['u'])} overs)</span></div>
<div><b>{tot['avg_total']:.2f}</b><span>average closing total</span></div></div>
<p>The best over team was the {e(over_top[0])} ({over_top[1]['o']}-{over_top[1]['u']}-{over_top[1]['p']}); the best under team was the {e(under_top[0])} ({under_top[1]['o']}-{under_top[1]['u']}-{under_top[1]['p']}).</p>
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and closing lines for every regular season game come from the Bet Legend game database. Moneyline units risk 1 unit per game at the close. The run line record compares the final margin with the closing 1.5 run line. Over and under compare total runs with the closing total. Postseason games are excluded. These are market results, not BetLegend picks; our own graded picks are on the <a href="mlb-records.html">MLB betting record page</a>.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="mlb-team-over-under-records.html">MLB over/under records by team</a></li><li><a href="mlb-run-line-records.html">MLB run line records by team</a></li><li><a href="yankees-vs-red-sox-betting-history.html">Yankees vs Red Sox betting history</a></li><li><a href="dodgers-vs-padres-betting-history.html">Dodgers vs Padres betting history</a></li><li><a href="mlb-picks-today.html">MLB picks today</a></li><li><a href="mlb.html">MLB odds, stats and picks</a></li><li><a href="mlb-records.html">BetLegend MLB picks record</a></li><li><a href="how-to-bet-mlb-totals.html">How to bet MLB totals</a></li><li><a href="ev-calculator.html">Expected value calculator</a></li><li><a href="kelly-criterion.html">Kelly criterion calculator</a></li></ul>
</section>"""
    title = f"MLB Team Betting Records {cur}: Moneyline, Run Line & Over/Under"
    desc = (f"All 30 MLB teams' {cur} betting records at closing lines: moneyline units and ROI, run line and over/under records, "
            f"ranked, with links to every team's season by season history and splits.")
    h1 = f"MLB Team Betting Records {cur}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + HUB, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat(), "isPartOf": {"@type": "WebSite", "name": "BetLegend Picks", "url": SITE}}]
    crumbs = [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", None)]
    return shell(HUB, title, desc, h1, body, ld, crumbs, now_pt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-espn-check", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(PT)
    cur = a.season
    games, report, finished = verified_games(a.db, cur, check=not a.no_espn_check)
    cur_games = [g for g in games if g["season"] == cur]
    if not cur_games:
        sys.exit(f"no {cur} games")
    missing = [g for g in cur_games if g["hml"] is None or g["total"] is None or g["line"] is None]
    print(f"  {cur}: {len(cur_games)} games, {len(missing)} without a complete closing line set")
    if missing and len(missing) > 0.02 * len(cur_games):
        sys.exit(f"ABORT: {len(missing)} {cur} games lack closing lines; refresh the dataset first")
    if any(g["est"] for g in games):
        sys.exit("ABORT: estimated lines present")
    last_date = max(g["date"] for g in cur_games)
    season_aggs = {t: agg(team_rows(cur_games, t)) for t in TEAMS}
    out = {HUB: build_hub(games, cur, season_aggs, now_pt, finished, last_date)}
    meta = []
    for t in TEAMS:
        f, page, m = build_team(t, games, season_aggs, cur, now_pt, {"finished": finished})
        out[f] = page; meta.append(m)
    titles = [m["title"] for m in meta]
    assert len(set(titles)) == len(titles), "duplicate titles"
    for f, page in out.items():
        if a.dry_run:
            continue
        with open(os.path.join(ROOT, f), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page)
    print(f"[mlb_team_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages; {cur} through {last_date}; finished={finished}")
    for m in sorted(meta, key=lambda m: -m["units"])[:3]:
        print("   ", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
