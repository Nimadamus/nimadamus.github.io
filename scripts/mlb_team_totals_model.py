from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import mean_absolute_error, mean_poisson_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path.home()))
from endgame.scripts.local_game_results import load_local_results_table


ROOT = Path(r"C:\Users\Nima\endgame")
CACHE = ROOT / "cache"
DESKTOP = Path.home() / "Desktop" / "MLB_Props"
FEATURES = CACHE / "v2_team_game_features.parquet"
LIVE_FEATURE_TEMPLATE = CACHE / "live_champion_features_{date_tag}.parquet"
LIVE_MARKET_TEMPLATE = CACHE / "live_market_lines_{date_tag}.parquet"
TEAM_TOTAL_LINES = CACHE / "historical_full_game_team_total_lines.parquet"

MODEL_FEATURES = [
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
    "home_bp_fip_l30",
    "away_bp_fip_l30",
    "home_bp_k_minus_bb_pct_l30",
    "away_bp_k_minus_bb_pct_l30",
    "home_bp_k_per_9_l30",
    "away_bp_k_per_9_l30",
    "home_bp_bb_per_9_l30",
    "away_bp_bb_per_9_l30",
    "home_bp_hr_per_9_l30",
    "away_bp_hr_per_9_l30",
    "home_bp_whip_l30",
    "away_bp_whip_l30",
    "home_bp_pitches_l3d",
    "away_bp_pitches_l3d",
    "home_bp_appearances_l3d",
    "away_bp_appearances_l3d",
    "home_bp_ip_l5d",
    "away_bp_ip_l5d",
    "home_opp_bp_top3_ip_last3d",
    "away_opp_bp_top3_ip_last3d",
    "home_opp_bp_unavailable_high_leverage_count",
    "away_opp_bp_unavailable_high_leverage_count",
    "home_rest_days",
    "away_rest_days",
    "park_run_factor",
    "park_is_domed",
    "wx_temp_f",
    "wx_wind_mph",
    "wx_wind_out_component",
    "wx_humidity_pct",
    "total_line",
    "ml_home",
    "ml_away",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build/backtest MLB full-game team-total model.")
    parser.add_argument("--date", default=str(date.today()), help="Live board date in YYYY-MM-DD.")
    parser.add_argument("--min-edge", type=float, default=0.035, help="Minimum EV/edge threshold for live candidates.")
    return parser.parse_args()


def american_to_decimal(price: float) -> float:
    return 1.0 + (price / 100.0 if price > 0 else 100.0 / abs(price))


def implied_prob(price: float) -> float:
    return 1.0 / american_to_decimal(price)


def devig_two_way(price_a: float, price_b: float) -> tuple[float, float]:
    pa = implied_prob(price_a)
    pb = implied_prob(price_b)
    total = pa + pb
    return pa / total, pb / total


def prob_to_american(prob: float) -> int | None:
    if not np.isfinite(prob) or prob <= 0 or prob >= 1:
        return None
    if prob >= 0.5:
        return int(round(-(prob / (1.0 - prob)) * 100))
    return int(round(((1.0 - prob) / prob) * 100))


def poisson_side_probs(lam: float, line: float) -> tuple[float, float, float]:
    if not np.isfinite(lam) or lam <= 0 or not np.isfinite(line):
        return float("nan"), float("nan"), float("nan")
    floor_line = math.floor(line)
    p_over = float(1.0 - poisson.cdf(floor_line, lam))
    if float(line).is_integer():
        p_push = float(poisson.pmf(int(line), lam))
        p_under = float(poisson.cdf(int(line) - 1, lam))
    else:
        p_push = 0.0
        p_under = float(poisson.cdf(floor_line, lam))
    return p_over, p_under, p_push


def ev_per_unit(p_win: float, p_push: float, price: float) -> float:
    p_loss = max(0.0, 1.0 - p_win - p_push)
    return p_win * (american_to_decimal(price) - 1.0) - p_loss


def grade(side: str, line: float, runs: int, price: float) -> tuple[str, float]:
    if runs == line:
        return "PUSH", 0.0
    won = runs > line if side == "over" else runs < line
    if won:
        return "WIN", american_to_decimal(price) - 1.0
    return "LOSS", -1.0


def build_pipeline(alpha: float = 1.0) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", PoissonRegressor(alpha=alpha, max_iter=1000)),
        ]
    )


def load_training_frame() -> pd.DataFrame:
    df = pd.read_parquet(FEATURES).copy()
    df["date"] = pd.to_datetime(df["date"])
    for col in MODEL_FEATURES:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["home_runs", "away_runs"]).sort_values("date").reset_index(drop=True)


def run_predictive_backtest(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    folds: list[dict[str, Any]] = []
    preds: list[pd.DataFrame] = []
    for season in range(2017, 2026):
        train = df[df["date"].dt.year < season].copy()
        test = df[df["date"].dt.year == season].copy()
        train = train.dropna(subset=["home_runs", "away_runs"])
        test = test.dropna(subset=["home_runs", "away_runs"])
        if len(train) < 1000 or test.empty:
            continue
        home_model = build_pipeline()
        away_model = build_pipeline()
        home_model.fit(train[MODEL_FEATURES], train["home_runs"])
        away_model.fit(train[MODEL_FEATURES], train["away_runs"])
        home_pred = np.clip(home_model.predict(test[MODEL_FEATURES]), 0.1, 15)
        away_pred = np.clip(away_model.predict(test[MODEL_FEATURES]), 0.1, 15)
        folds.append(
            {
                "season": season,
                "train_rows": len(train),
                "test_rows": len(test),
                "home_mae": mean_absolute_error(test["home_runs"], home_pred),
                "away_mae": mean_absolute_error(test["away_runs"], away_pred),
                "home_poisson_deviance": mean_poisson_deviance(test["home_runs"], home_pred),
                "away_poisson_deviance": mean_poisson_deviance(test["away_runs"], away_pred),
                "actual_home_runs": float(test["home_runs"].mean()),
                "pred_home_runs": float(home_pred.mean()),
                "actual_away_runs": float(test["away_runs"].mean()),
                "pred_away_runs": float(away_pred.mean()),
            }
        )
        out = test[["game_pk", "date", "away_team_name", "home_team_name", "away_runs", "home_runs"]].copy()
        out["pred_home_runs"] = home_pred
        out["pred_away_runs"] = away_pred
        preds.append(out)
    return pd.DataFrame(folds), pd.concat(preds, ignore_index=True) if preds else pd.DataFrame()


def fit_final_models(df: pd.DataFrame) -> tuple[Pipeline, Pipeline]:
    train = df[df["date"] < pd.Timestamp("2026-01-01")].copy()
    home_model = build_pipeline()
    away_model = build_pipeline()
    home_model.fit(train[MODEL_FEATURES], train["home_runs"])
    away_model.fit(train[MODEL_FEATURES], train["away_runs"])
    return home_model, away_model


def score_post_2025_rows(df: pd.DataFrame, home_model: Pipeline, away_model: Pipeline) -> pd.DataFrame:
    post = df[(df["date"] >= pd.Timestamp("2026-01-01")) & df["home_runs"].notna() & df["away_runs"].notna()].copy()
    if post.empty:
        return pd.DataFrame()
    for col in MODEL_FEATURES:
        post[col] = pd.to_numeric(post[col], errors="coerce")
    out = post[["game_pk", "date", "away_team_name", "home_team_name", "away_runs", "home_runs"]].copy()
    out["pred_home_runs"] = np.clip(home_model.predict(post[MODEL_FEATURES]), 0.1, 15)
    out["pred_away_runs"] = np.clip(away_model.predict(post[MODEL_FEATURES]), 0.1, 15)
    return out


def score_live_snapshot_rows(home_model: Pipeline, away_model: Pipeline) -> pd.DataFrame:
    results = load_local_results_table()
    if results.empty:
        return pd.DataFrame()
    results = results.dropna(subset=["home_runs", "away_runs"])[["game_pk", "date", "home_runs", "away_runs"]].copy()
    results["date"] = pd.to_datetime(results["date"]).dt.normalize()
    frames: list[pd.DataFrame] = []
    for path in sorted(CACHE.glob("live_champion_features_*.parquet")) + sorted((ROOT / "archive" / "live_runs").glob("*/live_champion_features_*.parquet")):
        try:
            snap = pd.read_parquet(path).copy()
        except Exception:
            continue
        required = {"game_pk", "date", "away_team_name", "home_team_name"}
        if not required.issubset(set(snap.columns)):
            continue
        snap["date"] = pd.to_datetime(snap["date"]).dt.normalize()
        merged = snap.merge(results, on=["game_pk", "date"], how="inner")
        if merged.empty:
            continue
        for col in MODEL_FEATURES:
            if col not in merged.columns:
                merged[col] = np.nan
            merged[col] = pd.to_numeric(merged[col], errors="coerce")
        out = merged[["game_pk", "date", "away_team_name", "home_team_name", "away_runs", "home_runs"]].copy()
        out["pred_home_runs"] = np.clip(home_model.predict(merged[MODEL_FEATURES]), 0.1, 15)
        out["pred_away_runs"] = np.clip(away_model.predict(merged[MODEL_FEATURES]), 0.1, 15)
        frames.append(out)
    if not frames:
        return pd.DataFrame()
    return (
        pd.concat(frames, ignore_index=True)
        .sort_values(["date", "game_pk"])
        .drop_duplicates(subset=["game_pk"], keep="last")
        .reset_index(drop=True)
    )


def load_actual_price_backtest(predictions: pd.DataFrame, min_edge: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    if predictions.empty or not TEAM_TOTAL_LINES.exists():
        return pd.DataFrame(), {"status": "no_predictions_or_lines"}
    lines = pd.read_parquet(TEAM_TOTAL_LINES).copy()
    lines["date"] = pd.to_datetime(lines["date"])
    joined = predictions.merge(
        lines,
        left_on=["date", "away_team_name", "home_team_name"],
        right_on=["date", "away_name", "home_name"],
        how="inner",
    )
    picks: list[dict[str, Any]] = []
    for _, row in joined.iterrows():
        for team_side, market, line_col, over_col, under_col, pred_col, runs_col in [
            ("home", "team_total_home", "tt_home", "tt_home_over", "tt_home_under", "pred_home_runs", "home_runs"),
            ("away", "team_total_away", "tt_away", "tt_away_over", "tt_away_under", "pred_away_runs", "away_runs"),
        ]:
            line = row.get(line_col)
            over_price = row.get(over_col)
            under_price = row.get(under_col)
            lam = row.get(pred_col)
            if pd.isna(line) or pd.isna(over_price) or pd.isna(under_price) or pd.isna(lam):
                continue
            p_over, p_under, p_push = poisson_side_probs(float(lam), float(line))
            dv_over, dv_under = devig_two_way(float(over_price), float(under_price))
            for side, price, p_win, devig_prob in [
                ("over", float(over_price), p_over, dv_over),
                ("under", float(under_price), p_under, dv_under),
            ]:
                edge = p_win - devig_prob
                result, units = grade(side, float(line), int(row[runs_col]), price)
                picks.append(
                    {
                        "date": row["date"].date().isoformat(),
                        "game": f"{row['away_team_name']} @ {row['home_team_name']}",
                        "market": market,
                        "team_side": team_side,
                        "side": side,
                        "line": float(line),
                        "price": int(price),
                        "lambda": round(float(lam), 6),
                        "model_probability": round(float(p_win), 6),
                        "devig_probability": round(float(devig_prob), 6),
                        "edge": round(float(edge), 6),
                        "ev": round(float(ev_per_unit(p_win, p_push, price)), 6),
                        "team_runs": int(row[runs_col]),
                        "result": result,
                        "units_won": round(float(units), 6),
                    }
                )
    out = pd.DataFrame(picks)
    summary = summarize_roi(out)
    if not out.empty:
        qualified = out[(out["edge"].astype(float) >= min_edge) & (out["ev"].astype(float) >= min_edge)].copy()
    else:
        qualified = pd.DataFrame()
    qualified_summary = summarize_roi(qualified)
    summary.update(
        {
            "status": "actual_price_sample_limited",
            "line_rows": int(len(lines)),
            "joined_games": int(len(joined)),
            "all_priced_sides": summarize_roi(out),
            "qualified_min_edge": min_edge,
            "qualified_model_selected": qualified_summary,
            "note": "Actual DK team-total archive currently covers only a small 2026 sample; this is not promotion-grade.",
        }
    )
    if out.empty:
        return out, summary
    return out.sort_values(["date", "ev"], ascending=[True, False]).reset_index(drop=True), summary


def summarize_roi(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"picks": 0, "wins": 0, "losses": 0, "pushes": 0, "units_won": 0.0, "units_risked": 0.0, "roi": None}
    graded = df[df["result"].isin(["WIN", "LOSS"])].copy()
    units_won = float(graded["units_won"].sum()) if not graded.empty else 0.0
    units_risked = float(len(graded))
    return {
        "picks": int(len(df)),
        "wins": int((df["result"] == "WIN").sum()),
        "losses": int((df["result"] == "LOSS").sum()),
        "pushes": int((df["result"] == "PUSH").sum()),
        "units_won": round(units_won, 6),
        "units_risked": round(units_risked, 6),
        "roi": round(units_won / units_risked, 6) if units_risked else None,
    }


def load_live_board(target_date: str, home_model: Pipeline, away_model: Pipeline, min_edge: float) -> pd.DataFrame:
    date_tag = target_date.replace("-", "")
    feat_path = Path(str(LIVE_FEATURE_TEMPLATE).format(date_tag=date_tag))
    market_path = Path(str(LIVE_MARKET_TEMPLATE).format(date_tag=date_tag))
    if not feat_path.exists() or not market_path.exists():
        return pd.DataFrame()
    live = pd.read_parquet(feat_path).copy()
    markets = pd.read_parquet(market_path).copy()
    live["date"] = pd.to_datetime(live["date"]).dt.strftime("%Y-%m-%d")
    for col in MODEL_FEATURES:
        if col not in live.columns:
            live[col] = np.nan
        live[col] = pd.to_numeric(live[col], errors="coerce")
    live["pred_home_runs"] = np.clip(home_model.predict(live[MODEL_FEATURES]), 0.1, 15)
    live["pred_away_runs"] = np.clip(away_model.predict(live[MODEL_FEATURES]), 0.1, 15)
    merged = live.merge(
        markets,
        left_on=["away_team_name", "home_team_name"],
        right_on=["away_name", "home_name"],
        how="inner",
        suffixes=("", "_market"),
    )
    rows: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        for team_side, market, line_col, over_col, under_col, pred_col, team_col in [
            ("home", "team_total_home", "tt_home", "tt_home_over", "tt_home_under", "pred_home_runs", "home_team_name"),
            ("away", "team_total_away", "tt_away", "tt_away_over", "tt_away_under", "pred_away_runs", "away_team_name"),
        ]:
            line = row.get(line_col)
            over_price = row.get(over_col)
            under_price = row.get(under_col)
            lam = row.get(pred_col)
            if pd.isna(line) or pd.isna(over_price) or pd.isna(under_price) or pd.isna(lam):
                continue
            p_over, p_under, p_push = poisson_side_probs(float(lam), float(line))
            dv_over, dv_under = devig_two_way(float(over_price), float(under_price))
            for side, price, p_win, devig_prob in [
                ("over", float(over_price), p_over, dv_over),
                ("under", float(under_price), p_under, dv_under),
            ]:
                edge = p_win - devig_prob
                ev = ev_per_unit(p_win, p_push, price)
                if edge < min_edge and ev < min_edge:
                    continue
                rows.append(
                    {
                        "date": target_date,
                        "game": f"{row['away_team_name']} @ {row['home_team_name']}",
                        "team": row[team_col],
                        "market": market,
                        "team_side": team_side,
                        "side": side,
                        "line": float(line),
                        "price": int(price),
                        "lambda": round(float(lam), 6),
                        "model_probability": round(float(p_win), 6),
                        "push_probability": round(float(p_push), 6),
                        "devig_probability": round(float(devig_prob), 6),
                        "edge": round(float(edge), 6),
                        "ev": round(float(ev), 6),
                        "fair_price": prob_to_american(float(p_win)),
                        "status": "shadow_candidate_not_official",
                        "reason": "team totals are not promotion-grade until actual-price archive clears sample thresholds",
                    }
                )
    return pd.DataFrame(rows).sort_values(["ev", "edge"], ascending=False).reset_index(drop=True) if rows else pd.DataFrame()


def write_outputs(
    target_date: str,
    folds: pd.DataFrame,
    price_bt: pd.DataFrame,
    price_summary: dict[str, Any],
    live: pd.DataFrame,
) -> None:
    out_dir = DESKTOP / target_date
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_json = out_dir / "mlb_team_totals_model_proof.json"
    proof_txt = out_dir / "mlb_team_totals_model_proof.txt"
    live_csv = out_dir / "team_totals_live_shadow_candidates.csv"
    live_txt = out_dir / "team_totals_live_shadow_candidates.txt"
    price_csv = out_dir / "team_totals_actual_price_backtest_sample.csv"

    if not price_bt.empty:
        price_bt.to_csv(price_csv, index=False)
    if not live.empty:
        live.to_csv(live_csv, index=False)

    fold_summary = {
        "folds": folds.to_dict(orient="records"),
        "overall": {
            "test_rows": int(folds["test_rows"].sum()) if not folds.empty else 0,
            "avg_home_mae": round(float(np.average(folds["home_mae"], weights=folds["test_rows"])), 6) if not folds.empty else None,
            "avg_away_mae": round(float(np.average(folds["away_mae"], weights=folds["test_rows"])), 6) if not folds.empty else None,
            "avg_home_poisson_deviance": round(float(np.average(folds["home_poisson_deviance"], weights=folds["test_rows"])), 6) if not folds.empty else None,
            "avg_away_poisson_deviance": round(float(np.average(folds["away_poisson_deviance"], weights=folds["test_rows"])), 6) if not folds.empty else None,
        },
    }
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "model": "PoissonRegressor separate home/away run models",
        "predictive_backtest": fold_summary,
        "actual_price_backtest": price_summary,
        "live_shadow_candidates": live.to_dict(orient="records") if not live.empty else [],
        "verdict": "predictive model built; actual team-total price sample is too small for official/proven betting status",
    }
    proof_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("MLB Team Totals Model Proof")
    lines.append("")
    lines.append("Verdict: predictive model built; team-total betting status remains shadow-only.")
    lines.append("")
    lines.append("Predictive walk-forward backtest")
    lines.append(f"- Seasons tested: {', '.join(map(str, folds['season'].tolist())) if not folds.empty else 'none'}")
    lines.append(f"- Test games: {fold_summary['overall']['test_rows']}")
    lines.append(f"- Home run MAE: {fold_summary['overall']['avg_home_mae']}")
    lines.append(f"- Away run MAE: {fold_summary['overall']['avg_away_mae']}")
    lines.append(f"- Home Poisson deviance: {fold_summary['overall']['avg_home_poisson_deviance']}")
    lines.append(f"- Away Poisson deviance: {fold_summary['overall']['avg_away_poisson_deviance']}")
    lines.append("")
    lines.append("Actual DK team-total price backtest")
    lines.append(f"- Status: {price_summary.get('status')}")
    lines.append(f"- Historical line rows: {price_summary.get('line_rows', 0)}")
    lines.append(f"- Joined games with predictions/outcomes: {price_summary.get('joined_games', 0)}")
    lines.append(f"- Sides graded: {price_summary.get('picks', 0)}")
    lines.append(f"- Record: {price_summary.get('wins', 0)}-{price_summary.get('losses', 0)}-{price_summary.get('pushes', 0)}")
    roi = price_summary.get("roi")
    lines.append(f"- ROI on all graded sides: {'N/A' if roi is None else f'{roi * 100:+.2f}%'}")
    qualified = price_summary.get("qualified_model_selected", {})
    q_roi = qualified.get("roi")
    lines.append(
        f"- Qualified model-selected slice at min edge {price_summary.get('qualified_min_edge')}: "
        f"{qualified.get('picks', 0)} sides | "
        f"{qualified.get('wins', 0)}-{qualified.get('losses', 0)}-{qualified.get('pushes', 0)} | "
        f"ROI {'N/A' if q_roi is None else f'{q_roi * 100:+.2f}%'}"
    )
    lines.append("- This is sample-limited and not promotion-grade.")
    lines.append("")
    lines.append("Live shadow candidates")
    if live.empty:
        lines.append("- No live team-total candidates cleared the current threshold.")
    else:
        for row in live.head(20).to_dict(orient="records"):
            lines.append(
                f"- {row['game']} | {row['team']} {row['side'].upper()} {row['line']} ({row['price']}) "
                f"| lambda={row['lambda']:.3f} | model={row['model_probability']:.2%} "
                f"| market={row['devig_probability']:.2%} | edge={row['edge']:+.2%} | EV={row['ev']:+.2%} | SHADOW"
            )
    lines.append("")
    lines.append("Files")
    lines.append(f"- {proof_json}")
    lines.append(f"- {proof_txt}")
    if not live.empty:
        lines.append(f"- {live_csv}")
    if not price_bt.empty:
        lines.append(f"- {price_csv}")
    proof_txt.write_text("\n".join(lines), encoding="utf-8")
    live_txt.write_text("\n".join(lines[lines.index("Live shadow candidates") :]), encoding="utf-8")
    print(f"Wrote {proof_txt}")
    print(f"Wrote {proof_json}")
    if not live.empty:
        print(f"Wrote {live_csv}")


def main() -> int:
    args = parse_args()
    df = load_training_frame()
    folds, predictions = run_predictive_backtest(df)
    home_model, away_model = fit_final_models(df)
    post_2025_predictions = score_post_2025_rows(df, home_model, away_model)
    live_snapshot_predictions = score_live_snapshot_rows(home_model, away_model)
    price_prediction_frames = [predictions]
    if not post_2025_predictions.empty:
        price_prediction_frames.append(post_2025_predictions)
    if not live_snapshot_predictions.empty:
        price_prediction_frames.append(live_snapshot_predictions)
    price_predictions = (
        pd.concat(price_prediction_frames, ignore_index=True)
        .sort_values(["date", "game_pk"])
        .drop_duplicates(subset=["game_pk"], keep="last")
        .reset_index(drop=True)
    )
    price_bt, price_summary = load_actual_price_backtest(price_predictions, args.min_edge)
    live = load_live_board(args.date, home_model, away_model, args.min_edge)
    write_outputs(args.date, folds, price_bt, price_summary, live)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
