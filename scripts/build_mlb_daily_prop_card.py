from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
TRACKER_PATH = DESKTOP_ROOT / "MLB_DAILY_PROP_TRACKER.csv"

FIRST_INNING_MIN_EDGE = 0.02
FIRST_INNING_MIN_EV = 0.03
PITCHER_CANDIDATE_MIN_EV_PCT = 5.0
TEAM_TOTAL_SHADOW_MIN_EV = 0.03


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build combined MLB daily prop card from pitcher and first-inning model outputs.")
    parser.add_argument("--date", required=True)
    return parser.parse_args()


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def load_first_inning_rows(target_date: str) -> list[dict[str, Any]]:
    payload = load_json(DESKTOP_ROOT / target_date / "first_inning_live_board.json", {})
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    out = []
    for row in rows:
        edge = float(row.get("edge", 0.0))
        ev = float(row.get("ev", 0.0))
        if edge >= FIRST_INNING_MIN_EDGE and ev >= FIRST_INNING_MIN_EV:
            book = row.get("bookmaker") or row.get("book") or "DraftKings"
            out.append(
                {
                    "date": target_date,
                    "family": "first_inning",
                    "status": "official",
                    "game": row["game"],
                    "market": row["market"],
                    "selection": row["side"],
                    "line": row.get("line", 0.5),
                    "book": book,
                    "odds": int(row["odds_american"]),
                    "model_prob": float(row["model_prob"]),
                    "market_prob": float(row["implied_prob"]),
                    "edge": edge,
                    "ev": ev,
                    "notes": "YRFI/NRFI v2 model; official if listed price is still available",
                }
            )
    best_by_selection: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in out:
        key = (row["game"], row["market"], row["selection"])
        if key not in best_by_selection or row["ev"] > best_by_selection[key]["ev"]:
            best_by_selection[key] = row
    return sorted(best_by_selection.values(), key=lambda r: r["ev"], reverse=True)


def load_pitcher_candidates(target_date: str) -> list[dict[str, Any]]:
    rows = load_json(DESKTOP_ROOT / target_date / "real_mlb_ev_props_v2.json", [])
    out = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        market = row.get("market")
        if market not in {"pitcher_strikeouts", "pitcher_outs"}:
            continue
        ev_pct = float(row.get("ev_pct", 0.0))
        if ev_pct < PITCHER_CANDIDATE_MIN_EV_PCT:
            continue
        status = "candidate"
        notes = []
        if row.get("snapshot_is_partial"):
            notes.append("partial board")
        if int(row.get("sample_size", 0) or 0) < 12:
            notes.append(f"small pitcher sample={row.get('sample_size')}")
        if not notes:
            status = "official"
        out.append(
            {
                "date": target_date,
                "family": "pitcher_props",
                "status": status,
                "game": row["game"],
                "market": market,
                "selection": f"{row['player']} {row['side']} {row['line']}",
                "line": row["line"],
                "book": row["bookmaker"],
                "odds": int(row["odds"]),
                "model_prob": float(row["model_prob"]),
                "market_prob": float(row["no_vig_prob"]),
                "edge": float(row["edge"]),
                "ev": ev_pct / 100.0,
                "notes": "; ".join(notes) or str(row.get("notes", "")),
            }
        )
    return sorted(out, key=lambda r: r["ev"], reverse=True)


def load_team_total_shadow_candidates(target_date: str) -> list[dict[str, Any]]:
    path = DESKTOP_ROOT / target_date / "team_totals_live_shadow_candidates.csv"
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                ev = float(row.get("ev", 0.0))
                edge = float(row.get("edge", 0.0))
            except ValueError:
                continue
            if ev < TEAM_TOTAL_SHADOW_MIN_EV:
                continue
            out.append(
                {
                    "date": target_date,
                    "family": "team_totals",
                    "status": "shadow",
                    "game": row["game"],
                    "market": row["market"],
                    "selection": f"{row['team']} {row['side'].upper()} {row['line']}",
                    "line": float(row["line"]),
                    "book": "DraftKings",
                    "odds": int(float(row["price"])),
                    "model_prob": float(row["model_probability"]),
                    "market_prob": float(row["devig_probability"]),
                    "edge": edge,
                    "ev": ev,
                    "notes": "SHADOW ONLY: team-total actual-price sample is too small for official/proven status",
                }
            )
    return sorted(out, key=lambda r: r["ev"], reverse=True)


def write_outputs(target_date: str, official: list[dict[str, Any]], candidates: list[dict[str, Any]], shadow: list[dict[str, Any]]) -> tuple[Path, Path, Path]:
    out_dir = DESKTOP_ROOT / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"mlb_daily_prop_card_{target_date}.json"
    csv_path = out_dir / f"mlb_daily_prop_card_{target_date}.csv"
    txt_path = out_dir / f"mlb_daily_prop_card_{target_date}.txt"

    payload = {
        "generated_at": datetime.now().isoformat(),
        "date": target_date,
        "official": official,
        "candidates": candidates,
        "shadow": shadow,
        "policy": {
            "first_inning_min_edge": FIRST_INNING_MIN_EDGE,
            "first_inning_min_ev": FIRST_INNING_MIN_EV,
            "pitcher_candidate_min_ev_pct": PITCHER_CANDIDATE_MIN_EV_PCT,
            "team_total_shadow_min_ev": TEAM_TOTAL_SHADOW_MIN_EV,
        },
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    all_rows = official + candidates + shadow
    fields = ["date", "family", "status", "game", "market", "selection", "line", "book", "odds", "model_prob", "market_prob", "edge", "ev", "notes"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    lines = [
        f"MLB Daily Prop Card - {target_date}",
        "",
        "Official plays",
    ]
    if not official:
        lines.append("- None.")
    for idx, row in enumerate(official, start=1):
        lines.append(
            f"{idx}. {row['family']} | {row['game']} | {row['selection']} {row['market']} | {row['odds']} {row['book']} | model {row['model_prob']:.2%} vs market {row['market_prob']:.2%} | edge {row['edge']:+.2%} | EV {row['ev']:+.2%}"
        )
    lines.extend(["", "Pitcher-prop candidates requiring price/sample confirmation"])
    if not candidates:
        lines.append("- None.")
    for idx, row in enumerate(candidates, start=1):
        lines.append(
            f"{idx}. {row['game']} | {row['selection']} {row['market']} | {row['odds']} {row['book']} | model {row['model_prob']:.2%} vs no-vig {row['market_prob']:.2%} | edge {row['edge']:+.2%} | EV {row['ev']:+.2%} | {row['notes']}"
        )
    lines.extend(["", "Team-total shadow candidates - NOT official"])
    if not shadow:
        lines.append("- None.")
    for idx, row in enumerate(shadow, start=1):
        lines.append(
            f"{idx}. {row['game']} | {row['selection']} | {row['odds']} {row['book']} | model {row['model_prob']:.2%} vs no-vig {row['market_prob']:.2%} | edge {row['edge']:+.2%} | EV {row['ev']:+.2%} | SHADOW ONLY"
        )
    lines.extend(
        [
            "",
            "Important:",
            "- First-inning plays are official only if the listed book/price is still available when betting.",
            "- Pitcher props are listed as candidates when board coverage is partial or pitcher sample size is below the official threshold.",
            "- Team totals are shadow-only until the actual-price archive clears sample thresholds; do not mix them with official picks.",
            "- Tracker rows are written with pending results for forward ROI verification.",
        ]
    )
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, csv_path, txt_path


def append_tracker(rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "date",
        "family",
        "status",
        "game",
        "market",
        "selection",
        "line",
        "book",
        "odds",
        "model_prob",
        "market_prob",
        "edge",
        "ev",
        "result",
        "units_risked",
        "units_won",
        "notes",
        "created_at",
    ]
    existing_keys: set[tuple[str, str, str, str, str]] = set()
    if TRACKER_PATH.exists():
        with TRACKER_PATH.open("r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                existing_keys.add((row["date"], row["family"], row["game"], row["market"], row["selection"]))
    with TRACKER_PATH.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if TRACKER_PATH.stat().st_size == 0:
            writer.writeheader()
        for row in rows:
            key = (str(row["date"]), row["family"], row["game"], row["market"], row["selection"])
            if key in existing_keys:
                continue
            out = {field: row.get(field, "") for field in fields}
            out["result"] = "PENDING"
            out["units_risked"] = 1.0
            out["units_won"] = ""
            out["created_at"] = datetime.now().isoformat()
            writer.writerow(out)


def main() -> int:
    args = parse_args()
    first_inning = load_first_inning_rows(args.date)
    pitcher_candidates = load_pitcher_candidates(args.date)
    team_total_shadow = load_team_total_shadow_candidates(args.date)
    official = first_inning + [row for row in pitcher_candidates if row["status"] == "official"]
    candidates = [row for row in pitcher_candidates if row["status"] != "official"]
    json_path, csv_path, txt_path = write_outputs(args.date, official, candidates, team_total_shadow)
    append_tracker(official)
    print(f"Saved {json_path}")
    print(f"Saved {csv_path}")
    print(f"Saved {txt_path}")
    print(f"Official plays: {len(official)}")
    print(f"Candidates: {len(candidates)}")
    print(f"Shadow plays: {len(team_total_shadow)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
