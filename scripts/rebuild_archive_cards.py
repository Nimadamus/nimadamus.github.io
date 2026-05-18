#!/usr/bin/env python3
"""Rebuild BetLegend archive/latest discovery pages from current dated posts."""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

import audit_archive_cards as audit


ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.betlegendpicks.com"
MANIFEST = ROOT / "site-posts-manifest.json"


def display_date(iso_date: str) -> str:
    date = dt.date.fromisoformat(iso_date)
    return f"{date.strftime('%B')} {date.day}, {date.year}"


def write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8", newline="\n")


def write_manifest(posts: list[dict[str, str]]) -> None:
    payload = {
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source_of_truth": "All current root-level dated post/article/pick HTML files, excluding utility surfaces, hubs, records pages, and generated archive pages.",
        "total_posts": len(posts),
        "posts": posts,
    }
    write(MANIFEST, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")


def archive_card(post: dict[str, str]) -> str:
    return (
        '<article class="archive-card">'
        f'<div class="archive-date">{display_date(post["date"])}</div>'
        f'<h2><a href="{html.escape(post["url"])}">{html.escape(post["title"])}</a></h2>'
        f'<a class="archive-link" href="{html.escape(post["url"])}">Read page</a>'
        "</article>"
    )


def write_archive(posts: list[dict[str, str]]) -> None:
    cards = "\n".join(archive_card(post) for post in posts)
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/archive.html">
<title>Full Pick and Article Archive | BetLegendPicks</title>
<meta name="description" content="Complete reverse chronological archive of BetLegendPicks posts, articles, previews, and picks.">
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#090806;color:#f7efe1;font-family:Arial,Helvetica,sans-serif;line-height:1.55}}a{{color:#f0c977;text-decoration:none}}.wrap{{max-width:1200px;margin:0 auto;padding:34px 20px 54px}}.top{{display:flex;justify-content:space-between;gap:16px;align-items:center;flex-wrap:wrap;border-bottom:1px solid rgba(255,238,203,.16);padding-bottom:18px;margin-bottom:24px}}.brand{{font-weight:900;text-transform:uppercase;letter-spacing:.08em;color:#fff}}h1{{margin:0 0 8px;font-size:clamp(30px,4vw,52px);line-height:1.05}}.meta{{color:#b9ad99;margin:0}}.archive-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}.archive-card{{border:1px solid rgba(255,238,203,.14);background:#171410;border-radius:9px;padding:18px;min-height:178px;display:flex;flex-direction:column}}.archive-date{{color:#b9ad99;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}}.archive-card h2{{font-size:20px;line-height:1.18;margin:0 0 16px;text-transform:uppercase;flex:1}}.archive-link{{font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.06em}}@media(max-width:900px){{.archive-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:620px){{.archive-grid{{grid-template-columns:1fr}}.wrap{{padding:24px 16px 44px}}}}
</style>
</head>
<body>
<main class="wrap">
<div class="top"><a class="brand" href="index.html">BetLegend Picks</a><nav><a href="index.html">Home</a> &nbsp; <a href="blog.html">Latest Picks</a></nav></div>
<h1>Full Pick and Article Archive</h1>
<p class="meta">{len(posts)} published posts, articles, previews, and picks. Newest first. Source: site-posts-manifest.json.</p>
<section class="archive-grid">
{cards}
</section>
</main>
</body>
</html>
"""
    write(ROOT / "archive.html", content)


def write_latest(posts: list[dict[str, str]]) -> None:
    rows = "\n".join(
        f'<li><a href="{html.escape(post["url"])}">{html.escape(post["title"])}</a> <span>{display_date(post["date"])}</span></li>'
        for post in posts
    )
    content = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{BASE_URL}/latest.html">
<title>Latest Published Pages | BetLegendPicks</title>
<meta name="description" content="Latest published BetLegendPicks pages, generated from the complete dated post manifest.">
</head>
<body>
<main>
<h1>Latest Published Pages</h1>
<p>All published pages from the complete archive source, newest first. Full card archive: <a href="archive.html">archive.html</a>.</p>
<ul>
{rows}
</ul>
</main>
</body>
</html>
"""
    write(ROOT / "latest.html", content)


def main() -> int:
    posts = audit.collect_posts()
    if not posts:
        raise SystemExit("No posts found; refusing to write archive files.")
    write_manifest(posts)
    write_archive(posts)
    write_latest(posts)
    print(f"Rebuilt archive.html, latest.html, and site-posts-manifest.json with {len(posts)} posts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
