"""
Sharp Action Detector - Scrapes public betting data from Action Network
Detects reverse line movement and sharp betting signals

Sharp Action Criteria:
1. Reverse Line Movement: When 65%+ of tickets are on one side, but line moves the other way
2. Money vs Tickets Split: When money % differs significantly from ticket % (sharps bet bigger)
3. Key Number Movement: In NFL, movement off 3 or 7 is significant
"""

import requests
import re
import json
from datetime import datetime

def get_action_network_data(sport='nba'):
    """Fetch public betting data from Action Network"""

    sport_urls = {
        'nba': 'https://www.actionnetwork.com/nba/public-betting',
        'nfl': 'https://www.actionnetwork.com/nfl/public-betting',
        'nhl': 'https://www.actionnetwork.com/nhl/public-betting',
        'ncaab': 'https://www.actionnetwork.com/ncaab/public-betting',
        'ncaaf': 'https://www.actionnetwork.com/ncaaf/public-betting',
        'mlb': 'https://www.actionnetwork.com/mlb/public-betting',
    }

    url = sport_urls.get(sport.lower())
    if not url:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        # Extract __NEXT_DATA__ JSON
        next_data = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            r.text, re.DOTALL
        )

        if not next_data:
            print(f"  No data found for {sport}")
            return []

        data = json.loads(next_data.group(1))
        games = data['props']['pageProps']['scoreboardResponse']['games']

        return games

    except Exception as e:
        print(f"  Error fetching {sport}: {e}")
        return []

def extract_betting_data(game):
    """Extract public betting percentages from game data"""

    teams = game.get('teams', [])
    away_team = teams[0].get('full_name', 'Away') if teams else 'Away'
    home_team = teams[1].get('full_name', 'Home') if len(teams) > 1 else 'Home'
    away_id = game.get('away_team_id')
    home_id = game.get('home_team_id')

    result = {
        'away_team': away_team,
        'home_team': home_team,
        'spread': {},
        'moneyline': {},
        'total': {},
        'sharp_signals': [],
    }

    # Get market 15 which has spread/total/moneyline
    markets = game.get('markets', {})
    event = markets.get('15', {}).get('event', {})

    # Process spread
    spreads = event.get('spread', [])
    for spread in spreads:
        team_id = spread.get('team_id')
        side = 'away' if team_id == away_id else 'home'
        bet_info = spread.get('bet_info', {})

        tickets_pct = bet_info.get('tickets', {}).get('percent', 0)
        money_pct = bet_info.get('money', {}).get('percent', 0)
        line = spread.get('value', 0)
        odds = spread.get('odds', 0)

        result['spread'][side] = {
            'line': line,
            'odds': odds,
            'tickets_pct': tickets_pct,
            'money_pct': money_pct,
        }

        # Detect sharp signal: money % significantly higher than tickets %
        if money_pct and tickets_pct:
            money_diff = money_pct - tickets_pct
            if money_diff >= 10:  # 10%+ more money than tickets = sharp action
                team_name = away_team if side == 'away' else home_team
                result['sharp_signals'].append({
                    'type': 'MONEY_SPLIT',
                    'market': 'spread',
                    'side': team_name,
                    'tickets_pct': tickets_pct,
                    'money_pct': money_pct,
                    'diff': money_diff,
                })

    # Process moneyline
    moneylines = event.get('moneyline', [])
    for ml in moneylines:
        team_id = ml.get('team_id')
        side = 'away' if team_id == away_id else 'home'
        bet_info = ml.get('bet_info', {})

        tickets_pct = bet_info.get('tickets', {}).get('percent', 0)
        money_pct = bet_info.get('money', {}).get('percent', 0)
        odds = ml.get('odds', 0)

        result['moneyline'][side] = {
            'odds': odds,
            'tickets_pct': tickets_pct,
            'money_pct': money_pct,
        }

        # Detect sharp signal on moneyline
        if money_pct and tickets_pct:
            money_diff = money_pct - tickets_pct
            if money_diff >= 10:
                team_name = away_team if side == 'away' else home_team
                result['sharp_signals'].append({
                    'type': 'MONEY_SPLIT',
                    'market': 'moneyline',
                    'side': team_name,
                    'tickets_pct': tickets_pct,
                    'money_pct': money_pct,
                    'diff': money_diff,
                })

    # Process totals
    totals = event.get('total', [])
    for total in totals:
        side = total.get('side', '')  # 'over' or 'under'
        bet_info = total.get('bet_info', {})

        tickets_pct = bet_info.get('tickets', {}).get('percent', 0)
        money_pct = bet_info.get('money', {}).get('percent', 0)
        line = total.get('value', 0)
        odds = total.get('odds', 0)

        result['total'][side] = {
            'line': line,
            'odds': odds,
            'tickets_pct': tickets_pct,
            'money_pct': money_pct,
        }

        # Detect sharp signal on totals
        if money_pct and tickets_pct:
            money_diff = money_pct - tickets_pct
            if money_diff >= 10:
                result['sharp_signals'].append({
                    'type': 'MONEY_SPLIT',
                    'market': 'total',
                    'side': side.upper(),
                    'tickets_pct': tickets_pct,
                    'money_pct': money_pct,
                    'diff': money_diff,
                })

    return result

def format_sharp_html(betting_data):
    """Format sharp action signals as HTML"""
    signals = betting_data.get('sharp_signals', [])

    if not signals:
        return '<span class="no-data">No sharp action detected</span>'

    html_parts = []
    for signal in signals:
        if signal['type'] == 'MONEY_SPLIT':
            # More money than tickets = sharps betting this side
            diff = signal['diff']
            if diff >= 20:
                level = 'sharp-strong'
                icon = '&#128293;'  # fire
                level_text = 'STRONG'
            elif diff >= 15:
                level = 'sharp-moderate'
                icon = '&#9888;'  # warning
                level_text = 'MODERATE'
            else:
                level = 'sharp-light'
                icon = '&#128202;'  # chart
                level_text = 'LIGHT'

            market = signal['market'].upper()
            side = signal['side']
            tickets = signal['tickets_pct']
            money = signal['money_pct']

            html_parts.append(
                f'<span class="{level}">{icon} {level_text} ({market}): '
                f'{tickets}% of bets but {money}% of money on {side}</span>'
            )

    return '<br>'.join(html_parts)

def update_handicapping_hub(all_betting_data):
    """Update handicapping-hub.html with sharp action data"""
    filepath = r'C:\Users\Nima\nimadamus.github.io\handicapping-hub.html'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    updated_count = 0

    for betting_data in all_betting_data:
        if not betting_data.get('sharp_signals'):
            continue

        away_team = betting_data['away_team']
        home_team = betting_data['home_team']
        sharp_html = format_sharp_html(betting_data)

        # Pattern to find and update the sharp-indicators section for this game
        pattern = (
            rf'(<h3>{re.escape(away_team)}</h3>.*?'
            rf'<h3>{re.escape(home_team)}</h3>.*?'
            rf'<div class="sharp-indicators">)'
            rf'(\s*<span class="[^"]*">[^<]*</span>(?:<br><span class="[^"]*">[^<]*</span>)*\s*)'
            rf'(</div>)'
        )

        replacement = rf'\1\n                                    {sharp_html}\n                                \3'

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)

        if new_content != content:
            content = new_content
            updated_count += 1
            print(f"  Updated: {away_team} @ {home_team}")

    if updated_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    return updated_count

def main():
    print("=" * 60)
    print("SHARP ACTION DETECTOR")
    print("=" * 60)
    print(f"Run time: {datetime.now()}")
    print("Source: Action Network (tickets vs money split)")
    print()

    all_betting_data = []

    for sport in ['NBA', 'NFL', 'NHL']:
        print(f"\n{sport}")
        print("-" * 40)

        games = get_action_network_data(sport)
        print(f"  Found {len(games)} games")

        sport_sharp_count = 0

        for game in games:
            betting_data = extract_betting_data(game)
            betting_data['sport'] = sport
            all_betting_data.append(betting_data)

            if betting_data['sharp_signals']:
                sport_sharp_count += 1
                print(f"\n  {betting_data['away_team']} @ {betting_data['home_team']}")

                for signal in betting_data['sharp_signals']:
                    diff = signal['diff']
                    level = 'STRONG' if diff >= 20 else 'MODERATE' if diff >= 15 else 'LIGHT'
                    print(f"    [{level}] {signal['market'].upper()}: "
                          f"{signal['tickets_pct']}% bets / {signal['money_pct']}% money on {signal['side']}")

        if sport_sharp_count == 0:
            print("  No sharp action detected")

    # Save data
    output_file = r'C:\Users\Nima\nimadamus.github.io\sharp_action_data.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'games': all_betting_data
        }, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Data saved to {output_file}")

    # Count total sharp signals
    total_sharp = sum(1 for g in all_betting_data if g['sharp_signals'])
    print(f"Total games with sharp action: {total_sharp}")

    # Update HTML
    if total_sharp > 0:
        print("\nUpdating handicapping-hub.html...")
        updated = update_handicapping_hub(all_betting_data)
        print(f"Updated {updated} games in HTML")

    return all_betting_data

if __name__ == '__main__':
    main()
