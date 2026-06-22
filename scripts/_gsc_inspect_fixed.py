#!/usr/bin/env python3
"""Query the GSC URL Inspection API for every previously-noindexed URL and
report Google's CURRENT recorded verdict (coverageState / indexingState /
robotsTxtState). Also resubmit the sitemap."""
import sys, time
from collections import Counter
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CRED = r"C:\Users\Nima\google_credentials.json"
SITE = "https://www.betlegendpicks.com/"
SITEMAP = "https://www.betlegendpicks.com/sitemap.xml"

creds = service_account.Credentials.from_service_account_file(
    CRED, scopes=["https://www.googleapis.com/auth/webmasters"])
svc = build("searchconsole", "v1", credentials=creds, cache_discovery=False)

files = [l.strip() for l in open(sys.argv[1]) if l.strip()]
urls = [SITE + f for f in files]

def inspect(url):
    for attempt in range(4):
        try:
            r = svc.urlInspection().index().inspect(
                body={"inspectionUrl": url, "siteUrl": SITE}).execute()
            idx = r.get("inspectionResult", {}).get("indexStatusResult", {})
            return {
                "url": url,
                "verdict": idx.get("verdict", "?"),
                "coverage": idx.get("coverageState", "?"),
                "indexing": idx.get("indexingState", "?"),
                "robots": idx.get("robotsTxtState", "?"),
                "lastCrawl": idx.get("lastCrawlTime", "never"),
            }
        except HttpError as e:
            if e.resp.status in (429, 500, 503):
                time.sleep(2 * (attempt + 1)); continue
            return {"url": url, "verdict": "API_ERROR", "coverage": str(e.resp.status),
                    "indexing": "", "robots": "", "lastCrawl": ""}
        except Exception as e:
            return {"url": url, "verdict": "ERROR", "coverage": str(e)[:60],
                    "indexing": "", "robots": "", "lastCrawl": ""}
    return {"url": url, "verdict": "RETRY_FAIL", "coverage": "", "indexing": "", "robots": "", "lastCrawl": ""}

print(f"Inspecting {len(urls)} previously-noindexed URLs via GSC URL Inspection API...\n")
rows = []
cov_counter = Counter()
robots_counter = Counter()
still_noindex = []
for i, u in enumerate(urls, 1):
    row = inspect(u)
    rows.append(row)
    cov_counter[row["coverage"]] += 1
    robots_counter[row["robots"]] += 1
    if "noindex" in row["coverage"].lower() or row["indexing"] == "BLOCKED_BY_META_TAG":
        still_noindex.append(row)
    print(f"[{i:>3}/{len(urls)}] {row['coverage']:<45} idx={row['indexing']:<22} robots={row['robots']:<10} {u}")

print("\n" + "=" * 70)
print("GSC URL INSPECTION SUMMARY (Google's current recorded state)")
print("=" * 70)
print("coverageState breakdown:")
for k, v in cov_counter.most_common():
    print(f"  {v:>4}  {k}")
print("\nrobotsTxtState breakdown:")
for k, v in robots_counter.most_common():
    print(f"  {v:>4}  {k}")
print(f"\nURLs Google STILL records as noindex-excluded: {len(still_noindex)}")
for r in still_noindex:
    print("  ", r["coverage"], "|", r["indexing"], "|", r["url"], "| lastCrawl:", r["lastCrawl"])

# Resubmit sitemap
try:
    svc.sitemaps().submit(siteUrl=SITE, feedpath=SITEMAP).execute()
    print(f"\n[OK] Sitemap resubmitted: {SITEMAP}")
except Exception as e:
    print(f"\n[sitemap submit error] {e}")
