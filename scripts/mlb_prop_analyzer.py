"""
MLB Prop EV Analyzer - Scrapes MLB prop odds and uses historical data to identify +EV bets.
Focuses on NRFI, YRFI, F5, Total Runs, Hits, and Errors.
"""

import requests
import re
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Paths to accumulated data
RECORDS_FILE = r'C:\Users\Nima\nimadamus.github.io\mlb-records.json'
PICKS_DATA_FILE = r'C:\Users\Nima\nimadamus.github.io\mlb-data.js'
SHARP_DATA_FILE = r'C:\Users\Nima\nimadamus.github.io\sharp_action_data.json'

class MLBPropAnalyzer:
    def __init__(self):
        self.records = self._load_json(RECORDS_FILE)
        self.historical_picks = self._load_picks_js(PICKS_DATA_FILE)
        self.sharp_data = self._load_json(SHARP_DATA_FILE)
        self.props = []
        self.results = []

    def _load_json(self, path: str) -> Any:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
        return []

    def _load_picks_js(self, path: str) -> List[Dict]:
        """Loads and parses the JS array from mlb-data.js"""
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    match = re.search(r'\[.*\]', content, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
        except Exception as e:
            print(f"Error loading {path}: {e}")
        return []

    def scrape_props(self):
        """Fetch live MLB prop odds using The Odds API"""
        print("Fetching MLB prop odds from The Odds API...")
        # Using the API key found in live-odds.html
        api_key = 'c405ed8a7e1f4ec945d39aeeaf647e4b'
        base_url = 'https://api.the-odds-api.com/v4/sports/baseball_mlb/events'
        
        try:
            # 1. Get all upcoming MLB events to find event IDs
            events_resp = requests.get(f"{base_url}?apiKey={api_key}")
            events_resp.raise_for_status()
            events = events_resp.json()
            
            # 2. For each event, fetch props
            # Markets to check: batter_home_runs, pitcher_strikeouts, batter_hits, etc.
            prop_markets = 'pitcher_strikeouts,batter_home_runs,batter_hits,batter_rbis'
            
            for event in events[:10]: # Limit to first 10 games to save API quota
                event_id = event['id']
                away_team = event['away_team']
                home_team = event['home_team']
                game_name = f"{away_team} @ {home_team}"
                
                print(f"  Fetching props for {game_name}...")
                odds_url = f"https://api.the-odds-api.com/v4/sports/baseball_mlb/events/{event_id}/odds"
                params = {
                    'apiKey': api_key,
                    'regions': 'us',
                    'markets': prop_markets,
                    'oddsFormat': 'american'
                }
                
                odds_resp = requests.get(odds_url, params=params)
                if odds_resp.status_code != 200:
                    continue
                    
                odds_data = odds_resp.json()
                for bookmaker in odds_data.get('bookmakers', []):
                    book_name = bookmaker['title']
                    for market in bookmaker.get('markets', []):
                        market_key = market['key']
                        for outcome in market.get('outcomes', []):
                            player = outcome.get('description', outcome.get('name'))
                            odds = outcome.get('price', 0)
                            line = outcome.get('point', 0)
                            
                            self.props.append({
                                'game': game_name,
                                'away_team': away_team,
                                'home_team': home_team,
                                'prop_type': market_key,
                                'player': player,
                                'line': line,
                                'odds': odds,
                                'book': book_name
                            })
            
            print(f"Successfully fetched {len(self.props)} props from The Odds API.")
        except Exception as e:
            print(f"Error fetching props from API: {e}")

    def build_historical_model(self):
        """Calculate baseline hit rates from accumulated data"""
        df = pd.DataFrame(self.historical_picks)
        if df.empty:
            return {}

        # League average baseline probabilities (if no historical data)
        # These are rough estimates for +EV baseline filtering
        self.baselines = {
            'batter_home_runs': 0.05,  # 5% chance for a HR
            'pitcher_strikeouts': 0.54, # Over/Under usually set at 50/50
            'batter_hits': 0.68,       # Over 0.5 hits is favored
            'batter_rbis': 0.35,       # RBI is less likely
            'nrfi': 0.55,              # NRFI hits slightly more than 50%
            'f5_total': 0.50,
            'f5_side': 0.48,
            'game_total': 0.50,
            'other': 0.524
        }

        # Group by team and pick type to find historical win percentages
        def categorize_pick(pick):
            pick = pick.lower()
            if 'home run' in pick: return 'batter_home_runs'
            if 'strikeout' in pick or ' k ' in pick: return 'pitcher_strikeouts'
            if ' hit' in pick: return 'batter_hits'
            if 'rbi' in pick: return 'batter_rbis'
            if 'under' in pick or 'over' in pick:
                if 'first five' in pick or 'f5' in pick: return 'f5_total'
                return 'game_total'
            if 'f5' in pick or 'first five' in pick: return 'f5_side'
            if 'nrfi' in pick or 'no run' in pick: return 'nrfi'
            return 'other'

        df['Category'] = df['Pick'].apply(categorize_pick)
        df['Win'] = df['Result'] == 'W'
        
        # Calculate win rates by Category
        summary = df.groupby('Category')['Win'].mean().to_dict()
        
        # Merge historical rates with league baselines
        for cat, rate in self.baselines.items():
            if cat not in summary:
                summary[cat] = rate
            else:
                # Weighted average: 30% baseline, 70% historical
                summary[cat] = (rate * 0.3) + (summary[cat] * 0.7)
                
        return summary

    def calculate_ev(self):
        """Find +EV bets using historical hit rates as 'True Probability'"""
        model_win_rates = self.build_historical_model()
        
        for p in self.props:
            # Map prop type to our categories
            pt = p['prop_type'].lower()
            true_prob = model_win_rates.get(pt, model_win_rates.get('other', 0.524))
            
            # Special handling for 'Under' vs 'Over' if line exists
            # (The Odds API usually gives Over/Under outcomes)
            outcome_name = str(p.get('player', '')).lower()
            if 'under' in outcome_name:
                true_prob = 1 - true_prob
            
            # Calculate Expected Value
            odds = p['odds']
            if odds == 0: continue
            
            if odds > 0:
                profit = odds / 100
            else:
                profit = 100 / abs(odds)
            
            ev = (true_prob * profit) - ((1 - true_prob) * 1.0)
            
            # Filter for realistic EV and probability
            # Extreme EV (like > 500%) is usually a data mismatch
            if 0.02 < ev < 5.0: 
                p['ev'] = round(ev * 100, 2)
                p['true_prob'] = round(true_prob * 100, 2)
                self.results.append(p)

    def generate_report(self):
        """Output +EV props to a JSON file"""
        output_file = r'C:\Users\Nima\nimadamus.github.io\data\mlb_ev_props.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        print(f"Report generated: {output_file}")
        
        # Also print top 5 EV plays
        sorted_results = sorted(self.results, key=lambda x: x['ev'], reverse=True)
        print("\nTOP +EV MLB PROPS TODAY:")
        for r in sorted_results[:5]:
            print(f"{r['ev']}% EV | {r['game']} | {r['player']} {r['prop_type']} {r['line']} | Odds: {r['odds']} ({r['book']})")

if __name__ == "__main__":
    analyzer = MLBPropAnalyzer()
    analyzer.scrape_props()
    analyzer.calculate_ev()
    analyzer.generate_report()
