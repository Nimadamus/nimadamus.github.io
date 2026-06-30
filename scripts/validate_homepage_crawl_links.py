#!/usr/bin/env python3
"""
BLOCKING guard: fail if index.html's STATIC html is missing the newest
published pages as real <a href> links. This is the piece that was missing
every prior time this "got fixed" and then silently went stale -- without a
guard, the static crawl block froze and Googlebot stopped discovering daily
pages. Runs in pre-commit and in ATLAS Phase 12.

Checks the newest entry from each live data source is present in index.html:
  - newest homepage-picks-data.js pick url
  - newest featured-games-data.js page
  - newest entry of each IN-SEASON sport calendar (>=1 entry in last 10 days)
Exit 0 = all present. Exit 1 = stale (lists what is missing).
"""
import os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
PICKS = os.path.join(ROOT, "homepage-picks-data.js")
FEATURED = os.path.join(ROOT, "featured-games-data.js")
SCRIPTS = os.path.join(ROOT, "scripts")
RECENT_DAYS = 10


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def newest_pick_url():
    body = read(PICKS)
    body = body[body.index("HOMEPAGE_PICKS"):]
    for blk in re.findall(r"\{[^{}]*\}", body):
        m = re.search(r'url\s*:\s*"([^"]+\.html)"', blk)
        if m:
            return ("homepage-picks-data.js (newest pick)", m.group(1))
    return None


def newest_dated(path, label):
    if not os.path.exists(path):
        return None
    rows = re.findall(r'date:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"\s*,\s*page:\s*"([^"]+\.html)"', read(path))
    if not rows:
        return None
    rows.sort(key=lambda r: r[0], reverse=True)
    date, page = rows[0]
    return (label, page, date)


def main():
    html = read(INDEX)
    today = datetime.date.today()
    cutoff = (today - datetime.timedelta(days=RECENT_DAYS)).isoformat()
    required = []

    p = newest_pick_url()
    if p:
        required.append((p[0], p[1]))

    f = newest_dated(FEATURED, "featured-games-data.js (newest featured)")
    if f and f[2] >= cutoff:
        required.append((f[0], f[1]))

    for fn in sorted(os.listdir(SCRIPTS)):
        if fn.endswith("-calendar.js") and fn != "featured-games-calendar.js":
            r = newest_dated(os.path.join(SCRIPTS, fn), f"{fn} (newest in-season preview)")
            if r and r[2] >= cutoff:   # only enforce sports active in the last 10 days
                required.append((r[0], r[1]))

    missing = [(label, page) for (label, page) in required if f'href="{page}"' not in html]
    if missing:
        print("[FAILED] index.html static HTML is STALE - Googlebot cannot discover these daily pages:")
        for label, page in missing:
            print(f"   MISSING <a href>: {page}   <- {label}")
        print("\nFix: python scripts/sync_homepage_crawl_links.py  (then re-stage index.html)")
        return 1
    print(f"[PASSED] index.html static HTML carries all {len(required)} newest pages as crawlable links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
