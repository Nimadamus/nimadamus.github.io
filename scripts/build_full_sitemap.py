#!/usr/bin/env python3
"""Build a complete sitemap.xml with every HTML page in the repo."""
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.betlegendpicks.com"

EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".github", ".vscode"}
EXCLUDE_FILES = {
    "google6f74b54ecd988601.html",
    "BingSiteAuth.xml",
    "404.html",
}

def url_for(rel_path: str) -> str:
    rel_path = rel_path.replace("\\", "/")
    if rel_path.endswith("/index.html"):
        rel_path = rel_path[:-len("index.html")]
    if rel_path == "index.html":
        return DOMAIN + "/"
    return DOMAIN + "/" + rel_path

def collect_html_files():
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if not fn.endswith(".html"):
                continue
            if fn in EXCLUDE_FILES:
                continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, REPO).replace("\\", "/")
            out.append((rel, full))
    return out

def main():
    files = collect_html_files()
    files.sort()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    seen = set()
    rows = []
    for rel, full in files:
        loc = url_for(rel)
        if loc in seen:
            continue
        seen.add(loc)
        try:
            mtime = os.path.getmtime(full)
            lastmod = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime("%Y-%m-%d")
        except OSError:
            lastmod = today

        if loc == DOMAIN + "/":
            priority = "1.0"
            changefreq = "daily"
        elif rel.endswith(("-records.html", "records.html")) or rel in {"sitemap.html"}:
            priority = "0.8"
            changefreq = "weekly"
        elif "-previews.html" in rel or rel.endswith((
            "nba.html", "nhl.html", "mlb.html", "nfl.html",
            "ncaab.html", "ncaaf.html", "soccer.html",
        )):
            priority = "0.9"
            changefreq = "daily"
        elif "/pro/" in rel or rel.startswith("pro/"):
            priority = "0.6"
            changefreq = "weekly"
        else:
            priority = "0.7"
            changefreq = "weekly"

        rows.append(
            "  <url>\n"
            f"    <loc>{escape(loc)}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            f"    <priority>{priority}</priority>\n"
            "  </url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )

    out_path = os.path.join(REPO, "sitemap.xml")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(xml)

    print(f"Wrote {out_path} with {len(rows)} URLs")

if __name__ == "__main__":
    main()
