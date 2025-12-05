"""
INJURY SCRAPER MODULE
=====================
Scrapes injury data from ESPN for all major sports.
Returns structured injury data for each team.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re

class InjuryScraper:
    """Scrape injury data from ESPN"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # ESPN injury page URLs by sport
        self.injury_urls = {
            'NBA': 'https://www.espn.com/nba/injuries',
            'NHL': 'https://www.espn.com/nhl/injuries',
            'NFL': 'https://www.espn.com/nfl/injuries',
            'MLB': 'https://www.espn.com/mlb/injuries',
            'NCAAF': None,  # College doesn't have central injury page - use team pages
            'NCAAB': None,
        }

        # Team name mappings for normalization
        self.team_aliases = {
            # NBA
            'LA Clippers': 'Los Angeles Clippers',
            'LA Lakers': 'Los Angeles Lakers',
            # NFL
            'NY Giants': 'New York Giants',
            'NY Jets': 'New York Jets',
            'LA Rams': 'Los Angeles Rams',
            'LA Chargers': 'Los Angeles Chargers',
        }

    def get_all_injuries(self, sport: str) -> Dict[str, List[Dict]]:
        """Get all injuries for a sport, keyed by team name"""
        url = self.injury_urls.get(sport)
        if not url:
            # For college sports, return empty - we'll handle per-team
            return {}

        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"    [WARN] Could not fetch {sport} injuries: HTTP {response.status_code}")
                return {}

            soup = BeautifulSoup(response.text, 'html.parser')
            injuries_by_team = {}

            # ESPN injury pages have team sections
            team_sections = soup.find_all('div', class_='ResponsiveTable')

            for section in team_sections:
                # Get team name from header
                header = section.find_previous('div', class_='Table__Title')
                if not header:
                    continue

                team_name = header.get_text(strip=True)
                team_name = self.team_aliases.get(team_name, team_name)

                injuries = []
                rows = section.find_all('tr', class_='Table__TR')

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        player_cell = cells[0]
                        player_link = player_cell.find('a')
                        player_name = player_link.get_text(strip=True) if player_link else player_cell.get_text(strip=True)

                        # Get position if available
                        pos_span = player_cell.find('span', class_='playerPosition')
                        position = pos_span.get_text(strip=True) if pos_span else ''

                        # Status and injury type
                        status = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                        injury_type = cells[2].get_text(strip=True) if len(cells) > 2 else ''

                        if player_name and status:
                            injuries.append({
                                'player': player_name,
                                'position': position,
                                'status': status,
                                'injury': injury_type
                            })

                if injuries:
                    injuries_by_team[team_name] = injuries

            return injuries_by_team

        except Exception as e:
            print(f"    [ERROR] Injury scrape failed for {sport}: {e}")
            return {}

    def get_team_injuries(self, sport: str, team_name: str) -> List[Dict]:
        """Get injuries for a specific team"""
        all_injuries = self.get_all_injuries(sport)

        # Try exact match first
        if team_name in all_injuries:
            return all_injuries[team_name]

        # Try partial match
        team_lower = team_name.lower()
        for key, injuries in all_injuries.items():
            if team_lower in key.lower() or key.lower() in team_lower:
                return injuries

        return []

    def get_college_team_injuries(self, team_id: str, sport: str = 'football') -> List[Dict]:
        """Get injuries for a college team by ESPN team ID"""
        sport_path = 'college-football' if sport == 'football' else 'mens-college-basketball'
        url = f'https://www.espn.com/{sport_path}/team/injuries/_/id/{team_id}'

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code != 200:
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
            injuries = []

            # Find injury table
            rows = soup.find_all('tr', class_='Table__TR')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    player_cell = cells[0]
                    player_link = player_cell.find('a')
                    player_name = player_link.get_text(strip=True) if player_link else ''

                    if not player_name:
                        continue

                    # Get position
                    pos_span = player_cell.find('span')
                    position = pos_span.get_text(strip=True) if pos_span else ''

                    # Get status
                    status = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                    injury_type = cells[2].get_text(strip=True) if len(cells) > 2 else ''

                    if player_name and status:
                        injuries.append({
                            'player': player_name,
                            'position': position,
                            'status': status,
                            'injury': injury_type
                        })

            return injuries

        except Exception as e:
            return []

    def format_injuries_html(self, injuries: List[Dict], max_display: int = 5) -> str:
        """Format injuries as HTML for display"""
        if not injuries:
            return '<span class="no-injuries">No injuries reported</span>'

        # Group by status
        out_players = [i for i in injuries if 'out' in i['status'].lower()]
        questionable = [i for i in injuries if 'questionable' in i['status'].lower() or 'doubtful' in i['status'].lower()]

        html_parts = []

        # Show OUT players first (most important)
        for inj in out_players[:max_display]:
            pos = f" ({inj['position']})" if inj['position'] else ""
            injury_note = f" - {inj['injury']}" if inj['injury'] else ""
            html_parts.append(f'<span class="injury-out">{inj["player"]}{pos}{injury_note} [OUT]</span>')

        # Then questionable
        remaining_slots = max_display - len(html_parts)
        for inj in questionable[:remaining_slots]:
            pos = f" ({inj['position']})" if inj['position'] else ""
            html_parts.append(f'<span class="injury-questionable">{inj["player"]}{pos} [Q]</span>')

        if not html_parts:
            return '<span class="no-injuries">No key injuries</span>'

        return '<br>'.join(html_parts)

    def format_injuries_short(self, injuries: List[Dict], max_display: int = 4) -> str:
        """Format injuries as short text for compact display"""
        if not injuries:
            return 'No key injuries'

        out_players = [i for i in injuries if 'out' in i['status'].lower()]
        questionable = [i for i in injuries if 'questionable' in i['status'].lower()]

        parts = []

        # OUT players
        out_names = [f"{i['player']} ({i['position']})" if i['position'] else i['player']
                     for i in out_players[:max_display]]
        if out_names:
            parts.append(f"OUT: {', '.join(out_names)}")

        # Questionable
        remaining = max_display - len(out_names)
        if remaining > 0 and questionable:
            q_names = [f"{i['player']} ({i['position']})" if i['position'] else i['player']
                       for i in questionable[:remaining]]
            parts.append(f"Q: {', '.join(q_names)}")

        return ' | '.join(parts) if parts else 'No key injuries'


# College football team IDs for major programs
COLLEGE_TEAM_IDS = {
    # SEC
    'Georgia Bulldogs': '61',
    'Alabama Crimson Tide': '333',
    'Florida Gators': '57',
    'LSU Tigers': '99',
    'Texas A&M Aggies': '245',
    'Tennessee Volunteers': '2633',
    'Ole Miss Rebels': '145',
    'Auburn Tigers': '2',
    'Missouri Tigers': '142',
    'Kentucky Wildcats': '96',
    'South Carolina Gamecocks': '2579',
    'Arkansas Razorbacks': '8',
    'Mississippi State Bulldogs': '344',
    'Vanderbilt Commodores': '238',
    'Texas Longhorns': '251',
    'Oklahoma Sooners': '201',

    # Big Ten
    'Ohio State Buckeyes': '194',
    'Michigan Wolverines': '130',
    'Penn State Nittany Lions': '213',
    'Oregon Ducks': '2483',
    'Indiana Hoosiers': '84',
    'Iowa Hawkeyes': '2294',
    'Wisconsin Badgers': '275',
    'Minnesota Golden Gophers': '135',
    'Illinois Fighting Illini': '356',
    'Northwestern Wildcats': '77',
    'Nebraska Cornhuskers': '158',
    'Purdue Boilermakers': '2509',
    'Michigan State Spartans': '127',
    'Rutgers Scarlet Knights': '164',
    'Maryland Terrapins': '120',
    'UCLA Bruins': '26',
    'USC Trojans': '30',
    'Washington Huskies': '264',

    # Big 12
    'Utah Utes': '254',
    'BYU Cougars': '252',
    'Colorado Buffaloes': '38',
    'Arizona Wildcats': '12',
    'Arizona State Sun Devils': '9',
    'Kansas State Wildcats': '2306',
    'Iowa State Cyclones': '66',
    'West Virginia Mountaineers': '277',
    'TCU Horned Frogs': '2628',
    'Texas Tech Red Raiders': '2641',
    'Baylor Bears': '239',
    'Kansas Jayhawks': '2305',
    'Oklahoma State Cowboys': '197',
    'Cincinnati Bearcats': '2132',
    'UCF Knights': '2116',
    'Houston Cougars': '248',

    # ACC
    'Clemson Tigers': '228',
    'Florida State Seminoles': '52',
    'Miami Hurricanes': '2390',
    'North Carolina Tar Heels': '153',
    'NC State Wolfpack': '152',
    'Duke Blue Devils': '150',
    'Virginia Tech Hokies': '259',
    'Virginia Cavaliers': '258',
    'Pittsburgh Panthers': '221',
    'Louisville Cardinals': '97',
    'Syracuse Orange': '183',
    'Boston College Eagles': '103',
    'Wake Forest Demon Deacons': '154',
    'Georgia Tech Yellow Jackets': '59',
    'SMU Mustangs': '2567',
    'Stanford Cardinal': '24',
    'California Golden Bears': '25',

    # Mountain West
    'Boise State Broncos': '68',
    'UNLV Rebels': '2439',
    'Colorado State Rams': '36',
    'Fresno State Bulldogs': '278',
    'San Diego State Aztecs': '21',
    'Air Force Falcons': '2005',

    # Other
    'Notre Dame Fighting Irish': '87',
    'Army Black Knights': '349',
    'Navy Midshipmen': '2426',
}


def get_injury_scraper():
    """Get singleton instance of injury scraper"""
    return InjuryScraper()
