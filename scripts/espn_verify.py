#!/usr/bin/env python3
"""Verify dataset games against ESPN team schedules, season by season (Phase 5 data pages).

Every published figure must come from games that exist exactly as ESPN records
them. A dataset row counts as verified when ESPN has a completed regular season
game with the same home team, away team and final score within one day of it;
each ESPN game can verify only one row. Unverified rows (wrong score, duplicate,
postseason that slipped in) are dropped. ESPN games with no dataset row have no
closing lines and are reported as missing.

Past seasons are cached under CACHE_DIR; the current season is always refetched.
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import datetime as dt
import json
import os
import time
import urllib.request

CACHE_DIR = r"C:\Users\BL\blp_seo_data\espn_schedules"
PATHS = {"mlb": "baseball/mlb", "nhl": "hockey/nhl", "nba": "basketball/nba"}


def _get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception:
            if i == 3:
                raise
            time.sleep(2 * (i + 1))


def team_schedule(sport, abbr, espn_season, refresh):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{sport}_{abbr}_{espn_season}.v2.json")
    if os.path.isfile(path) and not refresh:
        return json.load(open(path))
    d = _get(f"https://site.api.espn.com/apis/site/v2/sports/{PATHS[sport]}/teams/{abbr}/schedule?season={espn_season}&seasontype=2")
    out, remaining = [], 0
    for x in d.get("events", []):
        c = x["competitions"][0]
        st = c.get("status", {}).get("type", {})
        if not st.get("completed"):
            if st.get("state") == "pre":
                remaining += 1
            continue
        t, sc = {}, {}
        for cp in c["competitors"]:
            v = cp.get("score"); v = v.get("value") if isinstance(v, dict) else v
            sc[cp["homeAway"]] = int(float(v)); t[cp["homeAway"]] = cp["team"]["displayName"]
        out.append({"id": x["id"], "date": x["date"][:10], "home": t["home"], "away": t["away"], "hs": sc["home"], "as": sc["away"]})
    res = {"done": out, "remaining": remaining}
    json.dump(res, open(path, "w"))
    return res


def verify(games, sport, abbrs, aliases, espn_season_of, current, team_set):
    """games: dicts with season/date/home/away/hs/as. abbrs: team -> ESPN abbreviation.
    Returns (verified, dropped, report, current_season_problems, current_season_finished);
    report[(team, season)] = (kept, espn_games, dropped_rows, missing_games)."""
    seasons = sorted({g["season"] for g in games})
    jobs = [(t, s) for s in seasons for t in abbrs]

    def fetch(job):
        t, s = job
        try:
            return job, team_schedule(sport, abbrs[t], espn_season_of(s), refresh=(s == current))
        except Exception:
            return job, None
    sched = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for job, evs in ex.map(fetch, jobs):
            sched[job] = evs
    failed = [j for j, v in sched.items() if v is None]
    if failed:
        raise SystemExit(f"ABORT: ESPN schedule fetch failed for {failed[:5]}")
    espn = {}
    remaining = sum(v["remaining"] for (t, s), v in sched.items() if s == current)
    sched = {k: v["done"] for k, v in sched.items()}
    for (t, s), evs in sched.items():
        for ev in evs:
            h = aliases.get(ev["home"], ev["home"]); a = aliases.get(ev["away"], ev["away"])
            espn[ev["id"]] = (s, ev["date"], h, a, ev["hs"], ev["as"])
    pool = collections.defaultdict(list)
    for eid, (s, d, h, a, hs, as_) in espn.items():
        pool[(s, h, a, hs, as_)].append([d, False])
    kept, dropped = [], []
    for g in sorted(games, key=lambda g: g["date"]):
        cands = pool.get((g["season"], g["home"], g["away"], g["hs"], g["as"]), [])
        gd = dt.date.fromisoformat(g["date"])
        hit = next((c for c in cands if not c[1] and abs((dt.date.fromisoformat(c[0]) - gd).days) <= 1), None)
        if hit:
            hit[1] = True; kept.append(g)
        else:
            dropped.append(g)
    # rows dated outside a season's ESPN regular season window are postseason (or preseason), not errors
    window = {}
    for (s, d, *_rest) in espn.values():
        lo, hi = window.get(s, (d, d))
        window[s] = (min(lo, d), max(hi, d))

    def in_window(g):
        lo, hi = window.get(g["season"], ("0", "9"))
        d = dt.date.fromisoformat(g["date"])
        return dt.date.fromisoformat(lo) - dt.timedelta(1) <= d <= dt.date.fromisoformat(hi)  # ESPN dates are UTC, so hi is already a day late for night games
    report = {}
    for (t, s), evs in sched.items():
        if not evs:
            continue
        k = sum(1 for g in kept if g["season"] == s and t in (g["home"], g["away"]))
        dr = sum(1 for g in dropped if g["season"] == s and t in (g["home"], g["away"]) and in_window(g))
        report[(t, s)] = (k, len(evs), dr, len(evs) - k)
    cur_bad = {t: v for (t, s), v in report.items() if s == current and (v[2] or v[3])}
    return kept, dropped, report, cur_bad, remaining == 0


def coverage_note(report, team, seasons_label):
    """One sentence for a team page about games left out, or ''."""
    gaps = [(s, v) for (t, s), v in sorted(report.items(), key=lambda kv: kv[0][1]) if t == team and (v[2] or v[3])]
    if not gaps:
        return ""
    parts = [f"{seasons_label(s)}: {v[0]} of {v[1]} games" for s, v in gaps]
    return ("Some past seasons are missing a game or two that has no closing line on file or did not match ESPN's final score, "
            "so those games are left out: " + "; ".join(parts) + ".")
