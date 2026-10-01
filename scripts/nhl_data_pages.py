#!/usr/bin/env python3
"""NHL betting data pages (Phase 5 SEO, Oct 1 2026).

Builds from the Bet Legend game dataset (final scores, closing moneyline,
1.5 puck line and total for every regular season game since 2016-17):
  /nhl-team-betting-records.html   all 32 teams, current season
  /<team>-betting-record.html      one page per team (32)
  /nhl-puck-line-records.html      puck line by team, favorites and dogs, by season
  /nhl-home-away-records.html      home and road betting results by team
The current season is the newest one in which every team has played at least
5 regular season games (until then the finished season stays up, the same rule
as the NHL standings pages). The build refuses to write unless every team's
current season games match ESPN's schedule game for game. The paid dataset never
enters this repo.

    python scripts/nhl_data_pages.py --db DATASET.sqlite --prices DIR [--dry-run] [--no-espn-check]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import json
import os
import pickle
import sqlite3
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402  (shared page shell, tables and formatting)

ROOT = m.ROOT
SITE = m.SITE
HUB = "nhl-team-betting-records.html"
PL_HUB = "nhl-puck-line-records.html"
HA_HUB = "nhl-home-away-records.html"
FIRST_SEASON = 2016  # 2016-17
MIN_GP = 5
e, fu, froi, pct, fodds, fdate, cls, ordinal = m.e, m.fu, m.froi, m.pct, m.fodds, m.fdate, m.cls, m.ordinal

# name: (short, conference, division, espn abbreviation)
TEAMS = {
    "Boston Bruins": ("Bruins", "Eastern", "Atlantic", "bos"), "Buffalo Sabres": ("Sabres", "Eastern", "Atlantic", "buf"),
    "Detroit Red Wings": ("Red Wings", "Eastern", "Atlantic", "det"), "Florida Panthers": ("Panthers", "Eastern", "Atlantic", "fla"),
    "Montreal Canadiens": ("Canadiens", "Eastern", "Atlantic", "mtl"), "Ottawa Senators": ("Senators", "Eastern", "Atlantic", "ott"),
    "Tampa Bay Lightning": ("Lightning", "Eastern", "Atlantic", "tb"), "Toronto Maple Leafs": ("Maple Leafs", "Eastern", "Atlantic", "tor"),
    "Carolina Hurricanes": ("Hurricanes", "Eastern", "Metropolitan", "car"), "Columbus Blue Jackets": ("Blue Jackets", "Eastern", "Metropolitan", "cbj"),
    "New Jersey Devils": ("Devils", "Eastern", "Metropolitan", "nj"), "New York Islanders": ("Islanders", "Eastern", "Metropolitan", "nyi"),
    "New York Rangers": ("Rangers", "Eastern", "Metropolitan", "nyr"), "Philadelphia Flyers": ("Flyers", "Eastern", "Metropolitan", "phi"),
    "Pittsburgh Penguins": ("Penguins", "Eastern", "Metropolitan", "pit"), "Washington Capitals": ("Capitals", "Eastern", "Metropolitan", "wsh"),
    "Chicago Blackhawks": ("Blackhawks", "Western", "Central", "chi"), "Colorado Avalanche": ("Avalanche", "Western", "Central", "col"),
    "Dallas Stars": ("Stars", "Western", "Central", "dal"), "Minnesota Wild": ("Wild", "Western", "Central", "min"),
    "Nashville Predators": ("Predators", "Western", "Central", "nsh"), "St. Louis Blues": ("Blues", "Western", "Central", "stl"),
    "Utah Mammoth": ("Mammoth", "Western", "Central", "utah"), "Winnipeg Jets": ("Jets", "Western", "Central", "wpg"),
    "Anaheim Ducks": ("Ducks", "Western", "Pacific", "ana"), "Calgary Flames": ("Flames", "Western", "Pacific", "cgy"),
    "Edmonton Oilers": ("Oilers", "Western", "Pacific", "edm"), "Los Angeles Kings": ("Kings", "Western", "Pacific", "la"),
    "San Jose Sharks": ("Sharks", "Western", "Pacific", "sj"), "Seattle Kraken": ("Kraken", "Western", "Pacific", "sea"),
    "Vancouver Canucks": ("Canucks", "Western", "Pacific", "van"), "Vegas Golden Knights": ("Golden Knights", "Western", "Pacific", "vgk"),
}
# Utah Hockey Club (2024-25) became the Utah Mammoth. The Arizona Coyotes are a separate, inactive franchise and are not merged.
ALIASES = {"Utah Hockey Club": "Utah Mammoth"}
COVERAGE = {}


def slug(t):
    return t.lower().replace(".", "").replace(" ", "-")


def page_file(t):
    return f"{slug(t)}-betting-record.html"


def logo(t):
    return f"https://a.espncdn.com/i/teamlogos/nhl/500/{TEAMS[t][3]}.png"


def label(s):
    return f"{s}-{str(s + 1)[2:]}"


def season_of(date):
    d = dt.date.fromisoformat(date)
    return d.year if d.month >= 10 else d.year - 1  # the 2020 bubble playoffs (Aug, Sep) belong to 2019-20


def load_games(db):
    con = sqlite3.connect(db)
    out = []
    for blob, in con.execute("SELECT blob FROM games WHERE sport='NHL' AND date >= ?", (f"{FIRST_SEASON}-08-01",)):
        g = pickle.loads(blob)
        h = ALIASES.get(g["HomeTeam"], g["HomeTeam"]); a = ALIASES.get(g["AwayTeam"], g["AwayTeam"])
        if g.get("HomeScore") is None or g.get("AwayScore") is None:
            continue
        out.append({"season": season_of(g["Date"]), "date": g["Date"], "home": h, "away": a, "hs": int(g["HomeScore"]), "as": int(g["AwayScore"]),
                    "hml": g.get("HomeMoneyline"), "aml": g.get("AwayMoneyline"), "total": g.get("Total"),
                    # The dataset stores the NHL puck line from the away side (checked 2026-10-01: flipping it agrees
                    # with the dataset's own _calc_ATS on 13,264 of 13,264 graded games), so the home line is -Spread.
                    "line": None if g.get("Spread") is None else -g["Spread"],
                    "id": g.get("GameID"), "dn": None, "gt": g.get("GameTime"),
                    "est": bool(g.get("_ml_estimated") or g.get("_spread_estimated") or g.get("_total_estimated"))})
    return out


def regular_season(games):
    by = collections.defaultdict(list)
    for g in games:
        by[g["season"]].append(g)
    keep, report = [], {}
    for s, gs in sorted(by.items()):
        gs.sort(key=lambda g: g["date"])
        if s == 2019:  # 2019-20 regular season stopped March 11, 2020
            reg = [g for g in gs if g["date"] <= "2020-03-11"]; end = "2020-03-11"
        else:
            n = 56 if s == 2020 else 82
            cnt, nth = collections.Counter(), {}
            for g in gs:
                for t in (g["home"], g["away"]):
                    cnt[t] += 1
                    if cnt[t] == n:
                        nth[t] = g["date"]
            if len(nth) < 0.8 * len(cnt):
                reg, end = list(gs), "9999-12-31"
            else:
                end = collections.Counter(nth.values()).most_common(1)[0][0]
                played, reg = collections.Counter(), []
                for g in gs:
                    if g["date"] <= end or (played[g["home"]] < n and played[g["away"]] < n):
                        reg.append(g); played[g["home"]] += 1; played[g["away"]] += 1
        per = collections.Counter()
        for g in reg:
            per[g["home"]] += 1; per[g["away"]] += 1
        report[s] = (end, min(per.values()), max(per.values()), len(reg), len(gs) - len(reg))
        keep += [g for g in reg if g["home"] in TEAMS and g["away"] in TEAMS or s < 2024]
    return keep, report


def current_season(games):
    for s in sorted({g["season"] for g in games}, reverse=True):
        cnt = collections.Counter()
        for g in games:
            if g["season"] == s:
                cnt[g["home"]] += 1; cnt[g["away"]] += 1
        if all(cnt[t] >= MIN_GP for t in TEAMS):
            return s
    raise SystemExit("no complete season")


def verify_against_espn(cur_games, season):
    bad = []
    for t in TEAMS:
        url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{TEAMS[t][3]}/schedule?season={season + 1}&seasontype=2"
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


def attach_prices(games, price_dir):
    idx = {}
    for f in glob.glob(os.path.join(price_dir, "nhl_close_prices_*.json")):
        for ev in json.load(open(f)).values():
            h = ALIASES.get(ev["home"], ev["home"]); a = ALIASES.get(ev["away"], ev["away"])
            idx.setdefault((h, a, ev["hs"], ev["as"]), []).append(ev)
    n = collections.Counter()
    for g in games:
        gd = dt.date.fromisoformat(g["date"])
        ev = next((c for c in idx.get((g["home"], g["away"], g["hs"], g["as"]), [])
                   if abs((dt.date.fromisoformat(c["date"]) - gd).days) <= 1), None)
        c = (ev or {}).get("close") or {}
        hl = c.get("home_line")
        if hl is not None and abs(hl) == 1.5 and c.get("home_rl_price") and c.get("away_rl_price"):
            g["plp"] = (hl, c["home_rl_price"], c["away_rl_price"]); n["pl"] += 1
        if c.get("total") and c.get("over_price") and c.get("under_price"):
            g["oup"] = (c["total"], c["over_price"], c["under_price"]); n["ou"] += 1
    return n


def profit(price, won):
    if not won:
        return -1.0
    return price / 100.0 if price > 0 else 100.0 / abs(price)


def rows_for(games, team):
    out = []
    prev = {}
    for g in sorted((g for g in games if team in (g["home"], g["away"])), key=lambda g: g["date"]):
        r = m.team_rows([g], team)[0]
        r["b2b"] = (g["season"] in prev and (dt.date.fromisoformat(g["date"]) - dt.date.fromisoformat(prev[g["season"]][0])).days == 1)
        r["after"] = prev[g["season"]][1] if g["season"] in prev else None
        prev[g["season"]] = (g["date"], r["won"])
        r["pl_units"] = None
        if "plp" in g:
            hl, hp, ap = g["plp"]
            line = hl if r["home"] else -hl
            r["pl_units"] = profit(hp if r["home"] else ap, r["rf"] - r["ra"] + line > 0)
        out.append(r)
    return out


def u_cell(rows, key="pl_units", ok=True):
    vals = [r[key] for r in rows if r.get(key) is not None]
    if not ok or not vals or len(vals) < 0.95 * len(rows):
        return '<td class="na">not priced</td>'
    u = sum(vals)
    return f'<td class="{cls(u)}">{fu(u)}</td>'


EXTRA_CSS = "<style>.tr td.na{color:#7d8592;font-size:.8rem}</style>"


def season_tbl(rows, seasons):
    trs = []
    for s in seasons:
        rs = [r for r in rows if r["season"] == s]
        if not rs:
            continue
        a = m.agg(rs)
        trs.append(f"<tr><td>{label(s)}</td><td>{a['w']}-{a['l']}</td><td class=\"{cls(a['units'])}\">{fu(a['units'])}</td><td>{froi(a['roi'])}</td>"
                   f"<td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{a['avg_total']:.2f}</td><td>{a['rpg']:.2f}</td><td>{a['rapg']:.2f}</td></tr>")
    a = m.agg([r for r in rows if r["season"] in seasons])
    trs.append(f"<tr><td><strong>All {len(seasons)} seasons</strong></td><td><strong>{a['w']}-{a['l']}</strong></td><td class=\"{cls(a['units'])}\"><strong>{fu(a['units'])}</strong></td>"
               f"<td>{froi(a['roi'])}</td><td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{a['avg_total']:.2f}</td><td>{a['rpg']:.2f}</td><td>{a['rapg']:.2f}</td></tr>")
    return ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Record</th><th>ML units</th><th>ML ROI</th><th>Puck line</th>'
            '<th>O/U/P</th><th>Avg total</th><th>Goals/G</th><th>Allowed/G</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")


def split_tbl(splits, ok):
    trs = []
    for name, rs in splits:
        if not rs:
            continue
        a = m.agg(rs)
        trs.append(f"<tr><td class=\"t\">{e(name)}</td><td>{a['n']}</td><td>{a['w']}-{a['l']}</td><td class=\"{cls(a['units'])}\">{fu(a['units'])}</td>"
                   f"<td>{froi(a['roi'])}</td><td>{a['cov']}-{a['ncov']}</td>{u_cell(rs, ok=ok)}<td>{a['o']}-{a['u']}-{a['p']}</td></tr>")
    return ('<div class="tr-wrap"><table><thead><tr><th>Situation</th><th>Games</th><th>Record</th><th>ML units</th><th>ML ROI</th>'
            '<th>Puck line</th><th>PL units</th><th>O/U/P</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")


def build_team(team, games, cur, aggs, now_pt, finished, pl_ok):
    short, conf, div, _ = TEAMS[team]
    rows = rows_for(games, team)
    seasons = sorted({r["season"] for r in rows}, reverse=True)
    cr = [r for r in rows if r["season"] == cur]
    a = m.agg(cr)
    file = page_file(team)
    unit_rank = sorted(aggs, key=lambda t: -aggs[t]["units"]).index(team) + 1
    over_rank = sorted(aggs, key=lambda t: -(aggs[t]["o"] / max(1, aggs[t]["o"] + aggs[t]["u"]))).index(team) + 1
    sp = [("Home", [r for r in cr if r["home"]]), ("Road", [r for r in cr if not r["home"]]),
          ("As favorite", [r for r in cr if r["fav"]]), ("As underdog", [r for r in cr if r["ml"] is not None and not r["fav"]]),
          ("Favorite of -150 or shorter", [r for r in cr if r["ml"] is not None and r["ml"] <= -150]),
          ("Underdog of +130 or longer", [r for r in cr if r["ml"] is not None and r["ml"] >= 130]),
          ("Second night of a back to back", [r for r in cr if r["b2b"]]), ("With at least a day of rest", [r for r in cr if not r["b2b"]]),
          ("After a win", [r for r in cr if r["after"] is True]), ("After a loss", [r for r in cr if r["after"] is False]),
          (f"vs {div} Division", [r for r in cr if TEAMS.get(r["opp"], ("", "", ""))[2] == div]),
          (f"vs {conf} Conference", [r for r in cr if TEAMS.get(r["opp"], ("", ""))[1] == conf]),
          ("vs the other conference", [r for r in cr if TEAMS.get(r["opp"], ("", ""))[1] not in ("", conf)])]
    sa = {n: m.agg(rs) for n, rs in sp if rs}
    home, road, fav, dog, b2b = sa["Home"], sa["Road"], sa.get("As favorite"), sa.get("As underdog"), sa.get("Second night of a back to back")
    months = collections.OrderedDict()
    for r in cr:
        months.setdefault(dt.date.fromisoformat(r["date"]).strftime("%B"), []).append(r)
    opp = collections.defaultdict(list)
    for r in cr:
        opp[r["opp"]].append(r)
    def opp_link(o):
        return f'<a href="{page_file(o)}">{e(o)}</a>' if o in TEAMS else e(o)
    h2h = "".join(f"<tr><td class=\"t\">{opp_link(o)}</td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td>"
                  f"<td class=\"{cls(x['units'])}\">{fu(x['units'])}</td><td>{x['cov']}-{x['ncov']}</td><td>{x['o']}-{x['u']}-{x['p']}</td></tr>"
                  for o, x in sorted(((o, m.agg(rs)) for o, rs in opp.items()), key=lambda kv: (-kv[1]["n"], kv[0])))
    h2h_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Opponent</th><th>Games</th><th>Record</th><th>ML units</th><th>Puck line</th><th>O/U/P</th></tr></thead><tbody>'
               + h2h + "</tbody></table></div>")
    last = []
    for r in cr[-15:][::-1]:
        ou = {"O": "Over", "U": "Under", "P": "Push", None: "no line"}[r["ou"]]
        pl = "no line" if r["line"] is None else f"{r['line']:+.1f}"
        tot = "no line" if r["total"] is None else f"{r['total']:g}"
        last.append(f"<tr><td>{fdate(r['date'], False)}</td><td class=\"t\">{'vs' if r['home'] else 'at'} {e(TEAMS.get(r['opp'], (r['opp'],))[0])}</td>"
                    f"<td class=\"{'w' if r['won'] else 'l'}\">{'W' if r['won'] else 'L'} {r['rf']}-{r['ra']}</td><td>{fodds(r['ml'])}</td><td>{pl}</td><td>{tot}</td><td>{ou}</td>"
                    f"<td class=\"{cls(r['units'] or 0)}\">{'' if r['units'] is None else fu(r['units'])}</td></tr>")
    last_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Close ML</th><th>Puck line</th><th>Total</th><th>O/U</th><th>ML units</th></tr></thead><tbody>'
                + "".join(last) + "</tbody></table></div>")
    best = max(seasons, key=lambda s: m.agg([r for r in rows if r["season"] == s])["units"])
    worst = min(seasons, key=lambda s: m.agg([r for r in rows if r["season"] == s])["units"])
    bs, ws = m.agg([r for r in rows if r["season"] == best]), m.agg([r for r in rows if r["season"] == worst])
    allr = m.agg(rows)
    lean = "over" if a["o"] > a["u"] else ("under" if a["u"] > a["o"] else "neither way")
    when = f"the {label(cur)} regular season" if finished else f"{label(cur)} so far (through {fdate(cr[-1]['date'])})"
    lead = (f"The {short} went {a['w']}-{a['l']} in {when}. One unit on them at the closing moneyline in every game returned {fu(a['units'])} "
            f"({froi(a['roi'])} ROI), {ordinal(unit_rank)} of 32 NHL teams. They were {a['cov']}-{a['ncov']} on the puck line and "
            f"{a['o']}-{a['u']}-{a['p']} against the total, leaning {lean} ({ordinal(over_rank)} in over percentage).")
    stats = (f'<div class="tr-stats"><div><b>{a["w"]}-{a["l"]}</b><span>{label(cur)} record (OT and shootouts count)</span></div>'
             f'<div><b class="{cls(a["units"])}">{fu(a["units"])}</b><span>moneyline units, {ordinal(unit_rank)} in the NHL</span></div>'
             f'<div><b>{a["cov"]}-{a["ncov"]}</b><span>puck line ({pct(a["cov"], a["ncov"])})</span></div>'
             f'<div><b>{a["o"]}-{a["u"]}-{a["p"]}</b><span>over, under, push ({pct(a["o"], a["u"])} overs)</span></div></div>')
    faq = [(f"What is the {short} betting record in {label(cur)}?",
            f"{a['w']}-{a['l']} straight up, {fu(a['units'])} on the moneyline at the close, {a['cov']}-{a['ncov']} on the puck line and {a['o']}-{a['u']}-{a['p']} on totals ({when})."),
           (f"How do the {short} do at home and on the road?", f"Home {home['w']}-{home['l']} ({fu(home['units'])}); road {road['w']}-{road['l']} ({fu(road['units'])})."),
           (f"How do the {short} do on the second night of a back to back?",
            (f"{b2b['w']}-{b2b['l']} for {fu(b2b['units'])} on the moneyline in {b2b['n']} games." if b2b else "They had no back to back games in this span.")),
           (f"Are the {short} better as a favorite or an underdog?",
            (f"As a favorite {fav['w']}-{fav['l']} ({fu(fav['units'])}). " if fav else "") + (f"As an underdog {dog['w']}-{dog['l']} ({fu(dog['units'])})." if dog else "")),
           (f"What was the {short}' best betting season since {label(seasons[-1])}?",
            f"{label(best)}: {bs['w']}-{bs['l']}, {fu(bs['units'])}. Worst: {label(worst)}, {ws['w']}-{ws['l']}, {fu(ws['units'])}. All {len(seasons)} seasons: {allr['w']}-{allr['l']}, {fu(allr['units'])}.")]
    rivals = [t for t in TEAMS if t != team and TEAMS[t][2] == div]
    related = [(f"{t} betting record", page_file(t)) for t in rivals] + [
        ("All 32 NHL team betting records", HUB), ("NHL puck line records", PL_HUB), ("NHL home and road betting records", HA_HUB),
        ("NHL home and away splits", "nhl-home-away-splits.html"), ("NHL team trends", "nhl-team-trends.html"),
        ("NHL slate, odds and analysis", "nhl.html"), ("BetLegend NHL picks record", "nhl-records.html")]
    related_html = '<ul class="links">' + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in related if os.path.isfile(os.path.join(ROOT, h)) or h in (HUB, PL_HUB, HA_HUB) or h.endswith("-betting-record.html")) + "</ul>"
    import espn_verify
    note = espn_verify.coverage_note(COVERAGE, team, label) + " " if COVERAGE else ""
    note += "Utah's history starts with the 2024-25 season (Utah Hockey Club, renamed the Mammoth); the Arizona Coyotes are a separate franchise and are not included. " if team == "Utah Mammoth" else ""
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing lines, regular season games only, {label(seasons[-1])} to {label(seasons[0])}. <a href="#method">How these numbers are calculated</a>.</p>
<ul class="tr-jump"><li><a href="#season">{label(cur)} summary</a></li><li><a href="#history">Season by season</a></li><li><a href="#splits">Splits</a></li><li><a href="#opponents">vs every opponent</a></li><li><a href="#recent">Last 15 games</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="season"><h2>{e(short)} {label(cur)} betting summary</h2>
{stats}
<p>At home the {e(short)} were {home['w']}-{home['l']} ({fu(home['units'])}); on the road {road['w']}-{road['l']} ({fu(road['units'])}).</p>
</section>
<section id="history"><h2>{e(short)} betting record by season</h2>
<p>Moneyline units assume 1 unit on the {e(short)} every game at the closing price. Best season in this span: {label(best)} ({fu(bs['units'])}); worst: {label(worst)} ({fu(ws['units'])}).</p>
{season_tbl(rows, seasons)}
</section>
<section id="splits"><h2>{e(short)} betting splits, {label(cur)}</h2>
{split_tbl(sp, pl_ok)}
<h3>By month</h3>
{split_tbl(list(months.items()), pl_ok)}
</section>
<section id="opponents"><h2>{e(short)} record against every opponent, {label(cur)}</h2>
{h2h_tbl}
</section>
<section id="recent"><h2>Last 15 {e(short)} games with closing lines</h2>
{last_tbl}
</section>
<section id="faq"><h2>{e(short)} betting FAQ</h2>
{"".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)}
</section>
<section id="method"><h2>Methodology</h2>
<p>{e(note)}Final scores, closing moneylines, the closing 1.5 puck line and closing totals for every regular season game come from the Bet Legend game database; playoff games are excluded. Results include overtime and shootouts, as sportsbooks grade them, and every game is checked against ESPN's official final score. Moneyline units risk 1 unit at the close. Puck line units (where shown) use the DraftKings closing puck line and price published by ESPN. A back to back is a game played the day after the previous one. These are market results, not BetLegend picks; our own picks are on the <a href="nhl-records.html">NHL betting record page</a>.</p>
</section>
<section id="related"><h2>Related NHL betting data</h2>
{related_html}
</section>"""
    title = f"{team} Betting Record {label(cur)}: Moneyline, Puck Line, O/U"
    desc = (f"{team} {label(cur)} betting record: {a['w']}-{a['l']}, {fu(a['units'])} on the moneyline, {a['cov']}-{a['ncov']} puck line, "
            f"{a['o']}-{a['u']}-{a['p']} over/under, with home/road, back to back and favorite/underdog splits since {label(seasons[-1])}.")
    h1 = f"{team} Betting Record {label(cur)}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + file, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat(), "about": {"@type": "SportsTeam", "name": team, "sport": "Ice Hockey"}},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("NHL", "nhl.html"), ("NHL Team Betting Records", HUB), (f"{short} Betting Record", None)]
    return file, m.shell(file, title, desc, h1, EXTRA_CSS + body, ld, crumbs, now_pt, head_img=logo(team)), title


def build_hub(cur, aggs, now_pt, finished):
    ranked = sorted(aggs.items(), key=lambda kv: -kv[1]["units"])
    trs = "".join(f"<tr><td>{i}</td><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td><td>{a['w']}-{a['l']}</td><td class=\"{cls(a['units'])}\">{fu(a['units'])}</td>"
                  f"<td>{froi(a['roi'])}</td><td>{a['cov']}-{a['ncov']}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{pct(a['o'], a['u'])}</td></tr>"
                  for i, (t, a) in enumerate(ranked, 1))
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>Record</th><th>ML units</th><th>ROI</th><th>Puck line</th><th>O/U/P</th><th>Over %</th></tr></thead><tbody>'
             + trs + "</tbody></table></div>")
    top, bot = ranked[0], ranked[-1]
    when = f"the {label(cur)} regular season" if finished else f"{label(cur)} so far"
    lead = (f"Every NHL team's betting record for {when} at closing lines: moneyline units, puck line and over/under. "
            f"The {top[0]} were the most profitable moneyline bet ({fu(top[1]['units'])}); the {bot[0]} the least ({fu(bot[1]['units'])}).")
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Regular season games only; results include overtime and shootouts. Click a team for its season by season history and splits.</p>
<section id="table"><h2>NHL team betting records, {label(cur)}</h2>
<p>Sorted by moneyline units: 1 unit on the team every game at the closing price.</p>
{table}
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and closing lines for every regular season game come from the Bet Legend game database. The current season switches over once every team has played {MIN_GP} games. These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="{PL_HUB}">NHL puck line records</a></li><li><a href="{HA_HUB}">NHL home and road betting records</a></li><li><a href="nhl-home-away-splits.html">NHL home and away splits</a></li><li><a href="nhl-team-trends.html">NHL team trends</a></li><li><a href="nhl.html">NHL slate, odds and analysis</a></li><li><a href="nhl-records.html">BetLegend NHL picks record</a></li></ul>
</section>"""
    title = f"NHL Team Betting Records {label(cur)}: Moneyline, Puck Line & O/U"
    desc = f"All 32 NHL teams' {label(cur)} betting records at closing lines: moneyline units and ROI, puck line and over/under, ranked, with a page for every team."
    h1 = f"NHL Team Betting Records {label(cur)}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + HUB, "description": desc, "dateModified": now_pt.replace(microsecond=0).isoformat()}]
    return m.shell(HUB, title, desc, h1, EXTRA_CSS + body, ld, [("Home", "/"), ("NHL", "nhl.html"), ("NHL Team Betting Records", None)], now_pt)


def build_pl_hub(games, cur, now_pt, finished, pl_ok):
    data = []
    for t in TEAMS:
        rs = rows_for([g for g in games if g["season"] == cur], t)
        fav = [r for r in rs if r["line"] is not None and r["line"] < 0]; dog = [r for r in rs if r["line"] is not None and r["line"] > 0]
        data.append((t, m.agg(rs), rs, fav, dog))
    data.sort(key=lambda x: -(x[1]["cov"] / max(1, x[1]["cov"] + x[1]["ncov"])))
    trs = []
    for i, (t, a, rs, fav, dog) in enumerate(data, 1):
        fa, da = m.agg(fav), m.agg(dog)
        h = m.agg([r for r in rs if r["home"]]); rd = m.agg([r for r in rs if not r["home"]])
        trs.append(f"<tr><td>{i}</td><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td><td>{a['cov']}-{a['ncov']}</td><td>{pct(a['cov'], a['ncov'])}</td>{u_cell(rs, ok=pl_ok)}"
                   f"<td>{fa['cov']}-{fa['ncov']}</td>{u_cell(fav, ok=pl_ok)}<td>{da['cov']}-{da['ncov']}</td>{u_cell(dog, ok=pl_ok)}<td>{h['cov']}-{h['ncov']}</td><td>{rd['cov']}-{rd['ncov']}</td></tr>")
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>Puck line</th><th>Cover %</th><th>PL units</th><th>As -1.5 fav</th><th>Fav units</th>'
             '<th>As +1.5 dog</th><th>Dog units</th><th>Home</th><th>Road</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")
    srows = []
    for s in sorted({g["season"] for g in games}, reverse=True):
        gs = [g for g in games if g["season"] == s and g["line"] is not None and abs(g["line"]) == 1.5]
        fc = sum(((g["hs"] - g["as"]) if g["line"] < 0 else (g["as"] - g["hs"])) >= 2 for g in gs)
        hf = [g for g in gs if g["line"] < 0]; hfc = sum(g["hs"] - g["as"] >= 2 for g in hf)
        srows.append(f"<tr><td>{label(s)}</td><td>{len(gs)}</td><td>{fc}-{len(gs) - fc}</td><td>{pct(fc, len(gs) - fc)}</td><td>{hfc}-{len(hf) - hfc}</td><td>{pct(hfc, len(hf) - hfc)}</td></tr>")
    stbl = ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Games</th><th>-1.5 favorites</th><th>Cover %</th><th>Home -1.5 favorites</th><th>Cover %</th></tr></thead><tbody>'
            + "".join(srows) + "</tbody></table></div>")
    seasons = sorted({g["season"] for g in games}, reverse=True)[:6]
    mrows = "".join(f"<tr><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td>" + "".join(
        f"<td>{(lambda a: pct(a['cov'], a['ncov']))(m.agg(m.team_rows([g for g in games if g['season'] == s], t)))}</td>" for s in seasons) + "</tr>"
        for t in sorted(TEAMS, key=lambda t: TEAMS[t][0]))
    matrix = ('<div class="tr-wrap"><table><thead><tr><th>Team</th>' + "".join(f"<th>{label(s)}</th>" for s in seasons) + "</tr></thead><tbody>" + mrows + "</tbody></table></div>")
    top, bot = data[0], data[-1]
    curg = [g for g in games if g["season"] == cur and g["line"] is not None and abs(g["line"]) == 1.5]
    fc = sum(((g["hs"] - g["as"]) if g["line"] < 0 else (g["as"] - g["hs"])) >= 2 for g in curg)
    lead = (f"Every NHL team's puck line record for {label(cur)} at the closing 1.5 line. The {top[0]} covered most often ({top[1]['cov']}-{top[1]['ncov']}) and the "
            f"{bot[0]} least ({bot[1]['cov']}-{bot[1]['ncov']}). Favorites laying 1.5 goals covered {pct(fc, len(curg) - fc)} of the time.")
    pnote = "Puck line units use the DraftKings closing puck line and price published by ESPN." if pl_ok else "Units are shown only when at least 95% of games have a published closing puck line price."
    faq = [(f"Which NHL team has the best puck line record in {label(cur)}?", f"The {top[0]}: {top[1]['cov']}-{top[1]['ncov']} ({pct(top[1]['cov'], top[1]['ncov'])})."),
           ("How often do NHL favorites cover -1.5?", f"In {label(cur)}, -1.5 favorites covered {fc} of {len(curg)} games ({pct(fc, len(curg) - fc)}). Empty net goals late in close games are a big part of why favorites win by two."),
           ("Does overtime count for the puck line?", "Yes. Sportsbooks grade the puck line on the final score including overtime and the shootout, so a shootout win is a one goal win.")]
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing puck lines, regular season only. {e(pnote)}</p>
<section id="teams"><h2>NHL puck line records by team, {label(cur)}</h2>
{table}
</section>
<section id="seasons"><h2>Puck line results by season</h2>
{stbl}
</section>
<section id="history"><h2>Team puck line cover % by season</h2>
{matrix}
</section>
<section id="faq"><h2>NHL puck line FAQ</h2>
{"".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)}
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and the closing 1.5 puck line for every regular season game since 2016-17 come from the Bet Legend game database. A side covers when its final margin, including overtime and the shootout, plus its puck line is above zero. {e(pnote)} These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="{HUB}">NHL team betting records</a></li><li><a href="{HA_HUB}">NHL home and road betting records</a></li><li><a href="nhl-team-trends.html">NHL team trends</a></li><li><a href="nhl.html">NHL slate, odds and analysis</a></li><li><a href="nhl-records.html">BetLegend NHL picks record</a></li></ul>
</section>"""
    title = f"NHL Puck Line Records {label(cur)}: Cover % by Team, Favorites & Dogs"
    desc = f"Every NHL team's {label(cur)} puck line record at the closing 1.5 line: cover %, units, as favorite and underdog, home and road, and cover % by season since 2016-17."
    h1 = f"NHL Puck Line Records {label(cur)}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + PL_HUB, "description": desc, "dateModified": now_pt.replace(microsecond=0).isoformat()},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    return m.shell(PL_HUB, title, desc, h1, EXTRA_CSS + body, ld, [("Home", "/"), ("NHL", "nhl.html"), ("NHL Team Betting Records", HUB), ("Puck Line Records", None)], now_pt)


def build_ha_hub(games, cur, now_pt, finished):
    trs = []
    data = []
    for t in TEAMS:
        rs = rows_for([g for g in games if g["season"] == cur], t)
        h = m.agg([r for r in rs if r["home"]]); rd = m.agg([r for r in rs if not r["home"]])
        data.append((t, h, rd))
    data.sort(key=lambda x: -x[1]["units"])
    for i, (t, h, rd) in enumerate(data, 1):
        trs.append(f"<tr><td>{i}</td><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td><td>{h['w']}-{h['l']}</td><td class=\"{cls(h['units'])}\">{fu(h['units'])}</td>"
                   f"<td>{h['cov']}-{h['ncov']}</td><td>{h['o']}-{h['u']}-{h['p']}</td><td>{rd['w']}-{rd['l']}</td><td class=\"{cls(rd['units'])}\">{fu(rd['units'])}</td>"
                   f"<td>{rd['cov']}-{rd['ncov']}</td><td>{rd['o']}-{rd['u']}-{rd['p']}</td></tr>")
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>Home record</th><th>Home ML units</th><th>Home PL</th><th>Home O/U/P</th>'
             '<th>Road record</th><th>Road ML units</th><th>Road PL</th><th>Road O/U/P</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")
    srows = []
    for s in sorted({g["season"] for g in games}, reverse=True):
        gs = [g for g in games if g["season"] == s]
        hw = sum(g["hs"] > g["as"] for g in gs)
        hu = sum(m.ml_profit(g["hml"], g["hs"] > g["as"]) for g in gs if g["hml"])
        ru = sum(m.ml_profit(g["aml"], g["as"] > g["hs"]) for g in gs if g["aml"])
        srows.append(f"<tr><td>{label(s)}</td><td>{len(gs)}</td><td>{hw}-{len(gs) - hw}</td><td>{pct(hw, len(gs) - hw)}</td><td class=\"{cls(hu)}\">{fu(hu)}</td><td class=\"{cls(ru)}\">{fu(ru)}</td></tr>")
    stbl = ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Games</th><th>Home teams</th><th>Home win %</th><th>All home ML units</th><th>All road ML units</th></tr></thead><tbody>'
            + "".join(srows) + "</tbody></table></div>")
    top = data[0]; road_top = max(data, key=lambda x: x[2]["units"])
    lead = (f"How every NHL team did at home and on the road in {label(cur)}, at closing lines. The {top[0]} were the best home moneyline bet ({fu(top[1]['units'])}), "
            f"the {road_top[0]} the best road bet ({fu(road_top[2]['units'])}).")
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Regular season games only, results include overtime and shootouts. For goals, shots and special teams by venue see the <a href="nhl-home-away-splits.html">NHL home and away splits</a>.</p>
<section id="teams"><h2>NHL home and road betting records, {label(cur)}</h2>
<p>Sorted by home moneyline units.</p>
{table}
</section>
<section id="seasons"><h2>Home ice by season</h2>
{stbl}
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and closing lines for every regular season game since 2016-17 come from the Bet Legend game database. Moneyline units risk 1 unit at the close. These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="{HUB}">NHL team betting records</a></li><li><a href="{PL_HUB}">NHL puck line records</a></li><li><a href="nhl-home-away-splits.html">NHL home and away splits</a></li><li><a href="nhl.html">NHL slate, odds and analysis</a></li></ul>
</section>"""
    title = f"NHL Home and Road Betting Records {label(cur)} by Team"
    desc = f"Every NHL team's {label(cur)} home and road betting record at closing lines: moneyline units, puck line and over/under by venue, plus home ice results by season since 2016-17."
    h1 = f"NHL Home and Road Betting Records {label(cur)}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + HA_HUB, "description": desc, "dateModified": now_pt.replace(microsecond=0).isoformat()}]
    return m.shell(HA_HUB, title, desc, h1, EXTRA_CSS + body, ld, [("Home", "/"), ("NHL", "nhl.html"), ("NHL Team Betting Records", HUB), ("Home and Road Records", None)], now_pt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-espn-check", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(m.PT)
    import espn_verify
    raw = load_games(a.db)
    # current season = newest with every team at MIN_GP games or more, decided on the raw rows first
    cur = current_season([g for g in raw if g["home"] in TEAMS and g["away"] in TEAMS])
    if a.no_espn_check:
        games, report = regular_season(raw); finished = True; COVERAGE.clear()
    else:
        games, dropped, cov, cur_bad, finished = espn_verify.verify(
            raw, "nhl", {t: TEAMS[t][3] for t in TEAMS}, ALIASES, lambda s: s + 1, cur, TEAMS)
        if cur_bad:
            sys.exit(f"ABORT: {label(cur)} games disagree with ESPN: {cur_bad}")
        COVERAGE.clear(); COVERAGE.update(cov)
        by = collections.defaultdict(lambda: [0, 0])
        for (t, s), (k, n, dr, mi) in cov.items():
            by[s][0] += dr; by[s][1] += mi
        for s in sorted(by):
            print(f"  {label(s)}: verified against ESPN; team rows dropped {by[s][0]}, team games missing {by[s][1]}")
        print(f"  {label(cur)}: every team matches ESPN game for game; finished={finished}")
    cg = [g for g in games if g["season"] == cur]
    missing = [g for g in cg if g["hml"] is None or g["line"] is None or g["total"] is None]
    if len(missing) > 0.02 * len(cg) or any(g["est"] for g in cg):
        sys.exit(f"ABORT: {len(missing)} {label(cur)} games lack closing lines or carry estimates")
    st = attach_prices(games, a.prices)
    cov = sum("plp" in g for g in cg) / len(cg)
    pl_ok = cov >= 0.95
    print(f"  prices: puck line {st['pl']}, totals {st['ou']}; {label(cur)} puck line price coverage {cov:.1%}")
    aggs = {t: m.agg(rows_for(cg, t)) for t in TEAMS}
    out = {HUB: build_hub(cur, aggs, now_pt, finished), PL_HUB: build_pl_hub(games, cur, now_pt, finished, pl_ok), HA_HUB: build_ha_hub(games, cur, now_pt, finished)}
    titles = []
    for t in TEAMS:
        f, page, title = build_team(t, games, cur, aggs, now_pt, finished, pl_ok)
        out[f] = page; titles.append(title)
    assert len(set(titles)) == len(titles)
    if not a.dry_run:
        for f, page in out.items():
            with open(os.path.join(ROOT, f), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(page)
    print(f"[nhl_data_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages for {label(cur)} (finished={finished})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
