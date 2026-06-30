#!/usr/bin/env python3
"""
Regenerate the STATIC, crawlable internal links on index.html so Googlebot
discovers newly published pages every day WITHOUT executing JavaScript.

Two regions (both bounded by HTML-comment markers, idempotent):
  1. <!--PICKS_GRID_START--> ... <!--PICKS_GRID_END-->  inside #picks-grid
     Static fallback pick cards, newest-first, from homepage-picks-data.js.
  2. <!--CRAWL_LINKS_START--> ... <!--CRAWL_LINKS_END-->  before <footer>
     A "Recently Published" link list covering picks + featured games + every
     sport preview (from homepage-picks-data.js, featured-games-data.js and
     scripts/*-calendar.js), newest-first.

WHY THIS EXISTS (June 30, 2026): the daily pick cards / featured game / sport
previews are injected client-side (homepage-picks-data.js, calendar JS), so the
raw HTML Googlebot crawls had NO links to any new page -> every daily page came
back "URL is unknown to Google / referringUrls NONE" in GSC URL Inspection.
A one-time static snapshot was added once and then froze (stale at May 2026).
This script makes the static links regenerate on EVERY publish; the pre-commit
hook runs it and validate_homepage_crawl_links.py blocks a stale commit.
"""
import re, sys, os, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
PICKS_DATA = os.path.join(ROOT, "homepage-picks-data.js")
FEATURED_DATA = os.path.join(ROOT, "featured-games-data.js")
SCRIPTS = os.path.join(ROOT, "scripts")

MONTHS = {m: i for i, m in enumerate(
    ["January","February","March","April","May","June","July","August",
     "September","October","November","December"], 1)}

PICKS_GRID_N = 12      # static fallback cards rendered in #picks-grid
CRAWL_N = 60           # links in the "Recently Published" crawl list


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def read(p):
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


def norm_date(s):
    """'June 30, 2026' or '2026-06-30' -> '2026-06-30' (or '' if unparseable)."""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return s
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})$", s)
    if m and m.group(1) in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}"
    return ""


def parse_homepage_picks():
    """Return list of dicts {sport,title,date,url,image,result} newest-first."""
    txt = read(PICKS_DATA)
    body = txt[txt.index("HOMEPAGE_PICKS"):]
    out = []
    for blk in re.findall(r"\{[^{}]*\}", body):
        def g(k):
            m = re.search(k + r'\s*:\s*"((?:[^"\\]|\\.)*)"', blk)
            return m.group(1).replace('\\"', '"') if m else ""
        url = g("url")
        if not url or ".html" not in url:
            continue
        out.append({"sport": g("sport"), "title": g("title"), "date": g("date"),
                    "url": url, "image": g("image"), "result": g("result")})
    return out  # file is already newest-first


def parse_dated_pages(path):
    """Parse `{ date: "YYYY-MM-DD", page: "x.html", title: "..." }` entries."""
    if not os.path.exists(path):
        return []
    txt = read(path)
    out = []
    for m in re.finditer(r'date:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"\s*,\s*page:\s*"([^"]+)"\s*,\s*title:\s*"((?:[^"\\]|\\.)*)"', txt):
        out.append({"date": m.group(1), "page": m.group(2), "title": m.group(3).replace('\\"', '"')})
    return out


def badge(result):
    r = (result or "").upper()
    return {"W": ("win", "WIN"), "L": ("lost", "LOST"), "P": ("push", "PUSH")}.get(r, ("pending", "PENDING"))


def build_pick_cards(picks):
    cards = []
    for p in picks[:PICKS_GRID_N]:
        bcls, btxt = badge(p["result"])
        img = p["image"] or "newlogo.png"
        cards.append(
            f'        <a href="{esc(p["url"])}" class="pick-card">\n'
            f'          <div class="pick-card-header"><span class="pick-card-title">{esc(p["title"])}</span></div>\n'
            f'          <div class="pick-card-img-wrap"><img class="pick-card-img" src="{esc(img)}" alt="{esc(p["title"])}" onerror="this.onerror=null;this.src=\'newlogo.png\'"></div>\n'
            f'          <div class="pick-card-meta"><span class="pick-sport-tag">{esc(p["sport"] or "MLB")}</span><span class="pick-result-badge {bcls}">{btxt}</span></div>\n'
            f'          <div class="pick-card-footer"><span class="pick-published-label">Published</span><span class="pick-published-date">{esc(p["date"])}</span></div>\n'
            f'        </a>'
        )
    return "\n".join(cards)


def build_crawl_links(picks):
    seen = {}
    # picks
    for p in picks:
        d = norm_date(p["date"])
        if p["url"] not in seen:
            seen[p["url"]] = {"page": p["url"], "title": p["title"], "date": d}
    # featured + every sport calendar
    sources = [FEATURED_DATA] + [os.path.join(SCRIPTS, f) for f in os.listdir(SCRIPTS)
                                 if f.endswith("-calendar.js")]
    for src in sources:
        for e in parse_dated_pages(src):
            if e["page"] not in seen and e["page"].endswith(".html"):
                seen[e["page"]] = e
    items = sorted(seen.values(), key=lambda x: x.get("date") or "", reverse=True)[:CRAWL_N]
    links = "".join(f'<a href="{esc(i["page"])}">{esc(i["title"] or i["page"])}</a>' for i in items)
    return (
        '<nav class="seo-crawl-links" aria-label="Recently published pages" '
        'style="max-width:1200px;margin:30px auto 0;padding:24px 18px;border-top:1px solid rgba(255,238,203,.13);">\n'
        '  <h2 style="font-family:Oswald,sans-serif;font-size:18px;text-transform:uppercase;letter-spacing:2px;color:#aaa091;margin-bottom:14px;">Recently Published</h2>\n'
        '  <div style="display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;line-height:1.7;">' + links + '</div>\n'
        '</nav>'
    )


def replace_between(html, start, end, payload):
    s = html.index(start) + len(start)
    e = html.index(end)
    return html[:s] + "\n" + payload + "\n        " + html[e:]


def main():
    picks = parse_homepage_picks()
    if not picks:
        print("ERROR: no HOMEPAGE_PICKS parsed", file=sys.stderr)
        return 2
    html = read(INDEX)
    for marker in ("<!--PICKS_GRID_START", "<!--PICKS_GRID_END-->",
                   "<!--CRAWL_LINKS_START", "<!--CRAWL_LINKS_END-->"):
        if marker not in html:
            print(f"ERROR: marker {marker} missing from index.html", file=sys.stderr)
            return 2
    # 1) static pick cards
    s = html.index("<!--PICKS_GRID_START")
    s = html.index("-->", s) + 3
    e = html.index("<!--PICKS_GRID_END-->")
    html = html[:s] + "\n" + build_pick_cards(picks) + "\n        " + html[e:]
    # 2) crawl-links nav
    s = html.index("<!--CRAWL_LINKS_START")
    s = html.index("-->", s) + 3
    e = html.index("<!--CRAWL_LINKS_END-->")
    html = html[:s] + "\n" + build_crawl_links(picks) + "\n" + html[e:]
    # 3) stamp
    today = picks[0]["date"] or datetime.date.today().isoformat()
    html = re.sub(r'(<span class="section-chip" id="latest-picks-stamp">)[^<]*(</span>)',
                  rf'\g<1>Newest published picks first - updated {esc(today)}\g<2>', html)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[sync_homepage_crawl_links] {min(len(picks),PICKS_GRID_N)} static pick cards + "
          f"crawl links regenerated (newest pick: {picks[0]['url']} / {today})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
