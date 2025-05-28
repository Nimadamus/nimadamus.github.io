import requests
import json
from datetime import datetime

# Your API keys (keep private in production)
API_SPORTS_KEY = "c63a449bea9b087de00bc25f8fe42f7a"
ODDS_API_KEY = "c405ed8a7e1f4ec945d39aeeaf647e4b"

# Step 1: Fetch matchups from API-Sports
today = datetime.now().strftime('%Y-%m-%d')
headers = {
    "x-apisports-key": API_SPORTS_KEY
}
matchup_resp = requests.get(
    f"https://v1.baseball.api-sports.io/games?date={today}",
    headers=headers
)
games_data = matchup_resp.json().get("response", [])

# Step 2: Fetch odds from The Odds API
odds_resp = requests.get(
    f"https://api.the-odds-api.com/v4/sports/baseball_ml/mlb/odds",
    params={
        "regions": "us",
        "markets": "h2h,totals",
        "dateFormat": "iso",
        "oddsFormat": "american",
        "apiKey": ODDS_API_KEY
    }
)
odds_data = odds_resp.json()

# Helper to match odds to teams
def find_game_odds(home_team, away_team):
    for game in odds_data:
        if (game["home_team"] == home_team and game["away_team"] == away_team):
            odds = {"moneyline": {}, "total": {}}
            for book in game.get("bookmakers", []):
                if "markets" in book:
                    for market in book["markets"]:
                        if market["key"] == "h2h":
                            outcomes = market["outcomes"]
                            for o in outcomes:
                                if o["name"] == home_team:
                                    odds["moneyline"]["home"] = o["price"]
                                elif o["name"] == away_team:
                                    odds["moneyline"]["away"] = o["price"]
                        elif market["key"] == "totals":
                            for o in market["outcomes"]:
                                if o["name"] == "Over":
                                    odds["total"]["line"] = market["outcomes"][0]["point"]
                                    odds["total"]["over"] = o["price"]
                                elif o["name"] == "Under":
                                    odds["total"]["under"] = o["price"]
            return odds
    return {"moneyline": {}, "total": {}}

# Step 3: Combine into feed
combined = {
    "date": today,
    "games": []
}

for g in games_data:
    home = g["teams"]["home"]["name"]
    away = g["teams"]["away"]["name"]
    start_time = g["time"]
    pitchers = {
        "home": g["pitchers"]["home"]["player"]["name"] if g["pitchers"]["home"] else "TBD",
        "away": g["pitchers"]["away"]["player"]["name"] if g["pitchers"]["away"] else "TBD"
    }
    odds = find_game_odds(home, away)
    combined["games"].append({
        "home_team": home,
        "away_team": away,
        "start_time": start_time,
        "pitchers": pitchers,
        "odds": odds
    })

# Step 4: Save to file
with open("data/live_feed.json", "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)
