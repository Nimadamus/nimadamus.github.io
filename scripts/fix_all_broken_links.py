#!/usr/bin/env python3
import os, re, glob
from pathlib import Path

REPO = os.path.normpath('C:/Users/Nima/nimadamus.github.io')

stats = dict(files_mod=0, files_created=0, links_fixed=0,
             hub=0, kelly=0, consensus=0, mlbhist=0, favicon=0, proof=0, premium=0, terms=0)

def rf(p):
    try:
        with open(p, 'r', encoding='utf-8') as f: return f.read()
    except UnicodeDecodeError:
        with open(p, 'r', encoding='latin-1') as f: return f.read()

def wf(p, c):
    with open(p, 'w', encoding='utf-8', newline=chr(10)) as f: f.write(c)

def fix_subdir_file(filepath, depth=1):
    content = rf(filepath)
    orig = content
    prefix = '../' * depth
    fixes = 0
    lines = content.split(chr(10))
    new_lines = []
    in_script = False
    fdir = os.path.dirname(filepath)

    for line in lines:
        if '<script' in line.lower() and '</script>' not in line.lower():
            in_script = True
        if '</script>' in line.lower():
            if 'handicapping-hub-archive/hub-' in line and 'dateStr' in line:
                old = line
                line = line.replace('handicapping-hub-archive/hub-', 'hub-')
                if line != old: fixes += 1
            in_script = False
            new_lines.append(line)
            continue
        if in_script:
            if 'handicapping-hub-archive/hub-' in line and 'dateStr' in line:
                old = line
                line = line.replace('handicapping-hub-archive/hub-', 'hub-')
                if line != old: fixes += 1
            new_lines.append(line)
            continue
        if 'rel="canonical"' in line or 'og:url' in line:
            new_lines.append(line)
            continue

        cnt = [fixes]
        def fh(m, c=cnt, sd=fdir, px=prefix):
            v = m.group(1)
            if (v.startswith('../') or v.startswith('/') or v.startswith('http') or
                v.startswith('#') or v.startswith('mailto') or v.startswith('javascript') or
                v == '' or v.startswith('hub-')):
                return m.group(0)
            if os.path.exists(os.path.join(sd, v)):
                return m.group(0)
            if os.path.exists(os.path.join(REPO, v)) or v.endswith('.html') or v.endswith('.css'):
                c[0] += 1
                return 'href="' + px + v + '"'
            return m.group(0)

        new_line = re.sub(r'href="([^"]*)"', fh, line)
        fixes = cnt[0]
        new_lines.append(new_line)

    new_content = chr(10).join(new_lines)
    if new_content != orig:
        wf(filepath, new_content)
        return fixes
    return 0

def fix_hub_archive():
    print()
    print('=== FIXING: handicapping-hub-archive/ relative paths ===')
    d = os.path.join(REPO, 'handicapping-hub-archive')
    total = 0; fcount = 0
    for fp in sorted(glob.glob(os.path.join(d, '*.html'))):
        n = fix_subdir_file(fp, depth=1)
        if n > 0:
            fcount += 1; total += n
            print(f'  Fixed {n} links in {os.path.basename(fp)}')
    stats['hub'] = fcount; stats['links_fixed'] += total; stats['files_mod'] += fcount
    print(f'  TOTAL: {fcount} files, {total} links fixed')

def fix_kelly():
    print()
    print('=== FIXING: kelly-criterion/ relative paths ===')
    d = os.path.join(REPO, 'kelly-criterion')
    total = 0; fcount = 0
    for fp in sorted(glob.glob(os.path.join(d, '*.html'))):
        n = fix_subdir_file(fp, depth=1)
        if n > 0:
            fcount += 1; total += n
            print(f'  Fixed {n} links in {os.path.basename(fp)}')
    stats['kelly'] = fcount; stats['links_fixed'] += total; stats['files_mod'] += fcount
    print(f'  TOTAL: {fcount} files, {total} links fixed')

def fix_consensus():
    print()
    print('=== FIXING: consensus_library/ relative paths ===')
    cdir = os.path.join(REPO, 'consensus_library')
    total = 0; fcount = 0
    for root, dirs, files in os.walk(cdir):
        if os.sep + '.git' in root or root.endswith('.git'): continue
        for fn in files:
            if not fn.endswith('.html'): continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, REPO)
            depth = len(Path(rel).parts) - 1
            if depth <= 1: continue
            if fn == 'index.html': continue
            n = fix_subdir_file(fp, depth=depth)
            if n > 0:
                fcount += 1; total += n
                print(f'  Fixed {n} links in {os.path.relpath(fp, REPO)}')
    stats['consensus'] = fcount; stats['links_fixed'] += total; stats['files_mod'] += fcount
    print(f'  TOTAL: {fcount} files, {total} links fixed')

def fix_premium():
    print()
    print('=== FIXING: premium.html link in index.html ===')
    fp = os.path.join(REPO, 'index.html')
    c = rf(fp); o = c
    c = c.replace('href="premium.html"', 'href="blog.html"')
    if c != o:
        wf(fp, c); stats['premium'] = 1; stats['links_fixed'] += 1; stats['files_mod'] += 1
        print('  Changed premium.html -> blog.html')
    else:
        print('  Already fixed')

def fix_mlbhist():
    print()
    print('=== FIXING: mlb-historical.html references ===')
    fc = 0; lc = 0
    for root, dirs, files in os.walk(REPO):
        if os.sep + '.git' in root or root.endswith('.git'): continue
        for fn in files:
            if not fn.endswith('.html'): continue
            fp = os.path.join(root, fn)
            c = rf(fp)
            if 'mlb-historical.html' not in c: continue
            o = c
            cnt = c.count('mlb-historical.html')
            c = c.replace('mlb-historical.html', 'mlb.html')
            c = c.replace('>MLB Historical Betting Data<', '>MLB Analysis<')
            if c != o:
                wf(fp, c); fc += 1; lc += cnt
                print(f'  Fixed {cnt} refs in {os.path.basename(fp)}')
    stats['mlbhist'] = fc; stats['links_fixed'] += lc; stats['files_mod'] += fc
    print(f'  TOTAL: {fc} files, {lc} links fixed')

def fix_favicon():
    print()
    print('=== FIXING: favicon.ico references ===')
    fc = 0
    for fn in ['implied-probability-calculator.html', 'odds-converter.html']:
        fp = os.path.join(REPO, fn)
        if not os.path.exists(fp): continue
        c = rf(fp); o = c
        c = re.sub(r'\s*<link rel=.icon. type=.image/x-icon. href=.favicon\.ico.>\s*', '', c)
        if c != o:
            wf(fp, c); fc += 1
            print(f'  Removed favicon ref from {fn}')
    stats['favicon'] = fc; stats['links_fixed'] += fc; stats['files_mod'] += fc
    print(f'  TOTAL: {fc} files fixed')

def fix_proof():
    print()
    print('=== FIXING: 2.png references in proofofpicks.html ===')
    fp = os.path.join(REPO, 'proofofpicks.html')
    if not os.path.exists(fp):
        print('  Not found'); return
    c = rf(fp); o = c
    cnt = c.count('href="2.png"')
    c = c.replace('href="2.png"', 'href="images/betlegend-logo-2.png"')
    if c != o:
        wf(fp, c); stats['proof'] = 1; stats['links_fixed'] += cnt; stats['files_mod'] += 1
        print(f'  Fixed {cnt} broken 2.png links')
    else:
        print('  Already fixed')

def check_js_templates():
    print()
    print('=== INFO: JavaScript template literals (valid code, no fix needed) ===')
    hd = 0
    for fn in os.listdir(REPO):
        if fn.endswith('.html'):
            fp = os.path.join(REPO, fn)
            if os.path.isfile(fp):
                c = rf(fp)
                if 'hasData.page' in c: hd += 1
    print(f'  hasData.page in {hd} files (valid JS template literals)')
    for af in ['betlegend-expert-analysis-betting-picks-archive-8.html',
               'betlegend-nfl-mlb-ncaaf-expert-picks-archive-7.html']:
        fp = os.path.join(REPO, af)
        if os.path.exists(fp) and 'prevPage' in rf(fp):
            print(f'  prevPage/nextPage in {af} (valid JS)')
    fp = os.path.join(REPO, 'index.html')
    if 'plan.url' in rf(fp):
        print('  plan.url in index.html (valid JS Stripe rotator)')

def main():
    print('=' * 70)
    print('  BETLEGEND COMPREHENSIVE BROKEN LINK FIXER')
    print('=' * 70)
    fix_hub_archive()
    fix_kelly()
    fix_consensus()
    fix_premium()
    check_js_templates()
    fix_mlbhist()
    fix_favicon()
    fix_proof()
    print()
    print('=' * 70)
    print('  SUMMARY')
    print('=' * 70)
    print(f"  Files modified:              {stats['files_mod']}")
    print(f"  Files created:               {stats['files_created']}")
    print(f"  Total links fixed:           {stats['links_fixed']}")
    print(f"  Hub archive files:           {stats['hub']}")
    print(f"  Kelly criterion files:       {stats['kelly']}")
    print(f"  Consensus library files:     {stats['consensus']}")
    print(f"  premium.html link:           {stats['premium']}")
    print(f"  mlb-historical refs:         {stats['mlbhist']}")
    print(f"  favicon refs removed:        {stats['favicon']}")
    print(f"  proofofpicks 2.png:          {stats['proof']}")
    print('=' * 70)

if __name__ == '__main__':
    main()
