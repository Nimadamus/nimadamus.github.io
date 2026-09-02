#!/usr/bin/env python3
"""
Hub Trends Engine - Generates trend HTML for Handicapping Hub game cards.
Called by handicapping_hub_production.py to add trends under each game.

Uses the BetLegend Trend Scanner v2 combinatorial engine, adjusted for
baseline team strength to surface only "extreme" situational records.
"""

import sys
import os
import json
import pickle
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
from itertools import combinations
from typing import Dict, List, Optional, Tuple

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from sellable_market_eligibility import public_trend_exclusion_reason
except ImportError:
    public_trend_exclusion_reason = None

DATA_FILE = r"C:\Users\Nima\universal_games.pkl"

# Constants
MIN_SAMPLE = {1: 30, 2: 20, 3: 15, 4: 12}
MIN_EDGE = {1: 15.0, 2: 12.0, 3: 11.0, 4: 10.0}
MAX_COMBO_DEPTH = 4
MONSTER_PCT = 75.0
HOT_PCT = 62.0

# Cached data
_cached_games = None
_cached_sport = None

def _load_games(sport: str) -> list:
    """Load and process historical games for a sport"""
    global _cached_games, _cached_sport

    if _cached_sport == sport and _cached_games is not None:
        return _cached_games

    if not os.path.exists(DATA_FILE):
        print(f"  [ERROR] Database file not found: {DATA_FILE}")
        return []

    with open(DATA_FILE, 'rb') as f:
        data = pickle.load(f)
    all_games = data[0]

    raw_games = [g for g in all_games if g.get('Sport') == sport
                 and g.get('HomeTeam') and g.get('AwayTeam')
                 and g.get('HomeScore') is not None and g.get('AwayScore') is not None]

    # Filter out years with unreliable ATS spread data
    try:
        sys.path.insert(0, r"C:\Users\Nima\handicapping_tool")
        from data_quality import filter_reliable_games
        games = filter_reliable_games(raw_games, sport, include_marginal=True)
        excluded = len(raw_games) - len(games)
        if excluded > 0:
            print(f"  [TRENDS] Excluded {excluded:,} games from unreliable ATS years")
    except ImportError:
        games = raw_games

    # Apply public trend guardrails
    if public_trend_exclusion_reason is not None:
        before_guardrails = len(games)
        games = [g for g in games if public_trend_exclusion_reason(g, sport) is None]
        excluded_guardrails = before_guardrails - len(games)
        if excluded_guardrails > 0:
            print(f"  [TRENDS] Public guardrails suppressed {excluded_guardrails:,} unresolved/unsafe {sport} rows")

    games.sort(key=lambda x: x.get('Date', ''))

    # Process running state
    team_state = {}
    for g in games:
        home = g['HomeTeam']
        away = g['AwayTeam']
        date = g.get('Date', '')
        year = date[:4] if date else '0000'
        hs = int(g.get('HomeScore', 0) or 0)
        as_ = int(g.get('AwayScore', 0) or 0)
        home_won = hs > as_
        spread = g.get('Spread')
        total_line = g.get('Total')
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

        # SPORT-SPECIFIC ATS LOGIC:
        # NBA/NFL: Spread is AWAY TEAM SPREAD (Form 1: Home - Away - Spread)
        # NHL/MLB/NCAAB/NCAAF: Spread is HOME TEAM SPREAD (Form 2: Home - Away + Spread)
        if sport in ("NBA", "NFL"):
            home_ats_margin = home_margin - spread
        else:
            home_ats_margin = home_margin + spread
            
        g['_home_covered'] = home_ats_margin > 0 if spread != 0 else home_won
        g['_away_covered'] = home_ats_margin < 0 if spread != 0 else not home_won
        g['_ats_push'] = home_ats_margin == 0 if spread != 0 else False
        
        g['_over'] = game_total > total_line if total_line else None
        g['_under'] = game_total < total_line if total_line else None
        g['_month'] = int(date[5:7]) if date and len(date) >= 7 else 0
        g['_spread_abs'] = abs(spread) if spread else 0
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

            # Store pre-game state
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

            # Update state
            team_won = (is_home and home_won) or (not is_home and not home_won)
            gf = hs if is_home else as_
            ga = as_ if is_home else hs
            covered = g['_home_covered'] if is_home else g['_away_covered']
            
            # SPORT-SPECIFIC LOGIC:
            # NBA/NFL (Away Spr): Home is fav if Spread > 0, Away is fav if Spread < 0
            # NHL/MLB/NCAAB/NCAAF (Home Spr): Home is fav if Spread < 0, Away is fav if Spread > 0
            if sport in ("NBA", "NFL"):
                if is_home: was_fav = (spread > 0)
                else: was_fav = (spread < 0)
            else:
                if is_home: was_fav = (spread < 0)
                else: was_fav = (spread > 0)

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
    return games

def _build_filters(side, rest_days, streak, last_won, last_gf, last_ga, home_spread, total, wpct, month, opp_wpct=None, opp_rest=None, sport="NBA") -> list:
    """Build a list of filter lambdas for the current situation"""
    p = '_h_' if side == "home" else '_a_'
    opp_p = '_a_' if side == "home" else '_h_'
    
    # SPORT-SPECIFIC LOGIC:
    # NBA/NFL (Away Spr): Home is fav if Spread > 0, Away is fav if Spread < 0
    # NHL/MLB/NCAAB/NCAAF (Home Spr): Home is fav if Spread < 0, Away is fav if Spread > 0
    if sport in ("NBA", "NFL"):
        if side == "home":
            is_fav = (home_spread > 0)
        else:
            is_fav = (home_spread < 0)
    else:
        if side == "home":
            is_fav = (home_spread < 0)
        else:
            is_fav = (home_spread > 0)
        
    last_margin = (last_gf or 0) - (last_ga or 0)
    dow = datetime.now().weekday()
    
    filters = []
    
    # ---- REST (COVERS style) ----
    if rest_days <= 1:
        filters.append(("on B2B", lambda g, p=p: g.get(p + 'rest', 3) <= 1, "REST", ["on 2 days rest", "on 3+ rest"]))
    elif rest_days == 2:
        filters.append(("on 2 days rest", lambda g, p=p: g.get(p + 'rest', 3) == 2, "REST", ["on B2B", "on 3+ rest"]))
    elif rest_days >= 3:
        filters.append(("on 3+ rest", lambda g, p=p: g.get(p + 'rest', 3) >= 3, "REST", ["on B2B", "on 2 days rest"]))

    # ---- WIN/LOSS STREAKS ----
    if streak >= 3:
        filters.append(("on 3+ W streak", lambda g, p=p: g.get(p + 'streak', 0) >= 3, "STREAK", ["on 2+ W streak", "on 3+ L streak"]))
    elif streak >= 2:
        filters.append(("on 2+ W streak", lambda g, p=p: g.get(p + 'streak', 0) >= 2, "STREAK", ["on 3+ W streak", "on 2+ L streak"]))
    elif streak <= -3:
        filters.append(("on 3+ L streak", lambda g, p=p: g.get(p + 'streak', 0) <= -3, "STREAK", ["on 2+ L streak", "on 3+ W streak"]))
    elif streak <= -2:
        filters.append(("on 2+ L streak", lambda g, p=p: g.get(p + 'streak', 0) <= -2, "STREAK", ["on 3+ L streak", "on 2+ W streak"]))

    # ---- LAST GAME RESULT ----
    if last_won is True:
        filters.append(("after W", lambda g, p=p: g.get(p + 'last_won') is True, "LAST", ["after L"]))
    elif last_won is False:
        filters.append(("after L", lambda g, p=p: g.get(p + 'last_won') is False, "LAST", ["after W"]))

    # ---- LAST GAME SCORING (NHL/MLB only) ----
    if sport in ("NHL", "MLB") and last_gf is not None:
        if last_gf >= 4:
            filters.append(("after scoring 4+", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] >= 4, "GF", ["after scoring 0-1"]))
        elif last_gf <= 1:
            filters.append(("after scoring 0-1", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] <= 1, "GF", ["after scoring 4+"]))
        elif 2 <= last_gf <= 3:
            filters.append(("after scoring 2-3", lambda g, p=p: g.get(p + 'last_gf') is not None and 2 <= g[p + 'last_gf'] <= 3, "GF", ["after scoring 4+", "after scoring 0-1"]))

    # ---- GOALS/RUNS ALLOWED (NHL/MLB only) ----
    if sport in ("NHL", "MLB") and last_ga is not None:
        if last_ga >= 4:
            filters.append(("after allowing 4+", lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] >= 4, "GA", ["after allowing 0-1"]))
        elif last_ga <= 1:
            filters.append(("after allowing 0-1", lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] <= 1, "GA", ["after allowing 4+"]))

    # ---- BLOWOUTS / ONE-GOAL GAMES (NHL/MLB only) ----
    if sport in ("NHL", "MLB") and last_margin is not None:
        if last_margin >= 3:
            filters.append(("after blowout W", lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] >= 3, "MARGIN", ["after 1-goal game", "after blowout L"]))
        elif last_margin <= -3:
            filters.append(("after blowout L", lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] <= -3, "MARGIN", ["after 1-goal game", "after blowout W"]))
        elif abs(last_margin) <= 1:
            filters.append(("after 1-goal game", lambda g, p=p: g.get(p + 'last_margin') is not None and abs(g[p + 'last_margin']) <= 1, "MARGIN", ["after blowout W", "after blowout L"]))

    # ---- SHUTOUTS (NHL/MLB only) ----
    if sport in ("NHL", "MLB") and last_gf == 0:
        filters.append(("after shutout", lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] == 0, "SHUTOUT", []))

    # ---- ROLE: Favorite / Underdog ----
    # SPORT-SPECIFIC LOGIC:
    # NBA/NFL (Away Spr): Home is fav if Spread > 0, Away is fav if Spread < 0
    # NHL/MLB/NCAAB/NCAAF (Home Spr): Home is fav if Spread < 0, Away is fav if Spread > 0
    if sport in ("NBA", "NFL"):
        fav_lambda = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) > 0) or (p == '_a_' and float(g['Spread'] or 0) < 0))
        dog_lambda = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) < 0) or (p == '_a_' and float(g['Spread'] or 0) > 0))
    else:
        fav_lambda = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) < 0) or (p == '_a_' and float(g['Spread'] or 0) > 0))
        dog_lambda = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) > 0) or (p == '_a_' and float(g['Spread'] or 0) < 0))

    if is_fav:
        filters.append(("as FAV", fav_lambda, "ROLE", ["as DOG"]))
    else:
        filters.append(("as DOG", dog_lambda, "ROLE", ["as FAV"]))

    # ---- ATS COVER STATUS ----
    filters.append(("after covering", lambda g, p=p: g.get(p + 'last_covered') is True, "ATS", ["after not covering"]))
    filters.append(("after not covering", lambda g, p=p: g.get(p + 'last_covered') is False, "ATS", ["after covering"]))

    # ---- OVER / UNDER STATUS ----
    filters.append(("after OVER", lambda g, p=p: g.get(p + 'last_over') is True, "OU", ["after UNDER"]))
    filters.append(("after UNDER", lambda g, p=p: g.get(p + 'last_over') is False, "OU", ["after OVER"]))

    # ---- TEAM RECORD ----
    if wpct > 0.55:
        filters.append(("winning record", lambda g, p=p: g.get(p + 'wpct', 0.5) > 0.55, "REC", ["losing record", "near .500"]))
    elif wpct < 0.45:
        filters.append(("losing record", lambda g, p=p: g.get(p + 'wpct', 0.5) < 0.45, "REC", ["winning record", "near .500"]))
    else:
        filters.append(("near .500", lambda g, p=p: 0.45 <= g.get(p + 'wpct', 0.5) <= 0.55, "REC", ["winning record", "losing record"]))

    # ---- TOTAL RANGE (NHL only) ----
    if sport == "NHL":
        if total >= 6.0:
            filters.append(("total 6.0+", lambda g: g.get('Total') and float(g['Total'] or 0) >= 6.0, "TRANGE", ["total 5.5-"]))
        elif total and total <= 5.5:
            filters.append(("total 5.5-", lambda g: g.get('Total') and float(g['Total'] or 0) <= 5.5, "TRANGE", ["total 6.0+"]))

    # ---- ROLE + RESULT COMBOS ----
    filters.append(("after W as dog", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_was_fav') is False, "ROLE_RES", ["after L as fav"]))
    filters.append(("after L as fav", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_was_fav') is True, "ROLE_RES", ["after W as dog"]))

    # ---- SPREAD MAGNITUDE ----
    if home_spread >= 5 or home_spread <= -5:
        filters.append(("big spread 5+", lambda g: g.get('_spread_abs', 0) >= 5, "MAG", ["small spread 1-3"]))
    elif 1 <= abs(home_spread) <= 3:
        filters.append(("small spread 1-3", lambda g: 0 < g.get('_spread_abs', 0) <= 3, "MAG", ["big spread 5+"]))

    # ---- OPPONENT RECORD ----
    if opp_wpct is not None:
        if opp_wpct > 0.55:
            filters.append(("vs winning team", lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) > 0.55, "OPP_REC", ["vs losing team"]))
        elif opp_wpct < 0.45:
            filters.append(("vs losing team", lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) < 0.45, "OPP_REC", ["vs winning team"]))

    # ---- REST ADVANTAGE (NFL style) ----
    if opp_rest is not None:
        if rest_days > opp_rest:
            filters.append(("with rest advantage", lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) > g.get(opp_p + 'rest', 3), "OPP_REST", ["with rest disadvantage"]))
        elif rest_days < opp_rest:
            filters.append(("with rest disadvantage", lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) < g.get(opp_p + 'rest', 3), "OPP_REST", ["with rest advantage"]))

    # ---- VENUE SPECIFIC ----
    filters.append(("after road W", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is False, "LAST_VENUE", ["after home L", "after home W", "after road L"]))
    filters.append(("after home W", lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is True, "LAST_VENUE", ["after road L", "after road W", "after home L"]))
    filters.append(("after road L", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is False, "LAST_VENUE", ["after home W", "after home L", "after road W"]))
    filters.append(("after home L", lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is True, "LAST_VENUE", ["after road W", "after road L", "after home W"]))

    # ---- DAY OF WEEK ----
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if dow < 7:
        filters.append((f"on {day_names[dow]}", lambda g, d=dow: g.get('_day_of_week') == d, "DOW", []))

    # ---- WEEKEND vs WEEKDAY ----
    if dow >= 4:  # Fri-Sun
        filters.append(("on weekend", lambda g: g.get('_day_of_week', 0) >= 4, "WEEKEND", ["on weekday"]))
    else:
        filters.append(("on weekday", lambda g: g.get('_day_of_week', 0) < 4, "WEEKEND", ["on weekend"]))

    # ---- MONTHLY TRENDS ----
    month_name = datetime(2000, month, 1).strftime("%b")
    filters.append((f"in {month_name}", lambda g, m=month: g.get('_month') == m, "MONTH", []))

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
    
    ov = sum(1 for g in games if g.get('_over'))
    un = sum(1 for g in games if g.get('_under'))
    
    n = len(games)
    n_ats = w + l
    n_ou = ov + un
    
    return {
        "games": n,
        "w": w, "l": l, "p": p,
        "ov": ov, "un": un,
        "pct": w / n_ats * 100 if n_ats > 0 else 50,
        "ou_pct": ov / n_ou * 100 if n_ou > 0 else 50,
    }

def _run_combos(base_games, side, filters) -> list:
    """Find the best situational trends for a game"""
    n_filters = len(filters)
    results = []

    for depth in range(1, min(MAX_COMBO_DEPTH + 1, n_filters + 1)):
        min_n = MIN_SAMPLE.get(depth, 6)
        min_edge = MIN_EDGE.get(depth, 10)

        for combo in combinations(range(n_filters), depth):
            has_conflict = False
            categories = []
            for i in combo:
                cat = filters[i][2]
                if cat and categories.count(cat) > 0:
                    has_conflict = True
                    break
                categories.append(cat)
                for c_label in filters[i][3]:
                    for other_i in combo:
                        if filters[other_i][0] == c_label:
                            has_conflict = True
                            break
                    if has_conflict: break
                if has_conflict: break
            if has_conflict: continue

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
                    "rec": rec,
                    "depth": depth,
                    "edge": max(edge, ou_edge - 5)
                })
    return results

def _format_trend_description(team, venue, labels):
    """Convert label list to English description"""
    venue_str = "at home" if venue == "home" else "on the road"
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
        "after W as dog": "after winning as an underdog",
        "after L as fav": "after losing as the favorite",
        "big spread 5+": "with a spread of 5+",
        "small spread 1-3": "with a spread of 1-3",
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
        "total 6.0+": "when the total is set at 6.0+",
        "total 5.5-": "when the total is set at 5.5 or lower",
    }
    desc_labels = [LABEL_MAP.get(l, l) for l in labels]
    return f"{team} {venue_str}, " + ", ".join(desc_labels)

def generate_trends_html(sport, home_abbr, away_abbr, home_spread, total, home_rest=3, away_rest=3, home_streak=0, away_streak=0, home_last_won=None, away_last_won=None, home_last_gf=None, home_last_ga=None, away_last_gf=None, away_last_ga=None, home_wpct=0.5, away_wpct=0.5) -> str:
    games = _load_games(sport)
    if not games: return ''
    team_map = {
        "NBA": {"ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets", "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers", "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons", "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers", "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies", "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves", "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns", "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards"},
        "NHL": {"ANA": "Anaheim Ducks", "ARI": "Arizona Coyotes", "BOS": "Boston Bruins", "BUF": "Buffalo Sabres", "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes", "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets", "DAL": "Dallas Stars", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers", "FLA": "Florida Panthers", "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild", "MTL": "Montreal Canadiens", "NSH": "Nashville Predators", "NJ": "New Jersey Devils", "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators", "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks", "SEA": "Seattle Kraken", "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning", "TOR": "Toronto Maple Leafs", "VAN": "Vancouver Canucks", "VGK": "Vegas Golden Knights", "WSH": "Washington Capitals", "WPG": "Winnipeg Jets"},
        "MLB": {"ARI": "Arizona Diamondbacks", "ATL": "Atlanta Braves", "BAL": "Baltimore Orioles", "BOS": "Boston Red Sox", "CHC": "Chicago Cubs", "CHW": "Chicago White Sox", "CIN": "Cincinnati Reds", "CLE": "Cleveland Guardians", "COL": "Colorado Rockies", "DET": "Detroit Tigers", "HOU": "Houston Astros", "KC": "Kansas City Royals", "LAA": "Los Angeles Angels", "LAD": "Los Angeles Dodgers", "MIA": "Miami Marlins", "MIL": "Milwaukee Brewers", "MIN": "Minnesota Twins", "NYM": "New York Mets", "NYY": "New York Yankees", "OAK": "Oakland Athletics", "ATH": "Oakland Athletics", "PHI": "Philadelphia Phillies", "PIT": "Pittsburgh Pirates", "SD": "San Diego Padres", "SF": "San Francisco Giants", "SEA": "Seattle Mariners", "STL": "St. Louis Cardinals", "TB": "Tampa Bay Rays", "TEX": "Texas Rangers", "TOR": "Toronto Blue Jays", "WSH": "Washington Nationals"}
    }
    sport_teams = team_map.get(sport, {})
    home_full = sport_teams.get(home_abbr, home_abbr)
    away_full = sport_teams.get(away_abbr, away_abbr)
    home_games = [g for g in games if g.get('HomeTeam') == home_full]
    away_games = [g for g in games if g.get('AwayTeam') == away_full]
    month = datetime.now().month
    home_filters = _build_filters("home", home_rest, home_streak, home_last_won, home_last_gf, home_last_ga, home_spread, total, home_wpct, month, opp_wpct=away_wpct, opp_rest=away_rest, sport=sport)
    away_filters = _build_filters("away", away_rest, away_streak, away_last_won, away_last_gf, away_last_ga, home_spread, total, away_wpct, month, opp_wpct=home_wpct, opp_rest=home_rest, sport=sport)
    home_results = _run_combos(home_games, "home", home_filters)
    away_results = _run_combos(away_games, "away", away_filters)
    all_results = []
    for r in home_results: r["team"] = home_full; r["venue"] = "home"; all_results.append(r)
    for r in away_results: r["team"] = away_full; r["venue"] = "away"; all_results.append(r)
    all_results.sort(key=lambda x: x["edge"] * min(x["rec"]["games"], 50), reverse=True)
    hot_rows, monster_rows, fade_rows, ou_rows = [], [], [], []
    used_labels = set()
    for r in all_results:
        if len(monster_rows) + len(hot_rows) + len(fade_rows) + len(ou_rows) >= 12: break
        label_key = tuple(sorted(r["labels"]))
        if label_key in used_labels: continue
        used_labels.add(label_key)
        desc = _format_trend_description(r["team"], r["venue"], r["labels"])
        rec = r["rec"]
        tier = ""
        if rec["pct"] >= MONSTER_PCT: tier = "MONSTER"
        elif rec["pct"] >= HOT_PCT: tier = "HOT"
        elif rec["pct"] <= (100 - HOT_PCT): tier = "FADE"
        if tier == "MONSTER": monster_rows.append(f'<tr class="tier-monster"><td class="trend-tier">MONSTER</td><td class="trend-desc">{desc}</td><td class="trend-record">{rec["w"]}-{rec["l"]}</td><td class="trend-cover">{rec["pct"]:.1f}%</td><td class="trend-games">{rec["games"]}</td></tr>')
        elif tier == "HOT": hot_rows.append(f'<tr class="tier-hot"><td class="trend-tier">HOT</td><td class="trend-desc">{desc}</td><td class="trend-record">{rec["w"]}-{rec["l"]}</td><td class="trend-cover">{rec["pct"]:.1f}%</td><td class="trend-games">{rec["games"]}</td></tr>')
        elif tier == "FADE": fade_rows.append(f'<tr class="tier-fade"><td class="trend-tier">FADE</td><td class="trend-desc">{desc}</td><td class="trend-record">{rec["w"]}-{rec["l"]}</td><td class="trend-fade">{100-rec["pct"]:.1f}%</td><td class="trend-games">{rec["games"]}</td></tr>')
        if rec["ou_pct"] >= HOT_PCT or rec["ou_pct"] <= (100 - HOT_PCT):
            lean = "OVER" if rec["ou_pct"] >= 50 else "UNDER"; ou_class = "ou-over" if lean == "OVER" else "ou-under"
            ou_rows.append(f'<tr><td class="trend-desc">{desc}</td><td class="trend-record">{rec["ov"]}O-{rec["un"]}U ({rec["ou_pct"]:.1f}%)</td><td class="trend-games">{rec["games"]}</td><td class="{ou_class}"><strong>{lean}</strong></td></tr>')
    if not monster_rows and not hot_rows and not fade_rows and not ou_rows: return ''
    html = f'<div class="historical-trends"><div class="section-title">HISTORICAL TRENDS <span class="trends-badge">{len(monster_rows)+len(hot_rows)+len(fade_rows)} found</span></div><table class="trends-table"><thead><tr><th>TIER</th><th>SITUATION</th><th>ATS</th><th>HIT%</th><th>GAMES</th></tr></thead><tbody>{" ".join(monster_rows)}{" ".join(hot_rows)}{" ".join(fade_rows)}</tbody></table>'
    if ou_rows: html += f'<div class="trends-ou"><div class="section-title">O/U TRENDS <span class="trends-badge">{len(ou_rows)} found</span></div><table class="trends-table"><thead><tr><th>SITUATION</th><th>RECORD</th><th>GAMES</th><th>LEAN</th></tr></thead><tbody>{" ".join(ou_rows[:4])}</tbody></table></div>'
    html += '</div>'
    return html

def get_trends_css():
    return '.historical-trends { margin-top: 25px; background: rgba(0, 0, 0, 0.2); border-radius: 12px; padding: 20px; border: 1px solid rgba(255, 255, 255, 0.05); } .trends-badge { background: #f39c12; color: #000; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; margin-left: 10px; vertical-align: middle; } .trends-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9rem; } .trends-table th { text-align: left; padding: 8px; color: #999; font-size: 0.75rem; text-transform: uppercase; border-bottom: 1px solid rgba(255, 255, 255, 0.1); } .trends-table td { padding: 12px 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); } .trend-tier { font-weight: 800; font-size: 0.75rem; } .tier-monster .trend-tier { color: #00f5ff; text-shadow: 0 0 8px rgba(0, 245, 255, 0.4); } .tier-hot .trend-tier { color: #f1c40f; } .tier-fade .trend-tier { color: #ff69b4; text-shadow: 0 0 8px rgba(255,105,180,0.4); } .trend-desc { color: #e0e0e0; line-height: 1.4; } .trend-record { font-family: "Courier New", monospace; color: #fff; } .trend-cover { color: #2ecc71; font-weight: 800; text-align: center; } .trend-fade { color: #ff6b6b; font-weight: 800; text-align: center; } .trend-games { color: #7f8c8d; text-align: center; } .trends-ou { margin-top: 25px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 20px; } .ou-over { color: #2ecc71; font-weight: 700; font-size: 1.05rem; } .ou-under { color: #ff6b6b; font-weight: 700; font-size: 1.05rem; }'
