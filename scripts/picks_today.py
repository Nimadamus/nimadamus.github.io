#!/usr/bin/env python3
"""Evergreen "<Sport> Picks Today" pages (Nima, Oct 1 2026). MLB is the pilot.

One permanent URL per sport (mlb-picks-today.html). The content updates; the URL
never changes and no dated copy is ever written. Each build shows, in order:

  1. Today's posted BetLegend picks for the sport, read from the Pick Tracker
     sheet (the same sheet the Discord bot, blog and records read): pick, exact
     posted odds, units, posted time (Pacific) and a link to the blog post.
     If nothing is posted yet the page says so. A pick is never invented.
  2. Today's slate with lines (scripts/current_slate.py, ESPN).
  3. Record snapshot: last 30 days, graded rows only, from the tracker.
  4. The last 10 graded picks for the sport.
  5. The contextual Bet Legend Pro module.
  6. Grading and odds FAQ.

The season-to-date record is not shown until Nima approves the deduplicated
records (Oct 1 2026 audit); the 30-day window does not include any of the rows
awaiting his ruling.

Usage: python scripts/picks_today.py [--sport mlb] [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import io
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import current_slate  # noqa: E402
import pro_cta  # noqa: E402
from sync_records_from_tracker import calculate_unit_result, PICK_TRACKER_URL  # noqa: E402

ROOT = current_slate.ROOT
PT = current_slate.PT
SITE = "https://www.betlegendpicks.com/"

SPORT_PAGES = {
    "mlb": {"file": "mlb-picks-today.html", "label": "MLB", "league": "mlb", "records": "mlb-records.html",
            "hub": "mlb.html", "previews": "mlb-previews.html", "pro_variant": "hub-mlb",
            "units_note": "Run lines, moneylines, totals, team totals and first five innings plays are all graded the same way."},
}

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def fetch_tracker():
    req = urllib.request.Request(PICK_TRACKER_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))


def parse_date(s):
    s = (s or "").strip()
    for f in ("%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None


def parse_posted(s):
    s = (s or "").strip()
    for f in ("%m/%d/%Y %I:%M:%S %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M %p"):
        try:
            return dt.datetime.strptime(s, f)
        except ValueError:
            pass
    return None


def fmt_odds(o):
    o = str(o or "").strip()
    if not o:
        return "Not listed"
    if re.fullmatch(r"\d+(\.\d+)?", o):
        return "+" + o
    return o


def fmt_units(u):
    try:
        v = float(u)
        return f"{v:g}"
    except (TypeError, ValueError):
        return str(u or "")


def blog_link(blog_html, day, pick):
    """Blog post anchor for this pick: same date, best word overlap with the post id."""
    ids = re.findall(r'class="blog-post"\s+id="(post-%s-[^"]+)"' % day.strftime("%Y%m%d"), blog_html)
    if not ids:
        return None
    words = set(re.findall(r"[a-z]{3,}", pick.lower())) - {"under", "over", "team", "total", "moneyline", "first"}
    best = max(ids, key=lambda i: len(words & set(i.split("-"))))
    if len(ids) > 1 and not (words & set(best.split("-"))):
        return None
    return "blog.html#" + best


def build(sport, now_pt, rows, blog_html, slate_data):
    cfg = SPORT_PAGES[sport]
    label = cfg["label"]
    today = now_pt.date()
    mine = [r for r in rows if (r.get("League") or "").strip().lower() == cfg["league"]]
    for r in mine:
        r["_d"] = parse_date(r.get("Date"))
        r["_res"] = (r.get("Result") or "").strip().upper()[:1]
    todays = [r for r in mine if r["_d"] == today and (r.get("Ready") or "").strip().upper() == "POSTED"]
    graded = sorted([r for r in mine if r["_d"] and r["_res"] in ("W", "L", "P")],
                    key=lambda r: (r["_d"], parse_posted(r.get("PostedAt")) or dt.datetime.min), reverse=True)

    # 1. today's picks
    if todays:
        trs = []
        for r in sorted(todays, key=lambda r: parse_posted(r.get("PostedAt")) or dt.datetime.max):
            posted = parse_posted(r.get("PostedAt"))
            ptxt = (f"{posted:%I:%M %p}".lstrip("0") + " PT") if posted else "Posted"
            link = blog_link(blog_html, today, r.get("Pick", ""))
            ltxt = f'<a href="{e(link)}">Read the analysis</a>' if link else '<a href="blog.html">BetLegend blog</a>'
            res = {"W": "Won", "L": "Lost", "P": "Push"}.get(r["_res"], "Pending")
            trs.append(f"<tr><td><strong>{e(r.get('Pick'))}</strong></td><td class=\"n\">{e(fmt_odds(r.get('Odds')))}</td>"
                       f"<td class=\"n\">{e(fmt_units(r.get('Units')))}</td><td class=\"n\">{e(ptxt)}</td><td>{res}</td><td>{ltxt}</td></tr>")
        picks_html = ('<div class="pt-wrap"><table><thead><tr><th>Pick</th><th>Odds</th><th>Units</th><th>Posted</th>'
                      '<th>Status</th><th>Analysis</th></tr></thead><tbody>' + "".join(trs) + "</tbody></table></div>")
        lead = f"{len(todays)} BetLegend {label} pick{'s' if len(todays) != 1 else ''} posted for {current_slate.fmt_day(today)}."
    else:
        last = graded[0] if graded else None
        tail = ""
        if last:
            res = {"W": "won", "L": "lost", "P": "pushed"}[last["_res"]]
            tail = (f" The most recent graded {label} pick was {e(last.get('Pick'))} at {e(fmt_odds(last.get('Odds')))} "
                    f"on {e(current_slate.fmt_date(last['_d']))}, and it {res}.")
        picks_html = (f'<p class="pt-empty">No BetLegend {label} pick has been posted for {e(current_slate.fmt_day(today))} yet. '
                      f'When one is posted it appears here with the exact odds, units and time, and on the '
                      f'<a href="blog.html">BetLegend blog</a>.{tail}</p>')
        lead = f"No {label} pick posted yet for {current_slate.fmt_day(today)}."

    # 3. last 30 days
    start = today - dt.timedelta(days=30)
    window = [r for r in graded if start <= r["_d"] < today]
    w = sum(r["_res"] == "W" for r in window); l = sum(r["_res"] == "L" for r in window); p = sum(r["_res"] == "P" for r in window)
    units = sum(calculate_unit_result(r.get("Units", "3"), r.get("Odds", ""), r["_res"]) for r in window)
    pct = (100.0 * w / (w + l)) if (w + l) else 0.0
    snap = (f'<div class="pt-stats"><div><b>{w}-{l}-{p}</b><span>record, last 30 days</span></div>'
            f'<div><b>{units:+.2f}u</b><span>units, last 30 days</span></div>'
            f'<div><b>{pct:.1f}%</b><span>win rate (pushes excluded)</span></div>'
            f'<div><b>{len(window)}</b><span>graded picks, {e(current_slate.fmt_date(start))} to {e(current_slate.fmt_date(today - dt.timedelta(days=1)))}</span></div></div>')

    # 4. last 10 graded
    rows10 = []
    for r in graded[:10]:
        pl = calculate_unit_result(r.get("Units", "3"), r.get("Odds", ""), r["_res"])
        cls = {"W": "w", "L": "l", "P": "p"}[r["_res"]]
        rows10.append(f"<tr><td class=\"n\">{e(r['_d'].strftime('%b %d').replace(' 0', ' '))}</td><td>{e(r.get('Pick'))}</td>"
                      f"<td class=\"n\">{e(fmt_odds(r.get('Odds')))}</td><td class=\"n\">{e(fmt_units(r.get('Units')))}</td>"
                      f"<td class=\"{cls}\">{ {'W': 'Win', 'L': 'Loss', 'P': 'Push'}[r['_res']] }</td><td class=\"n {cls}\">{pl:+.2f}</td></tr>")
    last10 = ('<div class="pt-wrap"><table><thead><tr><th>Date</th><th>Pick</th><th>Odds</th><th>Units</th><th>Result</th>'
              '<th>Units won/lost</th></tr></thead><tbody>' + "".join(rows10) + "</tbody></table></div>")

    # 2. slate (reuse the hub block; its own markers keep it self-contained)
    _, _, slate_block = current_slate.render_block(sport, slate_data, now_pt)

    pro = pro_cta.block(cfg["file"], "picks", label, "picks-" + sport) if ("picks-" + sport) in pro_cta.COPY else ""

    title = f"{label} Picks Today: {current_slate.fmt_day(today)} | BetLegend"
    h1 = f"{label} Picks Today: {current_slate.fmt_day(today)}"
    desc = (f"BetLegend's {label} picks for {current_slate.fmt_date(today)} with the exact posted odds, units and time, "
            f"today's {label} slate and lines, our last 30 days and the last 10 graded picks.")
    url = SITE + cfg["file"]
    iso = now_pt.replace(microsecond=0).isoformat()
    faq = [
        ("When are BetLegend MLB picks posted?",
         "Picks go up when they are made, always before first pitch. Each one shows the exact time it was posted in Pacific time, and the same pick goes to the BetLegend blog with the full write-up."),
        ("What odds do you grade at?",
         "Every pick is graded at the price posted with it, the number in the Odds column. We do not move a pick to a better closing number."),
        ("What does a unit mean here?",
         "On favorites the units are what the bet wins. On underdogs (plus money) the units are what the bet risks. A 2 unit pick at -150 wins 2 units or loses 3; a 2 unit pick at +130 wins 2.6 units or loses 2. " + cfg["units_note"]),
        ("How are pushes and postponed games handled?",
         "A push returns the stake and counts as 0 units. A postponed game is void and does not count in the record."),
        ("Where do the lines in the slate come from?",
         "The slate shows the DraftKings lines that ESPN publishes, refreshed several times a day. They are market context, not the price on our picks, and they move before the game."),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in faq)
    ld = [
        {"@context": "https://schema.org", "@type": "WebPage", "name": h1, "url": url, "description": desc,
         "dateModified": iso, "isPartOf": {"@type": "WebSite", "name": "BetLegend Picks", "url": SITE}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": f"{label} Hub", "item": SITE + cfg["hub"]},
            {"@type": "ListItem", "position": 3, "name": f"{label} Picks Today", "item": url}]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ]
    updated = f"{now_pt:%B} {now_pt.day}, {now_pt.year} at " + f"{now_pt:%I:%M %p}".lstrip("0") + " PT"
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(h1)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}newlogo.png">
<meta property="og:site_name" content="BetLegend Picks">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{e(h1)}">
<meta name="twitter:description" content="{e(desc)}">
<link rel="icon" href="/images/newlogo-64.png" type="image/png">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-QS8L5TDNLY');</script>
{"".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + '</script>' for x in ld)}
<link rel="stylesheet" href="/site-navbar.css">
<link rel="stylesheet" href="/mobile-optimize.css">
<style>
body{{margin:0;background:#0d0f14;color:#e8ecf2;font-family:Inter,Manrope,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.6}}
.pt{{max-width:960px;margin:0 auto;padding:28px 18px 60px;box-sizing:border-box}}
.pt a{{color:#f3d77a}}
.pt .crumbs{{font-size:.85rem;color:#9aa3af;margin:0 0 10px}}
.pt .crumbs a{{color:#9aa3af}}
.pt h1{{font-size:2rem;line-height:1.2;margin:0 0 8px;color:#fff}}
.pt .lead{{color:#c9d0da;margin:0 0 6px}}
.pt .upd{{color:#8b94a1;font-size:.85rem;margin:0 0 26px}}
.pt h2{{font-size:1.3rem;margin:34px 0 12px;color:#fff}}
.pt section{{margin:0 0 8px}}
.pt-wrap{{overflow-x:auto;-webkit-overflow-scrolling:touch;width:0;min-width:100%}}
.pt table{{width:100%;border-collapse:collapse;font-size:.92rem;min-width:520px}}
.pt th{{text-align:left;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:#d4af37;padding:8px;border-bottom:1px solid rgba(212,175,55,.35)}}
.pt td{{padding:9px 8px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top}}
.pt td.n{{white-space:nowrap;font-variant-numeric:tabular-nums}}
.pt .w{{color:#6fd08f}}.pt .l{{color:#ef7d6f}}.pt .p{{color:#c9d0da}}
.pt-empty{{padding:16px 18px;border:1px solid rgba(212,175,55,.35);border-radius:10px;background:#141821}}
.pt-stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}}
.pt-stats div{{background:#141821;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:14px}}
.pt-stats b{{display:block;font-size:1.45rem;color:#fff;font-variant-numeric:tabular-nums}}
.pt-stats span{{color:#9aa3af;font-size:.82rem}}
.pt details{{border-bottom:1px solid rgba(255,255,255,.08);padding:10px 0}}
.pt summary{{cursor:pointer;font-weight:600;color:#fff}}
.pt details p{{color:#c9d0da;margin:8px 0 0}}
.pt .more{{display:flex;flex-wrap:wrap;gap:8px 18px;padding:0;list-style:none}}
</style>
</head>
<body>
<script src="/scripts/site-navbar.js" defer></script>
<main class="pt">
<p class="crumbs"><a href="/">Home</a> / <a href="{cfg['hub']}">{label}</a> / {label} Picks Today</p>
<h1>{e(h1)}</h1>
<p class="lead">{e(lead)} Every pick shows the exact odds and units it was posted at, and every result is graded in our public record.</p>
<p class="upd">Updated {e(updated)}.</p>

<section id="todays-picks"><h2>Today's BetLegend {label} picks</h2>
{picks_html}
</section>

<section id="slate"><h2>Today's {label} slate</h2>
{slate_block}
</section>

<section id="record"><h2>Our {label} record, last 30 days</h2>
{snap}
<p><a href="{cfg['records']}">See every graded {label} pick</a></p>
</section>

<section id="last-10"><h2>Last 10 graded {label} picks</h2>
{last10}
</section>

{pro}

<section id="faq"><h2>How we post and grade picks</h2>
{faq_html}
</section>

<ul class="more"><li><a href="blog.html">BetLegend blog</a></li><li><a href="{cfg['hub']}">{label} slate and odds</a></li><li><a href="{cfg['previews']}">{label} previews</a></li><li><a href="{cfg['records']}">{label} betting record</a></li><li><a href="best-bets-today.html">Best bets today</a></li></ul>
</main>
<script src="/blp-events.js" defer></script>
</body>
</html>
"""
    return page


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", default="mlb", choices=sorted(SPORT_PAGES))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    now_pt = dt.datetime.now(PT)
    try:
        rows = fetch_tracker()
    except Exception as ex:
        print(f"[picks_today] Pick Tracker fetch failed, page left unchanged: {ex}")
        return 2
    try:
        slate = current_slate.fetch_sport(a.sport, now_pt)
    except Exception as ex:
        print(f"[picks_today] ESPN fetch failed, page left unchanged: {ex}")
        return 2
    with open(os.path.join(ROOT, "blog.html"), encoding="utf-8", errors="ignore") as f:
        blog = f.read()
    page = build(a.sport, now_pt, rows, blog, slate)
    # email signup module (scripts/email_signup.py) right before the FAQ
    import email_signup
    label = "Soccer" if a.sport == "soccer" else a.sport.upper()
    page = page.replace('<section id="faq">', email_signup.block(SPORT_PAGES[a.sport]["file"], "picks", label).lstrip() + '<section id="faq">', 1)
    path = os.path.join(ROOT, SPORT_PAGES[a.sport]["file"])
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    strip = lambda s: re.sub(r"Updated [A-Z][a-z]+ \d{1,2}, \d{4} at [0-9:]+ [AP]M PT\.|\"dateModified\": \"[^\"]*\"", "", s)
    if strip(old) == strip(page):
        print("[picks_today] no change")
        return 0
    if a.dry_run:
        print(page[:3000])
        return 0
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"[picks_today] wrote {SPORT_PAGES[a.sport]['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
