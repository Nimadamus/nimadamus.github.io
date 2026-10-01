#!/usr/bin/env python3
"""Build the authoritative BetLegend record (approved by Nima, Oct 1 2026).

Approved totals at approval time: 1543-1331-83, -173.36u, 2,957 graded bets
(2025: 682-550-38 +27.12u; 2026: 861-781-45 -200.48u).

Sources (the same ones the records pages always read):
  * Pick Tracker sheet (gid=0) is the source of truth from 2025-12-25 on.
    Sport comes from its League column; Cross-Sport parlays count in the overall
    record but on no single sport page.
  * The seven published per-sport sheets (2025 history) before 2025-12-25.

Identity of a bet: (sport, date, canonical pick text). Canonical text lowercases,
maps point->pt, 1st/first half->1h, 2nd half->2h, first quarter->1q,
team total->tt, moneyline->ml, fixes the tsr/teasser/ppint typos, two team->2 team,
and drops punctuation and spaces. A sheet row and a tracker row with different
wording are the same bet when sport, date, result and units won or lost (to the
cent) agree and their word overlap is at least 50 percent. An exact repeat of a
row inside one per-sport sheet is counted once (approved rule R1).
Row-level rulings that the rules cannot express live in data/records_overrides.json
(R2 duplicate stub excluded, R3 settled loss with a blank result letter).

Units: favorites win the stated units, underdogs risk them (calculate_unit_result).

Writes:
  all-records.json         canonical rows (what every records page renders)
  data/records_totals.json totals by sport and year (audit trail)
  <sport>-records.html     the static fallback/SEO table body (#picks-table-body)

Exit codes: 0 ok, 2 a source failed to download (nothing written).
Usage: python scripts/build_canonical_records.py [--dry-run]
"""
import csv
import io
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_records_from_tracker import calculate_unit_result  # noqa: E402

TRACKER = "https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0"
SHEETS = {
    "NFL": "2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq",
    "NBA": "2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz",
    "NHL": "2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I",
    "MLB": "2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv",
    "NCAAF": "2PACX-1vQ9c45xiuXWNe-fAXYMoNb00kCBHfMf4Yn-Xr2LUqdCIiuoiXXDgrDa5mq1PZqxjg8hx-5KnS0L4uVU",
    "NCAAB": "2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y",
    "Soccer": "2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns",
}
CUT = date(2025, 12, 25)
PAGES = {"MLB": "mlb-records.html", "NHL": "nhl-records.html", "NFL": "nfl-records.html", "NBA": "nba-records.html",
         "NCAAF": "ncaaf-records.html", "NCAAB": "ncaab-records.html", "Soccer": "soccer-records.html"}
LEAGUE = [("mlb", "MLB"), ("nhl", "NHL"), ("nfl", "NFL"), ("nba", "NBA"), ("ncaaf", "NCAAF"), ("cfb", "NCAAF"),
          ("ncaab", "NCAAB"), ("cbb", "NCAAB"), ("soccer", "Soccer"), ("mls", "Soccer")]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def nd(s):
    p = re.split(r"[-/]", (s or "").strip())
    if len(p) != 3:
        return None
    try:
        m, d, y = int(p[0]), int(p[1]), p[2].strip()
        y = int(y[:2] + "2" + y[2:]) if re.fullmatch(r"20\d", y) else int(y)
        if y < 100:
            y += 2000
        return date(y, m, d) if 2020 <= y <= 2030 else None
    except ValueError:
        return None


def canon(s):
    s = (s or "").lower().replace("’", "'")
    for a, b in [("teasser", "teaser"), ("tsr", "teaser"), ("ppint", "point"), ("two team", "2 team"), ("point", "pt"),
                 ("first half", "1h"), ("1st half", "1h"), ("2nd half", "2h"), ("first quarter", "1q"),
                 ("team total", "tt"), ("moneyline", "ml")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9.]", "", s)


def toks(s):
    return set(re.findall(r"[a-z]{2,}|\d+(?:\.\d+)?", (s or "").lower().replace("point", "pt"))) - {"team", "the", "pt", "teaser", "tsr", "ml"}


def fnum(v):
    try:
        return float(str(v).replace(",", "").replace("+", ""))
    except (TypeError, ValueError):
        return None


def tracker_sport(r):
    lg = (r.get("League") or "").strip().lower()
    for k, v in LEAGUE:
        if lg.startswith(k):
            return v
    if "cross" in lg or "parlay" in lg:
        return "Cross-Sport"
    if "soccer" in (r.get("Sport") or "").lower():
        return "Soccer"
    return None


def load(overrides):
    rows, rejects = [], []
    tr_raw = list(csv.DictReader(io.StringIO(fetch(TRACKER))))
    tracker = []
    for i, r in enumerate(tr_raw):
        res = (r.get("Result") or "").strip().upper()[:1]
        if res not in ("W", "L", "P"):
            continue
        sport = tracker_sport(r)
        d = nd(r.get("Date"))
        if not sport or not d:
            rejects.append(("tracker", i + 2, "unknown sport or date", r.get("Pick")))
            continue
        tracker.append({"sport": sport, "date": d, "pick": (r.get("Pick") or "").strip(), "odds": (r.get("Odds") or "").strip(),
                        "units": (r.get("Units") or "").strip(), "league": (r.get("League") or "").strip(), "result": res,
                        "pl": calculate_unit_result(r.get("Units", "3"), r.get("Odds", ""), res), "source": "tracker-row-%d" % (i + 2)})
    sheet = []
    for sport, key in SHEETS.items():
        raw = list(csv.reader(io.StringIO(fetch("https://docs.google.com/spreadsheets/d/e/%s/pub?output=csv" % key))))
        hdr = [h.strip() for h in raw[0]]
        if "Result" not in hdr:  # the NBA sheet has a blank header over its result column
            hdr[3] = "Result"
        seen = set()
        for i, vals in enumerate(raw[1:]):
            src = "sheet-%s-row-%d" % (sport, i + 2)
            r = {h: (vals[j] if j < len(vals) else "") for j, h in enumerate(hdr) if h}
            pick = (r.get("Pick") or "").strip()
            odds = (r.get("Line") or r.get("Odds") or "").strip()
            res = (r.get("Result") or "").strip().upper()[:1]
            pl = fnum(r.get("Units"))
            d = nd(r.get("Date"))
            ov = overrides.get(src)
            if ov and ov.get("action") == "exclude":
                rejects.append((src, "override exclude", ov.get("reason")))
                continue
            if ov and ov.get("action") == "set":
                res, pl = ov["result"], ov["pl"]
            if res not in ("W", "L", "P"):
                if pick or r.get("Date"):
                    rejects.append((src, "no result", pick))
                continue
            if not d or not pick or pl is None:
                rejects.append((src, "bad date, pick or units", pick))
                continue
            k = (d, pick.lower(), odds, res, round(pl, 2))
            if k in seen:  # R1: exact repeat inside one sheet counts once
                rejects.append((src, "exact repeat in sheet (R1)", pick))
                continue
            seen.add(k)
            sheet.append({"sport": sport, "date": d, "pick": pick, "odds": odds, "units": "", "league": r.get("League", "") or "",
                          "result": res, "pl": pl, "source": src})
    by_date = {}
    for t in tracker:
        by_date.setdefault(t["date"], []).append(t)
    used = set()

    def same(a, b):
        if a["date"] != b["date"] or a["result"] != b["result"] or abs(a["pl"] - b["pl"]) > 0.011:
            return False
        if canon(a["pick"]) == canon(b["pick"]):
            return True
        ta, tb = toks(a["pick"]), toks(b["pick"])
        return len(ta & tb) / max(1, len(ta | tb)) >= 0.5

    for s in sheet:
        cands = [t for t in by_date.get(s["date"], []) if id(t) not in used]
        m = next((t for t in cands if canon(t["pick"]) == canon(s["pick"])), None) or next((t for t in cands if same(s, t)), None)
        if m is not None:
            used.add(id(m))
            continue
        rows.append(s)
    rows += tracker
    return rows, rejects


def q(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def tally(rs):
    w = sum(r["result"] == "W" for r in rs)
    l = sum(r["result"] == "L" for r in rs)
    p = sum(r["result"] == "P" for r in rs)
    return {"bets": len(rs), "record": "%d-%d-%d" % (w, l, p), "wins": w, "losses": l, "pushes": p,
            "units": q(sum(r["pl"] for r in rs))}


def fmt_date(d):
    return "%d/%d/%d" % (d.month, d.day, d.year)


def table_rows(rs):
    out = []
    for r in rs:
        pl = r["pl"]
        cls = "win" if pl > 0 else ("loss" if pl < 0 else "result-P")
        txt = ("+%.2f" % pl) if pl > 0 else ("%.2f" % pl)
        out.append('                    <tr><td>%s</td><td>%s</td><td>%s</td><td class="result-%s">%s</td><td class="%s">%s</td></tr>' % (
            fmt_date(r["date"]), r["pick"].replace("<", "&lt;"), r["odds"] or "", r["result"], r["result"], cls, txt))
    return "\n".join(out)


def main():
    dry = "--dry-run" in sys.argv
    ov_path = os.path.join(ROOT, "data", "records_overrides.json")
    overrides = {o["source"]: o for o in json.load(open(ov_path, encoding="utf-8"))["overrides"]}
    try:
        rows, rejects = load(overrides)
    except Exception as e:
        print("FAILED to load a source; nothing written: %s" % e)
        return 2
    rows.sort(key=lambda r: (r["date"], r["source"]), reverse=True)
    totals = {"overall": tally(rows), "by_year": {}, "by_sport": {}, "by_sport_year": {},
              "generated_pt": datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="minutes"),
              "last_graded_date": fmt_date(rows[0]["date"]) if rows else None,
              "note": "Overall includes Cross-Sport parlays, which no single sport page shows."}
    for y in sorted({r["date"].year for r in rows}):
        totals["by_year"][str(y)] = tally([r for r in rows if r["date"].year == y])
    for s in sorted({r["sport"] for r in rows}):
        rs = [r for r in rows if r["sport"] == s]
        totals["by_sport"][s] = tally(rs)
        for y in sorted({r["date"].year for r in rs}):
            totals["by_sport_year"]["%s %d" % (s, y)] = tally([r for r in rs if r["date"].year == y])
    print("OVERALL %(record)s %(units)+.2fu %(bets)d bets" % totals["overall"])
    for s, t in totals["by_sport"].items():
        print("  %-11s %s %+.2fu (%d)" % (s, t["record"], t["units"], t["bets"]))
    print("  rejected/ignored source rows: %d" % len(rejects))
    if dry:
        return 0
    out = [{"Sport": r["sport"], "League": r["league"], "Date": fmt_date(r["date"]), "Picks": r["pick"], "Odds": r["odds"],
            "Units": r["units"], "Result": r["result"], "ProfitLoss": "%.4f" % r["pl"], "Source": r["source"]} for r in rows]
    json.dump(out, open(os.path.join(ROOT, "all-records.json"), "w", encoding="utf-8"), indent=1)
    json.dump(totals, open(os.path.join(ROOT, "data", "records_totals.json"), "w", encoding="utf-8"), indent=1)
    for sport, page in PAGES.items():
        p = os.path.join(ROOT, page)
        html = open(p, encoding="utf-8", errors="ignore").read()
        rs = [r for r in rows if r["sport"] == sport]
        m = re.search(r'(<tbody id="picks-table-body">).*?(</tbody>)', html, re.S)
        if not m:
            print("  WARNING: no #picks-table-body in %s" % page)
            continue
        new = html[:m.start()] + m.group(1) + "\n" + table_rows(rs) + "\n                " + m.group(2) + html[m.end():]
        if new != html:
            open(p, "w", encoding="utf-8").write(new)
    print("wrote all-records.json (%d rows), data/records_totals.json and %d sport tables" % (len(out), len(PAGES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
