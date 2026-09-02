from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd
import requests


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
TRACKER_PATH = DESKTOP_ROOT / "MLB_DAILY_PROP_TRACKER.csv"
MLB_API = "https://statsapi.mlb.com/api/v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle tracked MLB daily prop card official plays.")
    parser.add_argument("--date", required=True)
    return parser.parse_args()


def american_profit(odds: int) -> float:
    return odds / 100.0 if odds > 0 else 100.0 / abs(odds)


def fetch_first_inning_results(target_date: str) -> dict[str, int]:
    response = requests.get(
        f"{MLB_API}/schedule",
        params={"sportId": 1, "startDate": target_date, "endDate": target_date, "gameType": "R", "hydrate": "linescore"},
        timeout=30,
    )
    response.raise_for_status()
    results: dict[str, int] = {}
    for date_block in response.json().get("dates", []):
        for game in date_block.get("games", []):
            status = (game.get("status") or {}).get("detailedState", "")
            if status not in {"Final", "Game Over", "Completed Early"}:
                continue
            linescore = game.get("linescore", {}) or {}
            innings = linescore.get("innings", []) or []
            if not innings:
                continue
            first = innings[0]
            away_runs = int((first.get("away") or {}).get("runs") or 0)
            home_runs = int((first.get("home") or {}).get("runs") or 0)
            away = game["teams"]["away"]["team"]["name"]
            home = game["teams"]["home"]["team"]["name"]
            results[f"{away} @ {home}"] = away_runs + home_runs
    return results


def settle_row(row: dict[str, str], first_inning_results: dict[str, int]) -> dict[str, str]:
    if row.get("result") not in {"", "PENDING"}:
        return row
    if row.get("family") != "first_inning":
        return row
    game = row.get("game", "")
    if game not in first_inning_results:
        return row
    total = first_inning_results[game]
    market = row.get("market", "").lower()
    if market == "yrfi":
        won = total >= 1
    elif market == "nrfi":
        won = total == 0
    else:
        return row
    odds = int(float(row["odds"]))
    row["result"] = "WIN" if won else "LOSS"
    row["units_risked"] = "1.0"
    row["units_won"] = f"{american_profit(odds):.6f}" if won else "-1.000000"
    note = row.get("notes", "")
    row["notes"] = f"{note}; settled first_inning_total={total}".strip("; ")
    return row


def write_summary(target_date: str, rows: list[dict[str, str]]) -> Path:
    graded = [row for row in rows if row.get("date") == target_date and row.get("result") in {"WIN", "LOSS"}]
    wins = sum(1 for row in graded if row.get("result") == "WIN")
    losses = sum(1 for row in graded if row.get("result") == "LOSS")
    units = sum(float(row.get("units_won") or 0.0) for row in graded)
    risked = sum(float(row.get("units_risked") or 0.0) for row in graded)
    roi = units / risked if risked else 0.0
    out = DESKTOP_ROOT / target_date / f"mlb_daily_prop_settlement_{target_date}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"MLB Daily Prop Settlement - {target_date}",
        "",
        f"Record: {wins}-{losses}",
        f"Units: {units:+.4f}",
        f"Risked: {risked:.4f}",
        f"ROI: {roi:+.2%}" if risked else "ROI: N/A",
        "",
    ]
    for row in graded:
        lines.append(f"- {row['result']} | {row['game']} | {row['selection']} {row['market']} | {row['odds']} | units {float(row['units_won']):+.4f}")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    args = parse_args()
    if not TRACKER_PATH.exists():
        raise SystemExit(f"Missing tracker: {TRACKER_PATH}")
    with TRACKER_PATH.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
        fields = list(rows[0].keys()) if rows else []
    first_inning_results = fetch_first_inning_results(args.date)
    updated = [settle_row(row, first_inning_results) for row in rows]
    with TRACKER_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(updated)
    summary_path = write_summary(args.date, updated)
    print(f"Updated {TRACKER_PATH}")
    print(f"Saved {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
