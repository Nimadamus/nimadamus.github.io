#!/usr/bin/env python3
"""
Calendar cache-bust stamper (Nima, June 24 2026).

THE recurring-calendar root cause this fixes:
A fix to a calendar ENGINE (scripts/*-calendar.js, featured-games-calendar.js)
ships to the server, but every page references that engine with a FROZEN
`?v=...` query string. Returning visitors' browsers keep the OLD cached engine
because the cache key never changed - so the fix is invisible and the calendar
"breaks again" even though the deployed file is correct.

The permanent fix: derive `?v=` from a content hash of the engine file. When an
engine changes, its hash changes, and EVERY page that loads it is re-stamped in
the same run -> browsers refetch automatically. When nothing changed, hashes are
identical and no page churns. Self-healing, no manual version bumping ever again.

Run order: AFTER sync_calendars.py / sync_featured_games_calendar.py (which write
the engine files), so the hash reflects the freshly generated engine.
Idempotent. Wired into pre-commit + the daily auto-fix-content.yml CI job.
"""
import os
import re
import sys
import glob
import hashlib

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# engine basename (no .js) -> path on disk
ENGINES = {
    'featured-games-calendar': os.path.join(REPO, 'scripts', 'featured-games-calendar.js'),
    'mlb-calendar':   os.path.join(REPO, 'scripts', 'mlb-calendar.js'),
    'nba-calendar':   os.path.join(REPO, 'scripts', 'nba-calendar.js'),
    'nhl-calendar':   os.path.join(REPO, 'scripts', 'nhl-calendar.js'),
    'soccer-calendar': os.path.join(REPO, 'scripts', 'soccer-calendar.js'),
    'ncaab-calendar': os.path.join(REPO, 'scripts', 'ncaab-calendar.js'),
    'ncaaf-calendar': os.path.join(REPO, 'scripts', 'ncaaf-calendar.js'),
    'nfl-calendar':   os.path.join(REPO, 'scripts', 'nfl-calendar.js'),
}


def engine_hash(path):
    with open(path, 'rb') as f:
        return 'c' + hashlib.md5(f.read()).hexdigest()[:10]


def build_versions():
    out = {}
    for name, path in ENGINES.items():
        if os.path.exists(path):
            out[name] = engine_hash(path)
    return out


def stamp_file(fp, versions):
    try:
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            s = f.read()
    except OSError:
        return 0
    orig = s
    names = '|'.join(re.escape(n) for n in versions)
    # versioned refs: (scripts/)?<engine>.js?v=...  -> correct hash for that engine
    s = re.sub(
        r'((?:scripts/)?(' + names + r')\.js)\?v=[^"\'> ]+',
        lambda m: m.group(1) + '?v=' + versions[m.group(2)], s)
    # unversioned refs: (scripts/)?<engine>.js"  -> add ?v=hash
    s = re.sub(
        r'((?:scripts/)?(' + names + r')\.js)(?=["\'])',
        lambda m: m.group(1) + '?v=' + versions[m.group(2)], s)
    if s != orig:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(s)
        return 1
    return 0


def main():
    versions = build_versions()
    if not versions:
        print('  [stamp] no calendar engines found - nothing to do')
        return 0
    files = glob.glob(os.path.join(REPO, '*.html')) + \
        glob.glob(os.path.join(REPO, 'archives', '**', '*.html'), recursive=True)
    changed = 0
    for fp in files:
        changed += stamp_file(fp, versions)
    print('  [stamp] calendar cache-bust stamped from engine hashes:')
    for n, v in sorted(versions.items()):
        print(f'         {n}.js -> ?v={v}')
    print(f'  [stamp] {changed} page(s) updated ({len(files)} scanned)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
