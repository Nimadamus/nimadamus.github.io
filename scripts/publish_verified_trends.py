#!/usr/bin/env python3
"""
DAILY VERIFIED TRENDS PUBLISHER
Generates standalone verified trends pages for all active sports.

Pulls today's games from ESPN, runs the combinatorial trend engine
(65K+ filter combinations per game) against the 130K+ game historical
database, and publishes only trends that meet strict verification thresholds.

VERIFICATION THRESHOLDS:
- MONSTER: 70%+ ATS hit rate, minimum 15 games (1-filter) to 6 games (4-filter)
- HOT: 62%+ ATS hit rate, same sample minimums
- FADE: opponent side 62%+ (bet AGAINST)
- O/U EXTREME: 65%+ over or under rate

All data is REAL from universal_games.pkl (130K+ games, 99.25% complete).
ATS integrity check runs automatically. Nothing is estimated or fabricated.

Usage:
    python publish_verified_trends.py              # All active sports
    python publish_verified_trends.py NBA           # Single sport
    python publish_verified_trends.py --no-publish  # Generate only, don't commit
"""

import os
import sys
import json
import requests
import re
from datetime import datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo('America/New_York')
except ImportError:
    EASTERN = timezone(timedelta(hours=-5))

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(REPO_DIR), 'handicapping_tool'))

from hub_trends_engine import get_trends_for_game, get_trends_css, _load_games

# =============================================================================
# CONFIGURATION
# =============================================================================

SPORTS_CONFIG = {
    'NBA': {
        'espn_path': 'basketball/nba',
        'logo_path': 'nba',
        'spread_label': 'SPREAD',
        'active_months': list(range(1, 7)) + [10, 11, 12],  # Oct-Jun
    },
    'NHL': {
        'espn_path': 'hockey/nhl',
        'logo_path': 'nhl',
        'spread_label': 'PUCK LINE',
        'active_months': list(range(1, 7)) + [10, 11, 12],  # Oct-Jun
    },
    'MLB': {
        'espn_path': 'baseball/mlb',
        'logo_path': 'mlb',
        'spread_label': 'RUN LINE',
        'active_months': list(range(3, 11)),  # Mar-Oct
    },
    'NFL': {
        'espn_path': 'football/nfl',
        'logo_path': 'nfl',
        'spread_label': 'SPREAD',
        'active_months': list(range(1, 3)) + list(range(9, 13)),  # Sep-Feb
    },
}

# Minimum trends required to include a game (skip if no significant trends)
MIN_TRENDS_PER_GAME = 1
# Minimum MONSTER+HOT trends to feature a game prominently
FEATURED_THRESHOLD = 3

MONSTER_PCT = 70.0
HOT_PCT = 62.0
FADE_PCT = 62.0


def fetch_espn_games(sport_path):
    """Fetch today's games from ESPN scoreboard API."""
    now = datetime.now(EASTERN)
    date_str = now.strftime('%Y%m%d')
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date_str}&limit=200"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('events', [])
    except Exception as e:
        print(f"  [ERROR] Failed to fetch ESPN games: {e}")
    return []


def fetch_espn_odds(sport_path):
    """Fetch odds from ESPN header API (DraftKings data)."""
    odds_keys = {
        'basketball/nba': 'basketball_nba',
        'hockey/nhl': 'icehockey_nhl',
        'baseball/mlb': 'baseball_mlb',
        'football/nfl': 'americanfootball_nfl',
    }
    key = odds_keys.get(sport_path)
    if not key:
        return {}

    urls = {
        'basketball_nba': 'https://site.api.espn.com/apis/v2/scoreboard/header?sport=basketball&league=nba',
        'icehockey_nhl': 'https://site.api.espn.com/apis/v2/scoreboard/header?sport=hockey&league=nhl',
        'baseball_mlb': 'https://site.api.espn.com/apis/v2/scoreboard/header?sport=baseball&league=mlb',
        'americanfootball_nfl': 'https://site.api.espn.com/apis/v2/scoreboard/header?sport=football&league=nfl',
    }

    url = urls.get(key)
    if not url:
        return {}

    odds_map = {}
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            for sport_data in data.get('sports', []):
                for league in sport_data.get('leagues', []):
                    for event in league.get('events', []):
                        event_id = str(event.get('id', ''))
                        odds_info = {}
                        for comp in event.get('competitors', []):
                            ha = comp.get('homeAway', '')
                            abbr = comp.get('abbreviation', '')
                            if ha == 'home':
                                odds_info['home_abbr'] = abbr
                            else:
                                odds_info['away_abbr'] = abbr

                        # Extract odds
                        full_status = event.get('fullStatus', {})
                        odds_type = full_status.get('type', {})

                        # Try odds from event directly
                        event_odds = event.get('odds', {})
                        if event_odds:
                            odds_info['spread'] = event_odds.get('spread', 0)
                            odds_info['total'] = event_odds.get('overUnder', 0)
                            odds_info['ml_home'] = event_odds.get('homeMoneyLine', '-')
                            odds_info['ml_away'] = event_odds.get('awayMoneyLine', '-')

                        if odds_info.get('home_abbr'):
                            odds_map[event_id] = odds_info
    except Exception as e:
        print(f"  [ODDS ERROR] {e}")

    return odds_map


def parse_game_data(event, sport, odds_map):
    """Parse ESPN event into game data dict for trend analysis."""
    comp = event.get('competitions', [{}])[0]
    competitors = comp.get('competitors', [])

    away_data = home_data = None
    for team in competitors:
        if team.get('homeAway') == 'away':
            away_data = team
        else:
            home_data = team

    if not away_data or not home_data:
        return None

    away_info = away_data.get('team', {})
    home_info = home_data.get('team', {})
    away_abbr = away_info.get('abbreviation', '?')
    home_abbr = home_info.get('abbreviation', '?')
    away_name = away_info.get('displayName', away_abbr)
    home_name = home_info.get('displayName', home_abbr)
    away_record = away_data.get('records', [{}])[0].get('summary', '0-0') if away_data.get('records') else '0-0'
    home_record = home_data.get('records', [{}])[0].get('summary', '0-0') if home_data.get('records') else '0-0'

    # Parse game time
    game_date_str = event.get('date', '')
    try:
        game_dt = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
        game_time = game_dt.astimezone(EASTERN).strftime('%I:%M %p ET')
    except:
        game_time = 'TBD'

    venue = comp.get('venue', {}).get('fullName', 'TBD')
    broadcasts = comp.get('broadcasts', [])
    network = broadcasts[0].get('names', [''])[0] if broadcasts else ''

    # Get odds
    event_id = str(event.get('id', ''))
    odds = odds_map.get(event_id, {})
    spread = 0
    total = 0
    ml_home = '-'
    ml_away = '-'

    if odds:
        try:
            spread = float(odds.get('spread', 0) or 0)
        except (ValueError, TypeError):
            spread = 0
        try:
            total = float(odds.get('total', 0) or 0)
        except (ValueError, TypeError):
            total = 0
        ml_home = odds.get('ml_home', '-')
        ml_away = odds.get('ml_away', '-')

    # Parse records for win pct
    def parse_wpct(rec):
        try:
            parts = str(rec).replace(' ', '').split('-')
            w = int(parts[0])
            l = int(parts[1])
            gp = w + l + (int(parts[2]) if len(parts) > 2 else 0)
            return w / gp if gp > 0 else 0.5
        except:
            return 0.5

    return {
        'away_abbr': away_abbr,
        'home_abbr': home_abbr,
        'away_name': away_name,
        'home_name': home_name,
        'away_record': away_record,
        'home_record': home_record,
        'game_time': game_time,
        'venue': venue,
        'network': network,
        'spread': spread,
        'total': total,
        'ml_home': ml_home,
        'ml_away': ml_away,
        'home_wpct': parse_wpct(home_record),
        'away_wpct': parse_wpct(away_record),
        'event_id': event_id,
    }


def run_trends_for_game(game, sport):
    """Run the combinatorial trend engine for a single game."""
    results = get_trends_for_game(
        sport=sport,
        home_abbr=game['home_abbr'],
        away_abbr=game['away_abbr'],
        home_spread=game['spread'],
        total=game['total'],
        home_wpct=game['home_wpct'],
        away_wpct=game['away_wpct'],
    )
    return results


def classify_trends(results):
    """Classify trends into tiers."""
    from hub_trends_engine import MIN_SAMPLE
    monsters = [r for r in results if r["rec"]["pct"] >= MONSTER_PCT and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    hot = [r for r in results if HOT_PCT <= r["rec"]["pct"] < MONSTER_PCT and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    fades = [r for r in results if r["rec"]["pct"] <= (100 - FADE_PCT) and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    ou_extremes = [r for r in results if r.get("ou_edge", 0) >= 15 and r["rec"]["games"] >= MIN_SAMPLE.get(r["depth"], 6)]
    ou_extremes.sort(key=lambda x: x["ou_edge"], reverse=True)
    return monsters, hot, fades, ou_extremes


def generate_game_trends_html(game, trends, sport_config):
    """Generate HTML block for a single game's trends."""
    monsters, hot, fades, ou_extremes = classify_trends(trends)

    if len(monsters) + len(hot) + len(fades) < MIN_TRENDS_PER_GAME:
        return '', 0

    is_featured = len(monsters) + len(hot) >= FEATURED_THRESHOLD
    card_class = 'game-trends-card featured' if is_featured else 'game-trends-card'

    away_logo = f"https://a.espncdn.com/i/teamlogos/{sport_config['logo_path']}/500/scoreboard/{game['away_abbr'].lower()}.png"
    home_logo = f"https://a.espncdn.com/i/teamlogos/{sport_config['logo_path']}/500/scoreboard/{game['home_abbr'].lower()}.png"

    # Verdict
    home_covers = len([r for r in trends if r["side"] == "home" and r["rec"]["pct"] >= 56])
    home_fades_count = len([r for r in trends if r["side"] == "home" and r["rec"]["pct"] <= 44])
    away_covers = len([r for r in trends if r["side"] == "away" and r["rec"]["pct"] >= 56])
    away_fades_count = len([r for r in trends if r["side"] == "away" and r["rec"]["pct"] <= 44])

    home_score = home_covers + away_fades_count
    away_score = away_covers + home_fades_count

    if home_score > away_score + 3:
        verdict = f"STRONG LEAN: {game['home_abbr']}"
        verdict_class = 'verdict-strong'
    elif away_score > home_score + 3:
        verdict = f"STRONG LEAN: {game['away_abbr']}"
        verdict_class = 'verdict-strong'
    elif home_score > away_score:
        verdict = f"LEAN: {game['home_abbr']}"
        verdict_class = 'verdict-lean'
    elif away_score > home_score:
        verdict = f"LEAN: {game['away_abbr']}"
        verdict_class = 'verdict-lean'
    else:
        verdict = 'NO CLEAR EDGE'
        verdict_class = 'verdict-neutral'

    # Build trend rows
    rows = []
    count = 0
    max_display = 15 if is_featured else 8

    def add_row(r, tier_class, tier_label):
        nonlocal count
        if count >= max_display:
            return
        rec = r["rec"]
        pct = rec["pct"]
        rows.append(f'''<tr class="{tier_class}">
            <td class="trend-tier">{tier_label}</td>
            <td class="trend-desc">{r["desc"]}</td>
            <td class="trend-record">{rec["w"]}-{rec["l"]}</td>
            <td class="trend-pct">{pct:.1f}%</td>
            <td class="trend-games">{rec["games"]}</td>
        </tr>''')
        count += 1

    for r in monsters[:8]:
        add_row(r, 'tier-monster', 'MONSTER')
    for r in hot[:6]:
        add_row(r, 'tier-hot', 'HOT')
    for r in fades[:4]:
        add_row(r, 'tier-fade', 'FADE')

    # O/U rows
    ou_rows = []
    for r in ou_extremes[:3]:
        rec = r["rec"]
        lean = "OVER" if rec["ou_pct"] > 55 else "UNDER"
        ou_class = "ou-over" if lean == "OVER" else "ou-under"
        ou_rows.append(f'''<tr>
            <td class="trend-desc">{r["desc"]}</td>
            <td class="{ou_class}">{rec["over"]}O-{rec["under"]}U ({rec["ou_pct"]:.1f}%)</td>
            <td class="trend-games">{rec["games"]}</td>
            <td class="{ou_class}"><strong>{lean}</strong></td>
        </tr>''')

    ou_html = ''
    if ou_rows:
        ou_html = f'''
        <div class="ou-trends">
            <h4 class="ou-title">O/U TRENDS</h4>
            <table class="trends-table ou-table">
                <thead><tr><th>SITUATION</th><th>RECORD</th><th>GAMES</th><th>LEAN</th></tr></thead>
                <tbody>{"".join(ou_rows)}</tbody>
            </table>
        </div>'''

    # Spread display
    if game['spread'] != 0:
        spread_display = f"{game['home_abbr']} {game['spread']:+.1f}"
    else:
        spread_display = 'PK'
    total_display = f"O/U {game['total']}" if game['total'] else 'N/A'

    trend_count = len(monsters) + len(hot) + len(fades)

    html = f'''
    <div class="{card_class}">
        <div class="game-header-trends">
            <div class="matchup-line">
                <img src="{away_logo}" class="trend-logo" onerror="this.style.display='none'">
                <span class="team-abbr">{game['away_abbr']}</span>
                <span class="team-record">({game['away_record']})</span>
                <span class="at-symbol">@</span>
                <img src="{home_logo}" class="trend-logo" onerror="this.style.display='none'">
                <span class="team-abbr">{game['home_abbr']}</span>
                <span class="team-record">({game['home_record']})</span>
            </div>
            <div class="game-meta">
                <span class="game-time">{game['game_time']}</span>
                <span class="game-spread">{spread_display}</span>
                <span class="game-total">{total_display}</span>
            </div>
        </div>
        <div class="verdict-bar {verdict_class}">
            <span class="verdict-text">{verdict}</span>
            <span class="trend-count">{trend_count} verified trends | {len(trends)} total analyzed</span>
        </div>
        <table class="trends-table">
            <thead><tr><th>TIER</th><th>SITUATION</th><th>ATS</th><th>HIT%</th><th>GAMES</th></tr></thead>
            <tbody>{"".join(rows)}</tbody>
        </table>
        {ou_html}
    </div>'''

    return html, trend_count


def generate_full_page(all_sport_data, date_str):
    """Generate the complete standalone HTML page."""
    now = datetime.now(EASTERN)
    display_date = now.strftime('%B %d, %Y')
    day_of_week = now.strftime('%A')

    # Count totals
    total_games = sum(len(games) for games in all_sport_data.values())
    total_trends = sum(
        sum(g.get('trend_count', 0) for g in games)
        for games in all_sport_data.values()
    )

    # Build sport sections
    sport_sections = ''
    toc_items = ''
    strong_leans = []

    for sport, games in all_sport_data.items():
        if not games:
            continue

        config = SPORTS_CONFIG[sport]
        game_cards = ''
        for g in games:
            if g.get('html'):
                game_cards += g['html']

        # Collect strong leans for summary
        for g in games:
            if 'STRONG LEAN' in g.get('verdict', ''):
                strong_leans.append(f"{sport}: {g['away_abbr']} @ {g['home_abbr']} - {g['verdict']}")

        sport_sections += f'''
        <section class="sport-section" id="{sport.lower()}-trends">
            <h2 class="sport-header">{sport} <span class="game-count">{len(games)} games</span></h2>
            {game_cards}
        </section>'''

        toc_items += f'<a href="#{sport.lower()}-trends" class="toc-link">{sport} ({len(games)})</a>\n'

    # Strong leans summary
    strong_leans_html = ''
    if strong_leans:
        items = ''.join(f'<li>{sl}</li>' for sl in strong_leans)
        strong_leans_html = f'''
        <div class="strong-leans-summary">
            <h3>STRONG LEANS</h3>
            <ul>{items}</ul>
        </div>'''

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verified Trends - {display_date} | BetLegend</title>
    <meta name="description" content="BetLegend verified betting trends for {display_date}. {total_trends} trends across {total_games} games analyzed from 130,000+ game historical database.">
    <meta property="og:title" content="Verified Trends - {display_date} | BetLegend">
    <meta property="og:description" content="{total_trends} verified betting trends across {total_games} games.">
    <meta property="og:type" content="article">
    <meta name="twitter:card" content="summary_large_image">
    <link rel="canonical" href="https://www.betlegendpicks.com/verified-trends.html">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: #0a0e1a;
            color: #e0e0e0;
            min-height: 100vh;
        }}
        .page-header {{
            background: linear-gradient(135deg, #0d1526 0%, #1a2744 50%, #0d1526 100%);
            border-bottom: 3px solid rgba(0, 245, 255, 0.3);
            padding: 40px 24px;
            text-align: center;
        }}
        .page-header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2.2rem;
            color: #00f5ff;
            text-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
            margin-bottom: 8px;
        }}
        .page-header .subtitle {{
            font-size: 1.1rem;
            color: #8594b0;
            margin-bottom: 16px;
        }}
        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.8rem;
            color: #00f5ff;
            font-weight: 700;
        }}
        .stat-label {{
            font-size: 0.75rem;
            color: #8594b0;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-top: 4px;
        }}
        .toc {{
            display: flex;
            justify-content: center;
            gap: 16px;
            padding: 16px;
            background: rgba(0, 20, 40, 0.5);
            border-bottom: 1px solid rgba(0, 245, 255, 0.1);
            flex-wrap: wrap;
        }}
        .toc-link {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            color: #00f5ff;
            text-decoration: none;
            padding: 8px 20px;
            border: 1px solid rgba(0, 245, 255, 0.3);
            border-radius: 20px;
            transition: all 0.3s;
        }}
        .toc-link:hover {{
            background: rgba(0, 245, 255, 0.15);
            border-color: #00f5ff;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 24px;
        }}
        .strong-leans-summary {{
            background: rgba(255, 50, 50, 0.1);
            border: 1px solid rgba(255, 50, 50, 0.3);
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 30px;
        }}
        .strong-leans-summary h3 {{
            font-family: 'Orbitron', sans-serif;
            color: #ff3333;
            font-size: 1rem;
            letter-spacing: 2px;
            margin-bottom: 12px;
        }}
        .strong-leans-summary li {{
            color: #e0e0e0;
            padding: 4px 0;
            font-size: 0.95rem;
        }}
        .sport-section {{
            margin-bottom: 40px;
        }}
        .sport-header {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.4rem;
            color: #00f5ff;
            border-bottom: 2px solid rgba(0, 245, 255, 0.3);
            padding-bottom: 12px;
            margin-bottom: 20px;
            letter-spacing: 2px;
        }}
        .game-count {{
            font-size: 0.8rem;
            color: #8594b0;
            font-weight: 400;
        }}
        .game-trends-card {{
            background: rgba(15, 25, 45, 0.8);
            border: 1px solid rgba(0, 245, 255, 0.15);
            border-radius: 12px;
            margin-bottom: 24px;
            overflow: hidden;
        }}
        .game-trends-card.featured {{
            border-color: rgba(255, 50, 50, 0.4);
            box-shadow: 0 0 20px rgba(255, 50, 50, 0.1);
        }}
        .game-header-trends {{
            padding: 16px 20px;
            background: rgba(0, 20, 40, 0.5);
            border-bottom: 1px solid rgba(0, 245, 255, 0.1);
        }}
        .matchup-line {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .trend-logo {{
            width: 28px;
            height: 28px;
            object-fit: contain;
        }}
        .team-abbr {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #fff;
        }}
        .team-record {{
            color: #8594b0;
            font-size: 0.85rem;
        }}
        .at-symbol {{
            color: #555;
            margin: 0 4px;
        }}
        .game-meta {{
            display: flex;
            gap: 20px;
            margin-top: 8px;
            font-size: 0.85rem;
            color: #8594b0;
        }}
        .verdict-bar {{
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .verdict-strong {{
            background: rgba(255, 50, 50, 0.15);
            border-bottom: 2px solid rgba(255, 50, 50, 0.4);
        }}
        .verdict-strong .verdict-text {{
            font-family: 'Orbitron', sans-serif;
            color: #ff3333;
            font-weight: 700;
            font-size: 1rem;
            letter-spacing: 1px;
        }}
        .verdict-lean {{
            background: rgba(0, 245, 255, 0.08);
            border-bottom: 2px solid rgba(0, 245, 255, 0.2);
        }}
        .verdict-lean .verdict-text {{
            font-family: 'Orbitron', sans-serif;
            color: #00f5ff;
            font-weight: 600;
            font-size: 0.95rem;
        }}
        .verdict-neutral {{
            background: rgba(100, 100, 100, 0.1);
            border-bottom: 2px solid rgba(100, 100, 100, 0.2);
        }}
        .verdict-neutral .verdict-text {{
            color: #888;
            font-size: 0.9rem;
        }}
        .trend-count {{
            font-size: 0.8rem;
            color: #8594b0;
        }}
        .trends-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}
        .trends-table thead th {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: #888;
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .trends-table tbody tr {{
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .trends-table tbody tr:hover {{
            background: rgba(0, 245, 255, 0.04);
        }}
        .trends-table td {{
            padding: 10px 12px;
        }}
        .trend-tier {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 1px;
            width: 90px;
        }}
        .tier-monster .trend-tier {{ color: #ff3333; text-shadow: 0 0 10px rgba(255,50,50,0.5); }}
        .tier-hot .trend-tier {{ color: #ffa500; text-shadow: 0 0 8px rgba(255,165,0,0.4); }}
        .tier-fade .trend-tier {{ color: #ff69b4; }}
        .trend-desc {{ color: #ccc; line-height: 1.4; }}
        .trend-record {{ font-weight: 600; color: #00f5ff; white-space: nowrap; }}
        .trend-pct {{ font-weight: 700; color: #4ade80; }}
        .tier-fade .trend-pct {{ color: #ff69b4; }}
        .trend-games {{ color: #888; font-size: 0.85rem; }}
        .ou-trends {{ padding: 16px 12px; border-top: 1px solid rgba(0, 245, 255, 0.1); }}
        .ou-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            color: #00f5ff;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }}
        .ou-over {{ color: #4ade80; font-weight: 600; }}
        .ou-under {{ color: #60a5fa; font-weight: 600; }}
        .disclaimer {{
            text-align: center;
            padding: 30px;
            color: #555;
            font-size: 0.8rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            margin-top: 40px;
        }}
        .data-source {{
            background: rgba(0, 245, 255, 0.05);
            border: 1px solid rgba(0, 245, 255, 0.1);
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
            font-size: 0.85rem;
            color: #8594b0;
            text-align: center;
        }}
        .data-source strong {{ color: #00f5ff; }}
        @media (max-width: 768px) {{
            .page-header h1 {{ font-size: 1.4rem; }}
            .stats-bar {{ gap: 20px; }}
            .stat-value {{ font-size: 1.3rem; }}
            .game-meta {{ flex-direction: column; gap: 4px; }}
            .matchup-line {{ font-size: 0.9rem; }}
            .trends-table {{ font-size: 0.8rem; }}
            .trend-desc {{ max-width: 200px; }}
        }}
    </style>
</head>
<body>
    <header class="page-header">
        <h1>VERIFIED TRENDS</h1>
        <div class="subtitle">{day_of_week}, {display_date}</div>
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-value">{total_games}</div>
                <div class="stat-label">Games Scanned</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_trends}</div>
                <div class="stat-label">Verified Trends</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(strong_leans)}</div>
                <div class="stat-label">Strong Leans</div>
            </div>
        </div>
    </header>

    <nav class="toc">
        {toc_items}
    </nav>

    <div class="container">
        <div class="data-source">
            All trends verified against <strong>130,000+ game historical database</strong>.
            Minimum sample sizes enforced. ATS integrity checked.
            Last updated: {now.strftime('%I:%M %p ET')}.
        </div>

        {strong_leans_html}
        {sport_sections}

        <div class="disclaimer">
            Trends are based on historical data and do not guarantee future results.
            All data sourced from verified game records. No estimates or fabrications.
            &copy; {now.year} BetLegend
        </div>
    </div>
</body>
</html>'''

    return page


def main():
    now = datetime.now(EASTERN)
    date_str = now.strftime('%Y-%m-%d')
    month = now.month

    print("=" * 60)
    print("VERIFIED TRENDS PUBLISHER")
    print(f"Date: {now.strftime('%B %d, %Y')}")
    print("=" * 60)

    # Parse args
    target_sport = None
    no_publish = False
    for arg in sys.argv[1:]:
        if arg == '--no-publish':
            no_publish = True
        elif arg.upper() in SPORTS_CONFIG:
            target_sport = arg.upper()

    all_sport_data = {}

    for sport, config in SPORTS_CONFIG.items():
        if target_sport and sport != target_sport:
            continue

        # Check if sport is in season
        if month not in config['active_months']:
            print(f"\n[{sport}] Off-season - skipping")
            continue

        print(f"\n[{sport}] Fetching games...")
        events = fetch_espn_games(config['espn_path'])
        print(f"  Found {len(events)} games")

        if not events:
            continue

        print(f"[{sport}] Fetching odds...")
        odds_map = fetch_espn_odds(config['espn_path'])

        games_data = []
        for event in events:
            game = parse_game_data(event, sport, odds_map)
            if not game:
                continue

            print(f"  Scanning {game['away_abbr']} @ {game['home_abbr']}...")
            trends = run_trends_for_game(game, sport)

            if trends:
                html, trend_count = generate_game_trends_html(game, trends, config)
                monsters, hot, fades, ou = classify_trends(trends)

                # Determine verdict string
                home_covers = len([r for r in trends if r["side"] == "home" and r["rec"]["pct"] >= 56])
                away_covers = len([r for r in trends if r["side"] == "away" and r["rec"]["pct"] >= 56])
                home_fades_count = len([r for r in trends if r["side"] == "home" and r["rec"]["pct"] <= 44])
                away_fades_count = len([r for r in trends if r["side"] == "away" and r["rec"]["pct"] <= 44])
                home_score = home_covers + away_fades_count
                away_score = away_covers + home_fades_count

                if home_score > away_score + 3:
                    verdict_str = f"STRONG LEAN: {game['home_abbr']}"
                elif away_score > home_score + 3:
                    verdict_str = f"STRONG LEAN: {game['away_abbr']}"
                elif home_score > away_score:
                    verdict_str = f"LEAN: {game['home_abbr']}"
                elif away_score > home_score:
                    verdict_str = f"LEAN: {game['away_abbr']}"
                else:
                    verdict_str = "NO CLEAR EDGE"

                game['html'] = html
                game['trend_count'] = trend_count
                game['verdict'] = verdict_str
                game['monsters'] = len(monsters)
                game['hot'] = len(hot)
                game['fades'] = len(fades)

                print(f"    {len(monsters)} MONSTER | {len(hot)} HOT | {len(fades)} FADE | {verdict_str}")
                games_data.append(game)
            else:
                print(f"    No significant trends found")

        all_sport_data[sport] = games_data
        print(f"  [{sport}] {len(games_data)} games with verified trends")

    # Generate the page
    print(f"\n[HTML] Generating verified trends page...")
    html = generate_full_page(all_sport_data, date_str)

    # Save to repo
    output_path = os.path.join(REPO_DIR, 'verified-trends.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[SUCCESS] Saved to: {output_path}")

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"VERIFIED TRENDS COMPLETE - {now.strftime('%B %d, %Y')}")
    print(f"{'=' * 60}")
    total_games = sum(len(g) for g in all_sport_data.values())
    total_trends = sum(sum(g.get('trend_count', 0) for g in games) for games in all_sport_data.values())
    print(f"Games scanned: {total_games}")
    print(f"Verified trends: {total_trends}")
    for sport, games in all_sport_data.items():
        if games:
            strong = sum(1 for g in games if 'STRONG LEAN' in g.get('verdict', ''))
            leans = sum(1 for g in games if g.get('verdict', '').startswith('LEAN'))
            print(f"  {sport}: {len(games)} games | {strong} strong leans | {leans} leans")
    print(f"{'=' * 60}")

    if not no_publish:
        print(f"\nPage ready at: {output_path}")
        print("Run 'python publish.py verified-trends.html betlegend' to publish")


if __name__ == '__main__':
    main()
