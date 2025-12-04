"""
BASE DATA FETCHER
=================
Abstract base class for all sport-specific data fetchers.
"""

import os
import requests
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

from .cache import cache


class BaseFetcher(ABC):
    """Base class for sport-specific data fetchers"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        })
        self.cache = cache
        self.rate_limit_delay = 0.3  # Seconds between requests

    def _safe_request(self, url: str, params: Dict = None, timeout: int = 15) -> Optional[Dict]:
        """Make a rate-limited, error-handled request"""
        try:
            time.sleep(self.rate_limit_delay)
            response = self.session.get(url, params=params, timeout=timeout)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"  Request failed ({response.status_code}): {url[:80]}...")
                return None

        except requests.exceptions.Timeout:
            print(f"  Timeout: {url[:80]}...")
            return None
        except Exception as e:
            print(f"  Request error: {e}")
            return None

    @property
    @abstractmethod
    def sport_name(self) -> str:
        """Return sport identifier (e.g., 'NBA', 'MLB')"""
        pass

    @abstractmethod
    def get_todays_games(self) -> List[Dict]:
        """Fetch today's games for this sport"""
        pass

    @abstractmethod
    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch comprehensive team statistics"""
        pass

    @abstractmethod
    def get_advanced_stats(self, team_id: str) -> Dict:
        """Fetch advanced analytics for a team"""
        pass

    @abstractmethod
    def get_injuries(self, team_id: str) -> List[Dict]:
        """Fetch injury report for a team"""
        pass

    def get_complete_game_data(self, game: Dict) -> Dict:
        """
        Fetch all data for a single game.
        Override in subclass for sport-specific additions.
        """
        away_id = game.get('away', {}).get('id')
        home_id = game.get('home', {}).get('id')

        return {
            'game': game,
            'away_stats': self.get_team_stats(away_id) if away_id else {},
            'home_stats': self.get_team_stats(home_id) if home_id else {},
            'away_advanced': self.get_advanced_stats(away_id) if away_id else {},
            'home_advanced': self.get_advanced_stats(home_id) if home_id else {},
            'away_injuries': self.get_injuries(away_id) if away_id else [],
            'home_injuries': self.get_injuries(home_id) if home_id else [],
        }

    def fetch_all(self) -> Dict:
        """
        Fetch all data for today's games.
        Returns comprehensive data structure.
        """
        print(f"\n[{self.sport_name}]")

        games = self.get_todays_games()
        print(f"  Found {len(games)} games")

        if not games:
            return {
                'sport': self.sport_name,
                'games': [],
                'timestamp': datetime.now().isoformat(),
            }

        all_data = []
        for i, game in enumerate(games[:12]):  # Limit to 12 games
            print(f"  Processing game {i+1}/{min(len(games), 12)}: {game.get('name', 'Unknown')[:50]}")
            game_data = self.get_complete_game_data(game)
            all_data.append(game_data)

        return {
            'sport': self.sport_name,
            'games': all_data,
            'game_count': len(all_data),
            'timestamp': datetime.now().isoformat(),
        }


class OddsClient:
    """Fetch betting odds from The Odds API"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('ODDS_API_KEY', '')
        self.base_url = 'https://api.the-odds-api.com/v4/sports'
        self.sport_keys = {
            'NBA': 'basketball_nba',
            'NHL': 'icehockey_nhl',
            'NFL': 'americanfootball_nfl',
            'MLB': 'baseball_mlb',
            'NCAAB': 'basketball_ncaab',
            'NCAAF': 'americanfootball_ncaaf',
        }

    def get_odds(self, sport: str) -> Dict:
        """Fetch odds for a sport"""
        if not self.api_key:
            return {}

        sport_key = self.sport_keys.get(sport)
        if not sport_key:
            return {}

        try:
            url = f'{self.base_url}/{sport_key}/odds'
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'spreads,totals,h2h',
                'oddsFormat': 'american',
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                return {}

            data = response.json()
            odds_by_game = {}

            for game in data:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                key = f"{away_team} @ {home_team}"

                odds_data = self._extract_odds(game, home_team, away_team)
                odds_by_game[key] = odds_data

            return odds_by_game

        except Exception as e:
            print(f"  Odds API error: {e}")
            return {}

    def _extract_odds(self, game: Dict, home_team: str, away_team: str) -> Dict:
        """Extract odds data from API response"""
        odds_data = {
            'spread_home': None,
            'spread_away': None,
            'total': None,
            'ml_home': None,
            'ml_away': None,
            'opening_spread_home': None,
            'opening_total': None,
        }

        for bookmaker in game.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'spreads':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == home_team:
                            odds_data['spread_home'] = outcome.get('point')
                        elif outcome.get('name') == away_team:
                            odds_data['spread_away'] = outcome.get('point')

                elif market.get('key') == 'totals':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == 'Over':
                            odds_data['total'] = outcome.get('point')

                elif market.get('key') == 'h2h':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == home_team:
                            odds_data['ml_home'] = outcome.get('price')
                        elif outcome.get('name') == away_team:
                            odds_data['ml_away'] = outcome.get('price')

            break  # Only use first bookmaker

        return odds_data


class WeatherClient:
    """Fetch weather data for outdoor sports"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('WEATHER_API_KEY', '')

    def get_game_weather(self, city: str, state: str = None) -> Dict:
        """
        Get weather for a game location.
        Returns default indoor values if no API key or outdoor.
        """
        if not self.api_key:
            return self._default_weather()

        try:
            # Using OpenWeatherMap API
            location = f"{city},{state},US" if state else f"{city},US"
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'imperial',
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                return self._default_weather()

            data = response.json()

            return {
                'temperature': round(data.get('main', {}).get('temp', 70)),
                'feels_like': round(data.get('main', {}).get('feels_like', 70)),
                'humidity': data.get('main', {}).get('humidity', 50),
                'wind_speed': round(data.get('wind', {}).get('speed', 0)),
                'wind_direction': data.get('wind', {}).get('deg', 0),
                'conditions': data.get('weather', [{}])[0].get('description', 'Clear'),
                'precipitation': data.get('rain', {}).get('1h', 0) or data.get('snow', {}).get('1h', 0),
                'is_dome': False,
            }

        except Exception as e:
            print(f"  Weather API error: {e}")
            return self._default_weather()

    def _default_weather(self) -> Dict:
        """Default indoor/neutral weather"""
        return {
            'temperature': 70,
            'feels_like': 70,
            'humidity': 50,
            'wind_speed': 0,
            'wind_direction': 0,
            'conditions': 'Indoor/Dome',
            'precipitation': 0,
            'is_dome': True,
        }
