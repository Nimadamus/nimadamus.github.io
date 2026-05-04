#!/usr/bin/env python3
"""
Delete the 1372 betlegendpicks files we accidentally FTP-uploaded to bestmlbhandicapper.com root.
The list is exactly the keys + values of date_strip_rename_map.json (old dated names + new dateless names),
plus the 5 May-4 SLATE files that were uploaded separately. Only files in that list are touched -
nothing else on bestmlbhandicapper is at risk.
"""
import os, json, ftplib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAP = os.path.join(ROOT, 'scripts', 'date_strip_rename_map.json')

with open(MAP, 'r', encoding='utf-8') as f:
    rename_map = json.load(f)

targets = set()
for old, new in rename_map.items():
    targets.add(old)
    targets.add(new)
# Also include the 5 May-4 files (uploaded outside the bulk script)
for old in [
    '76ers-vs-knicks-eastern-semis-game-1-analysis-stats-preview-may-4-2026.html',
    '76ers-knicks-spurs-wolves-east-west-semis-open-nba-may-4-2026.html',
    'flyers-hurricanes-game-2-ducks-knights-game-1-nhl-may-4-2026.html',
    'yamamoto-gordon-twelve-game-monday-mlb-may-4-2026.html',
    'everton-city-roma-fiorentina-monday-soccer-may-4-2026.html',
]:
    targets.add(old)

print(f'  Target files to remove from bestmlbhandicapper /: {len(targets)}')

ftp = ftplib.FTP('208.109.70.186', timeout=60)
ftp.login('master@bestmlbhandicapper.com', 'Warriors2025!')
ftp.cwd('/')

# Get the actual file listing on FTP, only delete intersection (safety)
existing = []
ftp.retrlines('NLST', existing.append)
existing_set = set(existing)
to_delete = sorted(targets & existing_set)
print(f'  Of those, present on bestmlbhandicapper: {len(to_delete)}')

deleted = 0
failed = []
for fn in to_delete:
    try:
        ftp.delete(fn)
        deleted += 1
        if deleted % 100 == 0:
            print(f'    {deleted}/{len(to_delete)}')
    except Exception as e:
        failed.append((fn, str(e)))

ftp.quit()
print(f'\n  Deleted: {deleted}/{len(to_delete)}')
if failed:
    print(f'  Failed: {len(failed)}')
    for f in failed[:10]:
        print(f'    {f}')
