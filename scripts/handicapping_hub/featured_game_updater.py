"""
FEATURED GAME UPDATER
=====================
Automatically updates the index.html featured game section with
the best game of the day and real injury data from ESPN.
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from handicapping_hub.injury_scraper import InjuryScraper, COLLEGE_TEAM_IDS


class FeaturedGameUpdater:
    """Updates the index.html featured game section"""

    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.index_path = os.path.join(self.repo_path, 'index.html')
        self.injury_scraper = InjuryScraper()

        # Priority sports/games for featuring (in order)
        self.priority_events = [
            # Championship games
            ('NCAAF', 'SEC Championship'),
            ('NCAAF', 'Big Ten Championship'),
            ('NCAAF', 'ACC Championship'),
            ('NCAAF', 'Big 12 Championship'),
            ('NCAAF', 'CFP'),
            ('NCAAF', 'Playoff'),
            # NFL primetime
            ('NFL', 'Monday Night'),
            ('NFL', 'Sunday Night'),
            ('NFL', 'Thursday Night'),
            # NBA marquee
            ('NBA', 'Lakers'),
            ('NBA', 'Celtics'),
            ('NBA', 'Warriors'),
            # NHL marquee
            ('NHL', 'Rangers'),
            ('NHL', 'Maple Leafs'),
            ('NHL', 'Bruins'),
        ]

    def select_featured_game(self, all_data: Dict) -> Optional[Dict]:
        """
        Select the best featured game from all sports data.
        Returns game info dict with sport, teams, and metadata.
        """
        # Priority 1: Check for championship/bowl games in NCAAF
        ncaaf_games = all_data.get('NCAAF', {}).get('games', [])

        # Known championship matchups - priority order (higher = checked first)
        # P5 championships come before G5 championships
        championship_matchups = [
            # Power 5 (highest priority)
            ('Georgia', 'Alabama', 'SEC Championship'),
            ('Oregon', 'Penn State', 'Big Ten Championship'),
            ('Ohio State', 'Oregon', 'Big Ten Championship'),
            ('Indiana', 'Oregon', 'Big Ten Championship'),
            ('Texas', 'Georgia', 'SEC Championship'),
            ('Clemson', 'SMU', 'ACC Championship'),
            ('Arizona State', 'Iowa State', 'Big 12 Championship'),
            ('BYU', 'Colorado', 'Big 12 Championship'),
            # Group of 5 (lower priority)
            ('Boise State', 'UNLV', 'Mountain West Championship'),
            ('Army', 'Tulane', 'AAC Championship'),
        ]

        # Check known championship matchups in priority order
        for team1, team2, champ_name in championship_matchups:
            for game in ncaaf_games:
                game_info = game.get('game', {})
                away = game_info.get('away', {})
                home = game_info.get('home', {})
                away_name = away.get('displayName', away.get('name', ''))
                home_name = home.get('displayName', home.get('name', ''))

                if ((team1.lower() in away_name.lower() or team1.lower() in home_name.lower()) and
                    (team2.lower() in away_name.lower() or team2.lower() in home_name.lower())):
                    return {
                        'sport': 'NCAAF',
                        'game': game,
                        'away': away,
                        'home': home,
                        'venue': game_info.get('venue', ''),
                        'notes': champ_name
                    }

        # Check for championship games by keywords
        for game in ncaaf_games:
            game_info = game.get('game', {})
            away = game_info.get('away', {})
            home = game_info.get('home', {})
            notes = game_info.get('notes', '') or ''
            name = game_info.get('name', '') or ''

            for keyword in ['Championship', 'CFP', 'Playoff', 'Bowl']:
                if keyword.lower() in notes.lower() or keyword.lower() in name.lower():
                    return {
                        'sport': 'NCAAF',
                        'game': game,
                        'away': away,
                        'home': home,
                        'venue': game_info.get('venue', ''),
                        'notes': notes or name
                    }

        # Priority 2: NFL primetime games
        nfl_games = all_data.get('NFL', {}).get('games', [])
        for game in nfl_games:
            game_info = game.get('game', {})
            notes = game_info.get('notes', '') or ''

            for keyword in ['Monday Night', 'Sunday Night', 'Thursday Night', 'Prime', 'Thanksgiving']:
                if keyword.lower() in notes.lower():
                    return {
                        'sport': 'NFL',
                        'game': game,
                        'away': game_info.get('away', {}),
                        'home': game_info.get('home', {}),
                        'venue': game_info.get('venue', ''),
                        'notes': notes
                    }

        # Priority 3: Marquee NBA matchups
        nba_games = all_data.get('NBA', {}).get('games', [])
        marquee_teams = ['Lakers', 'Celtics', 'Warriors', 'Nuggets', 'Thunder', 'Bucks', '76ers']
        for game in nba_games:
            game_info = game.get('game', {})
            away = game_info.get('away', {})
            home = game_info.get('home', {})
            away_name = away.get('displayName', away.get('name', ''))
            home_name = home.get('displayName', home.get('name', ''))

            # Check if both teams are marquee
            away_marquee = any(m in away_name for m in marquee_teams)
            home_marquee = any(m in home_name for m in marquee_teams)

            if away_marquee and home_marquee:
                return {
                    'sport': 'NBA',
                    'game': game,
                    'away': away,
                    'home': home,
                    'venue': game_info.get('venue', ''),
                    'notes': ''
                }

        # Priority 4: Any NBA game with a marquee team
        for game in nba_games:
            game_info = game.get('game', {})
            away = game_info.get('away', {})
            home = game_info.get('home', {})
            away_name = away.get('displayName', away.get('name', ''))
            home_name = home.get('displayName', home.get('name', ''))

            if any(m in away_name or m in home_name for m in marquee_teams):
                return {
                    'sport': 'NBA',
                    'game': game,
                    'away': away,
                    'home': home,
                    'venue': game_info.get('venue', ''),
                    'notes': ''
                }

        # Priority 5: Any NFL game
        if nfl_games:
            game = nfl_games[0]
            game_info = game.get('game', {})
            return {
                'sport': 'NFL',
                'game': game,
                'away': game_info.get('away', {}),
                'home': game_info.get('home', {}),
                'venue': game_info.get('venue', ''),
                'notes': game_info.get('notes', '')
            }

        # Priority 6: Any NHL game
        nhl_games = all_data.get('NHL', {}).get('games', [])
        if nhl_games:
            game = nhl_games[0]
            game_info = game.get('game', {})
            return {
                'sport': 'NHL',
                'game': game,
                'away': game_info.get('away', {}),
                'home': game_info.get('home', {}),
                'venue': game_info.get('venue', ''),
                'notes': ''
            }

        # Priority 7: Any NBA game
        if nba_games:
            game = nba_games[0]
            game_info = game.get('game', {})
            return {
                'sport': 'NBA',
                'game': game,
                'away': game_info.get('away', {}),
                'home': game_info.get('home', {}),
                'venue': game_info.get('venue', ''),
                'notes': ''
            }

        return None

    def get_team_injuries(self, sport: str, team_name: str) -> List[Dict]:
        """Get injuries for a specific team"""
        if sport in ['NCAAF', 'NCAAB']:
            # For college, try to find team ID
            for full_name, team_id in COLLEGE_TEAM_IDS.items():
                if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                    sport_type = 'football' if sport == 'NCAAF' else 'basketball'
                    return self.injury_scraper.get_college_team_injuries(team_id, sport_type)
            return []
        else:
            return self.injury_scraper.get_team_injuries(sport, team_name)

    def format_injury_html(self, away_injuries: List[Dict], home_injuries: List[Dict],
                          away_abbrev: str, home_abbrev: str) -> str:
        """Format injuries as HTML for the index page"""

        def format_team_injuries(injuries: List[Dict], abbrev: str) -> str:
            if not injuries:
                return f"<strong>{abbrev}:</strong> No key injuries reported"

            # Categorize injuries by status
            out_players = [i for i in injuries if 'out' in i.get('status', '').lower()]
            doubtful = [i for i in injuries if 'doubtful' in i.get('status', '').lower()]
            questionable = [i for i in injuries if 'questionable' in i.get('status', '').lower()]
            day_to_day = [i for i in injuries if 'day-to-day' in i.get('status', '').lower() or 'dtd' in i.get('status', '').lower()]

            # If no categorized injuries, show first few from list with their status
            all_categorized = out_players + doubtful + questionable + day_to_day
            if not all_categorized and injuries:
                # Show raw injury data
                injury_names = []
                for p in injuries[:4]:
                    name = p.get('player', p.get('name', ''))
                    pos = p.get('position', '')
                    status = p.get('status', '')
                    if name:
                        if pos:
                            injury_names.append(f"{name} ({pos})")
                        else:
                            injury_names.append(name)
                if injury_names:
                    return f"<strong>{abbrev}:</strong> {', '.join(injury_names)}"
                return f"<strong>{abbrev}:</strong> No key injuries reported"

            parts = []

            # OUT players
            if out_players:
                out_names = []
                for p in out_players[:4]:
                    name = p.get('player', p.get('name', ''))
                    pos = p.get('position', '')
                    if pos:
                        out_names.append(f"{name} ({pos})")
                    else:
                        out_names.append(name)
                parts.append(f"<strong>{abbrev} OUT:</strong> {', '.join(out_names)}")

            # Doubtful players
            if doubtful and len(parts) == 0:
                d_names = []
                for p in doubtful[:2]:
                    name = p.get('player', p.get('name', ''))
                    pos = p.get('position', '')
                    if pos:
                        d_names.append(f"{name} ({pos})")
                    else:
                        d_names.append(name)
                parts.append(f"<strong>{abbrev} D:</strong> {', '.join(d_names)}")

            # Questionable players
            if questionable and len(out_players) < 3:
                q_names = []
                for p in questionable[:2]:
                    name = p.get('player', p.get('name', ''))
                    pos = p.get('position', '')
                    if pos:
                        q_names.append(f"{name} ({pos})")
                    else:
                        q_names.append(name)
                if parts:
                    parts.append(f"<strong>Q:</strong> {', '.join(q_names)}")
                else:
                    parts.append(f"<strong>{abbrev} Q:</strong> {', '.join(q_names)}")

            return ' | '.join(parts) if parts else f"<strong>{abbrev}:</strong> No key injuries reported"

        away_html = format_team_injuries(away_injuries, away_abbrev)
        home_html = format_team_injuries(home_injuries, home_abbrev)

        return f'''<div class="injury-alert">
                    <h4>Key Injuries</h4>
                    <div class="injury-item">{away_html}</div>
                    <div class="injury-item">{home_html}</div>
                </div>'''

    def update_index(self, featured: Dict, away_injuries: List[Dict], home_injuries: List[Dict]) -> bool:
        """Update the index.html with the new featured game and injuries"""
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                content = f.read()

            away = featured['away']
            home = featured['home']
            sport = featured['sport']

            away_name = away.get('displayName', away.get('name', 'Away Team'))
            home_name = home.get('displayName', home.get('name', 'Home Team'))
            away_abbrev = away.get('abbreviation', away_name[:3].upper())
            home_abbrev = home.get('abbreviation', home_name[:3].upper())
            venue = featured.get('venue', '')
            notes = featured.get('notes', '')

            # Generate injury HTML
            injury_html = self.format_injury_html(away_injuries, home_injuries, away_abbrev, home_abbrev)

            # Find and replace the injury-alert section
            injury_pattern = r'<div class="injury-alert">.*?</div>\s*</div>'
            new_injury_section = f'''{injury_html}

            </div>'''

            content = re.sub(injury_pattern, new_injury_section, content, flags=re.DOTALL)

            # Save updated content
            with open(self.index_path, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"[FEATURED GAME] Updated index.html with {away_name} @ {home_name}")
            print(f"  Away injuries: {len(away_injuries)} players")
            print(f"  Home injuries: {len(home_injuries)} players")

            return True

        except Exception as e:
            print(f"[ERROR] Failed to update index.html: {e}")
            return False

    def run(self, all_data: Dict) -> bool:
        """
        Main entry point - select featured game, fetch injuries, update index.
        """
        print("\n[FEATURED GAME UPDATER]")

        # Select featured game
        featured = self.select_featured_game(all_data)
        if not featured:
            print("  No suitable featured game found")
            return False

        away = featured['away']
        home = featured['home']
        sport = featured['sport']

        away_name = away.get('displayName', away.get('name', ''))
        home_name = home.get('displayName', home.get('name', ''))

        print(f"  Selected: {away_name} @ {home_name} ({sport})")

        # Fetch injuries
        print(f"  Fetching injuries for {away_name}...")
        away_injuries = self.get_team_injuries(sport, away_name)

        print(f"  Fetching injuries for {home_name}...")
        home_injuries = self.get_team_injuries(sport, home_name)

        # Update index
        return self.update_index(featured, away_injuries, home_injuries)


def update_featured_game(all_data: Dict) -> bool:
    """Convenience function to update featured game"""
    updater = FeaturedGameUpdater()
    return updater.run(all_data)
