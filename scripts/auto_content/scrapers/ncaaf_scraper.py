"""
NCAAF (College Football) Data Scraper
Fetches college football games, stats, and standings from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class NCAAFScraper(BaseScraper):
    """Scraper for NCAAF data."""

    def __init__(self):
        super().__init__("football", "college-football")

    def get_full_game_data(self, date: str = None, limit: int = 15) -> List[GameData]:
        """Get comprehensive data for games on a date."""
        games = self.get_todays_games(date)

        # Filter to most relevant games
        prioritized = self._prioritize_games(games)
        games_to_process = prioritized[:limit]

        full_data = []
        for game in games_to_process:
            game_data = GameData(game)
            full_data.append(game_data)

        return full_data

    def _prioritize_games(self, games: List[Dict]) -> List[Dict]:
        """Prioritize games by importance (ranked, bowl games, conference championships)."""

        def game_score(game):
            score = 0
            home = game.get('home_team', {})
            away = game.get('away_team', {})
            name = game.get('name', '').lower()

            # Bowl games get highest priority
            if 'bowl' in name:
                score += 25

            # Playoff games
            if 'playoff' in name or 'championship' in name:
                score += 30

            # Ranked teams
            if '#' in home.get('name', '') or 'rank' in str(home):
                score += 10
            if '#' in away.get('name', '') or 'rank' in str(away):
                score += 10

            # Conference games
            if any(conf in name for conf in ['sec', 'big ten', 'big 12', 'acc', 'pac']):
                score += 5

            return score

        return sorted(games, key=game_score, reverse=True)

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """NCAAF-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            name = event.get('name', '').lower()

            # Game type detection
            if 'bowl' in name:
                game['is_bowl'] = True
                game['game_type'] = 'Bowl Game'
            elif 'playoff' in name:
                game['is_bowl'] = True
                game['game_type'] = 'CFP Playoff'
            elif 'championship' in name:
                game['is_bowl'] = True
                game['game_type'] = 'Championship'
            else:
                game['is_bowl'] = False
                game['game_type'] = 'Regular Season'

            # Week number
            game['week'] = event.get('week', {}).get('number', '')

        return game

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        def parse_record(record_str):
            try:
                # Handle conference records like "8-2 (5-1)"
                main_record = record_str.split('(')[0].strip()
                parts = main_record.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                total = wins + losses
                win_pct = (wins / total * 100) if total > 0 else 0
                return {'wins': wins, 'losses': losses, 'win_pct': win_pct}
            except:
                return {'wins': 0, 'losses': 0, 'win_pct': 0}

        home_parsed = parse_record(home.get('record', '0-0'))
        away_parsed = parse_record(away.get('record', '0-0'))

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
                'id': home.get('id', ''),  # Team ID for NCAA logo URLs
                'logo': home.get('logo', ''),  # Direct logo URL from ESPN
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'win_pct': home_parsed['win_pct'],
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID for NCAA logo URLs
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'win_pct': away_parsed['win_pct'],
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),
                'total': game_data.odds.get('over_under', ''),
            },
            'is_bowl': game.get('is_bowl', False),
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = NCAAFScraper()
    print(f"Fetching NCAAF games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} prioritized games\n")

    for game_data in games[:10]:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"Week {formatted['week']} - {formatted['game_type']}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']})")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']})")
        print(f"Spread: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print()
