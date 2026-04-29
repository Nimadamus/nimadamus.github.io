"""
Categorize every pick in all-records.json by bet type and print
W-L-P / Units / Win% / ROI per (Sport, BetType, Year), plus an
"Other" bucket of uncategorized picks for review.

This mirrors EXACTLY the logic that will run client-side in
records-sport-page.js so the on-page numbers match this verifier.
"""
import json, re, sys, collections, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'all-records.json')

# ---- math (matches records-sport-page.js calculateRisk + calculateStats) ----

def parse_odds(v):
    s = str(v or '').strip().lstrip('+').replace(',', '')
    try: return float(s)
    except: return None

def parse_pl(v):
    s = str(v or '').strip().lstrip('+').replace(',', '')
    try: return float(s)
    except: return 0.0

def parse_year(v):
    raw = str(v or '').strip()
    if not raw: return None
    parts = re.split(r'[-/]', raw)
    if len(parts) != 3: return None
    try:
        m = int(parts[0]); d = int(parts[1]); y = int(parts[2])
    except: return None
    if 0 <= y < 100: y += 2000
    if y > 2030 and y < 3000:
        y = int('20' + str(y)[-2:])
    return y

def calc_risk(odds, pl, result):
    if result == 'P':
        if odds is None: return 1.0
        return 1.0 * (abs(odds)/100) if odds < 0 else 1.0
    if odds is None or pl == 0: return 0.0
    if pl < 0: return abs(pl)
    if odds < 0: return pl * (abs(odds)/100)
    return pl / (odds/100)

# ---- categorizer ----
# Rules per-sport. Order matters: most specific first.

def normalize(p):
    return re.sub(r'\s+', ' ', str(p or '')).strip()

PARLAY_PAT = re.compile(r'\b(parlay|teaser|round robin)\b', re.I)

def category(sport, pick):
    p = normalize(pick)
    pl = p.lower()

    # Use word-boundary checks for "over" / "under" to avoid false positives
    # ("Thunder" contains "under" as a substring).
    has_over  = bool(re.search(r'\bover\b', pl))
    has_under = bool(re.search(r'\bunder\b', pl))

    # ---------- Parlay / teaser ----------
    if 'teaser' in pl: return 'Teaser'
    if 'parlay' in pl: return 'Parlay'
    # Implicit parlay: "X ML, Y ML" or "X ML + Y ML"
    if pl.count(' ml') >= 2 and (',' in pl or '+' in pl):
        return 'Parlay'
    # Implicit parlay: "X Moneyline, Y Moneyline"
    if pl.count('moneyline') >= 2 and (',' in pl or '+' in pl):
        return 'Parlay'

    # ---------- Futures ----------
    if re.search(r'to win (the )?(world series|stanley cup|super bowl|nba finals|world cup|championship|mvp|cy young|nl |al )', pl):
        return 'Futures'

    # ---------- 3-Way / Regulation (NHL) ----------
    if sport == 'NHL' and 'regulation' in pl and 'win' in pl:
        return '3-Way / Regulation'

    # ---------- Sport-specific period bets ----------
    if sport == 'MLB':
        if re.search(r'\b(f5|first 5|first five)\b', pl):
            if has_over or has_under: return 'F5 Total'
            return 'F5 Moneyline'
        if re.search(r'\b(nrfi|yrfi)\b', pl):
            return 'NRFI/YRFI'
    if sport in ('NBA', 'NCAAB'):
        if re.search(r'\b(1st half|first half|2nd half|second half|1h|2h)\b', pl):
            if has_over or has_under: return '1H/2H Total'
            return '1H/2H Spread'

    # ---------- Soccer corners ----------
    if sport == 'Soccer' and 'corner' in pl:
        return 'Corners O/U'

    # ---------- Team Total ----------
    if 'team total' in pl:
        if has_over:  return 'Team Total Over'
        if has_under: return 'Team Total Under'
        return 'Team Total'

    # ---------- Game Total ----------
    # "X/Y over N" / "X/Y under N" / bare "over N" / bare "under N"
    if has_over or has_under:
        if has_over and not has_under: return 'Game Total Over'
        if has_under and not has_over: return 'Game Total Under'

    # ---------- Moneyline ----------
    # Explicit "ML" suffix, full word "Moneyline", or "ML +" parlays already
    # caught above. Also bare team names with odds (no spread/total markers)
    # fall through to here.
    if re.search(r'\bml\b', pl) or 'moneyline' in pl or pl.endswith(' ml'):
        return 'Moneyline'

    # Spread / Puck Line / Run Line: contains +/- followed by digits
    if re.search(r'[+-]\d+(\.\d+)?\b', p):
        if sport == 'NHL': return 'Puck Line'
        if sport == 'MLB': return 'Run Line'
        return 'Spread'

    # Pickem
    if re.search(r'\bpk\b', pl) and sport in ('NBA','NFL','NCAAB','NCAAF'):
        return 'Spread'

    # Bare team name with odds → assume Moneyline (validated against odds present in row)
    # We don't have odds here, so just default these to Moneyline. The verifier
    # only treats this as ML if the picker matches no other rule. Most "bare team"
    # rows in the tracker are full-game ML.
    if re.match(r'^[A-Za-z\.\s]+$', p):
        return 'Moneyline'

    return 'Other'

# Display order per sport (Total appears as a synthetic last row inside each group)
GROUPS = {
    'NHL': [
        ('Moneyline', ['Moneyline']),
        ('Puck Line', ['Puck Line']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('3-Way / Regulation', ['3-Way / Regulation']),
        ('Parlays', ['Parlay', 'Teaser']),
        ('Other', ['Other']),
    ],
    'MLB': [
        ('Moneyline', ['Moneyline']),
        ('Run Line', ['Run Line']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('First 5 Innings', ['F5 Moneyline', 'F5 Total']),
        ('NRFI / YRFI', ['NRFI/YRFI']),
        ('Futures', ['Futures']),
        ('Parlays', ['Parlay', 'Teaser']),
        ('Other', ['Other']),
    ],
    'NFL': [
        ('Moneyline', ['Moneyline']),
        ('Spread', ['Spread']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('Teasers / Parlays', ['Teaser', 'Parlay']),
        ('Other', ['Other']),
    ],
    'NCAAF': [
        ('Moneyline', ['Moneyline']),
        ('Spread', ['Spread']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('Teasers / Parlays', ['Teaser', 'Parlay']),
        ('Other', ['Other']),
    ],
    'NBA': [
        ('Moneyline', ['Moneyline']),
        ('Spread', ['Spread']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('1st / 2nd Half', ['1H/2H Spread', '1H/2H Total']),
        ('Parlays / Teasers', ['Parlay', 'Teaser']),
        ('Other', ['Other']),
    ],
    'NCAAB': [
        ('Moneyline', ['Moneyline']),
        ('Spread', ['Spread']),
        ('Game Totals', ['Game Total Over', 'Game Total Under']),
        ('Team Totals', ['Team Total Over', 'Team Total Under']),
        ('1st / 2nd Half', ['1H/2H Spread', '1H/2H Total']),
        ('Parlays / Teasers', ['Parlay', 'Teaser']),
        ('Other', ['Other']),
    ],
    'Soccer': [
        ('Moneyline / 3-Way', ['Moneyline']),
        ('Goals O/U', ['Game Total Over', 'Game Total Under']),
        ('Corners O/U', ['Corners O/U']),
        ('Parlays', ['Parlay', 'Teaser']),
        ('Other', ['Other']),
    ],
}

YEARS = [2025, 2026]

def aggregate(rows, key_fn):
    buckets = collections.defaultdict(lambda: {'W':0,'L':0,'P':0,'units':0.0,'risk':0.0})
    for r in rows:
        k = key_fn(r)
        if k is None: continue
        b = buckets[k]
        res = r['result']
        if res in b: b[res] += 1
        b['units'] += r['pl']
        b['risk'] += r['risk']
    return buckets

def fmt_row(b):
    g = b['W'] + b['L']
    win_pct = (b['W']/g*100) if g else 0.0
    roi = (b['units']/b['risk']*100) if b['risk'] else 0.0
    units = b['units']
    sign = '+' if units >= 0 else ''
    rsign = '+' if roi >= 0 else ''
    return f"{b['W']}-{b['L']}-{b['P']}  {sign}{units:.2f}u  {win_pct:.1f}%  {rsign}{roi:.2f}%"

def main():
    with open(DATA) as fh: data = json.load(fh)
    rows = []
    for r in data:
        sport = (r.get('Sport') or r.get('sport') or '').strip()
        pick = r.get('Picks') or r.get('Pick') or r.get('pick') or ''
        odds = parse_odds(r.get('Odds') or r.get('Line') or r.get('line'))
        pl = parse_pl(r.get('ProfitLoss') or r.get('Units') or r.get('unitPL') or 0)
        result = (str(r.get('Result') or r.get('result') or '').strip().upper()[:1])
        if not result or result not in 'WLP': continue
        year = parse_year(r.get('Date') or r.get('date'))
        cat = category(sport, pick)
        rows.append({
            'sport':sport,'pick':pick,'odds':odds,'pl':pl,'result':result,
            'year':year,'cat':cat,'risk':calc_risk(odds,pl,result),
        })

    for sport in ('NHL','MLB','NFL','NCAAF','NBA','NCAAB','Soccer'):
        srows = [r for r in rows if r['sport']==sport]
        print('='*78)
        print(f'{sport}  ({len(srows)} graded picks)')
        print('='*78)
        groups = GROUPS.get(sport, [])
        for label, cats in groups:
            ggroup = [r for r in srows if r['cat'] in cats]
            if not ggroup:
                continue
            print(f'\n  {label}')
            # sub-rows
            for c in cats:
                cgroup = [r for r in ggroup if r['cat']==c]
                if not cgroup: continue
                print(f'    {c:24s}', end='  ')
                cells = []
                for y in YEARS:
                    yrows = [r for r in cgroup if r['year']==y]
                    if yrows:
                        agg = aggregate(yrows, lambda r:'k')
                        cells.append(f'{y}: {fmt_row(agg["k"])}')
                    else:
                        cells.append(f'{y}: -')
                tot = aggregate(cgroup, lambda r:'k')
                cells.append(f'TOTAL: {fmt_row(tot["k"])}')
                print('  |  '.join(cells))
            # group total (sums all sub-cats)
            print(f'    {"TOTAL ("+label+")":24s}', end='  ')
            cells = []
            for y in YEARS:
                yrows = [r for r in ggroup if r['year']==y]
                if yrows:
                    agg = aggregate(yrows, lambda r:'k')
                    cells.append(f'{y}: {fmt_row(agg["k"])}')
                else:
                    cells.append(f'{y}: -')
            tot = aggregate(ggroup, lambda r:'k')
            cells.append(f'TOTAL: {fmt_row(tot["k"])}')
            print('  |  '.join(cells))

        # Show "Other" bucket sample picks for review
        other = [r for r in srows if r['cat']=='Other']
        if other:
            print(f'\n  --- "Other" picks ({len(other)}) — sample ---')
            seen=set()
            for r in other:
                if r['pick'] in seen: continue
                seen.add(r['pick'])
                print(f'      {r["pick"]}  ({r["odds"]})  {r["result"]}  {r["pl"]}')
                if len(seen) >= 25: break
        print()

if __name__ == '__main__':
    main()
