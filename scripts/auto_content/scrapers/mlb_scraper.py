"""
MLB Data Scraper
Fetches MLB games, stats, standings, and injuries from ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class MLBScraper(BaseScraper):
    """Scraper for MLB data."""

    def __init__(self):
        super().__init__("baseball", "mlb")

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
        """MLB-specific game parsing."""
        game = super()._parse_game(event)

        if game:
            name = event.get('name', '').lower()
            competitions = event.get('competitions', [{}])[0]

            # Playoff detection
            if 'playoff' in name or 'world series' in name or 'alcs' in name or 'nlcs' in name:
                game['is_playoff'] = True
                if 'world series' in name:
                    game['game_type'] = 'World Series'
                elif 'alcs' in name or 'nlcs' in name:
                    game['game_type'] = 'League Championship'
                elif 'wild card' in name:
                    game['game_type'] = 'Wild Card'
                else:
                    game['game_type'] = 'Division Series'
            else:
                game['is_playoff'] = False
                game['game_type'] = 'Regular Season'

            # Try to get probable pitchers
            game['probable_pitchers'] = self._get_probable_pitchers(competitions)

        return game

    def _get_probable_pitchers(self, competition: Dict) -> Dict:
        """Extract probable pitchers if available."""
        pitchers = {'home': '', 'away': ''}

        # ESPN sometimes includes this in different places
        for competitor in competition.get('competitors', []):
            probables = competitor.get('probables', [])
            for probable in probables:
                if probable.get('type', {}).get('abbreviation') == 'SP':
                    athlete = probable.get('athlete', {})
                    pitcher_name = athlete.get('displayName', '')
                    if competitor.get('homeAway') == 'home':
                        pitchers['home'] = pitcher_name
                    else:
                        pitchers['away'] = pitcher_name

        return pitchers

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        def parse_record(record_str):
            try:
                parts = record_str.split('-')
                wins = int(parts[0])
                losses = int(parts[1])
                total = wins + losses
                win_pct = (wins / total) if total > 0 else 0
                return {'wins': wins, 'losses': losses, 'win_pct': win_pct}
            except:
                return {'wins': 0, 'losses': 0, 'win_pct': 0}

        home_parsed = parse_record(home.get('record', '0-0'))
        away_parsed = parse_record(away.get('record', '0-0'))

        pitchers = game.get('probable_pitchers', {})

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
                'id': home.get('id', ''),  # Team ID
                'logo': home.get('logo', ''),  # Direct logo URL from ESPN
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'losses': home_parsed['losses'],
                'win_pct': home_parsed['win_pct'],
                'l10': game_data.home_form.get('record', ''),
                'probable_pitcher': pitchers.get('home', ''),
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'losses': away_parsed['losses'],
                'win_pct': away_parsed['win_pct'],
                'l10': game_data.away_form.get('record', ''),
                'probable_pitcher': pitchers.get('away', ''),
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),  # Run line in MLB
                'total': game_data.odds.get('over_under', ''),
            },
            'is_playoff': game.get('is_playoff', False),
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = MLBScraper()
    print(f"Fetching MLB games for today...")

    games = scraper.get_full_game_data()
    print(f"Found {len(games)} games\n")

    for game_data in games:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"{formatted['game_type']}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']}) L10: {formatted['home']['l10']}")
        if formatted['home']['probable_pitcher']:
            print(f"  SP: {formatted['home']['probable_pitcher']}")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']}) L10: {formatted['away']['l10']}")
        if formatted['away']['probable_pitcher']:
            print(f"  SP: {formatted['away']['probable_pitcher']}")
        print(f"Run Line: {formatted['odds']['spread']}")
        print(f"Total: {formatted['odds']['total']}")
        print()
