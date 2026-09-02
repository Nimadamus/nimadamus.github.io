#!/usr/bin/env python3
"""Rename sport preview pages to unique, storyline-driven URLs.
For each rename:
1. git mv the file
2. Update canonical/og:url inside the new file
3. Update calendar JS files
4. Update cross-references in other HTML files
5. Create a redirect stub at the old URL
"""
import os
import re
import subprocess
import sys

REPO = r"C:\Users\Nima\nimadamus.github.io"

RENAMES = {
    # NBA
    "nba-game-previews-analysis-february-21-2026.html": "kings-fox-returns-to-sacramento-nba-preview-february-21-2026.html",
    "nba-game-previews-analysis-february-24-2026.html": "knicks-cavaliers-eastern-conference-showdown-nba-february-24-2026.html",
    "nba-game-previews-analysis-february-25-2026.html": "cavaliers-bucks-battle-for-east-supremacy-nba-february-25-2026.html",
    "nba-game-previews-analysis-february-26-2026.html": "rockets-magic-western-playoff-race-nba-february-26-2026.html",
    "nba-game-previews-analysis-february-27-2026.html": "nuggets-thunder-western-conference-clash-nba-february-27-2026.html",
    "nba-game-previews-analysis-march-1-2026.html": "timberwolves-nuggets-mile-high-rivalry-nba-march-1-2026.html",
    "nba-game-previews-analysis-march-2-2026.html": "celtics-bucks-playoff-positioning-nba-march-2-2026.html",
    "nba-game-previews-analysis-march-3-2026.html": "pistons-cavaliers-central-division-nba-march-3-2026.html",
    "nba-game-previews-analysis-march-4-2026.html": "thunder-knicks-marquee-matchup-nba-march-4-2026.html",
    "nba-game-previews-analysis-march-5-2026.html": "lakers-nuggets-western-conference-rivalry-nba-march-5-2026.html",
    "nba-game-previews-analysis-march-6-2026.html": "knicks-seek-revenge-in-denver-tatum-returns-nba-march-6-2026.html",
    # NHL
    "nhl-game-previews-analysis-february-25-2026.html": "maple-leafs-lightning-atlantic-division-nhl-february-25-2026.html",
    "nhl-game-previews-analysis-february-26-2026.html": "wild-avalanche-central-division-battle-nhl-february-26-2026.html",
    "nhl-game-previews-analysis-february-27-2026.html": "golden-knights-marner-visits-capitals-nhl-february-27-2026.html",
    "nhl-game-previews-analysis-march-1-2026.html": "golden-knights-penguins-cross-conference-nhl-march-1-2026.html",
    "nhl-game-previews-analysis-march-2-2026.html": "stars-canucks-pacific-division-nhl-march-2-2026.html",
    "nhl-game-previews-analysis-march-3-2026.html": "panthers-devils-defending-champs-visit-jersey-nhl-march-3-2026.html",
    "nhl-game-previews-analysis-march-4-2026.html": "hurricanes-canucks-cross-conference-showdown-nhl-march-4-2026.html",
    "nhl-game-previews-analysis-march-5-2026.html": "maple-leafs-rangers-original-six-rivalry-nhl-march-5-2026.html",
    "nhl-game-previews-analysis-march-6-2026.html": "nhl-trade-deadline-day-avalanche-stars-showdown-march-6-2026.html",
    # NCAAB
    "college-basketball-game-previews-february-21-2026.html": "duke-michigan-number-one-showdown-ncaab-february-21-2026.html",
    "college-basketball-game-previews-february-24-2026.html": "duke-visits-notre-dame-michigan-hosts-minnesota-ncaab-february-24-2026.html",
    "college-basketball-game-previews-february-25-2026.html": "st-johns-uconn-big-east-battle-ncaab-february-25-2026.html",
    "college-basketball-game-previews-february-26-2026.html": "michigan-state-purdue-big-ten-showdown-ncaab-february-26-2026.html",
    "college-basketball-game-previews-february-27-2026.html": "michigan-illinois-big-ten-rivalry-ncaab-february-27-2026.html",
    "college-basketball-game-previews-march-1-2026.html": "purdue-ohio-state-michigan-state-indiana-big-ten-ncaab-march-1-2026.html",
    "college-basketball-game-previews-march-2-2026.html": "duke-nc-state-iowa-state-arizona-marquee-ncaab-march-2-2026.html",
    "college-basketball-game-previews-march-3-2026.html": "north-carolina-hosts-clemson-alabama-georgia-ncaab-march-3-2026.html",
    "college-basketball-game-previews-march-4-2026.html": "baylor-houston-big-12-purdue-northwestern-ncaab-march-4-2026.html",
    "college-basketball-game-previews-march-5-2026.html": "michigan-iowa-big-ten-march-madness-push-ncaab-march-5-2026.html",
    "college-basketball-game-previews-march-6-2026.html": "miami-ohio-perfect-season-on-the-line-ncaab-march-6-2026.html",
    # Soccer
    "soccer-game-previews-analysis-february-24-2026.html": "champions-league-atletico-inter-newcastle-soccer-february-24-2026.html",
    "soccer-game-previews-analysis-february-25-2026.html": "real-madrid-benfica-psg-monaco-ucl-soccer-february-25-2026.html",
    "soccer-game-previews-analysis-february-26-2026.html": "europa-league-forest-fenerbahce-celtic-soccer-february-26-2026.html",
    "soccer-game-previews-analysis-february-27-2026.html": "premier-league-wolves-villa-european-leagues-soccer-february-27-2026.html",
    "soccer-game-previews-analysis-march-1-2026.html": "arsenal-chelsea-london-derby-premier-league-soccer-march-1-2026.html",
    "soccer-game-previews-analysis-march-2-2026.html": "real-madrid-getafe-serie-a-la-liga-soccer-march-2-2026.html",
    "soccer-game-previews-analysis-march-3-2026.html": "wolves-liverpool-premier-league-title-race-soccer-march-3-2026.html",
    "soccer-game-previews-analysis-march-4-2026.html": "brighton-arsenal-man-city-forest-premier-league-soccer-march-4-2026.html",
}

REDIRECT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url={new_url}">
<link rel="canonical" href="https://www.betlegendpicks.com/{new_url}">
<title>Redirecting...</title>
</head>
<body>
<p>This page has moved. <a href="{new_url}">Click here</a> if not redirected.</p>
</body>
</html>
"""

def main():
    os.chdir(REPO)

    renamed = 0
    errors = 0

    for old_name, new_name in RENAMES.items():
        old_path = os.path.join(REPO, old_name)
        new_path = os.path.join(REPO, new_name)

        if not os.path.exists(old_path):
            print(f"  SKIP (not found): {old_name}")
            continue

        # 1. Rename the file using git mv
        result = subprocess.run(["git", "mv", old_name, new_name],
                              capture_output=True, text=True, cwd=REPO)
        if result.returncode != 0:
            print(f"  ERROR git mv: {old_name} -> {new_name}: {result.stderr}")
            errors += 1
            continue

        # 2. Update canonical and og:url inside the renamed file
        with open(new_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update canonical
        content = content.replace(
            f'href="https://www.betlegendpicks.com/{old_name}"',
            f'href="https://www.betlegendpicks.com/{new_name}"'
        )
        # Update og:url
        content = content.replace(
            f'content="https://www.betlegendpicks.com/{old_name}"',
            f'content="https://www.betlegendpicks.com/{new_name}"'
        )

        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 3. Create redirect stub at old URL
        with open(old_path, 'w', encoding='utf-8') as f:
            f.write(REDIRECT_TEMPLATE.format(new_url=new_name))

        renamed += 1
        print(f"  OK: {old_name} -> {new_name}")

    # 4. Update calendar JS files
    calendar_files = [
        os.path.join(REPO, "scripts", "nba-calendar.js"),
        os.path.join(REPO, "scripts", "nhl-calendar.js"),
        os.path.join(REPO, "scripts", "ncaab-calendar.js"),
        os.path.join(REPO, "scripts", "soccer-calendar.js"),
    ]

    for cal_file in calendar_files:
        if not os.path.exists(cal_file):
            continue
        with open(cal_file, 'r', encoding='utf-8') as f:
            content = f.read()

        for old_name, new_name in RENAMES.items():
            content = content.replace(old_name, new_name)

        with open(cal_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  CALENDAR UPDATED: {os.path.basename(cal_file)}")

    # 5. Update cross-references in ALL HTML files (but NOT the redirect stubs we just created)
    html_files = []
    for f in os.listdir(REPO):
        if f.endswith('.html') and f not in RENAMES:  # Skip old names (now redirect stubs)
            html_files.append(f)

    # Also check new files (the renamed ones)
    for new_name in RENAMES.values():
        if os.path.exists(os.path.join(REPO, new_name)):
            html_files.append(new_name)

    # Deduplicate
    html_files = list(set(html_files))

    updated_files = set()
    for html_file in html_files:
        filepath = os.path.join(REPO, html_file)
        if not os.path.exists(filepath):
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content
        for old_name, new_name in RENAMES.items():
            # Only replace href references, not in redirect stubs
            content = content.replace(f'href="{old_name}"', f'href="{new_name}"')
            content = content.replace(f"href='{old_name}'", f"href='{new_name}'")

        if content != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_files.add(html_file)

    if updated_files:
        print(f"\n  CROSS-REFERENCES UPDATED in {len(updated_files)} files:")
        for f in sorted(updated_files):
            print(f"    {f}")

    print(f"\n{'='*60}")
    print(f"RENAMED: {renamed} files")
    print(f"REDIRECT STUBS: {renamed} created")
    print(f"ERRORS: {errors}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
