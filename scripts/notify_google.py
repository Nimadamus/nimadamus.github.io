#!/usr/bin/env python3
"""Tell Google about new BetLegend URLs without regenerating the site.

Does NOT noindex, rename, 404, or rebuild sitemaps. Appends missing locs
to sitemap-posts.xml only. Inspects live URLs in GSC. Submits the sitemap.

Google has no public "Request indexing" API for regular pages. Inspect +
sitemap submit is everything the API allows. Unknown URLs still need a
manual GSC Request indexing click until Google starts crawling them.

  python scripts/notify_google.py
  python scripts/notify_google.py --days 7 --url some-card.html
  python scripts/notify_google.py --no-gsc   # sitemap append only (CI)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
BASE = "https://www.betlegendpicks.com"
SITE = BASE + "/"
SITEMAP = BASE + "/sitemap.xml"
POSTS = REPO / "sitemap-posts.xml"
PICKS_JS = REPO / "homepage-picks-data.js"
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
CRED_CANDIDATES = [
    Path(r"C:\Users\BL\google_credentials.json"),
    Path(r"C:\Users\Nima\google_credentials.json"),
]
STATE = Path(r"C:\Users\BL\logs\betlegend-notify-google-state.json")
SKIP_NAMES = {
    "index.html",
    "404.html",
    "preview.html",
    "index-hero-preview.html",
    "preview-endgame-daily-card.html",
}

ET.register_namespace("", NS)


def cred_path() -> Path | None:
    for p in CRED_CANDIDATES:
        if p.exists():
            return p
    return None


def abs_url(name: str) -> str:
    name = name.strip().lstrip("/")
    if name.startswith("http"):
        return name
    if name in ("", "index.html"):
        return SITE
    return f"{BASE}/{name}"


def parse_picks(days: int, all_picks: bool = False) -> list[str]:
    if not PICKS_JS.exists():
        return []
    text = PICKS_JS.read_text(encoding="utf-8", errors="ignore")
    cutoff = dt.date.min if all_picks or days <= 0 else dt.date.today() - dt.timedelta(days=days)
    months = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    }
    out: list[str] = []
    for m in re.finditer(
        r"date:\s*\"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\".*?url:\s*\"([^\"]+)\"",
        text,
        re.S,
    ):
        mon, day, year, url = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            d = dt.date(int(year), months[mon.lower()], int(day))
        except Exception:
            continue
        if d >= cutoff:
            out.append(abs_url(url))
    # objects may list url before date
    for m in re.finditer(
        r"url:\s*\"([^\"]+)\".*?date:\s*\"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})\"",
        text,
        re.S,
    ):
        url, mon, day, year = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            d = dt.date(int(year), months[mon.lower()], int(day))
        except Exception:
            continue
        if d >= cutoff:
            u = abs_url(url)
            if u not in out:
                out.append(u)
    return out


def git_added_html(days: int) -> list[str]:
    try:
        raw = subprocess.check_output(
            [
                "git", "log", f"--since={days} days ago", "--diff-filter=A",
                "--name-only", "--pretty=format:", "--", "*.html",
            ],
            cwd=REPO,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return []
    urls = []
    for line in raw.splitlines():
        rel = line.strip().replace("\\", "/")
        if not rel.endswith(".html"):
            continue
        name = Path(rel).name
        if name in SKIP_NAMES or "/" in rel:
            continue
        if name.startswith("google") and name.endswith(".html"):
            continue
        urls.append(abs_url(rel))
    return urls


def live_ok(url: str) -> bool:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "BetLegend-notify-google"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return 200 <= r.status < 400
    except urllib.error.HTTPError as e:
        return 200 <= e.code < 400
    except Exception:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BetLegend-notify-google"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return 200 <= r.status < 400
        except Exception:
            return False


def sitemap_locs() -> set[str]:
    if not POSTS.exists():
        return set()
    tree = ET.parse(POSTS)
    return {el.text.strip() for el in tree.findall(f".//{{{NS}}}loc") if el.text}


def append_sitemap(urls: list[str]) -> list[str]:
    if not POSTS.exists() or not urls:
        return []
    tree = ET.parse(POSTS)
    root = tree.getroot()
    have = {el.text.strip() for el in root.findall(f"{{{NS}}}url/{{{NS}}}loc") if el.text}
    today = dt.date.today().isoformat()
    added = []
    for url in urls:
        if url in have or url.rstrip("/") == BASE:
            continue
        if url.endswith("/blog.html") is False and not url.endswith(".html"):
            continue
        el = ET.Element(f"{{{NS}}}url")
        loc = ET.SubElement(el, f"{{{NS}}}loc")
        loc.text = url
        last = ET.SubElement(el, f"{{{NS}}}lastmod")
        last.text = today
        freq = ET.SubElement(el, f"{{{NS}}}changefreq")
        freq.text = "daily"
        pri = ET.SubElement(el, f"{{{NS}}}priority")
        pri.text = "0.8"
        root.insert(0, el)
        have.add(url)
        added.append(url)
    if added:
        tree.write(POSTS, encoding="utf-8", xml_declaration=True)
    return added


def gsc_service():
    path = cred_path()
    if not path:
        return None
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    creds = service_account.Credentials.from_service_account_file(
        str(path), scopes=["https://www.googleapis.com/auth/webmasters"]
    )
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def inspect_url(svc, url: str) -> dict:
    for attempt in range(4):
        try:
            r = svc.urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": SITE}
            ).execute()
            idx = r.get("inspectionResult", {}).get("indexStatusResult", {})
            return {
                "url": url,
                "coverage": idx.get("coverageState", "?"),
                "verdict": idx.get("verdict", "?"),
                "lastCrawl": idx.get("lastCrawlTime", ""),
            }
        except Exception as e:
            if attempt < 3:
                time.sleep(2 * (attempt + 1))
                continue
            return {"url": url, "coverage": "API_ERROR", "verdict": str(e)[:80], "lastCrawl": ""}
    return {"url": url, "coverage": "RETRY_FAIL", "verdict": "?", "lastCrawl": ""}


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def collect(days: int, extra: list[str], all_picks: bool = False, git_added: bool = True) -> list[str]:
    urls: list[str] = []
    added = git_added_html(days) if git_added and not all_picks else []
    for u in extra + parse_picks(days, all_picks=all_picks) + added + [SITE, abs_url("blog.html")]:
        if u not in urls:
            urls.append(u)
    return urls


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--all-picks", action="store_true", help="Every homepage pick card, not just last --days")
    ap.add_argument(
        "--retry-unindexed",
        action="store_true",
        help="Also re-inspect URLs last seen as unknown/not indexed",
    )
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--no-gsc", action="store_true")
    ap.add_argument("--append-sitemap", action="store_true")
    args = ap.parse_args()

    extra = [abs_url(u) for u in args.url]
    if args.retry_unindexed:
        bad = {
            "URL is unknown to Google",
            "Discovered - currently not indexed",
            "Crawled - currently not indexed",
        }
        extra.extend(u for u, v in load_state().items() if v.get("coverage") in bad)
    urls = collect(
        args.days,
        extra,
        all_picks=args.all_picks,
        git_added=not args.all_picks,
    )
    article_urls = [u for u in urls if u not in (SITE, abs_url("blog.html"))]
    do_append = args.no_gsc or args.append_sitemap
    added = append_sitemap(article_urls) if do_append else []
    if added:
        print("sitemap_appended", len(added))
        for u in added:
            print("  +", u)
    else:
        print("sitemap_appended", 0)

    if args.no_gsc:
        return 0

    svc = gsc_service()
    if svc is None:
        print("gsc_skip no credentials")
        return 0

    try:
        svc.sitemaps().submit(siteUrl=SITE, feedpath=SITEMAP).execute()
        print("gsc_sitemap_submit ok")
    except Exception as e:
        print("gsc_sitemap_submit_err", e)

    state = load_state()
    unknown = []
    for url in urls:
        if not live_ok(url):
            print("not_live", url)
            continue
        row = inspect_url(svc, url)
        cov = row["coverage"]
        print(f"{cov:<42} {url}")
        state[url] = {
            "coverage": cov,
            "verdict": row["verdict"],
            "lastCrawl": row["lastCrawl"],
            "checked": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        if cov in ("URL is unknown to Google", "Discovered - currently not indexed", "Crawled - currently not indexed"):
            unknown.append(url)

    save_state(state)
    print("unknown_or_not_indexed", len(unknown))
    for u in unknown:
        print("  NEED_GSC_REQUEST_INDEXING", u)
    return 0


if __name__ == "__main__":
    sys.exit(main())
