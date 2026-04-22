from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any

import pandas as pd
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
for extra in (ROOT, ROOT / "handicapping_tool", ROOT / "endgame"):
    extra_str = str(extra)
    if extra_str not in sys.path:
        sys.path.insert(0, extra_str)

from core.odds import devig_two_way, ev_percent, format_american, implied_prob


PACIFIC = ZoneInfo("America/Los_Angeles")
SUPPORTED_MARKETS = {"pitcher_strikeouts", "pitcher_outs", "batter_total_bases"}
DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"
BOX_ROOT = ROOT / "endgame" / "cache" / "boxscores"

_PITCHER_FRAMES: dict[int, pd.DataFrame] = {}
_BATTER_FRAMES: dict[int, pd.DataFrame] = {}


@dataclass
class Candidate:
    game: str
    market: str
    player: str
    line: float
    bookmaker: str
    side: str
    odds: int
    other_side_odds: int
    no_vig_prob: float
    model_prob: float
    edge: float
    ev_pct: float
    sample_size: int
    fair_odds: str
    notes: str


def normal_cdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    z = (x - mu) / (sigma * math.sqrt(2))
    return 0.5 * (1 + math.erf(z))


def poisson_tail(mean_value: float, threshold: float) -> float:
    if mean_value <= 0:
        return 0.0
    k = math.floor(threshold)
    cdf = 0.0
    term = math.exp(-mean_value)
    cdf += term
    for i in range(1, max(0, k) + 1):
        term *= mean_value / i
        cdf += term
    return max(0.0, min(1.0, 1 - cdf))


def prob_to_american(prob: float) -> str:
    prob = min(max(prob, 1e-6), 1 - 1e-6)
    if prob >= 0.5:
        return str(int(round(-(100 * prob) / (1 - prob))))
    return f"+{int(round((100 * (1 - prob)) / prob))}"


def load_todays_props(target_date: str) -> list[dict[str, Any]]:
    path = DESKTOP_ROOT / target_date / "mlb_props_normalized.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return [row for row in data if row["market"] in SUPPORTED_MARKETS]


def load_pitchers(season: int) -> pd.DataFrame:
    if season not in _PITCHER_FRAMES:
        df = pd.read_parquet(BOX_ROOT / f"pitchers_{season}.parquet")
        if "pitcher_name" not in df.columns:
            df = pd.DataFrame(columns=["pitcher_name", "is_starter", "outs_recorded", "pitches", "k"])
        _PITCHER_FRAMES[season] = df
    return _PITCHER_FRAMES[season]


def load_batters(season: int) -> pd.DataFrame:
    if season not in _BATTER_FRAMES:
        _BATTER_FRAMES[season] = pd.read_parquet(BOX_ROOT / f"batters_{season}.parquet")
    return _BATTER_FRAMES[season]


def group_two_way_markets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        side = str(row["side"]).lower()
        if side not in {"over", "under"}:
            continue
        key = (
            row["game"],
            row["market"],
            row["player"],
            row["line"],
            row["bookmaker"],
        )
        item = grouped.setdefault(
            key,
            {
                "game": row["game"],
                "market": row["market"],
                "player": row["player"],
                "line": row["line"],
                "bookmaker": row["bookmaker"],
                "over": None,
                "under": None,
            },
        )
        item[side] = int(row["odds_american"])
    return [item for item in grouped.values() if item["over"] is not None and item["under"] is not None]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Real MLB EV props for today's slate.")
    parser.add_argument("--date", default=datetime.now(PACIFIC).date().isoformat())
    parser.add_argument("--tb-limit", type=int, default=120)
    return parser.parse_args()


def shortlist_markets(markets: list[dict[str, Any]], tb_limit: int) -> list[dict[str, Any]]:
    by_side: dict[tuple, list[int]] = defaultdict(list)
    for market in markets:
        base_key = (market["game"], market["market"], market["player"], market["line"])
        by_side[base_key + ("over",)].append(int(market["over"]))
        by_side[base_key + ("under",)].append(int(market["under"]))

    scored_tb: list[tuple[float, dict[str, Any]]] = []
    keep: list[dict[str, Any]] = []
    for market in markets:
        if market["market"] != "batter_total_bases":
            keep.append(market)
            continue
        base_key = (market["game"], market["market"], market["player"], market["line"])
        over_prices = by_side[base_key + ("over",)]
        under_prices = by_side[base_key + ("under",)]
        over_consensus = mean(implied_prob(x) for x in over_prices)
        under_consensus = mean(implied_prob(x) for x in under_prices)
        over_discount = over_consensus - implied_prob(int(market["over"]))
        under_discount = under_consensus - implied_prob(int(market["under"]))
        score = max(over_discount, under_discount)
        scored_tb.append((score, market))

    scored_tb.sort(key=lambda x: x[0], reverse=True)
    keep.extend(market for _, market in scored_tb[:tb_limit])
    return keep


def build_values(player: str, market: str) -> tuple[list[float], dict[str, Any]] | None:
    season_2026 = None
    season_2025 = None
    if market.startswith("pitcher_"):
        season_2026 = load_pitchers(2026)
        season_2025 = load_pitchers(2025)
        season_2026 = season_2026[(season_2026["pitcher_name"] == player) & (season_2026["is_starter"] == True)].copy()
        season_2025 = season_2025[(season_2025["pitcher_name"] == player) & (season_2025["is_starter"] == True)].copy()
        season_2026 = season_2026[(season_2026["outs_recorded"] >= 9) | (season_2026["pitches"] >= 50)]
        season_2025 = season_2025[(season_2025["outs_recorded"] >= 9) | (season_2025["pitches"] >= 50)]
        values_2026 = [
            int(row["k"]) if market == "pitcher_strikeouts" else int(row["outs_recorded"])
            for _, row in season_2026.iterrows()
        ]
        values_2025 = [
            int(row["k"]) if market == "pitcher_strikeouts" else int(row["outs_recorded"])
            for _, row in season_2025.iterrows()
        ]
    else:
        season_2026 = load_batters(2026)
        season_2025 = load_batters(2025)
        season_2026 = season_2026[(season_2026["batter_name"] == player) & (season_2026["is_starter"] == True)].copy()
        season_2025 = season_2025[(season_2025["batter_name"] == player) & (season_2025["is_starter"] == True)].copy()
        values_2026 = [
            int(row["h"]) + int(row["d"]) + 2 * int(row["t"]) + 3 * int(row["hr"])
            for _, row in season_2026.iterrows()
        ]
        values_2025 = [
            int(row["h"]) + int(row["d"]) + 2 * int(row["t"]) + 3 * int(row["hr"])
            for _, row in season_2025.iterrows()
        ]

    if not values_2026 and not values_2025:
        return None

    return values_2026 + values_2025, {
        "player_name": player,
        "values_2026": values_2026,
        "values_2025": values_2025,
    }


def model_probability(values: list[float], line: float, market: str) -> tuple[float, str]:
    if not values:
        return 0.0, "no sample"

    recent = values[-10:]
    season = values
    avg_recent = mean(recent)
    avg_full = mean(season)
    mu = avg_full * 0.6 + avg_recent * 0.4

    if market == "pitcher_outs":
        sigma = max(1.5, (sum((x - avg_full) ** 2 for x in season) / max(1, len(season) - 1)) ** 0.5)
        over = 1 - normal_cdf(line, mu, sigma)
        note = f"normal mu={mu:.2f} sigma={sigma:.2f}"
        return max(0.01, min(0.99, over)), note

    if market == "pitcher_strikeouts":
        over = poisson_tail(max(0.1, mu), line)
        note = f"poisson mu={mu:.2f}"
        return max(0.01, min(0.99, over)), note

    sigma = max(0.75, (sum((x - avg_full) ** 2 for x in season) / max(1, len(season) - 1)) ** 0.5)
    over = 1 - normal_cdf(line, mu, sigma)
    note = f"tb-normal mu={mu:.2f} sigma={sigma:.2f}"
    return max(0.01, min(0.99, over)), note


def build_candidates(target_date: str, tb_limit: int) -> list[Candidate]:
    rows = load_todays_props(target_date)
    markets = shortlist_markets(group_two_way_markets(rows), tb_limit)
    candidates: list[Candidate] = []
    cache: dict[tuple[str, str], tuple[list[float], dict[str, Any]] | None] = {}

    for market in markets:
        key = (market["player"], market["market"])
        if key not in cache:
            cache[key] = build_values(market["player"], market["market"])
        built = cache[key]
        if not built:
            continue
        values, meta = built
        over_prob, note = model_probability(values, float(market["line"]), market["market"])
        if market["market"].startswith("pitcher_") and len(values) < 8:
            continue
        if market["market"] == "batter_total_bases" and len(values) < 20:
            continue
        over_nv, under_nv = devig_two_way(int(market["over"]), int(market["under"]))
        over_ev = ev_percent(over_prob, int(market["over"]))
        under_prob = 1 - over_prob
        under_ev = ev_percent(under_prob, int(market["under"]))

        over_edge = over_prob - over_nv
        under_edge = under_prob - under_nv

        over_fair = prob_to_american(over_prob)
        under_fair = prob_to_american(under_prob)

        if over_ev > 0:
            candidates.append(
                Candidate(
                    game=market["game"],
                    market=market["market"],
                    player=meta["player_name"],
                    line=float(market["line"]),
                    bookmaker=market["bookmaker"],
                    side="Over",
                    odds=int(market["over"]),
                    other_side_odds=int(market["under"]),
                    no_vig_prob=over_nv,
                    model_prob=over_prob,
                    edge=over_edge,
                    ev_pct=over_ev * 100,
                    sample_size=len(values),
                    fair_odds=over_fair,
                    notes=note,
                )
            )
        if under_ev > 0:
            candidates.append(
                Candidate(
                    game=market["game"],
                    market=market["market"],
                    player=meta["player_name"],
                    line=float(market["line"]),
                    bookmaker=market["bookmaker"],
                    side="Under",
                    odds=int(market["under"]),
                    other_side_odds=int(market["over"]),
                    no_vig_prob=under_nv,
                    model_prob=under_prob,
                    edge=under_edge,
                    ev_pct=under_ev * 100,
                    sample_size=len(values),
                    fair_odds=under_fair,
                    notes=note,
                )
            )

    candidates.sort(key=lambda x: x.ev_pct, reverse=True)
    return candidates


def main() -> int:
    args = parse_args()
    target_date = args.date
    candidates = build_candidates(target_date, args.tb_limit)
    output_dir = DESKTOP_ROOT / target_date
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "real_mlb_ev_props.json"
    report_path = output_dir / "real_mlb_ev_props_report.txt"

    payload = [
        {
            "game": c.game,
            "market": c.market,
            "player": c.player,
            "line": c.line,
            "bookmaker": c.bookmaker,
            "side": c.side,
            "odds": c.odds,
            "other_side_odds": c.other_side_odds,
            "no_vig_prob": round(c.no_vig_prob, 4),
            "model_prob": round(c.model_prob, 4),
            "edge": round(c.edge, 4),
            "ev_pct": round(c.ev_pct, 2),
            "sample_size": c.sample_size,
            "fair_odds": c.fair_odds,
            "notes": c.notes,
        }
        for c in candidates
    ]
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [f"Real MLB EV props for {target_date}", ""]
    for idx, c in enumerate(candidates[:25], 1):
        lines.append(
            f"{idx}. {c.ev_pct:.2f}% EV | {c.game} | {c.player} | {c.side} {c.line} {c.market} | "
            f"{format_american(c.odds)} at {c.bookmaker} | model {c.model_prob:.1%} vs no-vig {c.no_vig_prob:.1%} | "
            f"fair {c.fair_odds} | n={c.sample_size} | {c.notes}"
        )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved {output_path}")
    print(f"Saved {report_path}")
    for line in lines[:12]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
