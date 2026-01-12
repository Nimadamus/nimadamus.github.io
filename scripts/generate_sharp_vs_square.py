#!/usr/bin/env python3
"""
Sharp vs Square Page Generator - Clean Table Format
Scrapes betting consensus data from SBR and generates readable HTML page
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

                # Get odds from first bookmaker
                odds_views = game.get('oddsViews', [])
                spread_home = None
                spread_away = None
                total = None
                ml_home = None
                ml_away = None

                for odds in odds_views:
                    if odds and odds.get('currentLine'):
                        line = odds['currentLine']
                        if spread_home is None and line.get('homeSpread') is not None:
                            spread_home = line.get('homeSpread')
                            spread_away = line.get('awaySpread')
                        if total is None and line.get('total') is not None:
                            total = line.get('total')
                        if ml_home is None and line.get('homeMoneyLine') is not None:
                            ml_home = line.get('homeMoneyLine')
                            ml_away = line.get('awayMoneyLine')
                        break

                game_data = {
                    'sport': sport,
                    'away_team': away_team.get('name', 'Unknown'),
                    'away_abbr': away_team.get('abbreviation', ''),
                    'home_team': home_team.get('name', 'Unknown'),
                    'home_abbr': home_team.get('abbreviation', ''),
                    'game_time': g.get('startDate', ''),
                    'spread_home': spread_home,
                    'spread_away': spread_away,
                    'total': total,
                    'ml_home': ml_home,
                    'ml_away': ml_away,
                    'away_spread_pct': consensus.get('awaySpreadPickPercent', 0),
                    'home_spread_pct': consensus.get('homeSpreadPickPercent', 0),
                    'over_pct': consensus.get('overPickPercent', 0),
                    'under_pct': consensus.get('underPickPercent', 0),
                    'away_ml_pct': consensus.get('awayMoneyLinePickPercent', 0),
                    'home_ml_pct': consensus.get('homeMoneyLinePickPercent', 0)
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


def format_spread(val):
    """Format spread value"""
    if val is None:
        return '-'
    try:
        num = float(val)
        return f"+{num}" if num > 0 else str(num)
    except:
        return '-'


def format_ml(val):
    """Format moneyline value"""
    if val is None:
        return '-'
    try:
        num = int(val)
        return f"+{num}" if num > 0 else str(num)
    except:
        return '-'


def get_sharp_signal(game):
    """Determine if there's a sharp signal and which side"""
    away_pct = game.get('away_spread_pct', 50)
    home_pct = game.get('home_spread_pct', 50)

    # Heavy one-sided action (potential sharp fade)
    if away_pct >= 65:
        return ('away_heavy', game['away_team'], away_pct)
    elif home_pct >= 65:
        return ('home_heavy', game['home_team'], home_pct)

    return None


def generate_game_table_html(games, sport):
    """Generate a clean table for games"""
    if not games:
        return '<p class="no-games">No games scheduled for today.</p>'

    rows = []
    for game in games:
        away_spread_pct = game.get('away_spread_pct', 0)
        home_spread_pct = game.get('home_spread_pct', 0)
        over_pct = game.get('over_pct', 0)
        under_pct = game.get('under_pct', 0)
        away_ml_pct = game.get('away_ml_pct', 0)
        home_ml_pct = game.get('home_ml_pct', 0)

        # Determine which side has more action
        away_spread_class = 'highlight-pct' if away_spread_pct > home_spread_pct else ''
        home_spread_class = 'highlight-pct' if home_spread_pct > away_spread_pct else ''
        over_class = 'highlight-pct' if over_pct > under_pct else ''
        under_class = 'highlight-pct' if under_pct > over_pct else ''
        away_ml_class = 'highlight-pct' if away_ml_pct > home_ml_pct else ''
        home_ml_class = 'highlight-pct' if home_ml_pct > away_ml_pct else ''

        # Sharp signal
        signal = get_sharp_signal(game)
        signal_html = ''
        if signal:
            signal_type, team, pct = signal
            signal_html = f'<div class="sharp-signal">&#x26A0; {pct:.0f}% of bets on {team} - potential fade opportunity</div>'

        rows.append(f'''
        <div class="game-block">
            {signal_html}
            <table class="consensus-table">
                <thead>
                    <tr>
                        <th class="team-col">TEAM</th>
                        <th class="line-col">SPREAD</th>
                        <th class="pct-col">SPREAD %</th>
                        <th class="line-col">TOTAL</th>
                        <th class="pct-col">O/U %</th>
                        <th class="line-col">ML</th>
                        <th class="pct-col">ML %</th>
                    </tr>
                </thead>
                <tbody>
                    <tr class="away-row">
                        <td class="team-name">{game['away_team']}</td>
                        <td class="line-val">{format_spread(game.get('spread_away'))}</td>
                        <td class="pct-val {away_spread_class}">{away_spread_pct:.0f}%</td>
                        <td class="line-val">O {game.get('total') or '-'}</td>
                        <td class="pct-val {over_class}">{over_pct:.0f}%</td>
                        <td class="line-val">{format_ml(game.get('ml_away'))}</td>
                        <td class="pct-val {away_ml_class}">{away_ml_pct:.0f}%</td>
                    </tr>
                    <tr class="home-row">
                        <td class="team-name">{game['home_team']}</td>
                        <td class="line-val">{format_spread(game.get('spread_home'))}</td>
                        <td class="pct-val {home_spread_class}">{home_spread_pct:.0f}%</td>
                        <td class="line-val">U {game.get('total') or '-'}</td>
                        <td class="pct-val {under_class}">{under_pct:.0f}%</td>
                        <td class="line-val">{format_ml(game.get('ml_home'))}</td>
                        <td class="pct-val {home_ml_class}">{home_ml_pct:.0f}%</td>
                    </tr>
                </tbody>
            </table>
        </div>
        ''')

    return '\n'.join(rows)


def generate_html(all_games):
    """Generate the complete Sharp vs Square HTML page"""
    now = datetime.now()

    # Group games by sport
    games_by_sport = {'NFL': [], 'NBA': [], 'NHL': [], 'NCAAB': []}
    for game in all_games:
        sport = game.get('sport', 'NFL')
        if sport in games_by_sport:
            games_by_sport[sport].append(game)

    # Generate tables for each sport
    sport_tables = {}
    for sport, games in games_by_sport.items():
        sport_tables[sport] = generate_game_table_html(games, sport)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sharp vs Square - Betting Consensus Tracker | BetLegend</title>
    <meta name="description" content="Track sharp money vs public betting percentages. See where the smart money is going with live consensus data for NFL, NBA, NHL, and college basketball.">
    <link rel="canonical" href="https://betlegendpicks.com/sharp-vs-square.html">
    <link rel="icon" type="image/png" href="favicon.png">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
            line-height: 1.6;
        }}

        /* Header */
        header {{
            background: linear-gradient(135deg, #1a365d 0%, #2d4a7c 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }}

        header h1 span {{
            color: #fd5000;
        }}

        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
            max-width: 700px;
            margin: 0 auto;
        }}

        .last-updated {{
            background: rgba(255,255,255,0.1);
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin-top: 1rem;
            font-size: 0.9rem;
        }}

        /* Navigation */
        nav {{
            background: #1a365d;
            padding: 0.75rem 2rem;
            border-bottom: 3px solid #fd5000;
        }}

        nav a {{
            color: white;
            text-decoration: none;
            margin-right: 1.5rem;
            font-weight: 500;
            opacity: 0.8;
            transition: opacity 0.2s;
        }}

        nav a:hover {{
            opacity: 1;
        }}

        /* Main Content */
        main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}

        /* Explanation Box */
        .explanation {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #fd5000;
        }}

        .explanation h2 {{
            color: #1a365d;
            font-size: 1.3rem;
            margin-bottom: 1rem;
        }}

        .explanation p {{
            color: #444;
            margin-bottom: 0.75rem;
        }}

        .explanation ul {{
            margin-left: 1.5rem;
            color: #444;
        }}

        .explanation li {{
            margin-bottom: 0.5rem;
        }}

        .explanation strong {{
            color: #1a365d;
        }}

        /* Sport Tabs */
        .sport-tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }}

        .sport-tab {{
            padding: 0.75rem 1.5rem;
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1rem;
        }}

        .sport-tab:hover {{
            border-color: #1a365d;
        }}

        .sport-tab.active {{
            background: #1a365d;
            border-color: #1a365d;
            color: white;
        }}

        /* Games Container */
        .games-container {{
            display: none;
        }}

        .games-container.active {{
            display: block;
        }}

        /* Game Block */
        .game-block {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        /* Sharp Signal */
        .sharp-signal {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            font-weight: 500;
        }}

        /* Consensus Table */
        .consensus-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .consensus-table th {{
            background: #f8f9fa;
            padding: 0.75rem 1rem;
            text-align: center;
            font-size: 0.8rem;
            font-weight: 700;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 2px solid #dee2e6;
        }}

        .consensus-table th.team-col {{
            text-align: left;
            width: 25%;
        }}

        .consensus-table th.line-col {{
            width: 12%;
        }}

        .consensus-table th.pct-col {{
            width: 12%;
        }}

        .consensus-table td {{
            padding: 1rem;
            text-align: center;
            border-bottom: 1px solid #eee;
        }}

        .consensus-table .team-name {{
            text-align: left;
            font-weight: 600;
            font-size: 1.05rem;
            color: #1a1a1a;
        }}

        .consensus-table .line-val {{
            font-weight: 500;
            color: #444;
            font-size: 0.95rem;
        }}

        .consensus-table .pct-val {{
            font-weight: 700;
            font-size: 1.1rem;
            color: #666;
        }}

        .consensus-table .highlight-pct {{
            color: #1a365d;
            background: #e8f4f8;
            border-radius: 4px;
        }}

        .away-row {{
            background: #fafafa;
        }}

        .home-row {{
            background: white;
        }}

        .no-games {{
            text-align: center;
            color: #666;
            padding: 3rem;
            font-size: 1.1rem;
            background: white;
            border-radius: 12px;
        }}

        /* Legend */
        .legend {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-top: 2rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}

        .legend h3 {{
            color: #1a365d;
            font-size: 1.1rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid #fd5000;
            padding-bottom: 0.5rem;
            display: inline-block;
        }}

        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
        }}

        .legend-item {{
            display: flex;
            gap: 0.75rem;
        }}

        .legend-item strong {{
            color: #1a365d;
            display: block;
            margin-bottom: 0.25rem;
        }}

        .legend-item span {{
            color: #666;
            font-size: 0.9rem;
        }}

        /* Footer */
        footer {{
            background: #1a365d;
            color: white;
            padding: 1.5rem 2rem;
            text-align: center;
            margin-top: 2rem;
        }}

        footer a {{
            color: #fd5000;
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8rem;
            }}

            .consensus-table {{
                font-size: 0.85rem;
            }}

            .consensus-table th,
            .consensus-table td {{
                padding: 0.5rem;
            }}

            .consensus-table th.team-col {{
                width: 30%;
            }}
        }}
    </style>
</head>
<body>
    <nav>
        <a href="index.html">Home</a>
        <a href="handicapping-hub.html">Handicapping Hub</a>
        <a href="sharp-vs-square.html" style="opacity:1; color:#fd5000;">Sharp vs Square</a>
        <a href="moneyline-parlay-of-the-day.html">ML Parlay</a>
        <a href="nba.html">NBA</a>
        <a href="nfl.html">NFL</a>
        <a href="nhl.html">NHL</a>
    </nav>

    <header>
        <h1>Sharp vs <span>Square</span></h1>
        <p>See where the betting public is putting their money. Track consensus percentages for spreads, totals, and moneylines across all major sports.</p>
        <div class="last-updated">Last Updated: {now.strftime('%B %d, %Y at %I:%M %p ET')}</div>
    </header>

    <main>
        <div class="explanation">
            <h2>What Is This Page?</h2>
            <p>This page shows <strong>betting consensus data</strong> - the percentage of bets placed on each side of a game. This data helps you understand where the general public ("squares") is betting.</p>
            <p><strong>How to use this information:</strong></p>
            <ul>
                <li><strong>High percentage (65%+) on one side</strong> = Heavy public action. Some bettors like to "fade the public" and bet the other side.</li>
                <li><strong>Look for value</strong> = When the public hammers one side, the line may move, creating value on the less popular side.</li>
                <li><strong>Not a guarantee</strong> = The public wins sometimes too. Use this as ONE tool in your analysis, not the only factor.</li>
            </ul>
            <p style="margin-top: 1rem; font-size: 0.9rem; color: #666;"><em>Data updates hourly. Percentages show % of total bets on each side.</em></p>
        </div>

        <div class="sport-tabs">
            <button class="sport-tab active" data-sport="nfl">NFL</button>
            <button class="sport-tab" data-sport="nba">NBA</button>
            <button class="sport-tab" data-sport="nhl">NHL</button>
            <button class="sport-tab" data-sport="ncaab">NCAAB</button>
        </div>

        <div id="nfl-games" class="games-container active">
            {sport_tables['NFL']}
        </div>

        <div id="nba-games" class="games-container">
            {sport_tables['NBA']}
        </div>

        <div id="nhl-games" class="games-container">
            {sport_tables['NHL']}
        </div>

        <div id="ncaab-games" class="games-container">
            {sport_tables['NCAAB']}
        </div>

        <div class="legend">
            <h3>Understanding the Data</h3>
            <div class="legend-grid">
                <div class="legend-item">
                    <div>
                        <strong>SPREAD %</strong>
                        <span>Percentage of bets on each team to cover the point spread. Higher % = more public money on that side.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <div>
                        <strong>O/U %</strong>
                        <span>Percentage of bets on the Over vs Under for the total points. Shows public lean on game tempo.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <div>
                        <strong>ML %</strong>
                        <span>Percentage of bets on each team's moneyline (to win straight up). Often favors favorites.</span>
                    </div>
                </div>
                <div class="legend-item">
                    <div>
                        <strong>Highlighted Numbers</strong>
                        <span>The side with more bets is highlighted in blue. 65%+ triggers a "potential fade" alert.</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer>
        <p>&copy; 2026 BetLegend | <a href="index.html">Home</a> | Data for entertainment purposes only.</p>
    </footer>

    <script>
        document.querySelectorAll('.sport-tab').forEach(tab => {{
            tab.addEventListener('click', () => {{
                document.querySelectorAll('.sport-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.games-container').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById(tab.dataset.sport + '-games').classList.add('active');
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

    all_games = []
    for sport, url in SBR_URLS.items():
        print(f"Fetching {sport} data...")
        games = fetch_sbr_consensus(sport, url)
        all_games.extend(games)

    print()
    print(f"Total games found: {len(all_games)}")

    print("Generating HTML...")
    html = generate_html(all_games)

    repo_path = r'C:\Users\Nima\nimadamus.github.io'
    output_path = os.path.join(repo_path, 'sharp-vs-square.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print()
    print("Done!")


if __name__ == '__main__':
    main()
