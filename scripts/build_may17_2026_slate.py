from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://www.betlegendpicks.com"
DATE_ISO = "2026-05-17"

LOGOS = {
    "Marlins": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/mia.png",
    "Rays": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tb.png",
    "Orioles": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/bal.png",
    "Nationals": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/wsh.png",
    "Phillies": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/phi.png",
    "Pirates": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/pit.png",
    "Red Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/bos.png",
    "Braves": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/atl.png",
    "Reds": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/cin.png",
    "Guardians": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/cle.png",
    "Blue Jays": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tor.png",
    "Tigers": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/det.png",
    "Yankees": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/nyy.png",
    "Mets": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/nym.png",
    "Rangers": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/tex.png",
    "Astros": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/hou.png",
    "Cubs": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/chc.png",
    "White Sox": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/chw.png",
    "Brewers": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/mil.png",
    "Twins": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/min.png",
    "Royals": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/kc.png",
    "Cardinals": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/stl.png",
    "Diamondbacks": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/ari.png",
    "Rockies": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/col.png",
    "Giants": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sf.png",
    "Athletics": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/ath.png",
    "Dodgers": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/lad.png",
    "Angels": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/laa.png",
    "Padres": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sd.png",
    "Mariners": "https://a.espncdn.com/i/teamlogos/mlb/500/scoreboard/sea.png",
    "Cavaliers": "https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/cle.png",
    "Pistons": "https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/det.png",
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="ignore")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8", newline="\n")


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def set_head(doc: str, slug: str, title: str, description: str) -> str:
    url = f"{SITE}/{slug}"
    doc = re.sub(r'<link rel="canonical" href="[^"]+">', f'<link rel="canonical" href="{url}">', doc, count=1)
    doc = re.sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>", doc, count=1, flags=re.S)
    doc = re.sub(r'<meta name="description" content="[^"]*"\s*/?>', f'<meta name="description" content="{esc(description)}"/>', doc, count=1)
    keywords = f"{title.replace(' | BetLegend', '')}, May 17 2026, BetLegend Picks"
    doc = re.sub(r'<meta name="keywords" content="[^"]*"\s*/?>', f'<meta name="keywords" content="{esc(keywords)}">', doc, count=1)
    doc = re.sub(r"<script>window\.FORCED_PAGE_DATE = .*?</script>", f"<script>window.FORCED_PAGE_DATE = '{DATE_ISO}';</script>", doc, count=1)
    for prop, val in [("og:title", title), ("og:description", description), ("og:url", url)]:
        doc = re.sub(rf'<meta [^>]*property="{prop}"[^>]*>', f'<meta content="{esc(val)}" property="{prop}"/>', doc, count=1)
    for name, val in [("twitter:title", title), ("twitter:description", description)]:
        doc = re.sub(rf'<meta [^>]*name="{name}"[^>]*>', f'<meta content="{esc(val)}" name="{name}"/>', doc, count=1)
    schema = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": title.replace(" | BetLegend", ""),
        "description": description,
        "datePublished": "2026-05-17T00:00:00-04:00",
        "dateModified": "2026-05-17T00:00:00-04:00",
        "author": {"@type": "Organization", "name": "BetLegend Picks"},
        "publisher": {"@type": "Organization", "name": "BetLegend Picks", "logo": {"@type": "ImageObject", "url": f"{SITE}/newlogo.png"}},
        "image": f"{SITE}/newlogo.png",
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
    }
    return re.sub(r'<script type="application/ld\+json"[^>]*>.*?</script>', '<script type="application/ld+json">\n' + json.dumps(schema, separators=(",", ":")) + "\n</script>", doc, count=1, flags=re.S)


def split_matchup(title: str) -> tuple[str, str]:
    base = title.split(" - ", 1)[0]
    if " at " in base:
        a, h = base.split(" at ", 1)
        return a.strip(), h.strip()
    if " vs " in base:
        a, h = base.split(" vs ", 1)
        return a.strip(), h.strip()
    return "", ""


def logo(team: str) -> str:
    src = LOGOS.get(team)
    if src:
        return f'<img alt="{esc(team)} logo" class="team-logo" src="{src}"/>'
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z0-9]+", team)[:3]).upper() or "BL"
    return f'<div class="team-logo team-logo--badge" aria-label="{esc(team)} badge">{esc(initials)}</div>'


def card(num: str, title: str, meta: str, paragraphs: list[str], tag: str = "") -> str:
    away, home = split_matchup(title)
    tag_html = f'<div class="broadcast-badge national">{esc(tag)}</div>' if tag else ""
    body = "\n".join(f"<p>{p}</p>" for p in paragraphs)
    return f"""<article class="game-preview">
<div class="game-number">{esc(num)}</div>
{tag_html}
<div class="game-header">
{logo(away) if away else ""}
<div class="matchup-info"><h2>{esc(title)}</h2><span class="game-time">{esc(meta)}</span></div>
{logo(home) if home else ""}
</div>
<div class="preview-content">
{body}
</div>
</article>"""


def build_page(template: str, slug: str, title: str, description: str, badge: str, hero: str, subtitle: str, cards: list[str], calendar_js: str) -> str:
    doc = set_head(read(template), slug, title, description)
    doc = re.sub(
        r'href="/(?:canadiens-sabres-game-5-featured-game-of-the-day|wolves-vs-nuggets-nba-analysis-stats-preview-april-27-2026)\.html"',
        'href="/cavaliers-pistons-game-7-featured-game-of-the-day.html"',
        doc,
    )
    if ".team-logo--badge" not in doc:
        doc = doc.replace("</style>", ".team-logo--badge{display:flex;align-items:center;justify-content:center;border:1px solid rgba(255,255,255,.25);border-radius:50%;background:linear-gradient(135deg,rgba(253,80,0,.25),rgba(15,23,42,.9));color:#fff;font-family:var(--font-display);font-weight:800;letter-spacing:1px}\n</style>", 1)
    if ".page-wrapper" not in doc:
        doc = doc.replace("</style>", ".page-wrapper{display:grid;grid-template-columns:280px minmax(0,900px);gap:34px;max-width:1240px;margin:0 auto;padding:36px 24px 80px}.main-content{min-width:0}@media(max-width:950px){.page-wrapper{display:block}}\n</style>", 1)
    extra_script = '<script src="featured-games-data.js?v=20260517slate-featured"></script>\n' if calendar_js == "featured-games-calendar.js" else ""
    content = f"""
<header class="hero">
<div class="hero-badge">{esc(badge)}</div>
<h1>{esc(hero)}</h1>
<p>{esc(subtitle)}</p>
</header>

<div class="page-wrapper">
<aside class="calendar-sidebar">
<div class="calendar-box">
<div class="calendar-title">{esc(badge.split()[0])} Archive</div>
<div class="year-display">2026</div>
<select class="month-select" id="month-select"><option value="2026-05">May 2026</option></select>
<div class="calendar-weekdays"><span>Sun</span><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span></div>
<div class="calendar-days" id="calendar-days"></div>
</div>
</aside>
<main class="main-content">
<div class="mobile-archive"><div class="mobile-archive-title">{esc(badge.split()[0])} Archive</div><select class="mobile-archive-select" id="mobile-archive-select"></select></div>
{''.join(cards)}
</main>
</div>

<footer>
<p>&copy; 2026 BetLegend Picks. All Rights Reserved.</p>
<p><a href="privacy.html">Privacy Policy</a> | <a href="terms.html">Terms of Service</a> | <a href="contact.html">Contact</a></p>
</footer>
{extra_script}<script src="scripts/{calendar_js}?v=20260517slate"></script>
</body>"""
    return re.sub(r"<(?:header|section) class=\"hero\">.*?</body>", content, doc, count=1, flags=re.S)


MLB = [
    ("1", "Marlins at Rays", "12:15 PM ET | Tropicana Field | Eury Perez vs Drew Rasmussen | MIA 21-25, TB 29-15", ["MLB's official schedule lists Miami at Tampa Bay as the Peacock opener, with Eury Perez against Drew Rasmussen. The Rays own the stronger verified record at 29-15, but the matchup is not just record versus record; Perez gives Miami enough swing-and-miss upside to keep the first five innings competitive if his command is clean.", "Tampa Bay's betting case is structure. The Rays can turn a close game into their preferred late-inning shape with matchup relief, defense and enough contact to pressure Miami's run prevention. The Marlins need early traffic because chasing Tampa Bay's bullpen map from behind is a difficult script."], "Peacock"),
    ("2", "Orioles at Nationals", "1:35 PM ET | Nationals Park | Brandon Young vs Miles Mikolas | BAL 20-26, WSH 23-23", ["MLB lists Baltimore at 20-26 and Washington at 23-23, with Brandon Young opposite Miles Mikolas. That makes this regional game more balanced than the Orioles name value might imply. Washington's even record and home park give the Nationals a real path if Mikolas keeps the game orderly.", "Baltimore's path is pressure before Mikolas can settle into his contact-management rhythm. The Orioles need traffic and extra-base contact, not just isolated loud swings. Washington need the opposite: quick outs, cleaner defensive innings and enough situational offense to make Baltimore manage leverage by the sixth."], ""),
    ("3", "Phillies at Pirates", "1:35 PM ET | PNC Park | Zack Wheeler vs Paul Skenes | PHI 23-23, PIT 24-22", ["Wheeler-Skenes is the premier pitching matchup of the MLB slate. MLB lists Philadelphia at 23-23 and Pittsburgh at 24-22, so the standings gap is tiny and the starting-pitcher layer carries the preview. Wheeler gives the Phillies a veteran ace with workload stability; Skenes gives Pittsburgh a power arm capable of changing the whole scoring environment.", "The betting read starts with run scarcity and bullpen timing. Philadelphia's lineup has to turn deep counts into pitch-count pressure because pure contact against Skenes is not enough. Pittsburgh's offense cannot waste early base runners; if Wheeler is allowed to cruise, the Pirates may need near-perfect defense and late-inning sequencing."], "Marquee"),
    ("4", "Red Sox at Braves", "1:35 PM ET | Truist Park | Brayan Bello vs Grant Holmes | BOS 19-26, ATL 31-15", ["Atlanta enter this game with MLB listing a 31-15 record, the clearest team-form edge on the board. Boston are 19-26 and send Brayan Bello into a road park where mistakes can turn into crooked innings quickly. Grant Holmes does not need to dominate if the Braves' lineup controls counts and keeps pressure on Boston's defense.", "The Red Sox need Bello to keep the first half calm. If Atlanta are hitting with runners aboard by the second trip through the order, Truist Park can become a difficult place to chase. Boston's counter is disciplined at-bats and early traffic, because a low-event game is much more manageable than a Braves depth contest."], ""),
    ("5", "Reds at Guardians", "1:40 PM ET | Progressive Field | Brady Singer vs Gavin Williams | CIN 24-22, CLE 25-22", ["Cincinnati-Cleveland is a tight Ohio matchup, with MLB listing the Reds at 24-22 and the Guardians at 25-22. Brady Singer against Gavin Williams creates a game where the winner likely controls contact quality and avoids free traffic. The rivalry tag is useful, but the handicap is more about run prevention than emotion.", "Cincinnati need speed and pressure without empty aggression. Cleveland's route is cleaner situational baseball: defend, keep the ball in the park and let bullpen leverage matter. If Williams gives Cleveland a stable first half, the Guardians can make this a low-margin home game on their terms."], ""),
    ("6", "Blue Jays at Tigers", "1:40 PM ET | Comerica Park | Kevin Gausman vs Jack Flaherty | TOR 20-25, DET 20-26", ["Toronto at Detroit is a veteran-pitcher game in a park that can mute cheap power. MLB lists Kevin Gausman against Jack Flaherty, with Toronto at 20-25 and Detroit at 20-26. The records are nearly identical, so the matchup leans into command, sequencing and whether either lineup can create sustained traffic.", "Comerica Park rewards teams that can hit gaps and run the bases cleanly. Toronto need walks and hard contact ahead of their middle order, while Detroit need to make Gausman work from the stretch. If both starters are efficient, this becomes a bullpen and defense preview more than a slugging contest."], ""),
    ("7", "Yankees at Mets", "1:40 PM ET | Citi Field | Elmer Rodriguez vs Freddy Peralta | NYY 28-18, NYM 19-26", ["The Subway Series carries the biggest market attention of the afternoon. MLB lists the Yankees at 28-18 and the Mets at 19-26, with Elmer Rodriguez opposite Freddy Peralta. The Yankees have the stronger verified record, but Citi Field and Peralta's strikeout profile can narrow the gap if the Mets keep traffic down.", "The Mets' betting path is command and clean innings. If Peralta avoids walks, the game can stay low-margin long enough for home-field tension to matter. The Yankees need runners before the big swings; isolated power is useful, but sustained pressure is what forces the Mets away from their preferred pitching plan."], "Subway"),
    ("8", "Rangers at Astros", "2:10 PM ET | Daikin Park | Nathan Eovaldi vs Peter Lambert | TEX 21-24, HOU 19-28", ["Texas-Houston is a division game with a sharper pitching lean than the records suggest. MLB lists Nathan Eovaldi for Texas and Peter Lambert for Houston, with the Astros sitting at 19-28. That Houston record makes the home side more urgent, but Eovaldi gives Texas the cleaner starter profile.", "The Rangers need to turn that starter edge into early control. Houston's best route is to make Eovaldi cover stressful outs and get the game into a home bullpen plan without chasing a deficit. If Texas build traffic early, Houston's already-thin full-season profile becomes more exposed."], ""),
    ("9", "Cubs at White Sox", "2:10 PM ET | Rate Field | Colin Rea vs Erick Fedde | CHC 29-17, CWS 23-22", ["The Chicago rivalry has a real standings split, with MLB listing the Cubs at 29-17 and the White Sox at 23-22. Colin Rea against Erick Fedde is not a glamour pairing, which makes team structure and lineup depth more important. The Cubs' edge is that they can win more types of games.", "The White Sox need a first-half answer. If Fedde is efficient and the Sox put runners in motion, the rivalry can tighten. If the Cubs grind at-bats and force the Sox to defend under pressure, the better-recorded team can let depth show up across nine innings."], ""),
    ("10", "Brewers at Twins", "2:10 PM ET | Target Field | Robert Gasser vs Bailey Ober | MIL 26-17, MIN 20-26", ["Milwaukee-Minnesota is a contrast game. MLB lists the Brewers at 26-17 and the Twins at 20-26, with Robert Gasser against Bailey Ober. Milwaukee's stronger record reflects a cleaner full-team profile, but Target Field can give Minnesota a path if Ober supplies length and the lineup generates early support.", "The Brewers need to keep Minnesota from building a loud inning. Milwaukee's contact-management and bullpen structure play well when the game stays contained. The Twins need pressure from more than the obvious bats, because isolated production will not be enough against a Brewers team comfortable winning late."], ""),
    ("11", "Royals at Cardinals", "2:15 PM ET | Busch Stadium | Stephen Kolek vs Andre Pallante | KC 19-27, STL 27-18", ["St. Louis enter the cross-state game with MLB listing a 27-18 record, while Kansas City sit 19-27. Stephen Kolek against Andre Pallante makes this less about ace dominance and more about who controls contact and baserunners. Busch Stadium can flatten impatient swings, which gives the Royals a route if they stay disciplined.", "The Cardinals' edge is stability. If Pallante keeps the ball on the ground and St. Louis creates traffic, the game can settle into the home team's preferred shape. Kansas City need speed, pressure and clean defense, because falling behind turns the matchup into a depth comparison they do not want."], ""),
    ("12", "Diamondbacks at Rockies", "3:10 PM ET | Coors Field | Michael Soroka vs Michael Lorenzen | ARI 21-23, COL 18-28", ["Arizona-Colorado is the run-environment game because MLB lists it at Coors Field. The Diamondbacks are 21-23 and the Rockies are 18-28, with Michael Soroka opposite Michael Lorenzen. The records matter, but Denver's conditions make bullpen exposure and inning management the real handicap.", "Arizona need pressure without chasing the park. Line drives, walks and traffic matter more than trying to lift every pitch. Colorado need early offense because falling behind at Coors is survivable only if the pitching staff does not have to cover too many stressful outs."], "Coors"),
    ("13", "Giants at Athletics", "4:05 PM ET | Sutter Health Park | Adrian Houser vs Jeffrey Springs | SF 19-27, ATH 23-22", ["The Bay Area matchup moves through Sacramento, with MLB listing San Francisco at 19-27 and the Athletics at 23-22. Adrian Houser against Jeffrey Springs gives the Athletics the cleaner left-handed starter profile, but the setting matters because Sutter Health Park can create different defensive and ball-flight reads.", "San Francisco's route is order: patient at-bats, clean defense and keeping the Athletics from stacking a big inning. Oakland's route is pressure early. If the A's get Springs a lead, they can make the Giants chase a game state that has not been friendly to San Francisco's full-season record."], ""),
    ("14", "Dodgers at Angels", "4:07 PM ET | Angel Stadium | Roki Sasaki vs Grayson Rodriguez | LAD 28-18, LAA 16-30", ["The Freeway Series has a huge record split, with MLB listing the Dodgers at 28-18 and the Angels at 16-30. Roki Sasaki against Grayson Rodriguez is the most watchable late-afternoon pitching matchup by pure stuff. The Dodgers have lineup depth, but the Angels can make it interesting if Rodriguez keeps them in the game early.", "Los Angeles' path is zone control and depth. The Dodgers do not need to chase if they keep forcing the Angels to record extra outs under stress. The Angels need clean defense, early traffic and a run-prevention plan that does not expose the bullpen too soon."], "Freeway"),
    ("15", "Padres at Mariners", "7:20 PM ET | T-Mobile Park | Lucas Giolito vs George Kirby | SD 27-18, SEA 22-25", ["Padres-Mariners is the NBC night game and the cleanest late pitching environment. MLB lists San Diego at 27-18 and Seattle at 22-25, with Lucas Giolito opposite George Kirby. T-Mobile Park rewards command, defense and fly-ball management, so this is less about raw star power than contact quality.", "Seattle need Kirby to control tempo and keep San Diego from layering base runners in front of the dangerous bats. The Padres need their bottom-half plate appearances to matter, because Seattle can pitch around isolated threats. If the game stays tight into the seventh, bullpen leverage and outfield defense become the deciding lanes."], "NBC"),
]

NBA = [
    ("1", "Cavaliers at Pistons - Game 7", "8:00 PM ET | Little Caesars Arena | Prime Video | Series tied 3-3", ["NBA.com lists Cleveland at Detroit for Sunday May 17 at 8 ET on Prime Video, with the series tied 3-3 after Detroit's 115-94 Game 6 road win. That result changes the tone completely. Cleveland had a closeout chance at home and missed it badly; Detroit now gets Game 7 in Little Caesars Arena after forcing the series back home.", "The tactical read starts with Detroit's defense. If the Pistons keep Cleveland out of early rhythm, the crowd becomes part of every half-court possession. Cleveland need composure, spacing and a cleaner response to Detroit's physicality than they showed in Game 6. This is not a spot for vague momentum talk; it is a shot-quality game, a turnover game and a defensive-rebounding game.", "Detroit's 60-22 regular-season record, listed by ESPN's scoreboard, gives the Pistons the home-court context that matters in a Game 7. Cleveland's 52-30 record is still elite, but the Cavaliers have to win on the road after absorbing the emotional hit of a 21-point loss. Watch the first six minutes: if Cleveland get organized touches and avoid live-ball turnovers, the game settles; if Detroit create early runouts, the building can tilt fast."], "Game 7"),
]

FEATURED = [
    ("Featured", "Cavaliers at Pistons - Game 7", "8:00 PM ET | Little Caesars Arena | Prime Video | Series tied 3-3", ["The Featured Game of the Day for May 17 is Cavaliers at Pistons because it is the only NBA game on the board and the stakes are clean: Game 7, Little Caesars Arena, series tied 3-3. NBA.com lists the matchup for Sunday May 17 at 8 ET on Prime Video after Detroit won Game 6 in Cleveland, 115-94, to force the deciding game.", "Detroit's position is powerful but not comfortable. ESPN's scoreboard lists the Pistons at 60-22 and the Cavaliers at 52-30, which explains why Game 7 is in Detroit, but the matchup is still tight enough that home court cannot be treated like a result. The Pistons need to turn the crowd into defensive energy without getting reckless on offense.", "Cleveland's job is to make this game normal again. After losing Game 6 by 21, the Cavaliers need early half-court execution, clean spacing and defensive rebounding. If they let Detroit run off live-ball turnovers, the game can become a home-crowd avalanche. If Cleveland control tempo, the experience and shot-making on the roster can still travel.", "The central betting-intelligence read is shot quality. Detroit want downhill pressure, second chances and possessions that make Cleveland rotate multiple times. Cleveland want a cleaner offensive geometry: paint touch, kickout, second-side action and no wasted possessions. Game 7s often get described through emotion, but the cleaner team in the middle possessions usually owns the final five minutes.", "No official pick is being attached here because this page is the Featured Game preview surface, not a Google Sheet pick card. The correct read is process: watch turnovers, defensive rebounds, free-throw pressure and whether Cleveland's first unit can get organized against Detroit's early physicality. If Detroit win those categories, Little Caesars Arena can decide the series. If Cleveland win them, the Cavaliers can take the crowd out of the game and turn it into a possession-by-possession test."], "Featured Game"),
]

SOCCER = [
    ("1", "Paris FC vs PSG", "Ligue 1 | Sunday, May 17", ["Soccerbase lists Paris FC vs PSG on the May 17 Ligue 1 board, and that local context is the headline soccer angle of the day. PSG's talent edge is obvious, but the handicap is not just name power; Paris FC need compact defensive spacing and enough counter threat to stop PSG from playing the match entirely in the attacking half.", "The useful betting read is pressure resistance. If Paris FC cannot play through the first wave, PSG can turn territory into repeated box entries. If the underdog can break pressure and win set pieces, the match can stay more awkward than the badge gap suggests."], ""),
    ("2", "PSV Eindhoven vs FC Twente", "Eredivisie | Sunday, May 17", ["Soccerbase lists PSV-Twente on a full Netherlands League slate. PSV at home usually means tempo, width and sustained possession, but Twente's route is to make central progression uncomfortable and force PSV to settle for lower-quality service from wide areas.", "The match should be read through first-half territory. If PSV pin Twente back early, the game can become a wave of restarts and second balls. If Twente keep possession spells alive, the home side have to solve a more balanced tactical problem."], ""),
    ("3", "Heerenveen vs Ajax", "Eredivisie | Sunday, May 17", ["Heerenveen-Ajax is another Soccerbase-listed Netherlands fixture with a clear brand edge but a tricky away setting. Ajax need to control transitions and avoid turning the match into a home-underdog energy spot. Heerenveen's path is fast counters and set pieces.", "For Ajax, patience matters. A slow start is not fatal if they keep field position and shot quality in their favor. For Heerenveen, the first goal changes everything because it lets the home side defend space instead of chasing the ball."], ""),
    ("4", "Fenerbahce vs Eyupspor", "Turkish Super Lig | Sunday, May 17", ["Soccerbase lists Fenerbahce-Eyupspor on the Turkish Super Lig board. Fenerbahce's home advantage is the obvious starting point, but the match still depends on how efficiently the favorite turns possession into real penalty-area pressure.", "Eyupspor need discipline in the first thirty minutes. If they concede territory and fouls around the box, the match can become a set-piece and second-ball grind. If they survive that opening wave, the favorite has to show patience rather than forcing low-value shots."], ""),
    ("5", "Kasimpasa vs Galatasaray", "Turkish Super Lig | Sunday, May 17", ["Kasimpasa-Galatasaray gives the soccer page a second Turkish fixture with a different tactical feel. Galatasaray's edge is attacking depth, but an away match against a side willing to transition can become uncomfortable if the favorite is careless with rest defense.", "The handicap is transition control. Galatasaray need attacks that end with shots or restarts, not turnovers that feed Kasimpasa counters. Kasimpasa need to make the match vertical enough that Galatasaray cannot simply manage possession and wait for the breakthrough."], ""),
]


def main() -> None:
    pages = [
        ("sunday-may-17-full-mlb-board-skenes-wheeler-sasaki-kirby.html", "mlb-previews.html", "mlb-previews.html", "MLB Sunday Preview: Full 15-Game Board for May 17, 2026 | BetLegend", "MLB Sunday preview for May 17, 2026 with all 15 official games, verified probable pitchers, team records, venues and matchup analysis.", "MLB Sunday - May 17", "MLB Sunday Preview: Full 15-Game Board", "Skenes-Wheeler, Subway Series, Freeway Series, Coors Field and the NBC night game in Seattle.", [card(*g) for g in MLB], "mlb-calendar.js"),
        ("cavaliers-pistons-game-7-eastern-semis-nba-may-17-2026.html", "nba-previews.html", "nba-previews.html", "NBA Game 7 Preview: Cavaliers at Pistons for May 17, 2026 | BetLegend", "NBA playoff Game 7 preview for May 17, 2026 with Cavaliers at Pistons, series tied 3-3, 8 ET on Prime Video from Little Caesars Arena.", "NBA Sunday - May 17", "Cavaliers at Pistons Game 7 Preview", "Detroit forced Game 7 with a 115-94 road win. Cleveland has to answer in Little Caesars Arena.", [card(*g) for g in NBA], "nba-calendar.js"),
        ("cavaliers-pistons-game-7-featured-game-of-the-day.html", "cavaliers-pistons-game-7-featured-game-of-the-day.html", "pistons-cavaliers-game-6-featured-game-of-the-day.html", "Cavaliers at Pistons Game 7 Featured Game of the Day | BetLegend", "Featured Game of the Day for May 17, 2026: Cavaliers at Pistons Game 7, series tied 3-3, 8 ET on Prime Video.", "Featured Game of the Day", "Cavaliers at Pistons Game 7", "Detroit has home court, Cleveland has to respond, and one Eastern semifinal season ends tonight.", [card(*g) for g in FEATURED], "featured-games-calendar.js"),
        ("psg-ajax-galatasaray-sunday-soccer-may-17-2026.html", "soccer-previews.html", "soccer-previews.html", "Soccer Sunday Preview: PSG, Ajax, PSV and Galatasaray for May 17, 2026 | BetLegend", "Soccer preview for May 17, 2026 using verified Soccerbase fixtures from Ligue 1, Eredivisie and Turkish Super Lig.", "Soccer Sunday - May 17", "Soccer Sunday Preview: PSG, Ajax, PSV and Galatasaray", "A focused May 17 soccer board from the verified Soccerbase fixture list.", [card(*g) for g in SOCCER], "soccer-calendar.js"),
    ]
    for slug, hub, template, title, desc, badge, hero, subtitle, cards, cal in pages:
        built = build_page(template, slug, title, desc, badge, hero, subtitle, cards, cal)
        write(slug, built)
        if hub != slug:
            write(hub, build_page(template, hub, title, desc, badge, hero, subtitle, cards, cal))


if __name__ == "__main__":
    main()
