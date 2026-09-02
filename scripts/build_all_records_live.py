#!/usr/bin/env python3
"""Rebuild all-records.json from the LIVE Google Sheets sources.

Mirrors records-engine.js exactly (same URLs, same dedup key
normalized-date|sport|normalized-pick|normalized-line, same tracker-first
precedence, same stake defaults) so the JSON fallback can never drift
from what the browser engine sees live.
"""
import csv, io, json, os, re, urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PICK = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0'
S = {
  'NFL':'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv',
  'NBA':'https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv',
  'NHL':'https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv',
  'MLB':'https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv',
  'NCAAF':'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ9c45xiuXWNe-fAXYMoNb00kCBHfMf4Yn-Xr2LUqdCIiuoiXXDgrDa5mq1PZqxjg8hx-5KnS0L4uVU/pub?output=csv',
  'NCAAB':'https://docs.google.com/spreadsheets/d/e/2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y/pub?output=csv',
  'Soccer':'https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv',
}
D = {'NFL':2,'NBA':1,'NHL':3,'MLB':1,'NCAAF':3,'NCAAB':3,'Soccer':1}
NFL = set(['49ers','bears','bengals','bills','broncos','browns','buccaneers','bucs','cardinals','chargers','chiefs','colts','commanders','cowboys','dolphins','eagles','falcons','giants','jaguars','jets','lions','packers','panthers','patriots','raiders','rams','ravens','saints','seahawks','steelers','texans','titans','vikings','san francisco','chicago','cincinnati','buffalo','denver','cleveland','tampa bay','arizona','kansas city','indianapolis','washington','dallas','philadelphia','atlanta','jacksonville','detroit','green bay','carolina','new england','las vegas','baltimore','new orleans','seattle','pittsburgh','houston','tennessee','minnesota'])
CO = set(['alabama','auburn','clemson','oregon','michigan','ohio state','texas tech','tcu','byu','missouri','army','uconn','new mexico','central michigan','coastal carolina','illinois','miami florida','mississippi','indiana','boise state','memphis','smu','tulane','unlv','fresno state','ole miss','notre dame','penn state','lsu','georgia','florida','florida state','oklahoma','iowa','wisconsin','purdue','northwestern','nebraska','maryland','rutgers','michigan state','james madison','liberty'])


def fetch(u):
    r = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(r, timeout=30).read().decode('utf-8', 'replace')


def nd(s):
    s = str(s or '').strip()
    p = re.split(r'[-/]', s)
    if len(p) != 3:
        return s
    try:
        m, d = int(p[0]), int(p[1])
        ys = p[2].strip()
        if re.match(r'^0\d+$', ys):
            ys = ys.lstrip('0')
        if re.match(r'^\d{3}$', ys) and ys.startswith('20'):
            ys = ys[:2] + '2' + ys[2:]
        y = int(ys)
        if y > 2030 and y < 3000:
            y = int('20' + str(y)[-2:])
        if 2020 <= y <= 2030:
            return '{}/{}/{}'.format(m, d, y)
    except ValueError:
        pass
    return s


def npk(s):
    return re.sub(r'\s+', ' ', str(s or '').strip()).lower()


def nln(s):
    return str(s or '').replace(',', '').strip().lstrip('+')


def po(v):
    try:
        return float(str(v or '').replace('+', '').replace(',', '').strip())
    except ValueError:
        return None


def calc(st, od, r):
    if od is None:
        od = -110.0
    try:
        s = float(st)
    except (TypeError, ValueError):
        s = 0
    r = (r or '').upper().strip()
    if r.startswith('W'):
        return s if od < 0 else s * (od / 100)
    if r.startswith('L'):
        return -s * (abs(od) / 100) if od < 0 else -s
    return 0


def ds(row):
    l = (row.get('League') or '').strip().lower()
    sp = (row.get('Sport') or '').strip().lower()
    if l == 'cross-sport':
        return None
    m = {'nfl': 'NFL', 'nba': 'NBA', 'nhl': 'NHL', 'mlb': 'MLB',
         'ncaaf': 'NCAAF', 'cfb': 'NCAAF', 'ncaab': 'NCAAB', 'cbb': 'NCAAB',
         'soccer': 'Soccer', 'mls': 'Soccer'}
    if l in m:
        return m[l]
    return {'football': 'NFL', 'basketball': 'NBA', 'hockey': 'NHL', 'baseball': 'MLB'}.get(sp)


def parse(text):
    rdr = csv.reader(io.StringIO(text))
    raw = next(rdr, [])
    has = any('result' in (h or '').lower() for h in raw)
    hs = []
    for i, h in enumerate(raw):
        n = (h or '').strip().replace('"', '')
        if n.lower() == 'odds':
            n = 'Line'
        if not n:
            if not has:
                n = 'Result'
                has = True
            else:
                n = 'Column{}'.format(i)
        hs.append(n)
    out = []
    for v in rdr:
        if not any(v) or len(v) < 4:
            continue
        r = {}
        for i, h in enumerate(hs):
            if i < len(v):
                r[h] = v[i].strip()
        if not r.get('Result'):
            for vv in v:
                u = vv.strip().upper()
                if u in ('W', 'L', 'P', 'WIN', 'LOSS', 'PUSH'):
                    r['Result'] = u
                    break
        out.append(r)
    return out


def main():
    tracker = []
    for row in parse(fetch(PICK)):
        sp = ds(row)
        if not sp:
            continue
        r = (row.get('Result') or '').upper().strip()
        if not (r.startswith('W') or r.startswith('L') or r.startswith('P')):
            continue
        pk = (row.get('Pick') or '').strip()
        if sp == 'NFL':
            pl = pk.lower()
            if any(t in pl for t in CO) and not any(t in pl for t in NFL):
                continue
        ln = row.get('Odds') or row.get('Line') or '-110'
        ss = (row.get('Units') or '').strip()
        try:
            st = float(ss) if ss else D[sp]
        except ValueError:
            st = D[sp]
        pl = calc(st, po(ln), r)
        tracker.append({
            'Sport': sp, 'League': row.get('League', ''), 'Date': nd(row.get('Date', '')),
            'Picks': pk, 'Odds': ln, 'Units': '', 'Result': r[0],
            'ProfitLoss': '{:.4f}'.format(pl), 'GradedAt': row.get('PostedAt', '')
        })

    seen = set()
    merged = []
    for r in tracker:
        k = '{}|{}|{}|{}'.format(r['Date'], r['Sport'], npk(r['Picks']), nln(r['Odds']))
        if k in seen:
            continue
        seen.add(k)
        merged.append(r)

    for sp, u in S.items():
        try:
            rows = parse(fetch(u))
        except Exception:
            continue
        for row in rows:
            r = (row.get('Result') or '').upper().strip()
            if not (r.startswith('W') or r.startswith('L') or r.startswith('P')):
                continue
            try:
                pl = float(str(row.get('Units') or '0').replace(',', '').strip())
            except ValueError:
                pl = 0.0
            rec = {
                'Sport': sp, 'League': '', 'Date': nd(row.get('Date', '')),
                'Picks': (row.get('Pick') or '').strip(),
                'Odds': row.get('Line') or row.get('Odds') or '-110',
                'Units': '', 'Result': r[0],
                'ProfitLoss': '{:.4f}'.format(pl), 'GradedAt': ''
            }
            k = '{}|{}|{}|{}'.format(rec['Date'], rec['Sport'], npk(rec['Picks']), nln(rec['Odds']))
            if k in seen:
                continue
            seen.add(k)
            merged.append(rec)

    cs_path = os.path.join(REPO, 'crosssport-parlays-records.html')
    if os.path.exists(cs_path):
        with open(cs_path, encoding='utf-8', errors='ignore') as f:
            html = f.read()
        for tid in ('parlays-table-body', 'teasers-table-body'):
            m = re.search(r'<tbody[^>]+id="' + tid + r'"[^>]*>(.*?)</tbody>', html, re.IGNORECASE | re.DOTALL)
            if not m:
                continue
            for rm in re.finditer(r'<tr>(.*?)</tr>', m.group(1), re.IGNORECASE | re.DOTALL):
                cells = re.findall(r'<td[^>]*>(.*?)</td>', rm.group(1), re.IGNORECASE | re.DOTALL)
                if len(cells) < 6:
                    continue
                st = [re.sub(r'<[^>]+>', '', c).strip() for c in cells[:6]]
                dt, _, pk, od, rs, un = st
                rs = (rs or '').upper().strip()
                rs = rs[0] if rs and rs[0] in ('W', 'L', 'P') else ''
                merged.append({
                    'Sport': 'Cross-Sport', 'League': '', 'Date': nd(dt), 'Picks': pk,
                    'Odds': od, 'Units': '', 'Result': rs,
                    'ProfitLoss': (un or '').replace('+', '').strip(), 'GradedAt': ''
                })

    def sk(row):
        p = re.split(r'[-/]', row['Date'] or '')
        if len(p) == 3:
            try:
                return (int(p[2]), int(p[0]), int(p[1]))
            except ValueError:
                return (0, 0, 0)
        return (0, 0, 0)

    merged.sort(key=sk, reverse=True)

    out = os.path.join(REPO, 'all-records.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2)

    b = defaultdict(lambda: [0, 0, 0, 0.0])
    for r in merged:
        bk = {'W': 0, 'L': 1, 'P': 2}.get(r['Result'])
        if bk is not None:
            b[r['Sport']][bk] += 1
        try:
            b[r['Sport']][3] += float(r['ProfitLoss'])
        except ValueError:
            pass

    print('Wrote {}: {} picks'.format(out, len(merged)))
    for s in ('NFL', 'NBA', 'NHL', 'MLB', 'NCAAF', 'NCAAB', 'Soccer', 'Cross-Sport'):
        w, l, p, u = b[s]
        print('  {}: {}-{}-{}, {:+.2f}u'.format(s, w, l, p, u))


if __name__ == '__main__':
    main()
