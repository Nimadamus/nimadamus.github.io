#!/usr/bin/env python3
"""Crawl-path pass 2: static links for the page groups still orphaned after
build_preview_archives.py (handicapping hub archives, standalone pick pages,
featured-game prediction pages, sport calendar pages).

- handicapping-hub-archive.html gets a static dated link list of every
  handicapping-hub-archive/hub-YYYY-MM-DD.html (the set the live calendar
  links). Ensures handicapping-hub.html links the archive page.
- picks-archive.html gets a static link list of every standalone pick page
  (*-pick.html) and every *-prediction-picks.html featured analysis page.
  Ensures upcomingpicks.html links picks-archive.html.
- Each sport hub's MONTHLY-ARCHIVES block gains a link to its
  <sport>-calendar.html page (these were orphans).

Idempotent via BEGIN/END markers. Insert-only: no content removed.
"""
import os, re, html as htmllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TITLE_RE = re.compile(r'<title[^>]*>(.*?)</title>', re.I | re.S)


def read(p):
    return open(p, encoding='utf-8', errors='ignore').read()


def write(p, txt):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def title_of(rel):
    try:
        t = TITLE_RE.search(read(os.path.join(ROOT, rel)))
        if t:
            return re.sub(r'\s*\|\s*BetLegend.*$', '', re.sub(r'\s+', ' ', t.group(1)).strip())
    except OSError:
        pass
    return rel.replace('.html', '').replace('-', ' ').title()


def replace_marked(txt, marker, block, anchor='</main>'):
    begin, end = f'<!-- BEGIN {marker} -->', f'<!-- END {marker} -->'
    wrapped = f'{begin}\n{block}\n{end}'
    pat = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.S)
    if pat.search(txt):
        return pat.sub(wrapped, txt)
    for a in (anchor, '<footer', '</body>'):
        if a in txt:
            return txt.replace(a, wrapped + '\n' + a, 1)
    return txt + wrapped


def is_stub(rel):
    return 'http-equiv="refresh"' in read(os.path.join(ROOT, rel))[:3000]


def section(heading, items):
    lis = '\n'.join(
        f'    <li><a href="/{href}">{htmllib.escape(label)}</a></li>' for href, label in items)
    return (
        '<section class="static-archive-links" style="max-width:900px;margin:30px auto;padding:0 20px">\n'
        f'  <h2 style="font-size:20px">{htmllib.escape(heading)}</h2>\n'
        f'  <ul style="line-height:1.9;list-style:disc;padding-left:22px">\n{lis}\n  </ul>\n</section>'
    )


def main():
    files = set(os.listdir(ROOT))

    # 1. handicapping hub archive list
    arch_dir = os.path.join(ROOT, 'handicapping-hub-archive')
    hubs = sorted((f for f in os.listdir(arch_dir) if re.match(r'hub-\d{4}-\d{2}-\d{2}\.html$', f)), reverse=True)
    items = [(f'handicapping-hub-archive/{f}',
              'Handicapping Hub - ' + f[4:-5]) for f in hubs]
    p = os.path.join(ROOT, 'handicapping-hub-archive.html')
    txt = read(p)
    txt = replace_marked(txt, 'STATIC-HUB-ARCHIVE-LINKS',
                         section('Daily Handicapping Hub Archive', items))
    write(p, txt)
    print(f'handicapping-hub-archive.html: {len(items)} static links')

    hub_main = os.path.join(ROOT, 'handicapping-hub.html')
    t = read(hub_main)
    if 'href="handicapping-hub-archive.html"' not in t and 'href="/handicapping-hub-archive.html"' not in t:
        t = replace_marked(t, 'HUB-ARCHIVE-LINK',
                           '<p style="text-align:center;margin:18px 0"><a href="/handicapping-hub-archive.html">Browse the full Handicapping Hub archive</a></p>')
        write(hub_main, t)
        print('handicapping-hub.html: archive link added')

    # 2. picks archive list
    picks = sorted(f for f in files
                   if (f.endswith('-pick.html') or f.endswith('-prediction-picks.html'))
                   and not is_stub(f))
    items = [(f, title_of(f)) for f in picks]
    p = os.path.join(ROOT, 'picks-archive.html')
    txt = read(p)
    txt = replace_marked(txt, 'STATIC-PICKS-ARCHIVE-LINKS',
                         section('Every BetLegend Pick & Featured Game Analysis', items))
    write(p, txt)
    print(f'picks-archive.html: {len(items)} static links')

    up = os.path.join(ROOT, 'upcomingpicks.html')
    t = read(up)
    if 'picks-archive.html' not in t:
        t = replace_marked(t, 'PICKS-ARCHIVE-LINK',
                           '<p style="text-align:center;margin:18px 0"><a href="/picks-archive.html">Browse the full pick archive</a></p>')
        write(up, t)
        print('upcomingpicks.html: picks-archive link added')

    # 3. hub -> sport calendar links
    for hub, cal, label in [
        ('mlb-previews.html', 'mlb-calendar.html', 'MLB'),
        ('nba-previews.html', 'nba-calendar.html', 'NBA'),
        ('nhl-previews.html', 'nhl-calendar.html', 'NHL'),
        ('soccer-previews.html', 'soccer-calendar.html', 'Soccer'),
        ('college-basketball-previews.html', 'ncaab-calendar.html', 'College Basketball'),
        ('nfl.html', 'nfl-calendar.html', 'NFL'),
        ('ncaaf.html', 'ncaaf-calendar.html', 'NCAAF'),
    ]:
        hp = os.path.join(ROOT, hub)
        if not os.path.exists(hp) or cal not in files:
            continue
        t = read(hp)
        if f'href="/{cal}"' not in t and f'href="{cal}"' not in t:
            t = replace_marked(t, f'CALENDAR-LINK {cal}',
                               f'<p style="max-width:900px;margin:10px auto;padding:0 20px"><a href="/{cal}">{label} Archive Calendar</a></p>')
            write(hp, t)
            print(f'{hub}: linked {cal}')


if __name__ == '__main__':
    main()
