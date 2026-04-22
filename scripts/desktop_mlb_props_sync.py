"""
Desktop MLB props sync for The Odds API.

Builds a quota-aware daily export of MLB player props to the desktop:
- raw event payload cache
- normalized JSON
- flat CSV
- quota/status manifest

This is designed to be resilient on free or low-credit plans. It fetches
today's MLB events, requests prop markets in chunks, and stops cleanly when
credits run low while preserving everything fetched so far.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List
from zoneinfo import ZoneInfo

import requests


PACIFIC = ZoneInfo("America/Los_Angeles")
SPORT_KEY = "baseball_mlb"
EVENTS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events"
EVENT_ODDS_URL = f"https://api.the-odds-api.com/v4/sports/{SPORT_KEY}/events/{{event_id}}/odds"

# Official MLB prop markets listed by The Odds API docs as of April 14, 2026.
CORE_MARKETS = [
    "batter_home_runs",
    "batter_first_home_run",
    "batter_hits",
    "batter_total_bases",
    "batter_rbis",
    "batter_runs_scored",
    "batter_hits_runs_rbis",
    "batter_singles",
    "batter_doubles",
    "batter_triples",
    "batter_walks",
    "batter_strikeouts",
    "batter_stolen_bases",
    "pitcher_strikeouts",
    "pitcher_record_a_win",
    "pitcher_hits_allowed",
    "pitcher_walks",
    "pitcher_earned_runs",
    "pitcher_outs",
]

ALTERNATE_MARKETS = [
    "batter_total_bases_alternate",
    "batter_home_runs_alternate",
    "batter_hits_alternate",
    "batter_rbis_alternate",
    "batter_walks_alternate",
    "batter_strikeouts_alternate",
    "batter_runs_scored_alternate",
    "batter_singles_alternate",
    "batter_doubles_alternate",
    "batter_triples_alternate",
    "pitcher_hits_allowed_alternate",
    "pitcher_walks_alternate",
    "pitcher_earned_runs_alternate",
    "pitcher_strikeouts_alternate",
    "pitcher_outs_alternate",
]

DEFAULT_BOOKMAKERS = [
    "draftkings",
    "fanduel",
    "betmgm",
    "betrivers",
    "espnbet",
    "fanatics",
    "betonlineag",
    "bovada",
]

OFFICIAL_PRIORITY_MARKETS = [
    "pitcher_strikeouts",
    "pitcher_outs",
]


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def american_implied_probability(price: Any) -> float | None:
    if not isinstance(price, (int, float)) or price == 0:
        return None
    if price > 0:
        return 100 / (price + 100)
    return abs(price) / (abs(price) + 100)


def safe_slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "unknown"


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def prioritize_markets(markets: List[str]) -> List[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for market in OFFICIAL_PRIORITY_MARKETS:
        if market in markets and market not in seen:
            ordered.append(market)
            seen.add(market)
    for market in markets:
        if market not in seen:
            ordered.append(market)
            seen.add(market)
    return ordered


@dataclass
class FetchContext:
    output_dir: Path
    raw_dir: Path
    api_key: str
    target_date: str
    chunk_size: int
    min_remaining: int
    bookmakers: List[str]
    markets: List[str]
    pause_ms: int


class DesktopMLBPropsSync:
    def __init__(self, ctx: FetchContext):
        self.ctx = ctx
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "desktop-mlb-props-sync/1.0"})
        self.quota: Dict[str, Any] = {
            "remaining": None,
            "used": None,
            "last_cost": None,
            "last_updated": None,
        }
        self.events: List[Dict[str, Any]] = []
        self.raw_payloads: List[Dict[str, Any]] = []
        self.rows: List[Dict[str, Any]] = []
        self.stopped_early = False

    def _update_quota(self, response: requests.Response) -> None:
        self.quota["remaining"] = response.headers.get("x-requests-remaining")
        self.quota["used"] = response.headers.get("x-requests-used")
        self.quota["last_cost"] = response.headers.get("x-requests-last")
        self.quota["last_updated"] = datetime.now(PACIFIC).isoformat()

    def _remaining_credits(self) -> int | None:
        remaining = self.quota.get("remaining")
        if remaining is None:
            return None
        try:
            return int(remaining)
        except (TypeError, ValueError):
            return None

    def _can_continue(self) -> bool:
        remaining = self._remaining_credits()
        if remaining is None:
            return True
        return remaining > self.ctx.min_remaining

    def fetch_events(self) -> None:
        response = self.session.get(EVENTS_URL, params={"apiKey": self.ctx.api_key}, timeout=30)
        response.raise_for_status()
        self._update_quota(response)
        all_events = response.json()
        self.events = [
            event for event in all_events if event.get("commence_time", "").startswith(self.ctx.target_date)
        ]

    def fetch_props(self) -> None:
        if not self.events:
            return

        for event in self.events:
            if not self._can_continue():
                self.stopped_early = True
                break

            for markets_chunk in chunked(self.ctx.markets, self.ctx.chunk_size):
                remaining = self._remaining_credits()
                estimated_cost = len(markets_chunk)
                if remaining is not None and remaining <= max(self.ctx.min_remaining, estimated_cost):
                    self.stopped_early = True
                    return

                params = {
                    "apiKey": self.ctx.api_key,
                    "regions": "us",
                    "markets": ",".join(markets_chunk),
                    "oddsFormat": "american",
                    "bookmakers": ",".join(self.ctx.bookmakers),
                }
                response = self.session.get(
                    EVENT_ODDS_URL.format(event_id=event["id"]),
                    params=params,
                    timeout=45,
                )
                if response.status_code == 429:
                    self._update_quota(response)
                    self.stopped_early = True
                    return
                response.raise_for_status()
                self._update_quota(response)
                payload = response.json()
                payload_record = {
                    "event_id": event["id"],
                    "game": f"{event['away_team']} @ {event['home_team']}",
                    "markets_requested": markets_chunk,
                    "fetched_at": datetime.now(PACIFIC).isoformat(),
                    "quota": dict(self.quota),
                    "payload": payload,
                }
                self.raw_payloads.append(payload_record)
                self._normalize_payload(event, payload, markets_chunk)
                time.sleep(self.ctx.pause_ms / 1000)

    def _normalize_payload(
        self, event: Dict[str, Any], payload: Dict[str, Any], markets_chunk: List[str]
    ) -> None:
        game_label = f"{event['away_team']} @ {event['home_team']}"
        for bookmaker in payload.get("bookmakers", []):
            book_name = bookmaker.get("title")
            book_key = bookmaker.get("key")
            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                for outcome in market.get("outcomes", []):
                    price = outcome.get("price")
                    line = outcome.get("point")
                    implied = american_implied_probability(price)
                    self.rows.append(
                        {
                            "date": self.ctx.target_date,
                            "game": game_label,
                            "event_id": event.get("id"),
                            "commence_time": event.get("commence_time"),
                            "away_team": event.get("away_team"),
                            "home_team": event.get("home_team"),
                            "bookmaker": book_name,
                            "bookmaker_key": book_key,
                            "market": market_key,
                            "requested_chunk": ",".join(markets_chunk),
                            "side": outcome.get("name"),
                            "player": outcome.get("description") or outcome.get("name"),
                            "line": line,
                            "odds_american": price,
                            "implied_probability": round(implied, 6) if implied is not None else None,
                            "last_update": market.get("last_update") or bookmaker.get("last_update"),
                        }
                    )

    def write_outputs(self) -> Dict[str, Path]:
        self.ctx.output_dir.mkdir(parents=True, exist_ok=True)
        self.ctx.raw_dir.mkdir(parents=True, exist_ok=True)

        raw_path = self.ctx.output_dir / "mlb_props_raw.json"
        normalized_path = self.ctx.output_dir / "mlb_props_normalized.json"
        csv_path = self.ctx.output_dir / "mlb_props_normalized.csv"
        status_path = self.ctx.output_dir / "sync_status.json"
        backup_dir = self.ctx.output_dir / "snapshots"
        backup_dir.mkdir(parents=True, exist_ok=True)

        previous_rows = read_json_file(normalized_path, [])
        previous_status = read_json_file(status_path, {})
        had_previous_rows = isinstance(previous_rows, list) and len(previous_rows) > 0
        preserve_previous = len(self.rows) == 0 and had_previous_rows
        active_rows = previous_rows if preserve_previous else self.rows

        if had_previous_rows:
            previous_stamp = previous_status.get("generated_at", "unknown").replace(":", "-")
            backup_raw = backup_dir / f"mlb_props_raw_{previous_stamp}.json"
            backup_norm = backup_dir / f"mlb_props_normalized_{previous_stamp}.json"
            if not backup_raw.exists() and raw_path.exists():
                backup_raw.write_text(raw_path.read_text(encoding="utf-8"), encoding="utf-8")
            if not backup_norm.exists() and normalized_path.exists():
                backup_norm.write_text(normalized_path.read_text(encoding="utf-8"), encoding="utf-8")

        if preserve_previous:
            raw_payloads_to_write = read_json_file(raw_path, [])
        else:
            raw_payloads_to_write = self.raw_payloads

        raw_path.write_text(json.dumps(raw_payloads_to_write, indent=2), encoding="utf-8")
        normalized_path.write_text(json.dumps(active_rows, indent=2), encoding="utf-8")

        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(active_rows[0].keys()) if active_rows else [])
            if active_rows:
                writer.writeheader()
                writer.writerows(active_rows)

        summary = self._build_summary(active_rows)
        available_markets = {row["market"] for row in active_rows}
        official_games = {
            row["game"] for row in active_rows if row["market"] in OFFICIAL_PRIORITY_MARKETS
        }
        status = {
            "generated_at": datetime.now(PACIFIC).isoformat(),
            "target_date": self.ctx.target_date,
            "sport_key": SPORT_KEY,
            "event_count": len(self.events),
            "raw_payload_count": len(self.raw_payloads),
            "prop_row_count": len(active_rows),
            "quota": self.quota,
            "stopped_early": self.stopped_early,
            "fetch_succeeded": len(self.rows) > 0,
            "preserved_previous_snapshot": preserve_previous,
            "previous_snapshot_generated_at": previous_status.get("generated_at") if preserve_previous else None,
            "official_markets_requested_first": True,
            "official_markets_present": [market for market in OFFICIAL_PRIORITY_MARKETS if market in available_markets],
            "official_markets_missing": [market for market in OFFICIAL_PRIORITY_MARKETS if market not in available_markets],
            "official_games_covered": len(official_games),
            "official_total_games": len(self.events),
            "markets_requested": self.ctx.markets,
            "bookmakers_requested": self.ctx.bookmakers,
            "summary": summary,
            "files": {
                "raw_json": str(raw_path),
                "normalized_json": str(normalized_path),
                "normalized_csv": str(csv_path),
            },
        }
        status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        return {
            "raw_json": raw_path,
            "normalized_json": normalized_path,
            "normalized_csv": csv_path,
            "status_json": status_path,
        }

    def _build_summary(self, rows: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
        use_rows = self.rows if rows is None else rows
        market_counts = Counter(row["market"] for row in use_rows)
        bookmaker_counts = Counter(row["bookmaker"] for row in use_rows)
        game_counts = Counter(row["game"] for row in use_rows)
        return {
            "markets": market_counts.most_common(),
            "bookmakers": bookmaker_counts.most_common(),
            "games": game_counts.most_common(),
        }


def build_output_dir(base_output_dir: Path, target_date: str) -> Path:
    return base_output_dir / "MLB_Props" / target_date


def parse_args() -> argparse.Namespace:
    local_today = datetime.now(PACIFIC).date().isoformat()
    parser = argparse.ArgumentParser(description="Sync MLB props to desktop with quota-aware caching.")
    parser.add_argument("--date", default=local_today, help="Target slate date in YYYY-MM-DD.")
    parser.add_argument(
        "--output-dir",
        default=str(Path.home() / "Desktop"),
        help="Desktop root where the MLB_Props folder should be created.",
    )
    parser.add_argument(
        "--markets",
        choices=["official", "core", "all"],
        default="all",
        help="Fetch only official model markets, core markets, or core + alternate markets.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=4,
        help="Number of markets per event request. Smaller values use more requests but are safer.",
    )
    parser.add_argument(
        "--min-remaining",
        type=int,
        default=25,
        help="Stop once remaining credits fall to this level.",
    )
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=250,
        help="Pause between API requests to stay polite and reduce burst risk.",
    )
    parser.add_argument(
        "--bookmakers",
        default=",".join(DEFAULT_BOOKMAKERS),
        help="Comma-separated sportsbook keys to request.",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ODDS_API_KEY", "c405ed8a7e1f4ec945d39aeeaf647e4b"),
        help="The Odds API key. Defaults to ODDS_API_KEY env var, then existing repo fallback.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.markets == "official":
        markets = OFFICIAL_PRIORITY_MARKETS.copy()
    elif args.markets == "all":
        markets = CORE_MARKETS + ALTERNATE_MARKETS
    else:
        markets = CORE_MARKETS
    markets = prioritize_markets(markets)
    output_dir = build_output_dir(Path(args.output_dir), args.date)
    ctx = FetchContext(
        output_dir=output_dir,
        raw_dir=output_dir / "raw_cache",
        api_key=args.api_key,
        target_date=args.date,
        chunk_size=max(1, args.chunk_size),
        min_remaining=max(0, args.min_remaining),
        bookmakers=[item.strip() for item in args.bookmakers.split(",") if item.strip()],
        markets=markets,
        pause_ms=max(0, args.pause_ms),
    )

    sync = DesktopMLBPropsSync(ctx)
    try:
        sync.fetch_events()
        sync.fetch_props()
        files = sync.write_outputs()
    except Exception as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        return 1

    print(f"MLB props sync complete for {args.date}")
    print(f"Events fetched: {len(sync.events)}")
    print(f"Prop rows saved: {len(sync.rows)}")
    print(f"Stopped early: {sync.stopped_early}")
    print(f"Quota remaining: {sync.quota.get('remaining')}")
    for label, path in files.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
