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
import argparse
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
ANALYSIS_N = 7
PICK_URL_RE = re.compile(r"-(mlb|nhl|nba|nfl|ncaab|ncaaf|soccer)-pick\.html$", re.I)
SPORT_FALLBACK_IMG = {
    "MLB": "images/mlb-great-american-ballpark-yankees-reds.webp",
    "NFL": "images/nfl-panthers-jets-betting-analysis-oct-19-2025.png",
    "NBA": "images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp",
    "NHL": "images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.png",
    "Soccer": "images/soccer-analysis-action-centered-preview.jpg",
    "NCAAB": "images/kansas-state-bowling-green-1h-under-76-ncaab-december-2025.webp",
    "NCAAF": "images/nfl-panthers-jets-betting-analysis-oct-19-2025.png",
}
EVERGREEN_DISCOVERY = [
    ("pro/index.html", "BetLegend Pro"),
    ("kelly-criterion/simple-guide.html", "Simple Kelly Criterion Guide"),
    ("kelly-criterion/parlays.html", "Kelly Criterion for Parlays"),
    ("ev-calculator/positive-ev-guide.html", "Positive EV Betting Guide"),
    ("bankroll-management/unit-sizing.html", "Unit Sizing"),
    ("records.html", "Verified Records"),
]


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
        '  <p style="margin-top:14px;font-size:13px;"><a href="complete-archive.html" style="color:#e8b85c;font-weight:700;">View the complete pick &amp; preview archive &rarr;</a></p>\n'
        '</nav>'
    )


def sport_from_page(page):
    p = (page or "").lower()
    if "soccer" in p or "champions-league" in p or "laliga" in p or "europa" in p:
        return "Soccer"
    if "nfl" in p or "preseason" in p and "nfl" in p:
        return "NFL"
    if "nba" in p:
        return "NBA"
    if "nhl" in p:
        return "NHL"
    if "ncaab" in p or "college-basketball" in p:
        return "NCAAB"
    if "ncaaf" in p or "college-football" in p:
        return "NCAAF"
    return "MLB"


def is_pick_url(page):
    return bool(PICK_URL_RE.search(page or "")) or (page or "").endswith("-mlb-pick.html")


def og_image(page):
    path = os.path.join(ROOT, page)
    if not os.path.isfile(path):
        return ""
    head = read(path)[:4000]
    m = re.search(r'property=["\']og:image["\'][^>]*content=["\']([^"\']+)', head, re.I)
    if not m:
        m = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', head, re.I)
    if m:
        src = m.group(1)
        if src.startswith("https://www.betlegendpicks.com/"):
            src = src[len("https://www.betlegendpicks.com/"):]
        return src
    return ""


def analysis_items(picks):
    seen = {}
    sources = [FEATURED_DATA] + [os.path.join(SCRIPTS, f) for f in os.listdir(SCRIPTS)
                                 if f.endswith("-calendar.js")]
    for src in sources:
        for e in parse_dated_pages(src):
            page = e["page"]
            if not page.endswith(".html") or is_pick_url(page) or page in seen:
                continue
            seen[page] = e
    for p in picks:
        url = p["url"]
        if is_pick_url(url) or url in seen:
            continue
        if any(k in url for k in ("analysis", "preview", "slate", "fifteen-game", "soccer", "nfl", "preseason")):
            seen[url] = {"page": url, "title": p["title"], "date": norm_date(p["date"])}
    keys = ("analysis-stats-preview", "fifteen-game", "soccer.html", "-soccer.html",
            "preseason", "champions-league", "europa-", "laliga")
    for name in os.listdir(ROOT):
        if not name.endswith(".html") or is_pick_url(name) or name in seen:
            continue
        if not any(k in name for k in keys) and "soccer" not in name and "nfl" not in name:
            continue
        path = os.path.join(ROOT, name)
        head = read(path)[:3500]
        dm = re.search(r"FORCED_PAGE_DATE\s*=\s*'(\d{4}-\d{2}-\d{2})'", head)
        if not dm:
            dm = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})', head)
        d = dm.group(1) if dm else ""
        tm = re.search(r"<title>([^<]+)</title>", head, re.I)
        title = (tm.group(1) if tm else name).replace(" | BetLegend", "").strip()
        seen[name] = {"page": name, "title": title, "date": d}
    items = sorted(seen.values(), key=lambda x: x.get("date") or "", reverse=True)
    return items


def build_analysis_cards(items):
    cards = []
    for i, e in enumerate(items[:ANALYSIS_N]):
        sport = sport_from_page(e["page"])
        tag = "red" if sport == "MLB" else ("blue" if sport in ("NBA", "NFL") else "")
        tag_attr = f' tag {tag}'.strip() if tag else "tag"
        img = og_image(e["page"]) or SPORT_FALLBACK_IMG.get(sport, "newlogo.png")
        title = e.get("title") or e["page"].replace(".html", "").replace("-", " ").title()
        blurb = title if len(title) < 120 else title[:117] + "..."
        d = e.get("date") or ""
        if re.match(r"\d{4}-\d{2}-\d{2}$", d):
            dt = datetime.date.fromisoformat(d)
            dlabel = dt.strftime("%B %d, %Y").replace(" 0", " ")
        else:
            dlabel = d
        feat = " feature" if i == 0 else ""
        cards.append(
            f'      <a class="article-card{feat}" data-card-category="{esc(sport)}" data-card-section="article" href="{esc(e["page"])}">\n'
            f'        <img data-card-image src="{esc(img)}" alt="{esc(title)}">\n'
            f'        <div class="card-body">\n'
            f'          <span class="{tag_attr}">{esc(sport)}</span>\n'
            f'          <h3>{esc(title)}</h3>\n'
            f'          <p>{esc(blurb)}</p>\n'
            f'          <time>{esc(dlabel)}</time>\n'
            f'        </div>\n'
            f'      </a>'
        )
    return "\n".join(cards)


def build_static_discovery(items):
    today = datetime.date.today().strftime("%B %d, %Y").replace(" 0", " ")
    lis = []
    for e in items[:12]:
        d = e.get("date") or ""
        if re.match(r"\d{4}-\d{2}-\d{2}$", d):
            dt = datetime.date.fromisoformat(d)
            dlabel = dt.strftime("%B %d, %Y").replace(" 0", " ")
        else:
            dlabel = d
        title = e.get("title") or e["page"]
        lis.append(
            f'      <li><a href="{esc(e["page"])}">{esc(title)}</a> '
            f'<span class="static-discovery-date">{esc(dlabel)}</span></li>'
        )
    for href, title in EVERGREEN_DISCOVERY:
        lis.append(f'      <li><a href="{esc(href)}">{esc(title)}</a></li>')
    return (
        '<section class="static-discovery-links" aria-labelledby="static-discovery-heading">\n'
        '  <h2 id="static-discovery-heading">Latest Published Pages</h2>\n'
        f'  <p>Static crawl links updated {esc(today)}. These links are present in raw HTML for search engines.</p>\n'
        '  <ul>\n' + "\n".join(lis) + "\n  </ul>\n"
        "</section>"
    )


def replace_between(html, start, end, payload):
    s = html.index(start) + len(start)
    e = html.index(end)
    return html[:s] + "\n" + payload + "\n        " + html[e:]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-archive", action="store_true",
                    help="Do not rebuild complete-archive.html")
    args = ap.parse_args(argv)
    picks = parse_homepage_picks()
    if not picks:
        print("ERROR: no HOMEPAGE_PICKS parsed", file=sys.stderr)
        return 2
    html = read(INDEX)
    for marker in ("<!--PICKS_GRID_START", "<!--PICKS_GRID_END-->",
                   "<!--CRAWL_LINKS_START", "<!--CRAWL_LINKS_END-->",
                   "<!--ANALYSIS_GRID_START-->", "<!--ANALYSIS_GRID_END-->",
                   "<!-- STATIC_DISCOVERY_LINKS_START -->", "<!-- STATIC_DISCOVERY_LINKS_END -->"):
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
    analysis = analysis_items(picks)
    # 4) Latest Analysis cards (previews/featured, not sheet picks)
    s = html.index("<!--ANALYSIS_GRID_START-->") + len("<!--ANALYSIS_GRID_START-->")
    e = html.index("<!--ANALYSIS_GRID_END-->")
    html = html[:s] + "\n" + build_analysis_cards(analysis) + "\n      " + html[e:]
    # 5) Frozen May 18 discovery list -> current URLs
    s = html.index("<!-- STATIC_DISCOVERY_LINKS_START -->") + len("<!-- STATIC_DISCOVERY_LINKS_START -->")
    e = html.index("<!-- STATIC_DISCOVERY_LINKS_END -->")
    html = html[:s] + "\n" + build_static_discovery(analysis) + "\n" + html[e:]
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[sync_homepage_crawl_links] {min(len(picks),PICKS_GRID_N)} static pick cards + "
          f"{min(len(analysis), ANALYSIS_N)} analysis cards + crawl links "
          f"(newest pick: {picks[0]['url']} / {today})")
    if not args.skip_archive:
        try:
            import build_static_archive
            build_static_archive.main()
        except Exception as e:
            print(f"[sync_homepage_crawl_links] WARN: complete-archive.html not rebuilt: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
