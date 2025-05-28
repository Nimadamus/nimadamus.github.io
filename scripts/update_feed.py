import requests
import json
from datetime import datetime
import difflib

# Keys
API_SPORTS_KEY = "c63a449bea9b087de00bc25f8fe42f7a"
ODDS_API_KEY = "c405ed8a7e1f4ec945d39aeeaf647e4b"

today = datetime.now().strftime('%Y-%m-%d')

# 1. Get matchups from API-Sports
headers = {
    "x-apisports-key": API_SPORTS_KEY
}
matchup_resp = requests.get(
    f"https://v1.baseball.api-sports.io/games?date={today}",
    headers=headers
)
games_data = matchup_resp.json().get("response", [])

# 2. Get odds from The Odds API
odds_resp = requests.get(
    "https://api.the-odds-api.com/v4/sports/baseball_mlb/odds",
    params={
        "regions": "us",
        "markets": "h2h,totals",
        "oddsFormat": "american",
        "apiKey": ODDS_API_KEY
    }
)
odds_data = odds_resp.json()

def match_team(name, options):
    """Use fuzzy matching to find the best match for a team name."""
    matches = difflib.get_close_matches(name, options, n=1, cutoff=0.5)
    return matches[0] if matches else None

def find_odds(home_team, away_team):
    team_names = set()
    for game in odds_data:
        team_names.add(game.get("home_team", ""))
        team_names.add(game.get("away_team", ""))

    matched_home = match_team(home_team, list(team_names))
    matched_away = match_team(away_team, list(team_names))

    for game in odds_data:
        if game.get("home_team") == matched_home and game.get("away_team") == matched_away:
            odds = {"moneyline": {}, "total": {}}
            for book in game.get("bookmakers", []):
                for market in book.get("markets", []):
                    if market["key"] == "h2h":
                        for o in market["outcomes"]:
                            if o["name"] == matched_home:
                                odds["moneyline"]["home"] = o["price"]
                            elif o["name"] == matched_away:
                                odds["moneyline"]["away"] = o["price"]
                    if market["key"] == "totals":
                        for o in market["outcomes"]:
                            if o["name"] == "Over":
                                odds["total"]["line"] = market["outcomes"][0]["point"]
                                odds["total"]["over"] = o["price"]
                            elif o["name"] == "Under":
                                odds["total"]["under"] = o["price"]
            return odds
    return {"moneyline": {}, "total": {}}

# 3. Build feed
combined = {
    "date": today,
    "games": []
}

for g in games_data:
    home = g["teams"]["home"]["name"]
    away = g["teams"]["away"]["name"]
    start_time = g["time"]
    pitchers = {
        "home": g.get("pitchers", {}).get("home", {}).get("player", {}).get("name", "TBD"),
        "away": g.get("pitchers", {}).get("away", {}).get("player", {}).get("name", "TBD")
    }
    odds = find_odds(home, away)
    combined["games"].append({
        "home_team": home,
        "away_team": away,
        "start_time": start_time,
        "pitchers": pitchers,
        "odds": odds
    })

# 4. Save to file
with open("data/live_feed.json", "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)
