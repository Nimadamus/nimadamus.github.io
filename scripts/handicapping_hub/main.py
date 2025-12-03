"""
ADVANCED HANDICAPPING HUB - MAIN ORCHESTRATION
===============================================
Coordinates all data fetchers and generates the HTML output.

This is the main entry point for the daily update workflow.
VERSION 2.0 - Integrated Advanced Analytics

Features:
- Multi-sport support (NBA, NHL, MLB, NFL, NCAAF, NCAAB)
- Advanced statistics (wOBA, xG, EPA, etc.)
- Killport Model V2 predictions
- Historical performance tracking
- ATS records and public betting %
- Sharp money indicators
- Power ratings and head-to-head history
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handicapping_hub.nba_fetcher import NBAFetcher
from handicapping_hub.nhl_fetcher import NHLFetcher
from handicapping_hub.mlb_fetcher import MLBFetcher
from handicapping_hub.football_fetcher import NFLFetcher, NCAAFFetcher, NCAABFetcher
from handicapping_hub.base_fetcher import OddsClient
from handicapping_hub.killport_model import KillportModel, generate_all_predictions
from handicapping_hub.cache import cache

# Import V2 modules
try:
    from handicapping_hub.killport_v2 import KillportModelV2
    from handicapping_hub.historical_tracker import tracker
    from handicapping_hub.advanced_scrapers import (
        BaseballSavantScraper,
        NaturalStatTrickScraper,
        CoversScraper,
        TeamRankingsScraper,
        HeadToHeadScraper,
        ActionNetworkScraper
    )
    ADVANCED_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Advanced modules not available: {e}")
    ADVANCED_MODULES_AVAILABLE = False


# Configuration
TODAY = datetime.now()
DATE_STR = TODAY.strftime("%Y-%m-%d")
DATE_DISPLAY = TODAY.strftime("%B %d, %Y")
TIME_DISPLAY = TODAY.strftime("%I:%M %p")


def fetch_advanced_data() -> Dict:
    """
    Fetch advanced data from scrapers (ATS, public betting, sharp money, etc.)
    """
    advanced_data = {
        'ats_records': {},
        'public_betting': {},
        'sharp_money': {},
        'power_ratings': {},
        'h2h_history': {},
        'statcast': {},
        'nhl_advanced': {},
    }

    if not ADVANCED_MODULES_AVAILABLE:
        print("[INFO] Advanced modules not available - using basic data only")
        return advanced_data

    print("\n[ADVANCED DATA COLLECTION]")

    # Covers.com ATS and Public Betting
    try:
        print("  Fetching ATS records and public betting...")
        covers = CoversScraper()
        for sport in ['NBA', 'NHL', 'NFL', 'NCAAF', 'NCAAB']:
            public = covers.get_public_betting(sport)
            if public:
                # Convert list to dict keyed by matchup
                for game in public:
                    matchup = game.get('matchup', '')
                    if matchup:
                        if sport not in advanced_data['public_betting']:
                            advanced_data['public_betting'][sport] = {}
                        advanced_data['public_betting'][sport][matchup] = game
        print(f"    [OK] Public betting loaded for {len(advanced_data['public_betting'])} sports")
    except Exception as e:
        print(f"    [X] Covers scraper failed: {e}")

    # TeamRankings Power Ratings
    try:
        print("  Fetching power ratings...")
        rankings = TeamRankingsScraper()
        for sport in ['NBA', 'NHL', 'NFL', 'NCAAF', 'NCAAB']:
            ratings = rankings.get_power_ratings(sport)
            if ratings:
                advanced_data['power_ratings'][sport] = ratings
        print(f"    [OK] Power ratings loaded for {len(advanced_data['power_ratings'])} sports")
    except Exception as e:
        print(f"    [X] TeamRankings scraper failed: {e}")

    # Sharp Money Indicators (ActionNetwork)
    try:
        print("  Fetching sharp money indicators...")
        action = ActionNetworkScraper()
        for sport in ['NBA', 'NHL', 'NFL']:
            sharp = action.get_sharp_action(sport)
            if sharp:
                advanced_data['sharp_money'][sport] = sharp
        print(f"    [OK] Sharp money loaded for {len(advanced_data['sharp_money'])} sports")
    except Exception as e:
        print(f"    [X] ActionNetwork scraper failed: {e}")

    # Baseball Savant Statcast (MLB only)
    try:
        print("  Fetching Baseball Savant data...")
        savant = BaseballSavantScraper()
        # Get team statcast for common teams
        statcast = {}
        for team in ['NYY', 'BOS', 'LAD', 'CHC', 'HOU', 'ATL', 'PHI', 'SD', 'SEA', 'TB']:
            team_data = savant.get_team_statcast(team)
            if team_data:
                statcast[team] = team_data
        if statcast:
            advanced_data['statcast'] = statcast
            print(f"    [OK] Statcast data loaded for {len(statcast)} teams")
    except Exception as e:
        print(f"    [X] Baseball Savant failed: {e}")

    # Natural Stat Trick (NHL only)
    try:
        print("  Fetching Natural Stat Trick data...")
        nst = NaturalStatTrickScraper()
        # Get analytics for common NHL teams
        nhl_adv = {}
        for team in ['BOS', 'TOR', 'FLA', 'NYR', 'CAR', 'EDM', 'VGK', 'COL', 'DAL', 'WPG']:
            team_data = nst.get_team_analytics(team)
            if team_data:
                nhl_adv[team] = team_data
        if nhl_adv:
            advanced_data['nhl_advanced'] = nhl_adv
            print(f"    [OK] NST data loaded for {len(nhl_adv)} teams")
    except Exception as e:
        print(f"    [X] Natural Stat Trick failed: {e}")

    return advanced_data


def fetch_all_sports_data() -> Dict:
    """
    Fetch comprehensive data for all sports.
    """
    print("\n" + "=" * 60)
    print("ADVANCED HANDICAPPING HUB - DATA COLLECTION V2.0")
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

    # Fetch advanced data first
    advanced_data = fetch_advanced_data()

    for sport, fetcher in fetchers.items():
        try:
            sport_data = fetcher.fetch_all()

            # Add odds data
            if odds_client and sport_data.get('games'):
                odds = odds_client.get_odds(sport)
                for game_data in sport_data['games']:
                    game = game_data.get('game', {})
                    away = game.get('away', {})
                    home = game.get('home', {})
                    away_name = away.get('name', '')
                    home_name = home.get('name', '')
                    game_key = f"{away_name} @ {home_name}"
                    game_data['odds'] = odds.get(game_key, {})

                    # Add ATS records
                    sport_ats = advanced_data.get('ats_records', {}).get(sport, {})
                    game_data['away_ats'] = sport_ats.get(away_name, sport_ats.get(away.get('abbreviation', ''), {}))
                    game_data['home_ats'] = sport_ats.get(home_name, sport_ats.get(home.get('abbreviation', ''), {}))

                    # Add public betting
                    sport_public = advanced_data.get('public_betting', {}).get(sport, {})
                    game_data['public_betting'] = sport_public.get(game_key, {})

                    # Add sharp money
                    sport_sharp = advanced_data.get('sharp_money', {}).get(sport, {})
                    game_data['sharp_money'] = sport_sharp.get(game_key, {})

                    # Add power ratings
                    sport_power = advanced_data.get('power_ratings', {}).get(sport, {})
                    game_data['away_power'] = sport_power.get(away_name, sport_power.get(away.get('abbreviation', ''), {}))
                    game_data['home_power'] = sport_power.get(home_name, sport_power.get(home.get('abbreviation', ''), {}))

                    # Add sport-specific advanced data
                    if sport == 'MLB':
                        statcast = advanced_data.get('statcast', {})
                        game_data['away_statcast'] = statcast.get(away_name, {})
                        game_data['home_statcast'] = statcast.get(home_name, {})
                    elif sport == 'NHL':
                        nst = advanced_data.get('nhl_advanced', {})
                        game_data['away_nst'] = nst.get(away_name, {})
                        game_data['home_nst'] = nst.get(home_name, {})

            all_data[sport] = sport_data

        except Exception as e:
            print(f"\n[ERROR] Failed to fetch {sport} data: {e}")
            all_data[sport] = {'sport': sport, 'games': [], 'error': str(e)}

    return all_data


def generate_model_record_html() -> str:
    """Generate the model performance record section"""
    if not ADVANCED_MODULES_AVAILABLE:
        return ''

    try:
        return tracker.generate_record_html()
    except Exception as e:
        print(f"[WARNING] Could not generate model record: {e}")
        return ''


def generate_html_content(all_data: Dict, predictions: Dict) -> str:
    """
    Generate the complete HTML content for the Handicapping Hub.
    """
    # Count games by sport
    game_counts = {sport: len(data.get('games', [])) for sport, data in all_data.items()}

    # Generate model record
    model_record_html = generate_model_record_html()

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

    # Count total predictions
    total_predictions = sum(len(predictions.get(s, [])) for s in predictions)

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
            <p class="subtitle">Powered by the Killport Model V2</p>
            <div class="timestamp">Last updated: {DATE_DISPLAY} at {TIME_DISPLAY} &bull; Data from ESPN + Advanced Analytics</div>
            <div class="stats-bar">
                <div class="stat-item"><span class="stat-num">{total_predictions}</span><span class="stat-label">Predictions</span></div>
                <div class="stat-item"><span class="stat-num">{sum(game_counts.values())}</span><span class="stat-label">Games Today</span></div>
                <div class="stat-item"><span class="stat-num">6</span><span class="stat-label">Sports Covered</span></div>
            </div>
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

    # Get new advanced data
    away_ats = game_data.get('away_ats', {})
    home_ats = game_data.get('home_ats', {})
    public_betting = game_data.get('public_betting', {})
    sharp_money = game_data.get('sharp_money', {})
    away_power = game_data.get('away_power', {})
    home_power = game_data.get('home_power', {})

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

    # Generate ATS and Betting Intelligence section
    betting_intel_html = generate_betting_intel_html(away.get('name', ''), home.get('name', ''),
                                                      away_ats, home_ats, public_betting, sharp_money,
                                                      away_power, home_power)

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

                {betting_intel_html}

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


def generate_betting_intel_html(away_name: str, home_name: str, away_ats: Dict, home_ats: Dict,
                                 public_betting: Dict, sharp_money: Dict,
                                 away_power: Dict, home_power: Dict) -> str:
    """Generate the betting intelligence section with ATS, public betting, sharp money, and power ratings"""

    # Format ATS records
    away_ats_str = f"{away_ats.get('wins', 0)}-{away_ats.get('losses', 0)}" if away_ats else 'N/A'
    home_ats_str = f"{home_ats.get('wins', 0)}-{home_ats.get('losses', 0)}" if home_ats else 'N/A'
    away_ats_pct = away_ats.get('win_pct', 'N/A') if away_ats else 'N/A'
    home_ats_pct = home_ats.get('win_pct', 'N/A') if home_ats else 'N/A'

    # Format public betting
    away_public = public_betting.get('away_pct', 'N/A')
    home_public = public_betting.get('home_pct', 'N/A')
    away_public_ml = public_betting.get('away_ml_pct', 'N/A')
    home_public_ml = public_betting.get('home_ml_pct', 'N/A')

    # Format sharp money
    sharp_side = sharp_money.get('side', 'N/A')
    sharp_indicator = sharp_money.get('indicator', '')
    rlm = sharp_money.get('rlm', False)
    steam_move = sharp_money.get('steam_move', False)

    # Format power ratings
    away_power_val = away_power.get('rating', 'N/A') if away_power else 'N/A'
    home_power_val = home_power.get('rating', 'N/A') if home_power else 'N/A'
    away_rank = away_power.get('rank', 'N/A') if away_power else 'N/A'
    home_rank = home_power.get('rank', 'N/A') if home_power else 'N/A'

    # Build sharp indicators HTML
    sharp_indicators_html = ''
    if rlm:
        sharp_indicators_html += '<span class="sharp-indicator rlm">RLM</span>'
    if steam_move:
        sharp_indicators_html += '<span class="sharp-indicator steam">STEAM</span>'
    if sharp_side and sharp_side != 'N/A':
        sharp_indicators_html += f'<span class="sharp-side">Sharp: {sharp_side}</span>'

    # Only return content if we have any data
    has_data = (away_ats or home_ats or public_betting or sharp_money or away_power or home_power)
    if not has_data:
        return ''

    return f'''
                <div class="betting-intel-section">
                    <div class="section-title">BETTING INTELLIGENCE</div>
                    <div class="intel-grid">
                        <div class="intel-box ats-box">
                            <div class="intel-header">ATS RECORDS</div>
                            <div class="intel-content">
                                <div class="intel-row">
                                    <span class="team-name">{away_name}</span>
                                    <span class="ats-record">{away_ats_str}</span>
                                    <span class="ats-pct">{away_ats_pct}%</span>
                                </div>
                                <div class="intel-row">
                                    <span class="team-name">{home_name}</span>
                                    <span class="ats-record">{home_ats_str}</span>
                                    <span class="ats-pct">{home_ats_pct}%</span>
                                </div>
                            </div>
                        </div>
                        <div class="intel-box public-box">
                            <div class="intel-header">PUBLIC BETTING</div>
                            <div class="intel-content">
                                <div class="intel-row">
                                    <span class="team-name">{away_name}</span>
                                    <span class="public-pct spread">Spread: {away_public}%</span>
                                    <span class="public-pct ml">ML: {away_public_ml}%</span>
                                </div>
                                <div class="intel-row">
                                    <span class="team-name">{home_name}</span>
                                    <span class="public-pct spread">Spread: {home_public}%</span>
                                    <span class="public-pct ml">ML: {home_public_ml}%</span>
                                </div>
                            </div>
                        </div>
                        <div class="intel-box sharp-box">
                            <div class="intel-header">SHARP MONEY</div>
                            <div class="intel-content">
                                <div class="sharp-indicators">
                                    {sharp_indicators_html if sharp_indicators_html else '<span class="no-data">No sharp action detected</span>'}
                                </div>
                            </div>
                        </div>
                        <div class="intel-box power-box">
                            <div class="intel-header">POWER RATINGS</div>
                            <div class="intel-content">
                                <div class="intel-row">
                                    <span class="team-name">{away_name}</span>
                                    <span class="power-rating">{away_power_val}</span>
                                    <span class="power-rank">#{away_rank}</span>
                                </div>
                                <div class="intel-row">
                                    <span class="team-name">{home_name}</span>
                                    <span class="power-rating">{home_power_val}</span>
                                    <span class="power-rank">#{home_rank}</span>
                                </div>
                            </div>
                        </div>
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
    """Generate the CSS styles - ULTRA MODERN FUTURISTIC DESIGN V3"""
    return '''
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

        :root {
            --bg-dark: #000000;
            --bg-card: #0a0f1a;
            --bg-panel: #0d1524;
            --accent-cyan: #00f0ff;
            --accent-gold: #ffcc00;
            --accent-orange: #ff6b00;
            --accent-green: #00ff88;
            --accent-red: #ff3366;
            --accent-purple: #9945ff;
            --text-white: #ffffff;
            --text-gray: #8899aa;
            --text-dim: #556677;
            --border-glow: rgba(0, 240, 255, 0.3);
            --card-glow: 0 0 60px rgba(0, 240, 255, 0.15);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg-dark);
            background-image:
                radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0, 240, 255, 0.12), transparent),
                radial-gradient(ellipse 60% 40% at 50% 110%, rgba(255, 204, 0, 0.08), transparent);
            background-attachment: fixed;
            font-family: 'Space Grotesk', sans-serif;
            color: var(--text-white);
            min-height: 100vh;
            font-size: 16px;
            line-height: 1.7;
        }

        /* ======== HEADER ======== */
        .header {
            background: linear-gradient(180deg, rgba(0, 15, 30, 0.98), rgba(0, 0, 0, 0.95));
            padding: 60px 40px 50px;
            text-align: center;
            border-bottom: 2px solid var(--border-glow);
            position: relative;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--accent-cyan), var(--accent-gold), var(--accent-cyan), transparent);
        }

        .header-content {
            max-width: 1100px;
            margin: 0 auto;
        }

        .back-link {
            display: inline-block;
            color: var(--accent-cyan);
            text-decoration: none;
            font-size: 15px;
            margin-bottom: 30px;
            padding: 10px 20px;
            border: 1px solid rgba(0, 240, 255, 0.3);
            border-radius: 8px;
            transition: all 0.3s;
        }

        .back-link:hover {
            background: rgba(0, 240, 255, 0.1);
            border-color: var(--accent-cyan);
        }

        .header h1 {
            font-family: 'Orbitron', sans-serif;
            font-size: 56px;
            font-weight: 900;
            letter-spacing: 8px;
            text-transform: uppercase;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #fff 0%, var(--accent-cyan) 50%, var(--accent-gold) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 80px rgba(0, 240, 255, 0.5);
        }

        .header h1 span {
            background: linear-gradient(135deg, var(--accent-gold), var(--accent-orange));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .subtitle {
            font-family: 'Orbitron', sans-serif;
            color: var(--accent-gold);
            font-size: 16px;
            text-transform: uppercase;
            letter-spacing: 6px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .timestamp {
            color: var(--text-dim);
            font-size: 14px;
            margin: 20px 0;
            letter-spacing: 1px;
        }

        /* ======== STATS BAR ======== */
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 80px;
            margin: 40px 0;
            padding: 30px 50px;
            background: linear-gradient(135deg, rgba(0, 240, 255, 0.08), rgba(255, 204, 0, 0.05));
            border: 1px solid var(--border-glow);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }

        .stat-item {
            text-align: center;
        }

        .stat-item .stat-num {
            font-family: 'Orbitron', sans-serif;
            font-size: 52px;
            font-weight: 900;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
            display: block;
        }

        .stat-item .stat-label {
            font-size: 13px;
            color: var(--text-gray);
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-top: 10px;
            font-weight: 600;
            display: block;
        }

        /* ======== TABS ======== */
        .tabs {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
            margin: 40px 0 30px;
        }

        .tab {
            background: transparent;
            border: 2px solid rgba(0, 240, 255, 0.25);
            padding: 18px 40px;
            border-radius: 14px;
            color: var(--text-white);
            cursor: pointer;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 16px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .tab:hover {
            border-color: var(--accent-cyan);
            background: rgba(0, 240, 255, 0.1);
            box-shadow: 0 0 30px rgba(0, 240, 255, 0.2);
        }

        .tab.active {
            background: linear-gradient(135deg, var(--accent-cyan), #0099cc);
            border-color: transparent;
            color: #000;
            box-shadow: 0 0 50px rgba(0, 240, 255, 0.5);
            font-weight: 900;
        }

        .archive-link {
            margin-top: 30px;
        }

        .archive-link a {
            font-family: 'Orbitron', sans-serif;
            color: var(--accent-gold);
            text-decoration: none;
            font-size: 14px;
            padding: 15px 35px;
            border: 2px solid var(--accent-gold);
            border-radius: 12px;
            transition: all 0.3s;
            letter-spacing: 2px;
            font-weight: 600;
        }

        .archive-link a:hover {
            background: rgba(255, 204, 0, 0.15);
            box-shadow: 0 0 30px rgba(255, 204, 0, 0.3);
        }

        /* ======== CONTAINER ======== */
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 50px 30px;
        }

        .section { display: none; }
        .section.active { display: block; }

        .section-header {
            text-align: center;
            margin-bottom: 50px;
        }

        .section-header h2 {
            font-family: 'Orbitron', sans-serif;
            color: var(--text-white);
            font-size: 38px;
            font-weight: 800;
            display: inline-block;
            position: relative;
            padding-bottom: 20px;
            letter-spacing: 4px;
        }

        .section-header h2::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 150px;
            height: 4px;
            background: linear-gradient(90deg, var(--accent-cyan), var(--accent-gold));
            border-radius: 2px;
        }

        .section-header .count {
            display: block;
            color: var(--accent-gold);
            font-size: 18px;
            margin-top: 15px;
            font-weight: 600;
            letter-spacing: 2px;
        }

        .no-games {
            text-align: center;
            padding: 100px 40px;
            color: var(--text-gray);
            background: var(--bg-card);
            border-radius: 24px;
            border: 1px solid var(--border-glow);
            font-size: 20px;
        }

        /* ======== GAME CARD ======== */
        .game-card {
            background: var(--bg-card);
            border: 1px solid var(--border-glow);
            border-radius: 28px;
            margin-bottom: 50px;
            overflow: hidden;
            box-shadow: var(--card-glow);
            transition: all 0.4s ease;
        }

        .game-card:hover {
            box-shadow: 0 0 80px rgba(0, 240, 255, 0.25);
            border-color: var(--accent-cyan);
            transform: translateY(-4px);
        }

        /* ======== MATCHUP HEADER ======== */
        .matchup-header {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 40px;
            align-items: center;
            padding: 45px 50px;
            background: linear-gradient(180deg, rgba(0, 240, 255, 0.08), transparent);
        }

        .team-box {
            display: flex;
            align-items: center;
            gap: 25px;
        }

        .team-box.home {
            flex-direction: row-reverse;
            text-align: right;
        }

        .team-logo {
            width: 95px;
            height: 95px;
            object-fit: contain;
            filter: drop-shadow(0 0 25px rgba(255, 255, 255, 0.2));
        }

        .team-details h3 {
            font-size: 26px;
            color: var(--text-white);
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }

        .team-records {
            font-size: 15px;
            color: var(--text-gray);
            line-height: 1.6;
        }

        .team-records .overall {
            color: var(--accent-cyan);
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 22px;
        }

        .vs-badge {
            background: linear-gradient(135deg, var(--accent-gold), var(--accent-orange));
            padding: 22px 32px;
            border-radius: 16px;
            font-family: 'Orbitron', sans-serif;
            font-weight: 900;
            font-size: 22px;
            color: #000;
            box-shadow: 0 0 40px rgba(255, 204, 0, 0.4);
            letter-spacing: 3px;
        }

        /* ======== KILLPORT MODEL ======== */
        .killport-section {
            background: linear-gradient(135deg, rgba(255, 107, 0, 0.15), rgba(255, 204, 0, 0.08));
            border: 2px solid rgba(255, 107, 0, 0.4);
            margin: 25px;
            border-radius: 20px;
            overflow: hidden;
        }

        .killport-header {
            background: linear-gradient(135deg, var(--accent-orange), #cc5500);
            padding: 18px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .killport-logo { font-size: 28px; }

        .killport-title {
            font-family: 'Orbitron', sans-serif;
            color: #fff;
            font-weight: 800;
            font-size: 18px;
            letter-spacing: 3px;
        }

        .confidence-stars {
            margin-left: auto;
            color: var(--accent-gold);
            font-size: 22px;
            letter-spacing: 4px;
        }

        .killport-content { padding: 30px; }

        .prediction-main {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 25px;
            margin-bottom: 25px;
        }

        .predicted-winner, .model-line, .edge-rating {
            text-align: center;
            padding: 25px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .predicted-winner .label, .model-line .label, .edge-rating .label {
            font-size: 12px;
            color: var(--text-gray);
            text-transform: uppercase;
            letter-spacing: 2px;
            display: block;
            margin-bottom: 10px;
        }

        .predicted-winner .winner {
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 800;
            color: var(--accent-gold);
            display: block;
        }

        .predicted-winner .margin {
            font-size: 14px;
            color: var(--text-gray);
            display: block;
            margin-top: 5px;
        }

        .model-line .line {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            font-weight: 800;
            color: var(--text-white);
        }

        .edge-rating .rating {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            font-weight: 800;
        }

        .edge-rating .rating.strong-positive { color: var(--accent-green); }
        .edge-rating .rating.positive { color: #88ff88; }
        .edge-rating .rating.neutral { color: var(--text-gray); }
        .edge-rating .rating.negative { color: #ff8888; }
        .edge-rating .rating.strong-negative { color: var(--accent-red); }

        .recommendation {
            background: rgba(0, 0, 0, 0.4);
            padding: 20px 30px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            gap: 15px;
            justify-content: center;
        }

        .recommendation.strong { border: 2px solid var(--accent-green); }
        .recommendation.moderate { border: 2px solid var(--accent-gold); }
        .recommendation.lean { border: 2px solid var(--text-dim); }

        .rec-label {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            color: var(--accent-cyan);
            letter-spacing: 1px;
        }

        .rec-side {
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 800;
            color: var(--accent-gold);
        }

        .rec-strength {
            font-size: 13px;
            color: var(--text-gray);
        }

        .rec-reasoning {
            font-size: 14px;
            color: var(--text-gray);
            margin-top: 15px;
            text-align: center;
            line-height: 1.6;
        }

        /* ======== STATS GRID ======== */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
        }

        .stats-panel {
            padding: 30px 35px;
            border-top: 1px solid var(--border-glow);
        }

        .stats-panel:first-child { border-right: 1px solid var(--border-glow); }
        .away-panel { background: rgba(0, 240, 255, 0.03); }
        .home-panel { background: rgba(255, 204, 0, 0.03); }

        .panel-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 20px;
            letter-spacing: 2px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-glow);
        }

        .basic-stat {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 15px;
        }

        .basic-stat span:first-child {
            color: var(--text-gray);
            font-weight: 500;
        }

        .basic-stat span:last-child {
            font-weight: 700;
            font-family: 'Orbitron', sans-serif;
            color: var(--text-white);
            font-size: 16px;
        }

        /* Advanced stats always visible */
        .advanced-toggle { display: none; }

        .advanced-panel {
            display: block;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 2px dashed rgba(0, 240, 255, 0.2);
        }

        .advanced-stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 14px;
        }

        .advanced-stat.highlight {
            background: linear-gradient(90deg, rgba(0, 240, 255, 0.12), transparent);
            margin: 8px -15px;
            padding: 12px 15px;
            border-radius: 10px;
            border: none;
        }

        .stat-label {
            color: var(--text-gray);
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
            font-weight: 600;
        }

        .stat-value {
            font-weight: 700;
            font-family: 'Orbitron', sans-serif;
            color: var(--text-white);
            font-size: 15px;
        }

        /* ======== SECTIONS ======== */
        .injuries-section, .betting-section, .recent-games-section, .betting-intel-section {
            padding: 30px 35px;
            border-top: 1px solid var(--border-glow);
        }

        .section-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 20px;
            letter-spacing: 3px;
            text-transform: uppercase;
        }

        .injuries-section .section-title { color: var(--accent-red); }
        .betting-section .section-title { color: var(--accent-gold); }
        .recent-games-section .section-title { color: var(--accent-purple); }
        .betting-intel-section .section-title { color: var(--accent-cyan); }

        .injuries-grid, .recent-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }

        .injury-column h5, .recent-column h5 {
            font-size: 16px;
            font-weight: 700;
            color: var(--text-white);
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--border-glow);
        }

        .injury-list { list-style: none; }

        .injury-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            font-size: 14px;
        }

        .player-info { display: flex; flex-direction: column; }
        .player-name { color: var(--text-white); font-weight: 600; font-size: 15px; }
        .injury-type { font-size: 13px; color: var(--text-dim); margin-top: 3px; }

        .status {
            font-weight: 700;
            padding: 6px 14px;
            border-radius: 8px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status.out { background: linear-gradient(135deg, #ff3366, #cc1144); color: #fff; }
        .status.doubtful { background: linear-gradient(135deg, #ff6600, #cc5500); color: #fff; }
        .status.questionable { background: linear-gradient(135deg, #ffaa00, #cc8800); color: #000; }
        .status.day-to-day { background: linear-gradient(135deg, #0088ff, #0066cc); color: #fff; }
        .status.probable { background: linear-gradient(135deg, #00cc66, #009944); color: #fff; }

        .no-injuries { color: var(--accent-green); font-size: 15px; font-weight: 600; }

        /* Recent Games */
        .game-results { display: flex; gap: 6px; flex-wrap: wrap; }

        .game-result {
            width: 36px;
            height: 36px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 13px;
            color: #fff;
        }

        .game-result.win { background: linear-gradient(135deg, var(--accent-green), #00aa55); }
        .game-result.loss { background: linear-gradient(135deg, var(--accent-red), #cc2244); }

        /* Betting Section */
        .betting-section { background: rgba(255, 204, 0, 0.03); }

        .betting-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 25px;
        }

        .line-box { text-align: center; }

        .line-type {
            font-size: 12px;
            font-weight: 700;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
        }

        .line-values { display: flex; flex-direction: column; gap: 10px; }

        .line-value {
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 17px;
            color: var(--text-white);
            background: rgba(255, 255, 255, 0.05);
            padding: 15px 20px;
            border-radius: 12px;
            border: 1px solid var(--border-glow);
        }

        .no-data {
            color: var(--text-dim);
            font-size: 14px;
            padding: 15px;
            text-align: center;
        }

        /* Betting Intelligence */
        .betting-intel-section { background: rgba(0, 240, 255, 0.03); }

        .intel-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }

        .intel-box {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-glow);
            border-radius: 14px;
            padding: 20px;
        }

        .intel-header {
            font-family: 'Orbitron', sans-serif;
            font-size: 11px;
            font-weight: 700;
            color: var(--accent-cyan);
            margin-bottom: 15px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        .intel-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            font-size: 13px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .intel-row .team-name {
            color: var(--text-gray);
            max-width: 80px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .intel-row .ats-record { font-weight: 700; color: var(--text-white); }
        .intel-row .ats-pct { color: var(--accent-cyan); font-weight: 700; }
        .intel-row .public-pct { font-size: 12px; color: var(--text-white); }
        .intel-row .power-rating { font-family: 'Orbitron', sans-serif; font-weight: 700; color: var(--accent-gold); }
        .intel-row .power-rank { font-size: 12px; color: var(--text-dim); }

        .sharp-indicators {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            padding: 10px 0;
        }

        .sharp-indicator {
            padding: 8px 14px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .sharp-indicator.rlm { background: linear-gradient(135deg, var(--accent-purple), #6622cc); color: #fff; }
        .sharp-indicator.steam { background: linear-gradient(135deg, var(--accent-orange), #cc5500); color: #fff; }
        .sharp-side { font-size: 14px; color: var(--accent-gold); font-weight: 700; }

        /* ======== RESPONSIVE ======== */
        @media (max-width: 1000px) {
            .header h1 { font-size: 42px; letter-spacing: 4px; }
            .stats-bar { gap: 40px; padding: 25px; }
            .stat-item .stat-num { font-size: 40px; }
            .matchup-header { padding: 35px; gap: 25px; }
            .team-logo { width: 75px; height: 75px; }
            .team-details h3 { font-size: 22px; }
        }

        @media (max-width: 768px) {
            .header h1 { font-size: 32px; letter-spacing: 2px; }
            .stats-bar { flex-direction: column; gap: 25px; }
            .tabs { gap: 10px; }
            .tab { padding: 14px 25px; font-size: 14px; }
            .matchup-header { grid-template-columns: 1fr; text-align: center; }
            .team-box, .team-box.home { flex-direction: column; text-align: center; }
            .vs-badge { margin: 15px auto; }
            .stats-grid { grid-template-columns: 1fr; }
            .stats-panel:first-child { border-right: none; border-bottom: 1px solid var(--border-glow); }
            .prediction-main { grid-template-columns: 1fr; }
            .injuries-grid, .recent-grid { grid-template-columns: 1fr; }
            .betting-grid { grid-template-columns: 1fr; }
            .intel-grid { grid-template-columns: 1fr 1fr; }
        }

        @media (max-width: 500px) {
            .header { padding: 40px 20px; }
            .header h1 { font-size: 26px; }
            .container { padding: 30px 15px; }
            .intel-grid { grid-template-columns: 1fr; }
            .killport-section { margin: 15px; }
            .matchup-header { padding: 25px 20px; }
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
