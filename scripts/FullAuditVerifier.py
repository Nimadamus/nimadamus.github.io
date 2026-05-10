#!/usr/bin/env python3
import pickle
import sys
import os
import json
import re
from datetime import datetime
from collections import defaultdict

DATA_FILE = r"C:\Users\Nima\universal_games.pkl"
sys.path.insert(0, r"C:\Users\Nima\handicapping_tool")
from data_quality import filter_reliable_games

try:
    # We are in scripts/
    from sellable_market_eligibility import public_trend_exclusion_reason
except ImportError:
    public_trend_exclusion_reason = None

# Reverse map from English phrase to internal label
LABEL_MAP = {
    "as the favorite": "as FAV",
    "as the underdog": "as DOG",
    "on a back-to-back": "on B2B",
    "with 2 days rest": "on 2 days rest",
    "with 3+ days rest": "on 3+ rest",
    "coming off a win": "after W",
    "coming off a loss": "after L",
    "after scoring 4+ goals last game": "after scoring 4+",
    "after scoring 0-1 goals last game": "after scoring 0-1",
    "after scoring 2-3 goals last game": "after scoring 2-3",
    "after allowing 4+ goals last game": "after allowing 4+",
    "after allowing 0-1 goals last game": "after allowing 0-1",
    "after a blowout win (3+ goals)": "after blowout W",
    "after a blowout loss (3+ goals)": "after blowout L",
    "after a one-goal game": "after 1-goal game",
    "after being shut out": "after shutout",
    "on a 3+ game win streak": "on 3+ W streak",
    "on a 2+ game win streak": "on 2+ W streak",
    "on a 3+ game losing streak": "on 3+ L streak",
    "on a 2+ game losing streak": "on 2+ L streak",
    "after covering the spread": "after covering",
    "after failing to cover": "after not covering",
    "after their last game went over": "after OVER",
    "after their last game went under": "after UNDER",
    "with a winning record": "winning record",
    "with a losing record": "losing record",
    "after winning as an underdog": "after W as dog",
    "after losing as the favorite": "after L as fav",
    "with a spread of 5+": "big spread 5+",
    "with a spread of 1-3": "small spread 1-3",
    "with a rest advantage over the opponent": "with rest advantage",
    "with a rest disadvantage vs the opponent": "with rest disadvantage",
    "on a 2-game win streak": "on 2 W streak",
    "on a 2+ game ATS cover streak": "on 2+ ATS cover streak",
    "on a 2+ game ATS non-cover streak": "on 2+ ATS fade streak",
    "with a near-.500 record": "near .500",
    "against a team with a winning record": "vs winning team",
    "against a team with a losing record": "vs losing team",
    "coming off a road win": "after road W",
    "coming off a home win": "after home W",
    "coming off a road loss": "after road L",
    "coming off a home loss": "after home L",
    "playing on a weekend": "on weekend",
    "playing on a weekday": "on weekday",
    "when the total is set at 6.0+": "total 6.0+",
    "when the total is set at 5.5 or lower": "total 5.5-",
}

def load_data(sport):
    print(f"Loading {sport} data...")
    with open(DATA_FILE, 'rb') as f:
        data = pickle.load(f)
    all_games = data[0]
    
    raw_games = [g for g in all_games if g.get('Sport') == sport
                 and g.get('HomeTeam') and g.get('AwayTeam')
                 and g.get('HomeScore') is not None and g.get('AwayScore') is not None]
    
    if public_trend_exclusion_reason is not None:
        before = len(raw_games)
        raw_games = [g for g in raw_games if public_trend_exclusion_reason(g, sport) is None]
        print(f"  [DEBUG] Guardrails excluded {before - len(raw_games)} {sport} games")

    games = filter_reliable_games(raw_games, sport, include_marginal=True)
    print(f"  [DEBUG] {sport} games after DQ filter: {len(games)}")
    excluded = len(raw_games) - len(games)
    if excluded > 0:
        print(f"  [DEBUG] Excluded {excluded} {sport} games from unreliable ATS years")
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
        spread = g.get('Spread') or 0
        total_line = g.get('Total') or 0
        game_total = hs + as_
        home_margin = hs - as_

        g['_game_total'] = game_total
        g['_home_margin'] = home_margin
        g['_home_won'] = home_won
        try: spread = float(spread) if spread else 0
        except: spread = 0
        try: total_line = float(total_line) if total_line else 0
        except: total_line = 0

        # SPORT-SPECIFIC ATS LOGIC
        if sport in ("NBA", "NFL", "NCAAB", "NCAAF"):
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
        try: g['_day_of_week'] = datetime.strptime(date, '%Y-%m-%d').weekday()
        except: g['_day_of_week'] = 0

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
                try: g[p + 'rest'] = (datetime.strptime(date, '%Y-%m-%d') - datetime.strptime(st['last_date'], '%Y-%m-%d')).days
                except: g[p + 'rest'] = 3
            else: g[p + 'rest'] = 3
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
            
            if sport in ("NBA", "NFL", "NCAAB", "NCAAF"):
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
            
    return games

def extract_trends(html_path):
    if not os.path.exists(html_path):
        print(f"Error: {html_path} not found")
        return []

    from bs4 import BeautifulSoup
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    trends = []
    cards = soup.find_all('div', class_='game-card')
    for card in cards:
        sport = card.get('data-sport', 'NBA').upper()
        
        tables = card.find_all('table', class_='trends-table')
        for table in tables:
            headers = [th.text.strip().upper() for th in table.find_all('th')]
            is_ou_table = "LEAN" in headers or "O/U" in headers
            
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if not cols: continue
                
                if is_ou_table:
                    situation = cols[0].text.strip()
                    record_text = cols[1].text.strip()
                    games = cols[2].text.strip()
                    match = re.search(r'(\d+)O-(\d+)U', record_text)
                    wins = int(match.group(1)) if match else 0
                    losses = int(match.group(2)) if match else 0
                    trends.append({"sport": sport, "market": "OU", "situation": situation, "record": record_text, "wins": wins, "losses": losses, "pushes": 0, "games": int(games) if games.isdigit() else 0, "tier": "OU"})
                else:
                    if len(cols) < 5: continue
                    tier = cols[0].text.strip()
                    situation = cols[1].text.strip()
                    ats_record = cols[2].text.strip()
                    games = cols[4].text.strip()
                    parts = ats_record.split('-')
                    w = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
                    l = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
                    p = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
                    trends.append({"sport": sport, "market": "ATS", "tier": tier, "situation": situation, "record": ats_record, "wins": w, "losses": l, "pushes": p, "games": int(games) if games.isdigit() else 0})
    return trends

def get_filter_lambda(label, p, opp_p, sport):
    if sport in ("NBA", "NFL"):
        fav_condition = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) > 0) or (p == '_a_' and float(g['Spread'] or 0) < 0))
        dog_condition = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) < 0) or (p == '_a_' and float(g['Spread'] or 0) > 0))
    else:
        fav_condition = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) < 0) or (p == '_a_' and float(g['Spread'] or 0) > 0))
        dog_condition = lambda g, p=p: g.get('Spread') is not None and ((p == '_h_' and float(g['Spread'] or 0) > 0) or (p == '_a_' and float(g['Spread'] or 0) < 0))

    if label == "as FAV": return fav_condition
    if label == "as DOG": return dog_condition
    if label == "on B2B": return lambda g, p=p: g.get(p + 'rest', 3) <= 1
    if label == "on 2 days rest": return lambda g, p=p: g.get(p + 'rest', 3) == 2
    if label == "on 3+ rest": return lambda g, p=p: g.get(p + 'rest', 3) >= 3
    if label == "after W": return lambda g, p=p: g.get(p + 'last_won') is True
    if label == "after L": return lambda g, p=p: g.get(p + 'last_won') is False
    if label == "after scoring 4+": return lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] >= 4
    if label == "after scoring 0-1": return lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] <= 1
    if label == "after scoring 2-3": return lambda g, p=p: g.get(p + 'last_gf') is not None and 2 <= g[p + 'last_gf'] <= 3
    if label == "after allowing 4+": return lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] >= 4
    if label == "after allowing 0-1": return lambda g, p=p: g.get(p + 'last_ga') is not None and g[p + 'last_ga'] <= 1
    if label == "after blowout W": return lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] >= 3
    if label == "after blowout L": return lambda g, p=p: g.get(p + 'last_margin') is not None and g[p + 'last_margin'] <= -3
    if label == "after 1-goal game": return lambda g, p=p: g.get(p + 'last_margin') is not None and abs(g[p + 'last_margin']) <= 1
    if label == "after shutout": return lambda g, p=p: g.get(p + 'last_gf') is not None and g[p + 'last_gf'] == 0
    if label == "on 3+ W streak": return lambda g, p=p: g.get(p + 'streak', 0) >= 3
    if label == "on 2+ W streak": return lambda g, p=p: g.get(p + 'streak', 0) >= 2
    if label == "on 3+ L streak": return lambda g, p=p: g.get(p + 'streak', 0) <= -3
    if label == "on 2+ L streak": return lambda g, p=p: g.get(p + 'streak', 0) <= -2
    if label == "after covering": return lambda g, p=p: g.get(p + 'last_covered') is True
    if label == "after not covering": return lambda g, p=p: g.get(p + 'last_covered') is False
    if label == "after OVER": return lambda g, p=p: g.get(p + 'last_over') is True
    if label == "after UNDER": return lambda g, p=p: g.get(p + 'last_over') is False
    if label == "winning record": return lambda g, p=p: g.get(p + 'wpct', 0.5) > 0.55
    if label == "losing record": return lambda g, p=p: g.get(p + 'wpct', 0.5) < 0.45
    if label == "after W as dog": return lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_was_fav') is False
    if label == "after L as fav": return lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_was_fav') is True
    if label == "big spread 5+": return lambda g: g.get('_spread_abs', 0) >= 5
    if label == "small spread 1-3": return lambda g: 0 < g.get('_spread_abs', 0) <= 3
    if label == "with rest advantage": return lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) > g.get(opp_p + 'rest', 3)
    if label == "with rest disadvantage": return lambda g, p=p, opp_p=opp_p: g.get(p + 'rest', 3) < g.get(opp_p + 'rest', 3)
    if label == "on 2 W streak": return lambda g, p=p: g.get(p + 'streak', 0) == 2
    if label == "on 2+ ATS cover streak": return lambda g, p=p: g.get(p + 'ats_streak', 0) >= 2
    if label == "on 2+ ATS fade streak": return lambda g, p=p: g.get(p + 'ats_streak', 0) <= -2
    if label == "near .500": return lambda g, p=p: 0.45 <= g.get(p + 'wpct', 0.5) <= 0.55
    if label == "vs winning team": return lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) > 0.55
    if label == "vs losing team": return lambda g, opp_p=opp_p: g.get(opp_p + 'wpct', 0.5) < 0.45
    if label == "after road W": return lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is False
    if label == "after home W": return lambda g, p=p: g.get(p + 'last_won') is True and g.get(p + 'last_home') is True
    if label == "after road L": return lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is False
    if label == "after home L": return lambda g, p=p: g.get(p + 'last_won') is False and g.get(p + 'last_home') is True
    if label == "on weekend": return lambda g: g.get('_day_of_week', 0) >= 4
    if label == "on weekday": return lambda g: g.get('_day_of_week', 0) < 4
    if label == "total 6.0+": return lambda g: g.get('Total') and float(g['Total'] or 0) >= 6.0
    if label == "total 5.5-": return lambda g: g.get('Total') and float(g['Total'] or 0) <= 5.5
    if label.startswith("in "):
        m_str = label[3:]; m_map = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12}; m_val = m_map.get(m_str)
        return lambda g, mv=m_val: g.get('_month') == mv
    if label.startswith("on "):
        d_str = label[3:]; d_map = {"Mon":0,"Tue":1,"Wed":2,"Thu":3,"Fri":4,"Sat":5,"Sun":6}; d_val = d_map.get(d_str)
        return lambda g, dv=d_val: g.get('_day_of_week') == dv
    return lambda g: True

def verify_trend(trend, all_games):
    sport = trend['sport']; situation = trend['situation']
    if " at home, " in situation: team_name, filters_str = situation.split(" at home, ", 1); side = "home"
    elif " on the road, " in situation: team_name, filters_str = situation.split(" on the road, ", 1); side = "away"
    else:
        if situation.endswith(" at home"): team_name = situation[:-8]; filters_str = ""; side = "home"
        elif situation.endswith(" on the road"): team_name = situation[:-12]; filters_str = ""; side = "away"
        else: return {"passed": False, "error": "Could not parse situation"}
    filter_phrases = [f.strip() for f in filters_str.split(",")] if filters_str else []
    labels = [LABEL_MAP.get(p, p if p.startswith("in ") or p.startswith("on ") else p) for p in filter_phrases]
    base_games = [g for g in all_games if g.get('HomeTeam' if side == "home" else 'AwayTeam') == team_name]
    p_prefix = '_h_' if side == "home" else '_a_'; opp_prefix = '_a_' if side == "home" else '_h_'
    filtered = base_games
    for lbl in labels:
        f_lambda = get_filter_lambda(lbl, p_prefix, opp_prefix, sport)
        filtered = [g for g in filtered if f_lambda(g)]
    if not filtered: return {"passed": False, "error": "No games found after filtering"}
    if side == "home": w = sum(1 for g in filtered if g.get('_home_covered')); l = sum(1 for g in filtered if g.get('_away_covered'))
    else: w = sum(1 for g in filtered if g.get('_away_covered')); l = sum(1 for g in filtered if g.get('_home_covered'))
    p = sum(1 for g in filtered if g.get('_ats_push')); ov = sum(1 for g in filtered if g.get('_over')); un = sum(1 for g in filtered if g.get('_under'))
    if trend['market'] == "ATS":
        passed = (w == trend['wins'] and l == trend['losses'] and len(filtered) == trend['games'])
        return {"passed": passed, "calc_w": w, "calc_l": l, "calc_p": p, "calc_games": len(filtered), "expected_w": trend['wins'], "expected_l": trend['losses'], "expected_games": trend['games']}
    else:
        passed = (ov == trend['wins'] and un == trend['losses'] and len(filtered) == trend['games'])
        return {"passed": passed, "calc_over": ov, "calc_under": un, "calc_games": len(filtered), "expected_over": trend['wins'], "expected_under": trend['losses'], "expected_games": trend['games']}
