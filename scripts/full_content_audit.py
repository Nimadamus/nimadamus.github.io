#!/usr/bin/env python3
"""
FULL CONTENT AUDIT SCRIPT
Scans ALL HTML files for known outdated player-team associations and other errors.
Created: January 17, 2026
"""

import os
import re
from datetime import datetime
from pathlib import Path

# Repository path
REPO_PATH = r'C:\Users\Nima\nimadamus.github.io'

# KNOWN OUTDATED PLAYER-TEAM ASSOCIATIONS
# Format: (player_name, wrong_team_keywords, current_status, date_changed)
OUTDATED_PLAYERS = [
    # NBA - Warriors trades/changes (2025)
    ("Andrew Wiggins", ["Warriors", "Golden State", "GSW"], "Traded to Heat Feb 2025", "2025-02-06"),
    ("Jonathan Kuminga", ["Warriors.*starting", "Warriors.*lineup", "Kuminga.*playing"], "Benched since Nov 2025, demanding trade", "2025-11-12"),

    # NBA - Major 2025 Trades
    ("Kevin Durant", ["Suns", "Phoenix"], "Traded to Rockets July 2025", "2025-07-01"),
    ("Brandon Ingram", ["Pelicans", "New Orleans"], "Traded to Raptors Feb 2025", "2025-02-01"),
    ("Jimmy Butler", ["Heat", "Miami"], "Traded to Warriors Feb 2025", "2025-02-06"),

    # NBA - Injuries (2025)
    ("Jayson Tatum", ["healthy", "playing well"], "Achilles injury since late 2025", "2025-12-01"),
    ("Fred VanVleet", ["Rockets.*starting", "VanVleet.*playing"], "Torn ACL, out for season", "2025-11-01"),
    ("Tyrese Haliburton", ["healthy", "playing"], "Achilles concerns from 2025 Finals", "2025-06-01"),

    # NFL - 2025 Offseason Moves
    ("Leonard Floyd", ["49ers", "San Francisco"], "Released, signed with Falcons Mar 2025", "2025-03-01"),
    ("Deebo Samuel", ["49ers", "San Francisco"], "Traded to Commanders Mar 2025", "2025-03-01"),
    ("Aaron Rodgers", ["Jets", "New York Jets"], "Signed with Steelers Mar 2025", "2025-03-01"),
    ("Davante Adams", ["Raiders", "Las Vegas"], "Traded to Rams Mar 2025", "2025-03-01"),
    ("Justin Fields", ["Bears", "Chicago"], "Signed with Jets Mar 2025", "2025-03-01"),
    ("Russell Wilson", ["Steelers", "Pittsburgh"], "Left Steelers Mar 2025", "2025-03-01"),
    ("Micah Parsons", ["Cowboys", "Dallas"], "Traded to Packers 2025", "2025-03-01"),

    # NFL - Major 2025 Injuries
    ("Nick Bosa", ["49ers.*healthy", "Bosa.*playing"], "Torn ACL Week 3, out for season", "2025-09-20"),
    ("Fred Warner", ["49ers.*healthy", "Warner.*playing"], "Fractured ankle, IR", "2025-10-01"),
    ("Brandon Aiyuk", ["49ers.*active", "Aiyuk.*playing"], "ACL tear 2024, Reserve/Left Team", "2024-12-01"),

    # NHL - 2025 Trades
    ("Mitch Marner", ["Maple Leafs", "Toronto"], "Traded to Golden Knights July 2025", "2025-07-01"),

    # MLB - 2025-26 Offseason (CRITICAL)
    ("Alex Bregman", ["Astros", "Houston", "unsigned", "free agent"], "Signed with Cubs Jan 14, 2026", "2026-01-14"),
    ("Kyle Tucker", ["Astros", "Houston"], "Signed with Dodgers Jan 15, 2026", "2026-01-15"),
    ("Pete Alonso", ["Mets", "New York Mets", "unsigned"], "Signed with Orioles Dec 2025", "2025-12-22"),
    ("Dylan Cease", ["Padres", "San Diego"], "Signed with Blue Jays Dec 2025", "2025-12-18"),

    # CFB - Coaching Changes
    ("Curt Cignetti", ["James Madison", "JMU"], "Now at Indiana since 2024", "2024-01-01"),
    ("Lane Kiffin", ["Ole Miss", "Oxford"], "Left for LSU, Pete Golding is Ole Miss HC", "2024-12-01"),
]

# PATTERNS THAT INDICATE OUTDATED CONTENT
OUTDATED_PATTERNS = [
    # Championship references that might be wrong
    (r"2024\s+(World Series|Super Bowl|NBA Finals|Stanley Cup)", "Championship year might be outdated - check if should be 2025"),

    # "Unsigned" claims for players who have signed
    (r"(Bregman|Tucker|Alonso|Cease).*unsigned", "Player has signed - check CURRENT_FACTS.md"),
    (r"(Bregman|Tucker|Alonso|Cease).*free agent", "Player has signed - check CURRENT_FACTS.md"),

    # Generic placeholder patterns
    (r"coming soon", "Placeholder text found"),
    (r"TBD|TBA|N/A", "Placeholder value found"),
]

def scan_file(filepath):
    """Scan a single file for errors."""
    errors = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return [f"Could not read file: {e}"]

    # Check for outdated player-team associations
    for player, wrong_keywords, status, date_changed in OUTDATED_PLAYERS:
        # Check if player is mentioned
        if player.lower() in content.lower():
            # Check if mentioned with wrong team context
            for keyword in wrong_keywords:
                pattern = rf'{player}.*{keyword}|{keyword}.*{player}'
                matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Get context around the match
                    for match in matches[:3]:  # Limit to first 3 matches
                        # Find the sentence containing the match
                        idx = content.lower().find(match.lower())
                        start = max(0, idx - 50)
                        end = min(len(content), idx + len(match) + 50)
                        context = content[start:end].replace('\n', ' ')
                        errors.append({
                            'type': 'OUTDATED_PLAYER',
                            'player': player,
                            'status': status,
                            'date_changed': date_changed,
                            'context': f"...{context}..."
                        })
                    break  # Only report once per player per file

    # Check for outdated patterns
    for pattern, message in OUTDATED_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            errors.append({
                'type': 'OUTDATED_PATTERN',
                'pattern': pattern,
                'message': message,
                'matches': matches[:5]  # Limit to first 5
            })

    return errors

def run_full_audit():
    """Run audit on all HTML files in the repository."""
    print("=" * 80)
    print("FULL CONTENT AUDIT - BetLegend Repository")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    all_errors = {}
    total_files = 0
    files_with_errors = 0
    total_errors = 0

    # Walk through all HTML files
    for root, dirs, files in os.walk(REPO_PATH):
        # Skip .git directory
        dirs[:] = [d for d in dirs if d != '.git']

        for filename in files:
            if filename.endswith('.html'):
                filepath = os.path.join(root, filename)
                relative_path = os.path.relpath(filepath, REPO_PATH)
                total_files += 1

                errors = scan_file(filepath)

                if errors:
                    all_errors[relative_path] = errors
                    files_with_errors += 1
                    total_errors += len(errors)

    # Print results
    print(f"Scanned {total_files} HTML files")
    print(f"Found {total_errors} potential errors in {files_with_errors} files")
    print()

    if all_errors:
        print("=" * 80)
        print("ERRORS FOUND:")
        print("=" * 80)

        for filepath, errors in sorted(all_errors.items()):
            print(f"\n{'='*60}")
            print(f"FILE: {filepath}")
            print(f"{'='*60}")

            for error in errors:
                if error['type'] == 'OUTDATED_PLAYER':
                    print(f"  [OUTDATED PLAYER] {error['player']}")
                    print(f"    Status: {error['status']}")
                    print(f"    Changed: {error['date_changed']}")
                    print(f"    Context: {error['context'][:100]}...")
                elif error['type'] == 'OUTDATED_PATTERN':
                    print(f"  [PATTERN] {error['message']}")
                    print(f"    Matches: {error['matches']}")
                else:
                    print(f"  {error}")
                print()

    # Save report to file
    report_path = os.path.join(REPO_PATH, 'AUDIT_REPORT.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("FULL CONTENT AUDIT REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total files scanned: {total_files}\n")
        f.write(f"Files with errors: {files_with_errors}\n")
        f.write(f"Total errors found: {total_errors}\n\n")

        for filepath, errors in sorted(all_errors.items()):
            f.write(f"\n{'='*60}\n")
            f.write(f"FILE: {filepath}\n")
            f.write(f"{'='*60}\n")

            for error in errors:
                if error['type'] == 'OUTDATED_PLAYER':
                    f.write(f"  [OUTDATED PLAYER] {error['player']}\n")
                    f.write(f"    Status: {error['status']}\n")
                    f.write(f"    Changed: {error['date_changed']}\n")
                    f.write(f"    Context: {error['context'][:200]}...\n\n")
                elif error['type'] == 'OUTDATED_PATTERN':
                    f.write(f"  [PATTERN] {error['message']}\n")
                    f.write(f"    Matches: {error['matches']}\n\n")

    print(f"\nFull report saved to: {report_path}")

    return all_errors, total_errors

if __name__ == "__main__":
    errors, count = run_full_audit()
    if count > 0:
        print(f"\n{'!'*80}")
        print(f"AUDIT COMPLETE: {count} ERRORS REQUIRE ATTENTION")
        print(f"{'!'*80}")
    else:
        print("\nAUDIT COMPLETE: No errors found")
