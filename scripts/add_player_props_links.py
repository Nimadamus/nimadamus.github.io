"""One-shot: insert Player Props Records links sitewide, preserving line endings.

Inserts:
  1. Records dropdown (records pages nav):   Player Props after Cross-Sport Bets
  2. Game Previews & Records mega-dropdown:  Player Props Records after Cross-Sport Parlays
  3. records.html sport strip, index.html footer + Record center grid
  4. sitemap-records.xml entry
Skips files whose legacy article content fails the universal validator.
"""
import glob
import io
import re

SKIP = {
    'player-props-records.html',
    # legacy pages with pre-existing validator failures (old roster text) -
    # leave untouched so the nav rollout cannot be blocked by old content
    'cavs-lakers-luka-mitchell-showdown-raptors-visit-pistons-nba.html',
    'rangers-moneyline-gore-strikeouts-athletics-sacramento-mlb.html',
}

mega_re = re.compile(
    r'(<a href="(/?)crosssport-parlays-records\.html">Cross-Sport Parlays<span>[^<]*</span></a>)')
drop_re = re.compile(
    r'(<a href="crosssport-parlays-records\.html" title="Cross-Sport Bets">Cross-Sport Bets</a>)')

DROP_LINK = '<a href="player-props-records.html" title="Player Props Records">Player Props</a>'


def read(path):
    with io.open(path, 'r', encoding='utf-8', errors='ignore', newline='') as fh:
        return fh.read()


def write(path, content):
    with io.open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(content)


def newline_of(content):
    return '\r\n' if '\r\n' in content[:2000] else '\n'


mega_files = drop_files = 0
for f in sorted(glob.glob('*.html')):
    if f in SKIP:
        continue
    c = read(f)
    if 'player-props-records.html' in c:
        continue
    nl = newline_of(c)
    orig = c

    def mega_sub(m):
        slash = m.group(2)
        return (m.group(1) + nl + '    <a href="' + slash +
                'player-props-records.html">Player Props Records'
                '<span>Graded player prop picks across all sports.</span></a>')

    c, n1 = mega_re.subn(mega_sub, c)
    c, n2 = drop_re.subn(lambda m: m.group(1) + nl + ' ' + DROP_LINK, c)
    if c != orig:
        write(f, c)
        mega_files += 1 if n1 else 0
        drop_files += 1 if n2 else 0

print('mega-dropdown files updated:', mega_files)
print('records-dropdown files updated:', drop_files)

# records.html sport strip
c = read('records.html')
nl = newline_of(c)
anchor = '<a href="soccer-records.html" style="color: #ccc; text-decoration: none; font-size: 13px;">Soccer</a>'
addition = (anchor + nl + ' <span style="color: #444;">|</span>' + nl +
            ' <a href="player-props-records.html" style="color: #ccc; text-decoration: none; font-size: 13px;">Player Props</a>')
if 'player-props-records.html" style="color: #ccc' not in c and anchor in c:
    c = c.replace(anchor, addition, 1)
    write('records.html', c)
    print('records.html sport strip: added')

# index.html footer Records group + Record center grid
c = read('index.html')
foot_old = '<a href="soccer-records.html">Soccer</a></div>'
foot_new = '<a href="soccer-records.html">Soccer</a><a href="player-props-records.html">Player Props</a></div>'
grid_old = '<a href="soccer-records.html">Soccer</a><a href="contact.html">Contact</a>'
grid_new = '<a href="soccer-records.html">Soccer</a><a href="player-props-records.html">Props</a><a href="contact.html">Contact</a>'
changed = False
if foot_old in c and 'player-props-records.html">Player Props</a></div>' not in c:
    c = c.replace(foot_old, foot_new, 1)
    changed = True
if grid_old in c:
    c = c.replace(grid_old, grid_new, 1)
    changed = True
if changed:
    write('index.html', c)
    print('index.html footer/grid: added')

# sitemap-records.xml
c = read('sitemap-records.xml')
entry = ('<url><loc>https://www.betlegendpicks.com/player-props-records.html</loc>'
         '<lastmod>2026-06-06</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>')
anchor = '<url><loc>https://www.betlegendpicks.com/records.html</loc>'
if 'player-props-records.html' not in c and anchor in c:
    c = c.replace(anchor, entry + anchor, 1)
    write('sitemap-records.xml', c)
    print('sitemap-records.xml: added')
