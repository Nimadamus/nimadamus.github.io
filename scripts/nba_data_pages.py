#!/usr/bin/env python3
"""NBA betting data pages (Phase 5 SEO, Oct 1 2026).

Builds from the Bet Legend game dataset (final scores, closing moneyline, spread and
total for every regular season game since 2016-17), keeping only games ESPN records
with the same teams and final score (scripts/espn_verify.py):
  /nba-team-betting-records.html    all 30 teams, current season, ranked by ATS
  /<team>-betting-record.html        one page per team (30)
  /nba-ats-records.html              against the spread by team, favorite/underdog, home/road, by season
  /nba-over-under-records.html       totals by team and season
  /nba-back-to-back-records.html     second night of back to backs, by season and team
The current season is the newest one in which every team has played 5 regular season
games; until then the finished season stays up. The dataset stores the NBA spread from
the AWAY side (flipping it agrees with the dataset's own ATS grading on every graded
game, checked 2026-10-01), so the home line here is -Spread.

    python scripts/nba_data_pages.py --db DATASET.sqlite --prices DIR [--dry-run]
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402  (shared page shell, aggregation and formatting)
import espn_verify  # noqa: E402

ROOT, SITE = m.ROOT, m.SITE
HUB, ATS_HUB, OU_HUB, B2B_HUB = "nba-team-betting-records.html", "nba-ats-records.html", "nba-over-under-records.html", "nba-back-to-back-records.html"
FIRST_SEASON = 2016
MIN_GP = 5
SPREAD_FROM_CLOSE = 2024
e, fu, froi, pct, fodds, fdate, cls, ordinal = m.e, m.fu, m.froi, m.pct, m.fodds, m.fdate, m.cls, m.ordinal

# name: (short, conference, division, espn abbreviation)
TEAMS = {
    "Boston Celtics": ("Celtics", "Eastern", "Atlantic", "bos"), "Brooklyn Nets": ("Nets", "Eastern", "Atlantic", "bkn"),
    "New York Knicks": ("Knicks", "Eastern", "Atlantic", "ny"), "Philadelphia 76ers": ("76ers", "Eastern", "Atlantic", "phi"),
    "Toronto Raptors": ("Raptors", "Eastern", "Atlantic", "tor"), "Chicago Bulls": ("Bulls", "Eastern", "Central", "chi"),
    "Cleveland Cavaliers": ("Cavaliers", "Eastern", "Central", "cle"), "Detroit Pistons": ("Pistons", "Eastern", "Central", "det"),
    "Indiana Pacers": ("Pacers", "Eastern", "Central", "ind"), "Milwaukee Bucks": ("Bucks", "Eastern", "Central", "mil"),
    "Atlanta Hawks": ("Hawks", "Eastern", "Southeast", "atl"), "Charlotte Hornets": ("Hornets", "Eastern", "Southeast", "cha"),
    "Miami Heat": ("Heat", "Eastern", "Southeast", "mia"), "Orlando Magic": ("Magic", "Eastern", "Southeast", "orl"),
    "Washington Wizards": ("Wizards", "Eastern", "Southeast", "wsh"), "Denver Nuggets": ("Nuggets", "Western", "Northwest", "den"),
    "Minnesota Timberwolves": ("Timberwolves", "Western", "Northwest", "min"), "Oklahoma City Thunder": ("Thunder", "Western", "Northwest", "okc"),
    "Portland Trail Blazers": ("Trail Blazers", "Western", "Northwest", "por"), "Utah Jazz": ("Jazz", "Western", "Northwest", "utah"),
    "Golden State Warriors": ("Warriors", "Western", "Pacific", "gs"), "Los Angeles Clippers": ("Clippers", "Western", "Pacific", "lac"),
    "Los Angeles Lakers": ("Lakers", "Western", "Pacific", "lal"), "Phoenix Suns": ("Suns", "Western", "Pacific", "phx"),
    "Sacramento Kings": ("Kings", "Western", "Pacific", "sac"), "Dallas Mavericks": ("Mavericks", "Western", "Southwest", "dal"),
    "Houston Rockets": ("Rockets", "Western", "Southwest", "hou"), "Memphis Grizzlies": ("Grizzlies", "Western", "Southwest", "mem"),
    "New Orleans Pelicans": ("Pelicans", "Western", "Southwest", "no"), "San Antonio Spurs": ("Spurs", "Western", "Southwest", "sa"),
}
ALIASES = {"LA Clippers": "Los Angeles Clippers"}
COVERAGE = {}


def page_file(t):
    return f"{t.lower().replace('.', '').replace(' ', '-')}-betting-record.html"


def logo(t):
    return f"https://a.espncdn.com/i/teamlogos/nba/500/{TEAMS[t][3]}.png"


def label(s):
    return f"{s}-{str(s + 1)[2:]}"


def season_of(date):
    d = dt.date.fromisoformat(date)
    if d.year == 2020 and d.month <= 11:  # the 2019-20 season finished in the October 2020 bubble
        return 2019
    return d.year if d.month >= 10 else d.year - 1


def load_games(db):
    out = []
    for blob, in sqlite3.connect(db).execute("SELECT blob FROM games WHERE sport='NBA' AND date >= ?", (f"{FIRST_SEASON}-09-01",)):
        g = pickle.loads(blob)
        if g.get("HomeScore") is None or g.get("AwayScore") is None:
            continue
        h = ALIASES.get(g["HomeTeam"], g["HomeTeam"]); a = ALIASES.get(g["AwayTeam"], g["AwayTeam"])
        out.append({"season": season_of(g["Date"]), "date": g["Date"], "home": h, "away": a, "hs": int(g["HomeScore"]), "as": int(g["AwayScore"]),
                    "hml": g.get("HomeMoneyline"), "aml": g.get("AwayMoneyline"), "total": g.get("Total"),
                    "line": None if g.get("Spread") is None else -g["Spread"],
                    "id": g.get("GameID"), "dn": None, "gt": g.get("GameTime"),
                    "est": bool(g.get("_ml_estimated") or g.get("_spread_estimated") or g.get("_total_estimated"))})
    return out


def drop_cup_finals(games):
    """The NBA Cup championship game is a regular season game on ESPN's schedule but does not count in
    the standings or team records, so it is left out. Found per season from the teams with an 83rd game
    and ESPN's note on that game ("NBA Cup Championship" / "In-Season Tournament Championship")."""
    import urllib.request
    keep, dropped = [], []
    by = collections.defaultdict(list)
    for g in games:
        by[g["season"]].append(g)
    for s, gs in by.items():
        cnt = collections.Counter()
        for g in gs:
            cnt[g["home"]] += 1; cnt[g["away"]] += 1
        over = {t for t, c in cnt.items() if c > 82}
        bad = set()
        for g in gs:
            if g["home"] in over and g["away"] in over and g["date"][5:7] == "12":
                d = json.load(urllib.request.urlopen(
                    f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={g['date'].replace('-', '')}", timeout=30))
                for ev in d.get("events", []):
                    c = ev["competitions"][0]
                    names = {ALIASES.get(x["team"]["displayName"], x["team"]["displayName"]) for x in c["competitors"]}
                    if names == {g["home"], g["away"]} and any("Championship" in (n.get("headline") or "") for n in c.get("notes", [])):
                        bad.add(id(g))
        for g in gs:
            (dropped if id(g) in bad else keep).append(g)
    for g in dropped:
        print(f"  left out NBA Cup championship {g['date']} {g['away']} at {g['home']}")
    return keep


def current_season(games):
    for s in sorted({g["season"] for g in games}, reverse=True):
        cnt = collections.Counter()
        for g in games:
            if g["season"] == s:
                cnt[g["home"]] += 1; cnt[g["away"]] += 1
        if all(cnt[t] >= MIN_GP for t in TEAMS):
            return s
    raise SystemExit("no complete season")


from mlb_data_pages import close_is_consistent  # noqa: E402


def attach_prices(games, price_dir):
    idx = {}
    for f in glob.glob(os.path.join(price_dir, "nba_close_prices_*.json")):
        for ev in json.load(open(f)).values():
            idx.setdefault((ALIASES.get(ev["home"], ev["home"]), ALIASES.get(ev["away"], ev["away"]), ev["hs"], ev["as"]), []).append(ev)
    n = 0
    for g in games:
        gd = dt.date.fromisoformat(g["date"])
        ev = next((c for c in idx.get((g["home"], g["away"], g["hs"], g["as"]), []) if abs((dt.date.fromisoformat(c["date"]) - gd).days) <= 1), None)
        c = (ev or {}).get("close") or {}
        if close_is_consistent(c):
            g["spp"] = (c["home_line"], c["home_rl_price"], c["away_rl_price"]); n += 1
    return n


def profit(price, won):
    if won is None:
        return 0.0
    if not won:
        return -1.0
    return price / 100.0 if price > 0 else 100.0 / abs(price)


def rows_for(games, team):
    out, prev = [], {}
    for g in sorted((g for g in games if team in (g["home"], g["away"])), key=lambda g: g["date"]):
        r = m.team_rows([g], team)[0]
        # team_rows keeps only 1.5 run lines (MLB); NBA spreads take any value, so recompute here
        r["line"] = None if g["line"] is None else (g["line"] if r["home"] else -g["line"])
        if r["line"] is None:
            r["cover"] = None
        else:
            mm0 = r["rf"] - r["ra"] + r["line"]
            r["cover"] = None if mm0 == 0 else mm0 > 0
        last = prev.get(g["season"])
        gap = (dt.date.fromisoformat(g["date"]) - dt.date.fromisoformat(last[0])).days if last else None
        r["b2b"] = gap == 1
        r["rest2"] = gap is not None and gap >= 3
        r["after"] = last[1] if last else None
        r["after_ats"] = last[2] if last else None
        prev[g["season"]] = (g["date"], r["won"], r["cover"])
        r["push_ats"] = r["line"] is not None and r["cover"] is None
        r["ats_units"] = None
        if "spp" in g:
            hl, hp, ap = g["spp"]
            line = hl if r["home"] else -hl
            mm = r["rf"] - r["ra"] + line
            r["ats_units"] = profit(hp if r["home"] else ap, None if mm == 0 else mm > 0)
        out.append(r)
    return out


def ats(a, rs):
    p = sum(r["push_ats"] for r in rs)
    return f"{a['cov']}-{a['ncov']}" + (f"-{p}" if p else "")


def u_cell(rows, ok):
    vals = [r["ats_units"] for r in rows if r.get("ats_units") is not None]
    if not ok or not rows or len(vals) < 0.95 * len(rows):
        return '<td class="na">not priced</td>'
    u = sum(vals)
    return f'<td class="{cls(u)}">{fu(u)}</td>'


EXTRA_CSS = "<style>.tr td.na{color:#7d8592;font-size:.8rem}</style>"


def table(head, rows):
    return '<div class="tr-wrap"><table><thead><tr>' + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"


def split_rows(splits, ok):
    out = []
    for name, rs in splits:
        if not rs:
            continue
        a = m.agg(rs)
        out.append(f"<tr><td class=\"t\">{e(name)}</td><td>{a['n']}</td><td>{a['w']}-{a['l']}</td><td>{ats(a, rs)}</td><td>{pct(a['cov'], a['ncov'])}</td>"
                   f"{u_cell(rs, ok)}<td class=\"{cls(a['units'])}\">{fu(a['units'])}</td><td>{a['o']}-{a['u']}-{a['p']}</td></tr>")
    return table(["Situation", "Games", "Record", "ATS", "Cover %", "ATS units", "ML units", "O/U/P"], out)


def team_link(t):
    return f'<a href="{page_file(t)}">{e(t)}</a>'


def faq_html(faq):
    return "".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)


def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}


def method(extra=""):
    return (f"<section id=\"method\"><h2>Methodology</h2><p>Final scores and closing lines for every regular season game since 2016-17 come from the Bet Legend game "
            f"database, and every game is checked against ESPN's official final score; play in, playoff and NBA Cup championship games are excluded (the Cup final does not count in the standings). A team covers when its final margin "
            f"plus its closing spread is above zero, and an exact landing is a push. Moneyline units risk 1 unit at the closing price. ATS units, where shown, use the "
            f"sportsbook closing spread and price that ESPN publishes (DraftKings or ESPN BET); from 2024-25 on that close is also the spread used for the ATS record. A back to back is a game played the day after the team's previous game. {e(extra)}"
            f"These are market results, not BetLegend picks; our own picks are on the <a href=\"nba-records.html\">NBA betting record page</a>.</p></section>")


RELATED = (f'<section id="related"><h2>Related NBA betting data</h2><ul class="links"><li><a href="{HUB}">NBA team betting records</a></li>'
           f'<li><a href="{ATS_HUB}">NBA ATS records</a></li><li><a href="{OU_HUB}">NBA over/under records</a></li>'
           f'<li><a href="{B2B_HUB}">NBA back to back records</a></li><li><a href="nba.html">NBA slate, odds and analysis</a></li>'
           f'<li><a href="nba-records.html">BetLegend NBA picks record</a></li><li><a href="kelly-criterion.html">Kelly criterion calculator</a></li></ul></section>')


def build_team(team, games, cur, aggs, now_pt, finished, ok):
    short, conf, div, _ = TEAMS[team]
    rows = rows_for(games, team)
    seasons = sorted({r["season"] for r in rows}, reverse=True)
    cr = [r for r in rows if r["season"] == cur]
    a = m.agg(cr)
    ats_rank = sorted(aggs, key=lambda t: -(aggs[t]["cov"] / max(1, aggs[t]["cov"] + aggs[t]["ncov"]))).index(team) + 1
    sp = [("Home", [r for r in cr if r["home"]]), ("Road", [r for r in cr if not r["home"]]),
          ("Favored by the spread", [r for r in cr if r["line"] is not None and r["line"] < 0]),
          ("Underdog by the spread", [r for r in cr if r["line"] is not None and r["line"] > 0]),
          ("Favored by 7 or more", [r for r in cr if r["line"] is not None and r["line"] <= -7]),
          ("Underdog by 7 or more", [r for r in cr if r["line"] is not None and r["line"] >= 7]),
          ("Second night of a back to back", [r for r in cr if r["b2b"]]), ("Two or more days of rest", [r for r in cr if r["rest2"]]),
          ("After a win", [r for r in cr if r["after"] is True]), ("After a loss", [r for r in cr if r["after"] is False]),
          ("After covering", [r for r in cr if r["after_ats"] is True]), ("After failing to cover", [r for r in cr if r["after_ats"] is False]),
          (f"vs {div} Division", [r for r in cr if TEAMS.get(r["opp"], ("", "", ""))[2] == div]),
          (f"vs {conf} Conference", [r for r in cr if TEAMS.get(r["opp"], ("", ""))[1] == conf]),
          ("vs the other conference", [r for r in cr if TEAMS.get(r["opp"], ("", ""))[1] not in ("", conf)])]
    sa = {n: m.agg(rs) for n, rs in sp if rs}
    home, road = sa["Home"], sa["Road"]
    b2b = sa.get("Second night of a back to back")
    fav, dog = sa.get("Favored by the spread"), sa.get("Underdog by the spread")
    months = collections.OrderedDict()
    for r in cr:
        months.setdefault(dt.date.fromisoformat(r["date"]).strftime("%B"), []).append(r)
    srows = []
    for s in seasons:
        rs = [r for r in rows if r["season"] == s]
        x = m.agg(rs)
        srows.append(f"<tr><td>{label(s)}</td><td>{x['w']}-{x['l']}</td><td>{ats(x, rs)}</td><td>{pct(x['cov'], x['ncov'])}</td>"
                     f"<td class=\"{cls(x['units'])}\">{fu(x['units'])}</td><td>{x['o']}-{x['u']}-{x['p']}</td><td>{x['avg_total']:.1f}</td><td>{x['rpg']:.1f}</td><td>{x['rapg']:.1f}</td></tr>")
    allr = m.agg(rows)
    srows.append(f"<tr><td><strong>All {len(seasons)} seasons</strong></td><td><strong>{allr['w']}-{allr['l']}</strong></td><td><strong>{ats(allr, rows)}</strong></td>"
                 f"<td>{pct(allr['cov'], allr['ncov'])}</td><td class=\"{cls(allr['units'])}\">{fu(allr['units'])}</td><td>{allr['o']}-{allr['u']}-{allr['p']}</td>"
                 f"<td>{allr['avg_total']:.1f}</td><td>{allr['rpg']:.1f}</td><td>{allr['rapg']:.1f}</td></tr>")
    opp = collections.defaultdict(list)
    for r in cr:
        opp[r["opp"]].append(r)
    orows = [f"<tr><td class=\"t\">{team_link(o) if o in TEAMS else e(o)}</td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td><td>{ats(x, opp[o])}</td>"
             f"<td class=\"{cls(x['units'])}\">{fu(x['units'])}</td><td>{x['o']}-{x['u']}-{x['p']}</td></tr>"
             for o, x in sorted(((o, m.agg(rs)) for o, rs in opp.items()), key=lambda kv: (-kv[1]["n"], kv[0]))]
    last = []
    for r in cr[-15:][::-1]:
        sp_txt = "no line" if r["line"] is None else f"{r['line']:+g}"
        tot_txt = "no line" if r["total"] is None else f"{r['total']:g}"
        res = "Push" if r["push_ats"] else ("Covered" if r["cover"] else ("Lost" if r["cover"] is False else "no line"))
        last.append(f"<tr><td>{fdate(r['date'], False)}</td><td class=\"t\">{'vs' if r['home'] else 'at'} {e(TEAMS.get(r['opp'], (r['opp'],))[0])}</td>"
                    f"<td class=\"{'w' if r['won'] else 'l'}\">{'W' if r['won'] else 'L'} {r['rf']}-{r['ra']}</td>"
                    f"<td>{sp_txt}</td><td>{res}</td>"
                    f"<td>{fodds(r['ml'])}</td><td>{tot_txt}</td>"
                    f"<td>{ {'O': 'Over', 'U': 'Under', 'P': 'Push', None: 'no line'}[r['ou']] }</td></tr>")
    best = max(seasons, key=lambda s: m.agg([r for r in rows if r["season"] == s])["cov"] / max(1, m.agg([r for r in rows if r["season"] == s])["n"]))
    bs = m.agg([r for r in rows if r["season"] == best])
    when = f"the {label(cur)} regular season" if finished else f"{label(cur)} so far (through {fdate(cr[-1]['date'])})"
    lean = "over" if a["o"] > a["u"] else ("under" if a["u"] > a["o"] else "neither way")
    lead = (f"The {short} went {a['w']}-{a['l']} in {when} and {ats(a, cr)} against the spread ({pct(a['cov'], a['ncov'])} covers, "
            f"{ordinal(ats_rank)} of 30 NBA teams). One unit on their moneyline every game returned {fu(a['units'])}. Their games went "
            f"{a['o']}-{a['u']}-{a['p']} against the total, leaning {lean}.")
    stats = (f'<div class="tr-stats"><div><b>{ats(a, cr)}</b><span>{label(cur)} ATS ({pct(a["cov"], a["ncov"])}), {ordinal(ats_rank)} in the NBA</span></div>'
             f'<div><b>{a["w"]}-{a["l"]}</b><span>straight up</span></div><div><b class="{cls(a["units"])}">{fu(a["units"])}</b><span>moneyline units</span></div>'
             f'<div><b>{a["o"]}-{a["u"]}-{a["p"]}</b><span>over, under, push</span></div></div>')
    faq = [(f"What is the {short} ATS record in {label(cur)}?", f"{ats(a, cr)} against the closing spread ({pct(a['cov'], a['ncov'])} covers) and {a['w']}-{a['l']} straight up ({when})."),
           (f"How do the {short} do against the spread at home and on the road?",
            f"Home {ats(home, [r for r in cr if r['home']])} ATS, road {ats(road, [r for r in cr if not r['home']])} ATS."),
           (f"How do the {short} do on the second night of a back to back?",
            (f"{b2b['w']}-{b2b['l']} straight up and {ats(b2b, [r for r in cr if r['b2b']])} ATS in {b2b['n']} games." if b2b else "They had no back to back games in this span.")),
           (f"Do the {short} cover more as favorites or underdogs?",
            (f"Favored: {ats(fav, [r for r in cr if r['line'] is not None and r['line'] < 0])} ATS. " if fav else "") +
            (f"Underdog: {ats(dog, [r for r in cr if r['line'] is not None and r['line'] > 0])} ATS." if dog else "")),
           (f"Do {short} games go over or under?", f"{a['o']} overs, {a['u']} unders, {a['p']} pushes against the closing total in {label(cur)}; the average total was {a['avg_total']:.1f}."),
           (f"What was the {short}' best ATS season since {label(seasons[-1])}?", f"{label(best)}: {ats(bs, [r for r in rows if r['season'] == best])} ATS. All {len(seasons)} seasons: {ats(allr, rows)}.")]
    rivals = [t for t in TEAMS if t != team and TEAMS[t][2] == div]
    note = espn_verify.coverage_note(COVERAGE, team, label) if COVERAGE else ""
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing lines, regular season games only, {label(seasons[-1])} to {label(seasons[0])}. <a href="#method">How these numbers are calculated</a>.</p>
<ul class="tr-jump"><li><a href="#season">{label(cur)} summary</a></li><li><a href="#history">Season by season</a></li><li><a href="#splits">Splits</a></li><li><a href="#opponents">vs every opponent</a></li><li><a href="#recent">Last 15 games</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="season"><h2>{e(short)} {label(cur)} betting summary</h2>
{stats}
<p>At home the {e(short)} were {ats(home, [r for r in cr if r['home']])} ATS; on the road {ats(road, [r for r in cr if not r['home']])} ATS.</p>
</section>
<section id="history"><h2>{e(short)} betting record by season</h2>
{table(["Season", "Record", "ATS", "Cover %", "ML units", "O/U/P", "Avg total", "Points/G", "Allowed/G"], srows)}
</section>
<section id="splits"><h2>{e(short)} betting splits, {label(cur)}</h2>
{split_rows(sp, ok)}
<h3>By month</h3>
{split_rows(list(months.items()), ok)}
</section>
<section id="opponents"><h2>{e(short)} record against every opponent, {label(cur)}</h2>
{table(["Opponent", "Games", "Record", "ATS", "ML units", "O/U/P"], orows)}
</section>
<section id="recent"><h2>Last 15 {e(short)} games with closing lines</h2>
{table(["Date", "Opponent", "Result", "Spread", "ATS", "Close ML", "Total", "O/U"], last)}
<p class="note">The spread is shown from the {e(short)}' side.</p>
</section>
<section id="faq"><h2>{e(short)} betting FAQ</h2>
{faq_html(faq)}
</section>
{method(note)}
<section id="related2"><h2>Division rivals</h2><ul class="links">{"".join(f'<li><a href="{page_file(t)}">{e(t)} betting record</a></li>' for t in rivals)}</ul></section>
{RELATED}"""
    title = f"{team} ATS Record {label(cur)}: Betting Record, O/U & Trends"
    desc = (f"{team} {label(cur)} betting record: {ats(a, cr)} against the spread, {a['w']}-{a['l']} straight up, {a['o']}-{a['u']}-{a['p']} over/under, "
            f"with home/road, back to back, favorite/underdog splits and every season since {label(seasons[-1])}.")
    h1 = f"{team} ATS and Betting Record {label(cur)}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": SITE + page_file(team), "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat(), "about": {"@type": "SportsTeam", "name": team, "sport": "Basketball"}}, faq_ld(faq)]
    crumbs = [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", HUB), (f"{short} Betting Record", None)]
    return page_file(team), m.shell(page_file(team), title, desc, h1, EXTRA_CSS + body, ld, crumbs, now_pt, head_img=logo(team)), title


def build_hubs(games, cur, now_pt, finished, ok):
    cg = [g for g in games if g["season"] == cur]
    data = {t: rows_for(cg, t) for t in TEAMS}
    ag = {t: m.agg(rs) for t, rs in data.items()}
    when = f"the {label(cur)} regular season" if finished else f"{label(cur)} so far"
    seasons = sorted({g["season"] for g in games}, reverse=True)
    out = {}
    # team hub
    ranked = sorted(TEAMS, key=lambda t: -(ag[t]["cov"] / max(1, ag[t]["cov"] + ag[t]["ncov"])))
    rows = [f"<tr><td>{i}</td><td class=\"t\">{team_link(t)}</td><td>{ag[t]['w']}-{ag[t]['l']}</td><td>{ats(ag[t], data[t])}</td><td>{pct(ag[t]['cov'], ag[t]['ncov'])}</td>"
            f"{u_cell(data[t], ok)}<td class=\"{cls(ag[t]['units'])}\">{fu(ag[t]['units'])}</td><td>{ag[t]['o']}-{ag[t]['u']}-{ag[t]['p']}</td></tr>" for i, t in enumerate(ranked, 1)]
    top, bot = ranked[0], ranked[-1]
    lead = (f"Every NBA team's betting record for {when} at closing lines. The {top} covered the spread most often ({ats(ag[top], data[top])}); "
            f"the {bot} least ({ats(ag[bot], data[bot])}).")
    body = (f"<p class=\"lead\">{e(lead)}</p><p class=\"upd\">Updated {{UPDATED}}. Regular season only. The {label(cur + 1)} season replaces this one once every team has played {MIN_GP} games.</p>"
            f"<section id=\"teams\"><h2>NBA team betting records, {label(cur)}</h2><p>Sorted by cover percentage (pushes excluded). Click a team for its season by season history and splits.</p>"
            + table(["#", "Team", "Record", "ATS", "Cover %", "ATS units", "ML units", "O/U/P"], rows) + "</section>" + method() + RELATED)
    desc = f"All 30 NBA teams' {label(cur)} betting records at closing lines: ATS record and cover %, moneyline units, over/under, ranked, with a page for every team."
    out[HUB] = m.shell(HUB, f"NBA Team Betting Records {label(cur)}: ATS, Moneyline & Over/Under", desc, f"NBA Team Betting Records {label(cur)}", EXTRA_CSS + body,
                       [{"@context": "https://schema.org", "@type": "WebPage", "name": f"NBA Team Betting Records {label(cur)}", "url": SITE + HUB, "description": desc,
                         "dateModified": now_pt.replace(microsecond=0).isoformat()}], [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", None)], now_pt)
    # ATS hub
    rows = []
    for i, t in enumerate(ranked, 1):
        rs = data[t]
        fav = [r for r in rs if r["line"] is not None and r["line"] < 0]; dog = [r for r in rs if r["line"] is not None and r["line"] > 0]
        h = [r for r in rs if r["home"]]; rd = [r for r in rs if not r["home"]]
        rows.append(f"<tr><td>{i}</td><td class=\"t\">{team_link(t)}</td><td>{ats(ag[t], rs)}</td><td>{pct(ag[t]['cov'], ag[t]['ncov'])}</td>{u_cell(rs, ok)}"
                    f"<td>{ats(m.agg(fav), fav)}</td><td>{ats(m.agg(dog), dog)}</td><td>{ats(m.agg(h), h)}</td><td>{ats(m.agg(rd), rd)}</td></tr>")
    lg = []
    for s in seasons:
        gs = [g for g in games if g["season"] == s and g["line"] is not None]
        hc = sum(g["hs"] - g["as"] + g["line"] > 0 for g in gs); hl = sum(g["hs"] - g["as"] + g["line"] < 0 for g in gs)
        fc = sum((g["hs"] - g["as"] + g["line"] > 0) if g["line"] < 0 else (g["hs"] - g["as"] + g["line"] < 0) for g in gs if g["line"] != 0)
        fl = sum((g["hs"] - g["as"] + g["line"] < 0) if g["line"] < 0 else (g["hs"] - g["as"] + g["line"] > 0) for g in gs if g["line"] != 0)
        lg.append(f"<tr><td>{label(s)}</td><td>{len(gs)}</td><td>{hc}-{hl}</td><td>{pct(hc, hl)}</td><td>{fc}-{fl}</td><td>{pct(fc, fl)}</td></tr>")
    mat = [f"<tr><td class=\"t\">{team_link(t)}</td>" + "".join(
        f"<td>{(lambda x: pct(x['cov'], x['ncov']))(m.agg(rows_for([g for g in games if g['season'] == s], t)))}</td>" for s in seasons[:6]) + "</tr>"
        for t in sorted(TEAMS, key=lambda t: TEAMS[t][0])]
    gcur = [g for g in cg if g["line"] is not None and g["line"] != 0]
    fav_cur = (sum((g["hs"] - g["as"] + g["line"] > 0) if g["line"] < 0 else (g["hs"] - g["as"] + g["line"] < 0) for g in gcur),
               sum((g["hs"] - g["as"] + g["line"] < 0) if g["line"] < 0 else (g["hs"] - g["as"] + g["line"] > 0) for g in gcur))
    faq = [(f"Which NBA team has the best ATS record in {label(cur)}?", f"The {top}: {ats(ag[top], data[top])} against the spread."),
           ("How often do NBA favorites cover the spread?", f"In {label(cur)} favorites went {fav_cur[0]}-{fav_cur[1]} against the closing spread ({pct(fav_cur[0], fav_cur[1])}); the season table shows every year since 2016-17."),
           ("Do NBA spread pushes count?", "A push (the final margin lands exactly on the spread) returns the stake. Records here show pushes as the third number and leave them out of cover %.")]
    body = (f"<p class=\"lead\">{e(f'Every NBA team against the closing spread in {when}: overall, as favorite and underdog, home and road. The {top} led the league at {ats(ag[top], data[top])}.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only.</p><section id=\"teams\"><h2>NBA ATS records by team, {label(cur)}</h2>"
            + table(["#", "Team", "ATS", "Cover %", "ATS units", "As favorite", "As underdog", "Home", "Road"], rows) + "</section>"
            f"<section id=\"seasons\"><h2>Home teams and favorites against the spread by season</h2>"
            + table(["Season", "Games", "Home teams ATS", "Home cover %", "Favorites ATS", "Favorite cover %"], lg) + "</section>"
            f"<section id=\"history\"><h2>Team cover % by season</h2>" + table(["Team"] + [label(s) for s in seasons[:6]], mat) + "</section>"
            f"<section id=\"faq\"><h2>NBA ATS FAQ</h2>{faq_html(faq)}</section>" + method() + RELATED)
    desc = f"Every NBA team's {label(cur)} record against the spread at closing lines: cover %, as favorite and underdog, home and road, plus favorite and home team ATS by season since 2016-17."
    out[ATS_HUB] = m.shell(ATS_HUB, f"NBA ATS Records {label(cur)}: Against the Spread by Team", desc, f"NBA ATS Records {label(cur)}", EXTRA_CSS + body,
                           [{"@context": "https://schema.org", "@type": "WebPage", "name": f"NBA ATS Records {label(cur)}", "url": SITE + ATS_HUB, "description": desc,
                             "dateModified": now_pt.replace(microsecond=0).isoformat()}, faq_ld(faq)],
                           [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", HUB), ("ATS Records", None)], now_pt)
    # O/U hub
    ou_rank = sorted(TEAMS, key=lambda t: -(ag[t]["o"] / max(1, ag[t]["o"] + ag[t]["u"])))
    rows = [f"<tr><td>{i}</td><td class=\"t\">{team_link(t)}</td><td>{ag[t]['o']}-{ag[t]['u']}-{ag[t]['p']}</td><td>{pct(ag[t]['o'], ag[t]['u'])}</td>"
            f"<td>{ag[t]['avg_total']:.1f}</td><td>{ag[t]['rpg'] + ag[t]['rapg']:.1f}</td>"
            f"<td class=\"{cls(ag[t]['rpg'] + ag[t]['rapg'] - ag[t]['avg_total'])}\">{ag[t]['rpg'] + ag[t]['rapg'] - ag[t]['avg_total']:+.1f}</td></tr>" for i, t in enumerate(ou_rank, 1)]
    lg = []
    for s in seasons:
        gs = [g for g in games if g["season"] == s and g["total"] is not None]
        o = sum(g["hs"] + g["as"] > g["total"] for g in gs); u = sum(g["hs"] + g["as"] < g["total"] for g in gs)
        lg.append(f"<tr><td>{label(s)}</td><td>{len(gs)}</td><td>{o}-{u}-{len(gs) - o - u}</td><td>{pct(o, u)}</td><td>{sum(g['total'] for g in gs) / len(gs):.1f}</td>"
                  f"<td>{sum(g['hs'] + g['as'] for g in gs) / len(gs):.1f}</td></tr>")
    mat = [f"<tr><td class=\"t\">{team_link(t)}</td>" + "".join(
        f"<td>{(lambda x: pct(x['o'], x['u']))(m.agg(rows_for([g for g in games if g['season'] == s], t)))}</td>" for s in seasons[:6]) + "</tr>"
        for t in sorted(TEAMS, key=lambda t: TEAMS[t][0])]
    o0, u0 = ou_rank[0], ou_rank[-1]
    gt = [g for g in cg if g["total"] is not None]
    avg_t = sum(g["total"] for g in gt) / len(gt); avg_p = sum(g["hs"] + g["as"] for g in gt) / len(gt)
    faq = [(f"Which NBA team went over the most in {label(cur)}?", f"The {o0}: {ag[o0]['o']}-{ag[o0]['u']}-{ag[o0]['p']} against the closing total."),
           (f"Which NBA team went under the most in {label(cur)}?", f"The {u0}: {ag[u0]['o']}-{ag[u0]['u']}-{ag[u0]['p']}."),
           ("What is the average NBA closing total?", f"{avg_t:.1f} points in {label(cur)}, against {avg_p:.1f} actual points per game.")]
    ou_txt = f"{ag[o0]['o']}-{ag[o0]['u']}-{ag[o0]['p']}"
    body = (f"<p class=\"lead\">{e(f'Every NBA team against the closing total in {when}. The {o0} were the best over team ({ou_txt}) and the {u0} the best under team.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only.</p><section id=\"teams\"><h2>NBA over/under records by team, {label(cur)}</h2>"
            "<p>Points vs total is the average actual total minus the average closing total.</p>"
            + table(["#", "Team", "O/U/P", "Over %", "Avg total", "Avg points", "Points vs total"], rows) + "</section>"
            f"<section id=\"seasons\"><h2>NBA over/under results by season</h2>" + table(["Season", "Games", "O/U/P", "Over %", "Avg total", "Avg points"], lg) + "</section>"
            f"<section id=\"history\"><h2>Team over % by season</h2>" + table(["Team"] + [label(s) for s in seasons[:6]], mat) + "</section>"
            f"<section id=\"faq\"><h2>NBA over/under FAQ</h2>{faq_html(faq)}</section>" + method() + RELATED)
    desc = f"Every NBA team's {label(cur)} over/under record against the closing total: over %, average total vs actual points, and league and team over % by season since 2016-17."
    out[OU_HUB] = m.shell(OU_HUB, f"NBA Over/Under Records {label(cur)}: Team Totals Trends", desc, f"NBA Over/Under Records {label(cur)}", EXTRA_CSS + body,
                          [{"@context": "https://schema.org", "@type": "WebPage", "name": f"NBA Over/Under Records {label(cur)}", "url": SITE + OU_HUB, "description": desc,
                            "dateModified": now_pt.replace(microsecond=0).isoformat()}, faq_ld(faq)],
                          [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", HUB), ("Over/Under Records", None)], now_pt)
    # back to back hub
    allrows = {s: [r for t in TEAMS for r in rows_for([g for g in games if g["season"] == s], t)] for s in seasons}
    lg = []
    for s in seasons:
        b = [r for r in allrows[s] if r["b2b"]]; rest = [r for r in allrows[s] if r["rest2"]]
        x, y = m.agg(b), m.agg(rest)
        lg.append(f"<tr><td>{label(s)}</td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td><td>{ats(x, b)}</td><td>{pct(x['cov'], x['ncov'])}</td>"
                  f"<td>{ats(y, rest)}</td><td>{pct(y['cov'], y['ncov'])}</td></tr>")
    ball = [r for s in seasons for r in allrows[s] if r["b2b"]]
    xb = m.agg(ball)
    # matchups by rest situation, current season, game level
    def rest_of(g, side, rows_by_team):
        return next((r for r in rows_by_team[side] if r["date"] == g["date"] and r["opp"] == (g["away"] if side == g["home"] else g["home"])), None)
    sit = collections.defaultdict(list)
    for s in seasons:
        rb = {t: rows_for([g for g in games if g["season"] == s], t) for t in TEAMS}
        idx = {t: {(r["date"], r["opp"]): r for r in rb[t]} for t in TEAMS}
        for g in (g for g in games if g["season"] == s):
            h = idx.get(g["home"], {}).get((g["date"], g["away"])); a = idx.get(g["away"], {}).get((g["date"], g["home"]))
            if not h or not a or h["line"] is None:
                continue
            if a["b2b"] and not h["b2b"]:
                sit["Home team rested, road team on a back to back"].append(h)
            elif h["b2b"] and not a["b2b"]:
                sit["Home team on a back to back, road team rested"].append(h)
            elif h["b2b"] and a["b2b"]:
                sit["Both teams on a back to back"].append(h)
    srows = [f"<tr><td class=\"t\">{e(k)}</td><td>{m.agg(v)['n']}</td><td>{m.agg(v)['w']}-{m.agg(v)['l']}</td><td>{ats(m.agg(v), v)}</td><td>{pct(m.agg(v)['cov'], m.agg(v)['ncov'])}</td></tr>"
             for k, v in sit.items()]
    trows = []
    for t in sorted(TEAMS, key=lambda t: TEAMS[t][0]):
        b = [r for r in rows_for(games, t) if r["b2b"]]
        x = m.agg(b)
        trows.append(f"<tr><td class=\"t\">{team_link(t)}</td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td><td>{ats(x, b)}</td><td>{pct(x['cov'], x['ncov'])}</td><td>{x['o']}-{x['u']}-{x['p']}</td></tr>")
    xb_rec = f"{xb['w']}-{xb['l']}"
    faq = [("How do NBA teams do on the second night of a back to back?", f"Since {label(seasons[-1])}: {xb['w']}-{xb['l']} straight up and {ats(xb, ball)} against the spread ({pct(xb['cov'], xb['ncov'])} covers) in {xb['n']} games."),
           ("Does the market already price in back to backs?", "Largely, yes: the cover rate on the second night sits close to 50% in most seasons even though the straight up record is poor. The table by season shows how it moves year to year."),
           ("What counts as a back to back here?", "A game played the day after the team's previous regular season game.")]
    body = (f"<p class=\"lead\">{e(f'How NBA teams do on the second night of a back to back, at closing lines. Since {label(seasons[-1])} they are {xb_rec} straight up and {ats(xb, ball)} against the spread.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only.</p>"
            f"<section id=\"seasons\"><h2>Back to back results by season</h2>" + table(["Season", "B2B games", "Record", "ATS", "Cover %", "Rested 2+ days ATS", "Cover %"], lg) + "</section>"
            f"<section id=\"rest\"><h2>Rest matchups, home team's side, since {label(seasons[-1])}</h2>" + table(["Situation", "Games", "Home record", "Home ATS", "Home cover %"], srows) + "</section>"
            f"<section id=\"teams\"><h2>Back to back record by team, {label(seasons[-1])} to {label(seasons[0])}</h2>" + table(["Team", "B2B games", "Record", "ATS", "Cover %", "O/U/P"], trows) + "</section>"
            f"<section id=\"faq\"><h2>NBA back to back FAQ</h2>{faq_html(faq)}</section>" + method() + RELATED)
    desc = f"NBA teams on the second night of a back to back since {label(seasons[-1])}: straight up and ATS by season, rest matchups (rested vs tired), and every team's back to back record."
    out[B2B_HUB] = m.shell(B2B_HUB, "NBA Back to Back Records: ATS and Betting Results by Season and Team", desc, "NBA Back to Back Betting Records", EXTRA_CSS + body,
                           [{"@context": "https://schema.org", "@type": "WebPage", "name": "NBA Back to Back Betting Records", "url": SITE + B2B_HUB, "description": desc,
                             "dateModified": now_pt.replace(microsecond=0).isoformat()}, faq_ld(faq)],
                           [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", HUB), ("Back to Back Records", None)], now_pt)
    return out, ag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(m.PT)
    raw = [g for g in load_games(a.db) if g["home"] in TEAMS and g["away"] in TEAMS]
    cur = current_season(raw)
    games, dropped, cov, cur_bad, finished = espn_verify.verify(raw, "nba", {t: TEAMS[t][3] for t in TEAMS}, ALIASES, lambda s: s + 1, cur, TEAMS)
    if cur_bad:
        sys.exit(f"ABORT: {label(cur)} games disagree with ESPN: {cur_bad}")
    games = drop_cup_finals(games)
    COVERAGE.clear(); COVERAGE.update(cov)
    by = collections.defaultdict(lambda: [0, 0])
    for (t, s), (k, n, dr, mi) in cov.items():
        by[s][0] += dr; by[s][1] += mi
    for s in sorted(by):
        print(f"  {label(s)}: verified against ESPN; team rows dropped {by[s][0]}, team games missing {by[s][1]}")
    cg = [g for g in games if g["season"] == cur]
    missing = [g for g in cg if g["hml"] is None or g["line"] is None or g["total"] is None]
    if len(missing) > 0.02 * len(cg) or any(g["est"] for g in cg):
        sys.exit(f"ABORT: {len(missing)} {label(cur)} games lack closing lines or carry estimates")
    n = attach_prices(games, a.prices)
    # The dataset's NBA spreads for 2024-25 and 2025-26 are unreliable (checked 2026-10-01: only 55% of
    # 2025-26 spreads put the favorite on the moneyline favorite, against 97% or better before 2024).
    # From 2024-25 on the spread is the sportsbook close ESPN publishes; a game without a usable close has no spread.
    for g in games:
        if g["season"] >= SPREAD_FROM_CLOSE:
            g["line"] = g["spp"][0] if "spp" in g else None
    ok = sum("spp" in g for g in cg) >= 0.95 * len(cg)
    print(f"  {label(cur)}: {len(cg)} games, ESPN game for game OK, finished={finished}; spread prices on {n} games, units shown={ok}")
    out, ag = build_hubs(games, cur, now_pt, finished, ok)
    titles = []
    for t in TEAMS:
        f, page, title = build_team(t, games, cur, ag, now_pt, finished, ok)
        out[f] = page; titles.append(title)
    assert len(set(titles)) == len(titles)
    if not a.dry_run:
        for f, page in out.items():
            open(os.path.join(ROOT, f), "w", encoding="utf-8", newline="\n").write(page)
    print(f"[nba_data_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages for {label(cur)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
