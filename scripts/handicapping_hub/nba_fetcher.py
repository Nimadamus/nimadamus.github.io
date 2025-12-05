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
        today = datetime.now().strftime('%Y%m%d')
        cache_key = f"nba_games_{today}"

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
                        value = stat.get('value', stat.get('displayValue', '-'))
                        stats[name] = value

            # Get statistics from team stats endpoint
            stats_data = team.get('statistics', [])
            for stat_group in stats_data:
                for stat in stat_group.get('stats', []):
                    name = stat.get('name', stat.get('abbreviation', ''))
                    value = stat.get('value', stat.get('displayValue', '-'))
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

    # ESPN team ID to NBA Stats team name mapping
    ESPN_TO_NBA_TEAM = {
        '1': 'Atlanta Hawks',
        '2': 'Boston Celtics',
        '17': 'Brooklyn Nets',
        '30': 'Charlotte Hornets',
        '4': 'Chicago Bulls',
        '5': 'Cleveland Cavaliers',
        '6': 'Dallas Mavericks',
        '7': 'Denver Nuggets',
        '8': 'Detroit Pistons',
        '9': 'Golden State Warriors',
        '10': 'Houston Rockets',
        '11': 'Indiana Pacers',
        '12': 'LA Clippers',
        '13': 'Los Angeles Lakers',
        '29': 'Memphis Grizzlies',
        '14': 'Miami Heat',
        '15': 'Milwaukee Bucks',
        '16': 'Minnesota Timberwolves',
        '3': 'New Orleans Pelicans',
        '18': 'New York Knicks',
        '25': 'Oklahoma City Thunder',
        '19': 'Orlando Magic',
        '20': 'Philadelphia 76ers',
        '21': 'Phoenix Suns',
        '22': 'Portland Trail Blazers',
        '23': 'Sacramento Kings',
        '24': 'San Antonio Spurs',
        '28': 'Toronto Raptors',
        '26': 'Utah Jazz',
        '27': 'Washington Wizards',
    }

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
                'Rank': 'N',
                'Season': season,
                'SeasonSegment': '',
                'SeasonType': 'Regular Season',
                'TeamID': '0',
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

            # Get expected team name from ESPN ID
            expected_team = self.ESPN_TO_NBA_TEAM.get(str(team_id), '')
            team_name_idx = headers_list.index('TEAM_NAME') if 'TEAM_NAME' in headers_list else 1

            for row in rows:
                team_name = row[team_name_idx] if team_name_idx < len(row) else ''
                if expected_team and expected_team.lower() in team_name.lower():
                    return self._parse_nba_stats_row(headers_list, row)

            return None

        except Exception as e:
            return None

    def _parse_nba_stats_row(self, headers: List, row: List) -> Dict:
        """Parse NBA Stats API row into dict"""
        stats = {}

        # Create index map for faster lookup
        header_map = {h: i for i, h in enumerate(headers)}

        # Key stats to extract
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
            'AST_PCT': 'ast_pct',
        }

        # Rank fields
        rank_mappings = {
            'OFF_RATING_RANK': 'off_rating_rank',
            'DEF_RATING_RANK': 'def_rating_rank',
            'NET_RATING_RANK': 'net_rating_rank',
            'PACE_RANK': 'pace_rank',
        }

        for header, key in key_mappings.items():
            idx = header_map.get(header)
            if idx is not None and idx < len(row):
                value = row[idx]
                if isinstance(value, (int, float)):
                    # Convert percentages (0.549 -> 54.9%)
                    if 'PCT' in header:
                        stats[key] = round(value * 100, 1)
                    else:
                        stats[key] = round(value, 1)
                else:
                    stats[key] = value

        for header, key in rank_mappings.items():
            idx = header_map.get(header)
            if idx is not None and idx < len(row):
                stats[key] = int(row[idx]) if row[idx] else None

        stats['from_nba_stats'] = True
        return stats

    def _calculate_advanced_from_basic(self, team_id: str) -> Dict:
        """Calculate advanced stats from basic ESPN data"""
        basic_stats = self.get_team_stats(team_id)

        # Extract values - use avgPointsFor instead of avgPoints
        ppg = self._parse_stat(basic_stats.get('avgPointsFor', basic_stats.get('avgPoints', 0)))
        opp_ppg = self._parse_stat(basic_stats.get('avgPointsAgainst', 0))
        diff = self._parse_stat(basic_stats.get('differential', 0))

        # If we have no real data, return N/A values
        if ppg == 0 and opp_ppg == 0:
            return self._default_advanced_stats()

        # Use differential directly if available
        if diff == 0 and ppg > 0 and opp_ppg > 0:
            diff = ppg - opp_ppg

        # Estimate pace based on points (NBA average is about 100 possessions)
        avg_points = (ppg + opp_ppg) / 2
        poss = avg_points / 1.1  # Rough estimate

        # Calculate metrics using actual team data
        ortg = (ppg / max(poss, 1)) * 100 if poss > 0 else ppg
        drtg = (opp_ppg / max(poss, 1)) * 100 if poss > 0 else opp_ppg

        return {
            'offensive_rating': round(ortg, 1),
            'defensive_rating': round(drtg, 1),
            'net_rating': round(diff, 1),  # Use actual differential from ESPN
            'pace': round(poss, 1),
            'efg_pct': '-',  # Need more detailed stats
            'ts_pct': '-',   # Need more detailed stats
            'ast_ratio': '-',
            'tov_pct': '-',
            'oreb_pct': '-',
            'dreb_pct': '-',
            'ppg': round(ppg, 1),
            'opp_ppg': round(opp_ppg, 1),
            'calculated': True,
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
                                'return_date': injury_data.get('details', {}).get('fantasyStatus', {}).get('description', ''),
                            })
                except Exception as e:
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
            'ats_overall': '-',
            'ats_home': '-',
            'ats_away': '-',
            'ats_favorite': '-',
            'ats_underdog': '-',
            'ou_overall': '-',
            'ou_over_pct': '-',
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
            'avgPoints': '-',
            'avgFieldGoalPct': '-',
            'avgThreePointPct': '-',
            'avgFreeThrowPct': '-',
            'avgRebounds': '-',
            'avgAssists': '-',
            'avgSteals': '-',
            'avgBlocks': '-',
            'avgTurnovers': '-',
        }

    def _default_advanced_stats(self) -> Dict:
        return {
            'offensive_rating': '-',
            'defensive_rating': '-',
            'net_rating': '-',
            'pace': '-',
            'efg_pct': '-',
            'ts_pct': '-',
            'ast_ratio': '-',
            'tov_pct': '-',
            'oreb_pct': '-',
            'dreb_pct': '-',
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
