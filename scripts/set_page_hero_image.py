"""Set the unique hero image on a preview/review page per PREVIEW_PAGE_STANDARD.md.

Usage:
  python scripts/set_page_hero_image.py <page.html> <image_url> "<alt text>" "<figcaption>"

Does, atomically per page:
  1. Verifies the image URL returns HTTP 200 and an image content-type (hard gate).
  2. Rejects newlogo.png / logos / data: URIs.
  3. Updates or inserts og:image + twitter:image metas.
  4. Updates NewsArticle JSON-LD "image" field when present.
  5. Inserts <figure class="hero-figure"> (face-safe .feature-photo) at the top of
     the article if the page has no real hero figure yet.
  6. Records {file, url} in reports/image_ledger/<page>.json for the global
     uniqueness sweep.
Exit 0 = success. Any other exit = page NOT updated; do not report it as done.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fail(msg):
    print("FAIL:", msg)
    sys.exit(2)


def verify_image(url):
    if "newlogo" in url or url.startswith("data:"):
        fail("logo/data URI not allowed")
    if re.search(r"teamlogos|/logos?/", url):
        fail("team logo URLs not allowed as hero")
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "BetLegendImageBot/1.0 (https://www.betlegendpicks.com; nj2121@gmail.com)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status = r.status
            ctype = r.headers.get("Content-Type", "")
            data = r.read(2048)
    except Exception as e:
        fail(f"fetch error: {e}")
    if status != 200:
        fail(f"HTTP {status}")
    if not ctype.startswith("image/"):
        fail(f"content-type {ctype}")
    print(f"image OK: HTTP {status} {ctype}")


def set_meta(html, prop_re, tag_template, value):
    m = re.search(prop_re, html)
    if m:
        tag = m.group(0)
        new = re.sub(r'content="[^"]*"', 'content="%s"' % value, tag)
        return html.replace(tag, new, 1), "updated"
    return html.replace("</head>", tag_template % value + "\n</head>", 1), "inserted"


def main():
    if len(sys.argv) != 5:
        fail("usage: set_page_hero_image.py <page.html> <url> <alt> <caption>")
    page, url, alt, caption = sys.argv[1:5]
    path = os.path.join(ROOT, os.path.basename(page))
    if not os.path.exists(path):
        fail("page not found: " + path)
    verify_image(url)
    with open(path, encoding="utf-8") as f:
        html = f.read()
    orig = html
    crlf = html.count("\r\n") > html.count("\n") // 2

    html, a1 = set_meta(html, r'<meta[^>]+property="og:image"[^>]*/?>|<meta[^>]+content="[^"]*"[^>]+property="og:image"[^>]*/?>',
                        '<meta property="og:image" content="%s">', url)
    html, a2 = set_meta(html, r'<meta[^>]+name="twitter:image"[^>]*/?>|<meta[^>]+content="[^"]*"[^>]+name="twitter:image"[^>]*/?>',
                        '<meta name="twitter:image" content="%s">', url)
    # NewsArticle schema image
    def fix_schema(m):
        block = m.group(0)
        if '"NewsArticle"' not in block:
            return block
        if '"image"' in block:
            return re.sub(r'"image"\s*:\s*"[^"]*"', '"image": "%s"' % url, block)
        return block.replace('"@type": "NewsArticle",', '"@type": "NewsArticle",\n  "image": "%s",' % url, 1)\
                    .replace('"@type":"NewsArticle",', '"@type":"NewsArticle","image":"%s",' % url, 1)
    html = re.sub(r"<script type=\"application/ld\+json\">.*?</script>", fix_schema, html, flags=re.S)

    inserted_fig = False
    has_fig = re.search(r'class="(?:hero-figure|feature-photo|pick-article-hero__figure)"', html)
    replaced_fig = False
    if has_fig:
        # replace the existing hero figure's img src/alt (+figcaption when adjacent)
        fig_img = re.search(
            r'(<figure class="(?:hero-figure|pick-article-hero__figure)"[^>]*>\s*<img[^>]*\bsrc=")[^"]*("[^>]*\balt=")[^"]*("[^>]*/?>)(\s*<figcaption>)?([^<]*)?(</figcaption>)?',
            html)
        if fig_img is None:
            fig_img = re.search(r'(<img[^>]*class="feature-photo"[^>]*\bsrc=")[^"]*("[^>]*\balt=")[^"]*("[^>]*/?>)', html)
            if fig_img is None:
                fig_img = re.search(r'(<img[^>]*\bsrc=")[^"]*("[^>]*class="feature-photo"[^>]*\balt=")[^"]*("[^>]*/?>)', html)
    if not has_fig:
        # bare classless <figure><img> hero (older pick pages)
        bare = re.search(r'(<figure[^>]*>\s*<img[^>]*\bsrc=")[^"]*("[^>]*\balt=")[^"]*("[^>]*/?>)', html)
        if bare:
            g = bare.groups()
            html = html[: bare.start()] + g[0] + url + g[1] + alt.replace('"', "'") + g[2] + html[bare.end():]
            replaced_fig = True
            has_fig = True
        if fig_img:
            g = fig_img.groups()
            rep = g[0] + url + g[1] + alt.replace('"', "'") + g[2]
            if len(g) > 3 and g[3]:
                rep += g[3] + caption + (g[5] or "</figcaption>")
            html = html[: fig_img.start()] + rep + html[fig_img.end():]
            replaced_fig = True
    if not has_fig:
        fig = ('<figure class="hero-figure">\n'
               '<img class="feature-photo" src="%s" alt="%s"/>\n'
               '<figcaption>%s</figcaption>\n</figure>\n' % (url, alt.replace('"', "'"), caption))
        for pat, mode in (
            (r'<main class="main-content"[^>]*>', "after"),          # boards
            (r'<div class="game-card"[^>]*>', "after"),               # old featured
            (r'<article class="game-preview[^"]*"[^>]*>', "after"),   # drifted featured
            (r'<div class="content-wrapper"[^>]*>', "after"),
            (r'<div class="page-wrapper"[^>]*>', "after"),            # featured (soccer/UCL)
        ):
            m = re.search(pat, html)
            if m:
                html = html[: m.end()] + "\n" + fig + html[m.end():]
                inserted_fig = True
                break
        if not inserted_fig:
            fail("no insertion point found for hero figure")

    if html != orig:
        with open(path, "w", encoding="utf-8", newline="\r\n" if crlf else "\n") as f:
            f.write(html)
    led_dir = os.path.join(ROOT, "reports", "image_ledger")
    os.makedirs(led_dir, exist_ok=True)
    with open(os.path.join(led_dir, os.path.basename(page) + ".json"), "w", encoding="utf-8") as f:
        json.dump({"file": os.path.basename(page), "url": url, "alt": alt, "caption": caption}, f)
    fig_state = "inserted" if inserted_fig else ("replaced" if replaced_fig else "already-present")
    print("OK %s og:%s tw:%s figure:%s" % (os.path.basename(page), a1, a2, fig_state))


if __name__ == "__main__":
    main()
