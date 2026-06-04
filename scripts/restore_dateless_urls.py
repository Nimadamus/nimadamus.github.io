#!/usr/bin/env python3
"""Indexation recovery (June 3, 2026): re-enforce the May 3, 2026 directive
"no dates in URLs anywhere on betlegendpicks.com".

The May 3 run (commit 748da93a8) renamed 686 dated files to dateless slugs and
left redirect stubs. Commit ee65c42d1 (May 15, "Restore sport calendar article
targets") clobbered those stubs back to full pages, and generators kept
creating new dated URLs. Result: 640 dated full-content pages live again, 240
of them exact duplicates of their dateless twin -> GSC "Crawled - not indexed".

This script fixes forward:
  1. PAIRS   (dated + dateless both exist): dated becomes a redirect stub to
     the dateless twin (dateless copy is the newer one - it carries the
     current site-navbar; article body is identical).
  2. OLD-ONLY (dated exists, dateless target from the May 3 map missing):
     git mv dated -> mapped dateless slug, stub at the old path.
  3. NEW dated files created after May 3 (not in the map): renamed to a
     dateless slug (collision -> -v2/-v3), stub at the old path.
  4. Every reference to an old dated slug is rewritten across HTML/JS/XML/
     JSON/TXT/MD (canonicals, og:url, hrefs, JSON-LD, calendar data,
     homepage-picks-data.js, featured-games-data.js).
  5. New mappings are merged into scripts/date_strip_rename_map.json.

Run with --dry-run to preview. Follow with sync_calendars.py,
validate_calendar_continuity.py and generate_discovery_artifacts.py.
"""
import os, re, json, subprocess, sys, html as htmllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAP_PATH = os.path.join(ROOT, 'scripts', 'date_strip_rename_map.json')
DATE_RE = re.compile(r'-(january|february|march|april|may|june|july|august|september|october|november|december)-\d{1,2}-(?:2024|2025|2026)\.html$', re.I)
DRY = '--dry-run' in sys.argv

REWRITE_SKIP = {
    os.path.normpath(MAP_PATH),
    os.path.normpath(os.path.join(ROOT, 'scripts', 'indexation_audit_report.json')),
    os.path.normpath(os.path.join(ROOT, 'scripts', 'restore_dateless_urls.py')),
    os.path.normpath(os.path.join(ROOT, 'scripts', 'strip_dates_from_urls.py')),
    os.path.normpath(os.path.join(ROOT, '_rename_mapping.json')),
}


def base_slug(f):
    return DATE_RE.sub('.html', f)


def is_stub(path):
    try:
        head = open(path, encoding='utf-8', errors='ignore').read(3000)
    except OSError:
        return False
    return 'http-equiv="refresh"' in head or "http-equiv='refresh'" in head


def write_redirect_stub(old_filename, new_filename):
    new_url = '/' + new_filename
    title = old_filename.replace('.html', '').replace('-', ' ').title() + ' - Redirect'
    stub = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>{htmllib.escape(title)}</title>
<link rel="canonical" href="https://www.betlegendpicks.com{new_url}"/>
<meta http-equiv="refresh" content="0; url={new_url}">
<meta name="robots" content="noindex, follow">
<script>window.location.replace("{new_url}");</script>
</head>
<body>
<p>Redirecting to <a href="{new_url}">{htmllib.escape(new_filename)}</a></p>
</body>
</html>
'''
    with open(os.path.join(ROOT, old_filename), 'w', encoding='utf-8', newline='\n') as f:
        f.write(stub)


def git_mv(old, new):
    if DRY:
        return True
    try:
        subprocess.run(['git', '-C', ROOT, 'mv', old, new], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        try:
            os.rename(os.path.join(ROOT, old), os.path.join(ROOT, new))
            return True
        except OSError as e:
            print(f'  RENAME-FAIL {old}: {e}')
            return False


def rewrite_references(rename_map):
    exts = ('.html', '.js', '.xml', '.json', '.txt', '.md')
    pat = re.compile('|'.join(re.escape(o) for o in sorted(rename_map, key=len, reverse=True)))
    changed = total = 0
    for dirpath, dirs, files in os.walk(ROOT):
        parts = dirpath.split(os.sep)
        if '.git' in parts or 'node_modules' in parts or '__pycache__' in parts:
            continue
        for fn in files:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dirpath, fn)
            if os.path.normpath(p) in REWRITE_SKIP:
                continue
            try:
                txt = open(p, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            new_txt, n = pat.subn(lambda m: rename_map[m.group(0)], txt)
            if n:
                changed += 1
                total += n
                if not DRY:
                    with open(p, 'w', encoding='utf-8', newline='') as f:
                        f.write(new_txt)
    print(f'  References rewritten: {total} replacements in {changed} files')


def main():
    old_map = json.load(open(MAP_PATH, encoding='utf-8'))
    files = set(f for f in os.listdir(ROOT) if f.endswith('.html'))

    pairs, old_only, new_dated = [], [], []
    for o, n in old_map.items():
        if o in files and not is_stub(os.path.join(ROOT, o)):
            (pairs if n in files else old_only).append((o, n))
    mapped_old = set(old_map)
    for f in sorted(files):
        if DATE_RE.search(f) and f not in mapped_old and not is_stub(os.path.join(ROOT, f)):
            new_dated.append(f)

    print(f'Pairs (stub dated side): {len(pairs)}')
    print(f'Old-only (rename to mapped slug): {len(old_only)}')
    print(f'New dated since May 3 (rename): {len(new_dated)}')

    rename_map = {}   # every old -> new applied this run (for reference rewriting)
    new_entries = {}  # additions to the persistent map

    # 1. pairs: dated -> stub
    for o, n in pairs:
        rename_map[o] = n

    # 2. old-only: mv to mapped target
    taken = set(files)
    for o, n in old_only:
        if n in taken:
            print(f'  SKIP {o}: target {n} appeared')
            continue
        if git_mv(o, n):
            rename_map[o] = n
            taken.add(n)

    # 3. new dated: compute dateless slug with collision suffix
    def date_key(filename):
        m = re.search(r'-(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{1,2})-(\d{4})\.html$', filename, re.I)
        months = {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                  'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12}
        return (int(m.group(3)), months[m.group(1).lower()], int(m.group(2))) if m else (0, 0, 0)

    for o in sorted(new_dated, key=date_key, reverse=True):
        target = base_slug(o)
        if target in taken:
            i = 2
            while base_slug(o).replace('.html', f'-v{i}.html') in taken:
                i += 1
            target = base_slug(o).replace('.html', f'-v{i}.html')
        if git_mv(o, target):
            rename_map[o] = target
            new_entries[o] = target
            taken.add(target)

    if not rename_map:
        print('Nothing to do.')
        return

    # 4. rewrite references everywhere
    print('Rewriting references...')
    rewrite_references(rename_map)

    # 5. stubs at all old paths
    if not DRY:
        for o, n in rename_map.items():
            write_redirect_stub(o, n)
        print(f'  Stubs written: {len(rename_map)}')

    # 6. persist new map entries
    if new_entries and not DRY:
        old_map.update(new_entries)
        with open(MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(old_map, f, indent=2)
        print(f'  Map updated: +{len(new_entries)} entries')

    print('DONE' + (' (dry run)' if DRY else ''))


if __name__ == '__main__':
    main()
