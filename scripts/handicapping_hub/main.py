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
        teams_fetched = set()
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

                    # Also fetch ATS records for each team
                    home_team = game.get('home_team', '')
                    away_team = game.get('away_team', '')
                    for team_name in [home_team, away_team]:
                        if team_name and (sport, team_name) not in teams_fetched:
                            teams_fetched.add((sport, team_name))
                            ats = covers.get_team_ats_record(team_name, sport)
                            if ats and ats.get('ats_overall') != 'N/A':
                                if sport not in advanced_data['ats_records']:
                                    advanced_data['ats_records'][sport] = {}
                                advanced_data['ats_records'][sport][team_name] = ats

        print(f"    [OK] Public betting loaded for {len(advanced_data['public_betting'])} sports")
        print(f"    [OK] ATS records loaded for {len(teams_fetched)} teams")
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
        for sport in ['NBA', 'NHL', 'NFL', 'NCAAB', 'NCAAF']:
            sharp = action.get_sharp_action(sport)
            if sharp:
                # Convert list to dict keyed by matchup
                for game in sharp:
                    matchup = game.get('matchup', '')
                    if matchup:
                        if sport not in advanced_data['sharp_money']:
                            advanced_data['sharp_money'][sport] = {}
                        advanced_data['sharp_money'][sport][matchup] = game
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

            # Add odds data (only if we have API key)
            odds = {}
            if odds_client:
                odds = odds_client.get_odds(sport)

            # Add betting intelligence to each game (regardless of odds API)
            if sport_data.get('games'):
                for game_data in sport_data['games']:
                    game = game_data.get('game', {})
                    away = game.get('away', {})
                    home = game.get('home', {})
                    # Use displayName for full team name (e.g., "Cleveland Cavaliers")
                    away_name = away.get('displayName', away.get('name', ''))
                    home_name = home.get('displayName', home.get('name', ''))
                    game_key = f"{away_name} @ {home_name}"

                    # Add odds if available
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
    <!-- SITE NAVIGATION -->
    <nav class="site-nav">
        <div class="nav-container">
            <a href="index.html" class="nav-logo">BETLEGEND</a>
            <div class="nav-links">
                <a href="index.html">Home</a>
                <a href="nba.html">NBA</a>
                <a href="nhl.html">NHL</a>
                <a href="nfl.html">NFL</a>
                <a href="ncaab.html">NCAAB</a>
                <a href="ncaaf.html">NCAAF</a>
                <a href="mlb.html">MLB</a>
                <a href="blog.html">Blog</a>
            </div>
        </div>
    </nav>

    <div class="header">
        <div class="header-content">
            <a href="index.html" class="back-link">&larr; Back to BetLegend</a>
            <h1>ADVANCED HANDICAPPING <span>HUB</span></h1>
            <p class="subtitle">Powered by the Killport Model V2</p>
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

    <!-- STATS GLOSSARY -->
    <div class="glossary-section">
        <div class="glossary-container">
            <h2>STATS GLOSSARY</h2>
            <p class="glossary-intro">Understanding the advanced metrics shown in the Handicapping Hub:</p>
            <div class="glossary-grid">
                <div class="glossary-category">
                    <h3>BASKETBALL STATS</h3>
                    <dl>
                        <dt>OFF RTG</dt><dd>Offensive Rating - Points scored per 100 possessions</dd>
                        <dt>DEF RTG</dt><dd>Defensive Rating - Points allowed per 100 possessions (lower is better)</dd>
                        <dt>NET RTG</dt><dd>Net Rating - OFF RTG minus DEF RTG (positive means outscoring opponents)</dd>
                        <dt>PACE</dt><dd>Possessions per 48 minutes - measures game tempo</dd>
                        <dt>eFG%</dt><dd>Effective Field Goal % - FG% adjusted for 3-pointers worth more</dd>
                        <dt>TS%</dt><dd>True Shooting % - Scoring efficiency including free throws</dd>
                        <dt>AST%</dt><dd>Assist Percentage - % of teammate field goals assisted</dd>
                        <dt>TOV%</dt><dd>Turnover % - Turnovers per 100 plays</dd>
                        <dt>OREB%</dt><dd>Offensive Rebound % - % of available offensive rebounds grabbed</dd>
                        <dt>DREB%</dt><dd>Defensive Rebound % - % of available defensive rebounds grabbed</dd>
                        <dt>PIE</dt><dd>Player Impact Estimate - Overall contribution metric (0.50 = league average)</dd>
                    </dl>
                </div>
                <div class="glossary-category">
                    <h3>BETTING TERMS</h3>
                    <dl>
                        <dt>ATS</dt><dd>Against The Spread - Win/loss record when factoring in point spread</dd>
                        <dt>POWER RATING</dt><dd>Calculated team strength (70-100 scale, higher = better)</dd>
                        <dt>PUBLIC %</dt><dd>Percentage of bets on each side from recreational bettors</dd>
                        <dt>RLM</dt><dd>Reverse Line Movement - Line moves opposite of public betting (sharp indicator)</dd>
                        <dt>STEAM MOVE</dt><dd>Sudden, significant line movement indicating sharp action</dd>
                        <dt>SPREAD</dt><dd>Point handicap for betting purposes</dd>
                        <dt>O/U</dt><dd>Over/Under total points line</dd>
                        <dt>ML</dt><dd>Moneyline - Straight up winner odds</dd>
                    </dl>
                </div>
                <div class="glossary-category">
                    <h3>HOCKEY STATS</h3>
                    <dl>
                        <dt>CF%</dt><dd>Corsi For % - Shot attempts for vs against (possession proxy)</dd>
                        <dt>xGF%</dt><dd>Expected Goals For % - Goal probability based on shot quality</dd>
                        <dt>PDO</dt><dd>Shooting % + Save % (100 = league average, regresses to mean)</dd>
                        <dt>GSAA</dt><dd>Goals Saved Above Average - Goalie performance vs average</dd>
                        <dt>SV%</dt><dd>Save Percentage - Shots saved divided by shots faced</dd>
                    </dl>
                </div>
                <div class="glossary-category">
                    <h3>FOOTBALL STATS</h3>
                    <dl>
                        <dt>EPA</dt><dd>Expected Points Added - Value added on each play</dd>
                        <dt>DVOA</dt><dd>Defense-adjusted Value Over Average - Efficiency vs league average</dd>
                        <dt>PPG DIFF</dt><dd>Points per game differential (scored minus allowed)</dd>
                        <dt>RED ZONE %</dt><dd>Touchdown percentage when inside opponent's 20-yard line</dd>
                    </dl>
                </div>
            </div>
        </div>
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

    # Format ATS records - use ats_overall from CoversScraper
    away_ats_str = away_ats.get('ats_overall', 'N/A') if away_ats else 'N/A'
    home_ats_str = home_ats.get('ats_overall', 'N/A') if home_ats else 'N/A'
    away_ats_pct = away_ats.get('ats_overall_pct', 'N/A') if away_ats else 'N/A'
    home_ats_pct = home_ats.get('ats_overall_pct', 'N/A') if home_ats else 'N/A'
    # Strip % sign if already present (we add it in the template)
    if isinstance(away_ats_pct, str) and away_ats_pct.endswith('%'):
        away_ats_pct = away_ats_pct[:-1]
    if isinstance(home_ats_pct, str) and home_ats_pct.endswith('%'):
        home_ats_pct = home_ats_pct[:-1]

    # Format public betting - get from game-specific data
    away_public = public_betting.get('away_spread_pct', 'N/A') if public_betting else 'N/A'
    home_public = public_betting.get('home_spread_pct', 'N/A') if public_betting else 'N/A'
    away_public_ml = public_betting.get('away_ml_pct', 'N/A') if public_betting else 'N/A'
    home_public_ml = public_betting.get('home_ml_pct', 'N/A') if public_betting else 'N/A'

    # Format sharp money - use sharp_side from ActionNetworkScraper
    sharp_side = sharp_money.get('sharp_side', None) if sharp_money else None
    sharp_confidence = sharp_money.get('confidence', 'none') if sharp_money else 'none'
    rlm = sharp_money.get('rlm', False) if sharp_money else False
    steam_move = sharp_money.get('steam_move', False) if sharp_money else False

    # Format power ratings (key is 'power_rating' from TeamRankingsScraper)
    away_power_val = away_power.get('power_rating', 'N/A') if away_power else 'N/A'
    home_power_val = home_power.get('power_rating', 'N/A') if home_power else 'N/A'
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
    if not advanced:
        return '<div class="no-data">Advanced stats unavailable</div>'

    # Check if we have real data (not all N/A)
    has_data = any(v != 'N/A' and v is not None for k, v in advanced.items() if k not in ['calculated', 'estimated'])
    if not has_data:
        return '<div class="no-data">Advanced stats unavailable</div>'

    if sport in ['NBA', 'NCAAB']:
        # Format NET_RATING with +/- sign
        net_rtg = advanced.get('net_rating', 'N/A')
        if isinstance(net_rtg, (int, float)):
            net_rtg = f"+{net_rtg}" if net_rtg > 0 else str(net_rtg)

        # Get rankings if available
        off_rank = advanced.get('off_rating_rank', '')
        def_rank = advanced.get('def_rating_rank', '')
        net_rank = advanced.get('net_rating_rank', '')
        off_rank_html = f' <span class="rank">(#{off_rank})</span>' if off_rank else ''
        def_rank_html = f' <span class="rank">(#{def_rank})</span>' if def_rank else ''
        net_rank_html = f' <span class="rank">(#{net_rank})</span>' if net_rank else ''

        return f'''
            <div class="advanced-header">ADVANCED METRICS</div>
            <div class="advanced-stat highlight">
                <span class="stat-label">OFF RTG</span>
                <span class="stat-value">{advanced.get('offensive_rating', 'N/A')}{off_rank_html}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">DEF RTG</span>
                <span class="stat-value">{advanced.get('defensive_rating', 'N/A')}{def_rank_html}</span>
            </div>
            <div class="advanced-stat highlight">
                <span class="stat-label">NET RTG</span>
                <span class="stat-value">{net_rtg}{net_rank_html}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">PACE</span>
                <span class="stat-value">{advanced.get('pace', 'N/A')}</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">eFG%</span>
                <span class="stat-value">{advanced.get('efg_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">TS%</span>
                <span class="stat-value">{advanced.get('ts_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">AST%</span>
                <span class="stat-value">{advanced.get('ast_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">TOV%</span>
                <span class="stat-value">{advanced.get('tov_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">OREB%</span>
                <span class="stat-value">{advanced.get('oreb_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">DREB%</span>
                <span class="stat-value">{advanced.get('dreb_pct', 'N/A')}%</span>
            </div>
            <div class="advanced-stat">
                <span class="stat-label">PIE</span>
                <span class="stat-value">{advanced.get('pie', 'N/A')}</span>
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
        # ESPN uses avgPointsFor, not avgPoints
        ppg = stats.get('avgPointsFor', stats.get('avgPoints', 'N/A'))
        if isinstance(ppg, float):
            ppg = round(ppg, 1)
        opp_ppg = stats.get('avgPointsAgainst', 'N/A')
        if isinstance(opp_ppg, float):
            opp_ppg = round(opp_ppg, 1)
        diff = stats.get('differential', 'N/A')
        if isinstance(diff, float):
            diff = round(diff, 1)
            diff = f"+{diff}" if diff > 0 else str(diff)
        return f'''
            <div class="basic-stat"><span>PPG</span><span>{ppg}</span></div>
            <div class="basic-stat"><span>OPP PPG</span><span>{opp_ppg}</span></div>
            <div class="basic-stat"><span>DIFF</span><span>{diff}</span></div>
            <div class="basic-stat"><span>WINS</span><span>{stats.get('wins', 'N/A')}</span></div>
            <div class="basic-stat"><span>LOSSES</span><span>{stats.get('losses', 'N/A')}</span></div>
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
    """Generate the CSS styles - LARGE READABLE PROFESSIONAL"""
    return '''
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: #0d1117;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #e6edf3;
            font-size: 16px;
            line-height: 1.6;
        }

        /* SITE NAVIGATION */
        .site-nav {
            background: #161b22;
            border-bottom: 1px solid #30363d;
            padding: 12px 20px;
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        .nav-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-logo {
            font-family: 'Orbitron', sans-serif;
            font-weight: 800;
            font-size: 22px;
            color: #58a6ff;
            text-decoration: none;
        }
        .nav-links {
            display: flex;
            gap: 25px;
        }
        .nav-links a {
            color: #8b949e;
            text-decoration: none;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: color 0.2s;
        }
        .nav-links a:hover {
            color: #58a6ff;
        }

        /* HEADER */
        .header {
            background: #161b22;
            padding: 40px 30px;
            text-align: center;
            border-bottom: 2px solid #30363d;
        }

        .header-content { max-width: 1200px; margin: 0 auto; }

        .back-link {
            color: #58a6ff;
            text-decoration: none;
            font-size: 16px;
            display: inline-block;
            margin-bottom: 20px;
        }

        .header h1 {
            font-size: 42px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 10px;
        }

        .header h1 span { color: #58a6ff; }

        .subtitle { display: none; }

        .timestamp {
            color: #8b949e;
            font-size: 16px;
            margin: 15px 0;
        }

        /* STATS BAR */
        .stats-bar {
            display: flex;
            justify-content: center;
            gap: 60px;
            margin: 25px 0;
            padding: 25px;
            background: rgba(88, 166, 255, 0.1);
            border-radius: 12px;
        }

        .stat-item { text-align: center; }
        .stat-item .stat-num { font-size: 36px; font-weight: 700; color: #58a6ff; display: block; }
        .stat-item .stat-label { font-size: 14px; color: #8b949e; text-transform: uppercase; display: block; margin-top: 5px; }

        /* TABS */
        .tabs {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin: 25px 0;
        }

        .tab {
            background: transparent;
            border: 2px solid #30363d;
            padding: 14px 30px;
            border-radius: 10px;
            color: #e6edf3;
            cursor: pointer;
            font-weight: 600;
            font-size: 16px;
            transition: all 0.2s;
        }

        .tab:hover { border-color: #58a6ff; background: rgba(88, 166, 255, 0.1); }
        .tab.active { background: #58a6ff; border-color: #58a6ff; color: #fff; }

        .archive-link { margin-top: 20px; }
        .archive-link a { color: #58a6ff; text-decoration: none; font-size: 16px; }

        /* CONTAINER */
        .container { max-width: 1100px; margin: 0 auto; padding: 35px 25px; }

        .section { display: none; }
        .section.active { display: block; }

        .section-header { text-align: center; margin-bottom: 35px; }
        .section-header h2 { font-size: 30px; color: #fff; font-weight: 700; }
        .section-header .count { color: #8b949e; font-size: 18px; margin-top: 10px; display: block; }

        .no-games {
            text-align: center;
            padding: 80px;
            color: #8b949e;
            background: #161b22;
            border-radius: 16px;
            font-size: 20px;
        }

        /* GAME CARD */
        .game-card {
            background: #161b22;
            border: 2px solid #30363d;
            border-radius: 16px;
            margin-bottom: 30px;
            overflow: hidden;
        }

        /* MATCHUP HEADER */
        .matchup-header {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 30px;
            align-items: center;
            padding: 30px 35px;
            background: #21262d;
        }

        .team-box { display: flex; align-items: center; gap: 20px; }
        .team-box.home { flex-direction: row-reverse; text-align: right; }

        .team-logo { width: 70px; height: 70px; object-fit: contain; }

        .team-details h3 { font-size: 22px; color: #fff; font-weight: 700; margin-bottom: 6px; }
        .team-records { font-size: 16px; color: #8b949e; }
        .team-records .overall { color: #58a6ff; font-weight: 700; font-size: 20px; }

        .vs-badge {
            background: #30363d;
            padding: 14px 24px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 18px;
            color: #8b949e;
        }

        /* STATS GRID */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; }

        .stats-panel { padding: 25px 30px; border-top: 2px solid #30363d; }
        .stats-panel:first-child { border-right: 2px solid #30363d; }

        .panel-header {
            font-size: 16px;
            font-weight: 700;
            color: #58a6ff;
            margin-bottom: 18px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .basic-stat {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            font-size: 16px;
            border-bottom: 1px solid #21262d;
        }

        .basic-stat span:first-child { color: #8b949e; }
        .basic-stat span:last-child { font-weight: 700; color: #e6edf3; font-size: 17px; }

        /* Advanced stats */
        .advanced-toggle { display: none; }
        .advanced-panel { margin-top: 20px; padding-top: 20px; border-top: 2px dashed #30363d; }

        .advanced-header {
            font-size: 14px;
            font-weight: 700;
            color: #7ee787;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .advanced-stat {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            font-size: 15px;
            border-bottom: 1px solid #21262d;
        }

        .advanced-stat.highlight {
            background: rgba(126, 231, 135, 0.15);
            margin: 6px -15px;
            padding: 12px 15px;
            border-radius: 8px;
            border: none;
        }

        .stat-label { color: #8b949e; text-transform: uppercase; font-size: 13px; font-weight: 600; }
        .stat-value { font-weight: 700; color: #e6edf3; font-size: 16px; }
        .stat-value .rank { color: #58a6ff; font-size: 12px; font-weight: 600; margin-left: 6px; }

        /* SECTIONS */
        .injuries-section, .betting-section, .recent-games-section, .betting-intel-section {
            padding: 25px 30px;
            border-top: 2px solid #30363d;
        }

        .section-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 18px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .injuries-section .section-title { color: #f85149; }
        .betting-section .section-title { color: #d29922; }
        .recent-games-section .section-title { color: #a371f7; }
        .betting-intel-section .section-title { color: #58a6ff; }

        .injuries-grid, .recent-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 35px; }

        .injury-column h5, .recent-column h5 {
            font-size: 17px;
            color: #e6edf3;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #30363d;
        }

        .injury-list { list-style: none; }
        .injury-list li {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            font-size: 15px;
            border-bottom: 1px solid #21262d;
        }

        .player-name { color: #e6edf3; font-weight: 600; font-size: 15px; }
        .injury-type { font-size: 14px; color: #8b949e; }

        .status {
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            text-transform: uppercase;
        }

        .status.out { background: #f85149; color: #fff; }
        .status.doubtful { background: #db6d28; color: #fff; }
        .status.questionable { background: #d29922; color: #000; }
        .status.day-to-day { background: #58a6ff; color: #fff; }
        .status.probable { background: #3fb950; color: #fff; }

        .no-injuries { color: #3fb950; font-size: 15px; }

        /* Recent Games */
        .game-results { display: flex; gap: 8px; flex-wrap: wrap; }
        .game-result {
            width: 36px;
            height: 36px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            color: #fff;
        }

        .game-result.win { background: #3fb950; }
        .game-result.loss { background: #f85149; }

        /* Betting Section */
        .betting-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
        .line-box { text-align: center; }
        .line-type { font-size: 13px; color: #8b949e; text-transform: uppercase; margin-bottom: 10px; font-weight: 600; }
        .line-values { display: flex; flex-direction: column; gap: 8px; }
        .line-value {
            font-weight: 700;
            font-size: 18px;
            color: #e6edf3;
            background: #21262d;
            padding: 14px;
            border-radius: 8px;
        }

        .no-data { color: #8b949e; font-size: 15px; padding: 15px; text-align: center; }

        /* Betting Intelligence */
        .intel-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; }

        .intel-box {
            background: #21262d;
            border-radius: 10px;
            padding: 18px;
        }

        .intel-header {
            font-size: 12px;
            font-weight: 700;
            color: #58a6ff;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .intel-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 14px;
            border-bottom: 1px solid #30363d;
        }

        .intel-row .team-name { color: #8b949e; max-width: 80px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .intel-row .ats-record { font-weight: 700; color: #e6edf3; }
        .intel-row .ats-pct { color: #58a6ff; font-weight: 700; }
        .intel-row .public-pct { color: #e6edf3; }
        .intel-row .power-rating { font-weight: 700; color: #d29922; }
        .intel-row .power-rank { color: #8b949e; }

        .sharp-indicators { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
        .sharp-indicator { padding: 6px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; text-transform: uppercase; }
        .sharp-indicator.rlm { background: #a371f7; color: #fff; }
        .sharp-indicator.steam { background: #db6d28; color: #fff; }
        .sharp-side { font-size: 14px; color: #d29922; font-weight: 700; }

        /* Responsive */
        @media (max-width: 900px) {
            .header h1 { font-size: 32px; }
            .matchup-header { grid-template-columns: 1fr; text-align: center; gap: 15px; }
            .team-box, .team-box.home { flex-direction: column; text-align: center; }
            .vs-badge { margin: 0 auto; }
            .stats-grid { grid-template-columns: 1fr; }
            .stats-panel:first-child { border-right: none; }
            .injuries-grid, .recent-grid { grid-template-columns: 1fr; }
            .betting-grid { grid-template-columns: 1fr; }
            .intel-grid { grid-template-columns: 1fr 1fr; }
        }

        @media (max-width: 600px) {
            .intel-grid { grid-template-columns: 1fr; }
            .stats-bar { gap: 30px; flex-wrap: wrap; }
            .stat-item .stat-num { font-size: 28px; }
            .nav-links { display: none; }
            .glossary-grid { grid-template-columns: 1fr; }
        }

        /* GLOSSARY SECTION */
        .glossary-section {
            background: #161b22;
            padding: 60px 30px;
            border-top: 2px solid #30363d;
            margin-top: 40px;
        }
        .glossary-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .glossary-section h2 {
            font-family: 'Orbitron', sans-serif;
            font-size: 28px;
            color: #58a6ff;
            text-align: center;
            margin-bottom: 10px;
        }
        .glossary-intro {
            text-align: center;
            color: #8b949e;
            margin-bottom: 40px;
            font-size: 16px;
        }
        .glossary-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 30px;
        }
        .glossary-category {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 25px;
        }
        .glossary-category h3 {
            color: #7ee787;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #30363d;
        }
        .glossary-category dl {
            display: grid;
            gap: 12px;
        }
        .glossary-category dt {
            color: #58a6ff;
            font-weight: 700;
            font-size: 14px;
            display: inline;
        }
        .glossary-category dd {
            color: #8b949e;
            font-size: 14px;
            display: inline;
            margin-left: 0;
        }
        .glossary-category dt::after {
            content: ' - ';
            color: #30363d;
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
