"""Retrofit preview/review pages to PREVIEW_PAGE_STANDARD.md (locked July 4, 2026).

Mechanical, insert-only structural pass:
  - <link rel="stylesheet" href="/preview-article.css"> in <head>
  - content H2s -> anchored <h2 id="..." class="section-header"> (drifted inline-styled
    and plain H2s inside article content only; matchup-info game-title H2s untouched)
  - emoji stripped from section headings
  - generic H1 ("Featured Game of the Day" / "Expert Analysis") -> title-tag-derived headline
  - toc-box built from the page's own anchored H2s / board game articles
  - share-buttons block (featured pages)
  - related-links block (sport hub / records / archive / handicapping hub)
  - BreadcrumbList JSON-LD when missing
Never deletes prose. Never touches canonicals, slugs, or existing calendar wiring.

Usage: python scripts/retrofit_preview_pages.py [--family featured|board] [--sport mlb]
       [--files f1.html f2.html] [--dry-run]
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "reports", "preview_page_audit.json")
CSS_LINK = '<link rel="stylesheet" href="/preview-article.css">'

EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿️]")

HUBS = {
    "mlb": ("mlb-previews.html", "MLB Game Previews", "mlb-records.html", "MLB Verified Records"),
    "nba": ("nba-previews.html", "NBA Game Previews", "nba-records.html", "NBA Verified Records"),
    "nhl": ("nhl-previews.html", "NHL Game Previews", "nhl-records.html", "NHL Verified Records"),
    "nfl": ("nfl.html", "NFL Game Previews", "nfl-records.html", "NFL Verified Records"),
    "ncaaf": ("ncaaf.html", "NCAAF Game Previews", "ncaaf-records.html", "NCAAF Verified Records"),
    "ncaab": ("college-basketball-previews.html", "College Basketball Previews", "ncaab-records.html", "NCAAB Verified Records"),
    "soccer": ("soccer-previews.html", "Soccer Game Previews", "soccer-records.html", "Soccer Verified Records"),
}

LOGO_SPORT = re.compile(r"teamlogos/(mlb|nba|nhl|nfl|ncaa|countries|soccer)/")


def detect_sport(fname, html, audit_sport):
    if audit_sport and audit_sport != "unknown":
        return audit_sport
    m = re.search(r"scripts/(mlb|nba|nhl|nfl|ncaaf|ncaab|soccer)-calendar\.js", html)
    if m:
        return m.group(1)
    m = LOGO_SPORT.search(html)
    if m:
        t = m.group(1)
        if t == "countries":
            return "soccer"
        if t == "ncaa":
            return "ncaab" if "basketball" in html.lower() else "ncaaf"
        return t
    return None


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:50] or "section"


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s).strip()


def ensure_css_link(html):
    if "preview-article.css" in html:
        return html, False
    return html.replace("</head>", CSS_LINK + "\n</head>", 1), True


def fix_generic_h1(html):
    m = re.search(r"<h1([^>]*)>(.*?)</h1>", html, re.S)
    if not m:
        return html, False
    inner = strip_tags(m.group(2))
    if inner not in ("Featured Game of the Day", "Expert Analysis", "Expert Analysis & Deep Dive"):
        return html, False
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    if not t:
        return html, False
    title = strip_tags(t.group(1))
    title = re.sub(r"\s*[|\-]\s*BetLegend.*$", "", title).strip()
    if len(title) < 12:
        return html, False
    new = "<h1%s>%s</h1>" % (m.group(1), title)
    return html[: m.start()] + new + html[m.end():], True


def convert_content_h2s(html):
    """Anchor content H2s. Skips game-title H2s (inside matchup-info / game-title class)."""
    changed = False
    seen = {}
    out = []
    pos = 0
    for m in re.finditer(r"<h2([^>]*)>(.*?)</h2>", html, re.S):
        attrs, inner = m.group(1), m.group(2)
        before = html[max(0, m.start() - 120): m.start()]
        out.append(html[pos: m.start()])
        pos = m.end()
        txt = strip_tags(inner)
        is_game_title = 'matchup-info' in before or 'game-title' in attrs or 'game-title' in before
        already = 'section-header' in attrs
        drifted = 'style=' in attrs
        plain = attrs.strip() == "" or re.fullmatch(r'\s*', attrs)
        clean_txt = EMOJI.sub("", txt).strip()
        if is_game_title:
            out.append(m.group(0))
            continue
        if already:
            # just strip emoji if present
            if clean_txt != txt:
                idm = re.search(r'id="([^"]+)"', attrs)
                out.append('<h2%s>%s</h2>' % (attrs, clean_txt))
                changed = True
            else:
                out.append(m.group(0))
            continue
        if drifted or plain:
            base = slugify(clean_txt)
            n = seen.get(base, 0)
            seen[base] = n + 1
            sid = base if n == 0 else f"{base}-{n+1}"
            out.append('<h2 id="%s" class="section-header">%s</h2>' % (sid, clean_txt))
            changed = True
        else:
            out.append(m.group(0))
    out.append(html[pos:])
    return "".join(out), changed


def convert_content_h3s(html):
    """June-era featured pages: plain <h3> section heads, no section-header H2s.
    Promote plain h3s to anchored section-header H2s (only when the page has no
    anchored H2 sections yet and >=3 plain h3s)."""
    if 'class="section-header"' in html:
        return html, False
    plains = re.findall(r"<h3>(.*?)</h3>", html, re.S)
    if len(plains) < 3:
        return html, False
    seen = {}
    def repl(m):
        txt = EMOJI.sub("", strip_tags(m.group(1))).strip()
        base = slugify(txt)
        n = seen.get(base, 0)
        seen[base] = n + 1
        sid = base if n == 0 else f"{base}-{n+1}"
        return '<h2 id="%s" class="section-header">%s</h2>' % (sid, txt)
    html2 = re.sub(r"<h3>(.*?)</h3>", repl, html, flags=re.S)
    return html2, html2 != html


def build_featured_toc(html):
    if 'class="toc-box"' in html:
        return html, False
    # ensure every section-header H2 has an id (any attribute order)
    seen = {}
    def ensure_id(m):
        attrs, inner = m.group(1), m.group(2)
        if "section-header" not in attrs:
            return m.group(0)
        if re.search(r'\bid="', attrs):
            return m.group(0)
        base = slugify(EMOJI.sub("", strip_tags(inner)).strip())
        n = seen.get(base, 0)
        seen[base] = n + 1
        sid = base if n == 0 else f"{base}-{n+1}"
        return '<h2 id="%s"%s>%s</h2>' % (sid, attrs, inner)
    html = re.sub(r"<h2([^>]*)>(.*?)</h2>", ensure_id, html, flags=re.S)
    heads = []
    for m in re.finditer(r"<h2([^>]*)>(.*?)</h2>", html, re.S):
        attrs, inner = m.group(1), m.group(2)
        if "section-header" not in attrs:
            continue
        idm = re.search(r'\bid="([^"]+)"', attrs)
        if idm:
            heads.append((idm.group(1), strip_tags(inner)))
    if len(heads) < 3:
        return html, False
    items = "\n".join('<li><a href="#%s">%s</a></li>' % (i, strip_tags(t)) for i, t in heads)
    toc = ('<div class="toc-box">\n<div class="toc-title">In This Preview</div>\n'
           '<ul class="toc-list">\n%s\n</ul>\n</div>\n' % items)
    # insert at start of the first preview-content or content-section div
    m = re.search(r'<div class="(?:preview-content|content-section)"[^>]*>', html)
    if not m:
        return html, False
    return html[: m.end()] + "\n" + toc + html[m.end():], True


def build_share_buttons(html):
    if re.search(r'share-buttons|Share on X|Share on Facebook|intent/tweet', html):
        return html, False
    c = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    if not c or not t:
        return html, False
    url = c.group(1)
    import urllib.parse
    title = urllib.parse.quote(strip_tags(t.group(1)).split("|")[0].strip()[:80])
    block = ('<div class="share-buttons">\n<p>Share This Analysis</p>\n'
             '<a href="https://twitter.com/intent/tweet?url=%s&amp;text=%s" style="background:#1DA1F2;" target="_blank" rel="noopener">Twitter</a>\n'
             '<a href="https://www.facebook.com/sharer/sharer.php?u=%s" style="background:#1877F2;" target="_blank" rel="noopener">Facebook</a>\n'
             '<a href="https://www.reddit.com/submit?url=%s&amp;title=%s" style="background:#FF4500;" target="_blank" rel="noopener">Reddit</a>\n'
             '</div>\n' % (url, title, url, url, title))
    m = re.search(r"</div>\s*\n?", html[html.find('class="toc-box"'):]) if 'class="toc-box"' in html else None
    if 'class="toc-box"' in html:
        idx = html.find('class="toc-box"')
        end = html.find("</div>", html.find("</ul>", idx)) + len("</div>")
        return html[:end] + "\n" + block + html[end:], True
    m2 = re.search(r'<div class="(?:preview-content|content-section)"[^>]*>', html)
    if not m2:
        return html, False
    return html[: m2.end()] + "\n" + block + html[m2.end():], True


def build_related_links(html, sport):
    if 'class="related-links"' in html or sport not in HUBS:
        return html, False
    hub, hub_label, rec, rec_label = HUBS[sport]
    block = ('<div class="related-links">\n<div class="related-title">More %s On BetLegend</div>\n<ul>\n'
             '<li><a href="%s">%s</a></li>\n'
             '<li><a href="%s">%s</a></li>\n'
             '<li><a href="complete-archive.html">Full Preview Archive</a></li>\n'
             '<li><a href="handicapping-hub.html">Today\'s Handicapping Hub</a></li>\n'
             '</ul>\n</div>\n' % (sport.upper() if sport != "soccer" else "Soccer", hub, hub_label, rec, rec_label))
    for anchor in ('<div class="back-nav">', "</main>", "<footer"):
        idx = html.find(anchor)
        if idx != -1:
            return html[:idx] + block + html[idx:], True
    return html, False


def add_board_article_ids_and_toc(html):
    """Give each game-preview article an id and build an 'On Today's Board' toc."""
    changed = False
    arts = list(re.finditer(r'<article class="game-preview[^"]*"(?![^>]*\bid=)([^>]*)>', html))
    entries = []
    offset = 0
    seen = {}
    for m in arts:
        seg = html[m.end() + offset: m.end() + offset + 1200]
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", seg, re.S)
        label = strip_tags(h2.group(1)) if h2 else "Game"
        base = "game-" + slugify(label)
        n = seen.get(base, 0)
        seen[base] = n + 1
        sid = base if n == 0 else f"{base}-{n+1}"
        tag = html[m.start() + offset: m.end() + offset]
        new_tag = tag[:-1] + ' id="%s">' % sid
        html = html[: m.start() + offset] + new_tag + html[m.end() + offset:]
        offset += len(new_tag) - len(tag)
        entries.append((sid, label))
        changed = True
    # collect ids for toc even if ids pre-existed
    if 'class="toc-box"' not in html:
        existing = re.findall(r'<article class="game-preview[^"]*"[^>]*\bid="([^"]+)"[^>]*>', html)
        if entries or existing:
            ids = entries if entries else None
            if ids is None:
                ids = []
                for sid in existing:
                    idx = html.find('id="%s"' % sid)
                    seg = html[idx: idx + 1200]
                    h2 = re.search(r"<h2[^>]*>(.*?)</h2>", seg, re.S)
                    ids.append((sid, strip_tags(h2.group(1)) if h2 else sid))
            if len(ids) >= 2:
                items = "\n".join('<li><a href="#%s">%s</a></li>' % (i, l) for i, l in ids)
                toc = ('<div class="toc-box">\n<div class="toc-title">On Today\'s Board</div>\n'
                       '<ul class="toc-list">\n%s\n</ul>\n</div>\n' % items)
                m = re.search(r'<main class="main-content"[^>]*>', html)
                if m:
                    html = html[: m.end()] + "\n" + toc + html[m.end():]
                    changed = True
    return html, changed


def add_breadcrumb(html, fname, sport):
    if '"BreadcrumbList"' in html:
        return html, False
    t = re.search(r"<title>(.*?)</title>", html, re.S)
    name = strip_tags(t.group(1)).split("|")[0].strip() if t else fname
    hub, hub_label = HUBS.get(sport, ("index.html", "Game Previews"))[:2]
    block = ('<script type="application/ld+json">\n'
             '{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":['
             '{"@type":"ListItem","position":1,"name":"Home","item":"https://www.betlegendpicks.com/"},'
             '{"@type":"ListItem","position":2,"name":"%s","item":"https://www.betlegendpicks.com/%s"},'
             '{"@type":"ListItem","position":3,"name":"%s","item":"https://www.betlegendpicks.com/%s"}]}\n'
             '</script>\n' % (hub_label, hub, name.replace('"', "'"), fname))
    return html.replace("</head>", block + "</head>", 1), True


def process(fname, meta, dry):
    path = os.path.join(ROOT, fname)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html
    sport = detect_sport(fname, html, meta.get("sport"))
    actions = []
    html, ch = ensure_css_link(html)
    if ch: actions.append("css-link")
    html, ch = fix_generic_h1(html)
    if ch: actions.append("h1")
    html, ch = convert_content_h2s(html)
    if ch: actions.append("h2-anchors")
    if meta["family"] == "featured":
        html, ch = convert_content_h3s(html)
        if ch: actions.append("h3-promote")
        html, ch = build_featured_toc(html)
        if ch: actions.append("toc")
        html, ch = build_share_buttons(html)
        if ch: actions.append("share")
    elif meta["family"] == "board":
        html, ch = add_board_article_ids_and_toc(html)
        if ch: actions.append("board-toc")
    html, ch = build_related_links(html, sport)
    if ch: actions.append("related-links")
    html, ch = add_breadcrumb(html, fname, sport)
    if ch: actions.append("breadcrumb")
    if html != orig and not dry:
        with open(path, "w", encoding="utf-8", newline="
") as f:
            f.write(html)
    return actions, sport


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=["featured", "board", "prediction-picks", "pick"])
    ap.add_argument("--sport")
    ap.add_argument("--files", nargs="*")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    audit = {r["file"]: r for r in json.load(open(AUDIT, encoding="utf-8"))}
    targets = []
    for fname, meta in audit.items():
        if args.files and fname not in args.files:
            continue
        if args.family and meta["family"] != args.family:
            continue
        if args.sport and meta["sport"] != args.sport:
            continue
        targets.append((fname, meta))
    n_changed = 0
    for fname, meta in sorted(targets):
        actions, sport = process(fname, meta, args.dry_run)
        if actions:
            n_changed += 1
            print(f"{fname} [{sport}]: {','.join(actions)}")
    print(f"-- {n_changed}/{len(targets)} pages modified{' (dry run)' if args.dry_run else ''}")


if __name__ == "__main__":
    sys.exit(main())
