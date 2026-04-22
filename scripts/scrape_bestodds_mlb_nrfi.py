from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
BESTODDS_EDGE_URL = "https://edge.bestodds.com/api/the-base/nrfi-enhanced"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape BestOdds EDGE MLB NRFI/YRFI odds.")
    parser.add_argument("--date", default=str(date.today()), help="Target game date in YYYY-MM-DD.")
    parser.add_argument("--output-dir", default=str(DESKTOP_ROOT), help="Root output directory.")
    return parser.parse_args()


def decimal_to_american(decimal_price: float | None) -> int | None:
    if decimal_price is None or decimal_price <= 1:
        return None
    if decimal_price >= 2:
        return round((decimal_price - 1) * 100)
    return round(-100 / (decimal_price - 1))


def parse_game_date(raw_date: str) -> str:
    # Example: "2026-04-15 13:40 -04:00"
    dt = datetime.strptime(raw_date, "%Y-%m-%d %H:%M %z")
    return dt.astimezone(ZoneInfo("America/New_York")).date().isoformat()


def fetch_bestodds_nrfi() -> dict[str, Any]:
    response = requests.get(
        BESTODDS_EDGE_URL,
        params={"getSchedules": "true"},
        headers={
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://edge.bestodds.com/nrfi",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=45,
    )
    response.raise_for_status()
    return response.json()


def normalize_rows(payload: dict[str, Any], target_date: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    scrape_time = datetime.now().isoformat(timespec="seconds")
    for game in payload.get("schedules", []):
        raw_date = game.get("date")
        if not raw_date:
            continue
        game_date = parse_game_date(raw_date)
        if game_date != target_date:
            continue
        away = game.get("awayAbbr") or game.get("teamOppInitials")
        home = game.get("homeAbbr") or game.get("teamInitials")
        if not away or not home:
            continue
        game_name = f"{away} @ {home}"
        for odds in game.get("nrfiOdds") or []:
            operator = odds.get("operator")
            yrfi_decimal = odds.get("price1")
            nrfi_decimal = odds.get("price2")
            for side, decimal_price in (("YRFI", yrfi_decimal), ("NRFI", nrfi_decimal)):
                if decimal_price is None:
                    continue
                rows.append(
                    {
                        "date": game_date,
                        "game_time": raw_date,
                        "game": game_name,
                        "away": away,
                        "home": home,
                        "bookmaker": operator,
                        "bookmaker_key": str(operator or "").lower(),
                        "market": "yrfi" if side == "YRFI" else "nrfi",
                        "side": side,
                        "line": 0.5,
                        "odds_decimal": float(decimal_price),
                        "odds_american": decimal_to_american(float(decimal_price)),
                        "metabet_game_id": game.get("mbGameId") or odds.get("metaBetGameId"),
                        "sr_game_id": game.get("srGameId") or game.get("gameID"),
                        "source": BESTODDS_EDGE_URL,
                        "last_update": scrape_time,
                    }
                )
    rows.sort(key=lambda row: (row["game_time"], row["game"], row["bookmaker"], row["side"]))
    return rows


def write_outputs(rows: list[dict[str, Any]], payload: dict[str, Any], output_root: Path, target_date: str) -> None:
    out_dir = output_root / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "bestodds_nrfi_yrfi_normalized.json"
    csv_path = out_dir / "bestodds_nrfi_yrfi_normalized.csv"
    raw_path = out_dir / "bestodds_nrfi_yrfi_raw.json"
    status_path = out_dir / "bestodds_nrfi_yrfi_status.json"

    json_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    status = {
        "target_date": target_date,
        "source": BESTODDS_EDGE_URL,
        "games_in_payload": len(payload.get("schedules", [])),
        "normalized_rows": len(rows),
        "games_for_target_date": len({row["game"] for row in rows}),
        "books": sorted({row["bookmaker"] for row in rows if row.get("bookmaker")}),
        "outputs": {
            "json": str(json_path),
            "csv": str(csv_path),
            "raw": str(raw_path),
        },
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
        "notes": "price1 is YRFI; price2 is NRFI, based on BestOdds EDGE NRFI app display code.",
    }
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))


def main() -> None:
    args = parse_args()
    target_date = date.fromisoformat(args.date).isoformat()
    payload = fetch_bestodds_nrfi()
    rows = normalize_rows(payload, target_date)
    write_outputs(rows, payload, Path(args.output_dir), target_date)


if __name__ == "__main__":
    main()
