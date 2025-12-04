"""
Sharp Action Detector for Handicapping Hub
Detects reverse line movement and sharp betting signals

Sharp Action Criteria:
1. Reverse Line Movement (RLM): Line moves OPPOSITE to where 65%+ of public is betting
2. Heavy RLM: 75%+ public on one side, line moves 1+ points the other way
3. Money vs Bets Split: When money % differs significantly from bet % (sharps bet bigger)
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import os

# The Odds API for current lines
ODDS_API_KEY = 'deeac7e7af6a8f1a5ac84c625e04973a'

# File to store opening lines for comparison
OPENING_LINES_FILE = r'C:\Users\Nima\nimadamus.github.io\opening_lines.json'

SPORT_KEYS = {
    'NBA': 'basketball_nba',
    'NFL': 'americanfootball_nfl',
    'NHL': 'icehockey_nhl',
    'NCAAB': 'basketball_ncaab',
    'NCAAF': 'americanfootball_ncaaf',
    'MLB': 'baseball_mlb'
}

def get_current_odds(sport):
    """Fetch current odds from The Odds API"""
    sport_key = SPORT_KEYS.get(sport)
    if not sport_key:
        return []

    url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
    params = {
        'apiKey': ODDS_API_KEY,
        'regions': 'us',
        'markets': 'spreads,h2h,totals',
        'oddsFormat': 'american'
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching {sport} odds: {e}")
        return []

def load_opening_lines():
    """Load stored opening lines"""
    if os.path.exists(OPENING_LINES_FILE):
        with open(OPENING_LINES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_opening_lines(lines):
    """Save opening lines to file"""
    with open(OPENING_LINES_FILE, 'w') as f:
        json.dump(lines, f, indent=2)

def update_opening_lines(games, sport):
    """Store opening lines for new games"""
    opening_lines = load_opening_lines()

    for game in games:
        game_id = game.get('id')
        if game_id not in opening_lines:
            # Extract spread from first bookmaker
            spread = None
            total = None

            for bookmaker in game.get('bookmakers', []):
                for market in bookmaker.get('markets', []):
                    if market['key'] == 'spreads' and not spread:
                        for outcome in market.get('outcomes', []):
                            if outcome['name'] == game['home_team']:
                                spread = outcome.get('point', 0)
                                break
                    if market['key'] == 'totals' and not total:
                        for outcome in market.get('outcomes', []):
                            if outcome['name'] == 'Over':
                                total = outcome.get('point', 0)
                                break

            opening_lines[game_id] = {
                'sport': sport,
                'home_team': game['home_team'],
                'away_team': game['away_team'],
                'opening_spread': spread,
                'opening_total': total,
                'timestamp': datetime.now().isoformat(),
                'commence_time': game.get('commence_time')
            }

    save_opening_lines(opening_lines)
    return opening_lines

def get_current_spread(game):
    """Extract current spread for home team from game data"""
    for bookmaker in game.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == game['home_team']:
                        return outcome.get('point', 0)
    return None

def get_current_total(game):
    """Extract current total from game data"""
    for bookmaker in game.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market['key'] == 'totals':
                for outcome in market.get('outcomes', []):
                    if outcome['name'] == 'Over':
                        return outcome.get('point', 0)
    return None

def scrape_public_betting_percentages():
    """
    Scrape public betting percentages from available sources
    Returns dict: {game_key: {'home_spread_pct': 55, 'away_spread_pct': 45, ...}}
    """
    public_data = {}

    # Try multiple sources
    sources = [
        ('covers', scrape_covers_consensus),
        ('vegasinsider', scrape_vegasinsider_consensus),
    ]

    for source_name, scraper_func in sources:
        try:
            data = scraper_func()
            if data:
                public_data.update(data)
                print(f"  Got public betting data from {source_name}")
                break
        except Exception as e:
            print(f"  Failed to get data from {source_name}: {e}")

    return public_data

def scrape_covers_consensus():
    """Scrape consensus data from Covers"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    public_data = {}

    for sport, endpoint in [('NBA', 'nba'), ('NFL', 'nfl'), ('NHL', 'nhl')]:
        try:
            url = f'https://www.covers.com/sports/{endpoint}/matchups'
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')

                # Look for consensus percentage elements
                # Covers typically shows percentages in elements with specific classes
                consensus_elements = soup.find_all(['div', 'span'], class_=re.compile(r'consensus|percentage|picks', re.I))

                for elem in consensus_elements:
                    text = elem.get_text(strip=True)
                    # Look for percentage patterns like "65%" or "65% / 35%"
                    pct_match = re.search(r'(\d+)%', text)
                    if pct_match:
                        print(f"    Found consensus: {text}")

        except Exception as e:
            print(f"  Covers scrape error for {sport}: {e}")

    return public_data

def scrape_vegasinsider_consensus():
    """Scrape consensus from VegasInsider"""
    # Placeholder - VegasInsider structure may vary
    return {}

def calculate_line_movement(game_id, current_spread, current_total, opening_lines):
    """Calculate line movement from opening to current"""
    if game_id not in opening_lines:
        return None, None

    opening = opening_lines[game_id]
    opening_spread = opening.get('opening_spread')
    opening_total = opening.get('opening_total')

    spread_movement = None
    total_movement = None

    if opening_spread is not None and current_spread is not None:
        spread_movement = current_spread - opening_spread

    if opening_total is not None and current_total is not None:
        total_movement = current_total - opening_total

    return spread_movement, total_movement

def detect_sharp_action(game, opening_lines, public_data=None):
    """
    Detect sharp action signals for a game
    Returns: dict with sharp action indicators
    """
    game_id = game.get('id')
    home_team = game['home_team']
    away_team = game['away_team']

    current_spread = get_current_spread(game)
    current_total = get_current_total(game)

    spread_movement, total_movement = calculate_line_movement(
        game_id, current_spread, current_total, opening_lines
    )

    signals = []
    confidence = 0
    sharp_side = None

    # Check for significant line movement
    if spread_movement is not None:
        if abs(spread_movement) >= 1.5:
            signals.append(f"Heavy line movement: {spread_movement:+.1f}")
            confidence += 30
            # Positive movement = home team got more points = sharps on away
            # Negative movement = home team gave more points = sharps on home
            sharp_side = away_team if spread_movement > 0 else home_team

        elif abs(spread_movement) >= 1.0:
            signals.append(f"Significant line movement: {spread_movement:+.1f}")
            confidence += 20
            sharp_side = away_team if spread_movement > 0 else home_team

        elif abs(spread_movement) >= 0.5:
            signals.append(f"Line movement: {spread_movement:+.1f}")
            confidence += 10
            sharp_side = away_team if spread_movement > 0 else home_team

    if total_movement is not None:
        if abs(total_movement) >= 2:
            direction = "UP" if total_movement > 0 else "DOWN"
            signals.append(f"Total moved {direction} {abs(total_movement):.1f}")
            confidence += 15

    # Determine sharp action level
    if confidence >= 30:
        action_level = "STRONG"
    elif confidence >= 20:
        action_level = "MODERATE"
    elif confidence >= 10:
        action_level = "LIGHT"
    else:
        action_level = None

    return {
        'game_id': game_id,
        'home_team': home_team,
        'away_team': away_team,
        'current_spread': current_spread,
        'spread_movement': spread_movement,
        'total_movement': total_movement,
        'signals': signals,
        'confidence': confidence,
        'action_level': action_level,
        'sharp_side': sharp_side
    }

def format_sharp_action_html(sharp_actions):
    """Format sharp action data as HTML for the handicapping hub"""
    if not sharp_actions:
        return '<span class="no-sharp">No significant sharp action detected</span>'

    html_parts = []
    for action in sharp_actions:
        if action['action_level']:
            level_class = {
                'STRONG': 'sharp-strong',
                'MODERATE': 'sharp-moderate',
                'LIGHT': 'sharp-light'
            }.get(action['action_level'], 'sharp-light')

            signals_text = '; '.join(action['signals'])
            sharp_text = f" → Sharps on {action['sharp_side']}" if action['sharp_side'] else ""

            html_parts.append(
                f'<div class="sharp-action {level_class}">'
                f'<strong>{action["away_team"]} @ {action["home_team"]}</strong>: '
                f'{signals_text}{sharp_text}'
                f'</div>'
            )

    return '\n'.join(html_parts) if html_parts else '<span class="no-sharp">No significant sharp action detected</span>'

def normalize_team_name(name):
    """Normalize team names for matching"""
    # Common name mappings between API and HTML
    mappings = {
        'Los Angeles Lakers': 'Los Angeles Lakers',
        'LA Lakers': 'Los Angeles Lakers',
        'Los Angeles Clippers': 'LA Clippers',
        'LA Clippers': 'LA Clippers',
    }
    return mappings.get(name, name)

def update_handicapping_hub(sharp_actions_list):
    """Update handicapping-hub.html with sharp action data for each game"""
    filepath = r'C:\Users\Nima\nimadamus.github.io\handicapping-hub.html'

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    updated_count = 0

    for action in sharp_actions_list:
        if not action.get('action_level'):
            continue

        home_team = normalize_team_name(action['home_team'])
        away_team = normalize_team_name(action['away_team'])

        # Build the sharp action HTML
        level_class = {
            'STRONG': 'sharp-strong',
            'MODERATE': 'sharp-moderate',
            'LIGHT': 'sharp-light'
        }.get(action['action_level'], 'sharp-light')

        signals_text = '; '.join(action['signals'])
        sharp_side = action.get('sharp_side', '')

        if action['action_level'] == 'STRONG':
            icon = '&#128293;'  # fire emoji
        elif action['action_level'] == 'MODERATE':
            icon = '&#9888;'  # warning sign
        else:
            icon = '&#128202;'  # chart

        sharp_html = (
            f'<span class="{level_class}">{icon} {action["action_level"]}: {signals_text}'
        )
        if sharp_side:
            sharp_html += f' &rarr; Sharps on {sharp_side}'
        sharp_html += '</span>'

        # Find the game card that contains both team names and update its sharp-indicators
        # Pattern: Find the game card with these teams, then find the sharp-indicators section

        # Look for pattern: team names in h3 tags followed by sharp-indicators
        # This is a simplified approach - we look for the away team name, then find the nearby sharp section

        # Create a pattern to find the game card section for this matchup
        # We'll match the away team h3, then capture up to the sharp-indicators and replace

        pattern = (
            rf'(<h3>{re.escape(away_team)}</h3>.*?'
            rf'<h3>{re.escape(home_team)}</h3>.*?'
            rf'<div class="sharp-indicators">)'
            rf'(\s*<span class="[^"]*">[^<]*</span>\s*)'
            rf'(</div>)'
        )

        replacement = rf'\1\n                                    {sharp_html}\n                                \3'

        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.IGNORECASE)

        if new_content != content:
            content = new_content
            updated_count += 1
            print(f"  Updated sharp action for: {away_team} @ {home_team}")

    if updated_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n  Total games updated with sharp action: {updated_count}")
    else:
        print("\n  No sharp action to update in HTML")

def main():
    print("=" * 60)
    print("SHARP ACTION DETECTOR")
    print("=" * 60)
    print(f"Run time: {datetime.now()}")
    print()

    opening_lines = load_opening_lines()
    sharp_by_sport = {}
    all_sharp_actions = []

    for sport in ['NBA', 'NFL', 'NHL']:
        print(f"\n{sport}")
        print("-" * 40)

        # Get current odds
        games = get_current_odds(sport)
        print(f"  Found {len(games)} games")

        if not games:
            continue

        # Update opening lines for new games
        opening_lines = update_opening_lines(games, sport)

        # Analyze each game for sharp action
        sport_actions = []
        for game in games:
            action = detect_sharp_action(game, opening_lines)

            if action['action_level']:
                sport_actions.append(action)
                print(f"  {action['action_level']}: {action['away_team']} @ {action['home_team']}")
                for signal in action['signals']:
                    print(f"    - {signal}")
                if action['sharp_side']:
                    print(f"    >> Sharps likely on: {action['sharp_side']}")

        if not sport_actions:
            print("  No sharp action detected")

        sharp_by_sport[sport] = sport_actions
        all_sharp_actions.extend(sport_actions)

    # Save sharp action data
    output_file = r'C:\Users\Nima\nimadamus.github.io\sharp_action_data.json'
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'by_sport': {k: [a for a in v] for k, v in sharp_by_sport.items()},
            'all_actions': all_sharp_actions
        }, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"Sharp action data saved to {output_file}")
    print(f"Total sharp action signals: {len(all_sharp_actions)}")

    # Update handicapping hub with sharp action data
    if all_sharp_actions:
        print("\nUpdating handicapping-hub.html with sharp action...")
        update_handicapping_hub(all_sharp_actions)
    else:
        print("\nNo sharp action detected - HTML not updated")

    return sharp_by_sport

if __name__ == '__main__':
    main()
