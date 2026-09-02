"""
NFL Data Scraper
Fetches NFL games, stats, standings, and injuries from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class NFLScraper(BaseScraper):
    """Scraper for NFL data."""

    def __init__(self):
        super().__init__("football", "nfl")

    def get_full_game_data(self, date: str = None) -> List[GameData]:
        """Get comprehensive data for all games on a date."""
        games = self.get_todays_games(date)
        full_data = []

        for game in games:
            game_data = GameData(game)

            # Get team forms (last 5 games for NFL)
            home_id = game['home_team'].get('id')
            away_id = game['away_team'].get('id')

            if home_id:
                game_data.home_form = self.get_recent_form(home_id, 5)
            if away_id:
                game_data.away_form = self.get_recent_form(away_id, 5)

            full_data.append(game_data)

        return full_data

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """NFL-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            # Add NFL-specific fields
            name = event.get('name', '')

            # Game type detection
            if 'Playoff' in name or 'Wild Card' in name or 'Divisional' in name:
                game['is_playoff'] = True
                game['game_type'] = 'Playoff'
            elif 'Conference' in name or 'NFC' in name or 'AFC' in name:
                game['is_playoff'] = True
                game['game_type'] = 'Conference Championship'
            elif 'Super Bowl' in name:
                game['is_playoff'] = True
                game['game_type'] = 'Super Bowl'
            else:
                game['is_playoff'] = False
                game['game_type'] = 'Regular Season'

            # Week number (if available)
            game['week'] = event.get('week', {}).get('number', '')

        return game

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        # Parse NFL records (W-L or W-L-T format)
        def parse_nfl_record(record_str):
            try:
                parts = record_str.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                ties = int(parts[2]) if len(parts) > 2 else 0
                total = wins + losses + ties
                win_pct = ((wins + 0.5 * ties) / total * 100) if total > 0 else 0
                return {
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'win_pct': win_pct
                }
            except:
                return {'wins': 0, 'losses': 0, 'ties': 0, 'win_pct': 0}

        home_parsed = parse_nfl_record(home.get('record', '0-0'))
        away_parsed = parse_nfl_record(away.get('record', '0-0'))

        return {
            'matchup': f"{away.get('name')} @ {home.get('name')}",
            'short_matchup': f"{away.get('abbreviation')} @ {home.get('abbreviation')}",
            'game_time': game.get('date', ''),
            'venue': game.get('venue', ''),
            'broadcast': game.get('broadcast', ''),
            'week': game.get('week', ''),
            'game_type': game.get('game_type', 'Regular Season'),
            'home': {
                'name': home.get('name'),
                'abbrev': home.get('abbreviation'),
                'id': home.get('id', ''),  # Team ID
                'logo': home.get('logo', ''),  # Direct logo URL from ESPN
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'ties': home_parsed['ties'],
                'win_pct': home_parsed['win_pct'],
                'l5': game_data.home_form.get('record', ''),
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'ties': away_parsed['ties'],
                'win_pct': away_parsed['win_pct'],
                'l5': game_data.away_form.get('record', ''),
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),
                'total': game_data.odds.get('over_under', ''),
            },
            'is_playoff': game.get('is_playoff', False),
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = NFLScraper()
    print(f"Fetching NFL games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} games\n")

    for game_data in games:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"Week {formatted['week']} - {formatted['game_type']}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']}) L5: {formatted['home']['l5']}")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']}) L5: {formatted['away']['l5']}")
        print(f"Spread: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print(f"Venue: {formatted['venue']}")
        print()
