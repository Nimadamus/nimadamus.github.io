#!/usr/bin/env python3
"""Closing spread (run line, puck line) and over/under PRICES from ESPN's published closes (MLB, NHL, NBA).

The Bet Legend dataset stores the closing run line and total but not their prices,
so run line units and over/under units cannot be computed from it. ESPN's core
odds resource publishes each book's close, including the run line price and the
over and under prices. This caches them per game so the data pages can show units
for the seasons where ESPN has them. Prices are matched to a dataset game by date,
teams and final score; the page builder only uses a price when ESPN's line equals
the dataset's line.

    python scripts/mlb_close_prices.py --season 2026 --out PATH/close_prices_2026.json
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import sys
import time
import urllib.request

PATHS = {"mlb": "baseball/mlb", "nhl": "hockey/nhl", "nba": "basketball/nba"}
SPORT = "mlb"


def sb_url(day):
    return f"https://site.api.espn.com/apis/site/v2/sports/{PATHS[SPORT]}/scoreboard?dates={day}&limit=100"


def core_url(eid):
    lg = PATHS[SPORT].split("/")
    return f"https://sports.core.api.espn.com/v2/sports/{lg[0]}/leagues/{lg[1]}/events/{eid}/competitions/{eid}/odds"


def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=25) as r:
                return json.load(r)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


def am(node):
    if not isinstance(node, dict):
        return None
    v = node.get("american") or node.get("alternateDisplayValue")
    if v in (None, ""):
        return None
    v = str(v).strip().upper()
    if v == "EVEN":
        return 100.0
    try:
        return float(v)
    except ValueError:
        return None


def events_on(day):
    d = get(sb_url(day.strftime("%Y%m%d")))
    out = []
    for ev in d.get("events", []):
        c = ev["competitions"][0]
        if not c.get("status", {}).get("type", {}).get("completed"):
            continue
        t = {cp["homeAway"]: cp for cp in c["competitors"]}
        out.append({"id": ev["id"], "date": day.isoformat(), "season_type": (ev.get("season") or {}).get("type"),
                    "home": t["home"]["team"]["displayName"], "away": t["away"]["team"]["displayName"],
                    "hs": int(float(t["home"]["score"])), "as": int(float(t["away"]["score"]))})
    return out


def close_for(eid):
    items = sorted(get(core_url(eid)).get("items") or [], key=lambda it: (it.get("provider") or {}).get("priority", 99))
    for it in items:
        h = (it.get("homeTeamOdds") or {}).get("close") or {}
        a = (it.get("awayTeamOdds") or {}).get("close") or {}
        c = it.get("close") or {}
        rec = {"provider": (it.get("provider") or {}).get("name"), "home_line": am(h.get("pointSpread")),
               "home_rl_price": am(h.get("spread")), "away_rl_price": am(a.get("spread")),
               "total": am(c.get("total")), "over_price": am(c.get("over")), "under_price": am(c.get("under")),
               "home_ml": am(h.get("moneyLine")), "away_ml": am(a.get("moneyLine"))}
        if rec["home_line"] is not None or rec["total"] is not None:
            return rec
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--sport", default="mlb", choices=sorted(PATHS))
    ap.add_argument("--out", required=True)
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    global SPORT
    SPORT = a.sport
    start = dt.date.fromisoformat(a.start or f"{a.season}-03-15")
    end = dt.date.fromisoformat(a.end or min(dt.date.today().isoformat(), f"{a.season}-10-05"))
    cache = json.load(open(a.out)) if os.path.isfile(a.out) else {}
    days = [start + dt.timedelta(n) for n in range((end - start).days + 1)]
    evs = []
    with cf.ThreadPoolExecutor(6) as ex:
        for lst in ex.map(events_on, days):
            evs += lst
    evs = [e for e in evs if e["season_type"] in (2, None)]
    todo = [e for e in evs if e["id"] not in cache]
    print(f"{len(evs)} completed regular season events, {len(todo)} to fetch")
    with cf.ThreadPoolExecutor(8) as ex:
        for e, c in zip(todo, ex.map(lambda e: close_for(e["id"]), todo)):
            cache[e["id"]] = dict(e, close=c)
    json.dump(cache, open(a.out, "w"))
    have = sum(1 for v in cache.values() if v.get("close") and v["close"].get("home_rl_price") is not None)
    print(f"cached {len(cache)} games, {have} with a run line price")


if __name__ == "__main__":
    sys.exit(main())
