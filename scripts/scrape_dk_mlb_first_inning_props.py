from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
PLAYWRIGHT_CHROMIUM = Path.home() / "AppData" / "Local" / "ms-playwright" / "chromium-1097" / "chrome-win" / "chrome.exe"
FIRST_INNING_URL = "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=quick-hits&subcategory=1st-inning-runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape DraftKings MLB first-inning run markets.")
    parser.add_argument("--date", default=str(date.today()), help="Reference date in YYYY-MM-DD.")
    parser.add_argument("--output-dir", default=str(Path.home() / "Desktop"))
    return parser.parse_args()


def parse_reference_date(text: str, page_date: date) -> date:
    lower = text.lower()
    if lower.startswith("today"):
        return page_date
    if lower.startswith("tomorrow"):
        return page_date + timedelta(days=1)
    return page_date


def normalize_market_rows(raw_rows: list[dict[str, Any]], page_date: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for game in raw_rows:
        away = game.get("away")
        home = game.get("home")
        game_time_label = game.get("gameTime") or ""
        market_label = game.get("marketLabel") or ""
        if not away or not home or "runs - 1st inning" not in market_label.lower():
            continue
        game_date = parse_reference_date(game_time_label, page_date).isoformat()
        for button in game.get("buttons", []):
            side = button.get("side")
            line = button.get("line")
            odds = button.get("odds")
            if side not in {"Over", "Under"} or line is None or odds is None:
                continue
            line_value = float(line)
            american = int(str(odds).replace("−", "-"))
            normalized_market = "first_inning_total_runs"
            normalized_side = side
            if line_value == 0.5:
                normalized_market = "yrfi" if side == "Over" else "nrfi"
                normalized_side = "YRFI" if side == "Over" else "NRFI"
            rows.append(
                {
                    "date": game_date,
                    "game": f"{away} @ {home}",
                    "bookmaker": "DraftKings",
                    "bookmaker_key": "draftkings_scrape",
                    "market": normalized_market,
                    "side": normalized_side,
                    "line": line_value,
                    "odds_american": american,
                    "market_type": "first_inning_runs",
                    "last_update": datetime.now().isoformat(),
                    "source": "draftkings_playwright_scrape",
                }
            )
    deduped: dict[tuple[str, str, str, float], dict[str, Any]] = {}
    for row in rows:
        key = (row["game"], row["market"], row["side"], float(row["line"]))
        deduped[key] = row
    return list(deduped.values())


def scrape_first_inning(page, page_date: date) -> list[dict[str, Any]]:
    page.goto(FIRST_INNING_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(8000)
    last_height = 0
    stable = 0
    for _ in range(12):
        page.mouse.wheel(0, 3000)
        page.wait_for_timeout(1200)
        height = page.evaluate("() => document.body.scrollHeight")
        if height == last_height:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last_height = height
    raw_rows = page.evaluate(
        """() => {
            const normalizeOdds = (value) => (value || '').replace(/−/g, '-').trim();
            return Array.from(document.querySelectorAll('[data-testid="non-collapsible-wrapper"]')).map(wrapper => {
                const text = (wrapper.innerText || '').split('\\n').map(x => x.trim()).filter(Boolean);
                const away = text[0] || null;
                const home = text[2] || null;
                const gameTime = text[3] || null;
                const marketLabel = text[4] || null;
                const buttons = Array.from(wrapper.querySelectorAll('button')).map(btn => ({
                    side: btn.querySelector('[data-testid="button-title-market-board"]')?.innerText?.trim() || null,
                    line: btn.querySelector('[data-testid="button-points-market-board"]')?.innerText?.trim() || null,
                    odds: normalizeOdds(btn.querySelector('[data-testid="button-odds-market-board"]')?.innerText || null),
                }));
                return { away, home, gameTime, marketLabel, buttons };
            });
        }"""
    )
    return normalize_market_rows(raw_rows, page_date)


def main() -> int:
    args = parse_args()
    requested_date = date.fromisoformat(args.date)
    page_date = date.today()
    out_dir = Path(args.output_dir) / "MLB_Props" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "dk_first_inning_normalized.json"
    status_path = out_dir / "dk_first_inning_status.json"

    if not PLAYWRIGHT_CHROMIUM.exists():
        raise SystemExit(f"Missing Playwright Chromium at {PLAYWRIGHT_CHROMIUM}")

    rows: list[dict[str, Any]] = []
    status: dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "reference_date": args.date,
        "url": FIRST_INNING_URL,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(PLAYWRIGHT_CHROMIUM), headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 2400})
        try:
            rows = scrape_first_inning(page, page_date)
            status["fetch_succeeded"] = True
        except PlaywrightTimeoutError as exc:
            status["fetch_succeeded"] = False
            status["error"] = str(exc)
        finally:
            browser.close()

    rows = [row for row in rows if row["date"] == requested_date.isoformat()]
    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    status["page_date"] = page_date.isoformat()
    status["row_count"] = len(rows)
    status["yrfi_rows"] = sum(1 for row in rows if row["market"] == "yrfi")
    status["nrfi_rows"] = sum(1 for row in rows if row["market"] == "nrfi")
    status["alt_total_rows"] = sum(1 for row in rows if row["market"] == "first_inning_total_runs")
    status["output_file"] = str(json_path)
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print(f"Saved {json_path}")
    print(f"Saved {status_path}")
    print(f"Rows: {len(rows)}")
    print(f"YRFI rows: {status['yrfi_rows']}")
    print(f"NRFI rows: {status['nrfi_rows']}")
    print(f"Alt total rows: {status['alt_total_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
