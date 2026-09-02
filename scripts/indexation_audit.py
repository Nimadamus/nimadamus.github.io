#!/usr/bin/env python3
"""Indexation recovery audit for BetLegendPicks.com.

Scans every HTML page + all sitemaps and reports:
  - sitemap URLs with no matching file (would 404)
  - files missing from sitemaps
  - canonical problems (missing, multiple, non-self, http/non-www)
  - noindex pages present in sitemaps
  - dated/undated duplicate pairs (date_strip_rename_map.json) both self-canonical
  - duplicate <title> / meta description groups
  - thin pages (low unique text)
  - orphan pages (no inbound internal link from any HTML or data JS)
Outputs JSON report to scripts/indexation_audit_report.json and a console summary.
"""
import json, os, re, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.betlegendpicks.com"
EXCLUDE_DIRS = {".git", "node_modules", "scripts", ".github", ".vscode", "__pycache__"}

def collect_html():
    out = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if fn.endswith(".html"):
                rel = os.path.relpath(os.path.join(root, fn), REPO).replace("\\", "/")
                out.append(rel)
    return sorted(out)

def url_for(rel):
    if rel == "index.html":
        return DOMAIN + "/"
    if rel.endswith("/index.html"):
        return DOMAIN + "/" + rel[: -len("index.html")]
    return DOMAIN + "/" + rel

def rel_for(url):
    p = url.replace(DOMAIN, "").lstrip("/")
    if p == "" or p.endswith("/"):
        p += "index.html"
    return p

CANON_RE = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]*>', re.I)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
DESC_RE2 = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', re.I)
ROBOTS_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']*)["\']', re.I)
ROBOTS_RE2 = re.compile(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']robots["\']', re.I)
TAG_RE = re.compile(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|<[^>]+>", re.S)
LINK_RE = re.compile(r'(?:href|HREF)=["\']([^"\'#?]+\.html)["\']')

def main():
    files = collect_html()
    fileset = set(files)

    # --- sitemap URLs ---
    sm_urls = {}
    for sm in ["sitemap-main.xml", "sitemap-previews.xml", "sitemap-featured-games.xml",
               "sitemap-posts.xml", "sitemap-records.xml"]:
        path = os.path.join(REPO, sm)
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8", errors="ignore").read()
        for loc in re.findall(r"<loc>([^<]+)</loc>", txt):
            sm_urls.setdefault(loc.strip(), sm)

    sm_missing_file = sorted(u for u in sm_urls if rel_for(u) not in fileset)
    in_sitemap_rel = {rel_for(u) for u in sm_urls}
    not_in_sitemap = sorted(f for f in files if f not in in_sitemap_rel)

    # --- per-page scan ---
    pages = {}
    titles = defaultdict(list)
    descs = defaultdict(list)
    inbound = defaultdict(set)
    for rel in files:
        try:
            txt = open(os.path.join(REPO, rel), encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        canon_tags = CANON_RE.findall(txt)
        canons = []
        for t in canon_tags:
            m = HREF_RE.search(t)
            if m:
                canons.append(m.group(1))
        title = (TITLE_RE.search(txt) or [None, ""])[1] if TITLE_RE.search(txt) else ""
        title = re.sub(r"\s+", " ", title).strip()
        dm = DESC_RE.search(txt) or DESC_RE2.search(txt)
        desc = dm.group(1).strip() if dm else ""
        rm = ROBOTS_RE.search(txt) or ROBOTS_RE2.search(txt)
        robots = rm.group(1).lower() if rm else ""
        text = TAG_RE.sub(" ", txt)
        words = len(re.findall(r"[A-Za-z]{2,}", text))
        pages[rel] = {
            "canonicals": canons, "title": title, "desc": desc,
            "robots": robots, "words": words,
        }
        if title:
            titles[title].append(rel)
        if desc:
            descs[desc].append(rel)
        # outbound internal links
        base_dir = os.path.dirname(rel)
        for href in LINK_RE.findall(txt):
            if href.startswith("http"):
                if not href.startswith(DOMAIN):
                    continue
                target = rel_for(href)
            else:
                target = os.path.normpath(os.path.join(base_dir, href)).replace("\\", "/")
                target = target.lstrip("./")
            if target in fileset and target != rel:
                inbound[target].add(rel)

    # data JS files that drive homepage/calendar links
    js_link_sources = []
    for root, dirs, fs in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in fs:
            if fn.endswith((".js", ".json")) and ("data" in fn or "calendar" in fn or "manifest" in fn or "picks" in fn):
                js_link_sources.append(os.path.join(root, fn))
    js_refs = set()
    for p in js_link_sources:
        try:
            txt = open(p, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for h in re.findall(r'["\']([A-Za-z0-9\-_/\.]+\.html)["\']', txt):
            t = h.lstrip("/").lstrip("./")
            if t in fileset:
                js_refs.add(t)

    # --- categorize problems ---
    report = {}
    report["sitemap_total_urls"] = len(sm_urls)
    report["total_html_files"] = len(files)
    report["sitemap_urls_no_file"] = sm_missing_file
    report["files_not_in_sitemap"] = not_in_sitemap

    bad_canon = {"missing": [], "multiple": [], "non_self": [], "scheme_host": []}
    noindex_in_sitemap = []
    noindex_pages = []
    for rel, info in pages.items():
        self_url = url_for(rel)
        cs = info["canonicals"]
        if "noindex" in info["robots"]:
            noindex_pages.append(rel)
            if rel in in_sitemap_rel:
                noindex_in_sitemap.append(rel)
            continue
        if not cs:
            bad_canon["missing"].append(rel)
        else:
            uniq = sorted(set(cs))
            if len(uniq) > 1:
                bad_canon["multiple"].append((rel, uniq))
            c = uniq[0]
            if c.rstrip("/") != self_url.rstrip("/"):
                if c.replace("http://", "https://").replace("://betlegendpicks", "://www.betlegendpicks").rstrip("/") == self_url.rstrip("/"):
                    bad_canon["scheme_host"].append((rel, c))
                else:
                    bad_canon["non_self"].append((rel, c))
    report["canonical_missing"] = sorted(bad_canon["missing"])
    report["canonical_multiple"] = bad_canon["multiple"]
    report["canonical_non_self"] = bad_canon["non_self"]
    report["canonical_scheme_host"] = bad_canon["scheme_host"]
    report["noindex_pages"] = sorted(noindex_pages)
    report["noindex_in_sitemap"] = sorted(noindex_in_sitemap)

    # dated/undated duplicate pairs
    dup_pairs = []
    map_path = os.path.join(REPO, "scripts", "date_strip_rename_map.json")
    if os.path.exists(map_path):
        m = json.load(open(map_path))
        for old, new in m.items():
            if old in fileset and new in fileset:
                oc = pages.get(old, {}).get("canonicals", [])
                dup_pairs.append({
                    "dated": old, "undated": new,
                    "dated_self_canonical": bool(oc) and url_for(old).rstrip("/") in [c.rstrip("/") for c in oc],
                    "dated_in_sitemap": old in in_sitemap_rel,
                    "undated_in_sitemap": new in in_sitemap_rel,
                })
    report["dated_undated_dup_pairs"] = dup_pairs
    report["dup_pairs_both_self_canonical"] = sum(1 for d in dup_pairs if d["dated_self_canonical"])
    report["dup_pairs_dated_in_sitemap"] = sum(1 for d in dup_pairs if d["dated_in_sitemap"])

    report["duplicate_titles"] = {t: v for t, v in titles.items() if len(v) > 1}
    report["duplicate_descriptions"] = {d: v for d, v in descs.items() if len(v) > 1}

    thin = sorted([(rel, i["words"]) for rel, i in pages.items() if i["words"] < 250 and "noindex" not in i["robots"]], key=lambda x: x[1])
    report["thin_pages_under_250_words"] = thin

    orphans = sorted(
        rel for rel in files
        if rel not in inbound and rel not in js_refs
        and rel != "index.html" and "noindex" not in pages.get(rel, {}).get("robots", "")
    )
    report["orphan_pages"] = orphans
    report["orphan_pages_in_sitemap"] = sorted(set(orphans) & in_sitemap_rel)

    out = os.path.join(REPO, "scripts", "indexation_audit_report.json")
    json.dump(report, open(out, "w", encoding="utf-8"), indent=1, default=list)

    print(f"HTML files: {len(files)} | sitemap URLs: {len(sm_urls)}")
    print(f"Sitemap URLs with NO file (404 in sitemap): {len(sm_missing_file)}")
    print(f"Files not in any sitemap: {len(not_in_sitemap)}")
    print(f"Canonical missing: {len(bad_canon['missing'])} | multiple: {len(bad_canon['multiple'])} | non-self: {len(bad_canon['non_self'])} | scheme/host: {len(bad_canon['scheme_host'])}")
    print(f"Noindex pages: {len(noindex_pages)} (in sitemap: {len(noindex_in_sitemap)})")
    print(f"Dated/undated dup pairs: {len(dup_pairs)} | dated self-canonical: {report['dup_pairs_both_self_canonical']} | dated in sitemap: {report['dup_pairs_dated_in_sitemap']}")
    print(f"Duplicate title groups: {len(report['duplicate_titles'])} | duplicate desc groups: {len(report['duplicate_descriptions'])}")
    print(f"Thin pages (<250 words): {len(thin)}")
    print(f"Orphan pages: {len(orphans)} (of which in sitemap: {len(report['orphan_pages_in_sitemap'])})")
    print(f"Report: {out}")

if __name__ == "__main__":
    main()
