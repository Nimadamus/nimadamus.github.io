from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
BOX_ROOT = Path.home() / "endgame" / "cache" / "boxscores"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Settle saved real MLB EV props using boxscore data.")
    parser.add_argument("--date", required=True, help="Slate date in YYYY-MM-DD.")
    return parser.parse_args()


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_boxscores(season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    pitchers = pd.read_parquet(BOX_ROOT / f"pitchers_{season}.parquet")
    batters = pd.read_parquet(BOX_ROOT / f"batters_{season}.parquet")
    return pitchers, batters


def total_bases_from_row(row: pd.Series) -> int:
    singles = int(row["h"]) - int(row["d"]) - int(row["t"]) - int(row["hr"])
    return singles + 2 * int(row["d"]) + 3 * int(row["t"]) + 4 * int(row["hr"])


def settle_row(row: dict[str, Any], pitchers: pd.DataFrame, batters: pd.DataFrame) -> dict[str, Any]:
    slate_date = row["game_date"] if "game_date" in row else row.get("date")
    market = row["market"]
    player = row["player"]
    line = float(row["line"])
    side = row["side"].lower()

    settled = dict(row)
    settled["settled"] = False
    settled["actual"] = None
    settled["result"] = "ungraded"
    settled["profit_units"] = None

    if market in {"pitcher_strikeouts", "pitcher_outs"}:
        subset = pitchers[(pitchers["date"] == slate_date) & (pitchers["pitcher_name"] == player) & (pitchers["is_starter"] == True)]
        if subset.empty:
            return settled
        record = subset.iloc[0]
        actual = int(record["k"]) if market == "pitcher_strikeouts" else int(record["outs_recorded"])
    elif market == "batter_total_bases":
        subset = batters[(batters["date"] == slate_date) & (batters["batter_name"] == player)]
        if subset.empty:
            return settled
        record = subset.iloc[0]
        actual = total_bases_from_row(record)
    else:
        return settled

    settled["actual"] = actual
    over = actual > line
    under = actual < line
    push = actual == line
    if push:
        result = "push"
        profit_units = 0.0
    elif side == "over":
        result = "win" if over else "loss"
    else:
        result = "win" if under else "loss"

    if not push:
        odds = int(row["odds"])
        if result == "win":
            profit_units = odds / 100 if odds > 0 else 100 / abs(odds)
        else:
            profit_units = -1.0

    settled["settled"] = True
    settled["result"] = result
    settled["profit_units"] = round(profit_units, 4)
    return settled


def main() -> int:
    args = parse_args()
    slate_date = args.date
    season = int(slate_date[:4])
    input_path = DESKTOP_ROOT / slate_date / "real_mlb_ev_props.json"
    output_path = DESKTOP_ROOT / slate_date / "real_mlb_ev_props_settled.json"
    summary_path = DESKTOP_ROOT / slate_date / "real_mlb_ev_props_settlement_summary.txt"

    rows = load_json(input_path)
    for row in rows:
        row["game_date"] = slate_date

    pitchers, batters = load_boxscores(season)
    settled = [settle_row(row, pitchers, batters) for row in rows]
    output_path.write_text(json.dumps(settled, indent=2), encoding="utf-8")

    graded = [row for row in settled if row["settled"]]
    wins = sum(1 for row in graded if row["result"] == "win")
    losses = sum(1 for row in graded if row["result"] == "loss")
    pushes = sum(1 for row in graded if row["result"] == "push")
    profit = round(sum(float(row["profit_units"]) for row in graded), 4)
    roi = round((profit / max(1, wins + losses)) * 100, 2)

    summary = [
        f"Settlement summary for {slate_date}",
        f"graded={len(graded)} wins={wins} losses={losses} pushes={pushes}",
        f"profit_units={profit}",
        f"roi_pct={roi}",
    ]
    summary_path.write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))
    print(f"Saved {output_path}")
    print(f"Saved {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
