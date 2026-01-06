"""
NBA Data Scraper
Fetches NBA games, stats, standings, and injuries from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class NBAScraper(BaseScraper):
    """Scraper for NBA data."""

    def __init__(self):
        super().__init__("basketball", "nba")

    def get_full_game_data(self, date: str = None) -> List[GameData]:
        """Get comprehensive data for all games on a date."""
        games = self.get_todays_games(date)
        full_data = []

        for game in games:
            game_data = GameData(game)

            # Get team forms (last 10 games)
            home_id = game['home_team'].get('id')
            away_id = game['away_team'].get('id')

            if home_id:
                game_data.home_form = self.get_recent_form(home_id, 10)
            if away_id:
                game_data.away_form = self.get_recent_form(away_id, 10)

            full_data.append(game_data)

        return full_data

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """NBA-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            # Add NBA-specific fields
            competitions = event.get('competitions', [{}])[0]

            # Check for playoff/tournament games
            if 'Playoff' in event.get('name', '') or 'Finals' in event.get('name', ''):
                game['is_playoff'] = True
                game['series'] = event.get('series', {})
            else:
                game['is_playoff'] = False

            # In-Season Tournament check
            if 'Tournament' in event.get('name', '') or 'Cup' in event.get('name', ''):
                game['is_tournament'] = True
            else:
                game['is_tournament'] = False

        return game

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        # Parse records for wins/losses
        home_record = home.get('record', '0-0')
        away_record = away.get('record', '0-0')

        # Calculate win percentages from records
        def parse_record(record_str):
            try:
                parts = record_str.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                total = wins + losses
                win_pct = (wins / total * 100) if total > 0 else 0
                return {'wins': wins, 'losses': losses, 'win_pct': win_pct}
            except:
                return {'wins': 0, 'losses': 0, 'win_pct': 0}

        home_parsed = parse_record(home_record)
        away_parsed = parse_record(away_record)

        return {
            'matchup': f"{away.get('name')} @ {home.get('name')}",
            'short_matchup': f"{away.get('abbreviation')} @ {home.get('abbreviation')}",
            'game_time': game.get('date', ''),
            'venue': game.get('venue', ''),
            'broadcast': game.get('broadcast', ''),
            'home': {
                'name': home.get('name'),
                'abbrev': home.get('abbreviation'),
                'id': home.get('id', ''),  # Team ID
                'logo': home.get('logo', ''),  # Direct logo URL from ESPN
                'record': home_record,
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'win_pct': home_parsed['win_pct'],
                'l10': game_data.home_form.get('record', ''),
                'streak': '',  # Would need additional API call
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away_record,
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'win_pct': away_parsed['win_pct'],
                'l10': game_data.away_form.get('record', ''),
                'streak': '',
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),
                'total': game_data.odds.get('over_under', ''),
            },
            'is_playoff': game.get('is_playoff', False),
            'is_tournament': game.get('is_tournament', False),
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = NBAScraper()
    print(f"Fetching NBA games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} games\n")

    for game_data in games:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']}) L10: {formatted['home']['l10']}")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']}) L10: {formatted['away']['l10']}")
        print(f"Spread: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print(f"Venue: {formatted['venue']}")
        print()
