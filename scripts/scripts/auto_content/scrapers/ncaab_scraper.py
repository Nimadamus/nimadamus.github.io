"""
NCAAB (College Basketball) Data Scraper
Fetches college basketball games, stats, and standings from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class NCAABScraper(BaseScraper):
    """Scraper for NCAAB data."""

    def __init__(self):
        super().__init__("basketball", "mens-college-basketball")

    def get_full_game_data(self, date: str = None, limit: int = 15) -> List[GameData]:
        """Get comprehensive data for games on a date.

        Args:
            date: Date in YYYYMMDD format
            limit: Maximum number of games to return (college has many games)
        """
        games = self.get_todays_games(date)

        # Filter to most relevant games (ranked teams, conference games)
        prioritized = self._prioritize_games(games)
        games_to_process = prioritized[:limit]

        full_data = []
        for game in games_to_process:
            game_data = GameData(game)
            full_data.append(game_data)

        return full_data

    def _prioritize_games(self, games: List[Dict]) -> List[Dict]:
        """Prioritize games by importance (ranked matchups, conference games)."""

        def game_score(game):
            score = 0
            home = game.get('home_team', {})
            away = game.get('away_team', {})
            name = game.get('name', '').lower()

            # Ranked teams get priority
            if 'rank' in str(home) or '#' in home.get('name', ''):
                score += 10
            if 'rank' in str(away) or '#' in away.get('name', ''):
                score += 10

            # Conference games
            if 'conference' in name:
                score += 5

            # Tournament games
            if 'tournament' in name or 'ncaa' in name:
                score += 20

            return score

        return sorted(games, key=game_score, reverse=True)

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """NCAAB-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            name = event.get('name', '').lower()

            # Tournament detection
            if 'ncaa tournament' in name or 'march madness' in name:
                game['is_tournament'] = True
                game['game_type'] = 'NCAA Tournament'
            elif 'nit' in name:
                game['is_tournament'] = True
                game['game_type'] = 'NIT'
            elif 'conference' in name and 'tournament' in name:
                game['is_tournament'] = True
                game['game_type'] = 'Conference Tournament'
            else:
                game['is_tournament'] = False
                game['game_type'] = 'Regular Season'

        return game

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        # Parse records
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

        home_parsed = parse_record(home.get('record', '0-0'))
        away_parsed = parse_record(away.get('record', '0-0'))

        return {
            'matchup': f"{away.get('name')} @ {home.get('name')}",
            'short_matchup': f"{away.get('abbreviation')} @ {home.get('abbreviation')}",
            'game_time': game.get('date', ''),
            'venue': game.get('venue', ''),
            'broadcast': game.get('broadcast', ''),
            'game_type': game.get('game_type', 'Regular Season'),
            'home': {
                'name': home.get('name'),
                'abbrev': home.get('abbreviation'),
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'win_pct': home_parsed['win_pct'],
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'win_pct': away_parsed['win_pct'],
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),
                'total': game_data.odds.get('over_under', ''),
            },
            'is_tournament': game.get('is_tournament', False),
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = NCAABScraper()
    print(f"Fetching NCAAB games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} prioritized games\n")

    for game_data in games[:10]:  # Show top 10
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"{formatted['game_type']}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']})")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']})")
        print(f"Spread: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print()
