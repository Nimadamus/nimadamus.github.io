#!/usr/bin/env python3
"""
refresh_preview_hubs.py - Re-bake each rolling sport preview hub from the
newest concrete standalone preview page. (June 6, 2026)

WHY THIS EXISTS
---------------
Hub freshness used to come from two places and BOTH silently died:
  1. SLATE manually refreshed hubs ("SLATE May 19: refresh sport-preview
     hubs with today's content" was the last one) until slate.md gained a
     blanket "DO NOT overwrite hub pages" rule.
  2. scripts/auto_content/main.py (7:30 AM task) generates content through
     the Anthropic API, which has been failing every call since the API
     credit balance ran out ("credit balance is too low", 4,200+ errors in
     auto_content_log.txt). It now commits only its own log.
Result: mlb/nba/soccer-previews.html froze on the 2026-05-19 bake.

This script needs NO API and NO model: the standalone preview pages that
SLATE already publishes are the verified content source. It copies the
newest concrete preview's hero + <article class="game-preview"> blocks into
the matching hub and sets window.FORCED_PAGE_DATE to that page's post date.

It deliberately touches NOTHING else in the hub: title/meta stay stable and
dateless (June 6 2026 standard), nav/calendar/canonical/guards untouched.

USAGE
  python scripts/refresh_preview_hubs.py            # refresh stale hubs
  python scripts/refresh_preview_hubs.py --dry-run  # report only, no writes
  python scripts/refresh_preview_hubs.py --commit   # + git add/commit/push

After a non-dry run that changed files, run scripts/sync_calendars.py (the
--commit path does it automatically; the pre-commit hook re-runs it anyway).
"""
import argparse
import os
import re
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# sport key -> (hub file, calendar js)
SPORTS = {
    'mlb': ('mlb-previews.html', 'scripts/mlb-calendar.js'),
    'nba': ('nba-previews.html', 'scripts/nba-calendar.js'),
    'nhl': ('nhl-previews.html', 'scripts/nhl-calendar.js'),
    'soccer': ('soccer-previews.html', 'scripts/soccer-calendar.js'),
    'ncaab': ('college-basketball-previews.html', 'scripts/ncaab-calendar.js'),
}

# Mirrors MAIN_PAGES / isConcreteContentPage in the generated calendar JS:
# never treat a hub, archive page, or pick page as a bake source.
HUB_PAGES = {hub for hub, _ in SPORTS.values()} | {
    'nfl.html', 'ncaaf.html', 'nba.html', 'nhl.html', 'mlb.html',
    'soccer.html', 'ncaab.html',
}
PICK_RE = re.compile(r'-picks?(?:-v\d+)?\.html$')

ENTRY_RE = re.compile(
    r'\{\s*date:\s*"(\d{4}-\d{2}-\d{2})"\s*,\s*page:\s*"([^"]+)"\s*,\s*title:\s*"([^"]*)"'
)
ARTICLE_RE = re.compile(r'<article class="game-preview[^"]*">.*?</article>', re.S)
FPD_RE = re.compile(r"window\.FORCED_PAGE_DATE\s*=\s*'(\d{4}-\d{2}-\d{2})'")
HERO_RE = re.compile(r'(<header class="hero">)(.*?)(</header>)', re.S)
BADGE_RE = re.compile(r'(<div class="hero-badge">)(.*?)(</div>)', re.S)
H1_RE = re.compile(r'(<h1[^>]*>)(.*?)(</h1>)', re.S)
HERO_P_RE = re.compile(r'(<p[^>]*>)(.*?)(</p>)', re.S)


def read(path):
    with open(path, 'rb') as f:
        return f.read().decode('utf-8')


def write(path, text):
    # bytes round-trip: never lets Windows text mode flip LF -> CRLF
    with open(path, 'wb') as f:
        f.write(text.encode('utf-8'))


def is_concrete(page):
    return (
        page
        and page not in HUB_PAGES
        and '#' not in page
        and '-archive-' not in page
        and not PICK_RE.search(page)
        # Featured Game pages route through Featured Game surfaces only
        # (repo CLAUDE.md routing rule) - never bake one in as a sport board.
        and '-analysis-stats-preview' not in page
    )


def pick_primary(entries):
    """Same heuristic as pickPrimaryPostForDate in the calendar JS."""
    for it in entries:
        t = it['title'].lower()
        p = it['page'].lower()
        if re.search(r'\banalysis\b|\bpreview\b|\bslate\b|\bboard\b|\bfull card\b', t) \
           or re.search(r'-game-|-slate-|-board-|-previews|full-card', p):
            return it
    return entries[0]


def source_candidates(cal_path):
    """Newest-first candidate list: primary pick first within each date."""
    entries = [
        {'date': d, 'page': p, 'title': t}
        for d, p, t in ENTRY_RE.findall(read(cal_path))
        if is_concrete(p) and os.path.exists(os.path.join(REPO, p))
    ]
    out = []
    for date in sorted({e['date'] for e in entries}, reverse=True):
        day = [e for e in entries if e['date'] == date]
        primary = pick_primary(day)
        out.append(primary)
        out.extend(e for e in day if e is not primary)
    return out


def refresh_hub(sport, hub_file, cal_js, dry_run):
    hub_path = os.path.join(REPO, hub_file)
    candidates = source_candidates(os.path.join(REPO, cal_js))
    if not candidates:
        print(f"[{sport}] SKIP - no concrete source page in {cal_js}")
        return None

    hub = read(hub_path)
    m = FPD_RE.search(hub)
    hub_date = m.group(1) if m else None

    src = articles = source = None
    for cand in candidates:
        if hub_date and hub_date >= cand['date']:
            print(f"[{sport}] FRESH - hub {hub_date} >= newest preview "
                  f"{cand['date']} ({cand['page']})")
            return None
        text = read(os.path.join(REPO, cand['page']))
        found = ARTICLE_RE.findall(text)
        if found:
            src, articles, source = cand, found, text
            break
        print(f"[{sport}] skipping candidate {cand['page']} - no game-preview articles")
    if not src:
        print(f"[{sport}] SKIP - no candidate newer than {hub_date} has articles")
        return None

    # --- swap the article block region (first article .. last </article>) ---
    first = hub.find('<article class="game-preview')
    if first == -1:
        print(f"[{sport}] SKIP - hub has no game-preview region to replace")
        return None
    tail_marker = hub.find('<!-- BEGIN MONTHLY-ARCHIVES')
    if tail_marker == -1:
        tail_marker = hub.find('</main>')
    last = hub.rfind('</article>', first, tail_marker)
    if last == -1:
        print(f"[{sport}] SKIP - hub article region malformed")
        return None
    new_hub = hub[:first] + '\n\n'.join(articles) + hub[last + len('</article>'):]

    # --- FORCED_PAGE_DATE = source post date ---
    new_hub = FPD_RE.sub(f"window.FORCED_PAGE_DATE = '{src['date']}'", new_hub, count=1)

    # --- hero (badge/h1/p) from source, structure-tolerant: skip on mismatch ---
    hub_hero = HERO_RE.search(new_hub)
    src_hero = HERO_RE.search(source)
    if hub_hero and src_hero:
        hero = hub_hero.group(2)
        for rx in (BADGE_RE, H1_RE, HERO_P_RE):
            hm, sm = rx.search(hero), rx.search(src_hero.group(2))
            if hm and sm:
                hero = hero[:hm.start(2)] + sm.group(2) + hero[hm.end(2):]
        new_hub = new_hub[:hub_hero.start(2)] + hero + new_hub[hub_hero.end(2):]

    # --- JSON-LD dateModified, when present ---
    new_hub = re.sub(r'("dateModified":")\d{4}-\d{2}-\d{2}',
                     r'\g<1>' + src['date'], new_hub, count=1)

    # --- sanity gates before writing ---
    if FPD_RE.search(new_hub).group(1) != src['date']:
        print(f"[{sport}] ABORT - FORCED_PAGE_DATE did not update")
        return None
    n = len(ARTICLE_RE.findall(new_hub))
    if n != len(articles):
        print(f"[{sport}] ABORT - article count mismatch ({n} != {len(articles)})")
        return None

    action = 'WOULD UPDATE' if dry_run else 'UPDATED'
    print(f"[{sport}] {action} {hub_file}: {hub_date} -> {src['date']}, "
          f"{len(articles)} articles from {src['page']}")
    if not dry_run:
        write(hub_path, new_hub)
    return hub_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--commit', action='store_true',
                    help='git add/commit/pull --rebase/push the refreshed hubs')
    args = ap.parse_args()

    changed = []
    for sport, (hub_file, cal_js) in SPORTS.items():
        try:
            out = refresh_hub(sport, hub_file, cal_js, args.dry_run)
            if out:
                changed.append(out)
        except Exception as e:  # one sport failing must not kill the others
            print(f"[{sport}] ERROR - {e}")

    if args.dry_run or not changed:
        print(f"\nDone. {len(changed)} hub(s) {'would be ' if args.dry_run else ''}refreshed.")
        return 0

    subprocess.run([sys.executable, os.path.join(REPO, 'scripts', 'sync_calendars.py')],
                   cwd=REPO, check=True)
    if args.commit:
        subprocess.run(['git', 'add'] + changed +
                       ['scripts/', 'featured-games-data.js'], cwd=REPO, check=True)
        subprocess.run(['git', 'commit', '-m',
                        'Refresh sport preview hubs from latest standalone previews (auto)'],
                       cwd=REPO, check=True)
        subprocess.run(['git', 'pull', '--rebase'], cwd=REPO, check=True)
        subprocess.run(['git', 'push'], cwd=REPO, check=True)
    print(f"\nDone. Refreshed: {', '.join(changed)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
