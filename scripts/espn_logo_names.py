"""ESPN logo abbreviation guard for generated pages (2026-10-31).

ESPN serves team logos only by abbreviation (e.g. teamlogos/mlb/500/scoreboard/ari.png).
Some data paths handed full team names ("arizona diamondbacks") to the logo URL builders,
which produced hundreds of 404 images on handicapping-hub archive pages. espn_abbr()
maps a full team name to the ESPN abbreviation and leaves real abbreviations unchanged;
espn_logo() returns a URL that always resolves (league logo when the team is unknown).
"""

MLB = {"arizona diamondbacks": "ARI", "athletics": "ATH", "atlanta braves": "ATL", "baltimore orioles": "BAL", "boston red sox": "BOS", "chicago cubs": "CHC", "chicago white sox": "CHW", "cincinnati reds": "CIN", "cleveland guardians": "CLE", "colorado rockies": "COL", "detroit tigers": "DET", "houston astros": "HOU", "kansas city royals": "KC", "los angeles angels": "LAA", "los angeles dodgers": "LAD", "miami marlins": "MIA", "milwaukee brewers": "MIL", "minnesota twins": "MIN", "new york mets": "NYM", "new york yankees": "NYY", "philadelphia phillies": "PHI", "pittsburgh pirates": "PIT", "san diego padres": "SD", "san francisco giants": "SF", "seattle mariners": "SEA", "st. louis cardinals": "STL", "tampa bay rays": "TB", "texas rangers": "TEX", "toronto blue jays": "TOR", "washington nationals": "WSH"}
NBA = {"atlanta hawks": "ATL", "boston celtics": "BOS", "brooklyn nets": "BKN", "charlotte hornets": "CHA", "chicago bulls": "CHI", "cleveland cavaliers": "CLE", "dallas mavericks": "DAL", "denver nuggets": "DEN", "detroit pistons": "DET", "golden state warriors": "GS", "houston rockets": "HOU", "indiana pacers": "IND", "la clippers": "LAC", "los angeles lakers": "LAL", "memphis grizzlies": "MEM", "miami heat": "MIA", "milwaukee bucks": "MIL", "minnesota timberwolves": "MIN", "new orleans pelicans": "NO", "new york knicks": "NY", "oklahoma city thunder": "OKC", "orlando magic": "ORL", "philadelphia 76ers": "PHI", "phoenix suns": "PHX", "portland trail blazers": "POR", "sacramento kings": "SAC", "san antonio spurs": "SA", "toronto raptors": "TOR", "utah jazz": "UTAH", "washington wizards": "WSH"}
NHL = {"anaheim ducks": "ANA", "boston bruins": "BOS", "buffalo sabres": "BUF", "calgary flames": "CGY", "carolina hurricanes": "CAR", "chicago blackhawks": "CHI", "colorado avalanche": "COL", "columbus blue jackets": "CBJ", "dallas stars": "DAL", "detroit red wings": "DET", "edmonton oilers": "EDM", "florida panthers": "FLA", "los angeles kings": "LA", "minnesota wild": "MIN", "montreal canadiens": "MTL", "nashville predators": "NSH", "new jersey devils": "NJ", "new york islanders": "NYI", "new york rangers": "NYR", "ottawa senators": "OTT", "philadelphia flyers": "PHI", "pittsburgh penguins": "PIT", "san jose sharks": "SJ", "seattle kraken": "SEA", "st. louis blues": "STL", "tampa bay lightning": "TB", "toronto maple leafs": "TOR", "utah mammoth": "UTAH", "vancouver canucks": "VAN", "vegas golden knights": "VGK", "washington capitals": "WSH", "winnipeg jets": "WPG"}
NFL = {"arizona cardinals": "ARI", "atlanta falcons": "ATL", "baltimore ravens": "BAL", "buffalo bills": "BUF", "carolina panthers": "CAR", "chicago bears": "CHI", "cincinnati bengals": "CIN", "cleveland browns": "CLE", "dallas cowboys": "DAL", "denver broncos": "DEN", "detroit lions": "DET", "green bay packers": "GB", "houston texans": "HOU", "indianapolis colts": "IND", "jacksonville jaguars": "JAX", "kansas city chiefs": "KC", "las vegas raiders": "LV", "los angeles chargers": "LAC", "los angeles rams": "LAR", "miami dolphins": "MIA", "minnesota vikings": "MIN", "new england patriots": "NE", "new orleans saints": "NO", "new york giants": "NYG", "new york jets": "NYJ", "philadelphia eagles": "PHI", "pittsburgh steelers": "PIT", "san francisco 49ers": "SF", "seattle seahawks": "SEA", "tampa bay buccaneers": "TB", "tennessee titans": "TEN", "washington commanders": "WSH"}

_TABLES = {"mlb": MLB, "nba": NBA, "nhl": NHL, "nfl": NFL}
_ALIASES = {"oakland athletics": "ATH", "utah hockey club": "UTAH", "la clippers": "LAC"}


def espn_abbr(league, value):
    """Return the lowercase ESPN abbreviation for value (abbreviation or full team name), or ''."""
    v = (value or "").strip()
    if not v:
        return ""
    key = " ".join(v.lower().split())
    table = _TABLES.get(league.lower(), {})
    if key in table:
        return table[key].lower()
    if key in _ALIASES:
        return _ALIASES[key].lower()
    if " " not in key and len(key) <= 5 and key.isalnum():
        return key
    return ""


def espn_logo(league, value):
    """Scoreboard logo URL for a pro team; falls back to the league logo instead of a dead URL."""
    lg = league.lower()
    ab = espn_abbr(lg, value)
    if ab:
        return f"https://a.espncdn.com/i/teamlogos/{lg}/500/scoreboard/{ab}.png"
    return f"https://a.espncdn.com/i/teamlogos/leagues/500/{lg}.png"
