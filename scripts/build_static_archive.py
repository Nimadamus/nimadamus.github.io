#!/usr/bin/env python3
"""
Build complete-archive.html: a STATIC, fully-crawlable index linking EVERY
daily content page (picks, featured games, sport previews) as real <a href>,
grouped by sport, newest-first. Linked from the homepage so Googlebot has a
crawl path to all historical pages - the months of pages that were only ever
reachable via client-side JS and so never got discovered/indexed.

Sources: homepage-picks-data.js + featured-games-data.js + scripts/*-calendar.js
for dated titles, then a disk scan of every content .html to catch anything the
data files miss (title + FORCED_PAGE_DATE read from the file).

Regenerated on every publish by sync_homepage_crawl_links.py so it stays current.
"""
import re, os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "complete-archive.html")
SCRIPTS = os.path.join(ROOT, "scripts")

SUFFIXES = ("-mlb-pick.html", "-nhl-pick.html", "-nba-pick.html", "-ncaab-pick.html",
            "-mlb.html", "-nhl.html", "-nba.html", "-soccer.html", "-ncaab.html",
            "-ncaaf.html", "-nfl.html", "-analysis-stats-preview.html", "-stats-preview.html",
            "-card-mlb-pick.html", "-soccer-analysis-stats-preview.html")

SPORT_OF = [("mlb", "MLB"), ("nhl", "NHL"), ("nba", "NBA"), ("ncaab", "NCAAB"),
            ("ncaaf", "NCAAF"), ("nfl", "NFL"), ("soccer", "Soccer"),
            ("world-cup", "Soccer"), ("analysis-stats-preview", "Featured Games")]


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def read(p):
    return open(p, "r", encoding="utf-8", errors="ignore").read()


def sport_for(page):
    p = page.lower()
    for key, label in SPORT_OF:
        if key in p:
            return label
    return "Other"


def from_data():
    pages = {}
    pd = os.path.join(ROOT, "homepage-picks-data.js")
    if os.path.exists(pd):
        t = read(pd); t = t[t.index("HOMEPAGE_PICKS"):]
        for blk in re.findall(r"\{[^{}]*\}", t):
            u = re.search(r'url:\s*"([^"]+\.html)"', blk)
            d = re.search(r'date:\s*"([^"]+)"', blk)
            ti = re.search(r'title:\s*"((?:[^"\\]|\\.)*)"', blk)
            if u:
                pages[u.group(1)] = {"title": (ti.group(1) if ti else u.group(1)).replace('\\"', '"'),
                                     "date": norm(d.group(1)) if d else ""}
    for src in [os.path.join(ROOT, "featured-games-data.js")] + glob.glob(os.path.join(SCRIPTS, "*-calendar.js")):
        if not os.path.exists(src):
            continue
        for m in re.finditer(r'date:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"\s*,\s*page:\s*"([^"]+\.html)"\s*,\s*title:\s*"((?:[^"\\]|\\.)*)"', read(src)):
            d, pg, tt = m.group(1), m.group(2), m.group(3).replace('\\"', '"')
            pages.setdefault(pg, {"title": tt, "date": d})
    return pages


MONTHS = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}


def norm(s):
    s = (s or "").strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    return ""


def disk_scan(pages):
    for f in os.listdir(ROOT):
        if not f.endswith(".html"):
            continue
        if not any(f.endswith(s) for s in SUFFIXES):
            continue
        if f in pages and pages[f].get("title") and pages[f].get("date"):
            continue
        try:
            t = read(os.path.join(ROOT, f))
        except Exception:
            continue
        if re.search(r'name="robots"[^>]*noindex', t):
            continue
        cur = pages.get(f, {})
        if not cur.get("title"):
            mt = re.search(r"<title>(.*?)</title>", t, re.S)
            cur["title"] = re.sub(r"\s*\|\s*BetLegend.*$", "", mt.group(1)).strip() if mt else f
        if not cur.get("date"):
            md = re.search(r"FORCED_PAGE_DATE\s*=\s*'([0-9]{4}-[0-9]{2}-[0-9]{2})'", t)
            cur["date"] = md.group(1) if md else ""
        pages[f] = cur
    return pages


def main():
    pages = disk_scan(from_data())
    groups = {}
    for pg, meta in pages.items():
        groups.setdefault(sport_for(pg), []).append((pg, meta))
    total = len(pages)
    order = ["MLB", "Soccer", "Featured Games", "NBA", "NHL", "NCAAB", "NCAAF", "NFL", "Other"]
    sections = []
    for sport in order:
        items = groups.get(sport)
        if not items:
            continue
        items.sort(key=lambda x: x[1].get("date") or "", reverse=True)
        lis = "\n".join(
            f'    <li><a href="{esc(pg)}">{esc(meta.get("title") or pg)}</a>'
            f'<span class="ca-date">{esc(meta.get("date") or "")}</span></li>'
            for pg, meta in items)
        sections.append(f'  <h2>{esc(sport)} <span class="ca-count">{len(items)}</span></h2>\n  <ul class="ca-list">\n{lis}\n  </ul>')
    body = "\n".join(sections)
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<link rel="canonical" href="https://www.betlegendpicks.com/complete-archive.html">
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Complete Pick and Preview Archive | BetLegend</title>
<meta name="description" content="Full crawlable archive of every BetLegend pick page, featured game, and sport preview - {total} pages across MLB, NBA, NHL, NCAAB, NCAAF, NFL, and Soccer.">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
<style>
body{{background:#0a0c10;color:#e6dccb;font-family:Inter,system-ui,sans-serif;line-height:1.6;margin:0;padding:0}}
.wrap{{max-width:1100px;margin:0 auto;padding:40px 22px 80px}}
h1{{font-family:Oswald,sans-serif;font-size:34px;text-transform:uppercase;letter-spacing:2px;color:#fbf7ed;margin:0 0 6px}}
.intro{{color:#aaa091;margin:0 0 30px}}
h2{{font-family:Oswald,sans-serif;font-size:22px;text-transform:uppercase;letter-spacing:1.5px;color:#e8b85c;margin:34px 0 12px;border-bottom:1px solid rgba(232,184,92,.25);padding-bottom:8px}}
.ca-count{{font-size:13px;color:#7c7468;margin-left:8px}}
.ca-list{{list-style:none;margin:0;padding:0;columns:2;column-gap:36px}}
.ca-list li{{break-inside:avoid;margin:0 0 7px;font-size:14px}}
.ca-list a{{color:#cdd6e4;text-decoration:none}}
.ca-list a:hover{{color:#00e5ff;text-decoration:underline}}
.ca-date{{color:#6b7280;font-size:12px;margin-left:8px}}
a.home{{color:#00e5ff;text-decoration:none;font-weight:700}}
@media(max-width:680px){{.ca-list{{columns:1}}}}
</style>
</head>
<body>
<div class="wrap">
<p><a class="home" href="index.html">&larr; BetLegend home</a></p>
<h1>Complete Pick &amp; Preview Archive</h1>
<p class="intro">Every published pick page, featured game, and sport preview - {total} pages. Newest first within each sport.</p>
{body}
</div>
</body>
</html>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[build_static_archive] complete-archive.html written: {total} pages across {len([s for s in order if groups.get(s)])} sports")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
