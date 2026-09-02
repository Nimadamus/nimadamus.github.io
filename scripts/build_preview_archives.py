#!/usr/bin/env python3
"""Build complete static crawl paths for daily preview/pick pages.

Google cannot follow the JS-rendered calendars, so every daily page needs a
plain <a href> chain: sport hub -> monthly archive -> daily page.

For each sport (from scripts/<sport>-calendar.js ARCHIVE_DATA):
  1. Group entries by month.
  2. For each month, ensure <sport>-previews-archive-<month>-<year>.html exists
     (cloned from the sport's newest existing archive page when missing).
  3. Insert/replace a marked static link section listing EVERY page of that
     month (date + title), newest first.
  4. Insert/replace a marked "Monthly Archives" static link block on the sport
     hub page linking every monthly archive.
Also rewrites links that still point at deleted dated URLs (old rename-map
keys that no longer exist on disk) to their dateless targets.

Idempotent: sections are delimited by BEGIN/END comment markers.
"""
import os, re, json, html as htmllib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAP_PATH = os.path.join(ROOT, 'scripts', 'date_strip_rename_map.json')

SPORTS = {
    'mlb': ('MLB', 'mlb-previews.html', 'mlb-previews-archive-{m}-{y}.html'),
    'nba': ('NBA', 'nba-previews.html', 'nba-previews-archive-{m}-{y}.html'),
    'nhl': ('NHL', 'nhl-previews.html', 'nhl-previews-archive-{m}-{y}.html'),
    'soccer': ('Soccer', 'soccer-previews.html', 'soccer-previews-archive-{m}-{y}.html'),
    'ncaab': ('College Basketball', 'college-basketball-previews.html', 'college-basketball-previews-archive-{m}-{y}.html'),
    'nfl': ('NFL', 'nfl.html', 'nfl-previews-archive-{m}-{y}.html'),
    'ncaaf': ('NCAAF', 'ncaaf.html', 'ncaaf-previews-archive-{m}-{y}.html'),
}
MONTH_NAMES = ['', 'january', 'february', 'march', 'april', 'may', 'june',
               'july', 'august', 'september', 'october', 'november', 'december']

ENTRY_RE = re.compile(r'\{\s*date:\s*"(\d{4})-(\d{2})-(\d{2})",\s*page:\s*"([^"]+)",\s*title:\s*"([^"]*)"')


def read(p):
    return open(p, encoding='utf-8', errors='ignore').read()


def write(p, txt):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)


def replace_marked(txt, marker, block, anchor='</main>'):
    begin, end = f'<!-- BEGIN {marker} -->', f'<!-- END {marker} -->'
    wrapped = f'{begin}\n{block}\n{end}'
    pat = re.compile(re.escape(begin) + r'.*?' + re.escape(end), re.S)
    if pat.search(txt):
        return pat.sub(wrapped, txt)
    if anchor in txt:
        return txt.replace(anchor, wrapped + '\n' + anchor, 1)
    return txt.replace('<footer', wrapped + '\n<footer', 1) if '<footer' in txt else txt + wrapped


def archive_link_section(sport_label, entries):
    items = []
    for (y, m, d, page, title) in sorted(entries, reverse=True):
        t = htmllib.escape(title) if title.strip() else page.replace('.html', '').replace('-', ' ').title()
        items.append(
            f'    <li><a href="/{page}">{t}</a> '
            f'<span style="color:#8b95a5;font-size:13px">({MONTH_NAMES[int(m)].title()} {int(d)}, {y})</span></li>')
    return (
        '<section class="static-archive-links" style="max-width:900px;margin:30px auto;padding:0 20px">\n'
        f'  <h2 style="font-size:20px">All {htmllib.escape(sport_label)} Articles This Month</h2>\n'
        '  <ul style="line-height:1.9;list-style:disc;padding-left:22px">\n'
        + '\n'.join(items) +
        '\n  </ul>\n</section>'
    )


def hub_archive_block(sport_label, archive_files):
    links = ' &middot; '.join(
        f'<a href="/{fn}">{MONTH_NAMES[mi].title()} {yr}</a>'
        for (yr, mi, fn) in sorted(archive_files, reverse=True))
    return (
        '<section class="monthly-archives" style="max-width:900px;margin:24px auto;padding:0 20px">\n'
        f'  <h2 style="font-size:18px">{htmllib.escape(sport_label)} Monthly Archives</h2>\n'
        f'  <p style="line-height:1.8">{links}</p>\n</section>'
    )


def main():
    files = set(os.listdir(ROOT))

    # 0. fix links that still point at DELETED dated URLs
    old_map = json.load(open(MAP_PATH, encoding='utf-8'))
    dead = {o: n for o, n in old_map.items() if o not in files and n in files}
    if dead:
        pat = re.compile('|'.join(re.escape(o) for o in sorted(dead, key=len, reverse=True)))
        fixed = 0
        for fn in sorted(files):
            if not fn.endswith('.html'):
                continue
            p = os.path.join(ROOT, fn)
            txt = read(p)
            new_txt, n = pat.subn(lambda mm: dead[mm.group(0)], txt)
            if n:
                write(p, new_txt)
                fixed += 1
        print(f'dead dated links rewritten in {fixed} files')

    today_created = []
    for key, (label, hub, arch_tpl) in SPORTS.items():
        cal = os.path.join(ROOT, 'scripts', f'{key}-calendar.js')
        if not os.path.exists(cal):
            continue
        entries = ENTRY_RE.findall(read(cal))
        if not entries:
            continue
        by_month = {}
        for y, m, d, page, title in entries:
            if (os.path.join(ROOT, page) and page in files):
                by_month.setdefault((y, m), []).append((y, m, d, page, title))

        archive_files = []
        # newest existing archive page of this sport = template for new months
        existing = sorted(f for f in files if re.match(
            arch_tpl.format(m='*', y='*').replace('*', r'[a-z0-9]+'), f))
        template = None
        for f in existing:
            template = f  # any existing one works; prefer latest by mtime
        if existing:
            template = max(existing, key=lambda f: os.path.getmtime(os.path.join(ROOT, f)))
        else:
            # sports with no archive pages yet (nfl/ncaaf) borrow the MLB shell
            fallback = sorted(f for f in files if re.match(r'mlb-previews-archive-[a-z]+-\d{4}\.html$', f))
            template = fallback[-1] if fallback else None

        for (y, m), ents in sorted(by_month.items()):
            mname = MONTH_NAMES[int(m)]
            arch = arch_tpl.format(m=mname, y=y)
            p = os.path.join(ROOT, arch)
            if not os.path.exists(p):
                if not template:
                    continue
                txt = read(os.path.join(ROOT, template))
                tm = re.search(r'archive-([a-z]+)-(\d{4})\.html', template)
                old_mname, old_y = tm.group(1), tm.group(2)
                txt = txt.replace(template, arch)
                txt = re.sub(re.escape(old_mname.title()) + r'\s+' + old_y, f'{mname.title()} {y}', txt)
                txt = txt.replace(old_mname, mname).replace(old_y, y)
                # strip the cloned month's article cards: keep shell (nav/header/footer),
                # the marked static section below carries this month's links
                mm_main = re.search(r'(<main[^>]*>).*?(</main>)', txt, re.S)
                if mm_main:
                    h1 = re.search(r'<h1[^>]*>.*?</h1>', mm_main.group(0), re.S)
                    inner = ('\n' + h1.group(0) + '\n') if h1 else '\n'
                    txt = txt[:mm_main.start()] + mm_main.group(1) + inner + mm_main.group(2) + txt[mm_main.end():]
                write(p, txt)
                files.add(arch)
                today_created.append(arch)
            txt = read(p)
            txt = replace_marked(txt, f'STATIC-ARCHIVE-LINKS {key} {y}-{m}',
                                 archive_link_section(label, ents))
            # self-canonical safety on created pages
            txt = re.sub(r'(<link[^>]+rel=["\']canonical["\'][^>]+href=["\'])[^"\']+(["\'])',
                         lambda mm: mm.group(1) + f'https://www.betlegendpicks.com/{arch}' + mm.group(2),
                         txt, count=1)
            write(p, txt)
            archive_files.append((y, int(m), arch))

        # hub block
        hp = os.path.join(ROOT, hub)
        if os.path.exists(hp) and archive_files:
            txt = read(hp)
            txt = replace_marked(txt, f'MONTHLY-ARCHIVES {key}',
                                 hub_archive_block(label, archive_files))
            write(hp, txt)
        print(f'{key}: {sum(len(v) for v in by_month.values())} pages across {len(archive_files)} monthly archives (hub block updated)')

    if today_created:
        print('created:', ', '.join(today_created))


if __name__ == '__main__':
    main()
