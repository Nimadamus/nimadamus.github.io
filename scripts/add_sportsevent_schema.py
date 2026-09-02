"""
Adds SportsEvent JSON-LD schema to single-game matchup pages.

Safe to run repeatedly — skips pages that already have SportsEvent schema.
Detects matchup pages by filename pattern (*-vs-* or *-at-*) and extracts
teams, sport, and date from the filename. Preserves all existing schema.

Usage:
    python scripts/add_sportsevent_schema.py [file.html]        # single file
    python scripts/add_sportsevent_schema.py --all              # sweep repo
"""
import os, re, sys, glob, json
from datetime import datetime

SPORT_MAP = {
    'nba': 'Basketball',
    'nhl': 'Ice Hockey',
    'mlb': 'Baseball',
    'nfl': 'American Football',
    'ncaab': 'Basketball',
    'college-basketball': 'Basketball',
    'ncaaf': 'American Football',
    'college-football': 'American Football',
    'cfp': 'American Football',
    'cfb': 'American Football',
    'mnf': 'American Football',
    'tnf': 'American Football',
    'snf': 'American Football',
    'soccer': 'Soccer',
    'mls': 'Soccer',
    'premier-league': 'Soccer',
    'champions-league': 'Soccer',
}

MONTHS = {
    'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
    'july':7,'august':8,'september':9,'october':10,'november':11,'december':12
}

SITE_BASE = 'https://www.betlegendpicks.com'

def parse_filename(fname):
    """Return dict with teams, sport, date, or None if not a matchup page."""
    slug = fname.replace('.html','')

    # Find the separator
    if '-vs-' in slug:
        sep = '-vs-'
    elif '-at-' in slug:
        sep = '-at-'
    else:
        return None

    left, right = slug.split(sep, 1)

    # Clean left team: strip leading rank (e.g. "9-alabama" -> "alabama", "1-arizona" -> "arizona")
    left = re.sub(r'^\d+-', '', left)
    away_slug = left  # first team in filename

    # Right side contains second team + context + date tail
    # Strip leading rank on right team too
    right_clean = re.sub(r'^\d+-', '', right)

    # Extract date from the end: "...-month-day-year"
    m = re.search(r'-(' + '|'.join(MONTHS.keys()) + r')-(\d{1,2})-(\d{4})$', right_clean)
    if not m:
        return None
    month_name, day, year = m.group(1), int(m.group(2)), int(m.group(3))
    month = MONTHS[month_name]
    date_iso = f'{year:04d}-{month:02d}-{day:02d}'

    # Body of right side before the date tail
    right_body = right_clean[:m.start()]

    # The second team is the first 1-3 tokens of right_body, before any context keywords
    # Context stop-words — carefully excluding any that are also team names
    # ('wild' = Minnesota Wild, 'vegas' = Vegas Golden Knights, 'kings' = LA Kings/Sac Kings)
    context_words = {'prediction','picks','pick','analysis','stats','preview','mnf','tnf','snf',
                     'cfp','nfc','afc','championship','semifinal','bowl',
                     'showdown','rivalry','series','playoff','playoffs','opener','nba','nhl',
                     'mlb','nfl','ncaab','ncaaf','mls','soccer','and','the','cfb','prop'}
    tokens = right_body.split('-')
    team_tokens = []
    for t in tokens:
        if t in context_words:
            break
        team_tokens.append(t)
        if len(team_tokens) >= 3:
            break
    if not team_tokens:
        return None
    home_slug = '-'.join(team_tokens)

    # Detect sport: scan full slug for a sport keyword
    sport = None
    for key, val in SPORT_MAP.items():
        if f'-{key}-' in f'-{slug}-' or slug.startswith(f'{key}-') or slug.endswith(f'-{key}'):
            sport = val
            break

    def titleize(s):
        # Special cases
        specials = {'ucla':'UCLA','usc':'USC','unc':'UNC','lsu':'LSU','tcu':'TCU','byu':'BYU',
                    'smu':'SMU','ucf':'UCF','utep':'UTEP','unlv':'UNLV','nc':'NC','fau':'FAU',
                    'fiu':'FIU','ulm':'ULM','ull':'ULL','utsa':'UTSA','wku':'WKU'}
        parts = s.split('-')
        out = []
        for p in parts:
            if p in specials:
                out.append(specials[p])
            else:
                out.append(p.capitalize())
        return ' '.join(out)

    return {
        'away': titleize(away_slug),
        'home': titleize(home_slug),
        'sport': sport,
        'date': date_iso,
        'slug': slug,
    }

def build_schema(info, existing_datetime=None):
    start_date = existing_datetime or info['date']
    schema = {
        '@context': 'https://schema.org',
        '@type': 'SportsEvent',
        'name': f"{info['away']} at {info['home']}",
        'startDate': start_date,
        'awayTeam': {'@type':'SportsTeam','name': info['away']},
        'homeTeam': {'@type':'SportsTeam','name': info['home']},
        'url': f"{SITE_BASE}/{info['slug']}.html",
        'eventStatus': 'https://schema.org/EventScheduled',
        'eventAttendanceMode': 'https://schema.org/OfflineEventAttendanceMode',
    }
    if info['sport']:
        schema['sport'] = info['sport']
    return schema

def detect_sport_from_content(content):
    """Fallback sport detection by scanning title and first chunk of body."""
    head = content[:5000].lower()
    # Order matters: check more specific first
    checks = [
        (['nba','national basketball association'], 'Basketball'),
        (['nhl','national hockey league','stanley cup'], 'Ice Hockey'),
        (['mlb','major league baseball','world series','run line'], 'Baseball'),
        (['nfl','national football league','super bowl'], 'American Football'),
        (['ncaab','college basketball','march madness'], 'Basketball'),
        (['ncaaf','college football','cfp','cfb'], 'American Football'),
        (['premier league','la liga','bundesliga','mls','champions league'], 'Soccer'),
    ]
    for keywords, sport in checks:
        for kw in keywords:
            # Word boundary so "nba" doesn't match inside other words
            if re.search(r'\b' + re.escape(kw) + r'\b', head):
                return sport
    return None

def process_file(path, dry_run=False):
    fname = os.path.basename(path)
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Skip redirect stubs
    if 'http-equiv="refresh"' in content or '<title>Redirecting' in content[:1500] or '<title>Page Moved' in content[:1500]:
        return 'skip:redirect'

    # Skip if already has SportsEvent
    if 'SportsEvent' in content:
        return 'skip:already-has-schema'

    info = parse_filename(fname)
    if not info:
        return 'skip:not-matchup'

    # Fallback: if slug didn't name the sport, scan the page content
    if not info['sport']:
        info['sport'] = detect_sport_from_content(content)

    # Try to reuse existing datePublished for a richer startDate
    existing_dt = None
    m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', content)
    if m:
        existing_dt = m.group(1)

    schema = build_schema(info, existing_datetime=existing_dt)
    schema_json = json.dumps(schema, indent=2)
    tag = f'<script type="application/ld+json">\n{schema_json}\n</script>'

    # Insert after the first JSON-LD script (typically NewsArticle), or before </head>
    existing_jsonld = re.search(r'</script>', content)
    if existing_jsonld and 'application/ld+json' in content[:existing_jsonld.end()]:
        insert_at = existing_jsonld.end()
        new_content = content[:insert_at] + '\n' + tag + content[insert_at:]
    else:
        # fallback: insert before </head>
        head_close = content.find('</head>')
        if head_close == -1:
            return 'skip:no-head'
        new_content = content[:head_close] + tag + '\n' + content[head_close:]

    if dry_run:
        return f'ok:would-add team={info["away"]}@{info["home"]} sport={info["sport"]} date={info["date"]}'

    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return f'ok:added team={info["away"]}@{info["home"]}'

def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']

    if not args or args[0] == '--all':
        # Sweep all matchup-pattern files in repo root
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(root)
        files = [f for f in glob.glob('*.html') if re.search(r'-vs-|-at-', f)]
        print(f'Scanning {len(files)} candidate files...')
        counts = {'added':0,'already':0,'not_matchup':0,'redirect':0,'no_head':0}
        errors = []
        for f in sorted(files):
            result = process_file(f, dry_run=dry_run)
            if result.startswith('ok:'): counts['added'] += 1
            elif 'already' in result: counts['already'] += 1
            elif 'not-matchup' in result: counts['not_matchup'] += 1
            elif 'redirect' in result: counts['redirect'] += 1
            elif 'no-head' in result: counts['no_head'] += 1
        print(f'Added SportsEvent schema: {counts["added"]}')
        print(f'Already had schema: {counts["already"]}')
        print(f'Redirect stubs skipped: {counts["redirect"]}')
        print(f'Non-matchup skipped: {counts["not_matchup"]}')
        print(f'Missing <head>: {counts["no_head"]}')
    else:
        for path in args:
            print(f'{path}: {process_file(path, dry_run=dry_run)}')

if __name__ == '__main__':
    main()
