"""One-time SEO retrofit: normalize handicapping-hub-archive/hub-YYYY-MM-DD.html.

Every dated archive snapshot must have a UNIQUE, DATED <title> + meta description
and a self-canonical to its own URL. ~58 archives had dateless/generic/PREVIEW
titles or reused the live hub's exact 'Today's Betting Stats' title, which
duplicated the evergreen hub and produced stale/inconsistent metadata in Google.

Idempotent. Only rewrites <title>, <meta name=description>, and canonical.
Does NOT touch visible page content/design.
"""
import os, re, glob
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(REPO, 'handicapping-hub-archive')

def pretty(date_iso):
    return datetime.strptime(date_iso, '%Y-%m-%d').strftime('%B %d, %Y')

changed = 0
for path in sorted(glob.glob(os.path.join(ARCHIVE, 'hub-*.html'))):
    base = os.path.basename(path)
    m = re.match(r'hub-(\d{4}-\d{2}-\d{2})\.html$', base)
    if not m:
        continue
    date_iso = m.group(1)
    d = pretty(date_iso)
    title = f'Handicapping Hub - {d} | BetLegend'
    desc = (f'BetLegend Handicapping Hub for {d}: advanced stats, betting lines, '
            f'injury reports, and situational data across NBA, NHL, MLB, NFL, '
            f'NCAAB, and soccer.')
    canon = f'https://www.betlegendpicks.com/handicapping-hub-archive/{base}'

    with open(path, 'r', encoding='utf-8', newline='') as f:
        html = f.read()
    orig = html

    html = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', html,
                  count=1, flags=re.DOTALL)
    if re.search(r'<meta\s+name="description"\s+content="[^"]*"', html):
        html = re.sub(r'(<meta\s+name="description"\s+content=")[^"]*(")',
                      lambda mm: mm.group(1) + desc + mm.group(2), html, count=1)
    else:
        html = html.replace('</title>',
                            f'</title>\n    <meta name="description" content="{desc}">', 1)
    # self-canonical
    tag = f'<link rel="canonical" href="{canon}"/>'
    if 'rel="canonical"' in html:
        html = re.sub(r'<link[^>]+rel="canonical"[^>]*>', tag, html, count=1)
    else:
        html = html.replace('</title>', '</title>\n    ' + tag, 1)

    if html != orig:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(html)
        changed += 1

print(f"Normalized {changed} archive files (of {len(glob.glob(os.path.join(ARCHIVE,'hub-*.html')))} total).")
