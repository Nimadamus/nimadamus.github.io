"""
Base Scraper for ESPN Data
Handles common functionality for all sport scrapers
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ESPN_BASE_URL, get_espn_scoreboard_url, get_espn_teams_url, get_espn_standings_url

class BaseScraper:
    """Base class for all sport scrapers."""

    def __init__(self, sport: str, league: str):
        self.sport = sport
        self.league = league
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self._teams_cache = None
        self._standings_cache = None

    def _make_request(self, url: str, retries: int = 3) -> Optional[Dict]:
        """Make HTTP request with retries."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def get_todays_games(self, date: str = None) -> List[Dict]:
        """Get today's games from ESPN API."""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = get_espn_scoreboard_url(self.sport, self.league, date)
        data = self._make_request(url)

        if not data or 'events' not in data:
            return []

        games = []
        for event in data['events']:
            game = self._parse_game(event)
            if game:
                games.append(game)

        return games

    def _parse_game(self, event: Dict) -> Optional[Dict]:
        """Parse a single game event. Override in subclasses for sport-specific parsing."""
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

            # Parse odds if available
            odds = self._parse_odds(competitions)

            # Get game status
            status = event.get('status', {})
            status_type = status.get('type', {})

            game = {
                'id': event.get('id'),
                'name': event.get('name', ''),
                'short_name': event.get('shortName', ''),
                'date': event.get('date'),
                'status': status_type.get('name', 'scheduled'),
                'status_detail': status_type.get('detail', ''),
                'venue': competitions.get('venue', {}).get('fullName', ''),
                'broadcast': self._get_broadcast(competitions),
                'home_team': self._parse_team(home_team),
                'away_team': self._parse_team(away_team),
                'odds': odds,
                'headlines': self._get_headlines(competitions)
            }

            return game

        except Exception as e:
            print(f"Error parsing game: {e}")
            return None

    def _parse_team(self, team_data: Dict) -> Dict:
        """Parse team data from competitor."""
        team = team_data.get('team', {})
        records = team_data.get('records', [])

        # Get overall record
        record = ""
        for rec in records:
            if rec.get('name') == 'overall' or rec.get('type') == 'total':
                record = rec.get('summary', '')
                break
        if not record and records:
            record = records[0].get('summary', '')

        # Get score if game is live/final
        score = team_data.get('score', '0')

        return {
            'id': team.get('id'),
            'name': team.get('displayName', team.get('name', '')),
            'abbreviation': team.get('abbreviation', ''),
            'short_name': team.get('shortDisplayName', ''),
            'logo': team.get('logo', ''),
            'color': team.get('color', ''),
            'record': record,
            'score': score,
            'winner': team_data.get('winner', False),
            'home_away': team_data.get('homeAway', '')
        }

    def _parse_odds(self, competition: Dict) -> Dict:
        """Parse betting odds from competition data."""
        odds_data = competition.get('odds', [])
        if not odds_data:
            return {'spread': '', 'over_under': '', 'home_ml': '', 'away_ml': '', 'provider': ''}

        odds = odds_data[0] if odds_data else {}
        if odds is None:
            odds = {}

        return {
            'spread': odds.get('details', '') if odds else '',
            'over_under': odds.get('overUnder', '') if odds else '',
            'home_ml': '',
            'away_ml': '',
            'provider': odds.get('provider', {}).get('name', '') if odds else ''
        }

    def _get_broadcast(self, competition: Dict) -> str:
        """Get broadcast network."""
        broadcasts = competition.get('broadcasts', [])
        if broadcasts:
            names = []
            for broadcast in broadcasts:
                for market in broadcast.get('names', []):
                    names.append(market)
            return ', '.join(names[:2])  # Limit to 2 networks
        return ''

    def _get_headlines(self, competition: Dict) -> List[str]:
        """Get game headlines/notes."""
        headlines = []
        notes = competition.get('notes', [])
        for note in notes:
            if note.get('headline'):
                headlines.append(note['headline'])
        return headlines

    def get_standings(self) -> Dict:
        """Get league standings."""
        if self._standings_cache:
            return self._standings_cache

        url = get_espn_standings_url(self.sport, self.league)
        data = self._make_request(url)

        if not data:
            return {}

        self._standings_cache = self._parse_standings(data)
        return self._standings_cache

    def _parse_standings(self, data: Dict) -> Dict:
        """Parse standings data. Override in subclasses for sport-specific parsing."""
        standings = {}

        children = data.get('children', [])
        for conference in children:
            conf_name = conference.get('name', '')
            standings[conf_name] = []

            # Some leagues have divisions within conferences
            if 'children' in conference:
                for division in conference['children']:
                    div_name = division.get('name', '')
                    for entry in division.get('standings', {}).get('entries', []):
                        team_standing = self._parse_standing_entry(entry, conf_name, div_name)
                        if team_standing:
                            standings[conf_name].append(team_standing)
            else:
                for entry in conference.get('standings', {}).get('entries', []):
                    team_standing = self._parse_standing_entry(entry, conf_name)
                    if team_standing:
                        standings[conf_name].append(team_standing)

        return standings

    def _parse_standing_entry(self, entry: Dict, conference: str = '', division: str = '') -> Optional[Dict]:
        """Parse a single standing entry."""
        try:
            team = entry.get('team', {})
            stats = {s['name']: s['value'] for s in entry.get('stats', [])}

            return {
                'team_id': team.get('id'),
                'team_name': team.get('displayName', ''),
                'abbreviation': team.get('abbreviation', ''),
                'conference': conference,
                'division': division,
                'wins': int(stats.get('wins', 0)),
                'losses': int(stats.get('losses', 0)),
                'ties': int(stats.get('ties', 0)),
                'win_pct': float(stats.get('winPercent', 0)),
                'games_back': stats.get('gamesBehind', '-'),
                'streak': stats.get('streak', ''),
                'last_10': stats.get('last10Record', ''),
                'home_record': stats.get('home', ''),
                'away_record': stats.get('road', '')
            }
        except Exception as e:
            print(f"Error parsing standing entry: {e}")
            return None

    def get_team_stats(self, team_id: str) -> Dict:
        """Get detailed stats for a specific team."""
        url = f"{ESPN_BASE_URL}/{self.sport}/{self.league}/teams/{team_id}/statistics"
        data = self._make_request(url)
        return data if data else {}

    def get_team_schedule(self, team_id: str) -> List[Dict]:
        """Get team's recent and upcoming games."""
        url = f"{ESPN_BASE_URL}/{self.sport}/{self.league}/teams/{team_id}/schedule"
        data = self._make_request(url)

        if not data or 'events' not in data:
            return []

        return data['events']

    def get_recent_form(self, team_id: str, num_games: int = 10) -> Dict:
        """Calculate team's recent form based on last N games."""
        schedule = self.get_team_schedule(team_id)

        completed_games = [g for g in schedule if g.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('completed', False)]
        recent_games = completed_games[-num_games:] if len(completed_games) >= num_games else completed_games

        wins = 0
        losses = 0

        for game in recent_games:
            competitions = game.get('competitions', [{}])[0]
            for competitor in competitions.get('competitors', []):
                if competitor.get('id') == team_id or competitor.get('team', {}).get('id') == team_id:
                    if competitor.get('winner', False):
                        wins += 1
                    else:
                        losses += 1
                    break

        return {
            'last_n': num_games,
            'wins': wins,
            'losses': losses,
            'record': f"{wins}-{losses}",
            'win_pct': wins / len(recent_games) if recent_games else 0
        }

    def format_game_for_content(self, game: Dict) -> Dict:
        """Format game data for content generation. Override in subclasses."""
        return game


class GameData:
    """Container for all data about a single game."""

    def __init__(self, game: Dict, home_stats: Dict = None, away_stats: Dict = None):
        self.game = game
        self.home_team = game.get('home_team', {})
        self.away_team = game.get('away_team', {})
        self.odds = game.get('odds', {})
        self.home_stats = home_stats or {}
        self.away_stats = away_stats or {}
        self.home_form = {}
        self.away_form = {}
        self.injuries = {'home': [], 'away': []}

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'game': self.game,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'odds': self.odds,
            'home_stats': self.home_stats,
            'away_stats': self.away_stats,
            'home_form': self.home_form,
            'away_form': self.away_form,
            'injuries': self.injuries
        }

    def __repr__(self):
        return f"GameData({self.away_team.get('name', 'Away')} @ {self.home_team.get('name', 'Home')})"
