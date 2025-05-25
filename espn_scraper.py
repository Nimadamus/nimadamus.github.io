import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

def scrape_espn_matchups():
    url = "https://www.espn.com/mlb/schedule"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch ESPN page. Status code: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table", class_="schedule")

    matchups = []
    today = datetime.now().strftime("%Y-%m-%d")

    for table in tables:
        rows = table.find_all("tr")[1:]  # skip header
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 2:
                teams = cols[0].text.strip().split(" at ")
                if len(teams) == 2:
                    away, home = teams
                    matchups.append({
                        "Away Team": away,
                        "Home Team": home,
                        "Odds": "N/A",
                        "Date": today
                    })

    return pd.DataFrame(matchups)

if __name__ == "__main__":
    df = scrape_espn_matchups()
    print(df)
