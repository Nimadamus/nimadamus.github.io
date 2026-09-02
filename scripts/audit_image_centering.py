#!/usr/bin/env python3
"""
Playwright audit of article/featured/hero image centering, desktop + mobile.

For each page it finds the primary cropped image, reads its COMPUTED object-fit /
object-position, natural vs rendered aspect, and saves a screenshot. Flags any
cover image whose object-position is the implicit 'center'/'50% 50%' (face-crop risk).

Usage:
  python scripts/audit_image_centering.py --local      # audit working-tree files (file://)
  python scripts/audit_image_centering.py --live       # audit https://www.betlegendpicks.com
"""
import sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "verification-screenshots" / "image-centering"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://www.betlegendpicks.com"

PAGES = [
    ("skenes-featured",   "dodgers-vs-pirates-skenes-analysis-stats-preview.html",            ".feature-photo"),
    ("spurs-pick-hero",   "spurs-moneyline-knicks-nba-finals-game-1-wembanyama-frost-bank-center-nba-pick.html", ".hero-image"),
    ("cubs-figure",       "cubs-team-total-under-3-5-pirates-skenes-mlb-pick.html",            "figure img"),
    ("nhl-slate-photo",   "nhl-previews.html",                                                 ".slate-photo img"),
    ("thunder-pick-hero", "thunder-moneyline-spurs-game-7-western-conference-final-nba-pick.html", ".hero-image"),
    ("homepage-card",     "homepage-preview-c-magazine.html",                                  ".pick-card-sm-img"),
    ("redsox-feature",    "red-sox-vs-yankees-rivalry-analysis-stats-preview.html",            ".feature-photo"),
]
VIEWPORTS = [("desktop", 1440, 900), ("mobile", 390, 844)]

def url_for(rel, live):
    if live:
        return f"{BASE}/{rel}"
    return (REPO / rel).resolve().as_uri()

def main():
    live = "--live" in sys.argv
    mode = "live" if live else "local"
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for vname, vw, vh in VIEWPORTS:
            ctx = b.new_context(viewport={"width": vw, "height": vh})
            pg = ctx.new_page()
            for label, rel, sel in PAGES:
                u = url_for(rel, live)
                rec = {"page": label, "viewport": vname, "selector": sel, "url": u}
                try:
                    pg.goto(u, wait_until="load", timeout=45000)
                    pg.wait_for_timeout(500)
                    el = pg.query_selector(sel)
                    if not el:
                        rec["status"] = "IMAGE_NOT_FOUND"
                    else:
                        info = el.evaluate(
                            """e=>{const c=getComputedStyle(e);const r=e.getBoundingClientRect();
                            return {fit:c.objectFit, pos:c.objectPosition,
                                    nat:(e.naturalWidth||0)+'x'+(e.naturalHeight||0),
                                    box:Math.round(r.width)+'x'+Math.round(r.height),
                                    visible:r.width>0&&r.height>0};}"""
                        )
                        rec.update(info)
                        cover = info["fit"] == "cover"
                        implicit = info["pos"].replace(" ", "") in ("50%50%", "center", "centercenter", "50%")
                        rec["status"] = "OK" if (not cover or not implicit) else "CROP_RISK_IMPLICIT_CENTER"
                        shot = OUT / f"{label}-{vname}-{mode}.png"
                        el.scroll_into_view_if_needed(timeout=5000)
                        el.screenshot(path=str(shot))
                        rec["screenshot"] = shot.name
                except Exception as e:
                    rec["status"] = f"ERROR:{type(e).__name__}:{str(e)[:80]}"
                rows.append(rec)
            ctx.close()
        b.close()

    print(f"=== IMAGE CENTERING AUDIT ({mode}) ===")
    bad = 0
    for r in rows:
        flag = "" if r.get("status") == "OK" else "  <<<"
        if r.get("status") not in ("OK",):
            bad += 1
        print(f"[{r['status']}] {r['page']:16} {r['viewport']:7} fit={r.get('fit','-'):7} "
              f"pos={r.get('pos','-'):14} nat={r.get('nat','-'):11} box={r.get('box','-'):11} "
              f"shot={r.get('screenshot','-')}{flag}")
    print(f"\nTOTAL={len(rows)}  OK={len(rows)-bad}  NON_OK={bad}")
    (OUT / f"audit-{mode}.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"json: verification-screenshots/image-centering/audit-{mode}.json")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
