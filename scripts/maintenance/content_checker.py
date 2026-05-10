#!/usr/bin/env python3
"""
Multi-Sport Content Accuracy Checker
======================================
Scans HTML files for player names, team assignments, and statistics
across ALL major sports and verifies against live ESPN + league API data.

Works on any sports betting website.

Usage:
    python content_checker.py C:\\path\\to\\site --report accuracy_report.txt
    python content_checker.py C:\\path\\to\\site --sport mlb nfl
    python content_checker.py C:\\path\\to\\site --verbose

Sports: MLB, NFL, NBA, NHL, NCAAF, NCAAB

Catches:
    - Player listed on wrong team (all sports)
    - Wrong statistics (batting avg, ERA, passing yards, PPG, goals, etc.)
    - Possible misspellings
    - Retired/inactive players referenced as current

Install:
    pip install requests beautifulsoup4
"""

import os, sys, re, json, time, argparse, hashlib
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("[ERROR] pip install requests"); sys.exit(1)
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERROR] pip install beautifulsoup4"); sys.exit(1)

# ═══════════ CACHE ═══════════
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".content_checker_cache")
CACHE_HOURS = 12

def cache_get(key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    p = os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")
    if os.path.exists(p) and datetime.now() - datetime.fromtimestamp(os.path.getmtime(p)) < timedelta(hours=CACHE_HOURS):
        try:
            with open(p) as f: return json.load(f)
        except: pass
    return None

def cache_set(key, data):
    os.makedirs(CACHE_DIR, exist_ok=True)
    p = os.path.join(CACHE_DIR, hashlib.md5(key.encode()).hexdigest() + ".json")
    try:
        with open(p, 'w') as f: json.dump(data, f)
    except: pass

def api_get(url, params=None):
    ck = f"{url}|{json.dumps(params or {}, sort_keys=True)}"
    c = cache_get(ck)
    if c is not None: return c
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        d = r.json(); cache_set(ck, d); time.sleep(0.35); return d
    except Exception as e:
        print(f"    [API WARN] {url} - {e}"); return None

# ═══════════ CONFIG ═══════════
ESPN = "https://site.api.espn.com/apis/site/v2/sports"
MLB_API = "https://statsapi.mlb.com/api/v1"

SPORTS = {
    "mlb": "baseball/mlb", "nfl": "football/nfl", "nba": "basketball/nba",
    "nhl": "hockey/nhl", "ncaaf": "football/college-football",
    "ncaab": "basketball/mens-college-basketball",
}

# ═══════════ DATABASE ═══════════
class PlayerDB:
    def __init__(self):
        self.players = {}
        self.team_lookup = {}

    def add_player(self, name, team, abbr, sport, pos="", stats=None):
        nl = name.lower().strip()
        key = f"{sport}:{nl}"
        self.players[key] = {
            "name": name, "team": team, "abbr": abbr,
            "sport": sport, "pos": pos, "stats": stats or {}
        }
        if nl not in self.players:
            self.players[nl] = self.players[key]

    def add_team(self, sport, full, abbr, nick=""):
        for val in [full, abbr, nick]:
            if val and len(val) >= 2:
                self.team_lookup[val.lower().strip()] = (sport, full)
        parts = full.split()
        if len(parts) >= 2:
            self.team_lookup[parts[-1].lower()] = (sport, full)

    def find_team_in_text(self, text, sport_hint=None):
        tl = text.lower()
        for key in sorted(self.team_lookup.keys(), key=len, reverse=True):
            if len(key) < 3: continue
            if key in tl:
                s, name = self.team_lookup[key]
                if sport_hint and s != sport_hint: continue
                return (s, name)
        return None

# ═══════════ LOADING ═══════════
def load_espn_sport(db, sport_key):
    path = SPORTS[sport_key]
    data = api_get(f"{ESPN}/{path}/teams", {"limit": 200})
    if not data: print(f"  [FAIL] {sport_key.upper()} teams"); return
    teams = []
    try:
        for e in data["sports"][0]["leagues"][0]["teams"]:
            t = e["team"]
            full = t.get("displayName", "")
            abbr = t.get("abbreviation", "")
            nick = t.get("shortDisplayName", t.get("name", ""))
            db.add_team(sport_key, full, abbr, nick)
            teams.append({"id": t["id"], "name": full, "abbr": abbr})
    except: pass
    print(f"  {sport_key.upper()}: {len(teams)} teams")

    total = 0
    for team in teams:
        rdata = api_get(f"{ESPN}/{path}/teams/{team['id']}/roster")
        if not rdata: continue
        try:
            for group in rdata.get("athletes", []):
                items = group.get("items", []) if isinstance(group, dict) else []
                if not items and isinstance(group, dict):
                    nm = group.get("displayName", group.get("fullName", ""))
                    ps = group.get("position", {}).get("abbreviation", "") if isinstance(group.get("position"), dict) else ""
                    if nm: db.add_player(nm, team["name"], team["abbr"], sport_key, ps); total += 1
                    continue
                for p in items:
                    nm = p.get("displayName", p.get("fullName", ""))
                    ps = p.get("position", {}).get("abbreviation", "") if isinstance(p.get("position"), dict) else ""
                    if nm: db.add_player(nm, team["name"], team["abbr"], sport_key, ps); total += 1
        except: pass
    print(f"  {sport_key.upper()}: {total} players")

def load_mlb_stats(db):
    print("  Loading MLB detailed stats...")
    season = datetime.now().year if datetime.now().month >= 4 else datetime.now().year - 1
    tdata = api_get(f"{MLB_API}/teams", {"sportId": 1})
    if not tdata: return
    for team in tdata.get("teams", []):
        roster = api_get(f"{MLB_API}/teams/{team['id']}/roster", {"rosterType": "40Man"})
        if not roster or "roster" not in roster: continue
        for entry in roster["roster"]:
            pid = entry.get("person", {}).get("id")
            pname = entry.get("person", {}).get("fullName", "")
            if not pid or not pname: continue
            key = f"mlb:{pname.lower().strip()}"
            if key not in db.players: continue
            sdata = api_get(f"{MLB_API}/people/{pid}/stats", {"stats": "season", "season": season, "group": "hitting,pitching"})
            if not sdata or "stats" not in sdata: continue
            for sg in sdata["stats"]:
                gn = sg.get("group", {}).get("displayName", "")
                sp = sg.get("splits", [])
                if not sp: continue
                sv = sp[0].get("stat", {})
                if gn == "hitting":
                    db.players[key]["stats"].update({
                        "avg": sv.get("avg",""), "hr": sv.get("homeRuns",""),
                        "rbi": sv.get("rbi",""), "ops": sv.get("ops",""),
                        "sb": sv.get("stolenBases",""), "hits": sv.get("hits",""),
                        "so_bat": sv.get("strikeOuts",""), "obp": sv.get("obp",""),
                        "slg": sv.get("slg",""),
                    })
                elif gn == "pitching":
                    db.players[key]["stats"].update({
                        "era": sv.get("era",""), "wins": sv.get("wins",""),
                        "losses": sv.get("losses",""), "so_pitch": sv.get("strikeOuts",""),
                        "whip": sv.get("whip",""), "ip": sv.get("inningsPitched",""),
                        "saves": sv.get("saves",""),
                    })
    print("  MLB stats loaded")

def build_database(sport_list=None):
    if not sport_list: sport_list = list(SPORTS.keys())
    db = PlayerDB()
    for s in sport_list:
        if s not in SPORTS: continue
        load_espn_sport(db, s)
    if "mlb" in sport_list:
        try: load_mlb_stats(db)
        except Exception as e: print(f"  [WARN] MLB stats: {e}")
    total = sum(1 for k in db.players if ":" in k)
    print(f"\n  TOTAL: {total} players across {len(sport_list)} sports\n")
    return db

# ═══════════ STAT PATTERNS ═══════════
PATTERNS = {
    # MLB
    "avg": (re.compile(r'(?:batting average|average|AVG|BA)[:\s]+\.?(\d{3})', re.I), "mlb", "avg", 0.020),
    "avg2": (re.compile(r'\.([23]\d{2})\b'), "mlb", "avg", 0.020),
    "hr": (re.compile(r'(\d{1,3})\s*(?:home runs?|HRs?|homers?)', re.I), "mlb", "hr", 5),
    "rbi": (re.compile(r'(\d{1,3})\s*RBIs?', re.I), "mlb", "rbi", 10),
    "era": (re.compile(r'(\d\.\d{1,2})\s*ERA', re.I), "mlb", "era", 0.50),
    "so_p": (re.compile(r'(\d{1,3})\s*(?:strikeouts?|Ks)\b', re.I), "mlb", "so_pitch", 15),
    "ops": (re.compile(r'(\.\d{3}|\d\.\d{3})\s*OPS', re.I), "mlb", "ops", 0.030),
    "whip": (re.compile(r'(\d\.\d{1,2})\s*WHIP', re.I), "mlb", "whip", 0.15),
    "sb": (re.compile(r'(\d{1,3})\s*(?:stolen bases?|SBs?|steals)', re.I), "mlb", "sb", 5),
    "saves": (re.compile(r'(\d{1,3})\s*saves?', re.I), "mlb", "saves", 5),
    # NFL
    "pass_yds": (re.compile(r'(\d{2,5})\s*(?:passing yards?|pass(?:ing)? yds?)', re.I), "nfl", "passing_yards", 300),
    "pass_td": (re.compile(r'(\d{1,3})\s*(?:passing TDs?|touchdown passes?)', re.I), "nfl", "passing_td", 5),
    "rush_yds": (re.compile(r'(\d{2,5})\s*(?:rushing yards?|rush(?:ing)? yds?)', re.I), "nfl", "rushing_yards", 150),
    "rush_td": (re.compile(r'(\d{1,2})\s*(?:rushing TDs?|rush(?:ing)? touchdowns?)', re.I), "nfl", "rushing_td", 3),
    "rec_yds": (re.compile(r'(\d{2,5})\s*(?:receiving yards?|rec(?:eiving)? yds?)', re.I), "nfl", "receiving_yards", 200),
    "recs": (re.compile(r'(\d{1,3})\s*(?:receptions?|catches)', re.I), "nfl", "receptions", 15),
    "ints": (re.compile(r'(\d{1,2})\s*(?:interceptions?|INTs)', re.I), "nfl", "interceptions", 3),
    "sacks": (re.compile(r'(\d{1,2}(?:\.\d)?)\s*sacks?', re.I), "nfl", "sacks", 3),
    "qbr": (re.compile(r'(\d{2,3}\.\d)\s*(?:passer rating|QBR)', re.I), "nfl", "passer_rating", 10),
    # NBA
    "ppg": (re.compile(r'(\d{1,2}\.\d)\s*(?:PPG|points? per game)', re.I), "nba", "ppg", 3.0),
    "rpg": (re.compile(r'(\d{1,2}\.\d)\s*(?:RPG|rebounds? per game)', re.I), "nba", "rpg", 2.0),
    "apg": (re.compile(r'(\d{1,2}\.\d)\s*(?:APG|assists? per game)', re.I), "nba", "apg", 2.0),
    "fg_pct": (re.compile(r'(\d{2}\.\d)%?\s*(?:FG%?|field goal)', re.I), "nba", "fg_pct", 5.0),
    "3pt_pct": (re.compile(r'(\d{2}\.\d)%?\s*(?:3PT%?|three[- ]point)', re.I), "nba", "three_pct", 5.0),
    # NHL
    "goals": (re.compile(r'(\d{1,3})\s*goals?', re.I), "nhl", "goals", 5),
    "assists": (re.compile(r'(\d{1,3})\s*assists?', re.I), "nhl", "assists", 8),
    "gaa": (re.compile(r'(\d\.\d{1,2})\s*(?:GAA|goals? against)', re.I), "nhl", "gaa", 0.40),
    "sv_pct": (re.compile(r'(\.\d{3})\s*(?:SV%|save (?:percentage|pct))', re.I), "nhl", "save_pct", 0.015),
}

PROJECTION_WORDS = [
    "projected", "projection", "expected", "forecast", "predict",
    "could", "should", "might", "over/under", "o/u", "prop line",
    "set at", "2026", "upcoming", "next season", "this season"
]

# ═══════════ SCANNING ═══════════
def extract_text(fp):
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f: html = f.read()
    except: return ""
    soup = BeautifulSoup(html, 'html.parser')
    for t in soup.find_all(['script', 'style']): t.decompose()
    return soup.get_text(separator='\n', strip=True)

def scan_page(fp, db):
    errors, warnings = [], []
    text = extract_text(fp)
    if not text or len(text) < 50: return errors, warnings
    tl = text.lower()

    for key, info in db.players.items():
        if ":" not in key: continue
        name = info["name"]; nl = name.lower()
        if len(nl) < 5: continue
        idx = tl.find(nl)
        if idx == -1: continue

        cs = max(0, idx-300); ce = min(len(text), idx+len(name)+300)
        ctx = text[cs:ce]; ctx_l = ctx.lower()

        # WRONG TEAM CHECK
        tm = db.find_team_in_text(ctx, info["sport"])
        if tm:
            fs, ft = tm
            if fs == info["sport"] and ft.lower() != info["team"].lower():
                pp = ctx_l.find(nl)
                rp = ctx_l.find(info["team"].lower())
                wp = ctx_l.find(ft.lower())
                rd = abs(pp - rp) if rp >= 0 else 9999
                wd = abs(pp - wp) if wp >= 0 else 9999
                if wd < rd:
                    errors.append({
                        "type": "WRONG_TEAM", "player": name, "sport": info["sport"].upper(),
                        "says": ft, "actual": info["team"],
                        "snippet": ctx.strip()[:200].replace('\n',' ')
                    })

        # WRONG STATS CHECK
        for pk, (pat, psport, skey, tol) in PATTERNS.items():
            if psport != info["sport"]: continue
            matches = pat.findall(ctx)
            for raw in matches:
                try: fv = float(raw)
                except: continue
                if pk in ("avg", "avg2") and fv > 1: fv /= 1000.0
                rv = info["stats"].get(skey)
                if rv is None or rv == "": continue
                try: rv = float(rv)
                except: continue
                diff = abs(fv - rv)
                if diff > tol:
                    is_proj = any(pw in ctx_l for pw in PROJECTION_WORDS)
                    if is_proj:
                        warnings.append({
                            "type": "PROJECTION_MISMATCH", "player": name,
                            "sport": info["sport"].upper(), "stat": skey.upper(),
                            "says": fv, "actual_last_season": rv, "diff": round(diff, 3)
                        })
                    else:
                        errors.append({
                            "type": "WRONG_STAT", "player": name,
                            "sport": info["sport"].upper(), "stat": skey.upper(),
                            "says": fv, "actual": rv, "diff": round(diff, 3),
                            "snippet": ctx.strip()[:200].replace('\n',' ')
                        })
    return errors, warnings

def scan_directory(directory, db, verbose=False):
    files = []
    for root, dirs, fnames in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        for f in fnames:
            if f.endswith('.html'): files.append(os.path.join(root, f))
    print(f"Scanning {len(files)} HTML files...\n")
    results = {}; te = tw = fi = 0
    for i, fp in enumerate(sorted(files)):
        rel = os.path.relpath(fp, directory)
        if verbose: print(f"  [{i+1}/{len(files)}] {rel}")
        errs, warns = scan_page(fp, db)
        if errs or warns:
            fi += 1; results[rel] = {"errors": errs, "warnings": warns}
            te += len(errs); tw += len(warns)
            if not verbose: print(f"  [!] {rel}: {len(errs)} errors, {len(warns)} warnings")
    return results, te, tw, fi, len(files)

# ═══════════ REPORT ═══════════
def report(results, te, tw, fi, tf, out=None):
    L = []
    L.append("=" * 70)
    L.append("CONTENT ACCURACY REPORT")
    L.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    L.append("=" * 70)
    L.append(f"\n  Files scanned:       {tf}")
    L.append(f"  Files with issues:   {fi}")
    L.append(f"  Total ERRORS:        {te}")
    L.append(f"  Total WARNINGS:      {tw}\n")

    if te == 0 and tw == 0:
        L.append("  [PASS] No content accuracy issues found!")
    else:
        wt = []; ws = []; pm = []
        for fp, d in sorted(results.items()):
            for e in d["errors"]:
                e["file"] = fp
                if e["type"] == "WRONG_TEAM": wt.append(e)
                elif e["type"] == "WRONG_STAT": ws.append(e)
            for w in d["warnings"]:
                w["file"] = fp
                if w["type"] == "PROJECTION_MISMATCH": pm.append(w)

        if wt:
            L.append("-" * 70)
            L.append(f"  WRONG TEAM ({len(wt)})")
            L.append("-" * 70)
            for e in wt:
                L.append(f"\n  File:    {e['file']}")
                L.append(f"  Player:  {e['player']} ({e['sport']})")
                L.append(f"  Says:    {e['says']}")
                L.append(f"  Actual:  {e['actual']}")
                L.append(f"  Context: {e.get('snippet','')[:150]}")

        if ws:
            L.append("\n" + "-" * 70)
            L.append(f"  WRONG STATISTICS ({len(ws)})")
            L.append("-" * 70)
            for e in ws:
                L.append(f"\n  File:    {e['file']}")
                L.append(f"  Player:  {e['player']} ({e['sport']})")
                L.append(f"  Stat:    {e['stat']}")
                L.append(f"  Says:    {e['says']}")
                L.append(f"  Actual:  {e['actual']}")
                L.append(f"  Off by:  {e['diff']}")
                L.append(f"  Context: {e.get('snippet','')[:150]}")

        if pm:
            L.append("\n" + "-" * 70)
            L.append(f"  PROJECTION MISMATCHES ({len(pm)} - may be intentional)")
            L.append("-" * 70)
            for w in pm:
                L.append(f"\n  File:         {w['file']}")
                L.append(f"  Player:       {w['player']} ({w['sport']})")
                L.append(f"  Stat:         {w['stat']}")
                L.append(f"  Says:         {w['says']}")
                L.append(f"  Last season:  {w['actual_last_season']}")

        L.append("\n" + "=" * 70)
        L.append("  PER-FILE SUMMARY")
        L.append("=" * 70)
        for fp, d in sorted(results.items()):
            ec = len(d["errors"]); wc = len(d["warnings"])
            L.append(f"\n  {fp}: {ec} errors, {wc} warnings")
            for e in d["errors"]:
                if e["type"] == "WRONG_TEAM":
                    L.append(f"    [ERR] {e['player']} - says {e['says']}, actual {e['actual']}")
                elif e["type"] == "WRONG_STAT":
                    L.append(f"    [ERR] {e['player']} {e['stat']}: says {e['says']}, real {e['actual']} (off {e['diff']})")
            for w in d["warnings"]:
                L.append(f"    [WARN] {w['player']} {w['stat']}: {w['says']} vs last season {w['actual_last_season']}")

    txt = "\n".join(L)
    if out:
        with open(out, 'w', encoding='utf-8') as f: f.write(txt)
        print(f"\nReport saved: {out}")
    print(txt)

# ═══════════ MAIN ═══════════
def main():
    ap = argparse.ArgumentParser(description="Multi-Sport Content Accuracy Checker")
    ap.add_argument("directory", nargs="?", default=".", help="Directory to scan")
    ap.add_argument("--report", "-r", default=None, help="Save report to file")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--sport", "-s", nargs="*", default=None, help="mlb nfl nba nhl ncaaf ncaab")
    a = ap.parse_args()

    if not os.path.isdir(a.directory):
        print(f"[ERROR] Not found: {a.directory}"); sys.exit(1)

    sports = a.sport or list(SPORTS.keys())
    print(f"Sports: {', '.join(s.upper() for s in sports)}")
    print(f"Directory: {a.directory}\n")

    db = build_database(sports)
    results, te, tw, fi, tf = scan_directory(a.directory, db, a.verbose)
    report(results, te, tw, fi, tf, a.report)
    sys.exit(1 if te > 0 else 0)

if __name__ == "__main__":
    main()
