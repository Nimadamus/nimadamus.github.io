"""Audit every BetLegend preview/review-family page against PREVIEW_PAGE_STANDARD.md.

Read-only. Classifies pages, flags drift/data/image issues, writes a JSON work
queue to reports/preview_page_audit.json and prints a summary.
"""
import json
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPORT_TOKENS = [
    ("-mlb-pick.html", "mlb", "pick"),
    ("-pick.html", None, "pick"),
    ("-analysis-stats-preview.html", None, "featured"),
    ("-prediction-picks.html", None, "prediction-picks"),
    ("-mlb.html", "mlb", "board"),
    ("-nhl.html", "nhl", "board"),
    ("-nba.html", "nba", "board"),
    ("-nfl.html", "nfl", "board"),
    ("-ncaaf.html", "ncaaf", "board"),
    ("-soccer.html", "soccer", "board"),
    ("-college-basketball.html", "ncaab", "board"),
]

SPORT_GUESS = re.compile(r"\b(mlb|nhl|nba|nfl|ncaaf|ncaab|soccer|college-basketball|world-cup)\b")

GENERIC_H1 = re.compile(r"<h1[^>]*>\s*(Featured Game of the Day|Expert Analysis[^<]*)\s*</h1>", re.I)
INLINE_H2 = re.compile(r"<h2 style=")
EMOJI = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
REDIRECT_STUB = re.compile(r'http-equiv=["\']refresh', re.I)


def classify(fname):
    for suffix, sport, family in SPORT_TOKENS:
        if fname.endswith(suffix):
            if sport is None:
                m = SPORT_GUESS.search(fname)
                sport = m.group(1) if m else "unknown"
                if sport == "college-basketball":
                    sport = "ncaab"
                if sport == "world-cup":
                    sport = "soccer"
            return sport, family
    return None, None


def audit_file(path, fname):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            html = f.read()
    except OSError as e:
        return {"file": fname, "error": str(e)}
    if REDIRECT_STUB.search(html[:2000]):
        return None  # redirect stub, not a content page
    sport, family = classify(fname)
    og = re.search(r'property="og:image"\s+content="([^"]+)"|content="([^"]+)"\s+property="og:image"', html)
    og_image = (og.group(1) or og.group(2)) if og else ""
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    h1_text = re.sub(r"<[^>]+>", "", h1.group(1)).strip()[:100] if h1 else ""
    body = html[html.find("<body"):] if "<body" in html else html
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", body, flags=re.S)
    words = len(text.split())
    schema_types = sorted(set(re.findall(r'"@type"\s*:\s*"(NewsArticle|FAQPage|BreadcrumbList|SportsEvent)"', html)))
    issues = []
    if not og_image or og_image.endswith("newlogo.png"):
        issues.append("og_image_logo_or_missing")
    elif any(h in og_image for h in ("heavy.com", "wp-content")):
        issues.append("og_image_hotlink_risky")
    if GENERIC_H1.search(html):
        issues.append("generic_h1")
    n_inline_h2 = len(INLINE_H2.findall(html))
    if n_inline_h2 >= 3:
        issues.append("drifted_inline_h2")
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.S)
    if any(EMOJI.search(h) for h in h2s):
        issues.append("emoji_headers")
    if 'class="toc-box"' not in html and family in ("featured", "board"):
        n_arts = len(re.findall(r'<article class="game-preview', html))
        n_secs = html.count('class="section-header"') + html.count("section-header ")
        if family == "board" and n_arts >= 2:
            issues.append("no_toc")
        elif family == "featured" and n_secs >= 3:
            issues.append("no_toc")
        elif family == "featured" or (family == "board" and n_arts == 0):
            issues.append("needs_manual_structure")
    if family == "featured" and not re.search(r'share-buttons|Share on X|intent/tweet', html):
        issues.append("no_share_buttons")
    if family == "featured" and "FAQPage" not in schema_types:
        issues.append("no_faqpage_schema")
    if family == "featured" and "SportsEvent" not in schema_types:
        issues.append("no_sportsevent_schema")
    if family == "featured" and "BreadcrumbList" not in schema_types:
        issues.append("no_breadcrumb_schema")
    # empty data boxes: a value element containing only --, TBD, N/A
    empties = re.findall(r">\s*(--|TBD|TBA|N/A)\s*<", html)
    if empties:
        issues.append("empty_data_boxes:%d" % len(empties))
    if re.search(r"coming soon|analysis pending|check back", html, re.I):
        issues.append("placeholder_text")
    if family == "featured" and words < 900:
        issues.append("thin_content:%dw" % words)
    fpd = re.search(r"FORCED_PAGE_DATE\s*=\s*'(\d{4}-\d{2}-\d{2})'", html)
    return {
        "file": fname,
        "sport": sport,
        "family": family,
        "og_image": og_image[:120],
        "h1": h1_text,
        "words": words,
        "schema": schema_types,
        "forced_date": fpd.group(1) if fpd else None,
        "issues": issues,
    }


def main():
    results = []
    for fname in sorted(os.listdir(ROOT)):
        if not fname.endswith(".html"):
            continue
        sport, family = classify(fname)
        if family is None:
            continue
        r = audit_file(os.path.join(ROOT, fname), fname)
        if r:
            results.append(r)
    out = os.path.join(ROOT, "reports", "preview_page_audit.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    fam = Counter(r["family"] for r in results)
    print("pages audited:", len(results), dict(fam))
    issue_counts = Counter(i.split(":")[0] for r in results for i in r.get("issues", []))
    for k, v in issue_counts.most_common():
        print(f"{k}: {v}")
    clean = sum(1 for r in results if not r.get("issues"))
    print("clean pages:", clean)
    print("wrote", out)


if __name__ == "__main__":
    sys.exit(main())
