"""
Scrape injury reports from ESPN and update handicapping-hub.html
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

# ESPN Injury Report URLs
INJURY_URLS = {
    'NBA': 'https://www.espn.com/nba/injuries',
    'NFL': 'https://www.espn.com/nfl/injuries',
    'NHL': 'https://www.espn.com/nhl/injuries',
    'MLB': 'https://www.espn.com/mlb/injuries',
}

# Team name mappings (ESPN name -> our name)
TEAM_MAPPINGS = {
    # NBA
    'LA Clippers': 'LA Clippers',
    'Los Angeles Clippers': 'LA Clippers',
    'Los Angeles Lakers': 'LA Lakers',
    'LA Lakers': 'LA Lakers',
    # NHL
    'Utah Hockey Club': 'Utah Mammoth',
    'Montreal Canadiens': 'Montreal Canadiens',
    'Montréal Canadiens': 'Montreal Canadiens',
}

def get_injuries_from_espn(sport):
    """Scrape injury data from ESPN using their API"""

    # ESPN uses an API endpoint for injuries
    api_urls = {
        'NBA': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',
        'NFL': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries',
        'NHL': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries',
        'MLB': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/injuries',
    }

    url = api_urls.get(sport)
    if not url:
        return {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        injuries = {}

        # Parse the JSON response - structure is injuries[].displayName for team, injuries[].injuries[] for players
        for team_data in data.get('injuries', []):
            team_name = team_data.get('displayName', 'Unknown')
            team_name = TEAM_MAPPINGS.get(team_name, team_name)

            players = []
            for injury in team_data.get('injuries', []):
                athlete = injury.get('athlete', {})
                player_name = athlete.get('displayName', '')
                status = injury.get('status', 'Unknown')

                # Get injury description from shortComment
                short_comment = injury.get('shortComment', '')
                # Extract injury type from comment (e.g., "Johnson (calf) won't play..." -> "calf")
                injury_type = ''
                if '(' in short_comment and ')' in short_comment:
                    start = short_comment.find('(') + 1
                    end = short_comment.find(')')
                    injury_type = short_comment[start:end].title()

                if player_name:
                    players.append({
                        'name': player_name,
                        'position': '',
                        'status': status,
                        'injury': injury_type
                    })

            if players:
                injuries[team_name] = players

        print(f"  Parsed {len(injuries)} teams with injuries")
        return injuries

    except Exception as e:
        print(f"Error fetching {sport} injuries from API: {e}")
        return {}

def get_injuries_from_html(sport):
    """Fallback: scrape HTML if API fails"""
    url = INJURY_URLS.get(sport)
    if not url:
        return {}

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        injuries = {}
        current_team = None

        # Look for team headers and their associated injury tables
        for element in soup.find_all(['div', 'table', 'tr']):
            # Check for team name
            if 'TeamLink' in element.get('class', []) or element.find(class_='TeamLink'):
                team_link = element.find(class_='TeamLink') or element
                team_name = team_link.get_text(strip=True)
                team_name = TEAM_MAPPINGS.get(team_name, team_name)
                current_team = team_name
                if current_team not in injuries:
                    injuries[current_team] = []

            # Check for player injury rows
            if element.name == 'tr' and current_team:
                cols = element.find_all('td')
                if len(cols) >= 3:
                    player_name = cols[0].get_text(strip=True)
                    if player_name and player_name not in ['NAME', 'Player']:
                        status = cols[-2].get_text(strip=True) if len(cols) > 2 else ''
                        injury = cols[-1].get_text(strip=True) if len(cols) > 3 else ''
                        injuries[current_team].append({
                            'name': player_name,
                            'position': cols[1].get_text(strip=True) if len(cols) > 1 else '',
                            'status': status,
                            'injury': injury
                        })

        # Remove teams with no injuries
        injuries = {k: v for k, v in injuries.items() if v}
        return injuries

    except Exception as e:
        print(f"Error scraping {sport} injuries HTML: {e}")
        return {}

def format_injury_html(players):
    """Format injury list as HTML"""
    if not players:
        return '<span class="no-injuries">No injuries reported</span>'

    html_parts = []
    for player in players[:5]:  # Limit to 5 players
        status_class = 'injury-out' if 'Out' in player['status'] else 'injury-questionable' if 'Questionable' in player['status'] or 'Doubtful' in player['status'] else 'injury-probable'
        injury_text = f" ({player['injury']})" if player['injury'] else ""
        html_parts.append(f'<span class="{status_class}">{player["name"]} - {player["status"]}{injury_text}</span>')

    return '<br>'.join(html_parts)

def update_handicapping_hub(injuries_by_sport):
    """Update the handicapping-hub.html with real injury data"""

    filepath = r'C:\Users\Nima\nimadamus.github.io\handicapping-hub.html'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Combine all injuries
    all_injuries = {}
    for sport, injuries in injuries_by_sport.items():
        all_injuries.update(injuries)

    # Pattern to find injury sections and update them
    # Match: <h5>Team Name</h5>\n<span class="no-injuries">No injuries reported</span>

    for team_name, players in all_injuries.items():
        injury_html = format_injury_html(players)

        # Try different patterns to match
        patterns = [
            (rf'(<h5>{re.escape(team_name)}</h5>\s*)<span class="no-injuries">No injuries reported</span>',
             rf'\1{injury_html}'),
            (rf'(<h5>{re.escape(team_name)}</h5>\s*)<span class="injury[^"]*">[^<]+</span>(?:<br><span class="injury[^"]*">[^<]+</span>)*',
             rf'\1{injury_html}'),
        ]

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
            if new_content != content:
                content = new_content
                print(f"Updated injuries for: {team_name}")
                break

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\nHandicapping hub updated at {datetime.now()}")

def main():
    print("Fetching injury reports from ESPN...")
    print("=" * 50)

    all_injuries = {}

    for sport in ['NBA', 'NFL', 'NHL']:
        print(f"\nFetching {sport} injuries...")
        injuries = get_injuries_from_espn(sport)
        all_injuries[sport] = injuries
        print(f"  Found injuries for {len(injuries)} teams")

        for team, players in list(injuries.items())[:3]:
            print(f"    {team}: {len(players)} players")

    print("\n" + "=" * 50)
    print("Updating handicapping-hub.html...")
    update_handicapping_hub(all_injuries)

    # Save injuries to JSON for reference
    with open(r'C:\Users\Nima\nimadamus.github.io\injuries_data.json', 'w') as f:
        json.dump(all_injuries, f, indent=2)
    print("Injuries saved to injuries_data.json")

if __name__ == '__main__':
    main()
