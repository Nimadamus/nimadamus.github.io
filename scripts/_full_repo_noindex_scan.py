#!/usr/bin/env python3
"""Crawl EVERY public .html file in the repo against the LIVE site, checking
for meta-robots noindex and X-Robots-Tag noindex. Also reports files in repo
NOT in the sitemap, and any local file that still contains noindex."""
import os, re, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.betlegendpicks.com"
UA = "Mozilla/5.0 (noindex-audit)"
NOINDEX = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', re.I)

# skip non-public dirs
SKIP_DIRS = {".git", "node_modules", "scripts", ".github", "__pycache__",
             "handicapping-hub-archive"}

def repo_html():
    out = []
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".html"):
                rel = os.path.relpath(os.path.join(dp, fn), ROOT).replace("\\", "/")
                out.append(rel)
    return sorted(out)

def local_has_noindex(rel):
    try:
        return bool(NOINDEX.search(open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()))
    except Exception:
        return False

def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception as e:
        return None, {}, ""

def check(rel):
    url = BASE + "/" + rel
    st, hdr, body = fetch(url)
    xr = (hdr.get("X-Robots-Tag") or hdr.get("x-robots-tag") or "")
    return {
        "rel": rel, "url": url, "status": st,
        "live_noindex": bool(NOINDEX.search(body)) if body else False,
        "x_noindex": "noindex" in xr.lower(),
        "local_noindex": local_has_noindex(rel),
    }

files = repo_html()
print(f"Repo public .html files: {len(files)}")

results = []
with ThreadPoolExecutor(max_workers=20) as ex:
    for r in ex.map(check, files):
        results.append(r)

local_ni = [r for r in results if r["local_noindex"]]
live_ni  = [r for r in results if r["live_noindex"]]
x_ni     = [r for r in results if r["x_noindex"]]
non200   = [r for r in results if r["status"] not in (200,)]

print(f"LOCAL files with noindex   : {len(local_ni)}")
print(f"LIVE pages with meta noindex: {len(live_ni)}")
print(f"LIVE X-Robots-Tag noindex  : {len(x_ni)}")
print(f"Non-200 live               : {len(non200)}")

def dump(t, rows, f="rel"):
    print(f"\n--- {t} ({len(rows)}) ---")
    for r in (rows[:60] or []):
        print("  ", r["status"], r[f])
    if not rows: print("   NONE")
    if len(rows) > 60: print(f"   ...+{len(rows)-60} more")

dump("LOCAL NOINDEX", local_ni)
dump("LIVE META NOINDEX", live_ni)
dump("LIVE X-ROBOTS NOINDEX", x_ni)
dump("NON-200 (status, file)", non200)
