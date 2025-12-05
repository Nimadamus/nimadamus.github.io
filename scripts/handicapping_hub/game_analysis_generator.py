"""
COMPREHENSIVE GAME ANALYSIS GENERATOR
=====================================
Creates in-depth analysis articles for each game with:
- Recent form and momentum
- Head-to-head history
- Advanced statistics
- Key injuries and their impact
- Betting trends (ATS, O/U, home/away)
- Line movement analysis
- Key matchups and players to watch
- Expert analysis and prediction

All data sourced from ESPN APIs for accuracy.
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handicapping_hub.injury_scraper import InjuryScraper, COLLEGE_TEAM_IDS


class ESPNDataFetcher:
    """Fetches comprehensive data from ESPN APIs"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.base_url = 'https://site.api.espn.com/apis/site/v2/sports'

    def _get_sport_path(self, sport: str) -> str:
        """Get ESPN API path for sport"""
        paths = {
            'NBA': 'basketball/nba',
            'NHL': 'hockey/nhl',
            'NFL': 'football/nfl',
            'MLB': 'baseball/mlb',
            'NCAAF': 'football/college-football',
            'NCAAB': 'basketball/mens-college-basketball',
        }
        return paths.get(sport, '')

    def get_team_schedule(self, sport: str, team_id: str, limit: int = 10) -> List[Dict]:
        """Get recent games for a team"""
        path = self._get_sport_path(sport)
        if not path:
            return []

        url = f"{self.base_url}/{path}/teams/{team_id}/schedule"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                events = data.get('events', [])
                # Filter to completed games
                completed = [e for e in events if e.get('competitions', [{}])[0].get('status', {}).get('type', {}).get('completed', False)]
                return completed[-limit:]  # Return last N completed games
        except Exception as e:
            print(f"    [WARN] Could not fetch schedule for team {team_id}: {e}")
        return []

    def get_team_stats(self, sport: str, team_id: str) -> Dict:
        """Get team statistics"""
        path = self._get_sport_path(sport)
        if not path:
            return {}

        url = f"{self.base_url}/{path}/teams/{team_id}/statistics"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            pass
        return {}

    def get_team_record(self, sport: str, team_id: str) -> Dict:
        """Get team record and standings info"""
        path = self._get_sport_path(sport)
        if not path:
            return {}

        url = f"{self.base_url}/{path}/teams/{team_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                team = data.get('team', {})
                return {
                    'record': team.get('record', {}).get('items', [{}])[0].get('summary', ''),
                    'standing': team.get('standingSummary', ''),
                    'form': team.get('form', ''),
                }
        except Exception as e:
            pass
        return {}

    def get_game_odds(self, sport: str, event_id: str) -> Dict:
        """Get betting odds for a specific game"""
        path = self._get_sport_path(sport)
        if not path:
            return {}

        url = f"{self.base_url}/{path}/summary?event={event_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                odds = data.get('odds', [])
                if odds:
                    return odds[0]  # Return first odds provider
        except Exception as e:
            pass
        return {}


class GameAnalysisGenerator:
    """Generates comprehensive analysis for each game"""

    def __init__(self):
        self.espn = ESPNDataFetcher()
        self.injury_scraper = InjuryScraper()

    def get_recent_form(self, games: List[Dict], team_id: str) -> Dict:
        """Analyze recent form from last games"""
        if not games:
            return {'record': '0-0', 'trend': 'Unknown', 'streak': 'Unknown'}

        wins = 0
        losses = 0
        streak = 0
        streak_type = None
        total_scored = 0
        total_allowed = 0

        for game in games[-10:]:  # Last 10 games
            comp = game.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])

            for team in competitors:
                if str(team.get('id')) == str(team_id):
                    winner = team.get('winner', False)
                    score = int(team.get('score', 0))
                    total_scored += score

                    # Get opponent score
                    for opp in competitors:
                        if str(opp.get('id')) != str(team_id):
                            total_allowed += int(opp.get('score', 0))

                    if winner:
                        wins += 1
                        if streak_type == 'W':
                            streak += 1
                        else:
                            streak = 1
                            streak_type = 'W'
                    else:
                        losses += 1
                        if streak_type == 'L':
                            streak += 1
                        else:
                            streak = 1
                            streak_type = 'L'
                    break

        ppg = total_scored / len(games) if games else 0
        papg = total_allowed / len(games) if games else 0

        return {
            'record': f'{wins}-{losses}',
            'win_pct': wins / (wins + losses) if (wins + losses) > 0 else 0,
            'streak': f'{streak_type}{streak}' if streak_type else 'N/A',
            'ppg': round(ppg, 1),
            'papg': round(papg, 1),
            'trend': 'Hot' if wins >= 7 else 'Cold' if losses >= 7 else 'Mixed'
        }

    def analyze_head_to_head(self, away_games: List[Dict], home_games: List[Dict],
                             away_id: str, home_id: str) -> Dict:
        """Analyze head-to-head history"""
        h2h_games = []

        # Find games where these teams played each other
        for game in away_games + home_games:
            comp = game.get('competitions', [{}])[0]
            competitors = comp.get('competitors', [])
            team_ids = [str(c.get('id')) for c in competitors]

            if str(away_id) in team_ids and str(home_id) in team_ids:
                h2h_games.append(game)

        if not h2h_games:
            return {'record': 'No recent meetings', 'avg_margin': 0}

        away_wins = 0
        home_wins = 0
        total_margin = 0

        for game in h2h_games[:5]:  # Last 5 H2H
            comp = game.get('competitions', [{}])[0]
            for team in comp.get('competitors', []):
                if str(team.get('id')) == str(away_id) and team.get('winner'):
                    away_wins += 1
                    away_score = int(team.get('score', 0))
                    home_score = int([t for t in comp.get('competitors', []) if str(t.get('id')) == str(home_id)][0].get('score', 0))
                    total_margin += (away_score - home_score)
                elif str(team.get('id')) == str(home_id) and team.get('winner'):
                    home_wins += 1
                    home_score = int(team.get('score', 0))
                    away_score = int([t for t in comp.get('competitors', []) if str(t.get('id')) == str(away_id)][0].get('score', 0))
                    total_margin -= (home_score - away_score)

        return {
            'away_wins': away_wins,
            'home_wins': home_wins,
            'record': f'{away_wins}-{home_wins}' if away_wins + home_wins > 0 else 'No recent meetings',
            'avg_margin': round(total_margin / len(h2h_games), 1) if h2h_games else 0
        }

    def generate_analysis(self, sport: str, game_data: Dict, advanced_data: Dict = None) -> str:
        """Generate comprehensive analysis text for a game"""
        game = game_data.get('game', {})
        away = game.get('away', {})
        home = game.get('home', {})

        away_name = away.get('displayName', away.get('name', 'Away Team'))
        home_name = home.get('displayName', home.get('name', 'Home Team'))
        away_abbrev = away.get('abbreviation', 'AWY')
        home_abbrev = home.get('abbreviation', 'HME')
        away_id = away.get('id', '')
        home_id = home.get('id', '')

        # Get data from game_data (already fetched)
        away_stats = game_data.get('away_stats', {})
        home_stats = game_data.get('home_stats', {})
        odds = game_data.get('odds', {})
        away_injuries = game_data.get('away_injuries', [])
        home_injuries = game_data.get('home_injuries', [])

        # Get ATS/betting data if available
        away_ats = game_data.get('away_ats', {})
        home_ats = game_data.get('home_ats', {})
        public_betting = game_data.get('public_betting', {})
        sharp_money = game_data.get('sharp_money', {})

        # Build analysis sections
        sections = []

        # OVERVIEW SECTION
        overview = self._generate_overview(sport, away_name, home_name, away_stats, home_stats, odds)
        sections.append(overview)

        # RECENT FORM SECTION
        form_section = self._generate_form_section(sport, away_name, home_name, away_stats, home_stats)
        sections.append(form_section)

        # KEY STATISTICS SECTION
        stats_section = self._generate_stats_section(sport, away_name, home_name, away_stats, home_stats, away_abbrev, home_abbrev)
        sections.append(stats_section)

        # INJURY IMPACT SECTION
        injury_section = self._generate_injury_section(away_injuries, home_injuries, away_abbrev, home_abbrev)
        if injury_section:
            sections.append(injury_section)

        # BETTING TRENDS SECTION
        betting_section = self._generate_betting_section(away_ats, home_ats, public_betting, sharp_money, away_abbrev, home_abbrev, odds)
        sections.append(betting_section)

        # MATCHUP ANALYSIS
        matchup_section = self._generate_matchup_analysis(sport, away_name, home_name, away_stats, home_stats)
        sections.append(matchup_section)

        return '\n\n'.join(sections)

    def _generate_overview(self, sport: str, away_name: str, home_name: str,
                           away_stats: Dict, home_stats: Dict, odds: Dict) -> str:
        """Generate game overview paragraph"""
        away_record = away_stats.get('record', 'N/A')
        home_record = home_stats.get('record', 'N/A')
        spread = odds.get('spread', 'N/A')
        total = odds.get('total', 'N/A')

        return f"""<div class="analysis-section overview">
<h4>Game Overview</h4>
<p>The <strong>{away_name}</strong> ({away_record}) travel to face the <strong>{home_name}</strong> ({home_record}) in what should be an intriguing {sport} matchup. The line has {home_name} as {spread} favorites with the total set at {total}.</p>
</div>"""

    def _generate_form_section(self, sport: str, away_name: str, home_name: str,
                               away_stats: Dict, home_stats: Dict) -> str:
        """Generate recent form analysis"""
        away_last10 = away_stats.get('last10', {})
        home_last10 = home_stats.get('last10', {})

        away_form = away_last10.get('record', 'N/A')
        home_form = home_last10.get('record', 'N/A')
        away_streak = away_stats.get('streak', '')
        home_streak = home_stats.get('streak', '')

        streak_text = []
        if away_streak:
            streak_text.append(f"{away_name} is on a {away_streak}")
        if home_streak:
            streak_text.append(f"{home_name} is on a {home_streak}")

        return f"""<div class="analysis-section form">
<h4>Recent Form</h4>
<p><strong>{away_name} (Last 10):</strong> {away_form}</p>
<p><strong>{home_name} (Last 10):</strong> {home_form}</p>
{f'<p>{" while ".join(streak_text)}.</p>' if streak_text else ''}
</div>"""

    def _generate_stats_section(self, sport: str, away_name: str, home_name: str,
                                 away_stats: Dict, home_stats: Dict,
                                 away_abbrev: str, home_abbrev: str) -> str:
        """Generate key statistics comparison"""
        stats_html = '<div class="analysis-section stats"><h4>Key Statistics</h4><div class="stats-comparison">'

        if sport == 'NBA':
            stats = [
                ('PPG', away_stats.get('ppg', 'N/A'), home_stats.get('ppg', 'N/A')),
                ('Opp PPG', away_stats.get('oppg', 'N/A'), home_stats.get('oppg', 'N/A')),
                ('Pace', away_stats.get('pace', 'N/A'), home_stats.get('pace', 'N/A')),
                ('Off Rtg', away_stats.get('offRtg', 'N/A'), home_stats.get('offRtg', 'N/A')),
                ('Def Rtg', away_stats.get('defRtg', 'N/A'), home_stats.get('defRtg', 'N/A')),
            ]
        elif sport == 'NHL':
            stats = [
                ('GF/G', away_stats.get('goalsFor', 'N/A'), home_stats.get('goalsFor', 'N/A')),
                ('GA/G', away_stats.get('goalsAgainst', 'N/A'), home_stats.get('goalsAgainst', 'N/A')),
                ('PP%', away_stats.get('powerPlayPct', 'N/A'), home_stats.get('powerPlayPct', 'N/A')),
                ('PK%', away_stats.get('penaltyKillPct', 'N/A'), home_stats.get('penaltyKillPct', 'N/A')),
                ('SOG/G', away_stats.get('shotsPerGame', 'N/A'), home_stats.get('shotsPerGame', 'N/A')),
            ]
        elif sport in ['NFL', 'NCAAF']:
            stats = [
                ('PPG', away_stats.get('ppg', 'N/A'), home_stats.get('ppg', 'N/A')),
                ('Opp PPG', away_stats.get('oppg', 'N/A'), home_stats.get('oppg', 'N/A')),
                ('Rush YPG', away_stats.get('rushYards', 'N/A'), home_stats.get('rushYards', 'N/A')),
                ('Pass YPG', away_stats.get('passYards', 'N/A'), home_stats.get('passYards', 'N/A')),
                ('TO Margin', away_stats.get('turnoverMargin', 'N/A'), home_stats.get('turnoverMargin', 'N/A')),
            ]
        else:
            stats = [
                ('PPG', away_stats.get('ppg', 'N/A'), home_stats.get('ppg', 'N/A')),
                ('Opp PPG', away_stats.get('oppg', 'N/A'), home_stats.get('oppg', 'N/A')),
            ]

        for stat_name, away_val, home_val in stats:
            stats_html += f"""<div class="stat-compare-row">
<span class="stat-label">{stat_name}</span>
<span class="stat-away">{away_abbrev}: {away_val}</span>
<span class="stat-home">{home_abbrev}: {home_val}</span>
</div>"""

        stats_html += '</div></div>'
        return stats_html

    def _generate_injury_section(self, away_injuries: List, home_injuries: List,
                                  away_abbrev: str, home_abbrev: str) -> str:
        """Generate injury impact analysis"""
        if not away_injuries and not home_injuries:
            return ''

        html = '<div class="analysis-section injuries"><h4>Injury Report</h4>'

        if away_injuries:
            out = [i for i in away_injuries if 'out' in i.get('status', '').lower()]
            questionable = [i for i in away_injuries if 'questionable' in i.get('status', '').lower()]
            html += f'<p><strong>{away_abbrev}:</strong> '
            if out:
                names = [f"{i.get('name', '')} ({i.get('position', '')})" for i in out[:4]]
                html += f'OUT: {", ".join(names)}. '
            if questionable:
                names = [f"{i.get('name', '')} ({i.get('position', '')})" for i in questionable[:3]]
                html += f'Questionable: {", ".join(names)}.'
            html += '</p>'

        if home_injuries:
            out = [i for i in home_injuries if 'out' in i.get('status', '').lower()]
            questionable = [i for i in home_injuries if 'questionable' in i.get('status', '').lower()]
            html += f'<p><strong>{home_abbrev}:</strong> '
            if out:
                names = [f"{i.get('name', '')} ({i.get('position', '')})" for i in out[:4]]
                html += f'OUT: {", ".join(names)}. '
            if questionable:
                names = [f"{i.get('name', '')} ({i.get('position', '')})" for i in questionable[:3]]
                html += f'Questionable: {", ".join(names)}.'
            html += '</p>'

        html += '</div>'
        return html

    def _generate_betting_section(self, away_ats: Dict, home_ats: Dict,
                                   public_betting: Dict, sharp_money: Dict,
                                   away_abbrev: str, home_abbrev: str, odds: Dict) -> str:
        """Generate betting trends section"""
        html = '<div class="analysis-section betting"><h4>Betting Trends</h4>'

        # ATS Records
        away_ats_rec = away_ats.get('ats_overall', 'N/A')
        home_ats_rec = home_ats.get('ats_overall', 'N/A')
        html += f'<p><strong>ATS Records:</strong> {away_abbrev} {away_ats_rec} | {home_abbrev} {home_ats_rec}</p>'

        # Public betting percentages
        if public_betting:
            spread_pct = public_betting.get('spread_pct', {})
            ml_pct = public_betting.get('ml_pct', {})
            if spread_pct:
                html += f'<p><strong>Public Spread:</strong> {spread_pct.get("away", "N/A")}% on {away_abbrev} | {spread_pct.get("home", "N/A")}% on {home_abbrev}</p>'

        # Sharp money
        if sharp_money and sharp_money.get('sharp_side'):
            html += f'<p><strong>Sharp Action:</strong> {sharp_money.get("sharp_side", "N/A")}</p>'

        # Line info
        spread = odds.get('spread', 'N/A')
        total = odds.get('total', 'N/A')
        html += f'<p><strong>Current Line:</strong> Spread {spread} | O/U {total}</p>'

        html += '</div>'
        return html

    def _generate_matchup_analysis(self, sport: str, away_name: str, home_name: str,
                                    away_stats: Dict, home_stats: Dict) -> str:
        """Generate matchup analysis and prediction"""
        html = '<div class="analysis-section matchup"><h4>Matchup Analysis</h4>'

        # Compare key metrics
        away_off = float(away_stats.get('ppg', 0) or 0)
        home_off = float(home_stats.get('ppg', 0) or 0)
        away_def = float(away_stats.get('oppg', 100) or 100)
        home_def = float(home_stats.get('oppg', 100) or 100)

        # Simple projection
        away_proj = (away_off + home_def) / 2
        home_proj = (home_off + away_def) / 2

        html += f"""<p>Based on season averages, this projects as approximately a <strong>{round(away_proj + home_proj)}</strong> total with {away_name if away_proj > home_proj else home_name} favored.</p>"""

        # Key factors
        html += '<p><strong>Key Factors:</strong></p><ul>'
        if away_off > home_off:
            html += f'<li>{away_name} averages more points per game</li>'
        else:
            html += f'<li>{home_name} averages more points per game</li>'

        if away_def < home_def:
            html += f'<li>{away_name} has the better defensive efficiency</li>'
        else:
            html += f'<li>{home_name} has the better defensive efficiency</li>'

        html += '<li>Home court/ice advantage typically worth 2-3 points</li>'
        html += '</ul></div>'

        return html


def generate_game_analysis(sport: str, game_data: Dict, advanced_data: Dict = None) -> str:
    """Convenience function to generate analysis"""
    generator = GameAnalysisGenerator()
    return generator.generate_analysis(sport, game_data, advanced_data)
