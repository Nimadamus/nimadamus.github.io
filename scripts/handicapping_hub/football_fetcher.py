"""
FOOTBALL DATA FETCHER (NFL & NCAAF)
===================================
Comprehensive football data including advanced analytics.

Data Sources:
- ESPN API: Schedules, basic stats, injuries

Advanced Stats Included:
- EPA (Expected Points Added) estimates
- Success Rate
- Rush/Pass efficiency
- Explosive play rate
- Red zone efficiency
- QB metrics (QBR, passer rating)
- Strength of schedule
- Weather impact
- Home/Road splits
"""

from typing import Dict, List, Optional
from datetime import datetime
import re

from .base_fetcher import BaseFetcher, WeatherClient


class NFLFetcher(BaseFetcher):
    """NFL data fetcher with advanced analytics"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/statistics'
    ESPN_INJURIES = 'https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/teams/{team_id}/injuries'

    # Dome/indoor stadiums
    DOME_STADIUMS = [
        'SoFi Stadium', 'Allegiant Stadium', 'AT&T Stadium', 'US Bank Stadium',
        'Lucas Oil Stadium', 'Mercedes-Benz Stadium', 'Caesars Superdome',
        'State Farm Stadium', 'Ford Field', 'NRG Stadium',
    ]

    @property
    def sport_name(self) -> str:
        return 'NFL'

    def __init__(self):
        super().__init__()
        self.weather_client = WeatherClient()

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's/this week's NFL games"""
        cache_key = f"nfl_games_{datetime.now().strftime('%Y-%m-%d')}"

        def fetch():
            data = self._safe_request(self.ESPN_SCOREBOARD)
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

                    games.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'venue': venue_name,
                        'venue_city': venue.get('address', {}).get('city', ''),
                        'venue_state': venue.get('address', {}).get('state', ''),
                        'is_dome': self._is_dome_stadium(venue_name),
                        'broadcast': self._get_broadcast(competition),
                        'home': home_team,
                        'away': away_team,
                        'week': event.get('week', {}).get('number', ''),
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
            'div_record': '',
            'conf_record': '',
            'streak': '',
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
            elif 'division' in rec_name:
                team_data['div_record'] = summary
            elif 'conference' in rec_name:
                team_data['conf_record'] = summary

        return team_data

    def _get_broadcast(self, competition: Dict) -> str:
        """Get broadcast info"""
        broadcasts = competition.get('broadcasts', [])
        if broadcasts:
            names = [b.get('names', [''])[0] for b in broadcasts if b.get('names')]
            return ', '.join(names[:2])
        return ''

    def _is_dome_stadium(self, venue_name: str) -> bool:
        """Check if stadium is domed/indoor"""
        for dome in self.DOME_STADIUMS:
            if dome.lower() in venue_name.lower():
                return True
        return False

    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch basic team statistics"""
        if not team_id:
            return self._default_stats()

        cache_key = f"nfl_stats_{team_id}"

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
                    value = stat.get('displayValue', stat.get('value', 'N/A'))
                    stats[name] = value

            return stats if stats else self._default_stats()

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def get_advanced_stats(self, team_id: str) -> Dict:
        """Calculate advanced football analytics"""
        if not team_id:
            return self._default_advanced_stats()

        cache_key = f"nfl_advanced_{team_id}"

        def fetch():
            basic_stats = self.get_team_stats(team_id)
            return self._calculate_advanced_stats(basic_stats)

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def _calculate_advanced_stats(self, stats: Dict) -> Dict:
        """Calculate advanced metrics from basic stats"""
        # Parse offensive stats
        ppg = self._parse_stat(stats.get('avgPointsPerGame', stats.get('totalPointsPerGame', 22)))
        opp_ppg = self._parse_stat(stats.get('avgPointsAgainst', 22))
        total_yards = self._parse_stat(stats.get('netTotalYards', stats.get('totalYards', 320)))
        rush_yards = self._parse_stat(stats.get('rushingYardsPerGame', 110))
        pass_yards = self._parse_stat(stats.get('netPassingYardsPerGame', stats.get('passingYardsPerGame', 210)))
        rush_att = self._parse_stat(stats.get('rushingAttempts', stats.get('rushingAttemptsPerGame', 26)))
        pass_att = self._parse_stat(stats.get('passingAttempts', stats.get('passAttempts', 32)))

        # Calculate per-play metrics
        total_plays = rush_att + pass_att
        yards_per_play = total_yards / max(total_plays, 1)
        yards_per_rush = rush_yards / max(rush_att, 1)
        yards_per_pass = pass_yards / max(pass_att, 1)

        # Turnover metrics
        turnovers = self._parse_stat(stats.get('totalGiveaways', stats.get('turnovers', 10)))
        takeaways = self._parse_stat(stats.get('totalTakeaways', stats.get('takeaways', 10)))
        turnover_diff = takeaways - turnovers

        # Third down
        third_pct = self._parse_stat(stats.get('thirdDownConvPct', 38))

        # Red zone
        rz_pct = self._parse_stat(stats.get('redZoneAttempts', 60)) / max(1, 16)  # Estimate

        # EPA estimate (simplified)
        # EPA correlates strongly with point differential and efficiency
        point_diff = ppg - opp_ppg
        efficiency = yards_per_play - 5.0  # 5.0 is roughly league average
        epa_estimate = (point_diff * 0.3) + (efficiency * 2) + (turnover_diff * 0.5)

        # Success rate estimate (plays gaining 40% of needed yards on 1st, 50% on 2nd, 100% on 3rd/4th)
        # Simplified: correlated with third down conversion and yards per play
        success_rate_est = min(50 + (third_pct - 38) + (yards_per_play - 5) * 3, 65)

        # Explosive play rate estimate
        explosive_rate = min(max(10 + (yards_per_play - 5) * 2, 5), 18)

        # QB Rating estimate
        comp_pct = self._parse_stat(stats.get('completionPct', 63))
        pass_td = self._parse_stat(stats.get('passingTouchdowns', 2))
        interceptions = self._parse_stat(stats.get('interceptions', 1))
        qbr_est = min(158.3, max(0,
            ((comp_pct / 100 - 0.3) * 5 +
             (yards_per_pass / 20) +
             (pass_td / pass_att * 20 if pass_att > 0 else 0) -
             (interceptions / max(pass_att, 1) * 25) + 2.375) / 6 * 100))

        return {
            # Offensive efficiency
            'ppg': round(ppg, 1),
            'yards_per_play': round(yards_per_play, 2),
            'yards_per_rush': round(yards_per_rush, 1),
            'yards_per_pass': round(yards_per_pass, 1),
            'rush_pct': round((rush_att / max(total_plays, 1)) * 100, 1),
            'pass_pct': round((pass_att / max(total_plays, 1)) * 100, 1),

            # Advanced metrics
            'epa_per_play': round(epa_estimate / 100, 2),
            'success_rate': round(success_rate_est, 1),
            'explosive_play_rate': round(explosive_rate, 1),

            # Situational
            'third_down_pct': round(third_pct, 1),
            'red_zone_pct': 'N/A',  # Need more detailed data

            # Turnovers
            'turnover_diff': round(turnover_diff, 0),
            'takeaways': round(takeaways, 0),
            'giveaways': round(turnovers, 0),

            # Defense
            'opp_ppg': round(opp_ppg, 1),
            'point_diff': round(point_diff, 1),

            # QB metrics
            'passer_rating': round(qbr_est, 1),
            'completion_pct': round(comp_pct, 1),

            'estimated': True,
        }

    def _parse_stat(self, value, default=0) -> float:
        """Parse stat value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('%', '').replace(',', ''))
            except:
                return default
        return default

    def get_injuries(self, team_id: str) -> List[Dict]:
        """Fetch injury report"""
        if not team_id:
            return []

        cache_key = f"nfl_injuries_{team_id}"

        def fetch():
            url = self.ESPN_INJURIES.format(team_id=team_id)
            data = self._safe_request(url)
            if not data:
                return []

            injuries = []
            for item in data.get('items', [])[:10]:
                try:
                    player_ref = item.get('athlete', {}).get('$ref', '')
                    if player_ref:
                        player_data = self._safe_request(player_ref)
                        if player_data:
                            injuries.append({
                                'name': player_data.get('displayName', 'Unknown'),
                                'position': player_data.get('position', {}).get('abbreviation', ''),
                                'injury': item.get('type', {}).get('description', 'Unknown'),
                                'status': item.get('status', 'Unknown'),
                            })
                except:
                    continue

            return injuries

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=3)

    def get_weather(self, city: str, state: str, is_dome: bool) -> Dict:
        """Get weather for game location"""
        if is_dome:
            return {
                'temperature': 72,
                'feels_like': 72,
                'humidity': 50,
                'wind_speed': 0,
                'wind_direction': 0,
                'conditions': 'Indoor/Dome',
                'precipitation': 0,
                'is_dome': True,
            }
        return self.weather_client.get_game_weather(city, state)

    def get_last_5_games(self, team_id: str) -> List[Dict]:
        """Get results of last 5 games"""
        cache_key = f"nfl_last5_{team_id}"

        def fetch():
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}/schedule"
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

            return games[-5:][::-1]

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def _get_opponent_abbrev(self, competitors: List, team_id: str) -> str:
        """Get opponent abbreviation"""
        for c in competitors:
            if c.get('team', {}).get('id') != team_id:
                return c.get('team', {}).get('abbreviation', '')
        return ''

    def _default_stats(self) -> Dict:
        return {
            'avgPointsPerGame': 'N/A',
            'totalYards': 'N/A',
            'rushingYardsPerGame': 'N/A',
            'passingYardsPerGame': 'N/A',
        }

    def _default_advanced_stats(self) -> Dict:
        return {
            'ppg': 'N/A',
            'yards_per_play': 'N/A',
            'epa_per_play': 'N/A',
            'success_rate': 'N/A',
            'turnover_diff': 'N/A',
        }

    def get_complete_game_data(self, game: Dict) -> Dict:
        """Get comprehensive data for a single NFL game"""
        base_data = super().get_complete_game_data(game)

        away_id = game.get('away', {}).get('id')
        home_id = game.get('home', {}).get('id')

        base_data.update({
            'away_last5': self.get_last_5_games(away_id) if away_id else [],
            'home_last5': self.get_last_5_games(home_id) if home_id else [],
            'weather': self.get_weather(
                game.get('venue_city', ''),
                game.get('venue_state', ''),
                game.get('is_dome', False)
            ),
        })

        return base_data


class NCAAFFetcher(NFLFetcher):
    """NCAAF data fetcher - extends NFL fetcher"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard?groups=80'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/statistics'
    ESPN_STANDINGS = 'https://site.web.api.espn.com/apis/v2/sports/football/college-football/standings'

    _standings_cache = None

    @property
    def sport_name(self) -> str:
        return 'NCAAF'

    def _get_standings_data(self) -> Dict:
        """Get standings data with avgPointsFor, avgPointsAgainst, etc."""
        if NCAAFFetcher._standings_cache is not None:
            return NCAAFFetcher._standings_cache

        cache_key = f"ncaaf_standings_{datetime.now().strftime('%Y-%m-%d')}"

        def fetch():
            data = self._safe_request(self.ESPN_STANDINGS)
            if not data:
                return {}

            standings = {}
            # Handle conference-based structure
            children = data.get('children', [])
            for conference in children:
                entries = conference.get('standings', {}).get('entries', [])
                for entry in entries:
                    team = entry.get('team', {})
                    team_id = str(team.get('id', ''))
                    team_name = team.get('displayName', '')
                    stats = {s.get('name'): s.get('value', s.get('displayValue', 0)) for s in entry.get('stats', [])}
                    standings[team_id] = stats
                    standings[team_name] = stats  # Also key by name

            return standings

        result = self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)
        NCAAFFetcher._standings_cache = result
        return result

    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch basic team statistics merged with standings data"""
        if not team_id:
            return self._default_stats()

        cache_key = f"ncaaf_stats_{team_id}"

        def fetch():
            url = self.ESPN_TEAM_STATS.format(team_id=team_id)
            data = self._safe_request(url)

            stats = {}
            if data:
                # ESPN API returns data at results.stats.categories
                categories = data.get('results', {}).get('stats', {}).get('categories', [])
                if not categories:
                    # Fallback to old structure
                    categories = data.get('splits', {}).get('categories', [])

                for stat_group in categories:
                    category = stat_group.get('name', '')
                    for stat in stat_group.get('stats', []):
                        name = stat.get('name', '')
                        value = stat.get('displayValue', stat.get('value', 'N/A'))
                        stats[name] = value

            # Merge with standings data for avgPointsAgainst, differential, etc.
            standings = self._get_standings_data()
            team_standings = standings.get(str(team_id), {})

            # Add standings stats that aren't in team stats
            if team_standings:
                for key in ['avgPointsFor', 'avgPointsAgainst', 'pointDifferential', 'differential', 'wins', 'losses']:
                    if key in team_standings and key not in stats:
                        stats[key] = team_standings[key]
                # Point differential
                if 'pointDifferential' in team_standings:
                    stats['point_diff'] = team_standings['pointDifferential']
                elif 'differential' in team_standings:
                    stats['point_diff'] = team_standings['differential']

            return stats if stats else self._default_stats()

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's NCAAF games (overrides NFLFetcher to use correct cache key)"""
        cache_key = f"ncaaf_games_{datetime.now().strftime('%Y-%m-%d')}"

        def fetch():
            data = self._safe_request(self.ESPN_SCOREBOARD)
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

                    games.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'venue': venue_name,
                        'venue_city': venue.get('address', {}).get('city', ''),
                        'venue_state': venue.get('address', {}).get('state', ''),
                        'is_dome': self._is_dome_stadium(venue_name),
                        'broadcast': self._get_broadcast(competition),
                        'home': home_team,
                        'away': away_team,
                        'week': event.get('week', {}).get('number', ''),
                    })

            return games

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=1)

    def get_injuries(self, team_id: str) -> List[Dict]:
        """NCAAF doesn't have detailed injury data"""
        return []

    def get_last_5_games(self, team_id: str) -> List[Dict]:
        """Get results of last 5 games"""
        cache_key = f"ncaaf_last5_{team_id}"

        def fetch():
            url = f"https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams/{team_id}/schedule"
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

            return games[-5:][::-1]

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)


class NCAABFetcher(BaseFetcher):
    """NCAAB data fetcher"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/{team_id}/statistics'
    ESPN_STANDINGS = 'https://site.web.api.espn.com/apis/v2/sports/basketball/mens-college-basketball/standings'

    _standings_cache = None

    @property
    def sport_name(self) -> str:
        return 'NCAAB'

    def _get_standings_data(self) -> Dict:
        """Get standings data with avgPointsFor, avgPointsAgainst, etc."""
        if NCAABFetcher._standings_cache is not None:
            return NCAABFetcher._standings_cache

        cache_key = f"ncaab_standings_{datetime.now().strftime('%Y-%m-%d')}"

        def fetch():
            data = self._safe_request(self.ESPN_STANDINGS)
            if not data:
                return {}

            standings = {}
            # Handle conference-based structure
            children = data.get('children', [])
            for conference in children:
                entries = conference.get('standings', {}).get('entries', [])
                for entry in entries:
                    team = entry.get('team', {})
                    team_id = str(team.get('id', ''))
                    team_name = team.get('displayName', '')
                    stats = {s.get('name'): s.get('value', s.get('displayValue', 0)) for s in entry.get('stats', [])}
                    standings[team_id] = stats
                    standings[team_name] = stats  # Also key by name

            return standings

        result = self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)
        NCAABFetcher._standings_cache = result
        return result

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's NCAAB games"""
        cache_key = f"ncaab_games_{datetime.now().strftime('%Y-%m-%d')}"

        def fetch():
            data = self._safe_request(self.ESPN_SCOREBOARD)
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
                    games.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'date': event.get('date'),
                        'status': event.get('status', {}).get('type', {}).get('description', ''),
                        'venue': competition.get('venue', {}).get('fullName', ''),
                        'broadcast': self._get_broadcast(competition),
                        'home': home_team,
                        'away': away_team,
                    })

            return games

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=1)

    def _extract_team_data(self, comp: Dict) -> Dict:
        """Extract team data"""
        team = comp.get('team', {})
        records = comp.get('records', [])

        team_data = {
            'id': team.get('id'),
            'name': team.get('displayName', ''),
            'abbreviation': team.get('abbreviation', ''),
            'logo': team.get('logo', ''),
            'record': '',
            'home_record': '',
            'away_record': '',
            'conf_record': '',
        }

        for rec in records:
            rec_type = rec.get('type', '')
            rec_name = rec.get('name', '').lower()
            summary = rec.get('summary', '')

            if rec_type == 'total' or rec_name == 'overall':
                team_data['record'] = summary
            elif rec_type == 'home':
                team_data['home_record'] = summary
            elif rec_type == 'road':
                team_data['away_record'] = summary
            elif 'conference' in rec_name:
                team_data['conf_record'] = summary

        return team_data

    def _get_broadcast(self, competition: Dict) -> str:
        """Get broadcast info"""
        broadcasts = competition.get('broadcasts', [])
        if broadcasts:
            names = [b.get('names', [''])[0] for b in broadcasts if b.get('names')]
            return ', '.join(names[:2])
        return ''

    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch basic team statistics merged with standings data"""
        if not team_id:
            return {}

        cache_key = f"ncaab_stats_{team_id}"

        def fetch():
            url = self.ESPN_TEAM_STATS.format(team_id=team_id)
            data = self._safe_request(url)

            stats = {}
            if data:
                # ESPN API returns data at results.stats.categories
                categories = data.get('results', {}).get('stats', {}).get('categories', [])
                if not categories:
                    # Fallback to old structure
                    categories = data.get('splits', {}).get('categories', [])

                for stat_group in categories:
                    for stat in stat_group.get('stats', []):
                        name = stat.get('name', '')
                        value = stat.get('displayValue', stat.get('value', 'N/A'))
                        stats[name] = value

            # Merge with standings data for avgPointsAgainst, differential, etc.
            standings = self._get_standings_data()
            team_standings = standings.get(str(team_id), {})

            # Add standings stats that aren't in team stats
            if team_standings:
                for key in ['avgPointsFor', 'avgPointsAgainst', 'pointDifferential', 'differential', 'wins', 'losses']:
                    if key in team_standings and key not in stats:
                        stats[key] = team_standings[key]
                # Map common aliases
                if 'avgPointsAgainst' not in stats and 'avgPointsAgainst' in team_standings:
                    stats['avgPointsAgainst'] = team_standings['avgPointsAgainst']
                if 'avgPointsFor' not in stats and 'avgPointsFor' in team_standings:
                    stats['avgPointsFor'] = team_standings['avgPointsFor']
                    if 'avgPoints' not in stats:
                        stats['avgPoints'] = team_standings['avgPointsFor']
                # Point differential
                if 'pointDifferential' in team_standings:
                    stats['point_diff'] = team_standings['pointDifferential']
                elif 'differential' in team_standings:
                    stats['point_diff'] = team_standings['differential']

            return stats

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def get_advanced_stats(self, team_id: str) -> Dict:
        """Calculate advanced stats (similar to NBA)"""
        if not team_id:
            return {}

        cache_key = f"ncaab_advanced_{team_id}"

        def fetch():
            basic = self.get_team_stats(team_id)  # Now includes standings data

            # Get PPG - try multiple keys
            ppg = self._parse_stat(basic.get('avgPoints',
                   basic.get('avgPointsFor',
                   basic.get('pointsPerGame', 72))))

            # Get opponent PPG from standings data
            opp_ppg = self._parse_stat(basic.get('avgPointsAgainst',
                      basic.get('oppPointsPerGame', 70)))

            # Get point differential directly or calculate it
            point_diff = self._parse_stat(basic.get('point_diff',
                         basic.get('pointDifferential',
                         basic.get('differential', ppg - opp_ppg))))

            # Shooting percentages
            fg_pct = self._parse_stat(basic.get('avgFieldGoalPct',
                     basic.get('fieldGoalPct', 44)))
            fg3_pct = self._parse_stat(basic.get('avgThreePointPct',
                      basic.get('threePointPct', 34)))
            ft_pct = self._parse_stat(basic.get('avgFreeThrowPct',
                     basic.get('freeThrowPct', 70)))

            # Rebounds
            rpg = self._parse_stat(basic.get('avgRebounds',
                  basic.get('reboundsPerGame', 35)))

            # Assists and turnovers
            apg = self._parse_stat(basic.get('avgAssists',
                  basic.get('assistsPerGame', 13)))
            topg = self._parse_stat(basic.get('avgTurnovers',
                   basic.get('turnoversPerGame', 12)))

            return {
                'ppg': round(ppg, 1),
                'opp_ppg': round(opp_ppg, 1),
                'point_diff': round(point_diff, 1),
                'fg_pct': round(fg_pct, 1),
                'three_pct': round(fg3_pct, 1),
                'ft_pct': round(ft_pct, 1),
                'rpg': round(rpg, 1),
                'apg': round(apg, 1),
                'topg': round(topg, 1),
            }

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def _parse_stat(self, value, default=0) -> float:
        """Parse stat value"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('%', ''))
            except:
                return default
        return default

    def get_injuries(self, team_id: str) -> List[Dict]:
        """NCAAB doesn't have detailed injury data"""
        return []

    def get_complete_game_data(self, game: Dict) -> Dict:
        """Get comprehensive data for a single NCAAB game"""
        return super().get_complete_game_data(game)
