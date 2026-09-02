#!/usr/bin/env python3
"""Compare live sitemap URLs against a Google Search Console Pages export.

This script does not infer indexing. A URL is only marked "Indexed" when the
provided Search Console export explicitly says it is indexed.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


REPO = Path(__file__).resolve().parents[1]
BASE_URL = "https://www.betlegendpicks.com"
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

GROUPS = [
    "Indexed",
    "Crawled currently not indexed",
    "Discovered currently not indexed",
    "Duplicate without user selected canonical",
    "Alternate page with proper canonical",
    "Not found 404",
    "Page with redirect",
    "Blocked by robots.txt",
    "Excluded by noindex",
    "Soft 404",
    "Server error",
    "Duplicate, Google chose different canonical than user",
    "Unknown from available GSC data",
]

DAILY_PRIORITY_PATTERNS = (
    "featured-game-of-the-day.html",
    "featured-game-calendar.html",
    "pistons-vs-cavaliers-eastern-semis-game-3-analysis-stats-preview-may-9-2026.html",
    "sale-fried-friday-fifteen-game-slate-mlb-may-8-2026.html",
    "knicks-76ers-spurs-wolves-game-3-east-west-semis-nba-may-8-2026.html",
    "sabres-canadiens-knights-ducks-second-round-game-fest-nhl-may-8-2026.html",
    "mlb-previews.html",
    "nba-previews.html",
    "nhl-previews.html",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gsc-csv", required=True, type=Path)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--out-dir", default=REPO / "reports", type=Path)
    return parser.parse_args()


def fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "BetLegend indexing audit"})
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read()


def normalize_url(url: str, base_url: str = BASE_URL) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    parsed = urllib.parse.urlsplit(url)
    scheme = "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if netloc == "betlegendpicks.com":
        netloc = "www.betlegendpicks.com"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urllib.parse.urlunsplit((scheme, netloc, path, "", ""))


def text_or_empty(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def parse_live_sitemaps(base_url: str) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
    status, headers, body = fetch(sitemap_url)
    if status != 200:
        raise RuntimeError(f"{sitemap_url} returned HTTP {status}")
    root = ET.fromstring(body)
    if root.tag.endswith("sitemapindex"):
        child_urls = [text_or_empty(node.find("sm:loc", NS)) for node in root.findall("sm:sitemap", NS)]
    else:
        child_urls = [sitemap_url]

    child_reports: list[dict[str, object]] = []
    url_rows: list[dict[str, str]] = []
    for child_url in child_urls:
        child_status, child_headers, child_body = fetch(child_url)
        report: dict[str, object] = {
            "sitemap_url": child_url,
            "http_status": child_status,
            "content_type": child_headers.get("content-type", ""),
            "valid_xml": False,
            "url_count": 0,
        }
        if child_status == 200:
            child_root = ET.fromstring(child_body)
            report["valid_xml"] = True
            for node in child_root.findall("sm:url", NS):
                loc = text_or_empty(node.find("sm:loc", NS))
                lastmod = text_or_empty(node.find("sm:lastmod", NS))
                if loc:
                    url_rows.append({"url": normalize_url(loc, base_url), "sitemap": child_url, "lastmod": lastmod})
            report["url_count"] = sum(1 for row in url_rows if row["sitemap"] == child_url)
        child_reports.append(report)
    return url_rows, child_reports


def normalize_issue(issue: str, status: str = "", noindex: str = "", robots_allowed: str = "") -> str:
    raw = (issue or "").strip().lower()
    status_raw = (status or "").strip()
    noindex_raw = (noindex or "").strip().lower()
    robots_raw = (robots_allowed or "").strip().lower()
    if raw in {"indexed", "submitted and indexed", "indexed, not submitted in sitemap"}:
        return "Indexed"
    if "crawled" in raw and "not indexed" in raw:
        return "Crawled currently not indexed"
    if "discovered" in raw and "not indexed" in raw:
        return "Discovered currently not indexed"
    if "duplicate without user" in raw:
        return "Duplicate without user selected canonical"
    if "alternate page with proper canonical" in raw:
        return "Alternate page with proper canonical"
    if "duplicate" in raw and "google chose different canonical" in raw:
        return "Duplicate, Google chose different canonical than user"
    if "not found" in raw or status_raw == "404":
        return "Not found 404"
    if "redirect" in raw or status_raw.startswith("3"):
        return "Page with redirect"
    if "blocked by robots" in raw or robots_raw == "false":
        return "Blocked by robots.txt"
    if "noindex" in raw or noindex_raw == "true":
        return "Excluded by noindex"
    if "soft 404" in raw:
        return "Soft 404"
    if "server error" in raw or status_raw.startswith("5"):
        return "Server error"
    return issue.strip() or "Unknown from available GSC data"


def load_gsc_rows(path: Path, base_url: str) -> dict[str, list[dict[str, str]]]:
    rows_by_url: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            url = normalize_url(row.get("url", ""), base_url)
            if not url:
                continue
            row["gsc_group"] = normalize_issue(
                row.get("issue", ""),
                status=row.get("status", ""),
                noindex=row.get("noindex", ""),
                robots_allowed=row.get("robots_allowed", ""),
            )
            rows_by_url[url].append(row)
    return rows_by_url


def choose_gsc_row(rows: list[dict[str, str]]) -> dict[str, str]:
    if len(rows) == 1:
        return rows[0]
    priority = {name: idx for idx, name in enumerate(GROUPS)}
    return sorted(rows, key=lambda row: priority.get(row.get("gsc_group", ""), 99))[0]


def recommendation(group: str, row: dict[str, str], in_sitemap: bool) -> tuple[str, str]:
    if group == "Indexed":
        return "No action from this audit.", "No"
    if group == "Crawled currently not indexed":
        return "Improve internal links/content quality, then inspect after recrawl.", "Only for high-priority daily URLs"
    if group == "Discovered currently not indexed":
        return "Confirm internal links and sitemap lastmod, then request indexing for priority URLs.", "Yes for important daily URLs"
    if group == "Duplicate without user selected canonical":
        return "Review canonical signals and internal links; do not change canonical without approval.", "After canonical review"
    if group == "Duplicate, Google chose different canonical than user":
        return "Inspect selected canonical in GSC and compare with intended canonical before changing anything.", "No until canonical decision"
    if group == "Alternate page with proper canonical":
        return "Usually expected if intentionally canonicalized; verify it is not a valid standalone page.", "No"
    if group == "Not found 404":
        return "If valid, restore/link the page; if obsolete, leave out of sitemap and fix stale internal links.", "After HTTP 200 restoration"
    if group == "Page with redirect":
        return "Verify redirects are intentional and remove redirected URLs from sitemap if they are not canonical pages.", "No"
    if group == "Blocked by robots.txt":
        return "Remove robots block only if this URL should be public/indexable.", "After robots fix"
    if group == "Excluded by noindex":
        return "Remove noindex only if this URL should be public/indexable.", "After noindex fix"
    if group == "Soft 404":
        return "Strengthen page content or remove from sitemap if it is not a valid public page.", "After content/status fix"
    if group == "Server error":
        return "Fix server error first, then revalidate in GSC.", "After HTTP 200 restoration"
    if not in_sitemap:
        return "GSC issue URL is not in the live sitemap; verify whether it is intentionally excluded.", "No"
    return "Not present in available GSC issue export; use a full GSC indexed/not-indexed export or URL Inspection for exact status.", "Only for priority URLs"


def audit(args: argparse.Namespace) -> dict[str, object]:
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    sitemap_rows, child_reports = parse_live_sitemaps(args.base_url)
    gsc_by_url = load_gsc_rows(args.gsc_csv, args.base_url)

    sitemap_by_url: dict[str, dict[str, str]] = {}
    for row in sitemap_rows:
        sitemap_by_url.setdefault(row["url"], row)

    all_urls = sorted(set(sitemap_by_url) | set(gsc_by_url))
    rows: list[dict[str, str]] = []
    for url in all_urls:
        in_sitemap = url in sitemap_by_url
        gsc_rows = gsc_by_url.get(url, [])
        gsc_row = choose_gsc_row(gsc_rows) if gsc_rows else {}
        group = gsc_row.get("gsc_group", "Unknown from available GSC data" if in_sitemap else "Not in sitemap")
        fix, request_indexing = recommendation(group, gsc_row, in_sitemap)
        rows.append(
            {
                "url": url,
                "group": group,
                "gsc_issue": gsc_row.get("issue", ""),
                "last_crawled": gsc_row.get("last_crawled", ""),
                "http_status_from_gsc_export": gsc_row.get("status", ""),
                "in_live_sitemap": str(in_sitemap),
                "sitemap_source": sitemap_by_url.get(url, {}).get("sitemap", ""),
                "sitemap_lastmod": sitemap_by_url.get(url, {}).get("lastmod", ""),
                "robots_allowed_from_gsc_export": gsc_row.get("robots_allowed", ""),
                "noindex_from_gsc_export": gsc_row.get("noindex", ""),
                "canonical_from_gsc_export": gsc_row.get("canonical", ""),
                "self_canonical_from_gsc_export": gsc_row.get("self_canonical", ""),
                "internal_link_sources_from_gsc_export": gsc_row.get("internal_link_sources", ""),
                "title_from_gsc_export": gsc_row.get("title", ""),
                "recommended_fix": fix,
                "request_indexing_manually": request_indexing,
            }
        )

    group_counts = Counter(row["group"] for row in rows)
    sitemap_counts = Counter(row["sitemap_source"] for row in rows if row["in_live_sitemap"] == "True")
    priority_rows = [
        row for row in rows if any(pattern in row["url"] for pattern in DAILY_PRIORITY_PATTERNS)
    ]
    priority_not_indexed = [
        row
        for row in priority_rows
        if row["group"] != "Indexed"
    ]
    valid_but_excluded_groups = {
        "Crawled currently not indexed",
        "Discovered currently not indexed",
        "Duplicate without user selected canonical",
        "Duplicate, Google chose different canonical than user",
        "Alternate page with proper canonical",
        "Excluded by noindex",
        "Blocked by robots.txt",
        "Soft 404",
    }
    error_groups = {"Not found 404", "Server error"}

    return {
        "timestamp_utc": timestamp,
        "base_url": args.base_url,
        "gsc_export_file": str(args.gsc_csv.resolve()),
        "gsc_export_last_modified": dt.datetime.fromtimestamp(args.gsc_csv.stat().st_mtime, dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "sitemap_index": args.base_url.rstrip("/") + "/sitemap.xml",
        "child_sitemaps": child_reports,
        "summary": {
            "total_live_sitemap_urls": len(sitemap_by_url),
            "total_gsc_export_issue_urls": len(gsc_by_url),
            "total_urls_compared": len(rows),
            "total_indexed_confirmed_by_gsc_export": group_counts.get("Indexed", 0),
            "total_not_indexed_or_excluded_in_gsc_export": sum(
                count for group, count in group_counts.items() if group not in {"Indexed", "Unknown from available GSC data"}
            ),
            "total_valid_but_excluded_in_gsc_export": sum(group_counts.get(group, 0) for group in valid_but_excluded_groups),
            "total_error_urls_in_gsc_export": sum(group_counts.get(group, 0) for group in error_groups),
            "total_unknown_from_available_gsc_data": group_counts.get("Unknown from available GSC data", 0),
        },
        "group_counts": dict(group_counts),
        "sitemap_counts": dict(sitemap_counts),
        "priority_not_indexed_or_unknown": priority_not_indexed,
        "rows": rows,
    }


def write_outputs(result: dict[str, object], out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    csv_path = out_dir / f"gsc-indexing-audit-{stamp}.csv"
    json_path = out_dir / f"gsc-indexing-audit-{stamp}.json"
    md_path = out_dir / f"gsc-indexing-audit-{stamp}.md"

    rows = result["rows"]  # type: ignore[index]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["url"])
        writer.writeheader()
        writer.writerows(rows)  # type: ignore[arg-type]
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    summary = result["summary"]  # type: ignore[index]
    group_counts = result["group_counts"]  # type: ignore[index]
    child_sitemaps = result["child_sitemaps"]  # type: ignore[index]
    priority_rows = result["priority_not_indexed_or_unknown"]  # type: ignore[index]

    lines = [
        "# BetLegendPicks GSC Indexing Audit",
        "",
        f"Generated: {result['timestamp_utc']}",
        f"GSC export: `{result['gsc_export_file']}`",
        f"GSC export modified: {result['gsc_export_last_modified']}",
        f"Live sitemap index checked: {result['sitemap_index']}",
        "",
        "Important limitation: this audit only marks a URL as indexed when the supplied Search Console export explicitly contains an indexed status. Sitemap URLs missing from the export are not claimed as indexed.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():  # type: ignore[union-attr]
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Child Sitemaps", ""])
    for child in child_sitemaps:  # type: ignore[union-attr]
        lines.append(
            f"- {child['sitemap_url']}: HTTP {child['http_status']}, valid_xml={child['valid_xml']}, urls={child['url_count']}"
        )
    lines.extend(["", "## Groups", ""])
    for group in GROUPS:
        lines.append(f"- {group}: {group_counts.get(group, 0)}")  # type: ignore[union-attr]
    other_groups = sorted(set(group_counts) - set(GROUPS))  # type: ignore[arg-type]
    for group in other_groups:
        lines.append(f"- {group}: {group_counts[group]}")  # type: ignore[index]
    lines.extend(["", "## Priority URLs Needing Manual URL Inspection", ""])
    if not priority_rows:
        lines.append("- None from the checked priority URL set.")
    else:
        for row in priority_rows:  # type: ignore[union-attr]
            lines.append(
                f"- {row['url']} | {row['group']} | fix: {row['recommended_fix']} | request indexing: {row['request_indexing_manually']}"
            )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Do not remove, noindex, canonicalize, or redirect any page from this report without separate approval.",
            "- Rows grouped as unknown require a full Search Console Pages export or URL Inspection API/browser check to determine exact indexed status.",
            "- The CSV contains every live sitemap URL plus every URL present in the supplied GSC issue export.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "md": md_path}


def main() -> int:
    args = parse_args()
    try:
        result = audit(args)
        paths = write_outputs(result, args.out_dir)
    except Exception as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    print(json.dumps({name: str(path) for name, path in paths.items()}, indent=2))
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
