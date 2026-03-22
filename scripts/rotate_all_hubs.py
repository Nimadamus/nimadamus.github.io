#!/usr/bin/env python3
"""
rotate_all_hubs.py - Run rotate_hub_content.py for ALL active sports.

Usage:
    python rotate_all_hubs.py

This is a convenience script for daily automation. It iterates through
all active sports and archives their hub content before the daily refresh.

Sports that don't have a hub page yet or only have placeholder content
are handled gracefully (skipped with a message).
"""

import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROTATE_SCRIPT = os.path.join(SCRIPT_DIR, 'rotate_hub_content.py')

# All sports to rotate - add/remove as needed
ACTIVE_SPORTS = ['nba', 'nhl', 'mlb', 'ncaab', 'soccer']


def main():
    print('=' * 60)
    print('  ROTATING ALL HUB CONTENT')
    print('=' * 60)
    print()

    results = {}

    for sport in ACTIVE_SPORTS:
        print(f'--- {sport.upper()} ---')
        try:
            result = subprocess.run(
                [sys.executable, ROTATE_SCRIPT, sport],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(SCRIPT_DIR)
            )
            print(result.stdout.strip() if result.stdout.strip() else '  (no output)')
            if result.stderr.strip():
                print(f'  STDERR: {result.stderr.strip()}')

            if result.returncode == 0:
                results[sport] = 'OK'
            else:
                results[sport] = 'SKIPPED/ERROR'
        except Exception as e:
            print(f'  ERROR: {e}')
            results[sport] = 'ERROR'
        print()

    # Summary
    print('=' * 60)
    print('  ROTATION SUMMARY')
    print('=' * 60)
    for sport, status in results.items():
        icon = '[OK]' if status == 'OK' else '[--]'
        print(f'  {icon} {sport.upper()}: {status}')
    print('=' * 60)

    # Return non-zero if any sport had an actual error (not just skipped)
    errors = [s for s, st in results.items() if st == 'ERROR']
    if errors:
        print(f'\nERRORS in: {", ".join(errors)}')
        sys.exit(1)


if __name__ == '__main__':
    main()
