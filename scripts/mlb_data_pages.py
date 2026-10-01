#!/usr/bin/env python3
"""MLB betting data pages, batch 2 (Phase 5 SEO, Oct 1 2026).

Builds, from the same verified game set as scripts/mlb_team_pages.py:
  /mlb-team-over-under-records.html   all 30 teams against the closing total
  /mlb-run-line-records.html          all 30 teams on the 1.5 run line
  /<a>-vs-<b>-betting-history.html    the 60 division rivalries, 2016 to today
and then rebuilds the 30 team pages and the team hub so they link to all of it.

Units on the run line and on totals need the closing PRICE, which the Bet Legend
dataset does not store. scripts/mlb_close_prices.py caches the DraftKings close ESPN
publishes (line and price); unit columns are computed against that book's own line.
Seasons where fewer than 95% of games carry a usable price show records only.

    python scripts/mlb_data_pages.py --db DATASET.sqlite --prices DIR [--dry-run] [--no-espn-check]
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import glob
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402

ROOT = m.ROOT
OU_HUB = "mlb-team-over-under-records.html"
RL_HUB = "mlb-run-line-records.html"
COVERAGE = 0.95
e, fu, froi, pct, fodds, fdate, cls, ordinal = m.e, m.fu, m.froi, m.pct, m.fodds, m.fdate, m.cls, m.ordinal
SHORT = {t: m.TEAMS[t][0] for t in m.TEAMS}
NICK_SLUG = {t: SHORT[t].lower().replace(" ", "-") for t in m.TEAMS}
# Nima named this URL explicitly (Oct 1 2026); every other pair is alphabetical by nickname.
ORDER_OVERRIDES = {frozenset(("New York Yankees", "Boston Red Sox")): ("New York Yankees", "Boston Red Sox")}


# ---------------------------------------------------------------- data

def attach_prices(games, price_dir):
    """Attach the DraftKings close (line and price) that ESPN publishes, matched by teams, score and date."""
    idx = {}
    for f in glob.glob(os.path.join(price_dir, "mlb_close_prices_*.json")):
        for ev in json.load(open(f)).values():
            h = m.ALIASES.get(ev["home"], ev["home"]); a = m.ALIASES.get(ev["away"], ev["away"])
            idx.setdefault((h, a, ev["hs"], ev["as"]), []).append(ev)
    stats = collections.Counter()
    for g in games:
        cands = idx.get((g["home"], g["away"], g["hs"], g["as"]), [])
        gd = dt.date.fromisoformat(g["date"])
        ev = next((c for c in cands if abs((dt.date.fromisoformat(c["date"]) - gd).days) <= 1), None)
        c = (ev or {}).get("close") or {}
        if not c:
            continue
        stats["matched"] += 1
        hl = c.get("home_line")
        if hl is not None and abs(hl) == 1.5 and c.get("home_rl_price") and c.get("away_rl_price"):
            g["rlp"] = (hl, c["home_rl_price"], c["away_rl_price"]); stats["rl"] += 1
        if c.get("total") and c.get("over_price") and c.get("under_price"):
            g["oup"] = (c["total"], c["over_price"], c["under_price"]); stats["ou"] += 1
    return stats


def priced_seasons(games, key):
    by = collections.defaultdict(lambda: [0, 0])
    for g in games:
        by[g["season"]][0] += 1
        by[g["season"]][1] += key in g
    return {s for s, (n, k) in by.items() if n and k / n >= COVERAGE}


def profit(price, won):
    if won is None:
        return 0.0
    if not won:
        return -1.0
    return price / 100.0 if price > 0 else 100.0 / abs(price)


def rows_for(games, team):
    """Team-side rows (from mlb_team_pages.team_rows) with run line and total units where priced."""
    out = []
    for g in sorted((g for g in games if team in (g["home"], g["away"])), key=lambda g: g["date"]):
        r = m.team_rows([g], team)[0]
        r["rl_units"] = r["over_units"] = r["under_units"] = None
        if "rlp" in g:  # DraftKings close: its own line and price
            hl, hp, ap = g["rlp"]
            line = hl if r["home"] else -hl
            r["rl_units"] = profit(hp if r["home"] else ap, r["rf"] - r["ra"] + line > 0)
        if "oup" in g:
            tot, op, up = g["oup"]
            runs = r["rf"] + r["ra"]
            r["over_units"] = 0.0 if runs == tot else profit(op, runs > tot)
            r["under_units"] = 0.0 if runs == tot else profit(up, runs < tot)
        out.append(r)
    return out


def sum_units(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return (sum(vals), len(vals)) if vals else (None, 0)


def units_cell(rows, key, ok):
    if not ok:
        return '<td class="na">not priced</td>'
    u, n = sum_units(rows, key)
    if u is None:
        return '<td class="na">not priced</td>'
    return f'<td class="{cls(u)}">{fu(u)}</td>'


# ---------------------------------------------------------------- shared bits

EXTRA_CSS = "<style>.tr td.na{color:#7d8592;font-size:.8rem}.tr .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:6px 22px}</style>"


def team_link(t):
    return f'<a href="{m.page_file(t)}">{e(t)}</a>'


def rivalry_pairs():
    pairs = []
    for t1, t2 in itertools.combinations(sorted(m.TEAMS), 2):
        if m.TEAMS[t1][2] == m.TEAMS[t2][2] and m.TEAMS[t1][3] == m.TEAMS[t2][3]:
            key = frozenset((t1, t2))
            a, b = ORDER_OVERRIDES.get(key) or tuple(sorted((t1, t2), key=lambda t: SHORT[t]))
            pairs.append((a, b))
    return pairs


def rivalry_file(a, b):
    return f"{NICK_SLUG[a]}-vs-{NICK_SLUG[b]}-betting-history.html"


def rivalry_file_for(t1, t2):
    for a, b in rivalry_pairs():
        if {a, b} == {t1, t2}:
            return rivalry_file(a, b)
    return None


# ---------------------------------------------------------------- O/U hub

def build_ou_hub(games, cur, now_pt, finished, last_date):
    cur_games = [g for g in games if g["season"] == cur]
    ou_priced = priced_seasons(games, "oup")
    ok = cur in ou_priced
    trs = []
    data = []
    for t in m.TEAMS:
        rs = rows_for(cur_games, t)
        a = m.agg(rs)
        h = m.agg([r for r in rs if r["home"]]); rd = m.agg([r for r in rs if not r["home"]])
        ou_runs = (a["rpg"] + a["rapg"])
        data.append((t, a, h, rd, rs, ou_runs))
    data.sort(key=lambda x: -(x[1]["o"] / max(1, x[1]["o"] + x[1]["u"])))
    for i, (t, a, h, rd, rs, runs) in enumerate(data, 1):
        trs.append(f"<tr><td>{i}</td><td class=\"t\">{team_link(t)}</td><td>{a['o']}-{a['u']}-{a['p']}</td><td>{pct(a['o'], a['u'])}</td>"
                   f"<td>{pct(a['u'], a['o'])}</td>{units_cell(rs, 'over_units', ok)}{units_cell(rs, 'under_units', ok)}"
                   f"<td>{a['avg_total']:.2f}</td><td>{runs:.2f}</td><td class=\"{cls(runs - a['avg_total'])}\">{runs - a['avg_total']:+.2f}</td>"
                   f"<td>{h['o']}-{h['u']}-{h['p']}</td><td>{rd['o']}-{rd['u']}-{rd['p']}</td></tr>")
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>O/U/P</th><th>Over %</th><th>Under %</th>'
             '<th>Over units</th><th>Under units</th><th>Avg total</th><th>Avg runs</th><th>Runs vs total</th><th>Home O/U/P</th><th>Road O/U/P</th></tr></thead><tbody>'
             + "".join(trs) + "</tbody></table></div>")
    # league by season
    srows = []
    for s in sorted({g["season"] for g in games}, reverse=True):
        gs = [g for g in games if g["season"] == s and g["total"] is not None]
        o = sum(g["hs"] + g["as"] > g["total"] for g in gs); u = sum(g["hs"] + g["as"] < g["total"] for g in gs); p = len(gs) - o - u
        avgt = sum(g["total"] for g in gs) / len(gs); avgr = sum(g["hs"] + g["as"] for g in gs) / len(gs)
        if s in ou_priced:
            ov = sum(profit(g["oup"][1], g["hs"] + g["as"] > g["oup"][0]) if g["hs"] + g["as"] != g["oup"][0] else 0 for g in gs if "oup" in g)
            un = sum(profit(g["oup"][2], g["hs"] + g["as"] < g["oup"][0]) if g["hs"] + g["as"] != g["oup"][0] else 0 for g in gs if "oup" in g)
            ucells = f'<td class="{cls(ov)}">{fu(ov)}</td><td class="{cls(un)}">{fu(un)}</td>'
        else:
            ucells = '<td class="na">not priced</td><td class="na">not priced</td>'
        srows.append(f"<tr><td>{s}</td><td>{len(gs)}</td><td>{o}-{u}-{p}</td><td>{pct(o, u)}</td>{ucells}<td>{avgt:.2f}</td><td>{avgr:.2f}</td></tr>")
    season_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Games</th><th>O/U/P</th><th>Over %</th><th>Over units</th><th>Under units</th>'
                  '<th>Avg total</th><th>Avg runs</th></tr></thead><tbody>' + "".join(srows) + "</tbody></table></div>")
    # situational (current season, game level)
    cg = [g for g in cur_games if g["total"] is not None]

    def ou_line(name, gs):
        o = sum(g["hs"] + g["as"] > g["total"] for g in gs); u = sum(g["hs"] + g["as"] < g["total"] for g in gs)
        return f"<tr><td class=\"t\">{e(name)}</td><td>{len(gs)}</td><td>{o}-{u}-{len(gs) - o - u}</td><td>{pct(o, u)}</td></tr>"
    bands = [("Total of 7 or lower", [g for g in cg if g["total"] <= 7]), ("Total of 7.5 to 8", [g for g in cg if 7 < g["total"] <= 8]),
             ("Total of 8.5 to 9", [g for g in cg if 8 < g["total"] <= 9]), ("Total of 9.5 or higher", [g for g in cg if g["total"] > 9])]
    months = collections.OrderedDict()
    for g in sorted(cg, key=lambda g: g["date"]):
        months.setdefault(dt.date.fromisoformat(g["date"]).strftime("%B"), []).append(g)
    inter = [g for g in cg if m.TEAMS[g["home"]][2] != m.TEAMS[g["away"]][2]]
    div = [g for g in cg if m.TEAMS[g["home"]][2:] == m.TEAMS[g["away"]][2:]]
    sit = [*bands, ("Division games", div), ("Interleague games", inter), *[(f"{k}", v) for k, v in months.items()]]
    sit_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Situation</th><th>Games</th><th>O/U/P</th><th>Over %</th></tr></thead><tbody>'
               + "".join(ou_line(n, gs) for n, gs in sit if gs) + "</tbody></table></div>")
    # team over % by season matrix (last 6 seasons)
    seasons = sorted({g["season"] for g in games}, reverse=True)[:6]
    mrows = []
    for t in sorted(m.TEAMS, key=lambda t: SHORT[t]):
        cells = []
        for s in seasons:
            a = m.agg(m.team_rows([g for g in games if g["season"] == s], t))
            cells.append(f"<td>{pct(a['o'], a['u'])}</td>")
        mrows.append(f"<tr><td class=\"t\">{team_link(t)}</td>{''.join(cells)}</tr>")
    matrix = ('<div class="tr-wrap"><table><thead><tr><th>Team</th>' + "".join(f"<th>{s}</th>" for s in seasons) + '</tr></thead><tbody>'
              + "".join(mrows) + "</tbody></table></div>")
    top, bot = data[0], data[-1]
    lg = [g for g in cg]
    lo = sum(g["hs"] + g["as"] > g["total"] for g in lg); lu = sum(g["hs"] + g["as"] < g["total"] for g in lg)
    when = f"the {cur} regular season" if finished else f"{cur} through {fdate(last_date)}"
    lead = (f"Every MLB team's over/under record for {when} against the closing total. Overs went {lo}-{lu} league wide ({pct(lo, lu)}). "
            f"The {top[0]} were the best over team at {top[1]['o']}-{top[1]['u']}-{top[1]['p']}, and the {bot[0]} the best under team at "
            f"{bot[1]['o']}-{bot[1]['u']}-{bot[1]['p']}.")
    price_note = ("Over and under units bet 1 unit on every game at the DraftKings closing total and price published by ESPN." if ok else
                  "Units are shown only for seasons where at least 95% of games have a published closing over/under price.")
    faq = [
        (f"Which MLB team went over the most in {cur}?", f"The {top[0]}: {top[1]['o']}-{top[1]['u']}-{top[1]['p']} against the closing total ({pct(top[1]['o'], top[1]['u'])} overs)."),
        (f"Which MLB team went under the most in {cur}?", f"The {bot[0]}: {bot[1]['o']}-{bot[1]['u']}-{bot[1]['p']} ({pct(bot[1]['u'], bot[1]['o'])} unders)."),
        (f"How often did MLB games go over in {cur}?", f"{lo} overs, {lu} unders and {len(lg) - lo - lu} pushes, so overs hit {pct(lo, lu)} of decided games."),
        ("What is the average MLB closing total?", f"{sum(g['total'] for g in lg) / len(lg):.2f} runs in {cur}, against {sum(g['hs'] + g['as'] for g in lg) / len(lg):.2f} actual runs per game."),
    ]
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing totals, regular season games only. {e(price_note)}</p>
<ul class="tr-jump"><li><a href="#teams">{cur} by team</a></li><li><a href="#situations">Situations</a></li><li><a href="#seasons">League by season</a></li><li><a href="#history">Team over % by season</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="teams"><h2>MLB team over/under records, {cur}</h2>
<p>Sorted by over percentage (pushes excluded). Runs vs total is the average actual total runs minus the average closing total; positive means the team's games ran over the number on average.</p>
{table}
</section>
<section id="situations"><h2>Over/under by situation, {cur}</h2>
{sit_tbl}
</section>
<section id="seasons"><h2>MLB over/under results by season</h2>
{season_tbl}
</section>
<section id="history"><h2>Team over percentage by season</h2>
<p>Each team's share of overs (pushes excluded) in each of the last {len(seasons)} seasons. Click a team for its full betting record.</p>
{matrix}
</section>
<section id="faq"><h2>MLB over/under FAQ</h2>
{"".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)}
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and closing totals for every regular season game since 2016 come from the Bet Legend game database. A game goes over when total runs beat the closing total, under when they fall short, and pushes on an exact match. {e(price_note)} Units use the DraftKings closing total and price that ESPN publishes for each game; when that book closed at a different total than the one in our database, the unit result follows the DraftKings number, so a game can count as an over in the record and still lose in the units column. These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="{m.HUB}">MLB team betting records</a></li><li><a href="{RL_HUB}">MLB run line records</a></li><li><a href="how-to-bet-mlb-totals.html">How to bet MLB totals</a></li><li><a href="mlb-picks-today.html">MLB picks today</a></li><li><a href="mlb.html">MLB odds, stats and picks</a></li><li><a href="ev-calculator.html">Expected value calculator</a></li></ul>
</section>"""
    title = f"MLB Team Over/Under Records {cur}: Over %, Totals & Trends"
    desc = (f"Every MLB team's {cur} over/under record against the closing total: over and under %, pushes, average total vs actual runs, "
            f"home/road splits, situations and over % by season since 2016.")
    h1 = f"MLB Team Over/Under Records {cur}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": m.SITE + OU_HUB, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat()},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", m.HUB), ("Over/Under Records", None)]
    return m.shell(OU_HUB, title, desc, h1, EXTRA_CSS + body, ld, crumbs, now_pt)


# ---------------------------------------------------------------- RL hub

def build_rl_hub(games, cur, now_pt, finished, last_date):
    cur_games = [g for g in games if g["season"] == cur]
    rl_priced = priced_seasons(games, "rlp")
    ok = cur in rl_priced
    data = []
    for t in m.TEAMS:
        rs = rows_for(cur_games, t)
        a = m.agg(rs)
        fav = [r for r in rs if r["line"] is not None and r["line"] < 0]; dog = [r for r in rs if r["line"] is not None and r["line"] > 0]
        data.append((t, a, rs, fav, dog))
    data.sort(key=lambda x: -(x[1]["cov"] / max(1, x[1]["cov"] + x[1]["ncov"])))
    trs = []
    for i, (t, a, rs, fav, dog) in enumerate(data, 1):
        fa, da = m.agg(fav), m.agg(dog)
        h = m.agg([r for r in rs if r["home"]]); rd = m.agg([r for r in rs if not r["home"]])
        trs.append(f"<tr><td>{i}</td><td class=\"t\">{team_link(t)}</td><td>{a['cov']}-{a['ncov']}</td><td>{pct(a['cov'], a['ncov'])}</td>"
                   f"{units_cell(rs, 'rl_units', ok)}<td>{fa['cov']}-{fa['ncov']}</td>{units_cell(fav, 'rl_units', ok)}"
                   f"<td>{da['cov']}-{da['ncov']}</td>{units_cell(dog, 'rl_units', ok)}<td>{h['cov']}-{h['ncov']}</td><td>{rd['cov']}-{rd['ncov']}</td></tr>")
    table = ('<div class="tr-wrap"><table><thead><tr><th>#</th><th>Team</th><th>Run line</th><th>Cover %</th><th>RL units</th>'
             '<th>As -1.5 fav</th><th>Fav units</th><th>As +1.5 dog</th><th>Dog units</th><th>Home</th><th>Road</th></tr></thead><tbody>'
             + "".join(trs) + "</tbody></table></div>")
    # league: favorites -1.5 by moneyline band, home/road
    cg = [g for g in cur_games if g["line"] is not None and abs(g["line"]) == 1.5 and g["hml"] is not None]

    def fav_rows(lo, hi):
        rs = []
        for g in cg:
            home_fav = g["hml"] < g["aml"]
            fml = g["hml"] if home_fav else g["aml"]
            if not (lo <= -fml < hi):
                continue
            margin = (g["hs"] - g["as"]) if home_fav else (g["as"] - g["hs"])
            fav_line = g["line"] if home_fav else -g["line"]
            if fav_line != -1.5:
                continue
            won = margin >= 2
            price = None
            if "rlp" in g and (g["rlp"][0] if home_fav else -g["rlp"][0]) == -1.5:
                price = g["rlp"][1] if home_fav else g["rlp"][2]
            rs.append((won, price, home_fav, margin > 0))
        return rs
    bands = [("Favorites of -110 to -149", 110, 150), ("Favorites of -150 to -199", 150, 200), ("Favorites of -200 or more", 200, 10000)]
    brows = []
    for name, lo, hi in bands:
        rs = fav_rows(lo, hi)
        if not rs:
            continue
        w = sum(r[0] for r in rs); ml_w = sum(r[3] for r in rs)
        pr = [r for r in rs if r[1] is not None]
        uc = f'<td class="{cls(sum(profit(r[1], r[0]) for r in pr))}">{fu(sum(profit(r[1], r[0]) for r in pr))}</td>' if ok and pr else '<td class="na">not priced</td>'
        brows.append(f"<tr><td class=\"t\">{name}</td><td>{len(rs)}</td><td>{ml_w}-{len(rs) - ml_w}</td><td>{w}-{len(rs) - w}</td><td>{pct(w, len(rs) - w)}</td>{uc}</tr>")
    band_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Favorite price</th><th>Games</th><th>Won outright</th><th>Covered -1.5</th><th>Cover %</th><th>-1.5 units</th></tr></thead><tbody>'
                + "".join(brows) + "</tbody></table></div>")
    # by season league: favorites -1.5 cover %, home favorites
    srows = []
    for s in sorted({g["season"] for g in games}, reverse=True):
        gs = [g for g in games if g["season"] == s and g["line"] is not None and abs(g["line"]) == 1.5]
        fav_cov = sum(((g["hs"] - g["as"]) if g["line"] < 0 else (g["as"] - g["hs"])) >= 2 for g in gs)
        hf = [g for g in gs if g["line"] < 0]; hfc = sum(g["hs"] - g["as"] >= 2 for g in hf)
        srows.append(f"<tr><td>{s}</td><td>{len(gs)}</td><td>{fav_cov}-{len(gs) - fav_cov}</td><td>{pct(fav_cov, len(gs) - fav_cov)}</td>"
                     f"<td>{hfc}-{len(hf) - hfc}</td><td>{pct(hfc, len(hf) - hfc)}</td></tr>")
    season_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Games</th><th>-1.5 favorites</th><th>Cover %</th><th>Home -1.5 favorites</th><th>Cover %</th></tr></thead><tbody>'
                  + "".join(srows) + "</tbody></table></div>")
    # team cover % by season matrix
    seasons = sorted({g["season"] for g in games}, reverse=True)[:6]
    mrows = []
    for t in sorted(m.TEAMS, key=lambda t: SHORT[t]):
        cells = "".join(f"<td>{(lambda a: pct(a['cov'], a['ncov']))(m.agg(m.team_rows([g for g in games if g['season'] == s], t)))}</td>" for s in seasons)
        mrows.append(f"<tr><td class=\"t\">{team_link(t)}</td>{cells}</tr>")
    matrix = ('<div class="tr-wrap"><table><thead><tr><th>Team</th>' + "".join(f"<th>{s}</th>" for s in seasons) + "</tr></thead><tbody>"
              + "".join(mrows) + "</tbody></table></div>")
    top, bot = data[0], data[-1]
    allfav = fav_rows(0, 10000); fw = sum(r[0] for r in allfav)
    when = f"the {cur} regular season" if finished else f"{cur} through {fdate(last_date)}"
    lead = (f"Every MLB team's run line record for {when} at the closing 1.5 run line. The {top[0]} covered most often ({top[1]['cov']}-{top[1]['ncov']}), "
            f"the {bot[0]} least ({bot[1]['cov']}-{bot[1]['ncov']}). League wide, -1.5 favorites covered {pct(fw, len(allfav) - fw)} of the time.")
    price_note = ("Run line units bet 1 unit on that side at the DraftKings closing run line and price published by ESPN." if ok else
                  "Units are shown only for seasons where at least 95% of games have a published closing run line price.")
    faq = [
        (f"Which MLB team has the best run line record in {cur}?", f"The {top[0]}: {top[1]['cov']}-{top[1]['ncov']} ({pct(top[1]['cov'], top[1]['ncov'])})."),
        (f"How often do MLB favorites cover -1.5?", f"In {cur}, -1.5 favorites covered {fw} of {len(allfav)} games ({pct(fw, len(allfav) - fw)}). Bigger favorites cover more often, but the run line price gets shorter too; see the price table above."),
        ("Can an MLB run line push?", "No. MLB run lines are 1.5 runs, so every game is a cover or a loss."),
    ]
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing run lines, regular season games only. {e(price_note)}</p>
<ul class="tr-jump"><li><a href="#teams">{cur} by team</a></li><li><a href="#price">By favorite price</a></li><li><a href="#seasons">League by season</a></li><li><a href="#history">Team cover % by season</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="teams"><h2>MLB run line records by team, {cur}</h2>
<p>Sorted by cover percentage. "As -1.5 fav" is the team laying 1.5 runs; "As +1.5 dog" is the team getting 1.5 runs.</p>
{table}
</section>
<section id="price"><h2>How -1.5 favorites cover by moneyline price, {cur}</h2>
<p>A favorite has to win by two or more runs to cover. This shows how often each price band wins outright and how often it wins by two.</p>
{band_tbl}
</section>
<section id="seasons"><h2>Run line results by season</h2>
{season_tbl}
</section>
<section id="history"><h2>Team run line cover % by season</h2>
{matrix}
</section>
<section id="faq"><h2>MLB run line FAQ</h2>
{"".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)}
</section>
<section id="method"><h2>Methodology</h2>
<p>Final scores and the closing 1.5 run line for every regular season game since 2016 come from the Bet Legend game database. A side covers when its final margin plus its run line is above zero. {e(price_note)} Units use the DraftKings closing run line and price that ESPN publishes for each game; on the few games where that book hung the run line the other way, the unit result follows the DraftKings line. These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
<ul class="links"><li><a href="{m.HUB}">MLB team betting records</a></li><li><a href="{OU_HUB}">MLB over/under records</a></li><li><a href="spread-vs-moneyline-betting.html">Moneyline vs spread explained</a></li><li><a href="mlb-picks-today.html">MLB picks today</a></li><li><a href="mlb.html">MLB odds, stats and picks</a></li><li><a href="parlay-calculator.html">Parlay calculator</a></li></ul>
</section>"""
    title = f"MLB Run Line Records {cur}: Cover % by Team, Favorites & Dogs"
    desc = (f"Every MLB team's {cur} run line record at the closing 1.5 line: cover %, units, as favorite and underdog, home and road, "
            f"how -1.5 favorites cover by price, and cover % by season since 2016.")
    h1 = f"MLB Run Line Records {cur}"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": m.SITE + RL_HUB, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat()},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", m.HUB), ("Run Line Records", None)]
    return m.shell(RL_HUB, title, desc, h1, EXTRA_CSS + body, ld, crumbs, now_pt)


# ---------------------------------------------------------------- rivalry pages

def build_rivalry(a, b, games, now_pt):
    file = rivalry_file(a, b)
    meet = [g for g in games if {g["home"], g["away"]} == {a, b}]
    ra = rows_for(meet, a)  # from a's side
    rb = rows_for(meet, b)
    seasons = sorted({r["season"] for r in ra}, reverse=True)
    A, B = SHORT[a], SHORT[b]
    aa, bb = m.agg(ra), m.agg(rb)
    rl_ok_seasons = priced_seasons(meet, "rlp")
    first, last = ra[0], ra[-1]
    span = f"{seasons[-1]} to {seasons[0]}"
    # favorites in the series
    fav_w = sum(1 for r in ra if r["ml"] is not None and r["oml"] is not None and r["ml"] != r["oml"] and (r["fav"] == r["won"]))
    fav_n = sum(1 for r in ra if r["ml"] is not None and r["oml"] is not None and r["ml"] != r["oml"])
    fav_units = sum(r["units"] if r["fav"] else (rb_r["units"]) for r, rb_r in zip(ra, rb) if r["ml"] is not None and r["oml"] is not None and r["ml"] != r["oml"] and r["units"] is not None and rb_r["units"] is not None) if fav_n else 0
    dog_units = sum(rb_r["units"] if r["fav"] else r["units"] for r, rb_r in zip(ra, rb) if r["ml"] is not None and r["oml"] is not None and r["ml"] != r["oml"] and r["units"] is not None and rb_r["units"] is not None) if fav_n else 0
    # season table
    srows = []
    for s in seasons:
        sa = m.agg([r for r in ra if r["season"] == s]); sb = m.agg([r for r in rb if r["season"] == s])
        srows.append(f"<tr><td>{s}</td><td>{sa['n']}</td><td>{sa['w']}-{sa['l']}</td><td class=\"{cls(sa['units'])}\">{fu(sa['units'])}</td>"
                     f"<td class=\"{cls(sb['units'])}\">{fu(sb['units'])}</td><td>{sa['cov']}-{sa['ncov']}</td><td>{sa['o']}-{sa['u']}-{sa['p']}</td>"
                     f"<td>{sa['avg_total']:.2f}</td><td>{sa['rpg'] + sa['rapg']:.2f}</td></tr>")
    srows.append(f"<tr><td><strong>All</strong></td><td>{aa['n']}</td><td><strong>{aa['w']}-{aa['l']}</strong></td><td class=\"{cls(aa['units'])}\"><strong>{fu(aa['units'])}</strong></td>"
                 f"<td class=\"{cls(bb['units'])}\"><strong>{fu(bb['units'])}</strong></td><td>{aa['cov']}-{aa['ncov']}</td><td>{aa['o']}-{aa['u']}-{aa['p']}</td>"
                 f"<td>{aa['avg_total']:.2f}</td><td>{aa['rpg'] + aa['rapg']:.2f}</td></tr>")
    season_tbl = (f'<div class="tr-wrap"><table><thead><tr><th>Season</th><th>Games</th><th>{e(A)} record</th><th>{e(A)} ML units</th><th>{e(B)} ML units</th>'
                  f'<th>{e(A)} run line</th><th>O/U/P</th><th>Avg total</th><th>Avg runs</th></tr></thead><tbody>' + "".join(srows) + "</tbody></table></div>")
    # venue
    va = m.agg([r for r in ra if r["home"]]); vb = m.agg([r for r in ra if not r["home"]])
    venue_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Venue</th><th>Games</th><th>' + e(A) + ' record</th><th>' + e(A) + ' ML units</th><th>'
                 + e(A) + ' run line</th><th>O/U/P</th><th>Avg total</th><th>Avg runs</th></tr></thead><tbody>'
                 f"<tr><td class=\"t\">At {e(A)} home park</td><td>{va['n']}</td><td>{va['w']}-{va['l']}</td><td class=\"{cls(va['units'])}\">{fu(va['units'])}</td><td>{va['cov']}-{va['ncov']}</td><td>{va['o']}-{va['u']}-{va['p']}</td><td>{va['avg_total']:.2f}</td><td>{va['rpg'] + va['rapg']:.2f}</td></tr>"
                 f"<tr><td class=\"t\">At {e(B)} home park</td><td>{vb['n']}</td><td>{vb['w']}-{vb['l']}</td><td class=\"{cls(vb['units'])}\">{fu(vb['units'])}</td><td>{vb['cov']}-{vb['ncov']}</td><td>{vb['o']}-{vb['u']}-{vb['p']}</td><td>{vb['avg_total']:.2f}</td><td>{vb['rpg'] + vb['rapg']:.2f}</td></tr>"
                 "</tbody></table></div>")
    # recent meetings
    rec = []
    for r in ra[-20:][::-1]:
        home_t, away_t = (a, b) if r["home"] else (b, a)
        hs, as_ = (r["rf"], r["ra"]) if r["home"] else (r["ra"], r["rf"])
        hml, aml = (r["ml"], r["oml"]) if r["home"] else (r["oml"], r["ml"])
        ou = {"O": "Over", "U": "Under", "P": "Push", None: "no line"}[r["ou"]]
        winner = home_t if hs > as_ else away_t
        tot = "no line" if r["total"] is None else f"{r['total']:g}"
        rec.append(f"<tr><td>{fdate(r['date'])}</td><td class=\"t\">{e(SHORT[away_t])} at {e(SHORT[home_t])}</td><td>{as_}-{hs}</td>"
                   f"<td>{e(SHORT[winner])}</td><td>{fodds(aml)} / {fodds(hml)}</td><td>{tot}</td><td>{ou}</td></tr>")
    rec_tbl = ('<div class="tr-wrap"><table><thead><tr><th>Date</th><th>Game</th><th>Score</th><th>Winner</th><th>Close ML (away / home)</th><th>Total</th><th>O/U</th></tr></thead><tbody>'
               + "".join(rec) + "</tbody></table></div>")
    lean = "over" if aa["o"] > aa["u"] else ("under" if aa["u"] > aa["o"] else "neither way")
    leader = A if aa["w"] > aa["l"] else (B if aa["l"] > aa["w"] else None)
    lead = (f"The {A} and {B} have met {aa['n']} times in the regular season since {seasons[-1]}"
            + (f", and the {leader} lead the series {max(aa['w'], aa['l'])}-{min(aa['w'], aa['l'])}." if leader else f", and the series is tied {aa['w']}-{aa['l']}.")
            + f" Betting the {A} on the closing moneyline in every meeting returned {fu(aa['units'])}; betting the {B} returned {fu(bb['units'])}. "
            f"The games went {aa['o']}-{aa['u']}-{aa['p']} against the total, leaning {lean}.")
    stats = (f'<div class="tr-stats"><div><b>{aa["w"]}-{aa["l"]}</b><span>{e(A)} vs {e(B)}, {span}</span></div>'
             f'<div><b class="{cls(aa["units"])}">{fu(aa["units"])}</b><span>{e(A)} moneyline units</span></div>'
             f'<div><b class="{cls(bb["units"])}">{fu(bb["units"])}</b><span>{e(B)} moneyline units</span></div>'
             f'<div><b>{aa["o"]}-{aa["u"]}-{aa["p"]}</b><span>over, under, push ({pct(aa["o"], aa["u"])} overs)</span></div></div>')
    fav_line = (f"The moneyline favorite won {fav_w} of {fav_n} meetings with a clear favorite ({pct(fav_w, fav_n - fav_w)}). "
                f"Betting the favorite every time returned {fu(fav_units)}; betting the underdog every time returned {fu(dog_units)}.") if fav_n else ""
    last_meet = ra[-1]
    faq = [
        (f"Who leads the {A} vs {B} series since {seasons[-1]}?",
         (f"The {leader}, {max(aa['w'], aa['l'])}-{min(aa['w'], aa['l'])} in {aa['n']} regular season meetings." if leader else f"Nobody: it is {aa['w']}-{aa['l']}.")),
        (f"Is it profitable to bet the {A} against the {B}?",
         f"At closing moneylines the {A} returned {fu(aa['units'])} ({froi(aa['roi'])} ROI) over {aa['n']} games; the {B} returned {fu(bb['units'])}."),
        (f"Do {A} vs {B} games go over or under?",
         f"{aa['o']} overs, {aa['u']} unders and {aa['p']} pushes against the closing total. The average total was {aa['avg_total']:.2f} and the games averaged {aa['rpg'] + aa['rapg']:.2f} runs."),
        (f"How do the favorites do in {A} vs {B} games?", fav_line or "Not enough priced games."),
        (f"When did the {A} and {B} last play?",
         f"{fdate(last_meet['date'])}: {('the ' + A) if last_meet['won'] else ('the ' + B)} won {max(last_meet['rf'], last_meet['ra'])}-{min(last_meet['rf'], last_meet['ra'])}."),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)
    other = [(f"{SHORT[x]} vs {SHORT[y]} betting history", rivalry_file(x, y)) for x, y in rivalry_pairs()
             if (x, y) != (a, b) and ({x, y} & {a, b})]
    related = [(f"{a} betting record", m.page_file(a)), (f"{b} betting record", m.page_file(b)), *other,
               ("MLB over/under records", OU_HUB), ("MLB run line records", RL_HUB), ("All 30 MLB team betting records", m.HUB),
               ("MLB picks today", "mlb-picks-today.html")]
    related_html = '<ul class="links">' + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in related) + "</ul>"
    body = f"""<p class="lead">{e(lead)}</p>
<p class="upd">Updated {{UPDATED}}. Closing lines, regular season meetings only, {span}. <a href="#method">How these numbers are calculated</a>.</p>
<ul class="tr-jump"><li><a href="#summary">Summary</a></li><li><a href="#seasons">By season</a></li><li><a href="#venue">By ballpark</a></li><li><a href="#recent">Recent meetings</a></li><li><a href="#faq">FAQ</a></li></ul>
<section id="summary"><h2>{e(A)} vs {e(B)} betting summary</h2>
{stats}
<p>{e(fav_line)} The {e(A)} were {aa['cov']}-{aa['ncov']} on the run line in the series.</p>
</section>
<section id="seasons"><h2>{e(A)} vs {e(B)} results by season</h2>
<p>Moneyline units risk 1 unit on that team in every meeting at the closing price.</p>
{season_tbl}
</section>
<section id="venue"><h2>{e(A)} vs {e(B)} by ballpark</h2>
{venue_tbl}
</section>
<section id="recent"><h2>Last 20 {e(A)} vs {e(B)} games with closing odds</h2>
{rec_tbl}
</section>
<section id="faq"><h2>{e(A)} vs {e(B)} betting FAQ</h2>
{faq_html}
</section>
<section id="method"><h2>Methodology</h2>
<p>Every regular season meeting since {seasons[-1]} comes from the Bet Legend game database with its final score, closing moneylines, closing 1.5 run line and closing total, and each game is checked against ESPN's official final score; postseason meetings are not included. Moneyline units risk 1 unit at the close: a win at -150 pays +0.67u, a win at +130 pays +1.30u. Over and under compare total runs with the closing total, and an exact match is a push. A "clear favorite" is a game where the two closing moneylines differ. These are market results, not BetLegend picks.</p>
</section>
<section id="related"><h2>Related</h2>
{related_html}
</section>"""
    title = f"{A} vs {B} Betting History: Odds, Results & Trends"
    desc = (f"{A} vs {B} betting history since {seasons[-1]}: {aa['w']}-{aa['l']} head to head, moneyline units for both teams, "
            f"over/under {aa['o']}-{aa['u']}-{aa['p']}, run line, ballpark splits and closing odds for recent meetings.")
    h1 = f"{A} vs {B} Betting History"
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": m.SITE + file, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat(),
           "about": [{"@type": "SportsTeam", "name": a, "sport": "Baseball"}, {"@type": "SportsTeam", "name": b, "sport": "Baseball"}]},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
              {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", m.HUB), (f"{A} vs {B}", None)]
    return file, m.shell(file, title, desc, h1, EXTRA_CSS + body, ld, crumbs, now_pt), {"pair": (A, B), "games": aa["n"], "title": title}


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--prices", required=True, help="directory with close_prices_<season>.json")
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-espn-check", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(m.PT)
    cur = a.season
    games, report, finished = m.verified_games(a.db, cur, check=not a.no_espn_check)
    cur_games = [g for g in games if g["season"] == cur]
    st = attach_prices(games, a.prices)
    print(f"  prices: matched {st['matched']}, run line priced {st['rl']}, totals priced {st['ou']}")
    print("  run line priced seasons:", sorted(priced_seasons(games, "rlp")), " totals priced seasons:", sorted(priced_seasons(games, "oup")))
    last_date = max(g["date"] for g in cur_games)
    out = {OU_HUB: build_ou_hub(games, cur, now_pt, finished, last_date), RL_HUB: build_rl_hub(games, cur, now_pt, finished, last_date)}
    meta = []
    for x, y in rivalry_pairs():
        f, page, info = build_rivalry(x, y, games, now_pt)
        out[f] = page; meta.append(info)
    titles = [i["title"] for i in meta]
    assert len(set(titles)) == len(titles)
    if not a.dry_run:
        for f, page in out.items():
            with open(os.path.join(ROOT, f), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(page)
    print(f"[mlb_data_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages ({len(meta)} rivalries); "
          f"fewest meetings {min(i['games'] for i in meta)}, most {max(i['games'] for i in meta)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
