import os
import sys
import pickle
import json
from datetime import datetime, timedelta

# Path setup
REPO_PATH = 'C:/Users/Nima/nimadamus.github.io'
TOOL_PATH = 'C:/Users/Nima/handicapping_tool'
sys.path.append(os.path.join(REPO_PATH, 'scripts'))
sys.path.append(TOOL_PATH)

try:
    from handicapping_hub_production import generate_page, block_line_movements
    print("[SUCCESS] Imported generation functions.")
except ImportError as e:
    print(f"[ERROR] Could not import hub functions: {e}")
    sys.exit(1)

def backfill_date(target_date_iso):
    print(f"\n--- Backfilling {target_date_iso} ---")
    
    # Load universal games
    pkl_path = os.path.join(TOOL_PATH, 'universal_games.pkl')
    if not os.path.exists(pkl_path):
        print(f"[ERROR] {pkl_path} not found.")
        return

    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
        
    # Correctly handle tuple return from pkl
    if isinstance(data, tuple):
        all_universal = data[0]
    else:
        all_universal = data

    # Filter for target date
    day_games = [g for g in all_universal if isinstance(g, dict) and g.get('Date') == target_date_iso]
    print(f"Found {len(day_games)} games in universal_games.pkl for {target_date_iso}")

    # Map universal games to hub format
    all_games = {'NBA': [], 'NFL': [], 'NHL': [], 'MLB': [], 'NCAAB': [], 'NCAAF': []}
    
    for ug in day_games:
        sport = ug.get('Sport', 'MLB').upper()
        if sport not in all_games: continue
        
        # Use a defaultdict to prevent crashes on any missing stat keys
        from collections import defaultdict
        stats_stub = defaultdict(lambda: '<span class="stat-na">—</span>')
        
        # Pre-populate common keys to be safe
        common_keys = ['ppg', 'opp_ppg', 'ats', 'ou', 'rpg', 'rapg', 'gf', 'ga', 'pwr', 'gd', 'rd']
        for k in common_keys:
            stats_stub[k] = '<span class="stat-na">—</span>'
        
        # Try to pull real historical moneyline if it exists in the pickle
        ml_away = ug.get('AwayMoneyline', 'N/A')
        ml_home = ug.get('HomeMoneyline', 'N/A')
        total = ug.get('Total', 'N/A')
        spread = ug.get('Spread', 'N/A')
        
        game_stub = {
            'time': ug.get('GameTime', 'TBD'),
            'venue': ug.get('Venue', 'Historical Data'),
            'network': '',
            'away': {
                'abbr': ug.get('AwayAbbr', ug.get('AwayTeam', 'UNK')),
                'name': ug.get('AwayTeam', 'Unknown'),
                'record': '0-0',
                'team_id': '',
                'stats': stats_stub,
                'injuries': []
            },
            'home': {
                'abbr': ug.get('HomeAbbr', ug.get('HomeTeam', 'UNK')),
                'name': ug.get('HomeTeam', 'Unknown'),
                'record': '0-0',
                'team_id': '',
                'stats': stats_stub,
                'injuries': []
            },
            'odds': {
                'spread_away': str(spread) if spread != 'N/A' else 'N/A',
                'spread_home': str(-spread) if spread != 'N/A' and isinstance(spread, (int, float)) else 'N/A',
                'ml_away': str(ml_away) if ml_away != 'N/A' else 'N/A',
                'ml_home': str(ml_home) if ml_home != 'N/A' else 'N/A',
                'total': str(total) if total != 'N/A' else 'N/A'
            },
            'h2h': None
        }
        all_games[sport].append(game_stub)

    # Generate HTML
    dt = datetime.fromisoformat(target_date_iso)
    date_str = dt.strftime('%B %d, %Y')
    
    html = generate_page(all_games, date_str)
    
    if not any(all_games.values()):
        no_slate_msg = '<div class="no-games">No qualifying games were available for this slate.</div>'
        html = html.replace('{sport_sections}', no_slate_msg)

    # Simple trend message since we aren't running the full combinatorial engine for backfill
    html = html.replace('HISTORICAL TRENDS', 'HISTORICAL TRENDS (No qualified trends found for this slate)')
    html = block_line_movements(html)

    # Save to archive
    archive_dir = os.path.join(REPO_PATH, 'handicapping-hub-archive')
    archive_path = os.path.join(archive_dir, f'hub-{target_date_iso}.html')
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"[SUCCESS] Saved to {archive_path}")

if __name__ == "__main__":
    dates = ['2026-05-04', '2026-05-06', '2026-04-18', '2026-04-19', '2026-04-20', '2026-04-21']
    for d in dates:
        try:
            backfill_date(d)
        except Exception as e:
            print(f"[CRITICAL ERROR] Failed backfill for {d}: {e}")
