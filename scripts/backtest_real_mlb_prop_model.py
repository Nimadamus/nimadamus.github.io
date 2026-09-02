from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean

import pandas as pd


BOX_ROOT = Path.home() / "endgame" / "cache" / "boxscores"


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


def total_bases(df: pd.DataFrame) -> pd.Series:
    singles = df["h"] - df["d"] - df["t"] - df["hr"]
    return singles + 2 * df["d"] + 3 * df["t"] + 4 * df["hr"]


def model_probability(values: list[float], line: float, market: str) -> float:
    recent = values[-10:]
    avg_recent = mean(recent)
    avg_full = mean(values)
    mu = avg_full * 0.6 + avg_recent * 0.4
    if market == "pitcher_strikeouts":
        return max(0.01, min(0.99, poisson_tail(max(0.1, mu), line)))
    sigma = max(1.5 if market == "pitcher_outs" else 0.75, (sum((x - avg_full) ** 2 for x in values) / max(1, len(values) - 1)) ** 0.5)
    return max(0.01, min(0.99, 1 - normal_cdf(line, mu, sigma)))


def run_pitcher_backtest(df: pd.DataFrame, market: str, lines: list[float], min_history: int) -> list[dict]:
    rows = []
    value_col = "k" if market == "pitcher_strikeouts" else "outs_recorded"
    if market == "pitcher_outs":
        df = df[df["is_starter"] == True].copy()
    grouped = df.sort_values("date").groupby("pitcher_name")
    for pitcher, group in grouped:
        vals = group[value_col].astype(float).tolist()
        dates = group["date"].tolist()
        for idx in range(min_history, len(vals)):
            hist = vals[:idx]
            actual = vals[idx]
            for line in lines:
                pred = model_probability(hist, line, market)
                outcome = 1.0 if actual > line else 0.0 if actual < line else None
                if outcome is None:
                    continue
                rows.append({"market": market, "line": line, "date": dates[idx], "player": pitcher, "pred": pred, "outcome": outcome})
    return rows


def run_batter_backtest(df: pd.DataFrame, lines: list[float], min_history: int) -> list[dict]:
    rows = []
    df = df[df["is_starter"] == True].copy()
    df["tb"] = total_bases(df)
    grouped = df.sort_values("date").groupby("batter_name")
    for batter, group in grouped:
        vals = group["tb"].astype(float).tolist()
        dates = group["date"].tolist()
        for idx in range(min_history, len(vals)):
            hist = vals[:idx]
            actual = vals[idx]
            for line in lines:
                pred = model_probability(hist, line, "batter_total_bases")
                outcome = 1.0 if actual > line else 0.0 if actual < line else None
                if outcome is None:
                    continue
                rows.append({"market": "batter_total_bases", "line": line, "date": dates[idx], "player": batter, "pred": pred, "outcome": outcome})
    return rows


def summarize(rows: list[dict]) -> dict:
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    df["brier"] = (df["pred"] - df["outcome"]) ** 2
    out = {}
    for (market, line), sub in df.groupby(["market", "line"]):
        out[f"{market}_{line}"] = {
            "bets": int(len(sub)),
            "avg_pred": round(float(sub["pred"].mean()), 4),
            "actual_rate": round(float(sub["outcome"].mean()), 4),
            "brier": round(float(sub["brier"].mean()), 4),
        }
    overall = df.groupby("market").agg(bets=("pred", "size"), avg_pred=("pred", "mean"), actual_rate=("outcome", "mean"), brier=("brier", "mean")).reset_index()
    out["_overall"] = overall.to_dict(orient="records")
    return out


def main() -> int:
    pitchers_2025 = pd.read_parquet(BOX_ROOT / "pitchers_2025.parquet")
    batters_2025 = pd.read_parquet(BOX_ROOT / "batters_2025.parquet")

    ks_rows = run_pitcher_backtest(pitchers_2025[pitchers_2025["is_starter"] == True].copy(), "pitcher_strikeouts", [3.5, 4.5, 5.5, 6.5, 7.5], 8)
    outs_rows = run_pitcher_backtest(pitchers_2025[pitchers_2025["is_starter"] == True].copy(), "pitcher_outs", [14.5, 15.5, 16.5, 17.5, 18.5], 8)
    tb_rows = run_batter_backtest(batters_2025, [0.5, 1.5], 20)

    summary = summarize(ks_rows + outs_rows + tb_rows)
    out_path = Path.home() / "Desktop" / "MLB_Props" / "model_backtest_2025.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {out_path}")
    print(json.dumps(summary.get("_overall", []), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
