#!/usr/bin/env python3
"""
Sharp vs Square Page Generator
Scrapes betting consensus data from SBR and generates HTML page
"""

import requests
import json
import re
import os
from datetime import datetime

# SBR URLs for each sport
SBR_URLS = {
    'NFL': 'https://www.sportsbookreview.com/betting-odds/nfl-football/consensus/',
    'NBA': 'https://www.sportsbookreview.com/betting-odds/nba-basketball/consensus/',
    'NHL': 'https://www.sportsbookreview.com/betting-odds/nhl-hockey/consensus/',
    'NCAAB': 'https://www.sportsbookreview.com/betting-odds/ncaa-basketball/consensus/'
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_sbr_consensus(sport, url):
    """Fetch consensus data from SBR for a specific sport"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        # Extract __NEXT_DATA__ JSON
        match = re.search(r'__NEXT_DATA__.*?type="application/json">([^<]+)', response.text)
        if not match:
            print(f"[{sport}] No __NEXT_DATA__ found")
            return []

        data = json.loads(match.group(1))
        games = data.get('props', {}).get('pageProps', {}).get('oddsTableModel', {}).get('gameRows', [])

        parsed_games = []
        for game in games:
            try:
                g = game.get('gameView', {})
                if not g:
                    continue

                away_team = g.get('awayTeam', {})
                home_team = g.get('homeTeam', {})
                consensus = g.get('consensus', {})

                # Get odds data
                odds_views = game.get('oddsViews', [])
                spread_data = {}
                total_data = {}
                ml_data = {}

                for odds in odds_views:
                    if odds and odds.get('currentLine'):
                        line = odds['currentLine']
                        open_line = odds.get('openingLine', {})

                        if 'spread' in str(line.get('homeSpread', '')).lower() or line.get('homeSpread') is not None:
                            spread_data = {
                                'home_spread': line.get('homeSpread'),
                                'away_spread': line.get('awaySpread'),
                                'home_spread_odds': line.get('homeSpreadOdds'),
                                'away_spread_odds': line.get('awaySpreadOdds'),
                                'open_home_spread': open_line.get('homeSpread') if open_line else None,
                                'open_away_spread': open_line.get('awaySpread') if open_line else None
                            }

                        if line.get('total') is not None:
                            total_data = {
                                'total': line.get('total'),
                                'over_odds': line.get('overOdds'),
                                'under_odds': line.get('underOdds'),
                                'open_total': open_line.get('total') if open_line else None
                            }

                        if line.get('homeMoneyLine') is not None:
                            ml_data = {
                                'home_ml': line.get('homeMoneyLine'),
                                'away_ml': line.get('awayMoneyLine'),
                                'open_home_ml': open_line.get('homeMoneyLine') if open_line else None,
                                'open_away_ml': open_line.get('awayMoneyLine') if open_line else None
                            }

                game_data = {
                    'sport': sport,
                    'away_team': away_team.get('name', 'Unknown'),
                    'away_abbr': away_team.get('abbreviation', ''),
                    'away_logo': away_team.get('logoUrl', ''),
                    'home_team': home_team.get('name', 'Unknown'),
                    'home_abbr': home_team.get('abbreviation', ''),
                    'home_logo': home_team.get('logoUrl', ''),
                    'game_time': g.get('startDate', ''),
                    'consensus': {
                        'away_spread_pct': consensus.get('awaySpreadPickPercent', 0),
                        'home_spread_pct': consensus.get('homeSpreadPickPercent', 0),
                        'over_pct': consensus.get('overPickPercent', 0),
                        'under_pct': consensus.get('underPickPercent', 0),
                        'away_ml_pct': consensus.get('awayMoneyLinePickPercent', 0),
                        'home_ml_pct': consensus.get('homeMoneyLinePickPercent', 0)
                    },
                    'spread': spread_data,
                    'total': total_data,
                    'moneyline': ml_data
                }

                parsed_games.append(game_data)

            except Exception as e:
                print(f"[{sport}] Error parsing game: {e}")
                continue

        print(f"[{sport}] Found {len(parsed_games)} games")
        return parsed_games

    except Exception as e:
        print(f"[{sport}] Error fetching data: {e}")
        return []


def identify_sharp_signals(game):
    """Identify sharp betting signals for a game"""
    signals = []
    consensus = game.get('consensus', {})
    spread = game.get('spread', {})
    total = game.get('total', {})

    # Check for Reverse Line Movement (RLM) on spread
    if spread.get('home_spread') is not None and spread.get('open_home_spread') is not None:
        home_spread = float(spread['home_spread']) if spread['home_spread'] else 0
        open_home_spread = float(spread['open_home_spread']) if spread['open_home_spread'] else 0
        home_spread_pct = consensus.get('home_spread_pct', 50)

        # RLM: Line moves against public (public on home but line gets worse for home)
        if home_spread_pct > 55 and home_spread > open_home_spread:
            signals.append({
                'type': 'RLM',
                'side': game['away_team'],
                'desc': f"Reverse line movement - {home_spread_pct:.0f}% on {game['home_team']} but line moved from {open_home_spread} to {home_spread}"
            })
        elif home_spread_pct < 45 and home_spread < open_home_spread:
            signals.append({
                'type': 'RLM',
                'side': game['home_team'],
                'desc': f"Reverse line movement - {100-home_spread_pct:.0f}% on {game['away_team']} but line moved from {open_home_spread} to {home_spread}"
            })

    # Check for total RLM
    if total.get('total') is not None and total.get('open_total') is not None:
        current_total = float(total['total']) if total['total'] else 0
        open_total = float(total['open_total']) if total['open_total'] else 0
        over_pct = consensus.get('over_pct', 50)

        if over_pct > 60 and current_total < open_total:
            signals.append({
                'type': 'RLM',
                'side': 'UNDER',
                'desc': f"Reverse line movement - {over_pct:.0f}% on OVER but total dropped from {open_total} to {current_total}"
            })
        elif over_pct < 40 and current_total > open_total:
            signals.append({
                'type': 'RLM',
                'side': 'OVER',
                'desc': f"Reverse line movement - {100-over_pct:.0f}% on UNDER but total rose from {open_total} to {current_total}"
            })

    # Heavy one-sided action (potential sharp or square trap)
    home_spread_pct = consensus.get('home_spread_pct', 50)
    if home_spread_pct >= 70:
        signals.append({
            'type': 'HEAVY',
            'side': game['home_team'],
            'desc': f"Heavy public action - {home_spread_pct:.0f}% on {game['home_team']}"
        })
    elif home_spread_pct <= 30:
        signals.append({
            'type': 'HEAVY',
            'side': game['away_team'],
            'desc': f"Heavy public action - {100-home_spread_pct:.0f}% on {game['away_team']}"
        })

    return signals


def generate_game_card_html(game):
    """Generate HTML for a single game card"""
    consensus = game.get('consensus', {})
    spread = game.get('spread', {})
    total = game.get('total', {})
    ml = game.get('moneyline', {})
    signals = identify_sharp_signals(game)

    away_spread_pct = consensus.get('away_spread_pct', 0)
    home_spread_pct = consensus.get('home_spread_pct', 0)
    over_pct = consensus.get('over_pct', 0)
    under_pct = consensus.get('under_pct', 0)
    away_ml_pct = consensus.get('away_ml_pct', 0)
    home_ml_pct = consensus.get('home_ml_pct', 0)

    # Determine sharp indicator
    sharp_indicator = ''
    if signals:
        for sig in signals:
            if sig['type'] == 'RLM':
                sharp_indicator = f'''
                <div class="sharp-alert">
                    <span class="sharp-icon">&#x1F4B0;</span>
                    <span>Sharp money appears to be on <strong>{sig['side']}</strong></span>
                </div>'''
                break

    # Format spread display
    home_spread_val = spread.get('home_spread')
    away_spread_val = spread.get('away_spread')

    def format_spread(val):
        if val is None or val == '-' or val == '':
            return '-'
        try:
            num = float(val)
            return f"+{num}" if num > 0 else str(num)
        except (ValueError, TypeError):
            return '-'

    home_spread_str = format_spread(home_spread_val)
    away_spread_str = format_spread(away_spread_val)

    # Format total display
    total_val = total.get('total', '-') or '-'

    # Format ML display
    home_ml = ml.get('home_ml')
    away_ml = ml.get('away_ml')

    def format_ml(val):
        if val is None or val == '-' or val == '':
            return '-'
        try:
            num = int(val)
            return f"+{num}" if num > 0 else str(num)
        except (ValueError, TypeError):
            return '-'

    home_ml_str = format_ml(home_ml)
    away_ml_str = format_ml(away_ml)

    # Line movement indicators
    spread_move = ''
    try:
        open_spread = spread.get('open_home_spread')
        curr_spread = spread.get('home_spread')
        if open_spread and curr_spread and open_spread != '-' and curr_spread != '-':
            diff = float(curr_spread) - float(open_spread)
            if abs(diff) >= 0.5:
                arrow = '&#x2191;' if diff > 0 else '&#x2193;'
                spread_move = f'<span class="line-move">({open_spread} {arrow})</span>'
    except (ValueError, TypeError):
        pass

    total_move = ''
    try:
        open_total = total.get('open_total')
        curr_total = total.get('total')
        if open_total and curr_total and open_total != '-' and curr_total != '-':
            diff = float(curr_total) - float(open_total)
            if abs(diff) >= 0.5:
                arrow = '&#x2191;' if diff > 0 else '&#x2193;'
                total_move = f'<span class="line-move">({open_total} {arrow})</span>'
    except (ValueError, TypeError):
        pass

    return f'''
    <div class="game-card">
        <div class="game-header">
            <span class="game-time">{game.get('game_time', 'TBD')}</span>
        </div>
        {sharp_indicator}
        <div class="teams-container">
            <div class="team-row">
                <div class="team-info">
                    <span class="team-name">{game['away_team']}</span>
                </div>
                <div class="consensus-bars">
                    <div class="bar-container">
                        <div class="bar-label">SPREAD {away_spread_str}</div>
                        <div class="bar-wrapper">
                            <div class="bar away-bar" style="width: {away_spread_pct}%;">
                                <span class="bar-pct">{away_spread_pct:.0f}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="bar-container">
                        <div class="bar-label">ML {away_ml_str}</div>
                        <div class="bar-wrapper">
                            <div class="bar away-bar" style="width: {away_ml_pct if away_ml_pct > 0 else 50}%;">
                                <span class="bar-pct">{away_ml_pct:.0f}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="team-row">
                <div class="team-info">
                    <span class="team-name">{game['home_team']}</span>
                </div>
                <div class="consensus-bars">
                    <div class="bar-container">
                        <div class="bar-label">SPREAD {home_spread_str} {spread_move}</div>
                        <div class="bar-wrapper">
                            <div class="bar home-bar" style="width: {home_spread_pct}%;">
                                <span class="bar-pct">{home_spread_pct:.0f}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="bar-container">
                        <div class="bar-label">ML {home_ml_str}</div>
                        <div class="bar-wrapper">
                            <div class="bar home-bar" style="width: {home_ml_pct if home_ml_pct > 0 else 50}%;">
                                <span class="bar-pct">{home_ml_pct:.0f}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="totals-row">
            <div class="total-info">
                <span class="total-label">TOTAL: {total_val} {total_move}</span>
            </div>
            <div class="total-bars">
                <div class="total-bar-item">
                    <span class="ou-label">OVER</span>
                    <div class="bar-wrapper small">
                        <div class="bar over-bar" style="width: {over_pct}%;">
                            <span class="bar-pct">{over_pct:.0f}%</span>
                        </div>
                    </div>
                </div>
                <div class="total-bar-item">
                    <span class="ou-label">UNDER</span>
                    <div class="bar-wrapper small">
                        <div class="bar under-bar" style="width: {under_pct}%;">
                            <span class="bar-pct">{under_pct:.0f}%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''


def generate_html(all_games):
    """Generate the complete Sharp vs Square HTML page"""
    now = datetime.now()

    # Group games by sport
    games_by_sport = {'NFL': [], 'NBA': [], 'NHL': [], 'NCAAB': []}
    for game in all_games:
        sport = game.get('sport', 'NFL')
        if sport in games_by_sport:
            games_by_sport[sport].append(game)

    # Generate game cards for each sport
    sport_sections = {}
    for sport, games in games_by_sport.items():
        cards_html = '\n'.join([generate_game_card_html(g) for g in games])
        sport_sections[sport] = cards_html if cards_html else '<p class="no-games">No games scheduled</p>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sharp vs Square - Betting Consensus Tracker | BetLegend</title>
    <meta name="description" content="Track sharp money vs public betting percentages. See where the smart money is going with live consensus data for NFL, NBA, NHL, and college basketball.">
    <link rel="canonical" href="https://betlegendpicks.com/sharp-vs-square.html">
    <link rel="icon" type="image/png" href="favicon.png">

    <!-- Open Graph -->
    <meta property="og:title" content="Sharp vs Square - Betting Consensus Tracker | BetLegend">
    <meta property="og:description" content="Track sharp money vs public betting percentages. See where the smart money is going.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://betlegendpicks.com/sharp-vs-square.html">

    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">

    <style>
        :root {{
            --bg-dark: #0a0a0f;
            --bg-card: #12121a;
            --bg-card-hover: #1a1a24;
            --accent-cyan: #00d4ff;
            --accent-gold: #ffd700;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --text-muted: #6a6a7a;
            --border-color: #2a2a3a;
            --away-color: #00d4ff;
            --home-color: #ff6b35;
            --over-color: #00ff88;
            --under-color: #ff4757;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.5;
        }}

        /* Header */
        header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #0a0a0f 100%);
            border-bottom: 1px solid var(--border-color);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .header-content {{
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .logo {{
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--accent-cyan);
            text-decoration: none;
            letter-spacing: -0.5px;
        }}

        .logo span {{
            color: var(--accent-gold);
        }}

        nav {{
            display: flex;
            gap: 1.5rem;
        }}

        nav a {{
            color: var(--text-secondary);
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
            transition: color 0.2s;
        }}

        nav a:hover, nav a.active {{
            color: var(--accent-cyan);
        }}

        /* Main Content */
        main {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}

        .page-header {{
            text-align: center;
            margin-bottom: 2rem;
        }}

        .page-header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }}

        .page-header p {{
            color: var(--text-secondary);
            font-size: 1.1rem;
        }}

        .last-updated {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-bottom: 2rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        /* Sport Tabs */
        .sport-tabs {{
            display: flex;
            justify-content: center;
            gap: 0.5rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }}

        .sport-tab {{
            padding: 0.75rem 1.5rem;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .sport-tab:hover {{
            background: var(--bg-card-hover);
            border-color: var(--accent-cyan);
        }}

        .sport-tab.active {{
            background: linear-gradient(135deg, var(--accent-cyan), #0099cc);
            border-color: var(--accent-cyan);
            color: var(--bg-dark);
        }}

        /* Games Container */
        .games-container {{
            display: none;
        }}

        .games-container.active {{
            display: block;
        }}

        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
        }}

        /* Game Card */
        .game-card {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.25rem;
            transition: all 0.2s;
        }}

        .game-card:hover {{
            border-color: var(--accent-cyan);
            transform: translateY(-2px);
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
        }}

        .game-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid var(--border-color);
        }}

        .game-time {{
            color: var(--text-muted);
            font-size: 0.85rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        .sharp-alert {{
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 215, 0, 0.05));
            border: 1px solid var(--accent-gold);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
        }}

        .sharp-icon {{
            font-size: 1.2rem;
        }}

        .sharp-alert strong {{
            color: var(--accent-gold);
        }}

        .teams-container {{
            margin-bottom: 1rem;
        }}

        .team-row {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 0;
        }}

        .team-row:first-child {{
            border-bottom: 1px dashed var(--border-color);
        }}

        .team-info {{
            min-width: 120px;
        }}

        .team-name {{
            font-weight: 600;
            font-size: 0.95rem;
        }}

        .consensus-bars {{
            flex: 1;
            display: flex;
            gap: 1rem;
        }}

        .bar-container {{
            flex: 1;
        }}

        .bar-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 0.25rem;
            font-family: 'JetBrains Mono', monospace;
        }}

        .bar-wrapper {{
            background: var(--bg-dark);
            border-radius: 4px;
            height: 24px;
            overflow: hidden;
        }}

        .bar-wrapper.small {{
            height: 20px;
        }}

        .bar {{
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 8px;
            border-radius: 4px;
            min-width: 40px;
            transition: width 0.3s ease;
        }}

        .bar-pct {{
            font-size: 0.75rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .away-bar {{
            background: linear-gradient(90deg, var(--away-color), #0099cc);
        }}

        .home-bar {{
            background: linear-gradient(90deg, var(--home-color), #cc4400);
        }}

        .over-bar {{
            background: linear-gradient(90deg, var(--over-color), #00cc66);
        }}

        .under-bar {{
            background: linear-gradient(90deg, var(--under-color), #cc3344);
        }}

        .line-move {{
            color: var(--accent-gold);
            font-size: 0.7rem;
            margin-left: 4px;
        }}

        .totals-row {{
            background: var(--bg-dark);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .total-info {{
            min-width: 100px;
        }}

        .total-label {{
            font-size: 0.85rem;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .total-bars {{
            flex: 1;
            display: flex;
            gap: 1rem;
        }}

        .total-bar-item {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .ou-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            min-width: 45px;
        }}

        .no-games {{
            text-align: center;
            color: var(--text-muted);
            padding: 3rem;
            font-size: 1.1rem;
        }}

        /* Legend */
        .legend {{
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            margin-top: 2rem;
        }}

        .legend h3 {{
            font-size: 1rem;
            color: var(--accent-cyan);
            margin-bottom: 1rem;
        }}

        .legend-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}

        .legend-item {{
            display: flex;
            align-items: flex-start;
            gap: 0.75rem;
        }}

        .legend-icon {{
            font-size: 1.2rem;
        }}

        .legend-text strong {{
            display: block;
            font-size: 0.9rem;
            margin-bottom: 0.25rem;
        }}

        .legend-text span {{
            font-size: 0.8rem;
            color: var(--text-muted);
        }}

        /* Footer */
        footer {{
            background: var(--bg-card);
            border-top: 1px solid var(--border-color);
            padding: 2rem;
            margin-top: 3rem;
            text-align: center;
        }}

        footer p {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        footer a {{
            color: var(--accent-cyan);
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .header-content {{
                flex-direction: column;
                gap: 1rem;
            }}

            nav {{
                flex-wrap: wrap;
                justify-content: center;
            }}

            .games-grid {{
                grid-template-columns: 1fr;
            }}

            .team-row {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .consensus-bars {{
                width: 100%;
            }}

            .totals-row {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .total-bars {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <a href="index.html" class="logo">Bet<span>Legend</span></a>
            <nav>
                <a href="index.html">Home</a>
                <a href="handicapping-hub.html">Handicapping Hub</a>
                <a href="sharp-vs-square.html" class="active">Sharp vs Square</a>
                <a href="moneyline-parlay-of-the-day.html">ML Parlay</a>
                <a href="featured-game-of-the-day-page49.html">Featured Game</a>
                <a href="nba.html">NBA</a>
                <a href="nfl.html">NFL</a>
                <a href="nhl.html">NHL</a>
                <a href="ncaab.html">NCAAB</a>
            </nav>
        </div>
    </header>

    <main>
        <div class="page-header">
            <h1>Sharp vs Square</h1>
            <p>Track where the smart money is going. Consensus betting percentages updated hourly.</p>
        </div>

        <div class="last-updated">
            Last Updated: {now.strftime('%B %d, %Y at %I:%M %p ET')}
        </div>

        <div class="sport-tabs">
            <button class="sport-tab active" data-sport="nfl">NFL</button>
            <button class="sport-tab" data-sport="nba">NBA</button>
            <button class="sport-tab" data-sport="nhl">NHL</button>
            <button class="sport-tab" data-sport="ncaab">NCAAB</button>
        </div>

        <div id="nfl-games" class="games-container active">
            <div class="games-grid">
                {sport_sections['NFL']}
            </div>
        </div>

        <div id="nba-games" class="games-container">
            <div class="games-grid">
                {sport_sections['NBA']}
            </div>
        </div>

        <div id="nhl-games" class="games-container">
            <div class="games-grid">
                {sport_sections['NHL']}
            </div>
        </div>

        <div id="ncaab-games" class="games-container">
            <div class="games-grid">
                {sport_sections['NCAAB']}
            </div>
        </div>

        <div class="legend">
            <h3>Understanding Sharp Signals</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <span class="legend-icon">&#x1F4B0;</span>
                    <div class="legend-text">
                        <strong>Reverse Line Movement (RLM)</strong>
                        <span>When the line moves against the side getting the majority of bets. This often indicates sharp money on the other side.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <span class="legend-icon">&#x26A1;</span>
                    <div class="legend-text">
                        <strong>Steam Move</strong>
                        <span>Rapid line movement across multiple sportsbooks simultaneously, typically caused by sharp bettors.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <span class="legend-icon">&#x1F4CA;</span>
                    <div class="legend-text">
                        <strong>Bet % vs Money %</strong>
                        <span>When a small percentage of tickets account for a large percentage of money, sharps are likely involved.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <span class="legend-icon">&#x1F465;</span>
                    <div class="legend-text">
                        <strong>Public Favorites</strong>
                        <span>Games with 70%+ public action on one side. Fading the public can be profitable long-term.</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; 2026 BetLegend. All rights reserved. | <a href="index.html">Home</a></p>
        <p style="margin-top: 0.5rem;">Data sourced from public betting consensus. For entertainment purposes only.</p>
    </footer>

    <script>
        // Sport tab switching
        document.querySelectorAll('.sport-tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                // Remove active from all tabs
                document.querySelectorAll('.sport-tab').forEach(t => t.classList.remove('active'));
                // Hide all containers
                document.querySelectorAll('.games-container').forEach(c => c.classList.remove('active'));

                // Activate clicked tab
                tab.classList.add('active');
                const sport = tab.dataset.sport;
                document.getElementById(sport + '-games').classList.add('active');
            }});
        }});
    </script>
</body>
</html>
'''

    return html


def main():
    print("=" * 60)
    print("Sharp vs Square Page Generator")
    print("=" * 60)
    print()

    # Fetch data for all sports
    all_games = []
    for sport, url in SBR_URLS.items():
        print(f"Fetching {sport} data...")
        games = fetch_sbr_consensus(sport, url)
        all_games.extend(games)

    print()
    print(f"Total games found: {len(all_games)}")

    # Generate HTML
    print("Generating HTML...")
    html = generate_html(all_games)

    # Write output file
    repo_path = r'C:\Users\Nima\nimadamus.github.io'
    output_path = os.path.join(repo_path, 'sharp-vs-square.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
