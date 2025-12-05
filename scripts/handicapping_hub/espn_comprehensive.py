"""
COMPREHENSIVE ESPN DATA FETCHER
================================
Fetches complete stats from ESPN with multiple endpoints and fallbacks.
Goal: Every field populated, every time.

Data Sources (in order of priority):
1. ESPN Site API (scoreboard, teams)
2. ESPN Core API (detailed stats)
3. Calculated from game logs
4. Smart defaults based on league averages
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .cache import cache

logger = logging.getLogger('espn_comprehensive')


class ESPNComprehensiveFetcher:
    """
    Fetches comprehensive data from ESPN with multiple fallbacks.
    Never returns empty values - always provides data or intelligent defaults.
    """

    # ESPN API endpoints
    SITE_API_BASE = "https://site.api.espn.com/apis/site/v2/sports"
    CORE_API_BASE = "https://sports.core.api.espn.com/v2/sports"
    WEB_API_BASE = "https://site.web.api.espn.com/apis/v2/sports"

    SPORT_PATHS = {
        'NBA': ('basketball', 'nba'),
        'NHL': ('hockey', 'nhl'),
        'NFL': ('football', 'nfl'),
        'MLB': ('baseball', 'mlb'),
        'NCAAF': ('football', 'college-football'),
        'NCAAB': ('basketball', 'mens-college-basketball'),
    }

    # League average defaults by sport
    LEAGUE_AVERAGES = {
        'NBA': {
            'ppg': 114.0, 'oppg': 114.0, 'fg_pct': 0.470, 'fg3_pct': 0.365,
            'ft_pct': 0.780, 'rpg': 43.5, 'apg': 25.5, 'spg': 7.5, 'bpg': 5.0,
            'topg': 13.5, 'off_rtg': 114.0, 'def_rtg': 114.0, 'net_rtg': 0.0,
            'pace': 100.0, 'efg_pct': 0.545, 'ts_pct': 0.580,
        },
        'NHL': {
            'gf_per_game': 3.10, 'ga_per_game': 3.10, 'pp_pct': 21.0, 'pk_pct': 79.0,
            'shots_per_game': 30.0, 'sv_pct': 0.905, 'pdo': 100.0, 'cf_pct': 50.0,
        },
        'NFL': {
            'ppg': 22.5, 'oppg': 22.5, 'ypg': 340.0, 'rush_ypg': 115.0, 'pass_ypg': 225.0,
            'third_down_pct': 0.40, 'red_zone_pct': 0.55, 'to_diff': 0,
        },
        'NCAAF': {
            'ppg': 28.0, 'oppg': 28.0, 'ypg': 380.0, 'rush_ypg': 150.0, 'pass_ypg': 230.0,
        },
        'NCAAB': {
            'ppg': 72.0, 'oppg': 72.0, 'fg_pct': 0.440, 'fg3_pct': 0.340,
            'off_rtg': 105.0, 'def_rtg': 105.0, 'net_rtg': 0.0, 'pace': 68.0,
        },
        'MLB': {
            'runs_per_game': 4.50, 'hits_per_game': 8.5, 'era': 4.20,
            'batting_avg': 0.248, 'obp': 0.320, 'slg': 0.410, 'ops': 0.730,
        },
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })
        self.rate_limit_delay = 0.25

    def _request_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """Make request with automatic retry on failure"""
        for attempt in range(max_retries):
            try:
                time.sleep(self.rate_limit_delay)
                response = self.session.get(url, params=params, timeout=15)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    time.sleep(5 * (attempt + 1))
                    continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {url[:60]}... - {e}")
                time.sleep(2 * (attempt + 1))
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                break
        return None

    def get_team_stats_comprehensive(self, sport: str, team_id: str, team_name: str = '') -> Dict:
        """
        Get comprehensive team stats using multiple endpoints.
        ALWAYS returns populated data - never empty.
        """
        if not team_id:
            return self._get_smart_defaults(sport)

        cache_key = f"espn_full_{sport}_{team_id}"

        def fetch():
            stats = {}

            # Try primary endpoint - team page
            sport_cat, sport_league = self.SPORT_PATHS.get(sport, ('', ''))
            if sport_cat:
                team_url = f"{self.SITE_API_BASE}/{sport_cat}/{sport_league}/teams/{team_id}"
                team_data = self._request_with_retry(team_url)
                if team_data:
                    stats.update(self._parse_team_page(team_data, sport))

            # Try statistics endpoint
            stats_url = f"{self.SITE_API_BASE}/{sport_cat}/{sport_league}/teams/{team_id}/statistics"
            stats_data = self._request_with_retry(stats_url)
            if stats_data:
                stats.update(self._parse_statistics_endpoint(stats_data, sport))

            # Calculate derived stats
            stats.update(self._calculate_derived_stats(stats, sport))

            # Fill any remaining gaps with smart defaults
            defaults = self._get_smart_defaults(sport)
            for key, value in defaults.items():
                if key not in stats or stats[key] in (None, '', '-', 'N/A', 0, 0.0):
                    stats[key] = value

            return stats

        return cache.get_or_fetch(cache_key, fetch, max_age_hours=4)

    def _parse_team_page(self, data: Dict, sport: str) -> Dict:
        """Parse stats from ESPN team page response"""
        stats = {}

        team = data.get('team', {})

        # Record info
        record = team.get('record', {})
        items = record.get('items', [])
        for item in items:
            if item.get('type') == 'total':
                for stat in item.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('value', stat.get('displayValue'))
                    if name and value is not None:
                        stats[name.lower()] = value

        # Direct statistics
        for stat_group in team.get('statistics', []):
            if isinstance(stat_group, dict):
                for stat in stat_group.get('stats', []):
                    if isinstance(stat, dict):
                        name = stat.get('name', stat.get('abbreviation', ''))
                        value = stat.get('value', stat.get('displayValue'))
                        if name and value is not None:
                            stats[name.lower()] = value

        # Next event stats (if available)
        next_event = team.get('nextEvent', [])
        if next_event:
            # Parse any embedded stats
            pass

        return stats

    def _parse_statistics_endpoint(self, data: Dict, sport: str) -> Dict:
        """Parse detailed statistics endpoint"""
        stats = {}

        # Handle splits format
        splits = data.get('splits', {})
        if isinstance(splits, dict):
            categories = splits.get('categories', [])
            for category in categories:
                if isinstance(category, dict):
                    cat_name = category.get('name', '').lower()
                    for stat in category.get('stats', []):
                        if isinstance(stat, dict):
                            name = stat.get('name', stat.get('abbreviation', ''))
                            value = stat.get('value', stat.get('displayValue'))
                            if name and value is not None:
                                # Prefix with category for clarity
                                key = f"{cat_name}_{name}".lower() if cat_name else name.lower()
                                stats[key] = value

        # Handle direct stats format
        for stat in data.get('stats', []):
            if isinstance(stat, dict):
                name = stat.get('name', '')
                value = stat.get('value', stat.get('displayValue'))
                if name and value is not None:
                    stats[name.lower()] = value

        return stats

    def _calculate_derived_stats(self, stats: Dict, sport: str) -> Dict:
        """Calculate derived statistics from available data"""
        derived = {}

        if sport in ['NBA', 'NCAAB']:
            # Net rating = Off RTG - Def RTG
            off_rtg = self._safe_float(stats.get('off_rtg', stats.get('offensiverating')))
            def_rtg = self._safe_float(stats.get('def_rtg', stats.get('defensiverating')))
            if off_rtg and def_rtg:
                derived['net_rtg'] = round(off_rtg - def_rtg, 1)

            # Point differential from PPG/OPPG
            ppg = self._safe_float(stats.get('ppg', stats.get('points', stats.get('avgpoints'))))
            oppg = self._safe_float(stats.get('oppg', stats.get('pointsagainst', stats.get('avgpointsagainst'))))
            if ppg and oppg:
                derived['point_diff'] = round(ppg - oppg, 1)

            # eFG% if we have FG data
            fgm = self._safe_float(stats.get('fgm', stats.get('fieldgoalsmade')))
            fga = self._safe_float(stats.get('fga', stats.get('fieldgoalsattempted')))
            fg3m = self._safe_float(stats.get('fg3m', stats.get('threepointersmade', 0)))
            if fgm and fga and fga > 0:
                derived['efg_pct'] = round((fgm + 0.5 * fg3m) / fga, 3)

        elif sport == 'NFL':
            # Point differential
            ppg = self._safe_float(stats.get('ppg', stats.get('points')))
            oppg = self._safe_float(stats.get('oppg', stats.get('pointsagainst')))
            if ppg and oppg:
                derived['point_diff'] = round(ppg - oppg, 1)

            # Yards per game
            rush_yds = self._safe_float(stats.get('rushingyards', stats.get('rush_ypg')))
            pass_yds = self._safe_float(stats.get('passingyards', stats.get('pass_ypg')))
            games = self._safe_float(stats.get('games', stats.get('gamesplayed', 1))) or 1
            if rush_yds:
                derived['rush_ypg'] = round(rush_yds / games, 1) if rush_yds > 500 else rush_yds
            if pass_yds:
                derived['pass_ypg'] = round(pass_yds / games, 1) if pass_yds > 500 else pass_yds

        elif sport == 'NHL':
            # PDO = SH% + SV%
            sh_pct = self._safe_float(stats.get('shootingpctg', stats.get('sh_pct')))
            sv_pct = self._safe_float(stats.get('savepctg', stats.get('sv_pct')))
            if sh_pct and sv_pct:
                # Convert to percentage if needed
                if sh_pct < 1:
                    sh_pct *= 100
                if sv_pct < 1:
                    sv_pct *= 100
                derived['pdo'] = round(sh_pct + sv_pct, 1)

        return derived

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None or value == '' or str(value) in ('-', 'N/A', 'NA'):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _get_smart_defaults(self, sport: str) -> Dict:
        """Get league average defaults for a sport"""
        return dict(self.LEAGUE_AVERAGES.get(sport, {}))

    def get_standings(self, sport: str) -> Dict[str, Dict]:
        """
        Get standings for all teams in a sport.
        Returns dict keyed by team name.
        """
        sport_cat, sport_league = self.SPORT_PATHS.get(sport, ('', ''))
        if not sport_cat:
            return {}

        cache_key = f"espn_standings_{sport}"

        def fetch():
            standings = {}

            # Try web API for structured standings
            url = f"{self.WEB_API_BASE}/{sport_cat}/{sport_league}/standings"
            data = self._request_with_retry(url)

            if data:
                # Handle conference-based structure
                for conf in data.get('children', []):
                    for entry in conf.get('standings', {}).get('entries', []):
                        team = entry.get('team', {})
                        team_name = team.get('displayName', '')
                        if team_name:
                            team_stats = {}
                            for stat in entry.get('stats', []):
                                team_stats[stat.get('name', '')] = stat.get('value', stat.get('displayValue'))
                            standings[team_name] = team_stats

                # Also check flat structure
                for entry in data.get('standings', {}).get('entries', []):
                    team = entry.get('team', {})
                    team_name = team.get('displayName', '')
                    if team_name:
                        team_stats = {}
                        for stat in entry.get('stats', []):
                            team_stats[stat.get('name', '')] = stat.get('value', stat.get('displayValue'))
                        standings[team_name] = team_stats

            return standings

        return cache.get_or_fetch(cache_key, fetch, max_age_hours=2)

    def get_injuries(self, sport: str, team_id: str) -> List[Dict]:
        """Get injury report for a team"""
        sport_cat, sport_league = self.SPORT_PATHS.get(sport, ('', ''))
        if not sport_cat or not team_id:
            return []

        cache_key = f"espn_injuries_{sport}_{team_id}"

        def fetch():
            injuries = []

            # Try core API for injuries
            url = f"{self.CORE_API_BASE}/{sport_cat}/leagues/{sport_league}/teams/{team_id}/injuries"
            data = self._request_with_retry(url)

            if data and 'items' in data:
                for item in data.get('items', []):
                    # Item might be a reference URL
                    if isinstance(item, dict) and '$ref' in item:
                        injury_data = self._request_with_retry(item['$ref'])
                        if injury_data:
                            injuries.append(self._parse_injury(injury_data))
                    elif isinstance(item, dict):
                        injuries.append(self._parse_injury(item))

            return injuries

        return cache.get_or_fetch(cache_key, fetch, max_age_hours=3)

    def _parse_injury(self, data: Dict) -> Dict:
        """Parse injury data into standard format"""
        athlete = data.get('athlete', {})
        if isinstance(athlete, dict) and '$ref' in athlete:
            # Could fetch athlete details if needed
            pass

        return {
            'player': data.get('athlete', {}).get('displayName', data.get('shortComment', '')),
            'position': data.get('athlete', {}).get('position', {}).get('abbreviation', ''),
            'injury': data.get('type', {}).get('description', data.get('longComment', '')),
            'status': data.get('status', 'Unknown'),
            'details': data.get('details', {}).get('detail', ''),
        }


# Singleton instance
espn_fetcher = ESPNComprehensiveFetcher()


def get_complete_team_stats(sport: str, team_id: str, team_name: str = '') -> Dict:
    """Convenience function to get comprehensive team stats"""
    return espn_fetcher.get_team_stats_comprehensive(sport, team_id, team_name)


def get_standings(sport: str) -> Dict:
    """Convenience function to get standings"""
    return espn_fetcher.get_standings(sport)
