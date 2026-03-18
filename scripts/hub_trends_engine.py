#!/usr/bin/env python3
"""
Hub Trends Engine - Generates trend HTML for Handicapping Hub game cards.
Called by handicapping_hub_production.py to add trends under each game.

Uses the BetLegend Trend Scanner v2 combinatorial engine against
the universal_games.pkl historical database.
"""

import pickle
import os
import sys
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Tuple

DATA_FILE = r"C:\Users\Nima\universal_games.pkl"

# Thresholds
MIN_SAMPLE = {1: 15, 2: 12, 3: 8, 4: 6}
MIN_EDGE = {1: 8.0, 2: 10.0, 3: 12.0, 4: 15.0}
MAX_COMBO_DEPTH = 4
MONSTER_PCT = 70.0
HOT_PCT = 62.0
NOTABLE_PCT = 56.0

# Max trends to show per game in the Hub
MAX_TRENDS_DISPLAY = 12

# ESPN abbr -> full name in database
ESPN_TO_FULL = {
    "ANA": "Anaheim Ducks", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres",
    "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes", "CHI": "Chicago Blackhawks",
    "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets", "DAL": "Dallas Stars",
    "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers",
    "LA": "Los Angeles Kings", "LAK": "Los Angeles Kings",
    "MIN": "Minnesota Wild", "MTL": "Montreal Canadiens",
    "NSH": "Nashville Predators", "NJ": "New Jersey Devils", "NJD": "New Jersey Devils",
    "NYI": "New York Islanders", "NYR": "New York Rangers",
    "OTT": "Ottawa Senators", "PHI": "Philadelphia Flyers",
    "PIT": "Pittsburgh Penguins", "SJ": "San Jose Sharks", "SJS": "San Jose Sharks",
    "SEA": "Seattle Kraken", "STL": "St. Louis Blues",
    "TB": "Tampa Bay Lightning", "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs", "UTA": "Utah Mammoth",
    "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights",
    "WSH": "Washington Capitals", "WPG": "Winnipeg Jets",
    # NBA
    "ATL": "Atlanta Hawks", "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets",
    "CLE": "Cleveland Cavaliers", "DEN": "Denver Nuggets",
    "GS": "Golden State Warriors", "GSW": "Golden State Warriors",
    "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies", "MIA": "Miami Heat", "MIL": "Milwaukee Bucks",
    "NO": "New Orleans Pelicans", "NOP": "New Orleans Pelicans",
    "NY": "New York Knicks", "NYK": "New York Knicks",
    "OKC": "OKC Thunder", "ORL": "Orlando Magic",
    "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers",
    "SA": "San Antonio Spurs", "SAS": "San Antonio Spurs",
    "SAC": "Sacramento Kings",
    "UTAH": "Utah Jazz",
    "WAS": "Washington Wizards",
    # NFL
    "ARI": "Arizona Cardinals", "BAL": "Baltimore Ravens",
    "CIN": "Cincinnati Bengals", "GB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars", "KC": "Kansas City Chiefs",
    "LV": "Las Vegas Raiders", "LAR": "Los Angeles Rams",
    "NE": "New England Patriots", "NO": "New Orleans Saints",
    "NYG": "New York Giants", "NYJ": "New York Jets",
    "PIT": "Pittsburgh Steelers", "SF": "San Francisco 49ers",
    "SEA": "Seattle Seahawks", "TB": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders",
}

# Cached data
_cached_games = None
_cached_sport = None


def _load_games(sport: str) -> list:
    """Load and process historical games for a sport"""
    global _cached_games, _cached_sport

    if _cached_sport == sport and _cached_games is not None:
        return _cached_games

    print(f"  [TRENDS] Loading {sport} historical data...")
    if not os.path.exists(DATA_FILE):
        print(f"  [TRENDS] WARNING: {DATA_FILE} not found")
        return []

    with open(DATA_FILE, 'rb') as f:
        data = pickle.load(f)
    all_games = data[0]

    games = [g for g in all_games if g.get('Sport') == sport
             and g.get('HomeTeam') and g.get('AwayTeam')
             and g.get('HomeScore') is not None and g.get('AwayScore') is not None]
    games.sort(key=lambda x: x.get('Date', ''))

    # Build running state
    team_state = {}
    for g in games:
        home = g['HomeTeam']
        away = g['AwayTeam']
        date = g.get('Date', '')
        year = date[:4] if date else '0000'
        hs = g.get('HomeScore', 0) or 0
        as_ = g.get('AwayScore', 0) or 0
        home_won = hs > as_
        spread = g.get('Spread') or 0
        total_line = g.get('Total') or 0
        game_total = hs + as_
        home_margin = hs - as_

        g['_game_total'] = game_total
        g['_home_margin'] = home_margin
        g['_home_won'] = home_won
        try:
            spread = float(spread) if spread else 0
        except (ValueError, TypeError):
            spread = 0
        try:
            total_line = float(total_line) if total_line else 0
        except (ValueError, TypeError):
            total_line = 0
        g['_home_covered'] = (home_margin + spread) > 0 if spread else None
        g['_away_covered'] = (home_margin + spread) < 0 if spread else None
        g['_ats_push'] = (home_margin + spread) == 0 if spread else False
        g['_over'] = game_total > total_line if total_line else None
        g['_under'] = game_total < total_line if total_line else None
        g['_month'] = int(date[5:7]) if date and len(date) >= 7 else 0
        g['_spread_abs'] = abs(spread) if spread else 0
        g['_day_of_week'] = 0
        try:
            g['_day_of_week'] = datetime.strptime(date, '%Y-%m-%d').weekday()
        except:
            pass

        for team, is_home in [(home, True), (away, False)]:
            key = f"{team}_{year}"
            if key not in team_state:
                team_state[key] = {
                    "w": 0, "l": 0, "streak": 0, "ats_streak": 0,
                    "last_date": None, "last_gf": None, "last_ga": None,
                    "last_won": None, "last_home": None,
                    "last_covered": None, "last_over": None,
                    "last_margin": None, "last_was_fav": None,
                }
            st = team_state[key]
            p = '_h_' if is_home else '_a_'

            g[p + 'w'] = st['w']
            g[p + 'l'] = st['l']
            g[p + 'streak'] = st['streak']
            g[p + 'ats_streak'] = st['ats_streak']
            if st['last_date'] and date:
                try:
                    g[p + 'rest'] = (datetime.strptime(date, '%Y-%m-%d') - datetime.strptime(st['last_date'], '%Y-%m-%d')).days
                except:
                    g[p + 'rest'] = 3
            else:
                g[p + 'rest'] = 3
            g[p + 'last_gf'] = st['last_gf']
            g[p + 'last_ga'] = st['last_ga']
            g[p + 'last_won'] = st['last_won']
            g[p + 'last_home'] = st['last_home']
            g[p + 'last_covered'] = st['last_covered']
            g[p + 'last_over'] = st['last_over']
            g[p + 'last_margin'] = st['last_margin']
            g[p + 'last_was_fav'] = st['last_was_fav']
            gp = st['w'] + st['l']
            g[p + 'wpct'] = st['w'] / gp if gp > 0 else 0.5

            team_won = (is_home and home_won) or (not is_home and not home_won)
            gf = hs if is_home else as_
            ga = as_ if is_home else hs
            covered = g['_home_covered'] if is_home else g['_away_covered']
            was_fav = (is_home and spread < 0) or (not is_home and spread > 0) if spread else None

            if team_won:
                st['w'] += 1
                st['streak'] = st['streak'] + 1 if st['streak'] > 0 else 1
            else:
                st['l'] += 1
                st['streak'] = st['streak'] - 1 if st['streak'] < 0 else -1
            if covered is True:
                st['ats_streak'] = st['ats_streak'] + 1 if st['ats_streak'] > 0 else 1
            elif covered is False:
                st['ats_streak'] = st['ats_streak'] - 1 if st['ats_streak'] < 0 else -1

            st['last_date'] = date
            st['last_gf'] = gf
            st['last_ga'] = ga
            st['last_won'] = team_won
            st['last_home'] = is_home
            st['last_covered'] = covered
            st['last_over'] = g['_over']
            st['last_margin'] = gf - ga
            st['last_was_fav'] = was_fav

    _cached_games = games
    _cached_sport = sport
    print(f"  [TRENDS] {len(games):,} {sport} games loaded")
    return games


def _build_filters(side, rest_days, streak, last_won, last_gf, last_ga, home_spread, total, wpct, month,
                    opp_wpct=0.5, opp_rest=3, ats_streak=0):
    """Build situational filters for one side - comprehensive set"""
    p = '_h_' if side == "home" else '_a_'
    opp_p = '_a_' if side == "home" else '_h_'
    is_fav = (side == "home" and home_spread < 0) or (side == "away" and home_spread > 0)
    last_margin = (last_gf or 0) - (last_ga or 0)
    dow = datetime.now().weekday()
    spread_abs = abs(home_spread) if home_spread else 0
    filters = []

    # ---- ROLE: Favorite / Underdog ----
    if is_fav:
        filters.append(("as FAV", lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) < 0) or (p == '_a_' and float(g['Spread'] or 0) > 0)), "ROLE", ["as DOG"]))
    else:
        filters.append(("as DOG", lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) > 0) or (p == '_a_' and float(g['Spread'] or 0) < 0)), "ROLE", ["as FAV"]))

    # ---- SPREAD SIZE ----
    if spread_abs >= 5:
        filters.append(("big spread 5+", lambda g: g.get('_spread_abs', 0) >= 5, "SPREAD_SIZE", ["small spread 1-3"]))
    elif spread_abs <= 3 and spread_abs > 0:
        filters.append(("small spread 1-3", lambda g: 0 < g.get('_spread_abs', 0) <= 3, "SPREAD_SIZE", ["big spread 5+"]))

    # ---- REST ----
    if rest_days == 1:
        filters.append(("on B2B", lambda g, p=p: g.get(p + 'rest', 3) <= 1, "REST", ["on 2 days rest", "on 3+ rest"]))
    elif rest_days == 2:
        filters.append(("on 2 days rest", lambda g, p=p: g.get(p + 'rest', 3) == 2, "REST", ["on B2B", "on 3+ rest"]))
    elif rest_days >= 3:
        filters.append(("on 3+ rest", lambda g, p=p: g.get(p + 'rest', 3) >= 3, "REST", ["on B2B", "on 2 days rest"]))

    # ---- OPPONENT REST (rest advantage/disadvantage) ----
    if rest_days > opp_rest:
        filters.append(("with rest advantage", lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) > g.get(opp_p + 'rest', 3), "OPP_REST", ["with rest disadvantage"]))
    elif rest_days < opp_rest:
        filters.append(("with rest disadvantage", lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) < g.get(opp_p + 'rest', 3), "OPP_REST", ["with rest advantage"]))

    # ---- LAST GAME RESULT ----
    if last_won is True:
        filters.append(("after W", lambda g, p=p: g.get(p + 'last_won') is True, "LAST", ["after L"]))
    elif last_won is False:
        filters.append(("after L", lambda g, p=p: g.get(p + 'last_won') is False, "LAST", ["after W"]))

    # ---- SCORING THRESHOLDS ----
    if last_gf is not None:
        if last_gf >= 4:
            filters.append(("after scoring 4+", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] >= 4, "GF", ["after scoring 0-1", "after scoring 2-3"]))
        elif last_gf <= 1:
            filters.append(("after scoring 0-1", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] <= 1, "GF", ["after scoring 4+", "after scoring 2-3"]))
        else:
            filters.append(("after scoring 2-3", lambda g, p=p: g.get(p + 'last_gf') is not None and 2 <= g[p + 'last_gf'] <= 3, "GF", ["after scoring 4+", "after scoring 0-1"]))

    # ---- GOALS ALLOWED ----
    if last_ga is not None:
        if last_ga >= 4:
            filters.append(("after allowing 4+", lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] >= 4, "GA", ["after allowing 0-1"]))
        elif last_ga <= 1:
            filters.append(("after allowing 0-1", lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] <= 1, "GA", ["after allowing 4+"]))

    # ---- GAME TYPE ----
    if last_margin >= 3:
        filters.append(("after blowout W", lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] >= 3, "TYPE", ["after blowout L", "after shutout", "after 1-goal game"]))
    elif last_margin <= -3:
        filters.append(("after blowout L", lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] <= -3, "TYPE", ["after blowout W", "after shutout", "after 1-goal game"]))
    elif abs(last_margin) <= 1 and (last_gf or 0) > 0:
        filters.append(("after 1-goal game", lambda g, p=p: g.get(p + 'last_margin') is not None and abs(g[p + 'last_margin']) <= 1, "TYPE", ["after blowout W", "after blowout L", "after shutout"]))
    if (last_gf or 0) == 0 and last_gf is not None:
        filters.append(("after shutout", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] == 0, "TYPE", []))

    # ---- SU STREAKS ----
    if streak >= 3:
        filters.append(("on 3+ W streak", lambda g, p=p: g.get(p + 'streak', 0) >= 3, "STREAK", ["on 2+ L streak", "on 3+ L streak"]))
    elif streak == 2:
        filters.append(("on 2 W streak", lambda g, p=p: g.get(p + 'streak', 0) == 2, "STREAK", ["on 2+ L streak", "on 3+ L streak"]))
    elif streak <= -3:
        filters.append(("on 3+ L streak", lambda g, p=p: g.get(p + 'streak', 0) <= -3, "STREAK", ["on 3+ W streak", "on 2 W streak"]))
    elif streak <= -2:
        filters.append(("on 2+ L streak", lambda g, p=p: g.get(p + 'streak', 0) <= -2, "STREAK", ["on 3+ W streak", "on 2 W streak"]))

    # ---- ATS STREAKS ----
    if ats_streak >= 2:
        filters.append(("on 2+ ATS cover streak", lambda g, p=p: g.get(p + 'ats_streak', 0) >= 2, "ATS_STREAK", ["on 2+ ATS fade streak"]))
    elif ats_streak <= -2:
        filters.append(("on 2+ ATS fade streak", lambda g, p=p: g.get(p + 'ats_streak', 0) <= -2, "ATS_STREAK", ["on 2+ ATS cover streak"]))

    # ---- LAST GAME ATS ----
    filters.append(("after covering", lambda g, p=p: g.get(p + 'last_covered') is True, "ATS", ["after not covering"]))
    filters.append(("after not covering", lambda g, p=p: g.get(p + 'last_covered') is False, "ATS", ["after covering"]))

    # ---- LAST GAME O/U ----
    filters.append(("after OVER", lambda g, p=p: g.get(p + 'last_over') is True, "OU", ["after UNDER"]))
    filters.append(("after UNDER", lambda g, p=p: g.get(p + 'last_over') is False, "OU", ["after OVER"]))

    # ---- TEAM RECORD ----
    if wpct > 0.55:
        filters.append(("winning record", lambda g, p=p: g.get(p + 'wpct', 0.5) > 0.55, "REC", ["losing record", "near .500"]))
    elif wpct < 0.45:
        filters.append(("losing record", lambda g, p=p: g.get(p + 'wpct', 0.5) < 0.45, "REC", ["winning record", "near .500"]))
    else:
        filters.append(("near .500", lambda g, p=p: 0.45 <= g.get(p + 'wpct', 0.5) <= 0.55, "REC", ["winning record", "losing record"]))

    # ---- OPPONENT RECORD QUALITY ----
    if opp_wpct > 0.55:
        filters.append(("vs winning team", lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) > 0.55, "OPP_REC", ["vs losing team"]))
    elif opp_wpct < 0.45:
        filters.append(("vs losing team", lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) < 0.45, "OPP_REC", ["vs winning team"]))

    # ---- LAST GAME VENUE ----
    if last_won is True:
        filters.append(("after road W", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is False, "LAST_VENUE", ["after home L", "after home W", "after road L"]))
        filters.append(("after home W", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is True, "LAST_VENUE", ["after road W", "after home L", "after road L"]))
    elif last_won is False:
        filters.append(("after home L", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is True, "LAST_VENUE", ["after road W", "after home W", "after road L"]))
        filters.append(("after road L", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is False, "LAST_VENUE", ["after road W", "after home W", "after home L"]))

    # ---- MONTH ----
    month_name = datetime(2000, month, 1).strftime("%b")
    filters.append((f"in {month_name}", lambda g, m=month: g.get('_month') == m, "MONTH", []))

    # ---- DAY OF WEEK ----
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if dow < 7:
        filters.append((f"on {day_names[dow]}", lambda g, d=dow: g.get('_day_of_week') == d, "DOW", []))

    # ---- WEEKEND vs WEEKDAY ----
    if dow >= 4:  # Fri-Sun
        filters.append(("on weekend", lambda g: g.get('_day_of_week', 0) >= 4, "WEEKEND", ["on weekday"]))
    else:
        filters.append(("on weekday", lambda g: g.get('_day_of_week', 0) < 4, "WEEKEND", ["on weekend"]))

    # ---- TOTAL RANGE ----
    if total >= 6.0:
        filters.append(("total 6.0+", lambda g: g.get('Total') and float(g['Total'] or 0) >= 6.0, "TRANGE", ["total 5.5-"]))
    elif total and total <= 5.5:
        filters.append(("total 5.5-", lambda g: g.get('Total') and float(g['Total'] or 0) <= 5.5, "TRANGE", ["total 6.0+"]))

    # ---- ROLE + RESULT COMBOS ----
    filters.append(("after W as dog", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_was_fav') is False, "ROLE_RES", ["after L as fav"]))
    filters.append(("after L as fav", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_was_fav') is True, "ROLE_RES", ["after W as dog"]))

    # ---- SECOND HALF OF SEASON (games played > 40) ----
    if wpct is not None:
        filters.append(("in 2nd half of season", lambda g, p=p: (g.get(p + 'w', 0) + g.get(p + 'l', 0)) > 40, "SEASON_HALF", []))

    return filters


def _calc_record(games, side):
    """Calculate ATS/OU record"""
    if not games:
        return None
    if side == "home":
        w = sum(1 for g in games if g.get('_home_covered'))
        l = sum(1 for g in games if g.get('_away_covered'))
    else:
        w = sum(1 for g in games if g.get('_away_covered'))
        l = sum(1 for g in games if g.get('_home_covered'))
    p = sum(1 for g in games if g.get('_ats_push'))
    td = w + l
    if td == 0:
        return None
    pct = w / td * 100
    ov = sum(1 for g in games if g.get('_over'))
    un = sum(1 for g in games if g.get('_under'))
    ou_pct = ov / (ov + un) * 100 if (ov + un) > 0 else 50
    return {"games": len(games), "w": w, "l": l, "p": p, "pct": round(pct, 1),
            "over": ov, "under": un, "ou_pct": round(ou_pct, 1)}


def _run_combos(base_games, side, filters):
    """Run combinatorial filter engine"""
    results = []
    n_filters = len(filters)

    for depth in range(1, min(MAX_COMBO_DEPTH + 1, n_filters + 1)):
        min_n = MIN_SAMPLE.get(depth, 6)
        min_edge = MIN_EDGE.get(depth, 10)

        for combo in combinations(range(n_filters), depth):
            categories = [filters[i][2] for i in combo]
            conflicts = []
            for i in combo:
                conflicts.extend(filters[i][3])

            has_conflict = False
            for i in combo:
                if filters[i][0] in conflicts:
                    has_conflict = True
                    break
                cat = filters[i][2]
                if cat and categories.count(cat) > 1:
                    has_conflict = True
                    break
            if has_conflict:
                continue

            filtered = base_games
            for i in combo:
                filtered = [g for g in filtered if filters[i][1](g)]

            if len(filtered) < min_n:
                continue

            rec = _calc_record(filtered, side)
            if rec is None:
                continue

            edge = abs(rec["pct"] - 50)
            ou_edge = abs(rec["ou_pct"] - 50)

            if edge >= min_edge or ou_edge >= min_edge + 5:
                labels = [filters[i][0] for i in combo]
                results.append({
                    "labels": labels,
                    "depth": depth,
                    "rec": rec,
                    "side": side,
                    "edge": edge,
                    "ou_edge": ou_edge,
                })

    return results


def _format_trend_description(team_name: str, venue: str, labels: list) -> str:
    """Convert shorthand filter labels into clear, readable English."""
    # Map shorthand labels to readable phrases
    LABEL_MAP = {
        "as FAV": "as the favorite",
        "as DOG": "as the underdog",
        "on B2B": "on a back-to-back",
        "on 2 days rest": "with 2 days rest",
        "on 3+ rest": "with 3+ days rest",
        "after W": "coming off a win",
        "after L": "coming off a loss",
        "after scoring 4+": "after scoring 4+ goals last game",
        "after scoring 0-1": "after scoring 0-1 goals last game",
        "after scoring 2-3": "after scoring 2-3 goals last game",
        "after allowing 4+": "after allowing 4+ goals last game",
        "after allowing 0-1": "after allowing 0-1 goals last game",
        "after blowout W": "after a blowout win (3+ goals)",
        "after blowout L": "after a blowout loss (3+ goals)",
        "after 1-goal game": "after a one-goal game",
        "after shutout": "after being shut out",
        "on 3+ W streak": "on a 3+ game win streak",
        "on 2+ W streak": "on a 2+ game win streak",
        "on 3+ L streak": "on a 3+ game losing streak",
        "on 2+ L streak": "on a 2+ game losing streak",
        "after covering": "after covering the spread",
        "after not covering": "after failing to cover",
        "after OVER": "after their last game went over",
        "after UNDER": "after their last game went under",
        "winning record": "with a winning record",
        "losing record": "with a losing record",
        "after road WIN": "coming off a road win",
        "after home LOSS": "coming off a home loss",
        "after road LOSS": "coming off a road loss",
        "after home WIN": "coming off a home win",
        "total 6.0+": "when the total is set at 6.0+",
        "total 5.5-": "when the total is set at 5.5 or lower",
        "after W as dog": "after winning as an underdog",
        "after L as fav": "after losing as the favorite",
    }

    # New filters
    LABEL_MAP.update({
        "big spread 5+": "with a spread of 5+",
        "small spread 1-3": "with a spread of 1-3",
        "on 2 days rest": "with 2 days rest",
        "with rest advantage": "with a rest advantage over the opponent",
        "with rest disadvantage": "with a rest disadvantage vs the opponent",
        "on 2 W streak": "on a 2-game win streak",
        "on 2+ ATS cover streak": "on a 2+ game ATS cover streak",
        "on 2+ ATS fade streak": "on a 2+ game ATS non-cover streak",
        "near .500": "with a near-.500 record",
        "vs winning team": "against a team with a winning record",
        "vs losing team": "against a team with a losing record",
        "after road W": "coming off a road win",
        "after home W": "coming off a home win",
        "after road L": "coming off a road loss",
        "after home L": "coming off a home loss",
        "on weekend": "playing on a weekend",
        "on weekday": "playing on a weekday",
        "in 2nd half of season": "in the second half of the season",
    })

    # Month and day labels
    for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
        LABEL_MAP[f"in {m}"] = f"in {m}"
    for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        LABEL_MAP[f"on {d}"] = f"on a {d}"

    venue_text = "at home" if venue == "home" else "on the road"
    parts = [LABEL_MAP.get(label, label) for label in labels]

    return f"{team_name} {venue_text}, {', '.join(parts)}"


_team_name_cache = {}

def _resolve_team_name(abbr: str, sport: str, games: list) -> str:
    """Resolve ESPN abbreviation to full team name using the actual database.
    Handles cross-sport collisions (DET = Red Wings in NHL, Pistons in NBA)."""
    cache_key = f"{sport}_{abbr}"
    if cache_key in _team_name_cache:
        return _team_name_cache[cache_key]

    # Hard overrides for tricky abbreviations that collide across sports
    SPORT_OVERRIDES = {
        "NBA": {"OKC": "Oklahoma City Thunder", "WSH": "Washington Wizards", "DET": "Detroit Pistons",
                "CHI": "Chicago Bulls", "MIN": "Minnesota Timberwolves", "PHI": "Philadelphia 76ers",
                "IND": "Indiana Pacers", "MIA": "Miami Heat", "BOS": "Boston Celtics",
                "TB": "Toronto Raptors", "SEA": "Seattle SuperSonics",
                "SA": "San Antonio Spurs", "GS": "Golden State Warriors",
                "NO": "New Orleans Pelicans", "NY": "New York Knicks",
                "PIT": "Pittsburgh", "CAR": "Charlotte Hornets",
                },
        "NFL": {"DET": "Detroit Lions", "CHI": "Chicago Bears", "MIN": "Minnesota Vikings",
                "PHI": "Philadelphia Eagles", "IND": "Indianapolis Colts",
                "MIA": "Miami Dolphins", "BOS": "New England Patriots",
                "CAR": "Carolina Panthers", "WSH": "Washington Commanders",
                "TB": "Tampa Bay Buccaneers", "SEA": "Seattle Seahawks",
                "BUF": "Buffalo Bills", "PIT": "Pittsburgh Steelers",
                "NYI": "New York Giants", "NYR": "New York Jets",
                "DAL": "Dallas Cowboys",
                },
        "MLB": {"DET": "Detroit Tigers", "CHI": "Chicago Cubs", "MIN": "Minnesota Twins",
                "PHI": "Philadelphia Phillies", "MIA": "Miami Marlins",
                "BOS": "Boston Red Sox", "TB": "Tampa Bay Rays",
                "SEA": "Seattle Mariners", "PIT": "Pittsburgh Pirates",
                "WSH": "Washington Nationals", "STL": "St. Louis Cardinals",
                },
    }

    sport_override = SPORT_OVERRIDES.get(sport, {})
    if abbr in sport_override:
        override = sport_override[abbr]
        _team_name_cache[cache_key] = override
        return override

    # Build set of all team names in this sport's data (from recent games)
    sport_teams = set()
    for g in games[-500:]:
        for key in ['HomeTeam', 'AwayTeam']:
            t = g.get(key, '')
            if t:
                sport_teams.add(t)

    # First try the static mapping - but verify it exists in THIS sport
    full = ESPN_TO_FULL.get(abbr)
    if full and full in sport_teams:
        _team_name_cache[cache_key] = full
        return full

    # Static mapping didn't match this sport - search by abbreviation
    abbr_lower = abbr.lower()
    abbr_upper = abbr.upper()

    # Common abbreviation patterns to try
    for team in sport_teams:
        team_lower = team.lower()
        words = team.split()

        # Direct word match: "OKC" in "OKC Thunder" or "Oklahoma City Thunder"
        if abbr_upper in [w.upper() for w in words]:
            _team_name_cache[cache_key] = team
            return team

        # First-letter abbreviation: "OKC" = Oklahoma City (Thunder isn't counted)
        # "WSH" = Washington (remove common suffixes)
        city_words = [w for w in words if w.lower() not in ('thunder', 'heat', 'magic', 'jazz', 'suns',
            'kings', 'nets', 'hawks', 'bulls', 'cavaliers', 'mavericks', 'nuggets', 'pistons',
            'warriors', 'rockets', 'pacers', 'clippers', 'lakers', 'grizzlies', 'bucks',
            'timberwolves', 'pelicans', 'knicks', 'hornets', 'celtics', '76ers',
            'blazers', 'spurs', 'raptors', 'wizards', 'trail',
            'bruins', 'sabres', 'flames', 'hurricanes', 'blackhawks', 'avalanche',
            'blue', 'jackets', 'stars', 'red', 'wings', 'oilers', 'panthers',
            'wild', 'canadiens', 'predators', 'devils', 'islanders', 'rangers',
            'senators', 'flyers', 'penguins', 'sharks', 'kraken', 'blues',
            'lightning', 'maple', 'leafs', 'mammoth', 'canucks', 'golden', 'knights',
            'capitals', 'jets')]
        if city_words:
            city_abbr = ''.join(w[0].upper() for w in city_words)
            if city_abbr == abbr_upper:
                _team_name_cache[cache_key] = team
                return team

        # Partial match in team name
        if abbr_lower in team_lower.replace(' ', '').replace('.', ''):
            _team_name_cache[cache_key] = team
            return team

    _team_name_cache[cache_key] = None
    return None


def get_trends_for_game(sport: str, home_abbr: str, away_abbr: str,
                        home_spread: float, total: float,
                        home_rest: int = 3, away_rest: int = 3,
                        home_streak: int = 0, away_streak: int = 0,
                        home_last_won: bool = None, away_last_won: bool = None,
                        home_last_gf: int = None, home_last_ga: int = None,
                        away_last_gf: int = None, away_last_ga: int = None,
                        home_wpct: float = 0.5, away_wpct: float = 0.5) -> List[Dict]:
    """
    Main entry point: get trend results for a single game.
    Returns a list of trend dicts sorted by strength.
    """
    games = _load_games(sport)
    if not games:
        return []

    home_full = _resolve_team_name(home_abbr, sport, games)
    away_full = _resolve_team_name(away_abbr, sport, games)

    if not home_full or not away_full:
        return []

    home_games = [g for g in games if g.get('HomeTeam') == home_full]
    away_games = [g for g in games if g.get('AwayTeam') == away_full]

    month = datetime.now().month

    home_filters = _build_filters("home", home_rest, home_streak, home_last_won,
                                   home_last_gf, home_last_ga, home_spread, total, home_wpct, month,
                                   opp_wpct=away_wpct, opp_rest=away_rest)
    away_filters = _build_filters("away", away_rest, away_streak, away_last_won,
                                   away_last_gf, away_last_ga, home_spread, total, away_wpct, month,
                                   opp_wpct=home_wpct, opp_rest=home_rest)

    home_results = _run_combos(home_games, "home", home_filters)
    away_results = _run_combos(away_games, "away", away_filters)

    all_results = home_results + away_results
    all_results.sort(key=lambda x: x["edge"] * min(x["rec"]["games"], 50), reverse=True)

    # Tag each with team info - build clear English descriptions
    for r in all_results:
        if r["side"] == "home":
            r["team"] = home_abbr
            r["desc"] = _format_trend_description(home_full, "home", r["labels"])
        else:
            r["team"] = away_abbr
            r["desc"] = _format_trend_description(away_full, "away", r["labels"])

    return all_results


def generate_trends_html(sport: str, home_abbr: str, away_abbr: str,
                         home_spread: float, total: float,
                         home_rest: int = 3, away_rest: int = 3,
                         home_streak: int = 0, away_streak: int = 0,
                         home_last_won: bool = None, away_last_won: bool = None,
                         home_last_gf: int = None, home_last_ga: int = None,
                         away_last_gf: int = None, away_last_ga: int = None,
                         home_wpct: float = 0.5, away_wpct: float = 0.5) -> str:
    """
    Generate HTML for the trends section of a Handicapping Hub game card.
    Returns HTML string to inject into the game card.
    """
    results = get_trends_for_game(
        sport, home_abbr, away_abbr, home_spread, total,
        home_rest, away_rest, home_streak, away_streak,
        home_last_won, away_last_won,
        home_last_gf, home_last_ga, away_last_gf, away_last_ga,
        home_wpct, away_wpct
    )

    if not results:
        return ''

    # Separate into categories
    monsters = [r for r in results if r["rec"]["pct"] >= MONSTER_PCT and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    hot = [r for r in results if HOT_PCT <= r["rec"]["pct"] < MONSTER_PCT and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    fades = [r for r in results if r["rec"]["pct"] <= (100 - HOT_PCT) and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]

    # O/U extremes
    ou_extremes = [r for r in results if r["ou_edge"] >= 15 and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    ou_extremes.sort(key=lambda x: x["ou_edge"], reverse=True)

    # Build HTML rows
    rows = []
    count = 0

    def add_row(r, tier_class, tier_label):
        nonlocal count
        if count >= MAX_TRENDS_DISPLAY:
            return
        rec = r["rec"]
        pct = rec["pct"]
        is_cover = pct >= 55
        pct_class = "trend-cover" if is_cover else "trend-fade"
        display_pct = pct if is_cover else round(100 - pct, 1)
        side_label = "COVER" if is_cover else "FADE"

        rows.append(f'''<tr class="{tier_class}">
            <td class="trend-tier">{tier_label}</td>
            <td class="trend-desc">{r["desc"]}</td>
            <td class="trend-record">{rec["w"]}-{rec["l"]}</td>
            <td class="{pct_class}">{display_pct:.1f}%</td>
            <td class="trend-games">{rec["games"]}</td>
        </tr>''')
        count += 1

    for r in monsters[:5]:
        add_row(r, "tier-monster", "MONSTER")
    for r in hot[:5]:
        add_row(r, "tier-hot", "HOT")
    for r in fades[:4]:
        add_row(r, "tier-fade", "FADE")

    if not rows:
        return ''

    # O/U section
    ou_rows = []
    for r in ou_extremes[:3]:
        rec = r["rec"]
        lean = "OVER" if rec["ou_pct"] > 55 else "UNDER"
        ou_class = "ou-over" if lean == "OVER" else "ou-under"
        ou_rows.append(f'''<tr>
            <td class="trend-desc">{r["desc"]}</td>
            <td class="{ou_class}">{rec["over"]}O-{rec["under"]}U ({rec["ou_pct"]:.1f}%)</td>
            <td class="trend-games">{rec["games"]}</td>
            <td class="{ou_class}"><strong>{lean}</strong></td>
        </tr>''')

    ou_html = ''
    if ou_rows:
        ou_html = f'''
        <div class="trends-ou">
            <div class="trends-subtitle">O/U TRENDS</div>
            <table class="trends-table trends-ou-table">
                <thead><tr><th>SITUATION</th><th>RECORD</th><th>GAMES</th><th>LEAN</th></tr></thead>
                <tbody>{"".join(ou_rows)}</tbody>
            </table>
        </div>'''

    # Verdict
    home_covers = len([r for r in results if r["side"] == "home" and r["rec"]["pct"] >= NOTABLE_PCT])
    home_fades_count = len([r for r in results if r["side"] == "home" and r["rec"]["pct"] <= 100 - NOTABLE_PCT])
    away_covers = len([r for r in results if r["side"] == "away" and r["rec"]["pct"] >= NOTABLE_PCT])
    away_fades_count = len([r for r in results if r["side"] == "away" and r["rec"]["pct"] <= 100 - NOTABLE_PCT])

    home_score = home_covers + away_fades_count
    away_score = away_covers + home_fades_count

    if home_score > away_score + 3:
        verdict = f"<strong>STRONG LEAN: {home_abbr}</strong>"
        verdict_class = "verdict-strong"
    elif away_score > home_score + 3:
        verdict = f"<strong>STRONG LEAN: {away_abbr}</strong>"
        verdict_class = "verdict-strong"
    elif home_score > away_score:
        verdict = f"LEAN: {home_abbr} ({home_score} vs {away_score})"
        verdict_class = "verdict-lean"
    elif away_score > home_score:
        verdict = f"LEAN: {away_abbr} ({away_score} vs {home_score})"
        verdict_class = "verdict-lean"
    else:
        verdict = "NO CLEAR EDGE"
        verdict_class = "verdict-neutral"

    return f'''
    <div class="section trends-section">
        <div class="section-title">HISTORICAL TRENDS <span class="trends-badge">{len(results)} found</span></div>
        <table class="trends-table">
            <thead><tr><th>TIER</th><th>SITUATION</th><th>ATS</th><th>HIT%</th><th>GAMES</th></tr></thead>
            <tbody>{"".join(rows)}</tbody>
        </table>
        {ou_html}
        <div class="trends-verdict {verdict_class}">{verdict}</div>
    </div>'''


def get_trends_css() -> str:
    """Return CSS for the trends section"""
    return '''
    /* TRENDS SECTION - LARGE & CLEAR */
    .trends-section {
        margin-top: 16px;
        border-top: 3px solid rgba(0, 245, 255, 0.3);
        padding: 20px 24px;
        background: rgba(0, 20, 40, 0.4);
    }
    .trends-section .section-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        color: #00f5ff;
        letter-spacing: 2px;
        margin-bottom: 16px;
        text-shadow: 0 0 15px rgba(0, 245, 255, 0.4);
    }
    .trends-badge {
        font-size: 0.85rem;
        background: rgba(0, 245, 255, 0.2);
        color: #00f5ff;
        padding: 4px 12px;
        border-radius: 12px;
        margin-left: 12px;
        font-weight: 500;
    }
    .trends-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 1.05rem;
        margin-top: 10px;
    }
    .trends-table thead th {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #aaa;
        padding: 10px 12px;
        text-align: left;
        border-bottom: 2px solid rgba(255,255,255,0.12);
    }
    .trends-table tbody tr {
        border-bottom: 1px solid rgba(255,255,255,0.06);
        transition: background 0.2s;
    }
    .trends-table tbody tr:hover {
        background: rgba(0, 245, 255, 0.05);
    }
    .trends-table td {
        padding: 12px;
        vertical-align: middle;
    }
    .trend-tier {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        width: 100px;
    }
    .tier-monster .trend-tier {
        color: #ff3333;
        text-shadow: 0 0 12px rgba(255,50,50,0.6);
        font-size: 0.85rem;
    }
    .tier-hot .trend-tier {
        color: #ffa500;
        text-shadow: 0 0 10px rgba(255,165,0,0.5);
    }
    .tier-fade .trend-tier {
        color: #ff69b4;
        text-shadow: 0 0 8px rgba(255,105,180,0.4);
    }
    .trend-desc {
        color: #e0e0e0;
        font-size: 1.0rem;
        font-weight: 500;
        line-height: 1.4;
    }
    .tier-monster .trend-desc {
        color: #fff;
        font-weight: 600;
    }
    .trend-record {
        font-weight: 700;
        color: #fff;
        text-align: center;
        font-size: 1.1rem;
        font-family: 'Rajdhani', sans-serif;
    }
    .trend-cover {
        color: #00ff88;
        font-weight: 800;
        text-align: center;
        font-size: 1.15rem;
        text-shadow: 0 0 8px rgba(0,255,136,0.3);
    }
    .trend-fade {
        color: #ff6b6b;
        font-weight: 800;
        text-align: center;
        font-size: 1.15rem;
        text-shadow: 0 0 8px rgba(255,107,107,0.3);
    }
    .trend-games {
        color: #999;
        font-size: 0.95rem;
        text-align: center;
        font-weight: 500;
    }
    .trends-ou {
        margin-top: 16px;
        padding-top: 12px;
        border-top: 1px solid rgba(0, 245, 255, 0.1);
    }
    .trends-subtitle {
        font-family: 'Orbitron', sans-serif;
        font-size: 0.9rem;
        color: #00f5ff;
        letter-spacing: 2px;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .trends-ou-table {
        font-size: 1.0rem;
    }
    .trends-ou-table thead th {
        font-size: 0.75rem;
    }
    .ou-over {
        color: #00ff88;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .ou-under {
        color: #ff6b6b;
        font-weight: 700;
        font-size: 1.05rem;
    }
    .trends-verdict {
        margin-top: 16px;
        padding: 14px 20px;
        border-radius: 10px;
        font-family: 'Orbitron', sans-serif;
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-align: center;
    }
    .verdict-strong {
        background: rgba(255, 50, 50, 0.15);
        border: 2px solid rgba(255, 50, 50, 0.4);
        color: #ff5555;
        text-shadow: 0 0 15px rgba(255,50,50,0.4);
    }
    .verdict-lean {
        background: rgba(0, 245, 255, 0.1);
        border: 2px solid rgba(0, 245, 255, 0.3);
        color: #00f5ff;
        text-shadow: 0 0 12px rgba(0,245,255,0.3);
    }
    .verdict-neutral {
        background: rgba(255, 255, 255, 0.05);
        border: 2px solid rgba(255, 255, 255, 0.15);
        color: #999;
    }
    '''
