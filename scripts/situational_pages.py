#!/usr/bin/env python3
"""Situational betting data pages (Phase 5 SEO, Oct 1 2026), all from ESPN verified regular season games:

  /mlb-favorites-underdogs-records.html   how MLB favorites and underdogs do by moneyline price, home and road, by season
  /nba-favorites-underdogs-ats.html       how NBA favorites and underdogs do by spread size, straight up and ATS, by season
  /nhl-back-to-back-records.html          NHL second night of back to backs, by season, rest matchups and team

    python scripts/situational_pages.py --db DATASET.sqlite --prices DIR [--dry-run]
"""
import argparse
import collections
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402
import nhl_data_pages as nhl  # noqa: E402
import nba_data_pages as nba  # noqa: E402
import espn_verify  # noqa: E402

e, fu, froi, pct, cls = m.e, m.fu, m.froi, m.pct, m.cls
MLB_FILE, NBA_FILE, NHL_FILE = "mlb-favorites-underdogs-records.html", "nba-favorites-underdogs-ats.html", "nhl-back-to-back-records.html"
CSS = "<style>.tr td.na{color:#7d8592;font-size:.8rem}</style>"


def table(head, rows):
    return nba.table(head, rows)


def faq_block(faq):
    return f"<section id=\"faq\"><h2>FAQ</h2>{nba.faq_html(faq)}</section>"


def page(file, title, desc, h1, body, faq, crumbs, now_pt):
    ld = [{"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": m.SITE + file, "description": desc,
           "dateModified": now_pt.replace(microsecond=0).isoformat()}, nba.faq_ld(faq)]
    return m.shell(file, title, desc, h1, CSS + body + faq_block(faq), ld, crumbs, now_pt)


# ---------------------------------------------------------------- MLB favorites and underdogs

def mlb_page(db, now_pt):
    games, _, _ = m.verified_games(db, 2026)
    games = [g for g in games if g["hml"] is not None and g["aml"] is not None and g["hml"] != g["aml"]]
    seasons = sorted({g["season"] for g in games}, reverse=True)

    def side(g, fav):
        home_fav = g["hml"] < g["aml"]
        is_home = home_fav if fav else not home_fav
        price = g["hml"] if is_home else g["aml"]
        won = (g["hs"] > g["as"]) if is_home else (g["as"] > g["hs"])
        return is_home, price, won

    bands = [("Favorites of -100 to -129", True, lambda p: -130 < p <= -100), ("Favorites of -130 to -159", True, lambda p: -160 < p <= -130),
             ("Favorites of -160 to -199", True, lambda p: -200 < p <= -160), ("Favorites of -200 or more", True, lambda p: p <= -200),
             ("Underdogs of +100 to +129", False, lambda p: 100 <= p < 130), ("Underdogs of +130 to +159", False, lambda p: 130 <= p < 160),
             ("Underdogs of +160 or longer", False, lambda p: p >= 160)]

    def stat(gs, fav, where=None, band=None):
        w = l = 0; u = 0.0; implied = []
        for g in gs:
            is_home, price, won = side(g, fav)
            if where is not None and is_home != where:
                continue
            if band is not None and not band(price):
                continue
            w += won; l += not won; u += m.ml_profit(price, won)
            implied.append(abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100))
        n = w + l
        return w, l, u, (u / n * 100 if n else 0.0), (sum(implied) / len(implied) * 100 if implied else 0.0)

    def row(name, s):
        w, l, u, roi, imp = s
        return (f"<tr><td class=\"t\">{e(name)}</td><td>{w + l}</td><td>{w}-{l}</td><td>{pct(w, l)}</td><td>{imp:.1f}%</td>"
                f"<td class=\"{cls(u)}\">{fu(u)}</td><td>{froi(roi)}</td></tr>")
    head = ["Situation", "Games", "Record", "Win %", "Implied win %", "Units", "ROI"]
    allg = games
    t_all = table(head, [row(n, stat(allg, f, band=b)) for n, f, b in bands])
    t_hr = table(head, [row("Home favorites", stat(allg, True, True)), row("Road favorites", stat(allg, True, False)),
                        row("Home underdogs", stat(allg, False, True)), row("Road underdogs", stat(allg, False, False))])
    srows = []
    for s in seasons:
        gs = [g for g in games if g["season"] == s]
        fw, fl, fuu, froi_, _ = stat(gs, True); dw, dl, duu, droi, _ = stat(gs, False)
        hw, hl, hu, _, _ = stat(gs, False, True)
        srows.append(f"<tr><td>{s}</td><td>{fw + fl}</td><td>{fw}-{fl}</td><td>{pct(fw, fl)}</td><td class=\"{cls(fuu)}\">{fu(fuu)}</td>"
                     f"<td class=\"{cls(duu)}\">{fu(duu)}</td><td>{hw}-{hl}</td><td class=\"{cls(hu)}\">{fu(hu)}</td></tr>")
    t_season = table(["Season", "Games", "Favorites", "Favorite win %", "Favorite units", "Underdog units", "Home dogs", "Home dog units"], srows)
    cur = [g for g in games if g["season"] == 2026]
    t_cur = table(head, [row(n, stat(cur, f, band=b)) for n, f, b in bands])
    fw, fl, fuu, froi_, _ = stat(allg, True)
    dw, dl, duu, droi, _ = stat(allg, False)
    hd = stat(allg, False, True)
    faq = [("How often do MLB favorites win?", f"Since {seasons[-1]}, moneyline favorites won {pct(fw, fl)} of regular season games ({fw}-{fl}). The bigger the favorite, the more often it wins, as the price table shows."),
           ("Is it profitable to bet every MLB underdog?", f"Not blindly: one unit on every underdog at the closing price returned {fu(duu)} ({froi(droi)}) since {seasons[-1]}; every favorite returned {fu(fuu)} ({froi(froi_)})."),
           ("How do home underdogs do in MLB?", f"{hd[0]}-{hd[1]} since {seasons[-1]} for {fu(hd[2])} at closing prices."),
           ("What does implied win % mean?", "The win rate the closing price implies (with the bookmaker's margin included). When the actual win % is above it, that group of bets made money.")]
    body = (f"<p class=\"lead\">{e(f'How MLB moneyline favorites and underdogs have actually done at closing prices since {seasons[-1]}: favorites won {pct(fw, fl)} of games. Every row is computed from ESPN verified regular season games.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only; pick em games (equal moneylines) are left out.</p>"
            f"<section id=\"price\"><h2>MLB favorites and underdogs by price, {seasons[-1]} to {seasons[0]}</h2>{t_all}</section>"
            f"<section id=\"venue\"><h2>Home and road favorites and underdogs</h2>{t_hr}</section>"
            f"<section id=\"current\"><h2>2026 by price</h2>{t_cur}</section>"
            f"<section id=\"seasons\"><h2>Favorites and underdogs by season</h2>{t_season}</section>"
            "<section id=\"method\"><h2>Methodology</h2><p>Final scores and closing moneylines come from the Bet Legend game database, with every game checked against ESPN's official schedule and final score. "
            "Units risk 1 unit per game at the closing price. These are market results, not BetLegend picks.</p></section>"
            "<section id=\"related\"><h2>Related</h2><ul class=\"links\"><li><a href=\"mlb-team-betting-records.html\">MLB team betting records</a></li>"
            "<li><a href=\"mlb-run-line-records.html\">MLB run line records</a></li><li><a href=\"mlb-team-over-under-records.html\">MLB over/under records</a></li>"
            "<li><a href=\"mlb-picks-today.html\">MLB picks today</a></li><li><a href=\"ev-calculator.html\">Expected value calculator</a></li>"
            "<li><a href=\"no-vig-calculator.html\">No vig calculator</a></li></ul></section>")
    return page(MLB_FILE, "MLB Favorites and Underdogs Records: Win % and Units by Moneyline",
                f"How MLB moneyline favorites and underdogs have done since {seasons[-1]} at closing prices: win % vs implied odds, units and ROI by price band, home and road, and by season.",
                "MLB Favorites and Underdogs Betting Records", body, faq,
                [("Home", "/"), ("MLB", "mlb.html"), ("MLB Team Betting Records", m.HUB), ("Favorites and Underdogs", None)], now_pt)


# ---------------------------------------------------------------- NBA favorites and underdogs by spread

def nba_games(db, prices):
    raw = [g for g in nba.load_games(db) if g["home"] in nba.TEAMS and g["away"] in nba.TEAMS]
    cur = nba.current_season(raw)
    games, _, cov, bad, _ = espn_verify.verify(raw, "nba", {t: nba.TEAMS[t][3] for t in nba.TEAMS}, nba.ALIASES, lambda s: s + 1, cur, nba.TEAMS)
    if bad:
        sys.exit(f"ABORT NBA: {bad}")
    games = nba.drop_cup_finals(games)
    nba.attach_prices(games, prices)
    for g in games:
        if g["season"] >= nba.SPREAD_FROM_CLOSE:
            g["line"] = g["spp"][0] if "spp" in g else None
    return games, cur


def nba_page(db, prices, now_pt):
    games, cur = nba_games(db, prices)
    games = [g for g in games if g["line"] is not None and g["line"] != 0]
    seasons = sorted({g["season"] for g in games}, reverse=True)
    lab = nba.label

    def fav(g):
        home_fav = g["line"] < 0
        margin = (g["hs"] - g["as"]) if home_fav else (g["as"] - g["hs"])
        return home_fav, abs(g["line"]), margin

    bands = [("1 to 3.5", 0, 3.5), ("4 to 6.5", 3.5, 6.5), ("7 to 9.5", 6.5, 9.5), ("10 to 12.5", 9.5, 12.5), ("13 or more", 12.5, 99)]

    def stat(gs, lo=0, hi=99, home=None):
        su_w = su_l = c = n_ = p = 0
        for g in gs:
            hf, sp, mg = fav(g)
            if not (lo < sp <= hi) or (home is not None and hf != home):
                continue
            su_w += mg > 0; su_l += mg < 0
            if mg - sp > 0:
                c += 1
            elif mg - sp < 0:
                n_ += 1
            else:
                p += 1
        return su_w, su_l, c, n_, p

    def row(name, s):
        w, l, c, n_, p = s
        ats = f"{c}-{n_}" + (f"-{p}" if p else "")
        return (f"<tr><td class=\"t\">{e(name)}</td><td>{w + l}</td><td>{w}-{l}</td><td>{pct(w, l)}</td><td>{ats}</td><td>{pct(c, n_)}</td>"
                f"<td>{ats_dog(n_, c, p)}</td><td>{pct(n_, c)}</td></tr>")

    def ats_dog(n_, c, p):
        return f"{n_}-{c}" + (f"-{p}" if p else "")
    head = ["Favorite by", "Games", "Favorite record", "Favorite win %", "Favorite ATS", "Favorite cover %", "Underdog ATS", "Underdog cover %"]
    t_all = table(head, [row(n, stat(games, lo, hi)) for n, lo, hi in bands] + [row("All favorites", stat(games))])
    t_hr = table(head, [row("Home favorites", stat(games, home=True)), row("Road favorites", stat(games, home=False))])
    cg = [g for g in games if g["season"] == cur]
    t_cur = table(head, [row(n, stat(cg, lo, hi)) for n, lo, hi in bands] + [row("All favorites", stat(cg))])
    srows = []
    for s in seasons:
        w, l, c, n_, p = stat([g for g in games if g["season"] == s])
        bw, bl, bc, bn, bp = stat([g for g in games if g["season"] == s], 9.5, 99)
        srows.append(f"<tr><td>{lab(s)}</td><td>{w}-{l}</td><td>{pct(w, l)}</td><td>{c}-{n_}-{p}</td><td>{pct(c, n_)}</td><td>{bc}-{bn}-{bp}</td><td>{pct(bc, bn)}</td></tr>")
    t_season = table(["Season", "Favorites SU", "Win %", "Favorites ATS", "Cover %", "Favorites of 10+ ATS", "Cover %"], srows)
    w, l, c, n_, p = stat(games)
    bw, bl, bc, bn, bp = stat(games, 9.5, 99)
    faq = [("How often do NBA favorites cover the spread?", f"Since {lab(seasons[-1])}, favorites covered {pct(c, n_)} of regular season games ({c}-{n_}-{p}) against the closing spread."),
           ("Do big NBA favorites cover?", f"Favorites of 10 or more points went {bc}-{bn}-{bp} ATS ({pct(bc, bn)}) and won {pct(bw, bl)} of those games outright."),
           ("How often do NBA favorites win outright?", f"{pct(w, l)} of the time since {lab(seasons[-1])} ({w}-{l}); see the table for each spread size."),
           ("Where do these spreads come from?", "The closing spread in the Bet Legend game database, and from 2024-25 on the sportsbook close that ESPN publishes, because the database's own spreads for those seasons were unreliable.")]
    body = (f"<p class=\"lead\">{e(f'How NBA favorites and underdogs have done against the closing spread since {lab(seasons[-1])}, by the size of the spread. Favorites covered {pct(c, n_)} of the time and won outright {pct(w, l)} of the time.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only, games with a pick em spread left out.</p>"
            f"<section id=\"spread\"><h2>NBA favorites and underdogs by spread, {lab(seasons[-1])} to {lab(seasons[0])}</h2>{t_all}</section>"
            f"<section id=\"venue\"><h2>Home and road favorites</h2>{t_hr}</section>"
            f"<section id=\"current\"><h2>{lab(cur)} by spread</h2>{t_cur}</section>"
            f"<section id=\"seasons\"><h2>Favorites by season</h2>{t_season}</section>"
            + nba.method() + nba.RELATED)
    return page(NBA_FILE, "NBA Favorites vs Underdogs ATS: Cover % by Spread Size",
                f"How NBA favorites and underdogs have done against the spread since {lab(seasons[-1])}: straight up and cover % by spread size, home and road favorites, and by season.",
                "NBA Favorites and Underdogs Against the Spread", body, faq,
                [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", nba.HUB), ("Favorites and Underdogs ATS", None)], now_pt)


# ---------------------------------------------------------------- NHL back to backs

def nhl_page(db, now_pt):
    raw = [g for g in nhl.load_games(db) if g["home"] in nhl.TEAMS and g["away"] in nhl.TEAMS]
    cur = nhl.current_season(raw)
    games, _, cov, bad, _ = espn_verify.verify(raw, "nhl", {t: nhl.TEAMS[t][3] for t in nhl.TEAMS}, nhl.ALIASES, lambda s: s + 1, cur, nhl.TEAMS)
    if bad:
        sys.exit(f"ABORT NHL: {bad}")
    seasons = sorted({g["season"] for g in games}, reverse=True)
    lab = nhl.label
    rows_by_season = {s: {t: nhl.rows_for([g for g in games if g["season"] == s], t) for t in nhl.TEAMS} for s in seasons}
    srows = []
    allb = []
    for s in seasons:
        b = [r for t in nhl.TEAMS for r in rows_by_season[s][t] if r["b2b"]]
        rest = [r for t in nhl.TEAMS for r in rows_by_season[s][t] if not r["b2b"]]
        allb += b
        x, y = m.agg(b), m.agg(rest)
        srows.append(f"<tr><td>{lab(s)}</td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td><td>{pct(x['w'], x['l'])}</td><td class=\"{cls(x['units'])}\">{fu(x['units'])}</td>"
                     f"<td>{x['cov']}-{x['ncov']}</td><td>{x['o']}-{x['u']}-{x['p']}</td><td>{pct(y['w'], y['l'])}</td></tr>")
    sit = collections.defaultdict(list)
    for s in seasons:
        idx = {t: {(r["date"], r["opp"]): r for r in rows_by_season[s][t]} for t in nhl.TEAMS}
        for g in (g for g in games if g["season"] == s):
            h = idx[g["home"]].get((g["date"], g["away"])); a = idx[g["away"]].get((g["date"], g["home"]))
            if not h or not a:
                continue
            if a["b2b"] and not h["b2b"]:
                sit["Home team rested, road team on a back to back"].append(h)
            elif h["b2b"] and not a["b2b"]:
                sit["Home team on a back to back, road team rested"].append(h)
            elif h["b2b"] and a["b2b"]:
                sit["Both teams on a back to back"].append(h)
    rrows = [f"<tr><td class=\"t\">{e(k)}</td><td>{m.agg(v)['n']}</td><td>{m.agg(v)['w']}-{m.agg(v)['l']}</td><td>{pct(m.agg(v)['w'], m.agg(v)['l'])}</td>"
             f"<td class=\"{cls(m.agg(v)['units'])}\">{fu(m.agg(v)['units'])}</td><td>{m.agg(v)['o']}-{m.agg(v)['u']}-{m.agg(v)['p']}</td></tr>" for k, v in sit.items()]
    trows = []
    for t in sorted(nhl.TEAMS, key=lambda t: nhl.TEAMS[t][0]):
        b = [r for s in seasons for r in rows_by_season[s][t] if r["b2b"]]
        x = m.agg(b)
        trows.append(f"<tr><td class=\"t\"><a href=\"{nhl.page_file(t)}\">{e(t)}</a></td><td>{x['n']}</td><td>{x['w']}-{x['l']}</td><td>{pct(x['w'], x['l'])}</td>"
                     f"<td class=\"{cls(x['units'])}\">{fu(x['units'])}</td><td>{x['o']}-{x['u']}-{x['p']}</td></tr>")
    xb = m.agg(allb)
    rested = sit["Home team rested, road team on a back to back"]
    xr = m.agg(rested)
    faq = [("How do NHL teams do on the second night of a back to back?", f"Since {lab(seasons[-1])}: {xb['w']}-{xb['l']} ({pct(xb['w'], xb['l'])}) and {fu(xb['units'])} for a 1 unit moneyline bettor at closing prices, over {xb['n']} games."),
           ("Should you bet against tired road teams?", f"When the home team was rested and the road team was on a back to back, home teams went {xr['w']}-{xr['l']} for {fu(xr['units'])} on the moneyline."),
           ("Do back to backs affect NHL totals?", f"Games where a team played the second night went {xb['o']}-{xb['u']}-{xb['p']} against the closing total from that team's side."),
           ("What counts as a back to back?", "A game played the day after the team's previous regular season game. Results include overtime and shootouts.")]
    xb_rec, xb_u = f"{xb['w']}-{xb['l']}", fu(xb["units"])
    body = (f"<p class=\"lead\">{e(f'How NHL teams do on the second night of a back to back at closing prices since {lab(seasons[-1])}: {xb_rec} straight up for {xb_u} on the moneyline.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only; results include overtime and shootouts.</p>"
            f"<section id=\"seasons\"><h2>Back to back results by season</h2>"
            + table(["Season", "B2B games", "Record", "Win %", "ML units", "Puck line", "O/U/P", "Win % with rest"], srows) + "</section>"
            f"<section id=\"rest\"><h2>Rest matchups, home team's side</h2>" + table(["Situation", "Games", "Home record", "Home win %", "Home ML units", "O/U/P"], rrows) + "</section>"
            f"<section id=\"teams\"><h2>Back to back record by team since {lab(seasons[-1])}</h2>" + table(["Team", "B2B games", "Record", "Win %", "ML units", "O/U/P"], trows) + "</section>"
            "<section id=\"method\"><h2>Methodology</h2><p>Final scores and closing lines for every regular season game since 2016-17 come from the Bet Legend game database, each checked against ESPN's official final score. "
            "Moneyline units risk 1 unit at the closing price. These are market results, not BetLegend picks.</p></section>"
            "<section id=\"related\"><h2>Related</h2><ul class=\"links\"><li><a href=\"nhl-team-betting-records.html\">NHL team betting records</a></li>"
            "<li><a href=\"nhl-puck-line-records.html\">NHL puck line records</a></li><li><a href=\"nhl-home-away-records.html\">NHL home and road betting records</a></li>"
            "<li><a href=\"nba-back-to-back-records.html\">NBA back to back records</a></li><li><a href=\"nhl.html\">NHL slate, odds and analysis</a></li></ul></section>")
    return page(NHL_FILE, "NHL Back to Back Records: Betting Results on the Second Night",
                f"How NHL teams do on the second night of a back to back since {lab(seasons[-1])}: record and moneyline units by season, rested vs tired matchups, and every team's back to back record.",
                "NHL Back to Back Betting Records", body, faq,
                [("Home", "/"), ("NHL", "nhl.html"), ("NHL Team Betting Records", nhl.HUB), ("Back to Back Records", None)], now_pt)


# ---------------------------------------------------------------- home and road (MLB, NBA)

def venue_page(sport, games, rows_for, teams, page_file, label, cur, line_word, now_pt):
    file = f"{sport.lower()}-home-road-records.html"
    seasons = sorted({g["season"] for g in games}, reverse=True)
    cg = [g for g in games if g["season"] == cur]
    data = []
    for t in teams:
        rs = rows_for(cg, t)
        h = [r for r in rs if r["home"]]; rd = [r for r in rs if not r["home"]]
        data.append((t, m.agg(h), m.agg(rd), h, rd))
    data.sort(key=lambda x: -(x[1]["w"] / max(1, x[1]["n"])))

    def rec(a):
        return f"{a['cov']}-{a['ncov']}"
    trs = [f"<tr><td>{i}</td><td class=\"t\"><a href=\"{page_file(t)}\">{e(t)}</a></td><td>{h['w']}-{h['l']}</td><td class=\"{cls(h['units'])}\">{fu(h['units'])}</td>"
           f"<td>{rec(h)}</td><td>{h['o']}-{h['u']}-{h['p']}</td><td>{r['w']}-{r['l']}</td><td class=\"{cls(r['units'])}\">{fu(r['units'])}</td>"
           f"<td>{rec(r)}</td><td>{r['o']}-{r['u']}-{r['p']}</td></tr>" for i, (t, h, r, _, _) in enumerate(data, 1)]
    t_team = table(["#", "Team", "Home record", "Home ML units", f"Home {line_word}", "Home O/U/P", "Road record", "Road ML units", f"Road {line_word}", "Road O/U/P"], trs)
    srows = []
    for s_ in seasons:
        gs = [g for g in games if g["season"] == s_]
        hw = sum(g["hs"] > g["as"] for g in gs); n = len(gs)
        hu = sum(m.ml_profit(g["hml"], g["hs"] > g["as"]) for g in gs if g["hml"])
        ru = sum(m.ml_profit(g["aml"], g["as"] > g["hs"]) for g in gs if g["aml"])
        lg = [g for g in gs if g["line"] is not None]
        hc = sum(g["hs"] - g["as"] + g["line"] > 0 for g in lg); hl = sum(g["hs"] - g["as"] + g["line"] < 0 for g in lg)
        srows.append(f"<tr><td>{label(s_)}</td><td>{n}</td><td>{hw}-{n - hw}</td><td>{pct(hw, n - hw)}</td><td class=\"{cls(hu)}\">{fu(hu)}</td>"
                     f"<td class=\"{cls(ru)}\">{fu(ru)}</td><td>{hc}-{hl}</td><td>{pct(hc, hl)}</td></tr>")
    t_season = table(["Season", "Games", "Home teams", "Home win %", "All home ML units", "All road ML units", f"Home {line_word}", "Home cover %"], srows)
    top = data[0]; bot = data[-1]; road_top = max(data, key=lambda x: x[2]["w"] / max(1, x[2]["n"]))
    gs = [g for g in games if g["season"] == cur]
    hw = sum(g["hs"] > g["as"] for g in gs)
    faq = [(f"Which {sport} team had the best home record in {label(cur)}?", f"The {top[0]}: {top[1]['w']}-{top[1]['l']} at home, {fu(top[1]['units'])} on the moneyline."),
           (f"Which {sport} team was the best on the road in {label(cur)}?", f"The {road_top[0]}: {road_top[2]['w']}-{road_top[2]['l']} on the road, {fu(road_top[2]['units'])}."),
           (f"How often do {sport} home teams win?", f"{pct(hw, len(gs) - hw)} of the time in {label(cur)}; the season table shows every year since {label(seasons[-1])}."),
           (f"Is betting {sport} home teams profitable?", "Rarely across a whole season: the home price already includes home advantage. The season table shows the units for betting every home or every road team at the close.")]
    top_rec = f"{top[1]['w']}-{top[1]['l']}"
    body = (f"<p class=\"lead\">{e(f'Every {sport} team at home and on the road in {label(cur)}, at closing lines. The {top[0]} had the best home record ({top_rec}) and the {bot[0]} the worst.')}</p>"
            f"<p class=\"upd\">Updated {{UPDATED}}. Regular season only. Click a team for its full betting record.</p>"
            f"<section id=\"teams\"><h2>{sport} home and road betting records, {label(cur)}</h2><p>Sorted by home win percentage.</p>{t_team}</section>"
            f"<section id=\"seasons\"><h2>Home teams by season</h2>{t_season}</section>"
            "<section id=\"method\"><h2>Methodology</h2><p>Final scores and closing lines come from the Bet Legend game database, each game checked against ESPN's official final score. "
            "Moneyline units risk 1 unit at the closing price. These are market results, not BetLegend picks.</p></section>")
    return file, page(file, f"{sport} Home and Road Records {label(cur)}: Betting Results by Team",
                      f"Every {sport} team's {label(cur)} home and road record at closing lines: moneyline units, {line_word.lower()} and over/under by venue, plus home team results by season since {label(seasons[-1])}.",
                      f"{sport} Home and Road Betting Records {label(cur)}", body, faq,
                      [("Home", "/"), (sport, f"{sport.lower()}.html"), (f"{sport} Team Betting Records", "mlb-team-betting-records.html" if sport == "MLB" else nba.HUB),
                       ("Home and Road Records", None)], now_pt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(m.PT)
    out = {MLB_FILE: mlb_page(a.db, now_pt), NBA_FILE: nba_page(a.db, a.prices, now_pt), NHL_FILE: nhl_page(a.db, now_pt)}
    mg, _, _ = m.verified_games(a.db, 2026)
    f, p = venue_page("MLB", mg, lambda gs, t: m.team_rows(gs, t), m.TEAMS, m.page_file, str, 2026, "Run line", now_pt)
    out[f] = p
    ng, ncur = nba_games(a.db, a.prices)
    f, p = venue_page("NBA", ng, nba.rows_for, nba.TEAMS, nba.page_file, nba.label, ncur, "ATS", now_pt)
    out[f] = p
    if not a.dry_run:
        for f, p in out.items():
            open(os.path.join(m.ROOT, f), "w", encoding="utf-8", newline="\n").write(p)
    print(f"[situational_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages")


if __name__ == "__main__":
    main()
