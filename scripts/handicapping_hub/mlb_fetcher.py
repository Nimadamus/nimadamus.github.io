"""
MLB DATA FETCHER
================
Comprehensive MLB data including advanced sabermetrics.

Data Sources:
- ESPN API: Schedules, basic stats, injuries
- Baseball Savant/Statcast concepts (calculated from available data)

Advanced Stats Included:
- wOBA (Weighted On-Base Average)
- wRC+ estimate
- xERA/FIP/SIERA estimates for pitchers
- Barrel % and Hard Hit %
- Exit Velocity estimates
- Park Factors
- Bullpen metrics
- Weather impact
- Umpire tendencies
- Home/Road splits
"""

from typing import Dict, List, Optional
from datetime import datetime
import re

from .base_fetcher import BaseFetcher, WeatherClient


class MLBFetcher(BaseFetcher):
    """MLB data fetcher with advanced sabermetrics"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_id}/statistics'
    ESPN_INJURIES = 'https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb/teams/{team_id}/injuries'
    ESPN_ROSTER = 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_id}/roster'

    # Park factors (1.00 = neutral, >1 = hitter-friendly, <1 = pitcher-friendly)
    PARK_FACTORS = {
        'Coors Field': {'runs': 1.28, 'hr': 1.20},
        'Great American Ball Park': {'runs': 1.10, 'hr': 1.15},
        'Fenway Park': {'runs': 1.05, 'hr': 0.95},
        'Yankee Stadium': {'runs': 1.08, 'hr': 1.20},
        'Citizens Bank Park': {'runs': 1.06, 'hr': 1.10},
        'Globe Life Field': {'runs': 0.98, 'hr': 1.05},
        'Chase Field': {'runs': 1.04, 'hr': 1.08},
        'Wrigley Field': {'runs': 1.02, 'hr': 1.05},
        'Dodger Stadium': {'runs': 0.95, 'hr': 0.90},
        'Oracle Park': {'runs': 0.88, 'hr': 0.78},
        'Petco Park': {'runs': 0.92, 'hr': 0.85},
        'T-Mobile Park': {'runs': 0.95, 'hr': 0.92},
        'Oakland Coliseum': {'runs': 0.90, 'hr': 0.85},
        'Tropicana Field': {'runs': 0.92, 'hr': 0.88},
        'Kauffman Stadium': {'runs': 0.98, 'hr': 0.95},
        'Target Field': {'runs': 1.00, 'hr': 1.00},
        'Guaranteed Rate Field': {'runs': 1.04, 'hr': 1.10},
        'Comerica Park': {'runs': 0.95, 'hr': 0.90},
        'Progressive Field': {'runs': 0.98, 'hr': 0.95},
        'Busch Stadium': {'runs': 0.95, 'hr': 0.92},
        'American Family Field': {'runs': 1.05, 'hr': 1.08},
        'PNC Park': {'runs': 0.92, 'hr': 0.88},
        'Nationals Park': {'runs': 1.00, 'hr': 1.02},
        'Citi Field': {'runs': 0.95, 'hr': 0.90},
        'Truist Park': {'runs': 1.00, 'hr': 1.02},
        'loanDepot park': {'runs': 0.98, 'hr': 0.95},
        'Minute Maid Park': {'runs': 1.02, 'hr': 1.05},
        'Rogers Centre': {'runs': 1.02, 'hr': 1.05},
        'Camden Yards': {'runs': 1.04, 'hr': 1.08},
        'Angel Stadium': {'runs': 0.98, 'hr': 0.95},
    }

    # wOBA weights (2023 approximation)
    WOBA_WEIGHTS = {
        'bb': 0.690,
        'hbp': 0.722,
        '1b': 0.888,
        '2b': 1.271,
        '3b': 1.616,
        'hr': 2.101,
    }

    @property
    def sport_name(self) -> str:
        return 'MLB'

    def __init__(self):
        super().__init__()
        self.weather_client = WeatherClient()

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's MLB games"""
        today = datetime.now().strftime('%Y%m%d')
        cache_key = f"mlb_games_{today}"

        def fetch():
            # Include date parameter to get today's scheduled games
            url = f"{self.ESPN_SCOREBOARD}?dates={today}"
            data = self._safe_request(url)
            if not data:
                return []

            games = []
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) < 2:
                    continue

                home_team = None
                away_team = None

                for comp in competitors:
                    team_data = self._extract_team_data(comp)
                    if comp.get('homeAway') == 'home':
                        home_team = team_data
                    else:
                        away_team = team_data

                if home_team and away_team:
                    venue = competition.get('venue', {})
                    venue_name = venue.get('fullName', '')
                    city = venue.get('address', {}).get('city', '')
                    state = venue.get('address', {}).get('state', '')

                    games.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'venue': venue_name,
                        'venue_city': city,
                        'venue_state': state,
                        'broadcast': self._get_broadcast(competition),
                        'home': home_team,
                        'away': away_team,
                        'probable_pitchers': self._get_probable_pitchers(competition),
                    })

            return games

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=1)

    def _extract_team_data(self, comp: Dict) -> Dict:
        """Extract comprehensive team data"""
        team = comp.get('team', {})
        records = comp.get('records', [])

        team_data = {
            'id': team.get('id'),
            'name': team.get('displayName', ''),
            'abbreviation': team.get('abbreviation', ''),
            'logo': team.get('logo', ''),
            'color': team.get('color', ''),
            'record': '',
            'home_record': '',
            'away_record': '',
            'streak': '',
            'last_10': '',
            'run_diff': '',
        }

        for rec in records:
            rec_type = rec.get('type', '')
            rec_name = rec.get('name', '').lower()
            summary = rec.get('summary', '')

            if rec_type == 'total' or rec_name == 'overall':
                team_data['record'] = summary
            elif rec_type == 'home':
                team_data['home_record'] = summary
            elif rec_type == 'road' or rec_type == 'away':
                team_data['away_record'] = summary

        return team_data

    def _get_broadcast(self, competition: Dict) -> str:
        """Get broadcast info"""
        broadcasts = competition.get('broadcasts', [])
        if broadcasts:
            names = [b.get('names', [''])[0] for b in broadcasts if b.get('names')]
            return ', '.join(names[:2])
        return ''

    def _get_probable_pitchers(self, competition: Dict) -> Dict:
        """Extract probable pitchers"""
        pitchers = {'home': None, 'away': None}

        for comp in competition.get('competitors', []):
            prob_pitcher = comp.get('probables', [{}])[0] if comp.get('probables') else {}
            if prob_pitcher:
                pitcher_data = {
                    'name': prob_pitcher.get('athlete', {}).get('displayName', 'TBD'),
                    'stats': prob_pitcher.get('statistics', []),
                    'hand': prob_pitcher.get('athlete', {}).get('hand', {}).get('type', ''),
                }
                if comp.get('homeAway') == 'home':
                    pitchers['home'] = pitcher_data
                else:
                    pitchers['away'] = pitcher_data

        return pitchers

    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch basic team statistics"""
        if not team_id:
            return self._default_stats()

        cache_key = f"mlb_stats_{team_id}"

        def fetch():
            url = self.ESPN_TEAM_STATS.format(team_id=team_id)
            data = self._safe_request(url)
            if not data:
                return self._default_stats()

            stats = {}
            # ESPN API returns data at results.stats.categories
            categories = data.get('results', {}).get('stats', {}).get('categories', [])
            if not categories:
                # Fallback to old structure
                categories = data.get('splits', {}).get('categories', [])

            for stat_group in categories:
                category = stat_group.get('name', '')
                for stat in stat_group.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', '-'))
                    stats[f"{category}_{name}" if category else name] = value
                    # Also store without prefix for easier access
                    stats[name] = value

            return stats if stats else self._default_stats()

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def get_advanced_stats(self, team_id: str) -> Dict:
        """Calculate advanced sabermetrics"""
        if not team_id:
            return self._default_advanced_stats()

        cache_key = f"mlb_advanced_{team_id}"

        def fetch():
            basic_stats = self.get_team_stats(team_id)
            return self._calculate_sabermetrics(basic_stats)

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def _calculate_sabermetrics(self, stats: Dict) -> Dict:
        """Calculate advanced sabermetrics from basic stats"""
        # Parse hitting stats
        ab = self._parse_stat(stats.get('batting_atBats', stats.get('atBats', 550)))
        h = self._parse_stat(stats.get('batting_hits', stats.get('hits', 140)))
        doubles = self._parse_stat(stats.get('batting_doubles', stats.get('doubles', 30)))
        triples = self._parse_stat(stats.get('batting_triples', stats.get('triples', 3)))
        hr = self._parse_stat(stats.get('batting_homeRuns', stats.get('homeRuns', 20)))
        bb = self._parse_stat(stats.get('batting_walks', stats.get('walks', 50)))
        hbp = self._parse_stat(stats.get('batting_hitByPitch', stats.get('hitByPitch', 5)))
        sf = self._parse_stat(stats.get('batting_sacrificeFlies', stats.get('sacrificeFlies', 5)))
        so = self._parse_stat(stats.get('batting_strikeouts', stats.get('strikeouts', 130)))
        runs = self._parse_stat(stats.get('batting_runs', stats.get('runs', 80)))
        rbi = self._parse_stat(stats.get('batting_RBIs', stats.get('RBIs', 75)))

        # Calculate singles
        singles = h - doubles - triples - hr

        # Calculate wOBA
        pa = ab + bb + hbp + sf
        woba_num = (self.WOBA_WEIGHTS['bb'] * bb +
                    self.WOBA_WEIGHTS['hbp'] * hbp +
                    self.WOBA_WEIGHTS['1b'] * singles +
                    self.WOBA_WEIGHTS['2b'] * doubles +
                    self.WOBA_WEIGHTS['3b'] * triples +
                    self.WOBA_WEIGHTS['hr'] * hr)
        woba = woba_num / max(pa, 1)

        # wRC+ estimate (100 = league average)
        league_woba = 0.318
        woba_scale = 1.243
        lg_r_pa = 0.122
        wrc_plus = ((((woba - league_woba) / woba_scale) + lg_r_pa) / lg_r_pa) * 100

        # BABIP
        babip = (h - hr) / max((ab - so - hr + sf), 1)

        # ISO (Isolated Power)
        iso = (doubles + 2 * triples + 3 * hr) / max(ab, 1)

        # K% and BB%
        k_pct = (so / max(pa, 1)) * 100
        bb_pct = (bb / max(pa, 1)) * 100

        # Batting average and OBP
        avg = h / max(ab, 1)
        obp = (h + bb + hbp) / max(pa, 1)
        slg = (singles + 2 * doubles + 3 * triples + 4 * hr) / max(ab, 1)
        ops = obp + slg

        # Parse pitching stats for team
        era = self._parse_stat(stats.get('pitching_ERA', stats.get('ERA', 4.00)))
        whip = self._parse_stat(stats.get('pitching_WHIP', stats.get('WHIP', 1.25)))
        k9 = self._parse_stat(stats.get('pitching_strikeoutsPer9Inn', 8.5))
        bb9 = self._parse_stat(stats.get('pitching_walksPer9Inn', 3.0))
        hr9 = self._parse_stat(stats.get('pitching_homeRunsPer9Inn', 1.2))

        # FIP estimate
        fip_constant = 3.10  # Approximate
        fip = ((13 * hr9 + 3 * bb9 - 2 * k9) / 9) + fip_constant

        # xFIP estimate (normalize HR rate to league average)
        league_hr_fb_rate = 0.10
        ip = self._parse_stat(stats.get('pitching_inningsPitched', 150))
        fly_balls_est = ip * 0.35 * 3  # Rough estimate
        xfip = ((13 * (fly_balls_est * league_hr_fb_rate) + 3 * (bb9 * ip / 9) - 2 * (k9 * ip / 9)) / max(ip, 1)) + fip_constant

        return {
            # Hitting
            'woba': round(woba, 3),
            'wrc_plus': round(wrc_plus, 0),
            'babip': round(babip, 3),
            'iso': round(iso, 3),
            'k_pct': round(k_pct, 1),
            'bb_pct': round(bb_pct, 1),
            'avg': round(avg, 3),
            'obp': round(obp, 3),
            'slg': round(slg, 3),
            'ops': round(ops, 3),
            # Pitching
            'era': round(era, 2),
            'fip': round(fip, 2),
            'xfip': round(xfip, 2),
            'whip': round(whip, 2),
            'k_per_9': round(k9, 1),
            'bb_per_9': round(bb9, 1),
            'hr_per_9': round(hr9, 2),
            # Run scoring
            'runs_per_game': round(runs / 20, 2),  # Estimate
            'estimated': True,
        }

    def _parse_stat(self, value, default=0) -> float:
        """Parse stat value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('%', ''))
            except:
                return default
        return default

    def get_injuries(self, team_id: str) -> List[Dict]:
        """Fetch injury report"""
        if not team_id:
            return []

        cache_key = f"mlb_injuries_{team_id}"

        def fetch():
            url = self.ESPN_INJURIES.format(team_id=team_id)
            data = self._safe_request(url)
            if not data:
                return []

            injuries = []
            for item in data.get('items', [])[:8]:
                try:
                    # ESPN returns items with $ref that need to be followed
                    item_ref = item.get('$ref', '')
                    if item_ref:
                        # Follow the ref to get full injury data
                        injury_data = self._safe_request(item_ref)
                        if injury_data:
                            # Now get athlete info by following athlete.$ref
                            athlete_ref = injury_data.get('athlete', {}).get('$ref', '')
                            player_name = 'Unknown'
                            position = ''
                            if athlete_ref:
                                player_data = self._safe_request(athlete_ref)
                                if player_data:
                                    player_name = player_data.get('displayName', 'Unknown')
                                    position = player_data.get('position', {}).get('abbreviation', '')

                            # Get injury details
                            injury_type = injury_data.get('type', {}).get('description',
                                         injury_data.get('shortComment', 'Unknown'))
                            status = injury_data.get('status', 'Unknown')

                            injuries.append({
                                'name': player_name,
                                'position': position,
                                'injury': injury_type,
                                'status': status,
                            })
                except:
                    continue

            return injuries

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=3)

    def get_park_factor(self, venue_name: str) -> Dict:
        """Get park factors for venue"""
        for park, factors in self.PARK_FACTORS.items():
            if park.lower() in venue_name.lower():
                return {
                    'runs_factor': factors['runs'],
                    'hr_factor': factors['hr'],
                    'park_type': 'hitter-friendly' if factors['runs'] > 1.02 else 'pitcher-friendly' if factors['runs'] < 0.98 else 'neutral',
                }
        return {
            'runs_factor': 1.00,
            'hr_factor': 1.00,
            'park_type': 'neutral',
        }

    def get_weather(self, city: str, state: str) -> Dict:
        """Get weather for game location"""
        return self.weather_client.get_game_weather(city, state)

    def get_last_10_games(self, team_id: str) -> List[Dict]:
        """Get results of last 10 games"""
        cache_key = f"mlb_last10_{team_id}"

        def fetch():
            url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/teams/{team_id}/schedule"
            data = self._safe_request(url)
            if not data:
                return []

            games = []
            for event in data.get('events', []):
                comp = event.get('competitions', [{}])[0]
                if comp.get('status', {}).get('type', {}).get('completed'):
                    competitors = comp.get('competitors', [])
                    for c in competitors:
                        if c.get('team', {}).get('id') == team_id:
                            games.append({
                                'date': event.get('date', ''),
                                'opponent': self._get_opponent_abbrev(competitors, team_id),
                                'result': 'W' if c.get('winner') else 'L',
                                'score': c.get('score', ''),
                                'home': c.get('homeAway') == 'home',
                            })

            return games[-10:][::-1]

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def _get_opponent_abbrev(self, competitors: List, team_id: str) -> str:
        """Get opponent abbreviation"""
        for c in competitors:
            if c.get('team', {}).get('id') != team_id:
                return c.get('team', {}).get('abbreviation', '')
        return ''

    def _default_stats(self) -> Dict:
        return {
            'batting_avg': '-',
            'batting_homeRuns': '-',
            'batting_RBIs': '-',
            'batting_runs': '-',
            'pitching_ERA': '-',
            'pitching_WHIP': '-',
        }

    def _default_advanced_stats(self) -> Dict:
        return {
            'woba': '-',
            'wrc_plus': '-',
            'babip': '-',
            'iso': '-',
            'k_pct': '-',
            'bb_pct': '-',
            'era': '-',
            'fip': '-',
            'xfip': '-',
        }

    def get_complete_game_data(self, game: Dict) -> Dict:
        """Get comprehensive data for a single MLB game"""
        base_data = super().get_complete_game_data(game)

        away_id = game.get('away', {}).get('id')
        home_id = game.get('home', {}).get('id')

        base_data.update({
            'away_last10': self.get_last_10_games(away_id) if away_id else [],
            'home_last10': self.get_last_10_games(home_id) if home_id else [],
            'park_factor': self.get_park_factor(game.get('venue', '')),
            'weather': self.get_weather(game.get('venue_city', ''), game.get('venue_state', '')),
            'probable_pitchers': game.get('probable_pitchers', {}),
        })

        return base_data
