from __future__ import annotations

import argparse
import json
import math
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import requests
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(r"C:\Users\Nima\endgame")
CACHE = ROOT / "cache"
DESKTOP = Path.home() / "Desktop" / "MLB_Props"
V2_FEATURES = CACHE / "v2_team_game_features.parquet"
LIVE_FEATURE_TEMPLATE = CACHE / "live_champion_features_{date_tag}.parquet"
FIRST_INNING_HISTORY = CACHE / "first_inning_outcomes_history.parquet"
DK_FIRST_INNING_TEMPLATE = DESKTOP / "{date}" / "dk_first_inning_normalized.json"
BESTODDS_FIRST_INNING_TEMPLATE = DESKTOP / "{date}" / "bestodds_nrfi_yrfi_normalized.json"
BOXSCORE_DIR = CACHE / "boxscores"
MLB_API = "https://statsapi.mlb.com/api/v1"

DK_TEAM_ALIASES = {
    "ARI Diamondbacks": "Arizona Diamondbacks",
    "ATL Braves": "Atlanta Braves",
    "BAL Orioles": "Baltimore Orioles",
    "BOS Red Sox": "Boston Red Sox",
    "CHI Cubs": "Chicago Cubs",
    "CHI White Sox": "Chicago White Sox",
    "CIN Reds": "Cincinnati Reds",
    "CLE Guardians": "Cleveland Guardians",
    "COL Rockies": "Colorado Rockies",
    "DET Tigers": "Detroit Tigers",
    "HOU Astros": "Houston Astros",
    "KC Royals": "Kansas City Royals",
    "LA Angels": "Los Angeles Angels",
    "LA Dodgers": "Los Angeles Dodgers",
    "MIA Marlins": "Miami Marlins",
    "MIL Brewers": "Milwaukee Brewers",
    "MIN Twins": "Minnesota Twins",
    "NY Mets": "New York Mets",
    "NY Yankees": "New York Yankees",
    "PHI Phillies": "Philadelphia Phillies",
    "PIT Pirates": "Pittsburgh Pirates",
    "SD Padres": "San Diego Padres",
    "SEA Mariners": "Seattle Mariners",
    "SF Giants": "San Francisco Giants",
    "STL Cardinals": "St. Louis Cardinals",
    "TB Rays": "Tampa Bay Rays",
    "TEX Rangers": "Texas Rangers",
    "TOR Blue Jays": "Toronto Blue Jays",
    "WAS Nationals": "Washington Nationals",
}

TEAM_ABBR_ALIASES = {
    "ARI": "Arizona Diamondbacks",
    "AZ": "Arizona Diamondbacks",
    "ATL": "Atlanta Braves",
    "BAL": "Baltimore Orioles",
    "BOS": "Boston Red Sox",
    "CHC": "Chicago Cubs",
    "CWS": "Chicago White Sox",
    "CHW": "Chicago White Sox",
    "CIN": "Cincinnati Reds",
    "CLE": "Cleveland Guardians",
    "COL": "Colorado Rockies",
    "DET": "Detroit Tigers",
    "HOU": "Houston Astros",
    "KC": "Kansas City Royals",
    "KCR": "Kansas City Royals",
    "LAA": "Los Angeles Angels",
    "LAD": "Los Angeles Dodgers",
    "MIA": "Miami Marlins",
    "MIL": "Milwaukee Brewers",
    "MIN": "Minnesota Twins",
    "NYM": "New York Mets",
    "NYY": "New York Yankees",
    "ATH": "Athletics",
    "OAK": "Athletics",
    "PHI": "Philadelphia Phillies",
    "PIT": "Pittsburgh Pirates",
    "SD": "San Diego Padres",
    "SDP": "San Diego Padres",
    "SEA": "Seattle Mariners",
    "SF": "San Francisco Giants",
    "SFG": "San Francisco Giants",
    "STL": "St. Louis Cardinals",
    "TB": "Tampa Bay Rays",
    "TBR": "Tampa Bay Rays",
    "TEX": "Texas Rangers",
    "TOR": "Toronto Blue Jays",
    "WAS": "Washington Nationals",
    "WSH": "Washington Nationals",
}

FOLDS = [
    ("2015-01-01", "2019-12-31", "2020-01-01", "2020-12-31", "train 2015-2019 -> test 2020"),
    ("2015-01-01", "2020-12-31", "2021-01-01", "2021-12-31", "train 2015-2020 -> test 2021"),
    ("2015-01-01", "2021-12-31", "2022-01-01", "2022-12-31", "train 2015-2021 -> test 2022"),
    ("2015-01-01", "2022-12-31", "2023-01-01", "2023-12-31", "train 2015-2022 -> test 2023"),
    ("2015-01-01", "2023-12-31", "2024-01-01", "2024-12-31", "train 2015-2023 -> test 2024"),
    ("2015-01-01", "2024-12-31", "2025-01-01", "2025-12-31", "train 2015-2024 -> test 2025"),
]

MODEL_FEATURES = [
    "home_sp_fip",
    "away_sp_fip",
    "home_sp_k_minus_bb_pct",
    "away_sp_k_minus_bb_pct",
    "home_sp_k_per_9",
    "away_sp_k_per_9",
    "home_sp_bb_per_9",
    "away_sp_bb_per_9",
    "home_sp_hr_per_9",
    "away_sp_hr_per_9",
    "home_sp_whip",
    "away_sp_whip",
    "home_sp_babip",
    "away_sp_babip",
    "home_sp_days_rest",
    "away_sp_days_rest",
    "home_off_woba_vs_hand",
    "away_off_woba_vs_hand",
    "home_off_k_pct_vs_hand",
    "away_off_k_pct_vs_hand",
    "home_off_bb_pct_vs_hand",
    "away_off_bb_pct_vs_hand",
    "home_off_iso_vs_hand",
    "away_off_iso_vs_hand",
    "home_off_runs_per_pa_vs_hand",
    "away_off_runs_per_pa_vs_hand",
    "home_projected_lineup_wrc_plus_vs_hand",
    "away_projected_lineup_wrc_plus_vs_hand",
    "home_projected_lineup_k_pct_vs_hand",
    "away_projected_lineup_k_pct_vs_hand",
    "home_missing_top_bat_flag",
    "away_missing_top_bat_flag",
    "home_missing_multiple_regulars_flag",
    "away_missing_multiple_regulars_flag",
    "park_run_factor",
    "park_is_domed",
    "wx_temp_f",
    "wx_wind_mph",
    "wx_wind_out_component",
    "wx_humidity_pct",
    "home_rest_days",
    "away_rest_days",
    "ml_home",
    "ml_away",
    "total_line",
    "srbo_total",
    "srbo_over_odds",
    "srbo_under_odds",
    "run_env_market",
    "ml_abs_spread",
    "home_fi_scored_rate_l20",
    "away_fi_scored_rate_l20",
    "home_fi_scored_rate_l50",
    "away_fi_scored_rate_l50",
    "home_fi_runs_for_l20",
    "away_fi_runs_for_l20",
    "home_fi_runs_for_l50",
    "away_fi_runs_for_l50",
    "home_fi_allowed_rate_l20",
    "away_fi_allowed_rate_l20",
    "home_fi_allowed_rate_l50",
    "away_fi_allowed_rate_l50",
    "home_fi_runs_allowed_l20",
    "away_fi_runs_allowed_l20",
    "home_fi_runs_allowed_l50",
    "away_fi_runs_allowed_l50",
    "home_sp_fi_allowed_rate_l10",
    "away_sp_fi_allowed_rate_l10",
    "home_sp_fi_runs_allowed_l10",
    "away_sp_fi_runs_allowed_l10",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest and score MLB first-inning runs / NRFI-YRFI model.")
    parser.add_argument("--date", default=str(date.today()), help="Reference date in YYYY-MM-DD.")
    parser.add_argument("--refresh-history", action="store_true", help="Refresh first-inning historical outcomes from MLB Stats API.")
    parser.add_argument("--history-start", default="2015-03-15")
    parser.add_argument("--history-end", default="2025-11-15")
    return parser.parse_args()


def _season_chunks(start_year: int, end_year: int) -> list[tuple[str, str]]:
    return [(f"{year}-03-15", f"{year}-11-15") for year in range(start_year, end_year + 1)]


def fetch_first_inning_history(start_date: str, end_date: str) -> pd.DataFrame:
    start_year = int(start_date[:4])
    end_year = int(end_date[:4])
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    rows: list[dict] = []
    for chunk_start, chunk_end in _season_chunks(start_year, end_year):
        response = session.get(
            f"{MLB_API}/schedule",
            params={"sportId": 1, "startDate": chunk_start, "endDate": chunk_end, "gameType": "R", "hydrate": "linescore"},
            timeout=60,
        )
        response.raise_for_status()
        for date_block in response.json().get("dates", []):
            for game in date_block.get("games", []):
                linescore = game.get("linescore", {}) or {}
                innings = linescore.get("innings", []) or []
                if len(innings) < 1:
                    continue
                first = innings[0]
                home_runs = (first.get("home") or {}).get("runs")
                away_runs = (first.get("away") or {}).get("runs")
                if home_runs is None or away_runs is None:
                    continue
                official_date = game.get("officialDate") or game.get("gameDate", "")[:10]
                rows.append(
                    {
                        "game_pk": int(game["gamePk"]),
                        "date": pd.to_datetime(official_date),
                        "season": int(official_date[:4]),
                        "home_first_inning_runs": int(home_runs),
                        "away_first_inning_runs": int(away_runs),
                        "first_inning_total_runs": int(home_runs) + int(away_runs),
                        "yrfi": int(home_runs + away_runs > 0),
                        "nrfi": int(home_runs + away_runs == 0),
                    }
                )
    history = pd.DataFrame(rows).drop_duplicates(subset=["game_pk"], keep="last").sort_values("date").reset_index(drop=True)
    FIRST_INNING_HISTORY.write_bytes(b"")
    history.to_parquet(FIRST_INNING_HISTORY, index=False)
    return history


def load_history(refresh: bool, start_date: str, end_date: str) -> pd.DataFrame:
    if refresh or not FIRST_INNING_HISTORY.exists():
        return fetch_first_inning_history(start_date, end_date)
    history = pd.read_parquet(FIRST_INNING_HISTORY)
    history["date"] = pd.to_datetime(history["date"])
    return history


def load_training_frame(history: pd.DataFrame) -> pd.DataFrame:
    features = pd.read_parquet(V2_FEATURES).copy()
    features["date"] = pd.to_datetime(features["date"])
    history = history.copy()
    history["date"] = pd.to_datetime(history["date"])
    merged = features.merge(
        history[["game_pk", "date", "first_inning_total_runs", "yrfi", "nrfi"]],
        on=["game_pk", "date"],
        how="inner",
    )
    merged = merged.dropna(subset=["yrfi"]).sort_values("date").reset_index(drop=True)
    merged = add_market_context_features(merged)
    return add_first_inning_priors(merged, history)


def _as_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("", pd.NA), errors="coerce")


def add_market_context_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    if "home_ml_price" in out.columns and "ml_home" not in out.columns:
        out["ml_home"] = _as_numeric(out["home_ml_price"])
    if "away_ml_price" in out.columns and "ml_away" not in out.columns:
        out["ml_away"] = _as_numeric(out["away_ml_price"])
    for col in ("ml_home", "ml_away", "total_line", "srbo_total", "srbo_over_odds", "srbo_under_odds"):
        if col in out.columns:
            out[col] = _as_numeric(out[col])
    available_totals = [col for col in ("total_line", "srbo_total") if col in out.columns]
    if available_totals:
        out["run_env_market"] = out[available_totals].mean(axis=1)
    if "ml_home" in out.columns and "ml_away" in out.columns:
        out["ml_abs_spread"] = (out["ml_home"] - out["ml_away"]).abs()
    return out


def load_starters() -> pd.DataFrame:
    frames = []
    for path in sorted(BOXSCORE_DIR.glob("pitchers_*.parquet")):
        df = pd.read_parquet(path)
        if df.empty:
            continue
        frames.append(df[df["is_starter"]].copy())
    if not frames:
        return pd.DataFrame()
    starters = pd.concat(frames, ignore_index=True)
    starters["date"] = pd.to_datetime(starters["date"])
    return starters[
        ["game_pk", "date", "team_id", "is_home", "pitcher_id", "pitcher_name"]
    ].drop_duplicates(subset=["game_pk", "team_id", "is_home"], keep="last")


def _rolling_shifted_mean(group: pd.Series, window: int) -> pd.Series:
    return group.shift(1).rolling(window, min_periods=5).mean()


def build_team_first_inning_priors(history: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    base = games[["game_pk", "date", "home_team_id", "away_team_id"]].merge(
        history[
            [
                "game_pk",
                "home_first_inning_runs",
                "away_first_inning_runs",
            ]
        ],
        on="game_pk",
        how="inner",
    )
    home = pd.DataFrame(
        {
            "game_pk": base["game_pk"],
            "date": base["date"],
            "team_id": base["home_team_id"],
            "is_home": True,
            "fi_runs_for": base["home_first_inning_runs"],
            "fi_runs_allowed": base["away_first_inning_runs"],
        }
    )
    away = pd.DataFrame(
        {
            "game_pk": base["game_pk"],
            "date": base["date"],
            "team_id": base["away_team_id"],
            "is_home": False,
            "fi_runs_for": base["away_first_inning_runs"],
            "fi_runs_allowed": base["home_first_inning_runs"],
        }
    )
    team = pd.concat([home, away], ignore_index=True).sort_values(["team_id", "date", "game_pk"]).reset_index(drop=True)
    team["fi_scored"] = (team["fi_runs_for"] > 0).astype(float)
    team["fi_allowed"] = (team["fi_runs_allowed"] > 0).astype(float)
    for window in (20, 50):
        team[f"fi_scored_rate_l{window}"] = team.groupby("team_id")["fi_scored"].transform(lambda s: _rolling_shifted_mean(s, window))
        team[f"fi_allowed_rate_l{window}"] = team.groupby("team_id")["fi_allowed"].transform(lambda s: _rolling_shifted_mean(s, window))
        team[f"fi_runs_for_l{window}"] = team.groupby("team_id")["fi_runs_for"].transform(lambda s: _rolling_shifted_mean(s, window))
        team[f"fi_runs_allowed_l{window}"] = team.groupby("team_id")["fi_runs_allowed"].transform(lambda s: _rolling_shifted_mean(s, window))
    return team


def build_starter_first_inning_priors(history: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    starters = load_starters()
    if starters.empty:
        return pd.DataFrame()
    base = games[["game_pk", "date", "home_team_id", "away_team_id"]].merge(
        history[
            [
                "game_pk",
                "home_first_inning_runs",
                "away_first_inning_runs",
            ]
        ],
        on="game_pk",
        how="inner",
    )
    starter_games = starters.merge(base, on=["game_pk", "date"], how="inner")
    starter_games["sp_fi_runs_allowed"] = starter_games.apply(
        lambda row: row["away_first_inning_runs"] if bool(row["is_home"]) else row["home_first_inning_runs"],
        axis=1,
    )
    starter_games["sp_fi_allowed"] = (starter_games["sp_fi_runs_allowed"] > 0).astype(float)
    starter_games = starter_games.sort_values(["pitcher_id", "date", "game_pk"]).reset_index(drop=True)
    starter_games["sp_fi_allowed_rate_l10"] = starter_games.groupby("pitcher_id")["sp_fi_allowed"].transform(lambda s: _rolling_shifted_mean(s, 10))
    starter_games["sp_fi_runs_allowed_l10"] = starter_games.groupby("pitcher_id")["sp_fi_runs_allowed"].transform(lambda s: _rolling_shifted_mean(s, 10))
    return starter_games[
        [
            "game_pk",
            "team_id",
            "is_home",
            "pitcher_id",
            "sp_fi_allowed_rate_l10",
            "sp_fi_runs_allowed_l10",
        ]
    ]


def add_first_inning_priors(frame: pd.DataFrame, history: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    team_priors = build_team_first_inning_priors(history, out)
    home_team = team_priors[team_priors["is_home"]].rename(
        columns={
            "fi_scored_rate_l20": "home_fi_scored_rate_l20",
            "fi_scored_rate_l50": "home_fi_scored_rate_l50",
            "fi_runs_for_l20": "home_fi_runs_for_l20",
            "fi_runs_for_l50": "home_fi_runs_for_l50",
            "fi_allowed_rate_l20": "home_fi_allowed_rate_l20",
            "fi_allowed_rate_l50": "home_fi_allowed_rate_l50",
            "fi_runs_allowed_l20": "home_fi_runs_allowed_l20",
            "fi_runs_allowed_l50": "home_fi_runs_allowed_l50",
        }
    )
    away_team = team_priors[~team_priors["is_home"]].rename(
        columns={
            "fi_scored_rate_l20": "away_fi_scored_rate_l20",
            "fi_scored_rate_l50": "away_fi_scored_rate_l50",
            "fi_runs_for_l20": "away_fi_runs_for_l20",
            "fi_runs_for_l50": "away_fi_runs_for_l50",
            "fi_allowed_rate_l20": "away_fi_allowed_rate_l20",
            "fi_allowed_rate_l50": "away_fi_allowed_rate_l50",
            "fi_runs_allowed_l20": "away_fi_runs_allowed_l20",
            "fi_runs_allowed_l50": "away_fi_runs_allowed_l50",
        }
    )
    out = out.merge(
        home_team[
            [
                "game_pk",
                "home_fi_scored_rate_l20",
                "home_fi_scored_rate_l50",
                "home_fi_runs_for_l20",
                "home_fi_runs_for_l50",
                "home_fi_allowed_rate_l20",
                "home_fi_allowed_rate_l50",
                "home_fi_runs_allowed_l20",
                "home_fi_runs_allowed_l50",
            ]
        ],
        on="game_pk",
        how="left",
    )
    out = out.merge(
        away_team[
            [
                "game_pk",
                "away_fi_scored_rate_l20",
                "away_fi_scored_rate_l50",
                "away_fi_runs_for_l20",
                "away_fi_runs_for_l50",
                "away_fi_allowed_rate_l20",
                "away_fi_allowed_rate_l50",
                "away_fi_runs_allowed_l20",
                "away_fi_runs_allowed_l50",
            ]
        ],
        on="game_pk",
        how="left",
    )
    starter_priors = build_starter_first_inning_priors(history, out)
    if not starter_priors.empty:
        home_sp = starter_priors[starter_priors["is_home"]].rename(
            columns={
                "sp_fi_allowed_rate_l10": "home_sp_fi_allowed_rate_l10",
                "sp_fi_runs_allowed_l10": "home_sp_fi_runs_allowed_l10",
            }
        )
        away_sp = starter_priors[~starter_priors["is_home"]].rename(
            columns={
                "sp_fi_allowed_rate_l10": "away_sp_fi_allowed_rate_l10",
                "sp_fi_runs_allowed_l10": "away_sp_fi_runs_allowed_l10",
            }
        )
        out = out.merge(
            home_sp[["game_pk", "home_sp_fi_allowed_rate_l10", "home_sp_fi_runs_allowed_l10"]],
            on="game_pk",
            how="left",
        )
        out = out.merge(
            away_sp[["game_pk", "away_sp_fi_allowed_rate_l10", "away_sp_fi_runs_allowed_l10"]],
            on="game_pk",
            how="left",
        )
    return out


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=3000, C=0.01)),
        ]
    )


def select_model_features(frame: pd.DataFrame) -> list[str]:
    # Candidate sweep showed first-inning rolling priors were noisy; keep validated base + market-context features.
    return [col for col in MODEL_FEATURES if col in frame.columns and "_fi_" not in col]


def brier_score(pred: pd.Series, actual: pd.Series) -> float:
    return float(((pred - actual) ** 2).mean())


def log_loss(pred: pd.Series, actual: pd.Series) -> float:
    clipped = pred.clip(1e-6, 1 - 1e-6)
    return float((-(actual * clipped.map(math.log) + (1 - actual) * (1 - clipped).map(math.log))).mean())


def expected_calibration_error(pred: pd.Series, actual: pd.Series, bins: int = 10) -> float:
    frame = pd.DataFrame({"pred": pred, "actual": actual}).dropna()
    if frame.empty:
        return float("nan")
    frame["bin"] = pd.cut(frame["pred"], bins=bins, labels=False, include_lowest=True)
    total = 0.0
    for _, bucket in frame.groupby("bin"):
        total += (len(bucket) / len(frame)) * abs(bucket["pred"].mean() - bucket["actual"].mean())
    return float(total)


def run_walk_forward_backtest(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    fold_rows: list[dict] = []
    all_preds: list[pd.DataFrame] = []
    available_features = select_model_features(frame)
    for train_start, train_end, test_start, test_end, label in FOLDS:
        train = frame[(frame["date"] >= train_start) & (frame["date"] <= train_end)].copy()
        test = frame[(frame["date"] >= test_start) & (frame["date"] <= test_end)].copy()
        if train.empty or test.empty:
            continue
        model = build_pipeline()
        model.fit(train[available_features], train["yrfi"])
        preds = pd.Series(model.predict_proba(test[available_features])[:, 1], index=test.index)
        test_out = test[["game_pk", "date", "yrfi", "nrfi", "first_inning_total_runs"]].copy()
        test_out["pred_yrfi"] = preds
        test_out["pred_nrfi"] = 1.0 - preds
        test_out["fold"] = label
        all_preds.append(test_out)
        fold_rows.append(
            {
                "fold": label,
                "test_season": int(test_start[:4]),
                "n_train": len(train),
                "n_test": len(test),
                "avg_pred_yrfi": round(float(preds.mean()), 6),
                "actual_yrfi": round(float(test["yrfi"].mean()), 6),
                "abs_gap": round(abs(float(preds.mean()) - float(test["yrfi"].mean())), 6),
                "brier": round(brier_score(preds, test["yrfi"]), 6),
                "log_loss": round(log_loss(preds, test["yrfi"]), 6),
                "ece": round(expected_calibration_error(preds, test["yrfi"]), 6),
            }
        )
    predictions = pd.concat(all_preds, ignore_index=True) if all_preds else pd.DataFrame()
    fold_df = pd.DataFrame(fold_rows)
    return fold_df, predictions


def summarize_predictions(predictions: pd.DataFrame) -> dict[str, float]:
    if predictions.empty:
        return {}
    yrfi_pred = predictions["pred_yrfi"]
    actual = predictions["yrfi"]
    baseline = float(actual.mean())
    baseline_brier = float(((actual - baseline) ** 2).mean())
    model_brier = brier_score(yrfi_pred, actual)
    return {
        "n_games": int(len(predictions)),
        "avg_pred_yrfi": round(float(yrfi_pred.mean()), 6),
        "actual_yrfi": round(float(actual.mean()), 6),
        "abs_gap": round(abs(float(yrfi_pred.mean()) - float(actual.mean())), 6),
        "brier": round(model_brier, 6),
        "baseline_brier": round(baseline_brier, 6),
        "brier_improvement": round(baseline_brier - model_brier, 6),
        "log_loss": round(log_loss(yrfi_pred, actual), 6),
        "ece": round(expected_calibration_error(yrfi_pred, actual), 6),
        "auc": round(float(roc_auc_score(actual, yrfi_pred)), 6),
    }


def summarize_confidence_slices(predictions: pd.DataFrame) -> list[dict[str, float]]:
    if predictions.empty:
        return []
    frame = predictions.copy()
    frame["confidence"] = (frame["pred_yrfi"] - 0.5).abs()
    frame["side_prob"] = frame["pred_yrfi"].where(frame["pred_yrfi"] >= 0.5, 1.0 - frame["pred_yrfi"])
    frame["win_if_model_side"] = ((frame["pred_yrfi"] >= 0.5) & (frame["yrfi"] == 1)) | ((frame["pred_yrfi"] < 0.5) & (frame["yrfi"] == 0))
    rows: list[dict[str, float]] = []
    for quantile in (0.5, 0.7, 0.8, 0.9, 0.95, 0.975):
        threshold = float(frame["confidence"].quantile(quantile))
        sliced = frame[frame["confidence"] >= threshold].copy()
        if sliced.empty:
            continue
        win_rate = float(sliced["win_if_model_side"].mean())
        flat_110_roi = win_rate * (100.0 / 110.0) - (1.0 - win_rate)
        rows.append(
            {
                "confidence_quantile": quantile,
                "n": int(len(sliced)),
                "avg_model_side_prob": round(float(sliced["side_prob"].mean()), 6),
                "actual_model_side_win_rate": round(win_rate, 6),
                "flat_minus_110_roi": round(flat_110_roi, 6),
            }
        )
    return rows


def american_to_decimal(odds: int) -> float:
    return (odds / 100.0 + 1.0) if odds > 0 else (100.0 / abs(odds) + 1.0)


def canonical_board_game(game: str) -> str:
    if " @ " not in str(game):
        return str(game)
    away, home = str(game).split(" @ ", 1)
    away_name = TEAM_ABBR_ALIASES.get(away, DK_TEAM_ALIASES.get(away, away))
    home_name = TEAM_ABBR_ALIASES.get(home, DK_TEAM_ALIASES.get(home, home))
    return f"{away_name} @ {home_name}"


def expected_value(prob: float, odds: int) -> float:
    return prob * (american_to_decimal(odds) - 1.0) - (1.0 - prob)


def add_live_first_inning_priors(live: pd.DataFrame, history: pd.DataFrame, target_date: str) -> pd.DataFrame:
    if live.empty:
        return live
    historical_games = pd.read_parquet(V2_FEATURES).copy()
    historical_games["date"] = pd.to_datetime(historical_games["date"])
    target_ts = pd.to_datetime(target_date)
    historical_games = historical_games[historical_games["date"] < target_ts].copy()
    if historical_games.empty:
        return live

    history = history.copy()
    history["date"] = pd.to_datetime(history["date"])
    history = history[history["date"] < target_ts].copy()
    if history.empty:
        return live

    team_priors = build_team_first_inning_priors(history, historical_games)
    latest_team = team_priors.sort_values(["team_id", "date", "game_pk"]).groupby("team_id").tail(1)
    latest_team = latest_team[
        [
            "team_id",
            "fi_scored_rate_l20",
            "fi_scored_rate_l50",
            "fi_runs_for_l20",
            "fi_runs_for_l50",
            "fi_allowed_rate_l20",
            "fi_allowed_rate_l50",
            "fi_runs_allowed_l20",
            "fi_runs_allowed_l50",
        ]
    ]
    home_team = latest_team.rename(
        columns={
            "team_id": "home_team_id",
            "fi_scored_rate_l20": "home_fi_scored_rate_l20",
            "fi_scored_rate_l50": "home_fi_scored_rate_l50",
            "fi_runs_for_l20": "home_fi_runs_for_l20",
            "fi_runs_for_l50": "home_fi_runs_for_l50",
            "fi_allowed_rate_l20": "home_fi_allowed_rate_l20",
            "fi_allowed_rate_l50": "home_fi_allowed_rate_l50",
            "fi_runs_allowed_l20": "home_fi_runs_allowed_l20",
            "fi_runs_allowed_l50": "home_fi_runs_allowed_l50",
        }
    )
    away_team = latest_team.rename(
        columns={
            "team_id": "away_team_id",
            "fi_scored_rate_l20": "away_fi_scored_rate_l20",
            "fi_scored_rate_l50": "away_fi_scored_rate_l50",
            "fi_runs_for_l20": "away_fi_runs_for_l20",
            "fi_runs_for_l50": "away_fi_runs_for_l50",
            "fi_allowed_rate_l20": "away_fi_allowed_rate_l20",
            "fi_allowed_rate_l50": "away_fi_allowed_rate_l50",
            "fi_runs_allowed_l20": "away_fi_runs_allowed_l20",
            "fi_runs_allowed_l50": "away_fi_runs_allowed_l50",
        }
    )
    out = live.merge(home_team, on="home_team_id", how="left").merge(away_team, on="away_team_id", how="left")

    starter_priors = build_starter_first_inning_priors(history, historical_games)
    if starter_priors.empty:
        return out
    latest_sp = starter_priors.sort_values(["pitcher_id", "game_pk"]).groupby("pitcher_id").tail(1)
    latest_sp = latest_sp[["pitcher_id", "sp_fi_allowed_rate_l10", "sp_fi_runs_allowed_l10"]]
    home_sp = latest_sp.rename(
        columns={
            "pitcher_id": "home_sp_id",
            "sp_fi_allowed_rate_l10": "home_sp_fi_allowed_rate_l10",
            "sp_fi_runs_allowed_l10": "home_sp_fi_runs_allowed_l10",
        }
    )
    away_sp = latest_sp.rename(
        columns={
            "pitcher_id": "away_sp_id",
            "sp_fi_allowed_rate_l10": "away_sp_fi_allowed_rate_l10",
            "sp_fi_runs_allowed_l10": "away_sp_fi_runs_allowed_l10",
        }
    )
    return out.merge(home_sp, on="home_sp_id", how="left").merge(away_sp, on="away_sp_id", how="left")


def load_live_features(target_date: str, history: pd.DataFrame) -> pd.DataFrame:
    path = Path(str(LIVE_FEATURE_TEMPLATE).format(date_tag=target_date.replace("-", "")))
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path).copy()
    df["date"] = pd.to_datetime(df["date"])
    df["game"] = df["away_team_name"].astype(str) + " @ " + df["home_team_name"].astype(str)
    df = add_market_context_features(df)
    return add_live_first_inning_priors(df, history, target_date)


def score_live_board(target_date: str, model: Pipeline, available_features: list[str], history: pd.DataFrame) -> pd.DataFrame:
    board = load_dk_first_inning_board(target_date)
    if board.empty:
        return pd.DataFrame()
    live = load_live_features(target_date, history)
    if live.empty:
        return pd.DataFrame()
    board = board[board["market"].isin(["yrfi", "nrfi"])].copy()
    for feature in available_features:
        if feature not in live.columns:
            live[feature] = float("nan")
    merged = board.merge(live[["game"] + available_features], on="game", how="left")
    merged = merged.dropna(subset=available_features, how="all").reset_index(drop=True)
    if merged.empty:
        return merged
    for feature in available_features:
        merged[feature] = pd.to_numeric(merged[feature], errors="coerce")
    merged["pred_yrfi"] = model.predict_proba(merged[available_features])[:, 1]
    merged["pred_nrfi"] = 1.0 - merged["pred_yrfi"]
    merged["model_prob"] = merged.apply(lambda row: row["pred_yrfi"] if row["market"] == "yrfi" else row["pred_nrfi"], axis=1)
    merged["implied_prob"] = merged["odds_american"].astype(int).map(lambda x: 1.0 / american_to_decimal(int(x)))
    merged["edge"] = merged["model_prob"] - merged["implied_prob"]
    merged["ev"] = merged.apply(lambda row: expected_value(float(row["model_prob"]), int(row["odds_american"])), axis=1)
    return merged.sort_values(["ev", "edge"], ascending=False).reset_index(drop=True)


def load_dk_first_inning_board(target_date: str) -> pd.DataFrame:
    candidate_paths = [
        Path(str(BESTODDS_FIRST_INNING_TEMPLATE).format(date=target_date)),
        Path(str(DK_FIRST_INNING_TEMPLATE).format(date=target_date)),
        *sorted(DESKTOP.glob("*/bestodds_nrfi_yrfi_normalized.json"), reverse=True),
        *sorted(DESKTOP.glob("*/dk_first_inning_normalized.json"), reverse=True),
    ]
    frames: list[pd.DataFrame] = []
    seen: set[Path] = set()
    for path in candidate_paths:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not rows:
            continue
        frame = pd.DataFrame(rows)
        if "date" not in frame.columns:
            continue
        frame = frame[frame["date"].astype(str) == target_date].copy()
        if not frame.empty:
            frame["board_file"] = str(path)
            frames.append(frame)
    if not frames:
        return pd.DataFrame()
    board = pd.concat(frames, ignore_index=True)
    board["game"] = board["game"].map(canonical_board_game)
    return board.drop_duplicates(subset=["date", "game", "market", "side", "line", "odds_american"], keep="first")


def write_outputs(target_date: str, history: pd.DataFrame, training_frame: pd.DataFrame, fold_df: pd.DataFrame, summary: dict[str, float], confidence_slices: list[dict[str, float]], live_board: pd.DataFrame) -> None:
    out_dir = DESKTOP / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_json = out_dir / "mlb_first_inning_model_proof.json"
    proof_txt = out_dir / "mlb_first_inning_model_proof.txt"
    live_json = out_dir / "first_inning_live_board.json"
    live_txt = out_dir / "first_inning_live_board.txt"

    proof_payload = {
        "generated_at": datetime.now().isoformat(),
        "history_rows": int(len(history)),
        "training_rows": int(len(training_frame)),
        "model_spec": "LogisticRegression(C=0.01) on base starter/offense/park/weather plus full-game market context.",
        "candidate_sweep_note": "Full-game market context materially improved walk-forward AUC/Brier. First-inning rolling team/starter priors were tested but excluded because they reduced walk-forward Brier/AUC.",
        "features_used": select_model_features(training_frame),
        "folds": fold_df.to_dict(orient="records"),
        "overall": summary,
        "confidence_slices": confidence_slices,
    }
    proof_json.write_text(json.dumps(proof_payload, indent=2), encoding="utf-8")

    proof_lines = [
        "MLB First Inning Model Proof",
        "",
        f"Generated: {datetime.now().isoformat()}",
        f"Historical outcome rows: {len(history)}",
        f"Training rows joined to features: {len(training_frame)}",
        "",
        "Overall walk-forward summary:",
    ]
    for key, value in summary.items():
        proof_lines.append(f"- {key}: {value}")
    proof_lines.extend(["", "Per-fold results:"])
    for row in fold_df.to_dict(orient="records"):
        proof_lines.append(
            f"- {row['fold']} | n_test={row['n_test']} | avg_pred_yrfi={row['avg_pred_yrfi']} | actual_yrfi={row['actual_yrfi']} | abs_gap={row['abs_gap']} | brier={row['brier']} | ece={row['ece']}"
        )
    proof_lines.extend(["", "Confidence slices using model side; flat -110 ROI is a stress-test proxy, not historical price proof:"])
    for row in confidence_slices:
        proof_lines.append(
            f"- q>={row['confidence_quantile']} | n={row['n']} | avg_side_prob={row['avg_model_side_prob']} | actual_win={row['actual_model_side_win_rate']} | flat_-110_roi={row['flat_minus_110_roi']:+.4f}"
        )
    proof_txt.write_text("\n".join(proof_lines), encoding="utf-8")

    if live_board.empty:
        live_payload = {"generated_at": datetime.now().isoformat(), "rows": [], "note": "No matching live features or board rows for this date."}
        live_json.write_text(json.dumps(live_payload, indent=2), encoding="utf-8")
        live_txt.write_text("No matching live features or board rows for this date.\n", encoding="utf-8")
        return

    display_columns = [
        "date",
        "game",
        "bookmaker",
        "market",
        "side",
        "line",
        "odds_american",
        "model_prob",
        "implied_prob",
        "edge",
        "ev",
        "board_file",
    ]
    live_rows = live_board[[column for column in display_columns if column in live_board.columns]].copy()
    live_json.write_text(json.dumps({"generated_at": datetime.now().isoformat(), "rows": live_rows.to_dict(orient="records")}, indent=2), encoding="utf-8")
    live_lines = ["MLB First Inning Live Board", ""]
    for row in live_rows.head(20).to_dict(orient="records"):
        book = f" | {row['bookmaker']}" if row.get("bookmaker") else ""
        live_lines.append(
            f"- {row['game']}{book} | {row['market'].upper()} | {row['odds_american']} | model={row['model_prob']:.4f} | implied={row['implied_prob']:.4f} | edge={row['edge']:+.4f} | ev={row['ev']:+.4f}"
        )
    live_txt.write_text("\n".join(live_lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    history = load_history(args.refresh_history, args.history_start, args.history_end)
    training_frame = load_training_frame(history)
    available_features = select_model_features(training_frame)
    fold_df, predictions = run_walk_forward_backtest(training_frame)
    summary = summarize_predictions(predictions)
    confidence_slices = summarize_confidence_slices(predictions)
    model = build_pipeline()
    model.fit(training_frame[available_features], training_frame["yrfi"])
    live_board = score_live_board(args.date, model, available_features, history)
    write_outputs(args.date, history, training_frame, fold_df, summary, confidence_slices, live_board)
    print(f"Wrote first-inning proof and live outputs to {DESKTOP / args.date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
