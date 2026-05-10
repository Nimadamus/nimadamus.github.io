from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sellable_market_eligibility import (  # noqa: E402
    public_trend_exclusion_reason,
    sellable_exclusion_reason,
)


def test_nhl_one_sided_moneyline_is_blocked_from_public_trends():
    game = {
        "Sport": "NHL",
        "Date": "2024-01-06",
        "AwayTeam": "St. Louis Blues",
        "HomeTeam": "Carolina Hurricanes",
        "AwayMoneyline": None,
        "HomeMoneyline": -105,
    }

    assert sellable_exclusion_reason(game, "NHL", "moneyline") == "blocked_unresolved_nhl_one_sided_moneyline"
    assert public_trend_exclusion_reason(game, "NHL") == "blocked_unresolved_nhl_one_sided_moneyline"


def test_unverified_clippers_and_utah_franchise_rows_are_blocked():
    clippers = {
        "Sport": "NBA",
        "Date": "2026-01-01",
        "AwayTeam": "LA Clippers",
        "HomeTeam": "Los Angeles Lakers",
        "AwayMoneyline": 110,
        "HomeMoneyline": -120,
    }
    utah = {
        "Sport": "NHL",
        "Date": "2026-01-01",
        "AwayTeam": "Utah Mammoth",
        "HomeTeam": "Colorado Avalanche",
        "AwayMoneyline": 110,
        "HomeMoneyline": -120,
    }

    assert public_trend_exclusion_reason(clippers, "NBA") == "blocked_unverified_nba_clippers_franchise_mapping"
    assert public_trend_exclusion_reason(utah, "NHL") == "blocked_unverified_nhl_utah_arizona_franchise_mapping"


def test_historical_missing_moneyline_rows_get_visible_source_limit_reasons():
    mlb = {
        "Sport": "MLB",
        "Date": "2005-06-06",
        "AwayTeam": "Anaheim Angels",
        "HomeTeam": "Atlanta Braves",
        "AwayMoneyline": None,
        "HomeMoneyline": None,
    }
    nfl = {
        "Sport": "NFL",
        "Date": "2008-09-07",
        "AwayTeam": "New York Jets",
        "HomeTeam": "Miami Dolphins",
        "AwayMoneyline": None,
        "HomeMoneyline": None,
    }

    assert sellable_exclusion_reason(mlb, "MLB", "moneyline") == "mlb_historical_source_limited_missing_moneyline_2000s"
    assert sellable_exclusion_reason(nfl, "NFL", "moneyline") == "nfl_historical_source_limited_missing_moneyline_2007_2009"


def test_nhl_non_league_alias_is_labeled_and_suppressed():
    game = {
        "Sport": "NHL",
        "Date": "2024-09-30",
        "AwayTeam": "SC Bern",
        "HomeTeam": "New York Rangers",
        "AwayMoneyline": 300,
        "HomeMoneyline": -350,
    }

    assert public_trend_exclusion_reason(game, "NHL") == "nhl_non_league_or_international_score_only"

