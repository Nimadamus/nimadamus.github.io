"""
NBA DATA FETCHER
================
Comprehensive NBA data including advanced analytics.

Data Sources:
- ESPN API: Schedules, basic stats, injuries
- NBA Stats API: Advanced metrics (ORTG, DRTG, pace, eFG%)

Advanced Stats Included:
- Offensive Rating (points per 100 possessions)
- Defensive Rating (points allowed per 100 possessions)
- Net Rating (ORTG - DRTG)
- Pace Factor (possessions per game)
- Effective FG% (eFG%)
- True Shooting % (TS%)
- Assist Ratio
- Turnover Ratio
- Rebound Rate (ORB%, DRB%)
- ATS Records
- Last 10 games performance
"""

from typing import Dict, List, Optional
from datetime import datetime
import re

from .base_fetcher import BaseFetcher


class NBAFetcher(BaseFetcher):
    """NBA data fetcher with advanced analytics"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/statistics'
    ESPN_INJURIES = 'https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/teams/{team_id}/injuries'
    NBA_STATS_TEAM = 'https://stats.nba.com/stats/leaguedashteamstats'

    @property
    def sport_name(self) -> str:
        return 'NBA'

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's NBA games"""
        cache_key = f"nba_games_{datetime.now().strftime('%Y-%m-%d')}"

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
        """Extract comprehensive team data from ESPN competitor"""
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
            'conf_record': '',
            'ats_record': '',
            'ou_record': '',
            'streak': '',
            'last_10': '',
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
        """Fetch basic team statistics from ESPN team page"""
        if not team_id:
            return self._default_stats()

        cache_key = f"nba_stats_{team_id}"

        def fetch():
            # Try the team endpoint which has stats
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
            data = self._safe_request(url)
            if not data:
                return self._default_stats()

            team = data.get('team', {})
            stats = {}

            # Get record info
            record = team.get('record', {})
            items = record.get('items', [])
            for item in items:
                if item.get('type') == 'total':
                    for stat in item.get('stats', []):
                        name = stat.get('name', '')
                        value = stat.get('value', stat.get('displayValue', 'N/A'))
                        stats[name] = value

            # Get statistics from team stats endpoint
            stats_data = team.get('statistics', [])
            for stat_group in stats_data:
                for stat in stat_group.get('stats', []):
                    name = stat.get('name', stat.get('abbreviation', ''))
                    value = stat.get('value', stat.get('displayValue', 'N/A'))
                    stats[name] = value

            # Also try to get stats from next statistics
            next_stats = team.get('nextEvent', [{}])[0] if team.get('nextEvent') else {}

            if not stats:
                return self._default_stats()

            return stats

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def get_advanced_stats(self, team_id: str) -> Dict:
        """
        Fetch advanced NBA analytics.
        Uses NBA Stats API for detailed metrics.
        """
        if not team_id:
            return self._default_advanced_stats()

        cache_key = f"nba_advanced_{team_id}"

        def fetch():
            # Try NBA Stats API first
            advanced = self._fetch_nba_stats_api(team_id)
            if advanced:
                return advanced

            # Fallback to calculated stats from ESPN data
            return self._calculate_advanced_from_basic(team_id)

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def _fetch_nba_stats_api(self, team_id: str) -> Optional[Dict]:
        """Fetch from official NBA Stats API"""
        try:
            # NBA Stats API requires specific headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.nba.com',
                'Referer': 'https://www.nba.com/',
                'x-nba-stats-origin': 'stats',
                'x-nba-stats-token': 'true',
            }

            # Get current season
            now = datetime.now()
            if now.month >= 10:
                season = f"{now.year}-{str(now.year + 1)[2:]}"
            else:
                season = f"{now.year - 1}-{str(now.year)[2:]}"

            params = {
                'Conference': '',
                'DateFrom': '',
                'DateTo': '',
                'Division': '',
                'GameScope': '',
                'GameSegment': '',
                'Height': '',
                'LastNGames': '0',
                'LeagueID': '00',
                'Location': '',
                'MeasureType': 'Advanced',
                'Month': '0',
                'OpponentTeamID': '0',
                'Outcome': '',
                'PORound': '0',
                'PaceAdjust': 'N',
                'PerMode': 'PerGame',
                'Period': '0',
                'PlayerExperience': '',
                'PlayerPosition': '',
                'PlusMinus': 'N',
                'Rank': 'N',
                'Season': season,
                'SeasonSegment': '',
                'SeasonType': 'Regular Season',
                'ShotClockRange': '',
                'StarterBench': '',
                'TeamID': '0',
                'TwoWay': '0',
                'VsConference': '',
                'VsDivision': '',
            }

            response = self.session.get(
                self.NBA_STATS_TEAM,
                params=params,
                headers=headers,
                timeout=15
            )

            if response.status_code != 200:
                return None

            data = response.json()

            # Parse NBA Stats response format
            result_set = data.get('resultSets', [{}])[0]
            headers_list = result_set.get('headers', [])
            rows = result_set.get('rowSet', [])

            # Find team in results
            team_id_idx = headers_list.index('TEAM_ID') if 'TEAM_ID' in headers_list else -1

            for row in rows:
                if team_id_idx >= 0 and str(row[team_id_idx]) == str(team_id):
                    return self._parse_nba_stats_row(headers_list, row)

            return None

        except Exception as e:
            return None

    def _parse_nba_stats_row(self, headers: List, row: List) -> Dict:
        """Parse NBA Stats API row into dict"""
        stats = {}
        key_mappings = {
            'OFF_RATING': 'offensive_rating',
            'DEF_RATING': 'defensive_rating',
            'NET_RATING': 'net_rating',
            'PACE': 'pace',
            'EFG_PCT': 'efg_pct',
            'TS_PCT': 'ts_pct',
            'AST_RATIO': 'ast_ratio',
            'AST_TO': 'ast_to_ratio',
            'OREB_PCT': 'oreb_pct',
            'DREB_PCT': 'dreb_pct',
            'REB_PCT': 'reb_pct',
            'TM_TOV_PCT': 'tov_pct',
            'PIE': 'pie',
        }

        for i, header in enumerate(headers):
            if header in key_mappings and i < len(row):
                value = row[i]
                if isinstance(value, float):
                    if 'PCT' in header or 'RATIO' in header:
                        stats[key_mappings[header]] = round(value * 100, 1) if value < 1 else round(value, 1)
                    else:
                        stats[key_mappings[header]] = round(value, 1)
                else:
                    stats[key_mappings[header]] = value

        return stats

    def _calculate_advanced_from_basic(self, team_id: str) -> Dict:
        """Calculate advanced stats from basic ESPN data"""
        basic_stats = self.get_team_stats(team_id)

        # Extract values
        ppg = self._parse_stat(basic_stats.get('avgPoints', 0))
        opp_ppg = self._parse_stat(basic_stats.get('avgPointsAgainst', ppg - 2))
        fgm = self._parse_stat(basic_stats.get('avgFieldGoalsMade', 40))
        fga = self._parse_stat(basic_stats.get('avgFieldGoalsAttempted', 88))
        fg3m = self._parse_stat(basic_stats.get('avgThreePointFieldGoalsMade', 12))
        fta = self._parse_stat(basic_stats.get('avgFreeThrowsAttempted', 22))
        ftm = self._parse_stat(basic_stats.get('avgFreeThrowsMade', 17))
        orb = self._parse_stat(basic_stats.get('avgOffensiveRebounds', 10))
        drb = self._parse_stat(basic_stats.get('avgDefensiveRebounds', 34))
        tov = self._parse_stat(basic_stats.get('avgTurnovers', 14))
        ast = self._parse_stat(basic_stats.get('avgAssists', 25))

        # Calculate possession estimate
        poss = 0.96 * (fga + tov + 0.44 * fta - orb)

        # Calculate advanced metrics
        efg_pct = ((fgm + 0.5 * fg3m) / max(fga, 1)) * 100 if fga > 0 else 0
        ts_pct = (ppg / (2 * (fga + 0.44 * fta))) * 100 if (fga + fta) > 0 else 0
        ortg = (ppg / max(poss, 1)) * 100 if poss > 0 else ppg
        ast_ratio = (ast / max(poss, 1)) * 100 if poss > 0 else 0
        tov_pct = (tov / max(poss, 1)) * 100 if poss > 0 else 0

        return {
            'offensive_rating': round(ortg, 1),
            'defensive_rating': round((opp_ppg / max(poss, 1)) * 100, 1) if poss > 0 else opp_ppg,
            'net_rating': round(ortg - ((opp_ppg / max(poss, 1)) * 100), 1) if poss > 0 else round(ppg - opp_ppg, 1),
            'pace': round(poss, 1),
            'efg_pct': round(efg_pct, 1),
            'ts_pct': round(ts_pct, 1),
            'ast_ratio': round(ast_ratio, 1),
            'tov_pct': round(tov_pct, 1),
            'oreb_pct': round((orb / (orb + 34)) * 100, 1),  # Estimate
            'dreb_pct': round((drb / (drb + 10)) * 100, 1),  # Estimate
            'calculated': True,  # Flag that these are estimates
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
        """Fetch injury report for team"""
        if not team_id:
            return []

        cache_key = f"nba_injuries_{team_id}"

        def fetch():
            url = self.ESPN_INJURIES.format(team_id=team_id)
            data = self._safe_request(url)
            if not data:
                return []

            injuries = []
            for item in data.get('items', [])[:8]:
                try:
                    player_ref = item.get('athlete', {}).get('$ref', '')
                    if player_ref:
                        player_data = self._safe_request(player_ref)
                        if player_data:
                            injuries.append({
                                'name': player_data.get('displayName', 'Unknown'),
                                'position': player_data.get('position', {}).get('abbreviation', ''),
                                'injury': item.get('type', {}).get('description', item.get('details', {}).get('type', 'Unknown')),
                                'status': item.get('status', 'Unknown'),
                                'return_date': item.get('details', {}).get('fantasyStatus', {}).get('description', ''),
                            })
                except:
                    continue

            return injuries

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=3)

    def get_ats_records(self, team_id: str) -> Dict:
        """
        Get Against The Spread records.
        This requires external data sources or manual tracking.
        """
        # Placeholder - would need Covers.com scraping or paid API
        return {
            'ats_overall': 'N/A',
            'ats_home': 'N/A',
            'ats_away': 'N/A',
            'ats_favorite': 'N/A',
            'ats_underdog': 'N/A',
            'ou_overall': 'N/A',
            'ou_over_pct': 'N/A',
        }

    def get_last_10_games(self, team_id: str) -> List[Dict]:
        """Get results of last 10 games"""
        cache_key = f"nba_last10_{team_id}"

        def fetch():
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/schedule"
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
                                'opponent': self._get_opponent_name(competitors, team_id),
                                'result': 'W' if c.get('winner') else 'L',
                                'score': c.get('score', ''),
                                'home': c.get('homeAway') == 'home',
                            })

            return games[-10:][::-1]  # Last 10, most recent first

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def _get_opponent_name(self, competitors: List, team_id: str) -> str:
        """Get opponent name from competitors"""
        for c in competitors:
            if c.get('team', {}).get('id') != team_id:
                return c.get('team', {}).get('abbreviation', '')
        return ''

    def _default_stats(self) -> Dict:
        return {
            'avgPoints': 'N/A',
            'avgFieldGoalPct': 'N/A',
            'avgThreePointPct': 'N/A',
            'avgFreeThrowPct': 'N/A',
            'avgRebounds': 'N/A',
            'avgAssists': 'N/A',
            'avgSteals': 'N/A',
            'avgBlocks': 'N/A',
            'avgTurnovers': 'N/A',
        }

    def _default_advanced_stats(self) -> Dict:
        return {
            'offensive_rating': 'N/A',
            'defensive_rating': 'N/A',
            'net_rating': 'N/A',
            'pace': 'N/A',
            'efg_pct': 'N/A',
            'ts_pct': 'N/A',
            'ast_ratio': 'N/A',
            'tov_pct': 'N/A',
            'oreb_pct': 'N/A',
            'dreb_pct': 'N/A',
        }

    def get_complete_game_data(self, game: Dict) -> Dict:
        """Get comprehensive data for a single NBA game"""
        base_data = super().get_complete_game_data(game)

        # Add NBA-specific data
        away_id = game.get('away', {}).get('id')
        home_id = game.get('home', {}).get('id')

        base_data.update({
            'away_last10': self.get_last_10_games(away_id) if away_id else [],
            'home_last10': self.get_last_10_games(home_id) if home_id else [],
            'away_ats': self.get_ats_records(away_id) if away_id else {},
            'home_ats': self.get_ats_records(home_id) if home_id else {},
        })

        return base_data
