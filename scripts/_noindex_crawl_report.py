#!/usr/bin/env python3
"""Full-site noindex crawl report for betlegendpicks.com.
Crawls the live sitemap index -> sub-sitemaps -> every URL, checking:
HTTP status, <meta robots> noindex, X-Robots-Tag noindex, canonical, robots.txt block.
"""
import re, sys, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

BASE = "https://www.betlegendpicks.com"
SITEMAP_INDEX = BASE + "/sitemap.xml"
UA = "Mozilla/5.0 (noindex-audit)"

def fetch(url, head=False):
    req = urllib.request.Request(url, method="HEAD" if head else "GET",
                                 headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = b"" if head else r.read()
            return r.status, dict(r.headers), body.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), ""
    except Exception as e:
        return None, {}, str(e)

# --- robots.txt rules ---
def load_robots():
    _, _, txt = fetch(BASE + "/robots.txt")
    disallow = []
    for line in txt.splitlines():
        line = line.strip()
        if line.lower().startswith("disallow:"):
            rule = line.split(":", 1)[1].strip()
            if rule:
                disallow.append(rule)
    return txt, disallow

def robots_blocked(path, rules):
    for rule in rules:
        if rule.endswith("$"):
            if path.endswith(rule[:-1].replace("*", "")):
                return rule
        elif "*" in rule:
            pat = "^" + re.escape(rule).replace(r"\*", ".*")
            if re.match(pat, path):
                return rule
        elif path.startswith(rule):
            return rule
    return None

# --- collect sitemap URLs ---
def locs(xml):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)

def collect_urls():
    _, _, idx = fetch(SITEMAP_INDEX)
    subs = [u for u in locs(idx) if u.endswith(".xml")]
    if not subs:
        subs = [SITEMAP_INDEX]
    urls = []
    for s in subs:
        _, _, sx = fetch(s)
        urls += [u for u in locs(sx) if not u.endswith(".xml")]
    return idx, subs, sorted(set(urls))

ROBOTS_TXT, ROBOTS_RULES = load_robots()
SITEMAP_IDX_XML, SUBS, URLS = collect_urls()

NOINDEX_META = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', re.I)
CANON = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', re.I)

def check(url):
    path = urlparse(url).path
    blocked = robots_blocked(path, ROBOTS_RULES)
    status, headers, body = fetch(url)
    xrobots = headers.get("X-Robots-Tag", "") or headers.get("x-robots-tag", "")
    xnoindex = "noindex" in xrobots.lower()
    meta_noindex = bool(NOINDEX_META.search(body)) if body else False
    m = CANON.search(body) if body else None
    canon = m.group(1) if m else ""
    return {
        "url": url, "status": status, "meta_noindex": meta_noindex,
        "xnoindex": xnoindex, "xrobots": xrobots, "blocked": blocked,
        "canon": canon,
    }

results = []
with ThreadPoolExecutor(max_workers=16) as ex:
    for r in ex.map(check, URLS):
        results.append(r)

total = len(results)
ok200 = sum(1 for r in results if r["status"] == 200)
non200 = [r for r in results if r["status"] != 200]
meta_ni = [r for r in results if r["meta_noindex"]]
x_ni = [r for r in results if r["xnoindex"]]
blocked = [r for r in results if r["blocked"]]
# canonical failure = 200 page with no canonical tag at all
canon_fail = [r for r in results if r["status"] == 200 and not r["canon"]]

print("="*70)
print("BETLEGENDPICKS.COM FULL SITEMAP NOINDEX CRAWL REPORT")
print("="*70)
print(f"Sitemap index : {SITEMAP_INDEX}")
print(f"Sub-sitemaps  : {len(SUBS)}")
for s in SUBS: print(f"   - {s}")
print("-"*70)
print(f"TOTAL URLs checked        : {total}")
print(f"HTTP 200                  : {ok200}")
print(f"Non-200                   : {len(non200)}")
print(f"meta robots noindex       : {len(meta_ni)}")
print(f"X-Robots-Tag noindex      : {len(x_ni)}")
print(f"robots.txt blocked        : {len(blocked)}")
print(f"canonical missing (200)   : {len(canon_fail)}")
print("="*70)

def dump(title, rows, fields):
    print(f"\n--- {title} ({len(rows)}) ---")
    if not rows:
        print("   NONE")
        return
    for r in rows:
        print("   " + " | ".join(str(r[f]) for f in fields))

dump("NON-200 FAILURES", non200, ["status", "url"])
dump("META NOINDEX FAILURES", meta_ni, ["url"])
dump("X-ROBOTS NOINDEX FAILURES", x_ni, ["url", "xrobots"])
dump("ROBOTS.TXT BLOCKED (in sitemap)", blocked, ["blocked", "url"])
dump("CANONICAL MISSING (200 pages)", canon_fail, ["url"])
