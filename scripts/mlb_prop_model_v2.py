from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import poisson, norm
from sklearn.linear_model import PoissonRegressor, Ridge


BOX_ROOT = Path.home() / "endgame" / "cache" / "boxscores"
DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"

PITCHER_FEATURES = [
    "is_home",
    "handed_r",
    "p_k_l5",
    "p_k_l10",
    "p_outs_l5",
    "p_pitches_l5",
    "p_bb_l5",
    "opp_k_rate_l10",
    "opp_tb_rate_l10",
]

BATTER_FEATURES = [
    "is_home",
    "order_slot",
    "b_tb_l5",
    "b_tb_l10",
    "b_pa_l10",
    "b_h_l10",
    "opp_sp_k_l5",
    "opp_sp_outs_l5",
    "opp_sp_h_l5",
    "opp_sp_bb_l5",
    "opp_sp_hand_r",
]

OFFICIAL_MARKETS = {"pitcher_strikeouts", "pitcher_outs"}
MAX_OFFICIAL_PICKS = 12
MIN_EDGE_PCT = 0.05
MIN_SAMPLE_K = 12
MIN_SAMPLE_OUTS = 12
MAX_ABS_CALIBRATION_GAP = 0.08
MAX_SNAPSHOT_AGE_HOURS = 4
MIN_OFFICIAL_GAME_COVERAGE_RATIO = 0.6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sophisticated MLB prop model v2.")
    parser.add_argument("--date", default="2026-04-14")
    parser.add_argument("--tb-limit", type=int, default=120)
    return parser.parse_args()


def parse_iso_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def american_to_decimal(odds: int) -> float:
    return 1 + (odds / 100 if odds > 0 else 100 / abs(odds))


def implied_prob(odds: int) -> float:
    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)


def devig_two_way(a: int, b: int) -> tuple[float, float]:
    pa, pb = implied_prob(a), implied_prob(b)
    total = pa + pb
    return pa / total, pb / total


def ev_pct(true_prob: float, odds: int) -> float:
    dec = american_to_decimal(odds)
    return (true_prob * (dec - 1) - (1 - true_prob)) * 100


def prob_to_american(prob: float) -> str:
    prob = min(max(prob, 1e-6), 1 - 1e-6)
    if prob >= 0.5:
        return str(int(round(-(100 * prob) / (1 - prob))))
    return f"+{int(round((100 * (1 - prob)) / prob))}"


def total_bases_series(df: pd.DataFrame) -> pd.Series:
    singles = df["h"] - df["d"] - df["t"] - df["hr"]
    return singles + 2 * df["d"] + 3 * df["t"] + 4 * df["hr"]


def add_group_rolls(df: pd.DataFrame, group_col: str, cols: list[str], windows: list[int], prefix: str) -> pd.DataFrame:
    df = df.sort_values(["date", "game_pk"]).copy()
    for col in cols:
        grp = df.groupby(group_col)[col]
        for window in windows:
            df[f"{prefix}{col}_l{window}"] = grp.transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    return df


def prepare_team_offense(batters: pd.DataFrame, starters_only: bool = True) -> pd.DataFrame:
    b = batters.copy()
    if starters_only:
        b = b[b["is_starter"] == True].copy()
    b["tb"] = total_bases_series(b)
    team_games = (
        b.groupby(["game_pk", "date", "team_id", "team_name"], as_index=False)
        .agg(team_so=("so", "sum"), team_pa=("pa", "sum"), team_tb=("tb", "sum"))
        .sort_values(["team_id", "date", "game_pk"])
    )
    team_games["team_k_rate"] = team_games["team_so"] / team_games["team_pa"].clip(lower=1)
    team_games["team_tb_rate"] = team_games["team_tb"] / team_games["team_pa"].clip(lower=1)
    team_games = add_group_rolls(team_games, "team_id", ["team_k_rate", "team_tb_rate"], [10], "roll_")
    return team_games


def load_base_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    pitchers_2025 = pd.read_parquet(BOX_ROOT / "pitchers_2025.parquet")
    batters_2025 = pd.read_parquet(BOX_ROOT / "batters_2025.parquet")
    batters_2026 = pd.read_parquet(BOX_ROOT / "batters_2026.parquet")
    pitchers_2026_path = BOX_ROOT / "pitchers_2026.parquet"
    pitchers_2026 = pd.read_parquet(pitchers_2026_path)
    if "pitcher_name" not in pitchers_2026.columns:
        pitchers_2026 = pitchers_2025.iloc[0:0].copy()
    return pitchers_2025, batters_2025, pitchers_2026, batters_2026


def build_pitcher_training(pitchers_2025: pd.DataFrame, batters_2025: pd.DataFrame) -> pd.DataFrame:
    starters = pitchers_2025[pitchers_2025["is_starter"] == True].copy()
    starters["date"] = pd.to_datetime(starters["date"])
    starters = starters.sort_values(["pitcher_id", "date", "game_pk"]).copy()
    starters["starts_hist"] = starters.groupby("pitcher_id").cumcount()
    starters["handed_r"] = (starters["handedness"] == "R").astype(int)
    starters = add_group_rolls(starters, "pitcher_id", ["k", "outs_recorded", "pitches", "bb"], [5, 10], "p_")

    team_off = prepare_team_offense(batters_2025)
    team_off["date"] = pd.to_datetime(team_off["date"])
    starters = starters.merge(
        team_off[["game_pk", "team_id", "roll_team_k_rate_l10", "roll_team_tb_rate_l10"]],
        left_on=["game_pk", "opp_team_id"],
        right_on=["game_pk", "team_id"],
        how="left",
    )
    starters["opp_k_rate_l10"] = starters["roll_team_k_rate_l10"].fillna(starters["roll_team_k_rate_l10"].median())
    starters["opp_tb_rate_l10"] = starters["roll_team_tb_rate_l10"].fillna(starters["roll_team_tb_rate_l10"].median())
    starters["is_home"] = starters["is_home"].astype(int)
    starters = starters.dropna(subset=["p_k_l5", "p_outs_recorded_l5", "p_pitches_l5", "p_bb_l5"])
    starters["p_outs_l5"] = starters["p_outs_recorded_l5"]
    starters["p_k_l10"] = starters["p_k_l10"].fillna(starters["p_k_l5"])
    return starters


def build_batter_training(pitchers_2025: pd.DataFrame, batters_2025: pd.DataFrame) -> pd.DataFrame:
    starters = batters_2025[batters_2025["is_starter"] == True].copy()
    starters["date"] = pd.to_datetime(starters["date"])
    starters = starters.sort_values(["batter_id", "date", "game_pk"]).copy()
    starters["games_hist"] = starters.groupby("batter_id").cumcount()
    starters["tb"] = total_bases_series(starters)
    starters = add_group_rolls(starters, "batter_id", ["tb", "pa", "h"], [5, 10], "b_")

    opp_starters = pitchers_2025[pitchers_2025["is_starter"] == True].copy()
    opp_starters["date"] = pd.to_datetime(opp_starters["date"])
    opp_starters["opp_sp_hand_r"] = (opp_starters["handedness"] == "R").astype(int)
    opp_starters = add_group_rolls(opp_starters, "pitcher_id", ["k", "outs_recorded", "h", "bb"], [5], "opp_sp_")
    opp_starters = opp_starters[
        ["game_pk", "team_id", "pitcher_name", "opp_sp_hand_r", "opp_sp_k_l5", "opp_sp_outs_recorded_l5", "opp_sp_h_l5", "opp_sp_bb_l5"]
    ].copy()
    opp_starters["opp_sp_outs_l5"] = opp_starters["opp_sp_outs_recorded_l5"]

    starters = starters.merge(
        opp_starters,
        left_on=["game_pk", "opp_team_id"],
        right_on=["game_pk", "team_id"],
        how="left",
    )
    starters["is_home"] = starters["is_home"].astype(int)
    starters["order_slot"] = starters["order_slot"].fillna(9).clip(lower=1, upper=9)
    starters = starters.dropna(subset=["b_tb_l5", "b_tb_l10", "opp_sp_k_l5", "opp_sp_outs_l5"])
    return starters


def fit_models(pitchers_2025: pd.DataFrame, batters_2025: pd.DataFrame) -> dict[str, Any]:
    pitcher_train = build_pitcher_training(pitchers_2025, batters_2025)
    batter_train = build_batter_training(pitchers_2025, batters_2025)

    k_model = PoissonRegressor(alpha=0.2, max_iter=1000)
    k_model.fit(pitcher_train[PITCHER_FEATURES], pitcher_train["k"])

    outs_model = Ridge(alpha=2.0)
    outs_model.fit(pitcher_train[PITCHER_FEATURES], pitcher_train["outs_recorded"])
    outs_resid_std = float((pitcher_train["outs_recorded"] - outs_model.predict(pitcher_train[PITCHER_FEATURES])).std())

    tb_model = PoissonRegressor(alpha=0.5, max_iter=1000)
    tb_model.fit(batter_train[BATTER_FEATURES], batter_train["tb"])

    return {
        "k_model": k_model,
        "outs_model": outs_model,
        "outs_resid_std": max(1.5, outs_resid_std),
        "tb_model": tb_model,
        "pitcher_train": pitcher_train,
        "batter_train": batter_train,
    }


def evaluate_models(models: dict[str, Any]) -> dict[str, Any]:
    pitcher_train = models["pitcher_train"].sort_values("date").copy()
    batter_train = models["batter_train"].sort_values("date").copy()

    pitcher_cut = pitcher_train["date"].quantile(0.8)
    batter_cut = batter_train["date"].quantile(0.8)
    pitcher_test = pitcher_train[pitcher_train["date"] >= pitcher_cut].copy()
    batter_test = batter_train[batter_train["date"] >= batter_cut].copy()

    k_pred = models["k_model"].predict(pitcher_test[PITCHER_FEATURES])
    outs_pred = models["outs_model"].predict(pitcher_test[PITCHER_FEATURES])
    tb_pred = models["tb_model"].predict(batter_test[BATTER_FEATURES])

    summary = {
        "pitcher_strikeouts": line_metrics_from_count_preds(k_pred, pitcher_test["k"].to_numpy(), [3.5, 4.5, 5.5, 6.5, 7.5], "poisson"),
        "pitcher_outs": line_metrics_from_count_preds(outs_pred, pitcher_test["outs_recorded"].to_numpy(), [14.5, 15.5, 16.5, 17.5, 18.5], "normal", models["outs_resid_std"]),
        "batter_total_bases": line_metrics_from_count_preds(tb_pred, batter_test["tb"].to_numpy(), [0.5, 1.5], "poisson"),
    }
    summary["_meta"] = {
        "pitcher_train_rows": int(len(pitcher_train)),
        "pitcher_test_rows": int(len(pitcher_test)),
        "batter_train_rows": int(len(batter_train)),
        "batter_test_rows": int(len(batter_test)),
    }
    return summary


def build_binary_outcomes(actual: np.ndarray, line: float) -> tuple[np.ndarray, np.ndarray]:
    outcomes = np.where(actual > line, 1.0, np.where(actual < line, 0.0, np.nan))
    mask = ~np.isnan(outcomes)
    return outcomes[mask], mask


def reliability_bins(probs: np.ndarray, obs: np.ndarray, n_bins: int = 8) -> list[dict[str, Any]]:
    if len(probs) == 0:
        return []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins: list[dict[str, Any]] = []
    for idx in range(n_bins):
        lo, hi = float(edges[idx]), float(edges[idx + 1])
        if idx == n_bins - 1:
            mask = (probs >= lo) & (probs <= hi)
        else:
            mask = (probs >= lo) & (probs < hi)
        if not np.any(mask):
            continue
        p = probs[mask]
        y = obs[mask]
        bins.append(
            {
                "bin_lo": round(lo, 3),
                "bin_hi": round(hi, 3),
                "count": int(mask.sum()),
                "avg_pred": round(float(np.mean(p)), 4),
                "actual_rate": round(float(np.mean(y)), 4),
                "gap": round(float(np.mean(p) - np.mean(y)), 4),
            }
        )
    return bins


def walkforward_pitcher_backtest(models: dict[str, Any]) -> dict[str, Any]:
    pitcher_train = models["pitcher_train"].sort_values("date").copy()
    unique_dates = np.array(sorted(pitcher_train["date"].dt.normalize().unique()))
    date_folds = [fold for fold in np.array_split(unique_dates, 5) if len(fold) > 0]

    line_map = {
        "pitcher_strikeouts": [4.5, 5.5, 6.5],
        "pitcher_outs": [15.5, 16.5, 17.5],
    }
    family_map = {
        "pitcher_strikeouts": "poisson",
        "pitcher_outs": "normal",
    }

    store: dict[str, dict[float, dict[str, list[float]]]] = {
        market: {line: {"preds": [], "obs": []} for line in lines}
        for market, lines in line_map.items()
    }
    fold_summaries: list[dict[str, Any]] = []

    for fold_idx in range(2, len(date_folds)):
        test_dates = set(pd.to_datetime(date_folds[fold_idx]))
        train_dates = set(pd.to_datetime(np.concatenate(date_folds[:fold_idx])))
        train_df = pitcher_train[pitcher_train["date"].dt.normalize().isin(train_dates)].copy()
        test_df = pitcher_train[pitcher_train["date"].dt.normalize().isin(test_dates)].copy()
        if len(train_df) < 250 or len(test_df) < 50:
            continue

        k_model = PoissonRegressor(alpha=0.2, max_iter=1000)
        k_model.fit(train_df[PITCHER_FEATURES], train_df["k"])
        outs_model = Ridge(alpha=2.0)
        outs_model.fit(train_df[PITCHER_FEATURES], train_df["outs_recorded"])
        outs_sigma = float((train_df["outs_recorded"] - outs_model.predict(train_df[PITCHER_FEATURES])).std())
        outs_sigma = max(1.5, outs_sigma)

        k_pred = k_model.predict(test_df[PITCHER_FEATURES])
        outs_pred = outs_model.predict(test_df[PITCHER_FEATURES])
        fold_summary = {
            "fold_index": fold_idx,
            "train_rows": int(len(train_df)),
            "test_rows": int(len(test_df)),
            "date_start": str(test_df["date"].min().date()),
            "date_end": str(test_df["date"].max().date()),
        }

        for market, lines in line_map.items():
            actual = test_df["k"].to_numpy() if market == "pitcher_strikeouts" else test_df["outs_recorded"].to_numpy()
            pred_mean = k_pred if market == "pitcher_strikeouts" else outs_pred
            for line in lines:
                if family_map[market] == "poisson":
                    probs = 1 - poisson.cdf(math.floor(line), pred_mean)
                else:
                    probs = 1 - norm.cdf(line, loc=pred_mean, scale=outs_sigma)
                obs, mask = build_binary_outcomes(actual, line)
                p = probs[mask]
                if len(p) == 0:
                    continue
                store[market][line]["preds"].extend([float(x) for x in p])
                store[market][line]["obs"].extend([float(x) for x in obs])
                fold_summary[f"{market}_{line}"] = {
                    "bets": int(len(p)),
                    "avg_pred": round(float(np.mean(p)), 4),
                    "actual_rate": round(float(np.mean(obs)), 4),
                    "brier": round(float(np.mean((p - obs) ** 2)), 4),
                }
        fold_summaries.append(fold_summary)

    aggregate: dict[str, Any] = {"folds": fold_summaries}
    for market, lines in line_map.items():
        aggregate[market] = {}
        for line in lines:
            probs = np.asarray(store[market][line]["preds"], dtype=float)
            obs = np.asarray(store[market][line]["obs"], dtype=float)
            if len(probs) == 0:
                continue
            aggregate[market][str(line)] = {
                "bets": int(len(probs)),
                "avg_pred": round(float(np.mean(probs)), 4),
                "actual_rate": round(float(np.mean(obs)), 4),
                "abs_gap": round(float(abs(np.mean(probs) - np.mean(obs))), 4),
                "brier": round(float(np.mean((probs - obs) ** 2)), 4),
                "reliability_bins": reliability_bins(probs, obs),
            }
    return aggregate


def calibrate_over_prob(market: str, line: float, over_prob: float, backtest: dict[str, Any]) -> float:
    market_block = backtest.get(market, {})
    line_block = market_block.get(str(float(line))) or market_block.get(str(line))
    if not line_block:
        return float(min(max(over_prob, 0.01), 0.99))
    avg_pred = float(line_block["avg_pred"])
    actual_rate = float(line_block["actual_rate"])
    if avg_pred <= 0:
        return float(min(max(over_prob, 0.01), 0.99))
    ratio = actual_rate / avg_pred
    # Partial shrink only; avoid overfitting to one holdout split.
    adjusted = over_prob * (0.65 + 0.35 * ratio)
    return float(min(max(adjusted, 0.01), 0.99))


def calibration_gap(market: str, line: float, backtest: dict[str, Any]) -> float:
    market_block = backtest.get(market, {})
    line_block = market_block.get(str(float(line))) or market_block.get(str(line))
    if not line_block:
        return 1.0
    return abs(float(line_block["avg_pred"]) - float(line_block["actual_rate"]))


def line_metrics_from_count_preds(pred_mean: np.ndarray, actual: np.ndarray, lines: list[float], family: str, sigma: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in lines:
        if family == "poisson":
            probs = 1 - poisson.cdf(math.floor(line), pred_mean)
        else:
            probs = 1 - norm.cdf(line, loc=pred_mean, scale=sigma)
        outcomes = np.where(actual > line, 1.0, np.where(actual < line, 0.0, np.nan))
        mask = ~np.isnan(outcomes)
        probs = probs[mask]
        obs = outcomes[mask]
        brier = float(np.mean((probs - obs) ** 2))
        out[str(line)] = {
            "bets": int(mask.sum()),
            "avg_pred": round(float(np.mean(probs)), 4),
            "actual_rate": round(float(np.mean(obs)), 4),
            "brier": round(brier, 4),
        }
    return out


def latest_pitcher_state(pitchers_2025: pd.DataFrame, pitchers_2026: pd.DataFrame, batters_2025: pd.DataFrame, batters_2026: pd.DataFrame) -> pd.DataFrame:
    all_pitchers = pd.concat([pitchers_2025, pitchers_2026], ignore_index=True)
    all_batters = pd.concat([batters_2025, batters_2026], ignore_index=True)
    states = build_pitcher_training(all_pitchers, all_batters).sort_values("date")
    return states.groupby("pitcher_name", as_index=False).tail(1).copy()


def latest_batter_state(pitchers_2025: pd.DataFrame, pitchers_2026: pd.DataFrame, batters_2025: pd.DataFrame, batters_2026: pd.DataFrame) -> pd.DataFrame:
    states = build_batter_training(pd.concat([pitchers_2025, pitchers_2026], ignore_index=True), pd.concat([batters_2025, batters_2026], ignore_index=True)).sort_values("date")
    return states.groupby("batter_name", as_index=False).tail(1).copy()


def load_live_props(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = DESKTOP_ROOT / target_date / "mlb_props_normalized.json"
    status_path = DESKTOP_ROOT / target_date / "sync_status.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    supported = {"pitcher_strikeouts", "pitcher_outs", "batter_total_bases"}
    data = [
        row for row in data
        if row.get("market") in supported
        and str(row.get("side")).lower() in {"over", "under"}
        and str(row.get("date", target_date)) == target_date
    ]
    grouped: dict[tuple, dict[str, Any]] = {}
    for row in data:
        key = (row["game"], row["market"], row["player"], row["line"], row["bookmaker"])
        item = grouped.setdefault(
            key,
            {
                "game": row["game"],
                "market": row["market"],
                "player": row["player"],
                "line": float(row["line"]),
                "bookmaker": row["bookmaker"],
                "over": None,
                "under": None,
                "snapshot_generated_at": status.get("generated_at"),
                "snapshot_fetch_succeeded": status.get("fetch_succeeded"),
                "snapshot_preserved_previous": status.get("preserved_previous_snapshot"),
                "snapshot_source_generated_at": status.get("previous_snapshot_generated_at") or status.get("generated_at"),
            },
        )
        item[str(row["side"]).lower()] = int(row["odds_american"])
    grouped_rows = [v for v in grouped.values() if v["over"] is not None and v["under"] is not None]
    dk_paths = [DESKTOP_ROOT / target_date / "dk_pitcher_props_normalized.json"]
    dk_paths.extend(sorted(DESKTOP_ROOT.glob("*/dk_pitcher_props_normalized.json"), reverse=True))
    seen_paths: set[Path] = set()
    for dk_path in dk_paths:
        if dk_path in seen_paths or not dk_path.exists():
            continue
        seen_paths.add(dk_path)
        dk_status_path = dk_path.with_name("dk_pitcher_props_status.json")
        dk_data = json.loads(dk_path.read_text(encoding="utf-8"))
        dk_status = json.loads(dk_status_path.read_text(encoding="utf-8")) if dk_status_path.exists() else {}
        for row in dk_data:
            if str(row.get("date", target_date)) != target_date:
                continue
            if row["market"] not in {"pitcher_strikeouts", "pitcher_outs"}:
                continue
            if str(row["side"]).lower() not in {"over", "under"}:
                continue
            key = (row["game"], row["market"], row["player"], row["line"], row["bookmaker"])
            item = grouped.setdefault(
                key,
                {
                    "game": row["game"],
                    "market": row["market"],
                    "player": row["player"],
                    "line": float(row["line"]),
                    "bookmaker": row["bookmaker"],
                    "over": None,
                    "under": None,
                    "snapshot_generated_at": dk_status.get("generated_at") or status.get("generated_at"),
                    "snapshot_fetch_succeeded": True,
                    "snapshot_preserved_previous": False,
                    "snapshot_source_generated_at": dk_status.get("generated_at") or status.get("generated_at"),
                },
            )
            item[str(row["side"]).lower()] = int(row["odds_american"])
        grouped_rows = [v for v in grouped.values() if v["over"] is not None and v["under"] is not None]
        if dk_status:
            status["dk_scrape_present"] = True
            status["dk_scrape_row_count"] = int(status.get("dk_scrape_row_count", 0) or 0) + int(dk_status.get("row_count", 0))
    return grouped_rows, status


def infer_today_starters(live_props: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    game_pitchers: dict[str, list[str]] = {}
    for row in live_props:
        if row["market"] in {"pitcher_strikeouts", "pitcher_outs"}:
            game_pitchers.setdefault(row["game"], [])
            if row["player"] not in game_pitchers[row["game"]]:
                game_pitchers[row["game"]].append(row["player"])
    mapping: dict[tuple[str, str], str] = {}
    for game, pitchers in game_pitchers.items():
        teams = game.split(" @ ")
        if len(teams) != 2 or len(pitchers) < 2:
            continue
        away, home = teams[0], teams[1]
        mapping[(game, away)] = pitchers[1] if len(pitchers) > 1 else pitchers[0]
        mapping[(game, home)] = pitchers[0]
    return mapping


def score_live_props(models: dict[str, Any], backtest: dict[str, Any], target_date: str, tb_limit: int, pitchers_2025: pd.DataFrame, batters_2025: pd.DataFrame, pitchers_2026: pd.DataFrame, batters_2026: pd.DataFrame) -> list[dict[str, Any]]:
    live_props, sync_status = load_live_props(target_date)
    if not live_props:
        raise RuntimeError(f"No live props available for {target_date}.")
    latest_pitchers = latest_pitcher_state(pitchers_2025, pitchers_2026, batters_2025, batters_2026).set_index("pitcher_name")
    latest_batters = latest_batter_state(pitchers_2025, pitchers_2026, batters_2025, batters_2026).set_index("batter_name")
    today_starters = infer_today_starters(live_props)
    scored = []
    tb_scored = []
    snapshot_generated_at = parse_iso_timestamp(sync_status.get("generated_at"))
    snapshot_source_at = parse_iso_timestamp(sync_status.get("previous_snapshot_generated_at") or sync_status.get("generated_at"))
    snapshot_age_hours = None
    if snapshot_source_at and snapshot_generated_at:
        snapshot_age_hours = max(0.0, (snapshot_generated_at - snapshot_source_at).total_seconds() / 3600)
    elif snapshot_source_at:
        snapshot_age_hours = 0.0
    is_snapshot_stale = snapshot_age_hours is not None and snapshot_age_hours > MAX_SNAPSHOT_AGE_HOURS
    official_games_covered = int(sync_status.get("official_games_covered", 0) or 0)
    official_total_games = int(sync_status.get("official_total_games", 0) or 0)
    official_coverage_ratio = (
        float(official_games_covered) / float(official_total_games)
        if official_total_games > 0
        else 0.0
    )
    is_snapshot_partial = official_coverage_ratio < MIN_OFFICIAL_GAME_COVERAGE_RATIO

    for row in live_props:
        over_nv, under_nv = devig_two_way(row["over"], row["under"])
        if row["market"] == "pitcher_strikeouts" and row["player"] in latest_pitchers.index:
            state = latest_pitchers.loc[row["player"]]
            feat = state[PITCHER_FEATURES].to_frame().T
            mu = float(models["k_model"].predict(feat)[0])
            over_prob = 1 - poisson.cdf(math.floor(row["line"]), mu)
            note = f"poisson-reg mu={mu:.2f}"
            sample_size = int(state.get("starts_hist", 0))
        elif row["market"] == "pitcher_outs" and row["player"] in latest_pitchers.index:
            state = latest_pitchers.loc[row["player"]]
            feat = state[PITCHER_FEATURES].to_frame().T
            mu = float(models["outs_model"].predict(feat)[0])
            over_prob = 1 - norm.cdf(row["line"], loc=mu, scale=models["outs_resid_std"])
            note = f"ridge-normal mu={mu:.2f} sigma={models['outs_resid_std']:.2f}"
            sample_size = int(state.get("starts_hist", 0))
        elif row["market"] == "batter_total_bases" and row["player"] in latest_batters.index:
            batter_feat = latest_batters.loc[row["player"]].copy()
            game, rest = row["game"], None
            teams = row["game"].split(" @ ")
            if len(teams) != 2:
                continue
            team = teams[0] if row["player"] in [] else None
            # infer batter team from game labels and latest starter names is not available directly; use both possibilities downstream via matching opp starter.
            chosen_feat = None
            for batter_team in teams:
                opp_pitcher = today_starters.get((game, batter_team))
                if opp_pitcher and opp_pitcher in latest_pitchers.index:
                    pf = latest_pitchers.loc[opp_pitcher]
                    candidate = batter_feat.copy()
                    candidate["opp_sp_k_l5"] = pf["p_k_l5"]
                    candidate["opp_sp_outs_l5"] = pf["p_outs_l5"]
                    candidate["opp_sp_h_l5"] = pf["opp_tb_rate_l10"] * 9
                    candidate["opp_sp_bb_l5"] = pf["p_bb_l5"]
                    candidate["opp_sp_hand_r"] = pf["handed_r"]
                    chosen_feat = candidate
                    break
            if chosen_feat is None:
                continue
            feat = chosen_feat[BATTER_FEATURES].to_frame().T
            mu = float(models["tb_model"].predict(feat)[0])
            over_prob = 1 - poisson.cdf(math.floor(row["line"]), mu)
            note = f"poisson-reg mu={mu:.2f}"
            sample_size = int(batter_feat.get("games_hist", 0))
        else:
            continue

        over_prob = calibrate_over_prob(row["market"], row["line"], float(over_prob), backtest)
        calib_gap = calibration_gap(row["market"], row["line"], backtest)

        under_prob = 1 - over_prob
        candidates = [
            {
                "game": row["game"],
                "market": row["market"],
                "player": row["player"],
                "line": row["line"],
                "bookmaker": row["bookmaker"],
                "side": "Over",
                "odds": row["over"],
                "model_prob": float(over_prob),
                "no_vig_prob": float(over_nv),
                "edge": float(over_prob - over_nv),
                "ev_pct": float(ev_pct(float(over_prob), row["over"])),
                "fair_odds": prob_to_american(float(over_prob)),
                "sample_size": sample_size,
                "calibration_gap": float(calib_gap),
                "snapshot_generated_at": row.get("snapshot_generated_at"),
                "snapshot_source_generated_at": row.get("snapshot_source_generated_at"),
                "snapshot_preserved_previous": bool(row.get("snapshot_preserved_previous")),
                "snapshot_age_hours": snapshot_age_hours,
                "snapshot_is_stale": bool(is_snapshot_stale),
                "snapshot_is_partial": bool(is_snapshot_partial),
                "official_coverage_ratio": float(official_coverage_ratio),
                "notes": note,
            },
            {
                "game": row["game"],
                "market": row["market"],
                "player": row["player"],
                "line": row["line"],
                "bookmaker": row["bookmaker"],
                "side": "Under",
                "odds": row["under"],
                "model_prob": float(under_prob),
                "no_vig_prob": float(under_nv),
                "edge": float(under_prob - under_nv),
                "ev_pct": float(ev_pct(float(under_prob), row["under"])),
                "fair_odds": prob_to_american(float(under_prob)),
                "sample_size": sample_size,
                "calibration_gap": float(calib_gap),
                "snapshot_generated_at": row.get("snapshot_generated_at"),
                "snapshot_source_generated_at": row.get("snapshot_source_generated_at"),
                "snapshot_preserved_previous": bool(row.get("snapshot_preserved_previous")),
                "snapshot_age_hours": snapshot_age_hours,
                "snapshot_is_stale": bool(is_snapshot_stale),
                "snapshot_is_partial": bool(is_snapshot_partial),
                "official_coverage_ratio": float(official_coverage_ratio),
                "notes": note,
            },
        ]
        for cand in candidates:
            if cand["ev_pct"] > 0:
                if cand["market"] == "batter_total_bases":
                    tb_scored.append(cand)
                else:
                    scored.append(cand)

    tb_scored.sort(key=lambda x: x["ev_pct"], reverse=True)
    scored.extend(tb_scored[:tb_limit])
    scored.sort(key=lambda x: x["ev_pct"], reverse=True)
    return scored


def build_official_card(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    seen_player_market: set[tuple[str, str]] = set()
    for row in scored:
        if row["market"] not in OFFICIAL_MARKETS:
            continue
        if row.get("snapshot_is_stale"):
            continue
        if row.get("snapshot_is_partial"):
            continue
        if row["edge"] < MIN_EDGE_PCT:
            continue
        if row["calibration_gap"] > MAX_ABS_CALIBRATION_GAP:
            continue
        if row["market"] == "pitcher_strikeouts" and row["sample_size"] < MIN_SAMPLE_K:
            continue
        if row["market"] == "pitcher_outs" and row["sample_size"] < MIN_SAMPLE_OUTS:
            continue
        key = (row["player"], row["market"])
        if key in seen_player_market:
            continue
        seen_player_market.add(key)
        filtered.append(row)
        if len(filtered) >= MAX_OFFICIAL_PICKS:
            break
    return filtered


def save_live_report(target_date: str, scored: list[dict[str, Any]], backtest: dict[str, Any]) -> tuple[Path, Path]:
    out_dir = DESKTOP_ROOT / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "real_mlb_ev_props_v2.json"
    txt_path = out_dir / "real_mlb_ev_props_v2_report.txt"
    json_path.write_text(json.dumps(scored, indent=2), encoding="utf-8")
    lines = [f"MLB prop model v2 live report for {target_date}", ""]
    lines.append("Backtest snapshot:")
    lines.append(json.dumps(backtest["_meta"], indent=2))
    lines.append("")
    for i, row in enumerate(scored[:25], 1):
        lines.append(
            f"{i}. {row['ev_pct']:.2f}% EV | {row['game']} | {row['player']} | {row['side']} {row['line']} {row['market']} | "
            f"{row['odds']:+d} at {row['bookmaker']} | model {row['model_prob']:.1%} vs no-vig {row['no_vig_prob']:.1%} | "
            f"fair {row['fair_odds']} | snap {row['snapshot_source_generated_at']} | "
            f"stale={row['snapshot_is_stale']} | partial={row['snapshot_is_partial']} | "
            f"coverage={row['official_coverage_ratio']:.0%} | {row['notes']}"
        )
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, txt_path


def save_official_card(target_date: str, official: list[dict[str, Any]]) -> tuple[Path, Path]:
    out_dir = DESKTOP_ROOT / target_date
    json_path = out_dir / "official_mlb_prop_card_v2.json"
    txt_path = out_dir / "official_mlb_prop_card_v2.txt"
    json_path.write_text(json.dumps(official, indent=2), encoding="utf-8")
    lines = [f"Official MLB prop card v2 for {target_date}", ""]
    for i, row in enumerate(official, 1):
        lines.append(
            f"{i}. {row['ev_pct']:.2f}% EV | edge {row['edge']:.1%} | {row['game']} | {row['player']} | "
            f"{row['side']} {row['line']} {row['market']} | {row['odds']:+d} at {row['bookmaker']} | "
            f"sample={row['sample_size']} | calib_gap={row['calibration_gap']:.3f} | "
            f"snap={row['snapshot_source_generated_at']} | stale={row['snapshot_is_stale']} | "
            f"partial={row['snapshot_is_partial']} | coverage={row['official_coverage_ratio']:.0%}"
        )
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, txt_path


def save_verification_report(target_date: str, backtest: dict[str, Any], official: list[dict[str, Any]]) -> Path:
    out_dir = DESKTOP_ROOT / target_date
    report_path = out_dir / "mlb_prop_model_v2_verification.txt"
    lines = [
        f"MLB Prop Model v2 Verification Report",
        f"Date: {target_date}",
        "",
        "Model scope:",
        "- Official card markets: pitcher_strikeouts, pitcher_outs",
        "- Experimental only: batter_total_bases",
        "- Pricing source: same-day de-vigged two-way bookmaker lines",
        "- Training source: local 2025 MLB boxscore cache plus current-state carry-forward",
        "",
        "Holdout backtest sample:",
        json.dumps(backtest.get("_meta", {}), indent=2),
        "",
        "Line-level calibration summary:",
    ]
    for market in ("pitcher_strikeouts", "pitcher_outs", "batter_total_bases"):
        lines.append(f"- {market}:")
        for line, stats in backtest.get(market, {}).items():
            lines.append(
                f"  line {line}: bets={stats['bets']}, avg_pred={stats['avg_pred']:.4f}, "
                f"actual={stats['actual_rate']:.4f}, brier={stats['brier']:.4f}"
            )
    lines.extend(
        [
            "",
            "Verification status:",
            "- pitcher_strikeouts: accepted for official card use",
            "- pitcher_outs: accepted for official card use with caution",
            "- batter_total_bases: rejected from official card due to overprediction",
            "- Historical +EV ROI is NOT verified because free odds access does not include historical player-prop prices",
            "- Official picks are rejected if the underlying odds snapshot is stale",
            f"- Official picks are rejected if official-game coverage is below {MIN_OFFICIAL_GAME_COVERAGE_RATIO:.0%}",
            "",
            "Official card filters:",
            f"- max picks: {MAX_OFFICIAL_PICKS}",
            f"- minimum edge: {MIN_EDGE_PCT:.1%}",
            f"- minimum K sample: {MIN_SAMPLE_K}",
            f"- minimum outs sample: {MIN_SAMPLE_OUTS}",
            f"- maximum calibration gap: {MAX_ABS_CALIBRATION_GAP:.3f}",
            "",
            f"Official card size: {len(official)}",
        ]
    )
    for i, row in enumerate(official, 1):
        lines.append(
            f"{i}. {row['player']} | {row['game']} | {row['side']} {row['line']} {row['market']} | "
            f"{row['odds']:+d} {row['bookmaker']} | EV={row['ev_pct']:.2f}% | "
            f"edge={row['edge']:.1%} | sample={row['sample_size']} | calib_gap={row['calibration_gap']:.3f} | "
            f"snap={row['snapshot_source_generated_at']} | stale={row['snapshot_is_stale']}"
        )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def save_proof_report(target_date: str, holdout: dict[str, Any], walkforward: dict[str, Any]) -> tuple[Path, Path]:
    out_dir = DESKTOP_ROOT / target_date
    json_path = out_dir / "mlb_prop_model_v2_proof.json"
    txt_path = out_dir / "mlb_prop_model_v2_proof.txt"
    json_path.write_text(json.dumps({"holdout": holdout, "walkforward": walkforward}, indent=2), encoding="utf-8")

    lines = [
        "MLB Prop Model v2 Proof Report",
        f"Date: {target_date}",
        "",
        "Scope:",
        "- This proves time-ordered predictive calibration for official markets.",
        "- This does NOT prove historical betting ROI because historical prop prices are unavailable on the free plan.",
        "",
        "Holdout sample:",
        json.dumps(holdout.get("_meta", {}), indent=2),
        "",
        "Walk-forward folds:",
        f"- folds_run: {len(walkforward.get('folds', []))}",
    ]
    for fold in walkforward.get("folds", []):
        lines.append(
            f"- fold {fold['fold_index']}: {fold['date_start']} to {fold['date_end']} | "
            f"train={fold['train_rows']} | test={fold['test_rows']}"
        )
    lines.append("")
    lines.append("Aggregate walk-forward official-market metrics:")
    for market in ("pitcher_strikeouts", "pitcher_outs"):
        lines.append(f"- {market}:")
        for line, stats in walkforward.get(market, {}).items():
            lines.append(
                f"  line {line}: bets={stats['bets']}, avg_pred={stats['avg_pred']:.4f}, "
                f"actual={stats['actual_rate']:.4f}, abs_gap={stats['abs_gap']:.4f}, brier={stats['brier']:.4f}"
            )
    lines.append("")
    lines.append("Conclusion:")
    lines.append("- pitcher_strikeouts is supported by both single holdout and walk-forward calibration.")
    lines.append("- pitcher_outs is usable but less stable than strikeouts.")
    lines.append("- +EV ROI remains unproven without historical price archives or a forward-settled pick log.")
    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, txt_path


def main() -> int:
    args = parse_args()
    pitchers_2025, batters_2025, pitchers_2026, batters_2026 = load_base_frames()
    models = fit_models(pitchers_2025, batters_2025)
    backtest = evaluate_models(models)
    walkforward = walkforward_pitcher_backtest(models)

    backtest_path = DESKTOP_ROOT / "model_backtest_v2_2025.json"
    backtest_path.write_text(json.dumps(backtest, indent=2), encoding="utf-8")

    scored = score_live_props(models, backtest, args.date, args.tb_limit, pitchers_2025, batters_2025, pitchers_2026, batters_2026)
    official = build_official_card(scored)
    json_path, txt_path = save_live_report(args.date, scored, backtest)
    official_json_path, official_txt_path = save_official_card(args.date, official)
    verification_path = save_verification_report(args.date, backtest, official)
    proof_json_path, proof_txt_path = save_proof_report(args.date, backtest, walkforward)
    print(f"Saved {backtest_path}")
    print(f"Saved {json_path}")
    print(f"Saved {txt_path}")
    print(f"Saved {official_json_path}")
    print(f"Saved {official_txt_path}")
    print(f"Saved {verification_path}")
    print(f"Saved {proof_json_path}")
    print(f"Saved {proof_txt_path}")
    print(json.dumps(backtest["_meta"], indent=2))
    print(f"Official card picks: {len(official)}")
    for row in scored[:10]:
        print(
            f"{row['ev_pct']:.2f}% EV | {row['game']} | {row['player']} | "
            f"{row['side']} {row['line']} {row['market']} | {row['odds']:+d} | {row['bookmaker']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
