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

MARKET_URLS = {
    "pitcher_strikeouts": "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=pitcher-props&subcategory=strikeouts-o-u",
    "pitcher_outs": "https://sportsbook.draftkings.com/leagues/baseball/mlb?category=pitcher-props&subcategory=outs-recorded-o-u",
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape DraftKings MLB official pitcher props.")
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


def scrape_market(page, market: str, url: str, page_date: date) -> list[dict[str, Any]]:
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
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
    scraped = page.evaluate(
        """(market) => {
            const normalizeOdds = (value) => (value || '').replace(/−/g, '-').trim();
            return Array.from(document.querySelectorAll('[data-testid="non-collapsible-wrapper"]')).map(wrapper => {
                const text = (wrapper.innerText || '').split('\\n').map(x => x.trim()).filter(Boolean);
                const away = text[0] || null;
                const home = text[2] || null;
                const gameTime = text[3] || null;
                const rows = Array.from(wrapper.querySelectorAll('[data-testid^="market-mapping-template"]')).map(row => {
                    const player = row.querySelector('[data-testid="player-page-link"] p')?.innerText?.trim() || null;
                    const buttons = Array.from(row.querySelectorAll('button')).map(btn => ({
                        side: btn.querySelector('[data-testid="button-title-market-board"]')?.innerText?.trim() || null,
                        line: btn.querySelector('[data-testid="button-points-market-board"]')?.innerText?.trim() || null,
                        odds: normalizeOdds(btn.querySelector('[data-testid="button-odds-market-board"]')?.innerText || null),
                    }));
                    return { player, buttons };
                });
                return { market, away, home, gameTime, rows };
            });
        }""",
        market,
    )

    rows: list[dict[str, Any]] = []
    for game in scraped:
        away = game.get("away")
        home = game.get("home")
        game_time_label = game.get("gameTime") or ""
        if not away or not home:
            continue
        game_date = parse_reference_date(game_time_label, page_date).isoformat()
        for player_row in game.get("rows", []):
            player = player_row.get("player")
            buttons = player_row.get("buttons") or []
            if not player or len(buttons) < 2:
                continue
            for button in buttons:
                side = button.get("side")
                line = button.get("line")
                odds = button.get("odds")
                if side not in {"O", "U"} or not line or not odds:
                    continue
                rows.append(
                    {
                        "date": game_date,
                        "game": f"{away} @ {home}",
                        "bookmaker": "DraftKings",
                        "bookmaker_key": "draftkings_scrape",
                        "market": market,
                        "side": "Over" if side == "O" else "Under",
                        "player": player,
                        "line": float(line),
                        "odds_american": int(odds),
                        "last_update": datetime.now().isoformat(),
                        "source": "draftkings_playwright_scrape",
                    }
                )
    deduped: dict[tuple[str, str, str, float, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["game"], row["market"], row["player"], float(row["line"]), row["side"])
        deduped[key] = row
    return list(deduped.values())


def main() -> int:
    args = parse_args()
    requested_date = date.fromisoformat(args.date)
    page_date = date.today()
    out_dir = Path(args.output_dir) / "MLB_Props" / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "dk_pitcher_props_normalized.json"
    status_path = out_dir / "dk_pitcher_props_status.json"

    if not PLAYWRIGHT_CHROMIUM.exists():
        raise SystemExit(f"Missing Playwright Chromium at {PLAYWRIGHT_CHROMIUM}")

    all_rows: list[dict[str, Any]] = []
    scrape_meta: dict[str, Any] = {"markets": {}, "generated_at": datetime.now().isoformat()}

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=str(PLAYWRIGHT_CHROMIUM), headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 2400})
        try:
            for market, url in MARKET_URLS.items():
                try:
                    rows = scrape_market(page, market, url, page_date)
                    all_rows.extend(rows)
                    scrape_meta["markets"][market] = {"rows": len(rows), "url": url}
                except PlaywrightTimeoutError as exc:
                    scrape_meta["markets"][market] = {"rows": 0, "url": url, "error": str(exc)}
        finally:
            browser.close()

    all_rows = [row for row in all_rows if row["date"] == requested_date.isoformat()]
    json_path.write_text(json.dumps(all_rows, indent=2), encoding="utf-8")
    status = {
        "generated_at": datetime.now().isoformat(),
        "reference_date": args.date,
        "page_date": page_date.isoformat(),
        "row_count": len(all_rows),
        "markets": scrape_meta["markets"],
        "output_file": str(json_path),
    }
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(f"Saved {json_path}")
    print(f"Saved {status_path}")
    print(f"Rows: {len(all_rows)}")
    for market, meta in scrape_meta["markets"].items():
        print(f"{market}: {meta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
