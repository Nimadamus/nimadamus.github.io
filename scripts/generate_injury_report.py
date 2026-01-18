#!/usr/bin/env python3
"""
BetLegend Injury Report Generator
Organized by TEAM - shows all players, all statuses, injury details
Runs hourly via GitHub Actions
"""

import urllib.request
import json
from datetime import datetime, timezone
import os

# ESPN API endpoints
ENDPOINTS = {
    'NBA': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries',
    'NHL': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/injuries',
    'NFL': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries',
    'MLB': 'https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/injuries'
}

# MLB Offseason: November through March - no active injuries to report
MLB_OFFSEASON_MONTHS = [11, 12, 1, 2, 3]  # Nov, Dec, Jan, Feb, Mar

# Status display order (most severe first)
STATUS_ORDER = ['Out', 'Injured Reserve', 'Doubtful', 'Questionable', 'Day-To-Day', 'Probable']

# =============================================================================
# NFL PLAYOFF TEAMS - UPDATE THIS LIST AS TEAMS ARE ELIMINATED
# =============================================================================
# Last Updated: January 18, 2026 - After Divisional Round Saturday games
#
# HOW TO UPDATE:
# 1. After each playoff game, remove the losing team from this list
# 2. Update the comment with the date and round
# 3. Push the change - GitHub Actions will regenerate the injury report
#
# DIVISIONAL ROUND RESULTS (Jan 18, 2026):
# - Seahawks 41, 49ers 6 → 49ers ELIMINATED
# - Broncos 33, Bills 30 (OT) → Bills ELIMINATED
#
# ELIMINATED THIS POSTSEASON:
# - Wild Card: Steelers, Chargers, Jaguars, Panthers, Packers, Eagles
# - Divisional: 49ers, Bills
# =============================================================================
NFL_PLAYOFF_TEAMS = [
    'Seattle Seahawks',      # NFC - Beat 49ers 41-6 (Divisional)
    'Chicago Bears',         # NFC 2 seed - plays Rams Sunday
    'Los Angeles Rams',      # NFC 5 seed - plays Bears Sunday
    'Denver Broncos',        # AFC - Beat Bills 33-30 OT (Divisional)
    'New England Patriots',  # AFC 2 seed - plays Texans Sunday
    'Houston Texans',        # AFC 5 seed - plays Patriots Sunday
]

# =============================================================================
# NBA PLAYOFF TEAMS - UPDATE WHEN PLAYOFFS BEGIN (typically mid-April)
# =============================================================================
# Set NBA_PLAYOFFS_ACTIVE = True when NBA playoffs start
# Then add the 16 playoff teams to the list below
# During regular season, all teams are shown
#
# NBA Playoffs typically run mid-April through mid-June
# =============================================================================
NBA_PLAYOFFS_ACTIVE = False  # Set to True when NBA playoffs begin

NBA_PLAYOFF_TEAMS = [
    # Add playoff teams here when playoffs start (16 teams)
    # Example:
    # 'Boston Celtics',
    # 'Cleveland Cavaliers',
    # etc.
]

# Supplemental injuries not always captured by ESPN API
# VERIFIED from official sources - major season-ending injuries
SUPPLEMENTAL_INJURIES = {
    'NFL': {
        'San Francisco 49ers': [
            {
                'name': 'Nick Bosa',
                'position': 'DE',
                'status': 'Injured Reserve',
                'injury': 'ACL',
                'comment': 'Torn ACL in right knee (Week 3 vs Cardinals, Sept 21) - Out for season',
                'days_out': 113,  # Sept 21 to Jan 12
                'days_display': '4 months',
                'date': '2025-09-21'
            },
            {
                'name': 'Fred Warner',
                'position': 'LB',
                'status': 'Injured Reserve',
                'injury': 'Ankle',
                'comment': 'Dislocated/fractured right ankle (Week 6 vs Buccaneers) - Unlikely for Divisional',
                'days_out': 89,   # Oct 15 to Jan 12
                'days_display': '3 months',
                'date': '2025-10-15'
            }
        ]
    }
}

def get_team_logo(sport, team_id):
    sport_path = {'NBA': 'nba', 'NHL': 'nhl', 'NFL': 'nfl', 'MLB': 'mlb'}
    return f"https://a.espncdn.com/i/teamlogos/{sport_path.get(sport, 'nba')}/500/{team_id}.png"

def fetch_injuries(sport, url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            return data.get('injuries', [])
    except Exception as e:
        print(f"Error fetching {sport}: {e}")
        return []

def extract_injury_type(comment):
    if not comment:
        return "Undisclosed"
    injuries = [
        'ACL', 'MCL', 'ankle', 'knee', 'hamstring', 'groin', 'shoulder',
        'concussion', 'head', 'back', 'hip', 'calf', 'quad', 'quadriceps',
        'foot', 'wrist', 'hand', 'finger', 'thumb', 'elbow', 'arm',
        'oblique', 'ribs', 'neck', 'Achilles', 'toe', 'illness',
        'rest', 'personal', 'suspension', 'lower body', 'upper body',
        'leg', 'thigh', 'abdomen', 'eye', 'jaw', 'nose', 'dental'
    ]
    comment_lower = comment.lower()
    for injury in injuries:
        if injury.lower() in comment_lower:
            return injury.title()
    import re
    match = re.search(r'\(([^)]+)\)', comment)
    if match:
        return match.group(1).title()
    return "Undisclosed"

def calculate_days_out(date_str):
    if not date_str:
        return None
    try:
        injury_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - injury_date
        return delta.days
    except:
        return None

def format_days_out(days):
    if days is None:
        return "Recently"
    if days == 0:
        return "Today"
    if days == 1:
        return "1 day"
    if days < 7:
        return f"{days} days"
    if days < 14:
        return "1 week"
    if days < 30:
        return f"{days // 7} weeks"
    if days < 60:
        return "1 month"
    return f"{days // 30} months"

def parse_all_injuries(sport, teams_data):
    teams = {}
    for team in teams_data:
        team_name = team.get('displayName', 'Unknown')
        team_id = team.get('id', '')

        # NFL: Only include playoff teams
        if sport == 'NFL' and team_name not in NFL_PLAYOFF_TEAMS:
            continue

        # NBA: Only include playoff teams when playoffs are active
        if sport == 'NBA' and NBA_PLAYOFFS_ACTIVE and team_name not in NBA_PLAYOFF_TEAMS:
            continue

        team_injuries = team.get('injuries', [])
        players = []

        # Track existing player names to avoid duplicates with supplemental
        existing_names = set()

        for inj in team_injuries:
            status = inj.get('status', 'Unknown')
            if status == 'Active':
                continue
            athlete = inj.get('athlete', {})
            comment = inj.get('shortComment', '')
            date_str = inj.get('date', '')
            position = ''
            if 'position' in athlete:
                position = athlete['position'].get('abbreviation', '')
            injury_type = extract_injury_type(comment)
            days_out = calculate_days_out(date_str)
            player_name = athlete.get('displayName', 'Unknown')
            existing_names.add(player_name)
            players.append({
                'name': player_name,
                'position': position,
                'status': status,
                'injury': injury_type,
                'comment': comment,
                'days_out': days_out,
                'days_display': format_days_out(days_out),
                'date': date_str
            })

        # Add supplemental injuries if available (major injuries not in API)
        if sport in SUPPLEMENTAL_INJURIES and team_name in SUPPLEMENTAL_INJURIES[sport]:
            for supp_injury in SUPPLEMENTAL_INJURIES[sport][team_name]:
                # Only add if not already in the list
                if supp_injury['name'] not in existing_names:
                    players.append(supp_injury)

        def status_sort(p):
            try:
                return STATUS_ORDER.index(p['status'])
            except ValueError:
                return 99
        players.sort(key=status_sort)
        teams[team_name] = {'id': team_id, 'players': players}

    # For NFL, ensure all playoff teams are listed even if no injuries
    if sport == 'NFL':
        for playoff_team in NFL_PLAYOFF_TEAMS:
            if playoff_team not in teams:
                # ESPN team IDs for remaining NFL playoff teams
                team_id_map = {
                    'Seattle Seahawks': '26',
                    'Chicago Bears': '3',
                    'Los Angeles Rams': '14',
                    'Denver Broncos': '7',
                    'New England Patriots': '17',
                    'Houston Texans': '34'
                }
                teams[playoff_team] = {
                    'id': team_id_map.get(playoff_team, ''),
                    'players': SUPPLEMENTAL_INJURIES.get('NFL', {}).get(playoff_team, [])
                }

    # For NBA, ensure all playoff teams are listed when playoffs are active
    if sport == 'NBA' and NBA_PLAYOFFS_ACTIVE:
        for playoff_team in NBA_PLAYOFF_TEAMS:
            if playoff_team not in teams:
                # Will need to add NBA team IDs here when playoffs start
                teams[playoff_team] = {
                    'id': '',  # Add team ID when playoffs start
                    'players': []
                }

    return dict(sorted(teams.items()))

def get_status_class(status):
    status_map = {
        'Out': 'status-out',
        'Injured Reserve': 'status-ir',
        'Doubtful': 'status-doubtful',
        'Questionable': 'status-questionable',
        'Day-To-Day': 'status-dtd',
        'Probable': 'status-probable'
    }
    return status_map.get(status, 'status-unknown')

def get_indicator_class(status):
    indicator_map = {
        'Out': 'indicator-out',
        'Injured Reserve': 'indicator-ir',
        'Doubtful': 'indicator-doubtful',
        'Questionable': 'indicator-questionable',
        'Day-To-Day': 'indicator-dtd',
        'Probable': 'indicator-probable'
    }
    return indicator_map.get(status, 'indicator-out')

def generate_html(all_data):
    now = datetime.now().strftime('%B %d, %Y at %I:%M %p ET')

    # Check if MLB is in offseason
    current_month = datetime.now().month
    is_mlb_offseason = current_month in MLB_OFFSEASON_MONTHS

    # Count totals for stats (exclude MLB during offseason)
    total_injuries = sum(
        sum(len(t['players']) for t in teams.values())
        for sport, teams in all_data.items()
        if not (sport == 'MLB' and is_mlb_offseason)
    )
    leagues_count = 3 if is_mlb_offseason else 4

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Injury Report - NFL, NBA, NHL, MLB | Updated Hourly | BetLegend</title>
    <meta name="description" content="Live injury reports for NFL, NBA, NHL, and MLB. Updated hourly with player status, injury details, and expected return dates. Your go-to resource for the most up-to-date injury information.">
    <meta name="keywords" content="NFL injury report, NBA injuries, NHL injury report, MLB injuries, sports injuries today, player injury status">
    <link rel="canonical" href="https://www.betlegendpicks.com/injury-report.html">
    <meta property="og:title" content="Injury Report - NFL, NBA, NHL, MLB | BetLegend">
    <meta property="og:description" content="Live injury reports updated hourly. NFL, NBA, NHL, MLB player status and injury details.">
    <meta property="og:url" content="https://www.betlegendpicks.com/injury-report.html">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">

    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', 'G-QS8L5TDNLY');
    </script>

    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background: #0d0d0d;
            color: #e0e0e0;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        /* Navigation - Matching Index Page */
        .nav-container {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(15px);
            border-bottom: 1px solid rgba(0, 240, 255, 0.2);
            padding: 0 30px;
        }}
        .nav-inner {{
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px 0;
        }}
        .logo {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            text-decoration: none;
            color: #fff;
            letter-spacing: 2px;
            text-shadow: 0 0 20px rgba(255,255,255,0.5);
            margin-right: auto;
        }}
        .logo span {{
            color: #00f0ff;
            text-shadow: 0 0 30px #00f0ff, 0 0 60px #00f0ff;
        }}
        .nav-menu {{
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: nowrap;
        }}
        .hub-btn {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.9rem;
            font-weight: 700;
            color: #fff;
            background: linear-gradient(135deg, #ff6b00, #ff8c00);
            padding: 12px 24px;
            border-radius: 10px;
            text-decoration: none;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            box-shadow: 0 0 25px rgba(255, 107, 0, 0.5);
            transition: all 0.3s ease;
            margin-right: 15px;
        }}
        .hub-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 0 40px rgba(255, 107, 0, 0.7);
        }}
        .nav-link {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            color: #fff;
            text-decoration: none;
            padding: 12px 18px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        .nav-link:hover {{
            color: #ffd700;
            text-shadow: 0 0 15px #ffd700;
        }}
        .nav-link.active {{
            color: #00f0ff;
            text-shadow: 0 0 15px #00f0ff;
        }}
        .dropdown {{
            position: relative;
            display: inline-flex;
            align-items: center;
        }}
        .dropdown .dropbtn {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            color: #fff;
            background: none;
            border: none;
            padding: 12px 18px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        .dropdown:hover .dropbtn {{
            color: #ffd700;
            text-shadow: 0 0 15px #ffd700;
        }}
        .dropdown-content {{
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            min-width: 220px;
            background: rgba(0, 5, 20, 0.98);
            backdrop-filter: blur(20px);
            border: 2px solid rgba(0, 240, 255, 0.2);
            border-radius: 12px;
            padding: 12px;
            margin-top: 10px;
            box-shadow: 0 10px 40px rgba(0, 240, 255, 0.3);
            z-index: 99999;
        }}
        .dropdown:hover .dropdown-content {{
            display: block;
        }}
        .dropdown-content a {{
            display: block;
            padding: 12px 16px;
            color: #00f0ff;
            text-decoration: none;
            font-size: 0.9rem;
            border-radius: 8px;
            border-left: 3px solid transparent;
            transition: all 0.2s ease;
        }}
        .dropdown-content a:hover {{
            background: rgba(0, 240, 255, 0.1);
            padding-left: 22px;
            border-left-color: #00f0ff;
            color: #fff;
        }}
        .sports-records-dropdown {{
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            min-width: 420px;
            background: rgba(0, 5, 20, 0.98);
            backdrop-filter: blur(20px);
            border: 2px solid rgba(0, 240, 255, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 10px 40px rgba(0, 240, 255, 0.3);
            z-index: 99999;
        }}
        .dropdown:hover .sports-records-dropdown {{
            display: block;
        }}
        .two-columns {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        .two-columns .column h4 {{
            color: #ffd700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 215, 0, 0.3);
        }}
        .two-columns .column a {{
            display: block;
            padding: 8px 12px;
            color: #00f0ff;
            text-decoration: none;
            font-size: 0.85rem;
            border-radius: 6px;
            transition: all 0.2s ease;
        }}
        .two-columns .column a:hover {{
            background: rgba(0, 240, 255, 0.1);
            color: #fff;
        }}
        @media (max-width: 1200px) {{
            .nav-menu {{ gap: 4px; }}
            .nav-link, .dropdown .dropbtn {{ padding: 10px 12px; font-size: 0.75rem; }}
            .hub-btn {{ padding: 10px 16px; font-size: 0.8rem; }}
        }}
        @media (max-width: 900px) {{
            .nav-menu {{ display: none; }}
            .logo {{ font-size: 1.5rem; }}
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 40px 20px;
            border-bottom: 2px solid #fd5000;
            margin-bottom: 20px;
        }}
        .header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            color: #fd5000;
            text-transform: uppercase;
            letter-spacing: 3px;
            margin-bottom: 15px;
        }}
        .header .tagline {{
            color: #aaa;
            font-size: 1.1rem;
            margin-bottom: 10px;
            max-width: 700px;
            margin-left: auto;
            margin-right: auto;
        }}
        .last-updated {{
            color: #00d4ff;
            font-size: 0.95rem;
            font-weight: 600;
        }}

        /* Stats Summary */
        .stats-summary {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 25px 0;
            padding: 20px;
            background: #1a1a1a;
            border-radius: 10px;
            flex-wrap: wrap;
        }}
        .stat-box {{
            text-align: center;
        }}
        .stat-number {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #fd5000;
        }}
        .stat-label {{
            font-size: 0.8rem;
            color: #888;
            text-transform: uppercase;
        }}

        /* Sport Tabs */
        .sport-tabs {{
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }}
        .sport-tab {{
            padding: 12px 28px;
            background: #1a1a1a;
            border: 2px solid #333;
            border-radius: 6px;
            color: #888;
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
        }}
        .sport-tab:hover {{
            border-color: #fd5000;
            color: #fd5000;
        }}
        .sport-tab.active {{
            background: #fd5000;
            border-color: #fd5000;
            color: #fff;
        }}

        /* Content */
        .sport-content {{ display: none; }}
        .sport-content.active {{ display: block; }}

        /* Legend */
        .legend {{
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 25px;
            padding: 12px;
            background: #1a1a1a;
            border-radius: 6px;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}

        /* Team Card */
        .team-card {{
            background: #141414;
            border: 1px solid #2a2a2a;
            border-radius: 8px;
            margin-bottom: 15px;
            overflow: hidden;
        }}
        .team-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 15px 20px;
            background: #1a1a1a;
            border-bottom: 1px solid #2a2a2a;
        }}
        .team-logo {{
            width: 40px;
            height: 40px;
            object-fit: contain;
        }}
        .team-name {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #fff;
            flex-grow: 1;
        }}
        .team-count {{
            font-size: 0.85rem;
            color: #888;
        }}
        .team-count span {{
            color: #ff4444;
            font-weight: 600;
        }}

        /* Player Row */
        .player-list {{ padding: 0; }}
        .player-row {{
            display: grid;
            grid-template-columns: 6px 200px 70px 110px 90px 1fr;
            gap: 10px;
            padding: 14px 20px;
            border-bottom: 1px solid #222;
            align-items: center;
            transition: background 0.2s;
        }}
        .player-row:last-child {{ border-bottom: none; }}
        .player-row:hover {{ background: rgba(255,255,255,0.03); }}

        /* Color indicator bar on left */
        .status-indicator {{
            width: 6px;
            height: 100%;
            min-height: 40px;
            border-radius: 3px;
        }}
        .indicator-ir {{ background: linear-gradient(180deg, #1a1a1a, #000); }}
        .indicator-out {{ background: linear-gradient(180deg, #ff3b30, #cc2020); }}
        .indicator-doubtful {{ background: linear-gradient(180deg, #ff6b00, #cc5500); }}
        .indicator-questionable {{ background: linear-gradient(180deg, #ffcc00, #e6b800); }}
        .indicator-dtd {{ background: linear-gradient(180deg, #00a8ff, #0088cc); }}
        .indicator-probable {{ background: linear-gradient(180deg, #34c759, #28a745); }}

        .player-name {{ font-weight: 600; color: #fff; font-size: 0.95rem; }}
        .player-position {{ color: #888; font-size: 0.85rem; font-weight: 500; }}
        .player-injury {{ color: #bbb; font-size: 0.9rem; }}
        .player-duration {{ color: #888; font-size: 0.85rem; }}
        .player-comment {{
            color: #666;
            font-size: 0.8rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        /* Status Badges - Enhanced */
        .status {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            min-width: 90px;
        }}
        .status-ir {{
            background: linear-gradient(135deg, #1a1a1a, #000);
            color: #fff;
            border: 1px solid #333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }}
        .status-out {{
            background: linear-gradient(135deg, #ff3b30, #cc2020);
            color: #fff;
            box-shadow: 0 2px 8px rgba(255,59,48,0.4);
        }}
        .status-doubtful {{
            background: linear-gradient(135deg, #ff6b00, #cc5500);
            color: #fff;
            box-shadow: 0 2px 8px rgba(255,107,0,0.4);
        }}
        .status-questionable {{
            background: linear-gradient(135deg, #ffcc00, #e6b800);
            color: #000;
            box-shadow: 0 2px 8px rgba(255,204,0,0.4);
        }}
        .status-dtd {{
            background: linear-gradient(135deg, #00a8ff, #0088cc);
            color: #fff;
            box-shadow: 0 2px 8px rgba(0,168,255,0.4);
        }}
        .status-probable {{
            background: linear-gradient(135deg, #34c759, #28a745);
            color: #fff;
            box-shadow: 0 2px 8px rgba(52,199,89,0.4);
        }}
        .status-unknown {{
            background: #444;
            color: #aaa;
            border: 1px solid #555;
        }}

        /* No Injuries */
        .no-injuries {{
            padding: 20px;
            text-align: center;
            color: #34c759;
            font-size: 0.9rem;
        }}

        /* Column Headers */
        .column-headers {{
            display: grid;
            grid-template-columns: 6px 200px 70px 110px 90px 1fr;
            gap: 10px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #0a0a0a, #111);
            font-size: 0.75rem;
            font-weight: 700;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            border-radius: 6px;
            border: 1px solid #222;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px;
            color: #555;
            font-size: 0.85rem;
            border-top: 1px solid #222;
            margin-top: 40px;
        }}
        .footer a {{ color: #fd5000; text-decoration: none; }}

        /* Mobile */
        @media (max-width: 900px) {{
            .player-row {{ grid-template-columns: 4px 1fr 50px 85px; }}
            .player-duration, .player-comment {{ display: none; }}
            .column-headers {{ grid-template-columns: 4px 1fr 50px 85px; }}
            .column-headers span:nth-child(5),
            .column-headers span:nth-child(6) {{ display: none; }}
            .nav-menu {{ display: none; }}
            .status {{ min-width: 70px; font-size: 0.65rem; padding: 5px 8px; }}
            .status-indicator {{ min-height: 30px; }}
        }}
        @media (max-width: 600px) {{
            .header h1 {{ font-size: 1.8rem; }}
            .sport-tab {{ padding: 10px 18px; font-size: 0.8rem; }}
            .team-name {{ font-size: 0.95rem; }}
            .player-row {{
                grid-template-columns: 4px 1fr 40px 70px;
                padding: 10px 12px;
                font-size: 0.85rem;
            }}
            .column-headers {{ grid-template-columns: 4px 1fr 40px 70px; }}
            .status {{ min-width: 60px; font-size: 0.6rem; padding: 4px 6px; }}
            .legend {{ gap: 10px; padding: 12px; }}
            .legend-item {{ font-size: 0.7rem; }}
            .stats-summary {{ gap: 20px; }}
            .stat-number {{ font-size: 1.5rem; }}
        }}
    </style>
</head>
<body>
    <!-- Navigation - Matching Index Page -->
    <nav class="nav-container">
        <div class="nav-inner">
            <a href="index.html" class="logo">BET<span>LEGEND</span></a>

            <div class="nav-menu">
                <!-- Handicapping Hub -->
                <a href="handicapping-hub.html" class="hub-btn">Handicapping Hub</a>

                <!-- Picks & Analysis -->
                <a href="blog-page11.html" class="nav-link">Picks & Analysis</a>

                <!-- Sports & Records Dropdown -->
                <div class="dropdown">
                    <button class="dropbtn">Sports & Records ▼</button>
                    <div class="sports-records-dropdown">
                        <div class="two-columns">
                            <div class="column">
                                <h4>Sports</h4>
                                <a href="nfl.html">NFL</a>
                                <a href="mlb-page2.html">MLB</a>
                                <a href="ncaaf.html">NCAAF</a>
                                <a href="nba.html">NBA</a>
                                <a href="ncaab.html">NCAAB</a>
                                <a href="nhl.html">NHL</a>
                                <a href="soccer.html">Soccer</a>
                            </div>
                            <div class="column">
                                <h4>Records</h4>
                                <a href="records.html">DETAILED BREAKDOWN</a>
                                <a href="mlb-records.html">MLB</a>
                                <a href="nfl-records.html">NFL</a>
                                <a href="ncaaf-records.html">NCAAF</a>
                                <a href="ncaab-records.html">NCAAB</a>
                                <a href="nhl-records.html">NHL</a>
                                <a href="nba-records.html">NBA</a>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Resources Dropdown -->
                <div class="dropdown">
                    <button class="dropbtn">Resources ▼</button>
                    <div class="dropdown-content">
                        <a href="proofofpicks.html">Proof of Picks</a>
                        <a href="live-odds.html">Live Odds</a>
                        <a href="bankroll.html">Bankroll</a>
                        <a href="kelly-criterion.html">Kelly Criterion</a>
                        <a href="betting-calculators.html">Betting Calculators</a>
                        <a href="betting-glossary.html">Betting Glossary</a>
                        <a href="betting-101.html">Betting 101</a>
                        <a href="contact.html">Contact Us</a>
                    </div>
                </div>

                <!-- News -->
                <a href="news-page3.html" class="nav-link">News</a>

                <!-- Injury Report -->
                <a href="injury-report.html" class="nav-link active">Injury Report</a>

                <!-- Game of the Day Dropdown -->
                <div class="dropdown">
                    <button class="dropbtn">Game of the Day ▼</button>
                    <div class="dropdown-content">
                        <a href="featured-game-of-the-day-page44.html">Game of the Day</a>
                        <a href="moneyline-parlay-of-the-day.html">ML Parlay of the Day</a>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <div class="container" style="padding-top: 80px;">
        <header class="header">
            <h1>Injury Report</h1>
            <p class="tagline">Your go-to resource for the most up-to-date injury information across all major sports. Updated hourly with real-time data.</p>
            <p class="last-updated" id="last-updated-time">Last Updated: Loading...</p>
        </header>

        <div class="stats-summary">
            <div class="stat-box">
                <div class="stat-number">{total_injuries}</div>
                <div class="stat-label">Total Players Injured</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{leagues_count}</div>
                <div class="stat-label">Leagues Tracked</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">Hourly</div>
                <div class="stat-label">Update Frequency</div>
            </div>
        </div>

        <div class="sport-tabs">
            <button class="sport-tab active" onclick="showSport('nba')">NBA</button>
            <button class="sport-tab" onclick="showSport('nhl')">NHL</button>
            <button class="sport-tab" onclick="showSport('nfl')">NFL</button>
            <button class="sport-tab" onclick="showSport('mlb')">MLB</button>
        </div>

        <div class="legend">
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #ff3b30, #cc2020);"></div> Out</div>
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #1a1a1a, #000); border:1px solid #333;"></div> IR</div>
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #ff6b00, #cc5500);"></div> Doubtful</div>
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #ffcc00, #e6b800);"></div> Questionable</div>
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #00a8ff, #0088cc);"></div> Day-to-Day</div>
            <div class="legend-item"><div class="legend-dot" style="background:linear-gradient(180deg, #34c759, #28a745);"></div> Probable</div>
        </div>
'''

    for sport in ['NBA', 'NHL', 'NFL', 'MLB']:
        teams = all_data.get(sport, {})
        sport_lower = sport.lower()
        is_active = 'active' if sport == 'NBA' else ''

        # Add playoff note for NFL and NBA (when applicable)
        playoff_note = ''
        if sport == 'NFL':
            playoff_note = '<p style="text-align:center;color:#00d4ff;font-size:0.9rem;margin-bottom:15px;font-weight:600;">NFL Playoff Teams Only - Conference Championships (Jan 25-26, 2026)</p>'
        elif sport == 'NBA' and NBA_PLAYOFFS_ACTIVE:
            playoff_note = '<p style="text-align:center;color:#00d4ff;font-size:0.9rem;margin-bottom:15px;font-weight:600;">NBA Playoff Teams Only</p>'

        # Check if MLB is in offseason
        current_month = datetime.now().month
        is_mlb_offseason = sport == 'MLB' and current_month in MLB_OFFSEASON_MONTHS

        if is_mlb_offseason:
            html += f'''
        <div id="{sport_lower}" class="sport-content {is_active}">
            <div style="text-align:center;padding:60px 20px;background:#1a1a1a;border-radius:10px;margin:20px 0;">
                <p style="color:#ffd700;font-size:1.3rem;font-weight:700;margin-bottom:15px;">MLB OFFSEASON</p>
                <p style="color:#888;font-size:1rem;">The MLB season runs from late March through October.</p>
                <p style="color:#888;font-size:1rem;margin-top:10px;">Injury reports will resume when the 2026 season begins.</p>
            </div>
        </div>
'''
            continue

        html += f'''
        <div id="{sport_lower}" class="sport-content {is_active}">
            {playoff_note}
            <div class="column-headers">
                <span></span>
                <span>Player</span>
                <span>Position</span>
                <span>Status</span>
                <span>Duration</span>
                <span>Injury Details</span>
            </div>
'''
        for team_name, team_data in teams.items():
            players = team_data['players']
            team_id = team_data['id']
            logo_url = get_team_logo(sport, team_id)
            injured_count = len(players)

            html += f'''
            <div class="team-card">
                <div class="team-header">
                    <img src="{logo_url}" alt="{team_name}" class="team-logo" onerror="this.style.display='none'">
                    <span class="team-name">{team_name}</span>
                    <span class="team-count"><span>{injured_count}</span> injured</span>
                </div>
'''
            if players:
                html += '                <div class="player-list">\n'
                for p in players:
                    status_class = get_status_class(p['status'])
                    indicator_class = get_indicator_class(p['status'])
                    comment = p['comment'][:80] + '...' if len(p['comment']) > 80 else p['comment']
                    html += f'''                    <div class="player-row">
                        <div class="status-indicator {indicator_class}"></div>
                        <div class="player-name">{p['name']}</div>
                        <div class="player-position">{p['position'] or '-'}</div>
                        <div><span class="status {status_class}">{p['status'].replace('Injured Reserve', 'IR').replace('Day-To-Day', 'DTD')}</span></div>
                        <div class="player-duration">{p['days_display']}</div>
                        <div class="player-comment" title="{p['comment']}">{p['injury']} - {comment}</div>
                    </div>
'''
                html += '                </div>\n'
            else:
                html += '                <div class="no-injuries">No injuries reported</div>\n'
            html += '            </div>\n'
        html += '        </div>\n'

    html += '''
        <footer class="footer">
            <p>Data sourced from ESPN. Updated hourly via automated system.</p>
            <p style="margin-top:10px;"><a href="index.html">Back to BetLegend Home</a> | <a href="handicapping-hub.html">Handicapping Hub</a></p>
        </footer>
    </div>

    <script>
        function showSport(sport) {
            document.querySelectorAll('.sport-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.sport-tab').forEach(el => el.classList.remove('active'));
            document.getElementById(sport).classList.add('active');
            event.target.classList.add('active');
        }

        // Update timestamp to current Eastern Time
        function updateTimestamp() {
            const now = new Date();
            const options = {
                timeZone: 'America/New_York',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                hour12: true
            };
            const formatter = new Intl.DateTimeFormat('en-US', options);
            const parts = formatter.formatToParts(now);

            let month = '', day = '', year = '', hour = '', minute = '', dayPeriod = '';
            parts.forEach(part => {
                if (part.type === 'month') month = part.value;
                if (part.type === 'day') day = part.value;
                if (part.type === 'year') year = part.value;
                if (part.type === 'hour') hour = part.value;
                if (part.type === 'minute') minute = part.value;
                if (part.type === 'dayPeriod') dayPeriod = part.value.toUpperCase();
            });

            const timeStr = `Last Updated: ${month} ${day}, ${year} at ${hour}:${minute} ${dayPeriod} ET`;
            document.getElementById('last-updated-time').textContent = timeStr;
        }

        // Update on page load
        updateTimestamp();

        // Update every minute
        setInterval(updateTimestamp, 60000);
    </script>
</body>
</html>
'''
    return html

def main():
    print("=" * 50)
    print("BetLegend Injury Report Generator")
    print("=" * 50)

    current_month = datetime.now().month
    is_mlb_offseason = current_month in MLB_OFFSEASON_MONTHS

    all_data = {}
    for sport, url in ENDPOINTS.items():
        # Skip fetching MLB during offseason
        if sport == 'MLB' and is_mlb_offseason:
            print(f"Skipping {sport} (offseason)...")
            all_data[sport] = {}
            continue

        print(f"Fetching {sport}...")
        teams_data = fetch_injuries(sport, url)
        teams = parse_all_injuries(sport, teams_data)
        all_data[sport] = teams
        total_injured = sum(len(t['players']) for t in teams.values())
        print(f"  {len(teams)} teams, {total_injured} injured players")

    print("\nGenerating HTML...")
    html = generate_html(all_data)

    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    output_path = os.path.join(repo_root, 'injury-report.html')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    main()
