"""Deployment gate: fail if records.html / upcomingpicks.html contain unbaked
placeholder shells instead of real baked data (SEO_AUDIT_REPORT_2026-07-30.md,
finding A). Runs in the Content Validation & Deployment Gate workflow so a
regression back to empty client-side-only shells blocks the deploy rather than
publishing pages Google sees as empty.

Exit 0 = baked content present and sane. Exit 1 = placeholders/failure text.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NO_PICKS_MSG = "No upcoming picks at this time. Check back soon!"


def fail(msgs):
    print("SEO BAKE VALIDATION FAILED:")
    for m in msgs:
        print(f"  - {m}")
    print("Run: python scripts/bake_seo_static_data.py")
    return 1


def main():
    errors = []

    rec = (ROOT / "records.html").read_text(encoding="utf-8", errors="ignore")
    if "<!-- seo-bake:" not in rec:
        errors.append("records.html: no seo-bake marker (never baked)")
    m = re.search(r'id="total-record">([^<]*)<', rec)
    total = m.group(1).strip() if m else ""
    if not re.match(r"^\d+-\d+(-\d+)?$", total):
        errors.append(f"records.html: total-record is placeholder/invalid: '{total}'")
    for tid in ("sport-breakdown", "bet-type-breakdown", "monthly-breakdown"):
        tb = re.search(rf'<tbody id="{tid}">(.*?)</tbody>', rec, re.S)
        if not tb or "<tr" not in tb.group(1):
            errors.append(f"records.html: tbody #{tid} has no baked rows")

    up = (ROOT / "upcomingpicks.html").read_text(encoding="utf-8", errors="ignore")
    if "<!-- seo-bake:" not in up:
        errors.append("upcomingpicks.html: no seo-bake marker (never baked)")
    tb = re.search(r'<tbody id="picks-table-body">(.*?)</tbody>', up, re.S)
    body = tb.group(1) if tb else ""
    if "Loading Picks" in body or "Could not load" in body:
        errors.append("upcomingpicks.html: placeholder/failure text in picks table")
    elif "<tr" not in body and NO_PICKS_MSG not in body:
        errors.append("upcomingpicks.html: picks table has neither rows nor no-picks message")

    if errors:
        return fail(errors)
    print(f"SEO bake validation OK (records total {total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
