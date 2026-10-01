#!/usr/bin/env python3
"""NBA division rivalry betting history pages (Phase 5 SEO, Oct 1 2026): /<team>-vs-<team>-nba-betting-history.html
for the 60 division pairs, from the same ESPN verified game set as scripts/nba_data_pages.py (spreads from the
sportsbook close from 2024-25 on). Every regular season meeting since 2016-17: straight up, ATS, moneyline units
for both sides, totals, venue and season splits, and the last 15 meetings with closing lines.

    python scripts/nba_rivalry_pages.py --db DATASET.sqlite --prices DIR [--dry-run]
"""
import argparse
import datetime as dt
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402
import nba_data_pages as nba  # noqa: E402
import situational_pages as sit  # noqa: E402

e, fu, froi, pct, fodds, fdate, cls = m.e, m.fu, m.froi, m.pct, m.fodds, m.fdate, m.cls
INDEX = "nba-rivalry-betting-history.html"


def nick(t):
    return nba.TEAMS[t][0]


def slug(t):
    return nick(t).lower().replace(" ", "-")


def pairs():
    out = []
    for a, b in itertools.combinations(sorted(nba.TEAMS), 2):
        if nba.TEAMS[a][2] == nba.TEAMS[b][2]:
            out.append(tuple(sorted((a, b), key=nick)))
    return out


def file_for(a, b):
    return f"{slug(a)}-vs-{slug(b)}-nba-betting-history.html"


def build(a, b, games, now_pt):
    A, B = nick(a), nick(b)
    meet = [g for g in games if {g["home"], g["away"]} == {a, b}]
    ra, rb = nba.rows_for(meet, a), nba.rows_for(meet, b)
    seasons = sorted({r["season"] for r in ra}, reverse=True)
    lab = nba.label
    aa, bb = m.agg(ra), m.agg(rb)
    span = f"{lab(seasons[-1])} to {lab(seasons[0])}"
    srows = []
    for s in seasons:
        xa = [r for r in ra if r["season"] == s]; xb = [r for r in rb if r["season"] == s]
        sa, sb = m.agg(xa), m.agg(xb)
        srows.append(f"<tr><td>{lab(s)}</td><td>{sa['n']}</td><td>{sa['w']}-{sa['l']}</td><td>{nba.ats(sa, xa)}</td><td class=\"{cls(sa['units'])}\">{fu(sa['units'])}</td>"
                     f"<td class=\"{cls(sb['units'])}\">{fu(sb['units'])}</td><td>{sa['o']}-{sa['u']}-{sa['p']}</td><td>{sa['avg_total']:.1f}</td><td>{sa['rpg'] + sa['rapg']:.1f}</td></tr>")
    srows.append(f"<tr><td><strong>All</strong></td><td>{aa['n']}</td><td><strong>{aa['w']}-{aa['l']}</strong></td><td><strong>{nba.ats(aa, ra)}</strong></td>"
                 f"<td class=\"{cls(aa['units'])}\">{fu(aa['units'])}</td><td class=\"{cls(bb['units'])}\">{fu(bb['units'])}</td><td>{aa['o']}-{aa['u']}-{aa['p']}</td>"
                 f"<td>{aa['avg_total']:.1f}</td><td>{aa['rpg'] + aa['rapg']:.1f}</td></tr>")
    t_season = nba.table(["Season", "Games", f"{A} record", f"{A} ATS", f"{A} ML units", f"{B} ML units", "O/U/P", "Avg total", "Avg points"], srows)
    vh = [r for r in ra if r["home"]]; vr = [r for r in ra if not r["home"]]
    vrows = [f"<tr><td class=\"t\">{e(n)}</td><td>{m.agg(x)['n']}</td><td>{m.agg(x)['w']}-{m.agg(x)['l']}</td><td>{nba.ats(m.agg(x), x)}</td>"
             f"<td class=\"{cls(m.agg(x)['units'])}\">{fu(m.agg(x)['units'])}</td><td>{m.agg(x)['o']}-{m.agg(x)['u']}-{m.agg(x)['p']}</td></tr>"
             for n, x in ((f"At {A} home court", vh), (f"At {B} home court", vr)) if x]
    t_venue = nba.table(["Venue", "Games", f"{A} record", f"{A} ATS", f"{A} ML units", "O/U/P"], vrows)
    fav = [r for r in ra if r["line"] is not None and r["line"] != 0]
    fav_c = sum((r["cover"] is True) if r["line"] < 0 else (r["cover"] is False) for r in fav)
    fav_n = sum((r["cover"] is False) if r["line"] < 0 else (r["cover"] is True) for r in fav)
    fav_w = sum((r["won"]) if r["line"] < 0 else (not r["won"]) for r in fav)
    rec = []
    for r in ra[-15:][::-1]:
        home_t, away_t = (a, b) if r["home"] else (b, a)
        hs, as_ = (r["rf"], r["ra"]) if r["home"] else (r["ra"], r["rf"])
        home_line = None if r["line"] is None else (r["line"] if r["home"] else -r["line"])
        sp = "no line" if home_line is None else (f"{nick(home_t)} {home_line:+g}" if home_line < 0 else (f"{nick(away_t)} {-home_line:+g}" if home_line > 0 else "pick em"))
        ats_txt = "Push" if r["push_ats"] else ("no line" if r["cover"] is None else (f"{A} covered" if r["cover"] else f"{B} covered"))
        tot = "no line" if r["total"] is None else f"{r['total']:g}"
        ou = {"O": "Over", "U": "Under", "P": "Push", None: "no line"}[r["ou"]]
        rec.append(f"<tr><td>{fdate(r['date'])}</td><td class=\"t\">{e(nick(away_t))} at {e(nick(home_t))}</td><td>{as_}-{hs}</td><td>{e(sp)}</td><td>{ats_txt}</td><td>{tot}</td><td>{ou}</td></tr>")
    t_rec = nba.table(["Date", "Game", "Score", "Closing spread", "ATS", "Total", "O/U"], rec)
    leader = A if aa["w"] > aa["l"] else (B if aa["l"] > aa["w"] else None)
    lead = (f"The {A} and {B} have met {aa['n']} times in the regular season since {lab(seasons[-1])}"
            + (f", and the {leader} lead {max(aa['w'], aa['l'])}-{min(aa['w'], aa['l'])} straight up." if leader else f", split {aa['w']}-{aa['l']}.")
            + f" Against the spread the {A} are {nba.ats(aa, ra)}, and the games went {aa['o']}-{aa['u']}-{aa['p']} against the closing total.")
    stats = (f'<div class="tr-stats"><div><b>{aa["w"]}-{aa["l"]}</b><span>{e(A)} vs {e(B)}, {span}</span></div><div><b>{nba.ats(aa, ra)}</b><span>{e(A)} against the spread</span></div>'
             f'<div><b>{nba.ats(bb, rb)}</b><span>{e(B)} against the spread</span></div><div><b>{aa["o"]}-{aa["u"]}-{aa["p"]}</b><span>over, under, push</span></div></div>')
    last = ra[-1]
    faq = [(f"Who leads the {A} vs {B} series since {lab(seasons[-1])}?", (f"The {leader}, {max(aa['w'], aa['l'])}-{min(aa['w'], aa['l'])} in regular season meetings." if leader else f"It is even at {aa['w']}-{aa['l']}.")),
           (f"What is the {A} ATS record against the {B}?", f"{nba.ats(aa, ra)} against the closing spread since {lab(seasons[-1])}; the {B} are {nba.ats(bb, rb)}."),
           (f"How do favorites do in {A} vs {B} games?", f"The spread favorite won {fav_w} of {len(fav)} meetings outright and went {fav_c}-{fav_n} against the spread."),
           (f"Do {A} vs {B} games go over or under?", f"{aa['o']} overs, {aa['u']} unders and {aa['p']} pushes; the average closing total was {aa['avg_total']:.1f} and the games averaged {aa['rpg'] + aa['rapg']:.1f} points."),
           (f"When did the {A} and {B} last play?", f"{fdate(last['date'])}: the {A if last['won'] else B} won {max(last['rf'], last['ra'])}-{min(last['rf'], last['ra'])}.")]
    others = [(f"{nick(x)} vs {nick(y)} betting history", file_for(x, y)) for x, y in pairs() if (x, y) != (a, b) and {x, y} & {a, b}]
    rel = [(f"{a} ATS record", nba.page_file(a)), (f"{b} ATS record", nba.page_file(b))] + others + [
        ("All NBA rivalry betting history", INDEX), ("NBA ATS records", nba.ATS_HUB), ("NBA over/under records", nba.OU_HUB), ("NBA back to back records", nba.B2B_HUB)]
    body = (f"<p class=\"lead\">{e(lead)}</p><p class=\"upd\">Updated {{UPDATED}}. Closing lines, regular season meetings only, {span}.</p>"
            f"<section id=\"summary\"><h2>{e(A)} vs {e(B)} betting summary</h2>{stats}</section>"
            f"<section id=\"seasons\"><h2>{e(A)} vs {e(B)} by season</h2>{t_season}</section>"
            f"<section id=\"venue\"><h2>{e(A)} vs {e(B)} by home court</h2>{t_venue}</section>"
            f"<section id=\"recent\"><h2>Last 15 {e(A)} vs {e(B)} games with closing lines</h2>{t_rec}</section>"
            + nba.method()
            + "<section id=\"related\"><h2>Related</h2><ul class=\"links\">" + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in rel) + "</ul></section>")
    desc = (f"{A} vs {B} betting history since {lab(seasons[-1])}: {aa['w']}-{aa['l']} head to head, {A} {nba.ats(aa, ra)} ATS, over/under {aa['o']}-{aa['u']}-{aa['p']}, "
            f"home court splits and closing spreads for recent meetings.")
    return file_for(a, b), sit.page(file_for(a, b), f"{A} vs {B} Betting History: ATS, Odds and Results", desc, f"{A} vs {B} Betting History", body, faq,
                                    [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", nba.HUB), (f"{A} vs {B}", None)], now_pt), aa["n"]


def index_page(now_pt):
    by_div = {}
    for a, b in pairs():
        by_div.setdefault(f"{nba.TEAMS[a][1]} Conference, {nba.TEAMS[a][2]} Division", []).append((a, b))
    html = "".join(f"<h3>{e(d)}</h3><ul class=\"links\">" + "".join(f'<li><a href="{file_for(a, b)}">{e(nick(a))} vs {e(nick(b))} betting history</a></li>' for a, b in prs) + "</ul>"
                   for d, prs in sorted(by_div.items()))
    faq = [("What do the NBA rivalry pages show?", "Every regular season meeting between two division rivals since 2016-17 at closing lines: straight up and ATS records, moneyline units for both teams, totals, home court splits and the last 15 games.")]
    body = ("<p class=\"lead\">Head to head betting history for all 60 NBA division rivalries since 2016-17, from ESPN verified games and closing lines.</p>"
            "<p class=\"upd\">Updated {UPDATED}.</p><section id=\"rivalries\"><h2>NBA division rivalries</h2>" + html + "</section>" + nba.RELATED)
    return sit.page(INDEX, "NBA Rivalry Betting History: Head to Head ATS for Every Division Rival",
                    "Head to head betting history for all 60 NBA division rivalries since 2016-17: ATS, moneyline, over/under and home court splits at closing lines.",
                    "NBA Rivalry Betting History", body, faq, [("Home", "/"), ("NBA", "nba.html"), ("NBA Team Betting Records", nba.HUB), ("Rivalries", None)], now_pt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--prices", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now_pt = dt.datetime.now(m.PT)
    games, _ = sit.nba_games(a.db, a.prices)
    out, counts = {INDEX: index_page(now_pt)}, []
    for x, y in pairs():
        f, p, n = build(x, y, games, now_pt)
        out[f] = p; counts.append(n)
    if not a.dry_run:
        for f, p in out.items():
            open(os.path.join(m.ROOT, f), "w", encoding="utf-8", newline="\n").write(p)
    print(f"[nba_rivalry_pages] {'would write' if a.dry_run else 'wrote'} {len(out)} pages; meetings per pair {min(counts)} to {max(counts)}")


if __name__ == "__main__":
    main()
