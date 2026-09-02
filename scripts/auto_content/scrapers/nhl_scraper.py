"""
NHL Data Scraper
Fetches NHL games, stats, standings, and injuries from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class NHLScraper(BaseScraper):
    """Scraper for NHL data."""

    def __init__(self):
        super().__init__("hockey", "nhl")

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
        """NHL-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            # Add NHL-specific fields
            competitions = event.get('competitions', [{}])[0]

            # Check for playoff games
            if 'Playoff' in event.get('name', '') or 'Stanley Cup' in event.get('name', ''):
                game['is_playoff'] = True
                game['series'] = event.get('series', {})
            else:
                game['is_playoff'] = False

        return game

    def _parse_team(self, team_data: Dict) -> Dict:
        """NHL-specific team parsing with points and OT losses."""
        team = super()._parse_team(team_data)

        # NHL uses W-L-OTL format
        records = team_data.get('records', [])
        for rec in records:
            if rec.get('name') == 'overall' or rec.get('type') == 'total':
                # Try to parse W-L-OTL
                summary = rec.get('summary', '')
                team['record'] = summary
                break

        return team

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        # Parse NHL records (W-L-OTL format)
        def parse_nhl_record(record_str):
            try:
                parts = record_str.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                otl = int(parts[2]) if len(parts) > 2 else 0
                points = (wins * 2) + otl
                games = wins + losses + otl
                pts_pct = (points / (games * 2) * 100) if games > 0 else 0
                return {
                    'wins': wins,
                    'losses': losses,
                    'otl': otl,
                    'points': points,
                    'pts_pct': pts_pct
                }
            except:
                return {'wins': 0, 'losses': 0, 'otl': 0, 'points': 0, 'pts_pct': 0}

        home_parsed = parse_nhl_record(home.get('record', '0-0-0'))
        away_parsed = parse_nhl_record(away.get('record', '0-0-0'))

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
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'otl': home_parsed['otl'],
                'points': home_parsed['points'],
                'pts_pct': home_parsed['pts_pct'],
                'l10': game_data.home_form.get('record', ''),
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'otl': away_parsed['otl'],
                'points': away_parsed['points'],
                'pts_pct': away_parsed['pts_pct'],
                'l10': game_data.away_form.get('record', ''),
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
    scraper = NHLScraper()
    print(f"Fetching NHL games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} games\n")

    for game_data in games:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']}) {formatted['home']['points']} pts, L10: {formatted['home']['l10']}")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']}) {formatted['away']['points']} pts, L10: {formatted['away']['l10']}")
        print(f"Puck Line: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print(f"Venue: {formatted['venue']}")
        print()
