#!/usr/bin/env python3
"""
Strip -<month>-<day>-<year> suffixes from every HTML filename in the repo root.
- Builds a rename map (with collision suffixes -v2, -v3, ...)
- git mv's every file to its dateless slug
- Writes a tiny redirect stub at every OLD path so existing inbound links 301-equivalent to the new path
- Rewrites every reference to old slugs across HTML and JS files (canonicals, og:url, hrefs, sitemap, JSON-LD, calendar data)
- Touches sitemap.xml and featured-games-data.js
"""
import os, re, json, subprocess, sys, html as htmllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATE_RE = re.compile(r'-(january|february|march|april|may|june|july|august|september|october|november|december)-\d{1,2}-(?:2024|2025|2026)\.html$', re.I)

def list_dated_files():
    return sorted([f for f in os.listdir(ROOT) if f.endswith('.html') and DATE_RE.search(f)])

def base_slug(f):
    """Strip the trailing -month-day-year before .html"""
    return DATE_RE.sub('.html', f)

def build_rename_map(files):
    """Return list of (old_filename, new_filename) tuples, with collisions resolved by -v2/-v3 suffix on the OLDER files (sorted-stable)."""
    # Map base -> list of old filenames
    base_to_olds = {}
    for f in files:
        b = base_slug(f)
        base_to_olds.setdefault(b, []).append(f)

    # Sort each group: newest date wins the bare slug, older get -v2, -v3...
    def date_key(filename):
        m = re.search(r'-(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{1,2})-(\d{4})\.html$', filename, re.I)
        if not m: return (0,0,0)
        months = {'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,'july':7,'august':8,'september':9,'october':10,'november':11,'december':12}
        return (int(m.group(3)), months[m.group(1).lower()], int(m.group(2)))

    rename_map = {}
    for base, olds in base_to_olds.items():
        # Reserve bare slug for the NEWEST dated file
        olds_sorted = sorted(olds, key=date_key, reverse=True)
        rename_map[olds_sorted[0]] = base
        # Older versions get numeric suffix
        for i, old in enumerate(olds_sorted[1:], start=2):
            new = base.replace('.html', f'-v{i}.html')
            rename_map[old] = new
    return rename_map

def git_mv(old, new):
    """git mv, fall back to plain rename if git complains."""
    old_path = os.path.join(ROOT, old)
    new_path = os.path.join(ROOT, new)
    if os.path.exists(new_path):
        return False, f'TARGET-EXISTS: {new}'
    try:
        subprocess.run(['git', '-C', ROOT, 'mv', old, new], check=True, capture_output=True, text=True)
        return True, 'git mv'
    except subprocess.CalledProcessError:
        try:
            os.rename(old_path, new_path)
            return True, 'os.rename'
        except OSError as e:
            return False, f'RENAME-FAIL: {e}'

def write_redirect_stub(old_filename, new_filename):
    """Write a tiny redirect stub at the OLD path."""
    new_url = '/' + new_filename
    title = old_filename.replace('.html','').replace('-',' ').title() + ' - Redirect'
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
    p = os.path.join(ROOT, old_filename)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(stub)

def rewrite_references(rename_map):
    """Rewrite every reference to an OLD filename (dated) to its NEW filename (dateless) across all HTML, JS, XML, JSON files in the repo."""
    extensions = ('.html', '.js', '.xml', '.json', '.txt', '.md')
    changed_files = 0
    total_replacements = 0
    # Collect every file under ROOT (skip .git, node_modules, scripts dir for safety only on this script's own path)
    for dirpath, dirs, files in os.walk(ROOT):
        if '.git' in dirpath.split(os.sep) or 'node_modules' in dirpath.split(os.sep):
            continue
        for fn in files:
            if not fn.endswith(extensions):
                continue
            p = os.path.join(dirpath, fn)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    c = fh.read()
            except Exception:
                continue
            orig = c
            replacements_in_file = 0
            for old, new in rename_map.items():
                if old in c:
                    cnt = c.count(old)
                    c = c.replace(old, new)
                    replacements_in_file += cnt
            if c != orig:
                with open(p, 'w', encoding='utf-8') as fh:
                    fh.write(c)
                changed_files += 1
                total_replacements += replacements_in_file
    return changed_files, total_replacements

def main():
    print('=' * 70)
    print('  STRIP DATES FROM URLS')
    print('=' * 70)
    files = list_dated_files()
    print(f'\n  Dated HTML files in repo root: {len(files)}')

    rename_map = build_rename_map(files)
    print(f'  Rename map built: {len(rename_map)} entries')

    collisions = sum(1 for new in rename_map.values() if '-v2' in new or '-v3' in new or '-v4' in new or '-v5' in new)
    print(f'  Collision suffixes assigned: {collisions}')

    if '--dry-run' in sys.argv:
        print('\n  --- DRY RUN, sample 20 ---')
        for old, new in list(rename_map.items())[:20]:
            print(f'    {old}  ->  {new}')
        sys.exit(0)

    # Phase 1: rename
    print('\n  Phase 1: renaming files...')
    renamed = 0
    failed = []
    for old, new in rename_map.items():
        ok, msg = git_mv(old, new)
        if ok:
            renamed += 1
        else:
            failed.append((old, new, msg))
    print(f'    Renamed: {renamed}')
    if failed:
        print(f'    FAILED: {len(failed)}')
        for f in failed[:10]:
            print(f'      {f}')

    # Phase 2: rewrite references everywhere
    print('\n  Phase 2: rewriting references across the repo...')
    cf, tr = rewrite_references(rename_map)
    print(f'    Files modified: {cf}')
    print(f'    Total replacements: {tr}')

    # Phase 3: redirect stubs at OLD paths
    print('\n  Phase 3: writing redirect stubs at old URLs...')
    stubs = 0
    for old, new in rename_map.items():
        try:
            write_redirect_stub(old, new)
            stubs += 1
        except Exception as e:
            print(f'    stub fail {old}: {e}')
    print(f'    Stubs written: {stubs}')

    # Save the map for later use (FTP sync, etc.)
    map_path = os.path.join(ROOT, 'scripts', 'date_strip_rename_map.json')
    with open(map_path, 'w', encoding='utf-8') as f:
        json.dump(rename_map, f, indent=2)
    print(f'\n  Rename map saved: {map_path}')
    print('\n  DONE.')

if __name__ == '__main__':
    main()
