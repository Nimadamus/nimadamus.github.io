"""
ADVANCED HANDICAPPING HUB - MAIN ORCHESTRATION
===============================================
Coordinates all data fetchers and generates the HTML output.

This is the main entry point for the daily update workflow.
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handicapping_hub.nba_fetcher import NBAFetcher
from handicapping_hub.nhl_fetcher import NHLFetcher
from handicapping_hub.mlb_fetcher import MLBFetcher
from handicapping_hub.football_fetcher import NFLFetcher, NCAAFFetcher, NCAABFetcher
from handicapping_hub.base_fetcher import OddsClient
from handicapping_hub.killport_model import KillportModel, generate_all_predictions
from handicapping_hub.cache import cache


# Configuration
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
TIME_DISPLAY = TODAY.strftime("%I:%M %p")


def fetch_all_sports_data() -> Dict:
    """
    Fetch comprehensive data for all sports.
    """
    print("\n" + "=" * 60)
    print("ADVANCED HANDICAPPING HUB - DATA COLLECTION")
    print(f"Date: {DATE_DISPLAY}")
    print("=" * 60)

    # Initialize fetchers
    fetchers = {
        'NBA': NBAFetcher(),
        'NHL': NHLFetcher(),
        'MLB': MLBFetcher(),
        'NFL': NFLFetcher(),
        'NCAAF': NCAAFFetcher(),
        'NCAAB': NCAABFetcher(),
    }

    # Initialize odds client
    odds_api_key = os.environ.get('ODDS_API_KEY', '')
    odds_client = OddsClient(odds_api_key) if odds_api_key else None

    if odds_api_key:
        print("\n[INFO] Odds API key found - will fetch betting lines")
    else:
        print("\n[INFO] No Odds API key - betting lines will show N/A")

    all_data = {}

    for sport, fetcher in fetchers.items():
        try:
            sport_data = fetcher.fetch_all()

            # Add odds data
            if odds_client and sport_data.get('games'):
                odds = odds_client.get_odds(sport)
                for game_data in sport_data['games']:
                    game = game_data.get('game', {})
                    away_name = game.get('away', {}).get('name', '')
                    home_name = game.get('home', {}).get('name', '')
                    game_key = f"{away_name} @ {home_name}"
                    game_data['odds'] = odds.get(game_key, {})

            all_data[sport] = sport_data

        except Exception as e:
            print(f"\n[ERROR] Failed to fetch {sport} data: {e}")
            all_data[sport] = {'sport': sport, 'games': [], 'error': str(e)}

    return all_data


def generate_html_content(all_data: Dict, predictions: Dict) -> str:
    """
    Generate the complete HTML content for the Handicapping Hub.
    """
    # Count games by sport
    game_counts = {sport: len(data.get('games', [])) for sport, data in all_data.items()}

    # Generate sport sections
    sections_html = ""
    for sport in ['NBA', 'NHL', 'MLB', 'NFL', 'NCAAF', 'NCAAB']:
        sport_data = all_data.get(sport, {})
        sport_predictions = predictions.get(sport, [])
        sections_html += generate_sport_section(sport, sport_data, sport_predictions)

    # Generate tabs HTML
    tabs_html = ""
    first_sport = True
    for sport in ['NBA', 'NHL', 'MLB', 'NFL', 'NCAAF', 'NCAAB']:
        count = game_counts.get(sport, 0)
        active = 'active' if first_sport and count > 0 else ''
        if first_sport and count > 0:
            first_sport = False
        tabs_html += f'<button class="tab {active}" onclick="showSection(\'{sport}\')">{sport} ({count})</button>\n            '

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Handicapping Hub - BetLegend</title>
    <meta name="description" content="Professional sports analytics and handicapping research center. Advanced stats, injury reports, betting lines, and Killport Model predictions.">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    {generate_css()}
</head>
<body>
    <div class="header">
        <div class="header-content">
            <a href="index.html" class="back-link">&larr; Back to BetLegend</a>
            <h1>ADVANCED HANDICAPPING <span>HUB</span></h1>
            <p class="subtitle">Powered by the Killport Model</p>
            <div class="timestamp">Last updated: {DATE_DISPLAY} at {TIME_DISPLAY} &bull; Data from ESPN + Advanced Analytics</div>
            <div class="tabs">
            {tabs_html}
            </div>
            <div class="archive-link">
                <a href="handicapping-hub-calendar.html">View Archive Calendar</a>
            </div>
        </div>
    </div>
    <div class="container">
{sections_html}
    </div>
    {generate_javascript()}
</body>
</html>'''


def generate_sport_section(sport: str, sport_data: Dict, predictions: List) -> str:
    """Generate HTML section for a sport"""
    games = sport_data.get('games', [])
    game_count = len(games)

    # Determine if this should be the active section
    is_active = game_count > 0 and sport == 'NBA'  # NBA is default

    active_class = 'active' if is_active else ''

    if not games:
        return f'''
        <div id="{sport}" class="section {active_class}">
            <div class="section-header">
                <h2>{sport} Games</h2><span class="count">0 games today</span>
            </div>
            <div class="no-games">
                <p>No {sport} games scheduled for today</p>
            </div>
        </div>
'''

    # Generate game cards
    cards_html = ""
    for i, game_data in enumerate(games):
        prediction = predictions[i] if i < len(predictions) else None
        cards_html += generate_game_card(sport, game_data, prediction)

    return f'''
        <div id="{sport}" class="section {active_class}">
            <div class="section-header">
                <h2>{sport} Games</h2><span class="count">{game_count} games today</span>
            </div>
{cards_html}
        </div>
'''


def generate_game_card(sport: str, game_data: Dict, prediction: Dict = None) -> str:
    """Generate HTML for a single game card with advanced stats"""
    game = game_data.get('game', {})
    away = game.get('away', {})
    home = game.get('home', {})

    away_stats = game_data.get('away_stats', {})
    home_stats = game_data.get('home_stats', {})
    away_advanced = game_data.get('away_advanced', {})
    home_advanced = game_data.get('home_advanced', {})
    away_injuries = game_data.get('away_injuries', [])
    home_injuries = game_data.get('home_injuries', [])
    odds = game_data.get('odds', {})

    # Get logos
    away_logo = away.get('logo', f"https://a.espncdn.com/i/teamlogos/{sport.lower()}/500/scoreboard/{away.get('abbreviation', '').lower()}.png")
    home_logo = home.get('logo', f"https://a.espncdn.com/i/teamlogos/{sport.lower()}/500/scoreboard/{home.get('abbreviation', '').lower()}.png")

    # Format odds
    spread_home = format_spread(odds.get('spread_home'))
    spread_away = format_spread(odds.get('spread_away'))
    total = odds.get('total', 'N/A')
    ml_home = format_ml(odds.get('ml_home'))
    ml_away = format_ml(odds.get('ml_away'))

    # Generate Killport Model section
    killport_html = ""
    if prediction:
        killport_html = generate_killport_section(prediction)

    # Generate advanced stats HTML based on sport
    away_advanced_html = generate_advanced_stats_html(sport, away_advanced, 'away')
    home_advanced_html = generate_advanced_stats_html(sport, home_advanced, 'home')

    # Generate basic stats HTML
    away_basic_html = generate_basic_stats_html(sport, away_stats)
    home_basic_html = generate_basic_stats_html(sport, home_stats)

    # Generate injuries HTML
    away_injuries_html = generate_injuries_html(away_injuries, away.get('name', ''))
    home_injuries_html = generate_injuries_html(home_injuries, home.get('name', ''))

    # Generate last games HTML
    away_last = game_data.get('away_last10', game_data.get('away_last5', []))
    home_last = game_data.get('home_last10', game_data.get('home_last5', []))
    last_games_html = generate_last_games_html(away_last, home_last, away.get('name', ''), home.get('name', ''))

    return f'''
            <div class="game-card">
                <div class="matchup-header">
                    <div class="team-box away">
                        <img src="{away_logo}" alt="{away.get('name', '')}" class="team-logo" onerror="this.style.display='none'">
                        <div class="team-details">
                            <h3>{away.get('name', 'Away Team')}</h3>
                            <div class="team-records">
                                <span class="overall">{away.get('record', 'N/A')}</span>
                                <br>Away: {away.get('away_record', 'N/A')}
                            </div>
                        </div>
                    </div>
                    <div class="vs-badge">VS</div>
                    <div class="team-box home">
                        <img src="{home_logo}" alt="{home.get('name', '')}" class="team-logo" onerror="this.style.display='none'">
                        <div class="team-details">
                            <h3>{home.get('name', 'Home Team')}</h3>
                            <div class="team-records">
                                <span class="overall">{home.get('record', 'N/A')}</span>
                                <br>Home: {home.get('home_record', 'N/A')}
                            </div>
                        </div>
                    </div>
                </div>

                {killport_html}

                <div class="stats-grid">
                    <div class="stats-panel away-panel">
                        <div class="panel-header">{away.get('abbreviation', 'AWAY')} STATS</div>
                        {away_basic_html}
                        <div class="advanced-toggle" onclick="toggleAdvanced(this)">
                            <span>▼ Advanced Analytics</span>
                        </div>
                        <div class="advanced-panel">
                            {away_advanced_html}
                        </div>
                    </div>
                    <div class="stats-panel home-panel">
                        <div class="panel-header">{home.get('abbreviation', 'HOME')} STATS</div>
                        {home_basic_html}
                        <div class="advanced-toggle" onclick="toggleAdvanced(this)">
                            <span>▼ Advanced Analytics</span>
                        </div>
                        <div class="advanced-panel">
                            {home_advanced_html}
                        </div>
                    </div>
                </div>

                <div class="injuries-section">
                    <div class="section-title">INJURY REPORT</div>
                    <div class="injuries-grid">
                        <div class="injury-column">
                            <h5>{away.get('name', '')}</h5>
                            {away_injuries_html}
                        </div>
                        <div class="injury-column">
                            <h5>{home.get('name', '')}</h5>
                            {home_injuries_html}
                        </div>
                    </div>
                </div>

                {last_games_html}

                <div class="betting-section">
                    <div class="section-title">BETTING LINES</div>
                    <div class="betting-grid">
                        <div class="line-box">
                            <div class="line-type">SPREAD</div>
                            <div class="line-values">
                                <span class="line-value">{away.get('abbreviation', '')} {spread_away}</span>
                                <span class="line-value">{home.get('abbreviation', '')} {spread_home}</span>
                            </div>
                        </div>
                        <div class="line-box">
                            <div class="line-type">TOTAL</div>
                            <div class="line-values">
                                <span class="line-value">O/U {total}</span>
                            </div>
                        </div>
                        <div class="line-box">
                            <div class="line-type">MONEYLINE</div>
                            <div class="line-values">
                                <span class="line-value">{away.get('abbreviation', '')} {ml_away}</span>
                                <span class="line-value">{home.get('abbreviation', '')} {ml_home}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
'''


def generate_killport_section(prediction: Dict) -> str:
    """Generate the Killport Model prediction section"""
    recommendation = prediction.get('recommendation', {})
    strength = recommendation.get('strength', 'LEAN')
    strength_class = strength.lower()

    return f'''
                <div class="killport-section">
                    <div class="killport-header">
                        <span class="killport-logo">⚡</span>
                        <span class="killport-title">KILLPORT MODEL</span>
                        <span class="confidence-stars">{prediction.get('confidence_stars', '☆☆☆☆☆')}</span>
                    </div>
                    <div class="killport-content">
                        <div class="prediction-main">
                            <div class="predicted-winner">
                                <span class="label">PREDICTION</span>
                                <span class="winner">{prediction.get('predicted_winner', 'N/A')}</span>
                                <span class="margin">by {prediction.get('predicted_margin', 0)} pts</span>
                            </div>
                            <div class="model-line">
                                <span class="label">MODEL LINE</span>
                                <span class="line">{prediction.get('model_line', 'N/A')}</span>
                            </div>
                            <div class="edge-rating">
                                <span class="label">EDGE RATING</span>
                                <span class="rating {get_edge_class(prediction.get('edge_rating', 0))}">{prediction.get('edge_rating', 0):+.1f}</span>
                            </div>
                        </div>
                        <div class="recommendation {strength_class}">
                            <span class="rec-label">{recommendation.get('play', 'PASS')}</span>
                            <span class="rec-side">{recommendation.get('side', '')}</span>
                            <span class="rec-strength">[{strength}]</span>
                        </div>
                        <div class="rec-reasoning">{recommendation.get('reasoning', '')}</div>
                    </div>
                </div>
'''


def generate_advanced_stats_html(sport: str, advanced: Dict, side: str) -> str:
    """Generate advanced stats HTML based on sport"""
    if not advanced or advanced.get('estimated') is None and not advanced:
        return '<div class="no-data">Advanced stats unavailable</div>'

    if sport in ['NBA', 'NCAAB']:
        return f'''
            <div class="advanced-stat">
                <span class="stat-label">OFF RTG</span>
                <span class="stat-value">{advanced.get('offensive_rating', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">DEF RTG</span>
                <span class="stat-value">{advanced.get('defensive_rating', 'N/A')}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">NET RTG</span>
                <span class="stat-value">{advanced.get('net_rating', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">PACE</span>
                <span class="stat-value">{advanced.get('pace', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">eFG%</span>
                <span class="stat-value">{advanced.get('efg_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">TS%</span>
                <span class="stat-value">{advanced.get('ts_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">TOV%</span>
                <span class="stat-value">{advanced.get('tov_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">OREB%</span>
                <span class="stat-value">{advanced.get('oreb_pct', 'N/A')}</span>
            </div>
'''

    elif sport == 'NHL':
        return f'''
            <div class="advanced-stat">
                <span class="stat-label">xGF/60</span>
                <span class="stat-value">{advanced.get('xgf_per_60', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">xGA/60</span>
                <span class="stat-value">{advanced.get('xga_per_60', 'N/A')}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">xG DIFF</span>
                <span class="stat-value">{advanced.get('xg_diff', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">CF%</span>
                <span class="stat-value">{advanced.get('corsi_for_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">FF%</span>
                <span class="stat-value">{advanced.get('fenwick_for_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">SH%</span>
                <span class="stat-value">{advanced.get('shooting_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">SV%</span>
                <span class="stat-value">{advanced.get('save_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">PDO</span>
                <span class="stat-value">{advanced.get('pdo', 'N/A')}</span>
            </div>
'''

    elif sport == 'MLB':
        return f'''
            <div class="advanced-stat highlight">
                <span class="stat-label">wOBA</span>
                <span class="stat-value">{advanced.get('woba', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">wRC+</span>
                <span class="stat-value">{advanced.get('wrc_plus', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">BABIP</span>
                <span class="stat-value">{advanced.get('babip', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">ISO</span>
                <span class="stat-value">{advanced.get('iso', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">K%</span>
                <span class="stat-value">{advanced.get('k_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">BB%</span>
                <span class="stat-value">{advanced.get('bb_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">FIP</span>
                <span class="stat-value">{advanced.get('fip', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">xFIP</span>
                <span class="stat-value">{advanced.get('xfip', 'N/A')}</span>
            </div>
'''

    elif sport in ['NFL', 'NCAAF']:
        return f'''
            <div class="advanced-stat highlight">
                <span class="stat-label">EPA/PLAY</span>
                <span class="stat-value">{advanced.get('epa_per_play', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">SUCCESS%</span>
                <span class="stat-value">{advanced.get('success_rate', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">EXPLOSIVE%</span>
                <span class="stat-value">{advanced.get('explosive_play_rate', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">YDS/PLAY</span>
                <span class="stat-value">{advanced.get('yards_per_play', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">3RD DOWN%</span>
                <span class="stat-value">{advanced.get('third_down_pct', 'N/A')}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">TO DIFF</span>
                <span class="stat-value">{advanced.get('turnover_diff', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">QB RTG</span>
                <span class="stat-value">{advanced.get('passer_rating', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">PT DIFF</span>
                <span class="stat-value">{advanced.get('point_diff', 'N/A')}</span>
            </div>
'''

    return '<div class="no-data">Sport not supported</div>'


def generate_basic_stats_html(sport: str, stats: Dict) -> str:
    """Generate basic stats HTML"""
    if not stats:
        return '<div class="no-data">Stats unavailable</div>'

    if sport in ['NBA', 'NCAAB']:
        return f'''
            <div class="basic-stat"><span>PPG</span><span>{stats.get('avgPoints', 'N/A')}</span></div>
            <div class="basic-stat"><span>FG%</span><span>{stats.get('avgFieldGoalPct', 'N/A')}</span></div>
            <div class="basic-stat"><span>3P%</span><span>{stats.get('avgThreePointPct', 'N/A')}</span></div>
            <div class="basic-stat"><span>REB</span><span>{stats.get('avgRebounds', 'N/A')}</span></div>
            <div class="basic-stat"><span>AST</span><span>{stats.get('avgAssists', 'N/A')}</span></div>
'''

    elif sport == 'NHL':
        return f'''
            <div class="basic-stat"><span>GF/G</span><span>{stats.get('goalsFor', 'N/A')}</span></div>
            <div class="basic-stat"><span>GA/G</span><span>{stats.get('goalsAgainst', 'N/A')}</span></div>
            <div class="basic-stat"><span>PP%</span><span>{stats.get('powerPlayPct', 'N/A')}</span></div>
            <div class="basic-stat"><span>PK%</span><span>{stats.get('penaltyKillPct', 'N/A')}</span></div>
'''

    elif sport in ['NFL', 'NCAAF']:
        return f'''
            <div class="basic-stat"><span>PPG</span><span>{stats.get('avgPointsPerGame', stats.get('totalPointsPerGame', 'N/A'))}</span></div>
            <div class="basic-stat"><span>YDS/G</span><span>{stats.get('netTotalYards', stats.get('totalYards', 'N/A'))}</span></div>
            <div class="basic-stat"><span>RUSH</span><span>{stats.get('rushingYardsPerGame', 'N/A')}</span></div>
            <div class="basic-stat"><span>PASS</span><span>{stats.get('netPassingYardsPerGame', stats.get('passingYardsPerGame', 'N/A'))}</span></div>
'''

    return ''


def generate_injuries_html(injuries: List, team_name: str) -> str:
    """Generate injuries HTML"""
    if not injuries:
        return '<span class="no-injuries">No injuries reported</span>'

    html = '<ul class="injury-list">'
    for inj in injuries[:5]:
        status_class = get_injury_status_class(inj.get('status', ''))
        html += f'''
            <li>
                <div class="player-info">
                    <span class="player-name">{inj.get('name', 'Unknown')} ({inj.get('position', 'N/A')})</span>
                    <span class="injury-type">{inj.get('injury', 'Unknown')}</span>
                </div>
                <span class="status {status_class}">{inj.get('status', 'Unknown')}</span>
            </li>'''
    html += '</ul>'
    return html


def generate_last_games_html(away_games: List, home_games: List, away_name: str, home_name: str) -> str:
    """Generate last games section HTML"""
    if not away_games and not home_games:
        return ''

    def format_games(games: List) -> str:
        if not games:
            return '<span class="no-data">No recent games</span>'
        return ''.join([
            f'<span class="game-result {"win" if g.get("result") == "W" else "loss"}">{g.get("result", "?")}</span>'
            for g in games[:10]
        ])

    return f'''
                <div class="recent-games-section">
                    <div class="section-title">RECENT FORM</div>
                    <div class="recent-grid">
                        <div class="recent-column">
                            <h5>{away_name}</h5>
                            <div class="game-results">{format_games(away_games)}</div>
                        </div>
                        <div class="recent-column">
                            <h5>{home_name}</h5>
                            <div class="game-results">{format_games(home_games)}</div>
                        </div>
                    </div>
                </div>
'''


def get_injury_status_class(status: str) -> str:
    """Get CSS class for injury status"""
    status_lower = status.lower()
    if 'out' in status_lower:
        return 'out'
    elif 'doubtful' in status_lower:
        return 'doubtful'
    elif 'questionable' in status_lower:
        return 'questionable'
    elif 'day' in status_lower:
        return 'day-to-day'
    elif 'probable' in status_lower:
        return 'probable'
    return 'questionable'


def get_edge_class(edge: float) -> str:
    """Get CSS class for edge rating"""
    if edge >= 5:
        return 'strong-positive'
    elif edge >= 2:
        return 'positive'
    elif edge <= -5:
        return 'strong-negative'
    elif edge <= -2:
        return 'negative'
    return 'neutral'


def format_spread(value) -> str:
    """Format spread value"""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        v = float(value)
        return f"+{v}" if v > 0 else str(v)
    except:
        return str(value)


def format_ml(value) -> str:
    """Format moneyline value"""
    if value is None or value == 'N/A':
        return 'N/A'
    try:
        v = int(value)
        return f"+{v}" if v > 0 else str(v)
    except:
        return str(value)


def generate_css() -> str:
    """Generate the CSS styles"""
    return '''
    <style>
        :root {
            --bg-primary: #0a0e17;
            --bg-secondary: #141b2d;
            --bg-card: #1a2332;
            --accent-cyan: #00d9ff;
            --accent-gold: #ffd700;
            --accent-orange: #fd5000;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --text-primary: #e8edf5;
            --text-secondary: #8b96a8;
            --border-color: rgba(0, 217, 255, 0.2);
            --glow-cyan: 0 0 20px rgba(0, 217, 255, 0.3);
            --glow-gold: 0 0 20px rgba(255, 215, 0, 0.3);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, #1a1f30 100%);
            background-attachment: fixed;
            font-family: 'Inter', -apple-system, sans-serif;
            color: var(--text-primary);
            min-height: 100vh;
            font-size: 14px;
            line-height: 1.5;
        }

        .header {
            background: rgba(10, 14, 23, 0.95);
            backdrop-filter: blur(20px);
            padding: 20px 30px;
            position: sticky;
            top: 0;
            z-index: 1000;
            border-bottom: 2px solid var(--border-color);
        }

        .header-content { max-width: 1400px; margin: 0 auto; }

        .header h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            color: #fff;
            font-weight: 900;
            letter-spacing: 2px;
            text-shadow: 0 0 30px rgba(0, 217, 255, 0.5);
        }

        .header h1 span { color: var(--accent-cyan); }

        .subtitle {
            color: var(--accent-gold);
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 5px;
        }

        .timestamp { color: var(--text-secondary); font-size: 12px; margin: 10px 0; }

        .tabs { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 15px; }

        .tab {
            background: rgba(0, 217, 255, 0.1);
            border: 1px solid var(--border-color);
            padding: 10px 22px;
            border-radius: 8px;
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 700;
            font-size: 13px;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }

        .tab:hover, .tab.active {
            background: linear-gradient(135deg, var(--accent-cyan), #0099cc);
            border-color: var(--accent-cyan);
            color: #000;
            box-shadow: var(--glow-cyan);
        }

        .back-link {
            color: #fff;
            text-decoration: none;
            font-size: 13px;
            opacity: 0.7;
        }

        .back-link:hover { opacity: 1; }

        .archive-link { margin-top: 15px; }
        .archive-link a {
            color: var(--accent-gold);
            text-decoration: none;
            font-size: 13px;
            padding: 10px 20px;
            border: 1px solid var(--accent-gold);
            border-radius: 8px;
        }

        .container { max-width: 1400px; margin: 0 auto; padding: 30px; }

        .section { display: none; }
        .section.active { display: block; }

        .section-header { margin-bottom: 25px; }
        .section-header h2 {
            font-family: 'Orbitron', sans-serif;
            color: var(--text-primary);
            font-size: 24px;
            display: inline-block;
            border-bottom: 3px solid var(--accent-cyan);
            padding-bottom: 10px;
        }
        .section-header .count {
            color: var(--accent-gold);
            font-size: 14px;
            margin-left: 15px;
        }

        .no-games {
            text-align: center;
            padding: 60px 20px;
            color: var(--text-secondary);
            background: var(--bg-card);
            border-radius: 15px;
            border: 1px solid var(--border-color);
        }

        .game-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 15px;
            margin-bottom: 25px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }

        .game-card:hover {
            box-shadow: 0 8px 40px rgba(0, 217, 255, 0.15);
            border-color: var(--accent-cyan);
        }

        .matchup-header {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 20px;
            align-items: center;
            padding: 25px 30px;
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.1), rgba(0, 217, 255, 0.02));
            border-bottom: 1px solid var(--border-color);
        }

        .team-box { display: flex; align-items: center; gap: 15px; }
        .team-box.home { flex-direction: row-reverse; text-align: right; }

        .team-logo {
            width: 64px;
            height: 64px;
            object-fit: contain;
            filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.2));
        }

        .team-details h3 { font-size: 18px; color: var(--text-primary); font-weight: 700; margin-bottom: 4px; }
        .team-records { font-size: 13px; color: var(--text-secondary); }
        .team-records .overall { color: var(--accent-cyan); font-weight: 700; }

        .vs-badge {
            background: linear-gradient(135deg, var(--accent-gold), #cc9900);
            padding: 12px 18px;
            border-radius: 10px;
            font-weight: 800;
            font-size: 14px;
            color: #000;
            box-shadow: var(--glow-gold);
        }

        /* Killport Model Section */
        .killport-section {
            background: linear-gradient(135deg, rgba(253, 80, 0, 0.15), rgba(255, 215, 0, 0.1));
            border: 1px solid rgba(253, 80, 0, 0.3);
            margin: 15px;
            border-radius: 12px;
            overflow: hidden;
        }

        .killport-header {
            background: linear-gradient(135deg, var(--accent-orange), #cc4000);
            padding: 12px 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .killport-logo { font-size: 20px; }

        .killport-title {
            font-family: 'Orbitron', sans-serif;
            color: #fff;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 2px;
        }

        .confidence-stars {
            margin-left: auto;
            color: var(--accent-gold);
            font-size: 16px;
            letter-spacing: 2px;
        }

        .killport-content { padding: 20px; }

        .prediction-main {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 15px;
        }

        .predicted-winner, .model-line, .edge-rating {
            text-align: center;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
        }

        .predicted-winner .label, .model-line .label, .edge-rating .label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            display: block;
            margin-bottom: 5px;
        }

        .predicted-winner .winner {
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-gold);
            display: block;
        }

        .predicted-winner .margin { font-size: 12px; color: var(--text-secondary); display: block; }

        .model-line .line {
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .edge-rating .rating {
            font-family: 'Orbitron', sans-serif;
            font-size: 20px;
            font-weight: 700;
        }

        .edge-rating .rating.strong-positive { color: var(--accent-green); }
        .edge-rating .rating.positive { color: #7fff00; }
        .edge-rating .rating.neutral { color: var(--text-secondary); }
        .edge-rating .rating.negative { color: #ff6b6b; }
        .edge-rating .rating.strong-negative { color: var(--accent-red); }

        .recommendation {
            background: rgba(0, 0, 0, 0.3);
            padding: 12px 20px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
            justify-content: center;
        }

        .recommendation.strong { border: 1px solid var(--accent-green); }
        .recommendation.moderate { border: 1px solid var(--accent-gold); }
        .recommendation.lean { border: 1px solid var(--text-secondary); }

        .rec-label {
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            color: var(--accent-cyan);
        }

        .rec-side {
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-gold);
        }

        .rec-strength { font-size: 11px; color: var(--text-secondary); }
        .rec-reasoning { font-size: 12px; color: var(--text-secondary); margin-top: 10px; text-align: center; }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            border-top: 1px solid var(--border-color);
        }

        .stats-panel {
            padding: 20px;
            border-right: 1px solid var(--border-color);
        }

        .stats-panel:last-child { border-right: none; }
        .away-panel { background: rgba(0, 217, 255, 0.03); }
        .home-panel { background: rgba(255, 215, 0, 0.03); }

        .panel-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 15px;
            letter-spacing: 1px;
        }

        .basic-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 13px;
        }

        .basic-stat span:first-child { color: var(--text-secondary); }
        .basic-stat span:last-child { font-weight: 700; font-family: 'Orbitron', sans-serif; }

        .advanced-toggle {
            padding: 12px;
            text-align: center;
            cursor: pointer;
            background: rgba(0, 217, 255, 0.1);
            border-radius: 8px;
            margin-top: 15px;
            font-size: 12px;
            color: var(--accent-cyan);
            transition: all 0.3s ease;
        }

        .advanced-toggle:hover { background: rgba(0, 217, 255, 0.2); }

        .advanced-panel {
            display: none;
            padding-top: 15px;
        }

        .advanced-panel.show { display: block; }

        .advanced-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 12px;
        }

        .advanced-stat.highlight {
            background: rgba(0, 217, 255, 0.1);
            margin: 5px -10px;
            padding: 8px 10px;
            border-radius: 6px;
            border: none;
        }

        .stat-label { color: var(--text-secondary); text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; }
        .stat-value { font-weight: 700; font-family: 'Orbitron', sans-serif; color: var(--text-primary); }

        /* Injuries Section */
        .injuries-section, .betting-section, .recent-games-section {
            padding: 20px 25px;
            border-top: 1px solid var(--border-color);
        }

        .section-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 12px;
            font-weight: 700;
            color: var(--accent-red);
            margin-bottom: 15px;
            letter-spacing: 2px;
        }

        .injuries-grid, .recent-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
        }

        .injury-column h5, .recent-column h5 {
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border-color);
        }

        .injury-list { list-style: none; }

        .injury-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 12px;
        }

        .player-info { display: flex; flex-direction: column; }
        .player-name { color: var(--text-primary); font-weight: 600; }
        .injury-type { font-size: 11px; color: var(--text-secondary); }

        .status {
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 10px;
            text-transform: uppercase;
        }

        .status.out { background: linear-gradient(135deg, #dc2626, #b91c1c); color: #fff; }
        .status.doubtful { background: linear-gradient(135deg, #ea580c, #c2410c); color: #fff; }
        .status.questionable { background: linear-gradient(135deg, #ca8a04, #a16207); color: #fff; }
        .status.day-to-day { background: linear-gradient(135deg, #0284c7, #0369a1); color: #fff; }
        .status.probable { background: linear-gradient(135deg, #16a34a, #15803d); color: #fff; }

        .no-injuries { color: var(--accent-green); font-size: 13px; }

        /* Recent Games */
        .game-results { display: flex; gap: 4px; flex-wrap: wrap; }

        .game-result {
            width: 28px;
            height: 28px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 11px;
            color: #fff;
        }

        .game-result.win { background: linear-gradient(135deg, #16a34a, #15803d); }
        .game-result.loss { background: linear-gradient(135deg, #dc2626, #b91c1c); }

        /* Betting Section */
        .betting-section { background: rgba(255, 215, 0, 0.03); }
        .betting-section .section-title { color: var(--accent-gold); }

        .betting-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .line-box { text-align: center; }

        .line-type {
            font-size: 10px;
            font-weight: 700;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }

        .line-values { display: flex; flex-direction: column; gap: 6px; }

        .line-value {
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 14px;
            color: var(--text-primary);
            background: rgba(26, 35, 50, 0.8);
            padding: 10px 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .no-data { color: var(--text-secondary); font-size: 12px; padding: 10px; text-align: center; }

        @media (max-width: 900px) {
            .matchup-header { grid-template-columns: 1fr; gap: 15px; text-align: center; }
            .team-box, .team-box.home { flex-direction: column; text-align: center; }
            .vs-badge { margin: 0 auto; }
            .stats-grid { grid-template-columns: 1fr; }
            .prediction-main { grid-template-columns: 1fr; }
            .injuries-grid, .recent-grid { grid-template-columns: 1fr; }
            .betting-grid { grid-template-columns: 1fr; }
        }
    </style>
'''


def generate_javascript() -> str:
    """Generate the JavaScript"""
    return '''
    <script>
        function showSection(sport) {
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

            document.getElementById(sport).classList.add('active');
            event.target.classList.add('active');
        }

        function toggleAdvanced(el) {
            const panel = el.nextElementSibling;
            panel.classList.toggle('show');
            el.querySelector('span').textContent = panel.classList.contains('show') ? '▲ Hide Advanced' : '▼ Advanced Analytics';
        }

        // Show first sport with games
        document.addEventListener('DOMContentLoaded', function() {
            const tabs = document.querySelectorAll('.tab');
            for (let tab of tabs) {
                const count = parseInt(tab.textContent.match(/\d+/)?.[0] || 0);
                if (count > 0) {
                    tab.click();
                    break;
                }
            }
        });
    </script>
'''


def update_handicapping_hub(html_content: str):
    """Write the HTML content to the handicapping-hub.html file"""
    repo_path = os.environ.get('GITHUB_WORKSPACE', os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    main_file = os.path.join(repo_path, "handicapping-hub.html")

    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n[SAVED] handicapping-hub.html")

    # Create dated archive
    archive_file = os.path.join(repo_path, f"handicapping-hub-{DATE_STR}.html")
    with open(archive_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"[SAVED] handicapping-hub-{DATE_STR}.html (archive)")


def main():
    """Main entry point"""
    print("\n" + "=" * 70)
    print("  BETLEGEND ADVANCED HANDICAPPING HUB")
    print("  Powered by the Killport Model")
    print("=" * 70)
    print(f"\nDate: {DATE_DISPLAY}")
    print(f"Time: {TIME_DISPLAY}")

    try:
        # Fetch all sports data
        all_data = fetch_all_sports_data()

        # Generate Killport predictions
        print("\n[KILLPORT MODEL]")
        print("  Generating predictions...")
        predictions = generate_all_predictions(all_data)

        total_predictions = sum(len(p) for p in predictions.values())
        print(f"  Generated {total_predictions} predictions")

        # Generate HTML
        print("\n[HTML GENERATION]")
        print("  Building page...")
        html_content = generate_html_content(all_data, predictions)

        # Save files
        update_handicapping_hub(html_content)

        # Summary
        print("\n" + "=" * 70)
        print("  UPDATE COMPLETE!")
        print("=" * 70)

        total_games = sum(len(d.get('games', [])) for d in all_data.values())
        print(f"\n  Total Games: {total_games}")
        for sport, data in all_data.items():
            count = len(data.get('games', []))
            if count > 0:
                print(f"    {sport}: {count} games")

        print("\n  Files updated:")
        print("    - handicapping-hub.html")
        print(f"    - handicapping-hub-{DATE_STR}.html (archive)")
        print("\n" + "=" * 70)

        # Clean old cache
        cache.clear_old(max_age_days=7)

        return 0

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
