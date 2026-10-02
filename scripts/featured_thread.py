#!/usr/bin/env python3
"""
featured_thread.py
==================
Featured Game of the Day is ONE running thread (Nima, 2026-10-01): every new
breakdown is a post at the top of featured-game-of-the-day.html. No new
standalone dated page is committed. Breakdowns published before the change keep
their own URLs and are listed under "Earlier breakdowns".

Usage:
  python scripts/featured_thread.py add <built_page.html> <YYYY-MM-DD>
      Build the breakdown exactly as before from docs/templates/featured-preview.template,
      save it OUTSIDE the repo (or delete it after), then run this. It moves the hero
      and the article body into the thread as <article class="fg-post" id="...">, adds the
      featured-games-data.js entry (page = featured-game-of-the-day.html#<id>) and
      rebuilds the earlier list. Then run scripts/sync_featured_game_preview.py.
  python scripts/featured_thread.py build
      Rebuild the page (earlier list) without adding a post.
"""
import os
import re
import sys
from html import escape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THREAD = os.path.join(REPO, 'featured-game-of-the-day.html')
DATA = os.path.join(REPO, 'featured-games-data.js')
SITE = 'https://www.betlegendpicks.com'
SHELL_SOURCE = 'marlins-vs-nationals-alcantara-cavalli-analysis-stats-preview.html'
TITLE = 'Featured Game of the Day: Every Matchup Breakdown in One Thread | BetLegend'
DESC = ('BetLegend Featured Game of the Day in one running thread: the marquee matchup breakdown with '
        'odds, starters, advanced stats, injuries and trends, newest first.')
H1 = 'Featured Game of the Day'
INTRO = ('Every Featured Game breakdown lives here in one running thread, newest first. Analysis only, '
         'every number read live on the day it was written. Breakdowns published before the thread started '
         'keep their own pages and are listed under Earlier breakdowns.')
SITEMAPS = [os.path.join(REPO, 'sitemap-featured-games.xml'), os.path.join(REPO, 'sitemap-archive.xml')]


def read(p):
    with open(p, encoding='utf-8', errors='ignore') as f:
        return f.read()


def write(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def split_page(html):
    """(top, hero, middle_through_content_open, body, tail) of a featured article page."""
    h0 = html.index('<header class="hero">')
    h1 = html.index('</header>', h0) + len('</header>')
    cw = html.index('<div class="content-wrapper">', h1) + len('<div class="content-wrapper">')
    bn = html.index('<div class="back-nav">', cw)
    body, tail = html[cw:bn], html[bn:]
    # The article body leaves its own wrappers (game card etc.) open; close them in the
    # body and drop the matching closes that follow the back-nav link in the tail.
    k = len(re.findall(r'<div\b', body)) - body.count('</div>')
    if k > 0:
        body += '</div>' * k
        bn_end = tail.index('</div>') + len('</div>')
        rest = tail[bn_end:]
        for _ in range(k):
            i = rest.index('</div>')
            rest = rest[:i] + rest[i + len('</div>'):]
        tail = tail[:bn_end] + rest
    return html[:h0], html[h0:h1], html[h1:cw], body, tail


def entries():
    return re.findall(r'\{\s*date:\s*"(\d{4}-\d{2}-\d{2})"\s*,\s*page:\s*"([^"]+)"\s*,\s*title:\s*"([^"]*)"\s*\}',
                      read(DATA))


def old_list():
    seen, items = set(), []
    for d, page, title in sorted(entries(), reverse=True):
        if '#' in page or page in seen or not os.path.exists(os.path.join(REPO, page)):
            continue
        seen.add(page)
        items.append('<li>%s: <a href="%s">%s</a></li>' % (escape(d), escape(page), escape(title)))
    return '<h2 id="earlier">Earlier breakdowns</h2>\n<ul class="fg-old">%s</ul>\n' % ''.join(items)


def fresh_shell():
    top, _hero, mid, _body, tail = split_page(read(os.path.join(REPO, SHELL_SOURCE)))
    tail = re.sub(r'featured-games-calendar\.js\?v=[^"]*', 'featured-games-calendar.js?v=thread20261001', tail)
    top = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', '', top, flags=re.S)
    top = re.sub(r"<script>window\.FORCED_PAGE_DATE = '[^']*';</script>\s*", '', top)
    top = re.sub(r'<link rel="canonical" href="[^"]*"/?>', '<link rel="canonical" href="%s/featured-game-of-the-day.html"/>' % SITE, top)
    top = re.sub(r'<title>.*?</title>', '<title>%s</title>' % escape(TITLE), top, flags=re.S)
    for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
        top = re.sub(r'<meta (?:content="[^"]*" %s|%s content="[^"]*")\s*/?>' % (attr, attr),
                     '<meta %s content="%s"/>' % (attr, escape(DESC)), top)
    for attr in ('property="og:title"', 'name="twitter:title"'):
        top = re.sub(r'<meta content="[^"]*" %s\s*/?>' % attr, '<meta content="%s" %s/>' % (escape(TITLE), attr), top)
    top = re.sub(r'<meta content="[^"]*" property="og:url"\s*/?>',
                 '<meta content="%s/featured-game-of-the-day.html" property="og:url"/>' % SITE, top)
    top = re.sub(r'<meta name="keywords"[^>]*>\s*', '', top)
    top = top.replace('</head>', '<style>.fg-post{border-top:1px solid rgba(255,255,255,.12);margin-top:40px;'
                      'padding-top:24px}.fg-post .hero{padding:24px 0;background:none;text-align:left}'
                      '.fg-old li{margin:6px 0}</style>\n</head>', 1)
    hero = ('<header class="hero">\n<div class="hero-badge">The thread</div>\n<h1>%s</h1>\n<p>%s</p>\n</header>'
            % (escape(H1), escape(INTRO)))
    return (top + hero + mid + '\n<!--FG-POSTS:START-->\n<!--FG-POSTS:END-->\n'
            '<!--FG-OLD:START--><!--FG-OLD:END-->\n' + tail)


def normalize(html):
    """Article first in <main class="main-content">, calendar rail after it (the rail is
    position:fixed, so DOM order does not move it), and the data file loaded for the calendar."""
    if '<main class="main-content">' not in html:
        a0 = html.index('<aside class="calendar-sidebar">')
        cw = html.index('<div class="content-wrapper">', a0)
        rail = html[a0:cw]
        html = html[:a0] + '<main class="main-content">\n' + html[cw:]
        bn = html.index('<div class="back-nav">')
        close = html.index('</div>', html.index('</div>', bn) + 6)  # back-nav close, then content-wrapper close
        html = html[:close + 6] + '\n</main>\n' + rail + html[close + 6:]
    if '<script src="featured-games-data.js"></script>' not in html:
        html = html.replace('<script src="scripts/featured-games-calendar.js',
                            '<script src="featured-games-data.js"></script>\n<script src="scripts/featured-games-calendar.js', 1)
    if '<!--FG-LATEST:START-->' not in html:
        html = html.replace('<!--FG-POSTS:START-->', '<!--FG-LATEST:START--><!--FG-LATEST:END-->\n<!--FG-POSTS:START-->', 1)
    return html


def ensure_thread():
    html = read(THREAD)
    if '<!--FG-POSTS:START-->' not in html:
        html = fresh_shell()
    return normalize(html)


def latest_card():
    """While the newest entry is still a standalone page, point to it above the thread."""
    ents = sorted(entries(), reverse=True)
    if not ents or '#' in ents[0][1]:
        return ''
    d, page, title = ents[0]
    return ('<div class="fg-latest"><span class="hero-badge">Latest breakdown, %s</span>'
            '<h2><a href="%s">%s</a></h2></div>' % (escape(d), escape(page), escape(title)))


def bump_sitemap():
    import datetime
    today = datetime.date.today().isoformat()
    for path in SITEMAPS:
        if not os.path.exists(path):
            continue
        sm = read(path)
        sm2 = re.sub(r'(<loc>%s/featured-game-of-the-day\.html</loc>\s*<lastmod>)[^<]*' % re.escape(SITE), r'\g<1>' + today, sm)
        if sm2 != sm:
            write(path, sm2)


def rebuild(html):
    html = re.sub(r'<!--FG-LATEST:START-->.*?<!--FG-LATEST:END-->',
                  lambda _m: '<!--FG-LATEST:START-->' + latest_card() + '<!--FG-LATEST:END-->', html, count=1, flags=re.S)
    bump_sitemap()
    return re.sub(r'<!--FG-OLD:START-->.*?<!--FG-OLD:END-->',
                  lambda _m: '<!--FG-OLD:START-->' + old_list() + '<!--FG-OLD:END-->', html, count=1, flags=re.S)


def add(built, date):
    page = read(built)
    _top, hero, _mid, body, _tail = split_page(page)
    assert body.count('<div') == body.count('</div>'), 'unbalanced article body'
    t = re.search(r'<title>(.*?)</title>', page, re.S).group(1).strip()
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', hero, re.S).group(1).strip()
    base = re.sub(r'-analysis-stats-preview$', '', os.path.basename(built)[:-5])
    pid = '%s-%s' % (base, date)
    hero = re.sub(r'<h1([^>]*)>(.*?)</h1>', r'<h2\1>\2</h2>', hero, count=1, flags=re.S)
    hero = hero.replace('<header class="hero">', '<div class="hero">').replace('</header>', '</div>')
    post = ('<article class="fg-post" id="%s" data-title="%s">\n%s\n%s\n<p><a href="featured-game-of-the-day.html#%s">Link to this breakdown</a></p>\n'
            '</article><!--/fg-post-->\n' % (pid, escape(t), hero, body, pid))
    html = ensure_thread()
    html = re.sub(r'<article class="fg-post" id="%s".*?</article><!--/fg-post-->\n?' % re.escape(pid), '', html, flags=re.S)
    html = html.replace('<!--FG-POSTS:START-->\n', '<!--FG-POSTS:START-->\n' + post, 1)
    data = read(DATA)
    ref = 'featured-game-of-the-day.html#' + pid
    if ref not in data:
        title = h1.replace('"', "'")
        line = '    { date: "%s", page: "%s", title: "%s" },\n' % (date, ref, title)
        marker = '    // ADD NEW FEATURED GAMES HERE'
        data = data.replace(marker, line + marker, 1) if marker in data else data.replace('];', line + '];', 1)
        write(DATA, data)
    write(THREAD, rebuild(html))
    # Keep featured-game-calendar.html's static archive links in step with the data file.
    sys.path.insert(0, os.path.join(REPO, 'scripts'))
    import generate_discovery_artifacts
    generate_discovery_artifacts.update_featured_calendar_static_links()
    print('thread post', pid)


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'build':
        write(THREAD, rebuild(ensure_thread()))
        print('rebuilt', THREAD)
    elif len(sys.argv) == 4 and sys.argv[1] == 'add':
        add(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(2)
