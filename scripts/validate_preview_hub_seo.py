#!/usr/bin/env python3
"""
Preview-hub SEO regression guard.

WHY THIS EXISTS (June 9, 2026):
The mlb/nba/nhl/soccer preview hubs kept shipping STALE head metadata. The daily
re-bake (scripts/refresh_preview_hubs.py) rewrites only the body/hero and leaves the
<head> frozen, so old game-specific title/description/keywords/og:url/JSON-LD/canonical
values rotted in place for days (e.g. a May 19 Yankees-Blue Jays board still named in
head while the body showed today's slate). This was "fixed" by hand several times and
kept coming back because nothing FAILED when it regressed.

This guard makes a regression fail CI instead of silently shipping. For each hub it
asserts the <head> is generic + self-referential, and it verifies sitemap routing.

Checks per hub (mlb/nba/nhl/soccer-previews.html):
  1. <link rel=canonical> == the hub's own URL
  2. og:url == the hub's own URL
  3. JSON-LD url + mainEntityOfPage @id (when present) == the hub's own URL
  4. <head> contains NO betlegendpicks.com/<other>.html URL (only the hub's own .html)
  5. title/description/keywords/og:* carry NO stale date or month+day token
     (generic hub metadata must never name a specific dated game again)

Sitemap routing checks:
  6. public sitemap.xml index references sitemap-previews.xml AND sitemap-featured-games.xml
  7. the 4 preview hubs appear in sitemap-previews.xml
  8. every *analysis-stats-preview*.html (Featured Game) belongs in sitemap-featured-games.xml
     and NONE of them leak into sitemap-previews.xml

Default mode reads LOCAL source files (what CI validates before deploy).
Pass --live to fetch the public site instead.

Exit 0 = clean. Exit 1 = regression (prints every [FAIL]).
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASE = "https://www.betlegendpicks.com"

HUBS = ["mlb-previews.html", "nba-previews.html", "nhl-previews.html", "soccer-previews.html"]

MONTHS = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
# A month immediately followed by a day number, e.g. "May 19", "June 1 2026".
DATE_TOKEN = re.compile(MONTHS + r"\s+\d{1,2}\b", re.I)
ISO_DATE = re.compile(r"\b20\d{2}-\d{2}-\d{2}\b")

BETLEGEND_HTML_URL = re.compile(r"https?://(?:www\.)?betlegendpicks\.com/([A-Za-z0-9._/-]+\.html)", re.I)


def read_local(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8", errors="replace")


def read_live(rel: str) -> str:
    url = rel if rel.startswith("http") else f"{BASE}/{rel.lstrip('/')}"
    req = urllib.request.Request(url, headers={"User-Agent": "betlegend-seo-guard"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def head_of(html: str) -> str:
    i = html.lower().find("</head>")
    return html[:i] if i != -1 else html


def attr(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.I)
    return m.group(1).strip() if m else None


def check_hub(rel: str, read, fails: list):
    html = read(rel)
    head = head_of(html)
    self_url = f"{BASE}/{rel}"

    canon = attr(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', head)
    if not canon:
        fails.append(f"{rel}: missing canonical")
    elif canon.rstrip("/") != self_url.rstrip("/"):
        fails.append(f"{rel}: canonical is '{canon}', expected self '{self_url}'")

    ogurl = (attr(r'property=["\']og:url["\'][^>]*content=["\']([^"\']+)', head)
             or attr(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:url["\']', head))
    if not ogurl:
        fails.append(f"{rel}: missing og:url")
    elif ogurl.rstrip("/") != self_url.rstrip("/"):
        fails.append(f"{rel}: og:url is '{ogurl}', expected self '{self_url}'")

    # JSON-LD url + mainEntityOfPage @id (only validate if present)
    for label, pat in [("JSON-LD url", r'"url"\s*:\s*"(https?://[^"]*betlegendpicks\.com/[^"]*\.html)"'),
                       ("JSON-LD mainEntityOfPage @id",
                        r'mainEntityOfPage"\s*:\s*\{[^}]*"@id"\s*:\s*"([^"]+)"')]:
        m = re.search(pat, head, re.I)
        if m:
            val = m.group(1)
            if val.rstrip("/") != self_url.rstrip("/"):
                fails.append(f"{rel}: {label} is '{val}', expected self '{self_url}'")

    # No OTHER betlegendpicks .html URL in the head (only the hub's own .html allowed)
    for u in BETLEGEND_HTML_URL.finditer(head):
        page = u.group(1)
        if page.lstrip("/") != rel:
            fails.append(f"{rel}: head references foreign article URL '{u.group(0)}' (stale game/article URL)")

    # No stale date / month+day token in title/description/keywords/og:* (generic hub meta only)
    fields = re.findall(r'<title>([^<]*)</title>', head, re.I)
    fields += re.findall(r'name=["\'](?:description|keywords)["\'][^>]*content=["\']([^"\']+)', head, re.I)
    fields += re.findall(r'content=["\']([^"\']+)["\'][^>]*name=["\'](?:description|keywords)["\']', head, re.I)
    fields += re.findall(r'property=["\']og:(?:title|description)["\'][^>]*content=["\']([^"\']+)', head, re.I)
    fields += re.findall(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:(?:title|description)["\']', head, re.I)
    for f in fields:
        if DATE_TOKEN.search(f) or ISO_DATE.search(f):
            fails.append(f"{rel}: stale date/game token in head metadata field: '{f.strip()[:90]}'")


def sitemap_checks(read, fails: list):
    try:
        index = read("sitemap.xml")
    except Exception as e:
        fails.append(f"sitemap.xml unreadable: {e}")
        return
    for child in ("sitemap-previews.xml", "sitemap-featured-games.xml"):
        if child not in index:
            fails.append(f"sitemap.xml index does not reference {child}")

    try:
        previews = read("sitemap-previews.xml")
        featured = read("sitemap-featured-games.xml")
    except Exception as e:
        fails.append(f"child sitemap unreadable: {e}")
        return

    # 7. preview hubs must be in the previews sitemap
    for hub in HUBS:
        if hub not in previews:
            fails.append(f"{hub} missing from sitemap-previews.xml")

    # 8. Featured Game pages (*analysis-stats-preview*) belong in featured-games, not previews
    featured_pages = set(re.findall(r"/([A-Za-z0-9._-]*analysis-stats-preview[A-Za-z0-9._-]*\.html)", featured))
    if not featured_pages:
        fails.append("sitemap-featured-games.xml contains no analysis-stats-preview pages (unexpected)")
    leaked = set(re.findall(r"/([A-Za-z0-9._-]*analysis-stats-preview[A-Za-z0-9._-]*\.html)", previews))
    for p in sorted(leaked):
        fails.append(f"Featured page '{p}' is in sitemap-previews.xml but belongs in sitemap-featured-games.xml")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="check the public site instead of local source files")
    args = ap.parse_args()
    read = read_live if args.live else read_local
    mode = "LIVE public" if args.live else "LOCAL source"

    fails: list[str] = []
    for hub in HUBS:
        try:
            check_hub(hub, read, fails)
        except Exception as e:
            fails.append(f"{hub}: unreadable ({e})")
    sitemap_checks(read, fails)

    if fails:
        print(f"[FAIL] Preview-hub SEO regression detected ({mode}):", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(f"[PASS] Preview-hub SEO guard ({mode}): all 4 hubs self-canonical/og:url/JSON-LD, "
          f"no stale game URLs/date tokens in head, sitemap routing correct.")
    for hub in HUBS:
        print(f"   ok {hub} -> canonical/og:url/JSON-LD = {BASE}/{hub}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
