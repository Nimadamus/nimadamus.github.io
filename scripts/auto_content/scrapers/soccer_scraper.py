"""
Soccer Data Scraper
Fetches soccer games from multiple leagues via ESPN
"""

from typing import Dict, List, Optional
from datetime import datetime
from .base_scraper import BaseScraper, GameData


class SoccerScraper(BaseScraper):
    """Scraper for Soccer data across multiple leagues."""

    # Major leagues to track
    LEAGUES = {
        'eng.1': {'name': 'Premier League', 'country': 'England'},
        'esp.1': {'name': 'La Liga', 'country': 'Spain'},
        'ger.1': {'name': 'Bundesliga', 'country': 'Germany'},
        'ita.1': {'name': 'Serie A', 'country': 'Italy'},
        'fra.1': {'name': 'Ligue 1', 'country': 'France'},
        'usa.1': {'name': 'MLS', 'country': 'USA'},
        'mex.1': {'name': 'Liga MX', 'country': 'Mexico'},
        'uefa.champions': {'name': 'Champions League', 'country': 'Europe'},
        'uefa.europa': {'name': 'Europa League', 'country': 'Europe'},
    }

    def __init__(self):
        super().__init__("soccer", "eng.1")  # Default to Premier League
        self.all_leagues_data = {}

    def get_full_game_data(self, date: str = None, leagues: List[str] = None) -> List[GameData]:
        """Get comprehensive data for games across all configured leagues."""
        if leagues is None:
            leagues = list(self.LEAGUES.keys())

        all_games = []

        for league_code in leagues:
            self.league = league_code
            try:
                games = self.get_todays_games(date)

                # Add league info to each game (filter out None values)
                for game in games:
                    if game is None:
                        continue

                    league_info = self.LEAGUES.get(league_code, {'name': league_code, 'country': ''})
                    game['league'] = league_info['name']
                    game['league_code'] = league_code
                    game['country'] = league_info['country']

                    game_data = GameData(game)
                    all_games.append(game_data)

            except Exception as e:
                print(f"Error fetching {league_code}: {e}")
                continue

        return all_games

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """Soccer-specific game parsing with robust error handling."""
        try:
            competitions = event.get('competitions', [{}])[0]
            competitors = competitions.get('competitors', [])

            if len(competitors) < 2:
                return None

            # Determine home/away
            home_team = None
            away_team = None
            for comp in competitors:
                if comp.get('homeAway') == 'home':
                    home_team = comp
                else:
                    away_team = comp

            if not home_team or not away_team:
                return None

            # Parse teams
            home = self._parse_team(home_team)
            away = self._parse_team(away_team)

            if not home or not away:
                return None

            # Parse odds
            odds = self._parse_odds(competitions)

            # Get status
            status = event.get('status', {})
            status_type = status.get('type', {})

            name = event.get('name', '').lower()

            # Competition type
            if 'champions league' in name:
                competition_type = 'Champions League'
            elif 'europa' in name:
                competition_type = 'Europa League'
            elif 'cup' in name or 'copa' in name:
                competition_type = 'Cup'
            else:
                competition_type = 'League'

            game = {
                'id': event.get('id'),
                'name': event.get('name', ''),
                'short_name': event.get('shortName', ''),
                'date': event.get('date'),
                'status': status_type.get('name', 'scheduled'),
                'status_detail': status_type.get('detail', ''),
                'venue': competitions.get('venue', {}).get('fullName', ''),
                'broadcast': self._get_broadcast(competitions),
                'home_team': home,
                'away_team': away,
                'odds': odds,
                'headlines': self._get_headlines(competitions),
                'competition_type': competition_type,
                'match_week': event.get('week', {}).get('number', '')
            }

            return game

        except Exception as e:
            print(f"Error parsing soccer game: {e}")
            return None

    def _parse_team(self, team_data: Dict) -> Dict:
        """Soccer-specific team parsing."""
        team = super()._parse_team(team_data)

        # Soccer records are often W-D-L (Wins-Draws-Losses)
        records = team_data.get('records', [])
        for rec in records:
            summary = rec.get('summary', '')
            if '-' in summary:
                team['record'] = summary
                break

        return team

    def format_for_article(self, game_data: GameData) -> Dict:
        """Format game data specifically for article generation."""
        game = game_data.game
        home = game_data.home_team
        away = game_data.away_team

        # Parse soccer records (W-D-L format, or just league position)
        def parse_soccer_record(record_str):
            try:
                if '-' in record_str:
                    parts = record_str.split('-')
                    if len(parts) == 3:  # W-D-L format
                        wins = int(parts[0])
                        draws = int(parts[1])
                        losses = int(parts[2])
                        points = (wins * 3) + draws
                        games = wins + draws + losses
                        ppg = points / games if games > 0 else 0
                        return {
                            'wins': wins,
                            'draws': draws,
                            'losses': losses,
                            'points': points,
                            'ppg': ppg
                        }
                return {'wins': 0, 'draws': 0, 'losses': 0, 'points': 0, 'ppg': 0}
            except:
                return {'wins': 0, 'draws': 0, 'losses': 0, 'points': 0, 'ppg': 0}

        home_parsed = parse_soccer_record(home.get('record', '0-0-0'))
        away_parsed = parse_soccer_record(away.get('record', '0-0-0'))

        return {
            'matchup': f"{away.get('name')} @ {home.get('name')}",
            'short_matchup': f"{away.get('abbreviation')} vs {home.get('abbreviation')}",
            'game_time': game.get('date', ''),
            'venue': game.get('venue', ''),
            'broadcast': game.get('broadcast', ''),
            'league': game.get('league', ''),
            'league_code': game.get('league_code', ''),
            'country': game.get('country', ''),
            'match_week': game.get('match_week', ''),
            'competition_type': game.get('competition_type', 'League'),
            'home': {
                'name': home.get('name'),
                'abbrev': home.get('abbreviation'),
                'id': home.get('id', ''),  # Team ID for logo URLs
                'logo': home.get('logo', ''),  # Direct logo URL from ESPN
                'record': home.get('record', ''),
                'wins': home_parsed['wins'],
                'draws': home_parsed['draws'],
                'losses': home_parsed['losses'],
                'points': home_parsed['points'],
                'ppg': home_parsed['ppg'],
            },
            'away': {
                'name': away.get('name'),
                'abbrev': away.get('abbreviation'),
                'id': away.get('id', ''),  # Team ID for logo URLs
                'logo': away.get('logo', ''),  # Direct logo URL from ESPN
                'record': away.get('record', ''),
                'wins': away_parsed['wins'],
                'draws': away_parsed['draws'],
                'losses': away_parsed['losses'],
                'points': away_parsed['points'],
                'ppg': away_parsed['ppg'],
            },
            'odds': {
                'spread': game_data.odds.get('spread', ''),
                'total': game_data.odds.get('over_under', ''),
            },
            'headlines': game.get('headlines', [])
        }


# Standalone test
if __name__ == "__main__":
    scraper = SoccerScraper()
    print(f"Fetching soccer games for today across all leagues...")

    # Test with just a few major leagues
    games = scraper.get_full_game_data(leagues=['eng.1', 'esp.1', 'ger.1', 'usa.1'])
    print(f"Found {len(games)} games\n")

    for game_data in games:
        formatted = scraper.format_for_article(game_data)
        print(f"{'='*60}")
        print(f"{formatted['league']} ({formatted['country']}) - Matchweek {formatted['match_week']}")
        print(f"Matchup: {formatted['matchup']}")
        print(f"Home: {formatted['home']['name']} ({formatted['home']['record']}) {formatted['home']['points']} pts")
        print(f"Away: {formatted['away']['name']} ({formatted['away']['record']}) {formatted['away']['points']} pts")
        print(f"Venue: {formatted['venue']}")
        print()
