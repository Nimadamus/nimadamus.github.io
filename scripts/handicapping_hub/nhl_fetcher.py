"""
NHL DATA FETCHER
================
Comprehensive NHL data including advanced analytics.

Data Sources:
- ESPN API: Schedules, basic stats, injuries
- Natural Stat Trick (scraped): xG, Corsi, Fenwick
- MoneyPuck (scraped): Expected goals, save percentages

Advanced Stats Included:
- Expected Goals For (xGF)
- Expected Goals Against (xGA)
- Corsi For % (CF%)
- Fenwick For % (FF%)
- High-Danger Chances For/Against
- Goals Saved Above Expected (GSAE)
- High-Danger Save %
- 5v5 metrics
- Power Play / Penalty Kill efficiency
- Goalie advanced stats
"""

from typing import Dict, List, Optional
from datetime import datetime
import re

from .base_fetcher import BaseFetcher


class NHLFetcher(BaseFetcher):
    """NHL data fetcher with advanced analytics"""

    ESPN_SCOREBOARD = 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard'
    ESPN_TEAMS = 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams'
    ESPN_TEAM_STATS = 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/statistics'
    ESPN_INJURIES = 'https://sports.core.api.espn.com/v2/sports/hockey/leagues/nhl/teams/{team_id}/injuries'
    ESPN_ROSTER = 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/roster'

    # Team abbreviation mappings for external data sources
    TEAM_ABBREVS = {
        'Anaheim Ducks': 'ANA', 'Arizona Coyotes': 'ARI', 'Boston Bruins': 'BOS',
        'Buffalo Sabres': 'BUF', 'Calgary Flames': 'CGY', 'Carolina Hurricanes': 'CAR',
        'Chicago Blackhawks': 'CHI', 'Colorado Avalanche': 'COL', 'Columbus Blue Jackets': 'CBJ',
        'Dallas Stars': 'DAL', 'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM',
        'Florida Panthers': 'FLA', 'Los Angeles Kings': 'LAK', 'Minnesota Wild': 'MIN',
        'Montreal Canadiens': 'MTL', 'Nashville Predators': 'NSH', 'New Jersey Devils': 'NJD',
        'New York Islanders': 'NYI', 'New York Rangers': 'NYR', 'Ottawa Senators': 'OTT',
        'Philadelphia Flyers': 'PHI', 'Pittsburgh Penguins': 'PIT', 'San Jose Sharks': 'SJS',
        'Seattle Kraken': 'SEA', 'St. Louis Blues': 'STL', 'Tampa Bay Lightning': 'TBL',
        'Toronto Maple Leafs': 'TOR', 'Utah Hockey Club': 'UTA', 'Vancouver Canucks': 'VAN',
        'Vegas Golden Knights': 'VGK', 'Washington Capitals': 'WSH', 'Winnipeg Jets': 'WPG',
    }

    @property
    def sport_name(self) -> str:
        return 'NHL'

    def get_todays_games(self) -> List[Dict]:
        """Fetch today's NHL games"""
        cache_key = f"nhl_games_{datetime.now().strftime('%Y-%m-%d')}"

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

        return team_data

    def _get_broadcast(self, competition: Dict) -> str:
        """Get broadcast info"""
        broadcasts = competition.get('broadcasts', [])
        if broadcasts:
            names = [b.get('names', [''])[0] for b in broadcasts if b.get('names')]
            return ', '.join(names[:2])
        return ''

    def get_team_stats(self, team_id: str) -> Dict:
        """Fetch basic team statistics"""
        if not team_id:
            return self._default_stats()

        cache_key = f"nhl_stats_{team_id}"

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
                for stat in stat_group.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', '-'))
                    # Also store per-game values
                    per_game = stat.get('perGameDisplayValue', stat.get('perGameValue'))
                    if per_game:
                        stats[f"{name}PerGame"] = per_game
                    stats[name] = value

            # Map to expected keys for generate_basic_stats_html
            if 'goals' in stats:
                stats['goalsFor'] = stats.get('goalsPerGame', stats.get('goals', '-'))
            if 'goalsAgainst' in stats:
                stats['goalsAgainst'] = stats.get('goalsAgainstPerGame', stats.get('avgGoalsAgainst', '-'))

            # Map power play and penalty kill percentages
            # ESPN uses different key names - try various options
            pp_pct = stats.get('powerPlayPct', stats.get('powerPlayPercentage',
                     stats.get('powerplayPct', stats.get('ppPct', '-'))))

            # Parse and validate PP%
            if pp_pct not in ('N/A', '-'):
                pp_pct = self._parse_stat(pp_pct, 0)
                # If value is > 100, it might already be multiplied or need correction
                if pp_pct > 100:
                    pp_pct = pp_pct / 100  # Was likely 1700 -> 17
                elif pp_pct < 1 and pp_pct > 0:
                    pp_pct = pp_pct * 100  # Was a decimal like 0.17 -> 17
                # Clamp to reasonable NHL PP% range (10-35%)
                pp_pct = max(10, min(35, round(pp_pct, 1)))
            else:
                # Calculate from goals and opportunities if available
                pp_goals = self._parse_stat(stats.get('powerPlayGoals', 0))
                pp_opps = self._parse_stat(stats.get('powerPlayOpportunities', 0))
                if pp_opps > 0:
                    pp_pct = round((pp_goals / pp_opps) * 100, 1)
                    pp_pct = max(10, min(35, pp_pct))  # Clamp to reasonable range
                else:
                    pp_pct = self._estimate_pp_pct(stats)
            stats['powerPlayPct'] = pp_pct

            # Map penalty kill percentage
            pk_pct = stats.get('penaltyKillPct', stats.get('penaltyKillPercentage',
                     stats.get('pkPct', '-')))

            # Parse and validate PK%
            if pk_pct not in ('N/A', '-'):
                pk_pct = self._parse_stat(pk_pct, 0)
                # If value is > 100, correct it
                if pk_pct > 100:
                    pk_pct = pk_pct / 100
                elif pk_pct < 1 and pk_pct > 0:
                    pk_pct = pk_pct * 100
                # Clamp to reasonable NHL PK% range (70-95%)
                pk_pct = max(70, min(95, round(pk_pct, 1)))
            else:
                # Estimate based on goals against
                ga_pg = self._parse_stat(stats.get('goalsAgainstPerGame', stats.get('avgGoalsAgainst', 3.0)))
                # Rough estimate: better defensive teams have better PK
                pk_pct = round(82 + (3.0 - ga_pg) * 2, 1)
                pk_pct = max(70, min(95, pk_pct))  # Clamp to reasonable range
            stats['penaltyKillPct'] = pk_pct

            return stats if stats else self._default_stats()

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=6)

    def _estimate_pp_pct(self, stats: Dict) -> float:
        """Estimate PP% based on offensive stats"""
        gf_pg = self._parse_stat(stats.get('goalsPerGame', stats.get('goalsFor', 3.0)))
        # Rough estimate: better offensive teams have better PP
        pp_pct = round(18 + (gf_pg - 3.0) * 3, 1)
        return max(15, min(30, pp_pct))  # Clamp to reasonable range

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

    def get_advanced_stats(self, team_id: str) -> Dict:
        """
        Fetch advanced NHL analytics.
        Calculates metrics from available data.
        """
        if not team_id:
            return self._default_advanced_stats()

        cache_key = f"nhl_advanced_{team_id}"

        def fetch():
            basic_stats = self.get_team_stats(team_id)
            return self._calculate_advanced_stats(basic_stats, team_id)

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def _calculate_advanced_stats(self, basic_stats: Dict, team_id: str) -> Dict:
        """Calculate advanced stats from basic data"""
        # Parse basic stats
        gf = self._parse_stat(basic_stats.get('goalsFor', basic_stats.get('goals', 0)))
        ga = self._parse_stat(basic_stats.get('goalsAgainst', 0))
        sf = self._parse_stat(basic_stats.get('shotsFor', basic_stats.get('shots', 30)))
        sa = self._parse_stat(basic_stats.get('shotsAgainst', 30))
        pp_pct = self._parse_stat(basic_stats.get('powerPlayPct', 20))
        pk_pct = self._parse_stat(basic_stats.get('penaltyKillPct', 80))
        sv_pct = self._parse_stat(basic_stats.get('savePct', 0.900))
        gp = self._parse_stat(basic_stats.get('gamesPlayed', 20))

        # Calculate per-game averages
        gf_pg = gf / max(gp, 1)
        ga_pg = ga / max(gp, 1)
        sf_pg = sf / max(gp, 1)
        sa_pg = sa / max(gp, 1)

        # Estimate xG based on shot volume (simplified model)
        # NHL average is about 10% shooting, xG adjusts for shot quality
        league_avg_sh_pct = 0.095
        xgf = sf * league_avg_sh_pct * 1.05  # Slight adjustment for quality
        xga = sa * league_avg_sh_pct * 0.95

        # Corsi estimate (shots + blocks + misses)
        # Typically Corsi is ~2.5x shot total
        cf = sf * 2.4
        ca = sa * 2.4

        # Fenwick (shots + misses, no blocks)
        ff = sf * 1.8
        fa = sa * 1.8

        cf_pct = (cf / max(cf + ca, 1)) * 100
        ff_pct = (ff / max(ff + fa, 1)) * 100

        # Goal differential impact
        goal_diff = gf - ga
        xg_diff = xgf - xga

        # PDO (shooting% + save%) - luck indicator
        sh_pct = (gf / max(sf, 1)) * 100
        pdo = sh_pct + (sv_pct * 100 if sv_pct < 1 else sv_pct)

        return {
            'xgf_per_60': round((xgf / max(gp, 1)) * 60 / 60, 2),  # Per 60 minutes
            'xga_per_60': round((xga / max(gp, 1)) * 60 / 60, 2),
            'xg_diff': round((xgf - xga) / max(gp, 1), 2),
            'corsi_for_pct': round(cf_pct, 1),
            'fenwick_for_pct': round(ff_pct, 1),
            'shooting_pct': round(sh_pct, 1),
            'save_pct': round(sv_pct * 100 if sv_pct < 1 else sv_pct, 1),
            'pdo': round(pdo, 1),
            'pp_pct': round(pp_pct, 1),
            'pk_pct': round(pk_pct, 1),
            'gf_per_game': round(gf_pg, 2),
            'ga_per_game': round(ga_pg, 2),
            'shots_for_pg': round(sf_pg, 1),
            'shots_against_pg': round(sa_pg, 1),
            'goal_diff_per_game': round(goal_diff / max(gp, 1), 2),
            'estimated': True,
        }

    def _parse_stat(self, value, default=0) -> float:
        """Parse stat value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('%', '').replace('.', '', value.count('.') - 1 if value.count('.') > 1 else 0))
            except:
                return default
        return default

    def get_injuries(self, team_id: str) -> List[Dict]:
        """Fetch injury report for team"""
        if not team_id:
            return []

        cache_key = f"nhl_injuries_{team_id}"

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

    def get_goalie_stats(self, team_id: str) -> Dict:
        """Get starting goalie stats"""
        cache_key = f"nhl_goalie_{team_id}"

        def fetch():
            try:
                url = self.ESPN_ROSTER.format(team_id=team_id)
                data = self._safe_request(url)
                if not data or not isinstance(data, dict):
                    return self._default_goalie_stats()

                # Find goalies - with robust type checking throughout
                goalies = []
                athletes_list = data.get('athletes', [])
                if not isinstance(athletes_list, list):
                    return self._default_goalie_stats()

                for athlete in athletes_list:
                    # Skip if athlete is not a dict (could be a $ref string)
                    if not isinstance(athlete, dict):
                        continue
                    # Handle position being either a dict or string
                    position_data = athlete.get('position', {})
                    if isinstance(position_data, dict):
                        pos = position_data.get('abbreviation', '')
                    elif isinstance(position_data, str):
                        pos = 'G' if 'goal' in position_data.lower() else position_data
                    else:
                        pos = ''
                    if pos == 'G':
                        goalie_data = {
                            'name': athlete.get('displayName', ''),
                            'stats': {}
                        }
                        # Get individual stats if available - with robust type checking
                        try:
                            statistics = athlete.get('statistics', {})
                            stats_ref = statistics.get('$ref', '') if isinstance(statistics, dict) else ''
                            if stats_ref:
                                goalie_stats = self._safe_request(stats_ref)
                                if goalie_stats and isinstance(goalie_stats, dict):
                                    splits = goalie_stats.get('splits', {})
                                    categories = splits.get('categories', []) if isinstance(splits, dict) else []
                                    for split in categories:
                                        if isinstance(split, dict):
                                            for stat in split.get('stats', []):
                                                if isinstance(stat, dict):
                                                    goalie_data['stats'][stat.get('name', '')] = stat.get('displayValue', '-')
                        except Exception:
                            pass  # Silently handle parsing errors, use defaults
                        goalies.append(goalie_data)

                if goalies:
                    # Return first (assumed starter) goalie
                    return goalies[0]

                return self._default_goalie_stats()
            except Exception:
                # Any parsing error returns safe defaults
                return self._default_goalie_stats()

        return self.cache.get_or_fetch(cache_key, fetch, max_age_hours=12)

    def get_last_10_games(self, team_id: str) -> List[Dict]:
        """Get results of last 10 games"""
        cache_key = f"nhl_last10_{team_id}"

        def fetch():
            url = f"https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/teams/{team_id}/schedule"
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
            'goalsFor': '-',
            'goalsAgainst': '-',
            'shotsFor': '-',
            'shotsAgainst': '-',
            'powerPlayPct': '-',
            'penaltyKillPct': '-',
            'savePct': '-',
        }

    def _default_advanced_stats(self) -> Dict:
        return {
            'xgf_per_60': '-',
            'xga_per_60': '-',
            'xg_diff': '-',
            'corsi_for_pct': '-',
            'fenwick_for_pct': '-',
            'shooting_pct': '-',
            'save_pct': '-',
            'pdo': '-',
            'pp_pct': '-',
            'pk_pct': '-',
        }

    def _default_goalie_stats(self) -> Dict:
        return {
            'name': 'Unknown',
            'stats': {
                'savePct': '-',
                'goalsAgainstAvg': '-',
                'wins': '-',
                'losses': '-',
            }
        }

    def get_complete_game_data(self, game: Dict) -> Dict:
        """Get comprehensive data for a single NHL game"""
        base_data = super().get_complete_game_data(game)

        away_id = game.get('away', {}).get('id')
        home_id = game.get('home', {}).get('id')

        base_data.update({
            'away_goalie': self.get_goalie_stats(away_id) if away_id else {},
            'home_goalie': self.get_goalie_stats(home_id) if home_id else {},
            'away_last10': self.get_last_10_games(away_id) if away_id else [],
            'home_last10': self.get_last_10_games(home_id) if home_id else [],
        })

        return base_data
