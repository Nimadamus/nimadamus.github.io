from __future__ import annotations

import json
from pathlib import Path


DESKTOP_ROOT = Path.home() / "Desktop" / "MLB_Props"


def main() -> int:
    settled_files = sorted(DESKTOP_ROOT.glob("*/real_mlb_ev_props_settled.json"))
    rows = []
    for path in settled_files:
        rows.extend(json.loads(path.read_text(encoding="utf-8")))

    graded = [row for row in rows if row.get("settled")]
    if not graded:
        print("No settled prop files found.")
        return 0

    graded.sort(key=lambda row: row.get("ev_pct", 0), reverse=True)
    wins = sum(1 for row in graded if row["result"] == "win")
    losses = sum(1 for row in graded if row["result"] == "loss")
    pushes = sum(1 for row in graded if row["result"] == "push")
    risked = max(1, wins + losses)
    profit = sum(float(row["profit_units"]) for row in graded)
    roi = profit / risked * 100

    print(f"graded={len(graded)} wins={wins} losses={losses} pushes={pushes}")
    print(f"profit_units={profit:.4f}")
    print(f"roi_pct={roi:.2f}")

    thresholds = [0, 5, 10, 15, 20, 25, 30, 40]
    print("")
    for threshold in thresholds:
        subset = [row for row in graded if float(row.get('ev_pct', 0)) >= threshold]
        w = sum(1 for row in subset if row["result"] == "win")
        l = sum(1 for row in subset if row["result"] == "loss")
        p = sum(1 for row in subset if row["result"] == "push")
        risk = max(1, w + l)
        prof = sum(float(row["profit_units"]) for row in subset)
        sub_roi = prof / risk * 100
        print(f"ev>={threshold:>2}% | bets={len(subset):>3} | wins={w:>3} | losses={l:>3} | pushes={p:>3} | profit={prof:>7.2f}u | roi={sub_roi:>7.2f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
