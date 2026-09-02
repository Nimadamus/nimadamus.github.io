#!/usr/bin/env python3
"""Indexation recovery pass 2 (June 3, 2026): targeted canonical fixes.

1. Sport preview hubs whose canonical points at a dated/stale article
   (clone artifact of the daily hub refresh) -> self-canonical.
2. Pages whose canonical uses the bare host (https://betlegendpicks.com/...)
   -> force https://www.betlegendpicks.com/...
3. penguins-team-total-over-2-5-hurricanes-nhl.html carries TWO canonicals
   (self + nhl-previews.html) -> drop the non-self one.
4. handicapping-hub pages with no canonical at all -> add self-canonical.
   (NO consolidation: each page canonicals to ITSELF. The banned
   "canonicalize dated hub archives to handicapping-hub.html" is NOT done.)

Idempotent; prints every change. No content is removed.
"""
import os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BASE = 'https://www.betlegendpicks.com'
CANON_RE = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*>|<link[^>]+href=["\'][^"\']+["\'][^>]+rel=["\']canonical["\'][^>]*>', re.I)

def url_for(rel):
    return BASE + '/' + rel.replace('\\', '/')

def read(p):
    return open(p, encoding='utf-8', errors='ignore').read()

def write(p, txt):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)

changes = []

def fix_self_canonical(rel):
    """Force every canonical tag in `rel` to the page's own www URL."""
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print(f'  MISSING {rel}')
        return
    txt = read(p)
    self_url = url_for(rel)
    tags = CANON_RE.findall(txt)
    if not tags:
        return
    new_txt = txt
    seen_one = False
    for t in tags:
        m = re.search(r'href=["\']([^"\']+)["\']', t)
        href = m.group(1) if m else ''
        if href == self_url and not seen_one:
            seen_one = True
            continue
        if not seen_one:
            new_tag = t[:m.start(1)] + self_url + t[m.end(1):]
            new_txt = new_txt.replace(t, new_tag, 1)
            seen_one = True
            changes.append(f'{rel}: canonical {href} -> SELF')
        else:
            # extra canonical tag: remove it
            new_txt = new_txt.replace(t, '', 1)
            changes.append(f'{rel}: removed extra canonical ({href})')
    # also fix og:url if it mismatches
    new_txt = re.sub(
        r'(<meta[^>]+property=["\']og:url["\'][^>]+content=["\'])[^"\']+(["\'])',
        lambda mm: mm.group(1) + self_url + mm.group(2), new_txt)
    if new_txt != txt:
        write(p, new_txt)

def add_self_canonical(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        return
    txt = read(p)
    if CANON_RE.search(txt):
        return
    tag = f'<link rel="canonical" href="{url_for(rel)}"/>\n'
    if '</head>' in txt:
        new_txt = txt.replace('</head>', tag + '</head>', 1)
        write(p, new_txt)
        changes.append(f'{rel}: added self-canonical')

def main():
    # 1+3. hubs and multi-canonical page -> self
    for rel in ['mlb-previews.html', 'nba-previews.html', 'soccer-previews.html',
                'penguins-team-total-over-2-5-hurricanes-nhl.html']:
        fix_self_canonical(rel)

    # 2. bare-host canonicals -> www (scan whole repo root + subdirs)
    for dirpath, dirs, files in os.walk(ROOT):
        parts = dirpath.split(os.sep)
        if '.git' in parts or 'node_modules' in parts or 'scripts' in parts:
            continue
        for fn in files:
            if not fn.endswith('.html'):
                continue
            p = os.path.join(dirpath, fn)
            txt = read(p)
            if 'href="https://betlegendpicks.com/' in txt or "href='https://betlegendpicks.com/" in txt:
                new_txt = txt.replace('https://betlegendpicks.com/', 'https://www.betlegendpicks.com/')
                write(p, new_txt)
                rel = os.path.relpath(p, ROOT).replace('\\', '/')
                changes.append(f'{rel}: bare-host -> www')

    # 4. handicapping hub pages missing canonicals -> self
    targets = [f for f in os.listdir(ROOT)
               if f.startswith('handicapping-hub') and f.endswith('.html')]
    arch = os.path.join(ROOT, 'handicapping-hub-archive')
    if os.path.isdir(arch):
        targets += ['handicapping-hub-archive/' + f for f in os.listdir(arch) if f.endswith('.html')]
    for rel in sorted(targets):
        add_self_canonical(rel)

    print(f'{len(changes)} changes:')
    for c in changes:
        print(' ', c)

if __name__ == '__main__':
    main()
