#!/usr/bin/env python3
"""Keep every sport hub on the CURRENT slate (Oct 1 2026, Nima: "the site
cannot say MLB Analysis April 9 when it is October").

Why this exists: the hubs depended on two things that both stopped. The
Claude-written daily analysis (scripts/auto_content, daily-covers-update.yml)
has failed every day with "credit balance is too low" while the workflow still
reported success, and the preview hubs were only refreshed by hand during
ATLAS. Nothing in the pipeline was data driven, so when the writers stopped
the pages froze on April, February and January content.

This script is deterministic and needs no AI: it reads ESPN's public
scoreboards and bakes a static "current slate" block (games, start times,
records, venue, TV, DraftKings lines as published by ESPN, live and final
scores) into the top of <main> on each hub, between
<!-- CURRENT-SLATE-START --> and <!-- CURRENT-SLATE-END -->. On the main
sport hubs it also refreshes the <title>, H1, meta description, og/twitter
titles and JSON-LD dateModified so they describe the slate on the page.
Older written analysis stays on the page, labeled with its real date.
No URL, canonical, robots tag or sitemap entry is touched, and no dated
archive page is ever created.

If ESPN fails for a sport the page is left exactly as it was.

Usage:
  python scripts/current_slate.py            # update every hub
  python scripts/current_slate.py --dry-run  # print, write nothing
  python scripts/current_slate.py --only mlb
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PT = ZoneInfo("America/Los_Angeles")
ET = ZoneInfo("America/New_York")
ESPN = "https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
# ESPN answers 403 to custom bot strings and truncated browser strings and 200 to
# the plain requests client string (same finding as commit 55fd8a840a), so keep it.
UA = {}

START = "<!-- CURRENT-SLATE-START (auto-updated by scripts/current_slate.py) -->"
END = "<!-- CURRENT-SLATE-END -->"
BLOCK_RE = re.compile(r"<!-- CURRENT-SLATE-START.*?<!-- CURRENT-SLATE-END -->\s*", re.S)

SPORTS = {
    "mlb": {"label": "MLB", "feeds": [("baseball/mlb", {})], "records": "mlb-records.html",
            "hub": "mlb.html", "pages": ["mlb.html", "mlb-previews.html"], "weekly": False},
    "nfl": {"label": "NFL", "feeds": [("football/nfl", {})], "records": "nfl-records.html",
            "hub": "nfl.html", "pages": ["nfl.html"], "weekly": True},
    "ncaaf": {"label": "College Football", "short": "NCAAF",
              "feeds": [("football/college-football", {"groups": "80", "limit": "400"})],
              "records": "ncaaf-records.html", "hub": "ncaaf.html", "pages": ["ncaaf.html"],
              "weekly": True, "ranked_only": True},
    "nba": {"label": "NBA", "feeds": [("basketball/nba", {})], "records": "nba-records.html",
            "hub": "nba.html", "pages": ["nba.html", "nba-previews.html"], "weekly": False},
    "nhl": {"label": "NHL", "feeds": [("hockey/nhl", {})], "records": "nhl-records.html",
            "hub": "nhl.html", "pages": ["nhl.html", "nhl-previews.html"], "weekly": False},
    "ncaab": {"label": "College Basketball", "short": "NCAAB",
              "feeds": [("basketball/mens-college-basketball", {"groups": "50", "limit": "400"})],
              "records": "ncaab-records.html", "hub": "ncaab.html",
              "pages": ["ncaab.html", "college-basketball-previews.html"], "weekly": False,
              "ranked_only": True},
    "soccer": {"label": "Soccer", "feeds": [("soccer/eng.1", {}), ("soccer/uefa.champions", {}),
                                            ("soccer/usa.1", {})],
               "records": "soccer-records.html", "hub": "soccer.html",
               "pages": ["soccer.html", "soccer-previews.html"], "weekly": False},
}
SEASON_TYPE = {1: "Preseason", 2: "Regular Season", 3: "Postseason", 4: "Offseason"}


# ---------------------------------------------------------------- data
def _get(path, params):
    r = requests.get(ESPN.format(path=path), params=params, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def _odds(comp):
    o = (comp.get("odds") or [None])[0]
    if not o:
        return None

    def close(market, side, key):
        try:
            v = o[market][side]["close"][key]
            return None if v in (None, "", "OFF") else str(v)
        except (KeyError, TypeError):
            return None

    total = o.get("overUnder")
    return {
        "provider": (o.get("provider") or {}).get("displayName") or (o.get("provider") or {}).get("name"),
        "away_ml": close("moneyline", "away", "odds"), "home_ml": close("moneyline", "home", "odds"),
        "away_spread": close("pointSpread", "away", "line"), "home_spread": close("pointSpread", "home", "line"),
        "away_spread_odds": close("pointSpread", "away", "odds"), "home_spread_odds": close("pointSpread", "home", "odds"),
        "total": (f"{total:g}" if isinstance(total, (int, float)) else None),
        "details": o.get("details"),
    }


def _team(c):
    t = c.get("team") or {}
    rec = next((r.get("summary") for r in c.get("records") or [] if r.get("type") in (None, "total", "ytd")), None)
    if rec is None and c.get("records"):
        rec = c["records"][0].get("summary")
    rank = (c.get("curatedRank") or {}).get("current")
    probable = None
    for p in c.get("probables") or []:
        a = p.get("athlete") or {}
        if a.get("displayName"):
            probable = a["displayName"]
            break
    return {
        "name": t.get("displayName") or t.get("name") or "",
        "short": t.get("shortDisplayName") or t.get("name") or "",
        "abbr": t.get("abbreviation") or "",
        "logo": t.get("logo") or "",
        "record": rec,
        "rank": rank if isinstance(rank, int) and 0 < rank <= 25 else None,
        "score": c.get("score"),
        "probable": probable,
    }


def parse_event(e, league_name=None):
    comp = (e.get("competitions") or [{}])[0]
    cs = comp.get("competitors") or []
    away = next((c for c in cs if c.get("homeAway") == "away"), None)
    home = next((c for c in cs if c.get("homeAway") == "home"), None)
    if not away or not home:
        return None
    start = dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
    st = (comp.get("status") or e.get("status") or {}).get("type") or {}
    venue = comp.get("venue") or {}
    tv = []
    for b in comp.get("broadcasts") or []:
        tv += b.get("names") or []
    notes = [re.sub(r"\s+-\s+", " ", n.get("headline")) for n in comp.get("notes") or [] if n.get("headline")]
    stype = (e.get("season") or {}).get("type")
    return {
        "id": e.get("id"),
        "start": start,
        "state": st.get("state"),             # pre / in / post
        "status": st.get("shortDetail") or st.get("detail") or "",
        "completed": bool(st.get("completed")),
        "away": _team(away), "home": _team(home),
        "neutral": bool(comp.get("neutralSite")),
        "venue": venue.get("fullName"),
        "city": ", ".join(x for x in [(venue.get("address") or {}).get("city"),
                                      (venue.get("address") or {}).get("state")] if x),
        "tv": ", ".join(dict.fromkeys(tv)),
        "notes": notes[0] if notes else None,
        "season_type": SEASON_TYPE.get(stype) if isinstance(stype, int) else None,
        "league": league_name,
        "odds": _odds(comp),
    }


def fetch_sport(key, now_pt=None):
    """ESPN's default scoreboard can still point at yesterday after midnight, so
    daily sports also pull today's date explicitly and the two are merged."""
    cfg = SPORTS[key]
    events, meta, seen = [], {}, set()
    today = (now_pt or dt.datetime.now(PT)).strftime("%Y%m%d")
    requests_list = []
    for path, params in cfg["feeds"]:
        requests_list.append((path, params))
        if not cfg["weekly"]:
            requests_list.append((path, dict(params, dates=today)))
    for path, params in requests_list:
        d = _get(path, params)
        lg = (d.get("leagues") or [{}])[0]
        name = lg.get("abbreviation") if key == "soccer" else None
        if key == "soccer":
            name = {"eng.1": "Premier League", "uefa.champions": "Champions League",
                    "usa.1": "MLS"}.get(path.split("/")[-1], lg.get("name"))
        for e in d.get("events") or []:
            if e.get("id") in seen:
                continue
            seen.add(e.get("id"))
            ev = parse_event(e, name)
            if ev:
                events.append(ev)
        if not meta:
            meta = {"week": (d.get("week") or {}).get("number"),
                    "season_type": ((lg.get("season") or {}).get("type") or {}).get("name")}
    events.sort(key=lambda x: (x["start"], x["away"]["name"]))
    return {"key": key, "events": events, **meta}


def slate_window(data, now_pt):
    """Choose what the hub shows: today's games (PT) if any are left or were
    played today, else the next date with games. Weekly sports show the whole
    current ESPN week."""
    ev = data["events"]
    if not ev:
        return [], None
    if SPORTS[data["key"]]["weekly"]:
        return ev, "week"
    today = now_pt.date()
    by_day = {}
    for e in ev:
        by_day.setdefault(e["start"].astimezone(PT).date(), []).append(e)
    if today in by_day:
        return by_day[today], "today"
    future = sorted(d for d in by_day if d > today)
    if future:
        return by_day[future[0]], "next"
    # ESPN returned only past games (late night): show them as today's results.
    last = max(by_day)
    return by_day[last], "past"


# ---------------------------------------------------------------- render
def esc(s):
    return html.escape(str(s or ""), quote=True)


def fmt_day(d):
    return f"{d:%A}, {d:%B} {d.day}, {d.year}"


def fmt_date(d):
    return f"{d:%B} {d.day}, {d.year}"


def fmt_time(t):
    et, pt = t.astimezone(ET), t.astimezone(PT)
    return f"{et:%I:%M %p}".lstrip("0") + " ET / " + f"{pt:%I:%M %p}".lstrip("0") + " PT"


def team_page(key, t):
    """The team's betting record page (Phase 5 data pages), when one exists for this sport."""
    if key != "mlb":
        return None
    try:
        import mlb_team_pages
    except Exception:
        return None
    name = mlb_team_pages.ALIASES.get(t.get("name"), t.get("name"))
    if name not in mlb_team_pages.TEAMS:
        return None
    f = mlb_team_pages.page_file(name)
    return f if os.path.isfile(os.path.join(ROOT, f)) else None


def team_cell(t, key=None):
    rank = f'<span class="cs-rank">{t["rank"]}</span> ' if t.get("rank") else ""
    rec = f' <span class="cs-rec">({esc(t["record"])})</span>' if t.get("record") else ""
    prob = f'<span class="cs-prob">{esc(t["probable"])}</span>' if t.get("probable") else ""
    label = esc(t["short"] or t["name"])
    page = team_page(key, t)
    if page:
        label = f'<a href="{page}" title="{esc(t["name"])} betting record">{label}</a>'
    return f'{logo_img(t)}{rank}<strong>{label}</strong>{rec}{prob}'


def line_cell(e, key):
    o = e.get("odds")
    if not o:
        return '<span class="cs-muted">Not posted</span>'
    rows = []
    for side in ("away", "home"):
        abbr = e[side]["abbr"]
        parts = []
        sp = o.get(f"{side}_spread")
        if sp and key not in ("mlb", "nhl", "soccer"):
            parts.append(sp)
        elif sp and key in ("mlb", "nhl"):
            parts.append(f"{sp} ({o.get(f'{side}_spread_odds') or ''})".replace(" ()", ""))
        ml = o.get(f"{side}_ml")
        if ml:
            parts.append(f"ML {ml}")
        if parts:
            rows.append(f"{esc(abbr)} {esc(' / '.join(parts))}")
    if o.get("total"):
        rows.append(f"Total {esc(o['total'])}")
    if not rows and o.get("details"):
        rows.append(esc(o["details"]))
    return "<br>".join(rows) or '<span class="cs-muted">Not posted</span>'


def status_cell(e):
    """Pregame only (repo rule: sports pages never show final scores or outcomes)."""
    if e["state"] == "pre":
        return esc(fmt_time(e["start"]))
    label = "Completed" if e["completed"] else "In progress"
    return f'<strong>{label}</strong><br><span class="cs-muted">Started {esc(fmt_time(e["start"]))}</span>'


def logo_img(t):
    src = t.get("logo") or ""
    if not src.startswith("https://a.espncdn.com/"):
        return ""
    path = src.split("a.espncdn.com", 1)[1]
    small = f"https://a.espncdn.com/combiner/i?img={path}&w=64&h=64"
    return f'<img class="cs-logo" src="{esc(small)}" alt="" width="22" height="22" loading="lazy" decoding="async">'


CSS = """<style id="current-slate-css">
#current-slate{margin:0 0 32px;padding:22px 22px 18px;border:1px solid rgba(212,175,55,.35);border-radius:12px;background:linear-gradient(160deg,#141821,#0d1016);color:#e8ecf2;font-family:inherit}
#current-slate h2{margin:0 0 4px;font-size:1.45rem;line-height:1.25;color:#fff}
#current-slate .cs-sub{margin:0 0 14px;color:#aeb6c2;font-size:.92rem}
#current-slate{max-width:100%;box-sizing:border-box}
#current-slate .cs-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;width:0;min-width:100%}
#current-slate table{width:100%;border-collapse:collapse;font-size:.9rem;min-width:560px}
#current-slate th{text-align:left;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:#d4af37;padding:8px 8px;border-bottom:1px solid rgba(212,175,55,.35)}
#current-slate td{padding:9px 8px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;line-height:1.4}
#current-slate td.cs-time{white-space:nowrap}
#current-slate .cs-rec,#current-slate .cs-muted{color:#9aa3af;font-size:.85em}
#current-slate .cs-prob{display:block;color:#9aa3af;font-size:.82em}
#current-slate .cs-rank{display:inline-block;min-width:1.6em;padding:0 4px;border-radius:4px;background:rgba(212,175,55,.18);color:#f3d77a;font-size:.78em;text-align:center}
#current-slate .cs-logo{width:22px;height:22px;vertical-align:-5px;margin-right:6px}
#current-slate .cs-note{display:block;color:#f3d77a;font-size:.8em}
#current-slate .cs-links{display:flex;flex-wrap:wrap;gap:8px 16px;margin:14px 0 0;padding:0;list-style:none;font-size:.9rem}
#current-slate .cs-links a{color:#f3d77a}
#current-slate .cs-src{margin:10px 0 0;color:#8b94a1;font-size:.78rem}
#current-slate .cs-day{margin:16px 0 6px;font-size:.95rem;color:#fff}
.cs-archive-note{margin:0 0 22px;padding:10px 14px;border-left:3px solid #d4af37;background:rgba(255,255,255,.03);color:#aeb6c2;font-size:.9rem}
</style>"""


def heading_for(key, mode, games, now_pt, week=None):
    cfg = SPORTS[key]
    label = cfg["label"]
    stype = next((g["season_type"] for g in games if g.get("season_type")), None)
    tag = f" {stype}" if stype in ("Preseason", "Postseason") else ""
    days = sorted({g["start"].astimezone(PT).date() for g in games})
    if mode == "week":
        wk = f" Week {week}" if week and stype != "Postseason" else ""
        if len(days) > 1 and days[0].month == days[-1].month:
            rng = f"{days[0]:%B} {days[0].day} to {days[-1].day}, {days[-1].year}"
        elif len(days) > 1:
            rng = f"{days[0]:%B} {days[0].day} to {days[-1]:%B} {days[-1].day}, {days[-1].year}"
        else:
            rng = fmt_date(days[0])
        return f"{label}{wk}{tag} Slate: {rng}", rng
    d = days[0]
    if mode == "today":
        return f"{label}{tag} Games Today: {fmt_day(d)}", fmt_date(d)
    if mode == "next":
        return f"Next {label}{tag} Games: {fmt_day(d)}", fmt_date(d)
    return f"{label}{tag} Games: {fmt_day(d)}", fmt_date(d)


def render_block(key, data, now_pt, analysis_date=None, page=None):
    cfg = SPORTS[key]
    games, mode = slate_window(data, now_pt)
    updated = f"{now_pt:%B} {now_pt.day}, {now_pt.year} at " + f"{now_pt:%I:%M %p}".lstrip("0") + " PT"
    attrs = (f'id="current-slate" data-sport="{key}" data-updated="{now_pt:%Y-%m-%d}"'
             + (f' data-analysis-date="{esc(analysis_date)}"' if analysis_date else ""))
    picks_page = {"mlb": "mlb-picks-today.html"}.get(key)
    links = [(picks_page, f"Today's BetLegend {cfg['label']} picks") if picks_page else ("blog.html", "Today's BetLegend picks"), (cfg["records"], f"{cfg.get('short', cfg['label'])} betting record"),
             ("injury-report.html", "Injury report"), ("live-odds.html", "Line shopping")]
    links_html = "".join(f'<li><a href="{h}">{esc(t)}</a></li>' for h, t in links)
    if not games:
        head = f"{cfg['label']}: No Games Scheduled"
        body = (f'<p class="cs-sub">ESPN lists no upcoming {esc(cfg["label"])} games right now. '
                f'This page updates automatically when the schedule is posted.</p>')
        return head, None, (f"{START}\n{CSS}\n<section {attrs}>\n<h2>{esc(head)}</h2>\n{body}\n"
                            f'<ul class="cs-links">{links_html}</ul>\n<p class="cs-src">Updated {esc(updated)}.</p>\n</section>\n{END}\n')
    head, date_label = heading_for(key, mode, games, now_pt, data.get("week"))
    shown = games
    extra = ""
    if cfg.get("ranked_only"):
        ranked = [g for g in games if g["away"]["rank"] or g["home"]["rank"]]
        if ranked and len(ranked) < len(games):
            shown = ranked
            extra = (f'<p class="cs-sub">Showing the {len(ranked)} games with an AP Top 25 team. '
                     f'ESPN lists {len(games)} Division I games in this window.</p>')
    by_day = {}
    for g in shown:
        by_day.setdefault(g["start"].astimezone(PT).date(), []).append(g)
    parts = []
    for d in sorted(by_day):
        if len(by_day) > 1:
            parts.append(f'<h3 class="cs-day">{esc(fmt_day(d))}</h3>')
        rows = []
        for g in by_day[d]:
            note = f'<span class="cs-note">{esc(g["notes"])}</span>' if g.get("notes") else ""
            if key == "soccer" and g.get("league"):
                note = f'<span class="cs-note">{esc(g["league"])}{": " + esc(g["notes"]) if g.get("notes") else ""}</span>'
            sep = "vs" if g["neutral"] else "at"
            where = esc(g["venue"] or "")
            if g.get("city"):
                where += f'<br><span class="cs-muted">{esc(g["city"])}</span>'
            if g.get("tv"):
                where += f'<br><span class="cs-muted">TV: {esc(g["tv"])}</span>'
            rows.append(
                f'<tr><td>{note}{team_cell(g["away"], key)} <span class="cs-muted">{sep}</span><br>{team_cell(g["home"], key)}</td>'
                f'<td class="cs-time">{status_cell(g)}</td><td>{line_cell(g, key)}</td><td>{where}</td></tr>')
        parts.append('<div class="cs-wrap"><table><thead><tr><th>Matchup</th><th>Start</th>'
                     '<th>Lines</th><th>Venue and TV</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")
    providers = sorted({g["odds"]["provider"] for g in shown if g.get("odds") and g["odds"].get("provider")})
    src = "Schedule, records, venues and TV from ESPN."
    if providers:
        src += f" Lines are the {', '.join(providers)} numbers published by ESPN and can move before start time."
    sub = f'<p class="cs-sub">{len(shown)} game{"s" if len(shown) != 1 else ""}. Times are Eastern and Pacific.</p>'
    # id="board-date-note" tells the page's stale-board guard script that a dated
    # label already exists, so it does not stack a second note above today's slate.
    analysis_note = '\n<span id="board-date-note" hidden></span>'
    if analysis_date:
        analysis_note = (f'\n<p class="cs-archive-note" id="board-date-note">The written analysis below this slate was published '
                         f'{esc(analysis_date)}. New BetLegend picks post daily to the '
                         f'<a href="blog.html">BetLegend blog</a>.</p>')
    block = (f"{START}\n{CSS}\n<section {attrs}>\n<h2>{esc(head)}</h2>\n{sub}{extra}\n" + "\n".join(parts)
             + f'\n<ul class="cs-links">{links_html}</ul>\n<p class="cs-src">{esc(src)} Updated {esc(updated)}.</p>\n'
             f"</section>{analysis_note}\n{END}\n")
    return head, date_label, block


# ---------------------------------------------------------------- page edits
MONTH_DATE_RE = re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December)"
                           r"\s+(\d{1,2}),?\s+(20\d\d)")


def _main_body(page_html):
    m = re.search(r"<main\b[^>]*>", page_html)
    if m:
        return m, page_html.find("</main>", m.end())
    # college-basketball-previews.html has no <main>; its column is div.main-content
    m = re.search(r"<div\s+class=[\"']main-content[\"'][^>]*>", page_html)
    if not m:
        return None, None
    end = page_html.find("<footer", m.end())
    return m, (end if end > 0 else len(page_html))


def existing_analysis_date(page_html):
    """Date the written analysis on the page was published, from the page's own
    FORCED_PAGE_DATE or its first dated H1/title (read before we rewrite them)."""
    m = re.search(r"FORCED_PAGE_DATE\s*=\s*['\"](\d{4}-\d{2}-\d{2})['\"]", page_html)
    if m:
        d = dt.date.fromisoformat(m.group(1))
        return fmt_date(d)
    for pat in (r"<h1[^>]*>(.*?)</h1>", r"<title>(.*?)</title>"):
        h = re.search(pat, page_html, re.S | re.I)
        if h:
            dm = MONTH_DATE_RE.search(re.sub(r"<[^>]+>", " ", h.group(1)))
            if dm:
                return f"{dm.group(1)} {int(dm.group(2))}, {dm.group(3)}"
    return None


def _set_meta(page_html, attr, name, value):
    pat = re.compile(rf'(<meta\s+[^>]*{attr}=["\']{re.escape(name)}["\'][^>]*content=["\'])([^"\']*)(["\'])', re.I)
    if pat.search(page_html):
        return pat.sub(lambda m: m.group(1) + esc(value) + m.group(3), page_html)
    pat2 = re.compile(rf'(<meta\s+[^>]*content=["\'])([^"\']*)(["\'][^>]*{attr}=["\']{re.escape(name)}["\'])', re.I)
    return pat2.sub(lambda m: m.group(1) + esc(value) + m.group(3), page_html)


def update_page(path, key, data, now_pt, is_main_hub):
    with open(path, encoding="utf-8") as f:
        original = f.read()
    page = original
    old_block = BLOCK_RE.search(page)
    prev_analysis = None
    prev_hash = None
    if old_block:
        a = re.search(r'data-analysis-date="([^"]*)"', old_block.group(0))
        prev_analysis = html.unescape(a.group(1)) if a else None
        h = re.search(r'data-main-hash="([0-9a-f]+)"', old_block.group(0))
        prev_hash = h.group(1) if h else None
        page = BLOCK_RE.sub("", page, count=1)
    m, end = _main_body(page)
    if not m:
        print(f"  [{key}] {os.path.basename(path)}: no <main>, skipped")
        return False
    rest = page[m.end():end]
    # Other auto-managed blocks (Pro module, email signup) are not "written analysis".
    rest = re.sub(r"<!-- (PRO-CTA|EMAIL-SIGNUP|DATA-LINKS)-START.*?<!-- \1-END -->", "", rest, flags=re.S)
    rest_text = re.sub(r"<[^>]+>|\s+", "", rest)
    main_hash = hashlib.sha1(rest_text.encode("utf-8")).hexdigest()[:12]
    has_rest = len(rest_text) > 200
    if not has_rest:
        analysis = None
    elif prev_hash and prev_hash == main_hash and prev_analysis:
        analysis = prev_analysis
    elif old_block and prev_hash and prev_hash != main_hash:
        analysis = fmt_date(now_pt.date())   # new written content arrived since the last run
    else:
        analysis = existing_analysis_date(original)
    head, date_label, block = render_block(key, data, now_pt, analysis, os.path.basename(path))
    block = block.replace('<section id="current-slate"', f'<section data-main-hash="{main_hash}" id="current-slate"', 1)
    page = page[:m.end()] + "\n" + block + page[m.end():]

    label = SPORTS[key]["label"]
    if is_main_hub:
        title_core = head.replace(" Games Today: ", " Games Today, ").replace(": ", ", ")
        if date_label:
            title = f"{label} Slate, Odds and Analysis for {date_label} | BetLegend"
            if key == "mlb":  # approved by Nima 2026-10-01 on Search Console evidence (mlb / baseball betting stats)
                title = f"MLB Betting Odds, Stats and Picks for {date_label} | BetLegend"
            if SPORTS[key]["weekly"]:
                title = f"{head.replace(' Slate: ', ' Slate, Odds and Analysis: ')} | BetLegend"
        else:
            title = f"{label} Slate, Odds and Analysis | BetLegend"
        desc = (f"{label} games for {date_label}: start times, records, current spreads, moneylines and totals, "
                f"plus BetLegend picks and analysis. Updated automatically every day."
                if date_label else f"{label} schedule, odds and BetLegend analysis. Updated automatically every day.")
        page = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", page, count=1, flags=re.S | re.I)
        for attr, name in (("name", "description"), ("property", "og:description"), ("name", "twitter:description")):
            page = _set_meta(page, attr, name, desc)
        for attr, name in (("property", "og:title"), ("name", "twitter:title")):
            page = _set_meta(page, attr, name, title.replace(" | BetLegend", ""))
        h1_text = title.replace(" | BetLegend", "")

        def fix_ld(mm):
            body = mm.group(2)
            if '"NewsArticle"' not in body:
                return mm.group(0)
            body = re.sub(r'("headline"\s*:\s*)"(?:\\.|[^"\\])*"', lambda x: x.group(1) + json.dumps(h1_text), body, count=1)
            body = re.sub(r'("description"\s*:\s*)"(?:\\.|[^"\\])*"', lambda x: x.group(1) + json.dumps(desc), body, count=1)
            return mm.group(1) + body + mm.group(3)
        page = re.sub(r'(<script type="application/ld\+json">)(.*?)(</script>)', fix_ld, page, flags=re.S)
        page = re.sub(r"(<header[^>]*class=[\"'][^\"']*\bhero\b[^\"']*[\"'][^>]*>.*?<h1[^>]*>)(.*?)(</h1>)",
                      lambda mm: mm.group(1) + esc(h1_text) + mm.group(3), page, count=1, flags=re.S | re.I)
        _ = title_core
    else:
        h1_text = f"{label} Game Previews and Odds: " + (head.split(": ", 1)[1] if ": " in head else head)
        page = re.sub(r"(<header[^>]*class=[\"'][^\"']*\bhero\b[^\"']*[\"'][^>]*>.*?<h1[^>]*>)(.*?)(</h1>)",
                      lambda mm: mm.group(1) + esc(h1_text) + mm.group(3), page, count=1, flags=re.S | re.I)
    # Hero badge and intro line used to describe the last written article
    # ("NFL Archive", "Spring Training 2026", a June Game 6 recap). Describe the slate instead.
    games, mode = slate_window(data, now_pt)
    stype = next((g["season_type"] for g in games if g.get("season_type") in ("Preseason", "Postseason")), None)
    if SPORTS[key]["weekly"] and data.get("week") and stype != "Postseason":
        badge = f"{label} Week {data['week']}"
    else:
        badge = f"{label} {stype}" if stype else f"{label} Today"
    if games:
        n = len(games)
        when = {"today": "on today's board", "next": "on the next game day", "week": "this week",
                "past": "on the board"}[mode]
        intro = (f"{n} {label} game{'s' if n != 1 else ''} {when}, with start times, records and the current "
                 f"lines for every one, refreshed automatically four times a day. BetLegend picks post to the blog, "
                 f"and any written analysis further down this page carries its own date.")
    else:
        intro = (f"No {label} games are on the schedule right now. Start times and lines appear here "
                 f"automatically as soon as the schedule is posted.")
    hero = re.search(r"(<header[^>]*class=[\"'][^\"']*\bhero\b[^\"']*[\"'][^>]*>)(.*?)(</header>)", page, re.S | re.I)
    if hero:
        inner = hero.group(2)
        inner = re.sub(r'(<div class="hero-badge">)(.*?)(</div>)', lambda mm: mm.group(1) + esc(badge) + mm.group(3), inner, count=1, flags=re.S)
        inner = re.sub(r"(</h1>\s*<p[^>]*>)(.*?)(</p>)", lambda mm: mm.group(1) + esc(intro) + mm.group(3), inner, count=1, flags=re.S)
        page = page[:hero.start(2)] + inner + page[hero.end(2):]
    # Hubs that load neither shared stylesheet get the small layout guard (no sideways
    # scrolling on phones, nav and sidebar fit desktop widths).
    if "mobile-optimize.css" not in page and "layout-guard.css" not in page and "</head>" in page:
        page = page.replace("</head>", '<link rel="stylesheet" href="/layout-guard.css">\n</head>', 1)
    iso = now_pt.replace(microsecond=0).isoformat()
    page = re.sub(r'("dateModified"\s*:\s*")[^"]*(")', lambda mm: mm.group(1) + iso + mm.group(2), page)
    page = re.sub(r'(<meta\s+property=["\']article:modified_time["\']\s+content=["\'])[^"\']*', lambda mm: mm.group(1) + iso, page)

    # Do not rewrite a file when nothing but the timestamp would change.
    def strip_volatile(s):
        s = re.sub(r"Updated [A-Z][a-z]+ \d{1,2}, \d{4} at [0-9:]+ [AP]M PT\.", "", s)
        s = re.sub(r'("dateModified"\s*:\s*")[^"]*(")', r"\1\2", s)
        s = re.sub(r'(article:modified_time["\']\s+content=["\'])[^"\']*', r"\1", s)
        return s
    if strip_volatile(page) == strip_volatile(original):
        return False
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(page)
    return True


# ---------------------------------------------------------------- homepage featured game
NATIONAL_TV = ("ESPN", "ABC", "NBC", "CBS", "FOX", "TNT", "TBS", "Prime Video", "Peacock", "Netflix",
               "NFL Network", "FS1", "truTV", "Apple TV")
FEATURE_SPORTS = ("mlb", "nfl", "ncaaf", "nba", "nhl")


def _winpct(rec):
    try:
        parts = [int(x) for x in str(rec).split("-")[:2]]
        return parts[0] / max(1, sum(parts))
    except (ValueError, TypeError):
        return 0.5


def feature_score(key, g):
    """Deterministic marquee rule. Postseason first, then the NFL, ranked college
    football, national TV, then the better teams."""
    score = 0.0
    if g.get("season_type") == "Postseason":
        score += 100
    if g.get("season_type") == "Preseason":
        score -= 60
    score += {"nfl": 50, "ncaaf": 10, "mlb": 5, "nba": 5, "nhl": 0}.get(key, 0)
    ranks = [g["away"]["rank"], g["home"]["rank"]]
    if key == "ncaaf":
        score += 40 if all(ranks) else (15 if any(ranks) else -20)
    if any(n.lower() in (g.get("tv") or "").lower() for n in NATIONAL_TV):
        score += 20
    score += 10 * (_winpct(g["away"]["record"]) + _winpct(g["home"]["record"]))
    return score


def pick_featured(now_pt, slates=None):
    """Return (key, game) for the homepage featured game: the best game still to
    start today (PT); if none, the best game on the next day that has games."""
    slates = slates or {}
    pool = []
    for key in FEATURE_SPORTS:
        data = slates.get(key)
        if data is None:
            try:
                data = fetch_sport(key, now_pt)
            except Exception as e:
                print(f"  [featured] {key} fetch failed: {e}")
                continue
        for g in data["events"]:
            if g["state"] == "pre" and g["start"] > now_pt:
                pool.append((key, g))
    if not pool:
        return None, None
    first_day = min(g["start"].astimezone(PT).date() for _, g in pool)
    day_pool = [(k, g) for k, g in pool if g["start"].astimezone(PT).date() == first_day]
    return max(day_pool, key=lambda kg: (feature_score(*kg), -kg[1]["start"].timestamp()))


def _logo(t, size=140):
    src = t.get("logo") or ""
    if src.startswith("https://a.espncdn.com/"):
        return f"https://a.espncdn.com/combiner/i?img={src.split('a.espncdn.com', 1)[1]}&w={size}&h={size}"
    return src


def featured_widget_html(key, g, now_pt):
    cfg = SPORTS[key]
    sport = cfg.get("short", cfg["label"])
    o = g.get("odds") or {}
    et = g["start"].astimezone(ET)
    when = f"{et:%I:%M %p}".lstrip("0") + " ET"
    day = g["start"].astimezone(PT).date()
    label = "Today's Featured Game" if day == now_pt.date() else f"Next Featured Game: {day:%A}"
    venue_bits = [f"{day:%B} {day.day}", g.get("venue"), g.get("notes") or g.get("season_type"), g.get("tv")]
    venue = " | ".join(esc(x) for x in venue_bits if x)

    def cls(v):
        if not v:
            return "fg-unset"
        return "fg-fav" if str(v).startswith("-") else "fg-dog"

    def team_box(t):
        rec = f'<div class="fg-team-record">{esc(t["record"])}</div>' if t.get("record") else ""
        return (f'<div class="fg-team">\n                                <img src="{esc(_logo(t))}" alt="{esc(t["abbr"])}" width="70" height="70" decoding="async">\n'
                f'                                <div class="fg-team-name">{esc(t["abbr"])}</div>\n                                {rec}\n                            </div>')

    def row(side, ou):
        t = g[side]
        sp = o.get(f"{side}_spread")
        ml = o.get(f"{side}_ml")
        tot = f"{ou} {o['total']}" if o.get("total") else "Not posted"
        return (f'<tr><td class="fg-team-cell"><img src="{esc(_logo(t, 48))}" alt="{esc(t["abbr"])}" width="24" height="24" loading="lazy"><span>{esc(t["abbr"])}</span></td>'
                f'<td class="{cls(sp)}">{esc(sp or "Not posted")}</td><td class="{cls(ml)}">{esc(ml or "Not posted")}</td>'
                f'<td style="color: #fff; font-weight: 600; font-size: 0.9rem;">{esc(tot)}</td></tr>')
    provider = o.get("provider") or "ESPN"
    hub = cfg["hub"]
    return f"""<!-- FEATURED-GAME-PREVIEW-START (auto-synced by scripts/sync_featured_game_preview.py; live ESPN slate via scripts/current_slate.py) -->
                    <!-- Header Banner -->
                    <div class="fg-header">
                        <div class="fg-header-top">
                            <span class="fg-header-label">{esc(label)}</span>
                            <span class="fg-time-badge">{esc(sport)} {esc(when)}</span>
                        </div>
                        <div class="fg-matchup">
                            {team_box(g["away"])}
                            <div class="fg-vs">{"vs" if g["neutral"] else "@"}</div>
                            {team_box(g["home"])}
                        </div>
                        <div class="fg-venue">{venue}</div>
                    </div>

                    <!-- Betting Lines Table ({esc(provider)} lines published by ESPN, refreshed {now_pt:%B} {now_pt.day} at {f"{now_pt:%I:%M %p}".lstrip("0")} PT) -->
                    <div class="fg-lines">
                        <table>
                            <thead>
                                <tr style="border-bottom: 2px solid rgba(239,97,0,0.5);">
                                    <th style="text-align: left;">Team</th>
                                    <th>{"Run line" if key == "mlb" else ("Puck line" if key == "nhl" else "Spread")}</th>
                                    <th>ML</th>
                                    <th>O/U</th>
                                </tr>
                            </thead>
                            <tbody>
                                {row("away", "O")}
                                {row("home", "U")}
                            </tbody>
                        </table>
                    </div>

                    <!-- Injuries -->
                    <div class="fg-injuries-bar">
                        <div class="fg-injuries-label">Lines and injuries</div>
                        <div class="fg-injuries-list">
                            <div>{esc(provider)} numbers via ESPN, can move before first pitch or kickoff.</div>
                            <div><a href="injury-report.html" style="color:#e8b85c">Full injury report</a></div>
                        </div>
                    </div>

                    <!-- Link to Featured Game Page - NEVER DELETE -->
                    <a href="{hub}#current-slate" class="fg-breakdown-btn">
                        <span>View Today's Full {esc(sport)} Slate &rarr;</span>
                    </a>
                    <!-- FEATURED-GAME-PREVIEW-END -->"""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", choices=sorted(SPORTS))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dump", help="write fetched slate JSON here (debug)")
    args = ap.parse_args(argv)
    now_pt = dt.datetime.now(PT)
    changed, failed = [], []
    dump = {}
    for key in args.only or SPORTS:
        try:
            data = fetch_sport(key, now_pt)
        except Exception as e:  # leave the page untouched on any feed failure
            print(f"  [{key}] ESPN fetch failed, pages left unchanged: {e}")
            failed.append(key)
            continue
        games, mode = slate_window(data, now_pt)
        print(f"  [{key}] {len(data['events'])} events from ESPN, showing {len(games)} ({mode})")
        dump[key] = [{"start": g["start"].isoformat(), "away": g["away"]["name"], "home": g["home"]["name"],
                      "state": g["state"], "odds": g["odds"]} for g in games]
        for p in SPORTS[key]["pages"]:
            path = os.path.join(ROOT, p)
            if not os.path.isfile(path):
                continue
            if args.dry_run:
                head, date_label, _ = render_block(key, data, now_pt)
                print(f"    {p}: {head}")
                continue
            if update_page(path, key, data, now_pt, p == SPORTS[key]["hub"]):
                changed.append(p)
    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            json.dump(dump, f, indent=1, default=str)
    print(f"[current_slate] updated {len(changed)} page(s): {', '.join(changed) or 'none'}"
          + (f"; feed failures: {', '.join(failed)}" if failed else ""))
    # Non-zero when any feed failed so the workflow run turns red; pages for the
    # sports that did update are still written before this returns.
    return 2 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
