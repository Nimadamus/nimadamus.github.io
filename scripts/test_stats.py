#!/usr/bin/env python3
"""Test script to verify ESPN stat extraction accuracy"""
import requests
import json

def fetch_team_stats(sport_path, team_id):
    """Fetch and print ALL available stats"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_id}/statistics"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            stats = {}
            # Parse all stats
            for cat in data.get('results', {}).get('stats', {}).get('categories', []):
                cat_name = cat.get('name', 'Unknown')
                print(f"\n=== {cat_name.upper()} ===")
                for stat in cat.get('stats', []):
                    name = stat.get('name', '')
                    value = stat.get('displayValue', stat.get('value', '-'))
                    desc = stat.get('description', '')
                    print(f"  {name}: {value}")
                    stats[name] = value
            return stats
    except Exception as e:
        print(f"Error: {e}")
    return {}

# Test NBA - Lakers (team 13)
print("\n" + "="*60)
print("NBA - Los Angeles Lakers")
print("="*60)
nba_stats = fetch_team_stats('basketball/nba', '13')

# Test NFL - Chiefs (team 12)
print("\n" + "="*60)
print("NFL - Kansas City Chiefs")
print("="*60)
nfl_stats = fetch_team_stats('football/nfl', '12')

# Test NHL - Canadiens (team 10)
print("\n" + "="*60)
print("NHL - Montreal Canadiens")
print("="*60)
nhl_stats = fetch_team_stats('hockey/nhl', '10')

print("\n" + "="*60)
print("SUMMARY - Key stats found:")
print("="*60)
print(f"\nNBA key stats:")
print(f"  Points/game: {nba_stats.get('avgPoints', 'NOT FOUND')}")
print(f"  FG%: {nba_stats.get('fieldGoalPct', 'NOT FOUND')}")
print(f"  3P%: {nba_stats.get('threePointPct', nba_stats.get('threePointFieldGoalPct', 'NOT FOUND'))}")
print(f"  Rebounds: {nba_stats.get('avgRebounds', 'NOT FOUND')}")
print(f"  Assists: {nba_stats.get('avgAssists', 'NOT FOUND')}")
print(f"  Steals: {nba_stats.get('avgSteals', 'NOT FOUND')}")
print(f"  Blocks: {nba_stats.get('avgBlocks', 'NOT FOUND')}")
print(f"  Turnovers: {nba_stats.get('avgTurnovers', 'NOT FOUND')}")
print(f"  A/TO ratio: {nba_stats.get('assistTurnoverRatio', 'NOT FOUND')}")

print(f"\nNFL key stats:")
print(f"  PPG: {nfl_stats.get('totalPointsPerGame', 'NOT FOUND')}")
print(f"  Total YPG: {nfl_stats.get('yardsPerGame', 'NOT FOUND')}")
print(f"  Pass YPG: {nfl_stats.get('netPassingYardsPerGame', 'NOT FOUND')}")
print(f"  Rush YPG: {nfl_stats.get('rushingYardsPerGame', 'NOT FOUND')}")
print(f"  Comp%: {nfl_stats.get('completionPct', 'NOT FOUND')}")
print(f"  QBR: {nfl_stats.get('QBRating', 'NOT FOUND')}")
print(f"  3rd Down%: {nfl_stats.get('thirdDownConvPct', 'NOT FOUND')}")
print(f"  4th Down%: {nfl_stats.get('fourthDownConvPct', 'NOT FOUND')}")
print(f"  RZ TD%: {nfl_stats.get('redzoneTouchdownPct', 'NOT FOUND')}")
print(f"  TO Diff: {nfl_stats.get('turnOverDifferential', 'NOT FOUND')}")
print(f"  Sacks: {nfl_stats.get('sacks', 'NOT FOUND')}")
print(f"  INTs: {nfl_stats.get('interceptions', 'NOT FOUND')}")
print(f"  TFL: {nfl_stats.get('tacklesForLoss', 'NOT FOUND')}")

print(f"\nNHL key stats:")
print(f"  Goals For: {nhl_stats.get('goals', 'NOT FOUND')}")
print(f"  Goals Against: {nhl_stats.get('goalsAgainst', nhl_stats.get('avgGoalsAgainst', 'NOT FOUND'))}")
print(f"  Shots: {nhl_stats.get('shotsTotal', 'NOT FOUND')}")
print(f"  Save%: {nhl_stats.get('savePct', 'NOT FOUND')}")
print(f"  PP Goals: {nhl_stats.get('powerPlayGoals', 'NOT FOUND')}")
print(f"  Shooting%: {nhl_stats.get('shootingPct', 'NOT FOUND')}")
print(f"  FO%: {nhl_stats.get('faceoffPercent', 'NOT FOUND')}")
print(f"  PIM: {nhl_stats.get('penaltyMinutes', 'NOT FOUND')}")
