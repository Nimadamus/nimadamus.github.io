"""
Script to fix placeholder data (N/A values) in sports pages with real betting lines and scores.
This script will replace N/A values with actual game data for completed NFL Week 14 games.
"""
import re
import os

# NFL Week 14 Game Data (December 4-8, 2025)
NFL_WEEK14_DATA = {
    "Cowboys @ Lions": {
        "spread": "DET -3",
        "ou": "54.5",
        "away_ml": "+130",
        "home_ml": "-155",
        "final": "LIONS 44, COWBOYS 30",
        "result": "DET covered -3 by 11 points | OVER 54.5 hit (74 total)"
    },
    "Seahawks @ Falcons": {
        "spread": "SEA -4.5",
        "ou": "44.5",
        "away_ml": "-200",
        "home_ml": "+165",
        "final": "SEAHAWKS 37, FALCONS 9",
        "result": "SEA covered -4.5 by 23.5 points | OVER 44.5 hit (46 total)"
    },
    "Bengals @ Bills": {
        "spread": "BUF -6",
        "ou": "53.5",
        "away_ml": "+230",
        "home_ml": "-285",
        "final": "BILLS 39, BENGALS 34",
        "result": "BUF FAILED to cover -6 (won by 5) | OVER 53.5 hit easily (73 total)"
    },
    "Titans @ Browns": {
        "spread": "CLE -3",
        "ou": "33.5",
        "away_ml": "+135",
        "home_ml": "-160",
        "final": None,
        "result": None
    },
    "Commanders @ Vikings": {
        "spread": "MIN -3.5",
        "ou": "42.5",
        "away_ml": "+145",
        "home_ml": "-175",
        "final": None,
        "result": None
    },
    "Dolphins @ Jets": {
        "spread": "MIA -3",
        "ou": "41.5",
        "away_ml": "-155",
        "home_ml": "+130",
        "final": "DOLPHINS 34, JETS 10",
        "result": "MIA covered -3 by 21 points | OVER 41.5 hit (44 total)"
    },
    "Saints @ Buccaneers": {
        "spread": "TB -7",
        "ou": "41.5",
        "away_ml": "+250",
        "home_ml": "-315",
        "final": "SAINTS 24, BUCCANEERS 20",
        "result": "NO covered +7 (UPSET WIN) | OVER 41.5 hit (44 total)"
    },
    "Colts @ Jaguars": {
        "spread": "IND -1.5",
        "ou": "46.5",
        "away_ml": "-130",
        "home_ml": "+110",
        "final": "JAGUARS 36, COLTS 19",
        "result": "JAX covered +1.5 (UPSET WIN by 17) | OVER 46.5 hit (55 total)"
    },
    "Steelers @ Ravens": {
        "spread": "BAL -5.5",
        "ou": "43",
        "away_ml": "+218",
        "home_ml": "-267",
        "final": "STEELERS 27, RAVENS 22",
        "result": "PIT covered +5.5 (UPSET WIN by 5) | OVER 43 hit (49 total)"
    },
    "Broncos @ Raiders": {
        "spread": "DEN -7.5",
        "ou": "40.5",
        "away_ml": "-320",
        "home_ml": "+255",
        "final": "BRONCOS WIN (11-2)",
        "result": "DEN covered -7.5 | Broncos improve to 11-2 on season"
    },
    "Bears @ Packers": {
        "spread": "GB -3.5",
        "ou": "44.5",
        "away_ml": "+145",
        "home_ml": "-175",
        "final": "PACKERS 28, BEARS 21",
        "result": "GB covered -3.5 by 3.5 points | OVER 44.5 hit (49 total)"
    },
    "Rams @ Cardinals": {
        "spread": "LAR -6",
        "ou": "47.5",
        "away_ml": "-260",
        "home_ml": "+210",
        "final": "RAMS 45+ CARDINALS (BLOWOUT)",
        "result": "LAR covered -6 easily | OVER 47.5 crushed"
    }
}

def get_game_key(away_team, home_team):
    """Generate game key from team names."""
    # Normalize team names
    team_mappings = {
        "Dallas Cowboys": "Cowboys",
        "Detroit Lions": "Lions",
        "Seattle Seahawks": "Seahawks",
        "Atlanta Falcons": "Falcons",
        "Cincinnati Bengals": "Bengals",
        "Buffalo Bills": "Bills",
        "Tennessee Titans": "Titans",
        "Cleveland Browns": "Browns",
        "Washington Commanders": "Commanders",
        "Minnesota Vikings": "Vikings",
        "Miami Dolphins": "Dolphins",
        "New York Jets": "Jets",
        "New Orleans Saints": "Saints",
        "Tampa Bay Buccaneers": "Buccaneers",
        "Indianapolis Colts": "Colts",
        "Jacksonville Jaguars": "Jaguars",
        "Pittsburgh Steelers": "Steelers",
        "Baltimore Ravens": "Ravens",
        "Denver Broncos": "Broncos",
        "Las Vegas Raiders": "Raiders",
        "Chicago Bears": "Bears",
        "Green Bay Packers": "Packers",
        "Los Angeles Rams": "Rams",
        "Arizona Cardinals": "Cardinals"
    }

    away = team_mappings.get(away_team, away_team.split()[-1])
    home = team_mappings.get(home_team, home_team.split()[-1])

    return f"{away} @ {home}"

def fix_nfl_page(filepath):
    """Fix a single NFL page by replacing N/A values with real data."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content

    # Find all game titles and their positions
    game_pattern = r'<h3 class="game-title">([^<]+) @ ([^<]+)</h3>'

    for match in re.finditer(game_pattern, content):
        away_team = match.group(1).strip()
        home_team = match.group(2).strip()
        game_key = get_game_key(away_team, home_team)

        if game_key in NFL_WEEK14_DATA:
            data = NFL_WEEK14_DATA[game_key]

            # Find the stat-row section after this game title
            game_start = match.start()
            # Look for the next game-card or end of main
            next_game = content.find('<article class="game-card">', game_start + 100)
            if next_game == -1:
                next_game = len(content)

            game_section = content[game_start:next_game]

            # Replace N/A values with real data
            # Get team abbreviations
            away_abbr = away_team.split()[-1][:3].upper()
            home_abbr = home_team.split()[-1][:3].upper()

            # Custom abbreviations
            abbr_map = {
                "Cowboys": "DAL", "Lions": "DET", "Seahawks": "SEA", "Falcons": "ATL",
                "Bengals": "CIN", "Bills": "BUF", "Titans": "TEN", "Browns": "CLE",
                "Commanders": "WSH", "Vikings": "MIN", "Dolphins": "MIA", "Jets": "NYJ",
                "Saints": "NO", "Buccaneers": "TB", "Colts": "IND", "Jaguars": "JAX",
                "Steelers": "PIT", "Ravens": "BAL", "Broncos": "DEN", "Raiders": "LV",
                "Bears": "CHI", "Packers": "GB", "Rams": "LAR", "Cardinals": "ARI"
            }

            away_abbr = abbr_map.get(away_team.split()[-1], away_abbr)
            home_abbr = abbr_map.get(home_team.split()[-1], home_abbr)

            # Replace spread
            game_section = re.sub(
                r'<span class="value">N/A</span><span class="label">Spread</span>',
                f'<span class="value">{data["spread"]}</span><span class="label">Spread</span>',
                game_section, count=1
            )

            # Replace away ML
            game_section = re.sub(
                rf'<span class="value">N/A</span><span class="label">{away_abbr} ML</span>',
                f'<span class="value">{data["away_ml"]}</span><span class="label">{away_abbr} ML</span>',
                game_section
            )

            # Replace home ML
            game_section = re.sub(
                rf'<span class="value">N/A</span><span class="label">{home_abbr} ML</span>',
                f'<span class="value">{data["home_ml"]}</span><span class="label">{home_abbr} ML</span>',
                game_section
            )

            # Add final score if available
            if data["final"]:
                # Check if result section already exists
                if 'result-section' not in game_section:
                    # Add result section after stat-row
                    result_html = f'''
<div class="result-section" style="background:rgba(0,200,100,0.15);border:1px solid rgba(0,200,100,0.3);border-radius:10px;padding:12px;margin:12px 0;">
<p style="font-size:0.85rem;color:#00ff88;margin-bottom:6px;font-weight:700;">FINAL: {data["final"]}</p>
<p style="font-size:0.8rem;color:#ccc;margin:4px 0;">{data["result"]}</p>
</div>'''
                    # Insert after the stat-row closing div
                    stat_row_end = game_section.find('</div>\n<div class="injury-section"')
                    if stat_row_end != -1:
                        game_section = game_section[:stat_row_end+6] + result_html + game_section[stat_row_end+6:]

            # Replace the game section in content
            content = content[:game_start] + game_section + content[next_game:]

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    repo_path = r'C:\Users\Nima\nimadamus.github.io'

    # Find NFL pages with N/A values
    nfl_pages = []
    for f in os.listdir(repo_path):
        if f.startswith('nfl-page') and f.endswith('.html'):
            filepath = os.path.join(repo_path, f)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
                if 'class="value">N/A</span>' in file.read():
                    nfl_pages.append(filepath)

    print(f"Found {len(nfl_pages)} NFL pages with N/A values")

    for page in nfl_pages:
        if fix_nfl_page(page):
            print(f"Fixed: {os.path.basename(page)}")
        else:
            print(f"No changes: {os.path.basename(page)}")

if __name__ == "__main__":
    main()
