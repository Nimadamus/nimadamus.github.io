#!/usr/bin/env python3
"""Public trend guardrails for unresolved historical betting data gaps.

These rules do not repair source data. They fail closed so unresolved identity
or market gaps cannot grade or surface public betting trend records.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


APPROVED_NHL_TEAMS = {
    "Anaheim Ducks",
    "Anaheim Mighty Ducks",
    "Arizona Coyotes",
    "Atlanta Thrashers",
    "Boston Bruins",
    "Buffalo Sabres",
    "Calgary Flames",
    "Carolina Hurricanes",
    "Chicago Blackhawks",
    "Colorado Avalanche",
    "Columbus Blue Jackets",
    "Dallas Stars",
    "Detroit Red Wings",
    "Edmonton Oilers",
    "Florida Panthers",
    "Los Angeles Kings",
    "Minnesota Wild",
    "Montreal Canadiens",
    "Nashville Predators",
    "New Jersey Devils",
    "New York Islanders",
    "New York Rangers",
    "Ottawa Senators",
    "Philadelphia Flyers",
    "Phoenix Coyotes",
    "Pittsburgh Penguins",
    "San Jose Sharks",
    "Seattle Kraken",
    "St. Louis Blues",
    "Tampa Bay Lightning",
    "Toronto Maple Leafs",
    "Vancouver Canucks",
    "Vegas Golden Knights",
    "Washington Capitals",
    "Winnipeg Jets",
}


UNVERIFIED_PUBLIC_TEAM_ALIASES = {
    "NBA": {
        "LA Clippers": "blocked_unverified_nba_clippers_franchise_mapping",
        "Los Angeles Clippers": "blocked_unverified_nba_clippers_franchise_mapping",
    },
    "NHL": {
        "Arizona Coyotes": "blocked_unverified_nhl_utah_arizona_franchise_mapping",
        "Phoenix Coyotes": "blocked_unverified_nhl_utah_arizona_franchise_mapping",
        "Utah Hockey Club": "blocked_unverified_nhl_utah_arizona_franchise_mapping",
        "Utah Mammoth": "blocked_unverified_nhl_utah_arizona_franchise_mapping",
    },
}


def parse_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def season_for(date_str: str, sport: str) -> int | None:
    try:
        dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except ValueError:
        return None
    if sport in {"NBA", "NHL"}:
        return dt.year if dt.month >= 10 else dt.year - 1
    if sport == "NFL":
        return dt.year if dt.month >= 9 else dt.year - 1
    return dt.year


def market_missing_reason(game: dict[str, Any], market_key: str) -> str:
    if market_key != "moneyline":
        return "source_limited_missing_market"

    away_missing = game.get("AwayMoneyline") in (None, "")
    home_missing = game.get("HomeMoneyline") in (None, "")
    if away_missing != home_missing:
        return "one_sided_moneyline"
    if away_missing or home_missing:
        return "source_limited_missing_moneyline"
    if game.get("_ml_estimated"):
        return "source_limited_estimated_moneyline"

    away_ml = parse_float(game.get("AwayMoneyline"))
    home_ml = parse_float(game.get("HomeMoneyline"))
    if away_ml is None or home_ml is None or away_ml == 0 or home_ml == 0:
        return "source_limited_unusable_moneyline"
    return "available"


def public_team_guardrail_reason(game: dict[str, Any], sport: str) -> str | None:
    aliases = UNVERIFIED_PUBLIC_TEAM_ALIASES.get(sport, {})
    for field in ("AwayTeam", "HomeTeam"):
        reason = aliases.get(str(game.get(field) or ""))
        if reason:
            return reason

    if sport == "NHL":
        home = str(game.get("HomeTeam") or "")
        away = str(game.get("AwayTeam") or "")
        if home not in APPROVED_NHL_TEAMS or away not in APPROVED_NHL_TEAMS:
            return "nhl_non_league_or_international_score_only"
    return None


def sellable_exclusion_reason(game: dict[str, Any], sport: str | None, market_key: str) -> str | None:
    sport = (sport or game.get("Sport") or "").upper()
    team_reason = public_team_guardrail_reason(game, sport)
    if team_reason:
        return team_reason

    if sport == "NHL" and market_key == "moneyline":
        if market_missing_reason(game, "moneyline") == "one_sided_moneyline":
            return "blocked_unresolved_nhl_one_sided_moneyline"

    if sport == "NFL" and market_key == "moneyline":
        season = season_for(str(game.get("Date") or ""), "NFL")
        if season is not None and season < 2007:
            return "nfl_moneyline_source_limited_pre_2007"
        if season is not None and season <= 2009 and market_missing_reason(game, "moneyline") == "source_limited_missing_moneyline":
            return "nfl_historical_source_limited_missing_moneyline_2007_2009"

    if sport == "MLB" and market_key == "moneyline":
        season = season_for(str(game.get("Date") or ""), "MLB")
        if (
            season is not None
            and 2000 <= season <= 2009
            and market_missing_reason(game, "moneyline") == "source_limited_missing_moneyline"
        ):
            return "mlb_historical_source_limited_missing_moneyline_2000s"

    reason = market_missing_reason(game, market_key)
    return None if reason == "available" else reason


def public_trend_exclusion_reason(game: dict[str, Any], sport: str | None) -> str | None:
    """Suppress unresolved rows from all public trend samples."""
    sport = (sport or game.get("Sport") or "").upper()
    team_reason = public_team_guardrail_reason(game, sport)
    if team_reason:
        return team_reason
    if sport == "NHL" and market_missing_reason(game, "moneyline") == "one_sided_moneyline":
        return "blocked_unresolved_nhl_one_sided_moneyline"
    return None

