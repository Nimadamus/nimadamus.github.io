from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAV = """
<header class="nav">
  <a class="brand" href="index.html"><img src="newlogo.png" alt="">Bet<span>Legend</span></a>
  <nav>
    <a href="mlb-previews.html">MLB</a>
    <a href="nhl-previews.html">NHL</a>
    <a href="nba-previews.html">NBA</a>
    <a href="nfl.html">NFL</a>
    <a href="soccer-previews.html">Soccer</a>
    <a href="records.html">Records</a>
    <a href="betting-calculators.html">Tools</a>
  </nav>
  <a class="trial" href="free-trial-info.html">Free Trial</a>
</header>
"""

FOOTER = """
<footer>
  <strong>BetLegend</strong>
  <span>Preview only. The live homepage has not been changed.</span>
  <a href="records.html">Records</a>
  <a href="best-bets-today.html">Best Bets</a>
  <a href="handicapping-hub.html">Handicapping Hub</a>
  <a href="sitemap.xml">Sitemap</a>
</footer>
"""

BASE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title}</title>
<link rel="icon" href="newlogo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{font_url}" rel="stylesheet">
<style>
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:{bg};color:{text};font-family:{font};line-height:1.45}}
a{{color:inherit;text-decoration:none}}
img{{display:block;max-width:100%}}
.note{{background:{note_bg};color:{note_text};text-align:center;padding:8px 16px;font-size:13px;font-weight:800}}
.nav{{position:sticky;top:0;z-index:20;min-height:82px;padding:0 34px;display:flex;align-items:center;justify-content:space-between;gap:30px;background:{nav_bg};backdrop-filter:blur(18px);border-bottom:1px solid {line}}}
.brand{{display:flex;align-items:center;gap:12px;font-size:28px;font-weight:900;white-space:nowrap}}
.brand img{{width:46px;height:46px;border-radius:7px}}
.brand span{{color:{accent}}}
.nav nav{{display:flex;gap:34px;align-items:center;font-size:15px;font-weight:850;letter-spacing:.01em}}
.nav nav a{{color:{nav_text}}}
.nav nav a:hover{{color:#fff}}
.trial,.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 18px;border-radius:6px;border:1px solid {line};font-weight:850;background:{button_bg};color:{button_text}}}
.btn.secondary{{background:transparent;color:{text}}}
.hero{{position:relative;min-height:690px;overflow:hidden;border-bottom:1px solid {line}}}
.hero:before{{content:"";position:absolute;inset:0;background:{hero_overlay},url("{hero_img}") {hero_pos}/cover no-repeat}}
.hero:after{{content:"";position:absolute;left:0;right:0;bottom:0;height:180px;background:linear-gradient(180deg,transparent,{bg})}}
.hero-inner{{position:relative;z-index:1;max-width:1320px;margin:0 auto;min-height:690px;padding:92px 30px 56px;display:grid;grid-template-columns:minmax(0,680px) 420px;gap:54px;align-items:end}}
.kicker{{display:inline-flex;align-items:center;gap:8px;border:1px solid {accent_soft};background:{accent_wash};color:{kicker};border-radius:999px;padding:8px 12px;font-size:13px;font-weight:900}}
.kicker i{{width:8px;height:8px;border-radius:50%;background:{green};box-shadow:0 0 0 6px {green_soft}}}
h1{{margin:18px 0 16px;font-size:clamp(42px,5.4vw,76px);line-height:.96;letter-spacing:0;font-weight:900;max-width:720px}}
.lead{{max-width:610px;margin:0;color:{muted_light};font-size:18px}}
.actions{{display:flex;gap:12px;flex-wrap:wrap;margin-top:28px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:36px;max-width:620px}}
.stat{{border:1px solid {line};background:{panel_alpha};border-radius:8px;padding:15px}}
.stat b{{display:block;font-size:26px;line-height:1}}
.stat span{{display:block;margin-top:8px;color:{muted};font-size:12px;font-weight:900;text-transform:uppercase}}
.ticket{{border:1px solid {line_bright};background:{ticket_bg};box-shadow:0 28px 80px rgba(0,0,0,.42);border-radius:10px;overflow:hidden}}
.ticket-head{{display:flex;justify-content:space-between;gap:16px;padding:18px;border-bottom:1px solid {line};background:{ticket_head}}}
.ticket-head strong{{font-size:15px}}
.ticket-head span{{color:{muted};font-size:13px;font-weight:800}}
.ticket-body{{padding:18px}}
.match{{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center;text-align:center;margin-bottom:18px}}
.team{{border:1px solid {line};background:{team_bg};border-radius:8px;padding:14px 8px}}
.team img{{width:66px;height:66px;object-fit:cover;border-radius:8px;margin:0 auto 8px}}
.team b{{font-size:16px}}
.vs{{color:{accent};font-weight:900}}
.markets{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}}
.market{{border:1px solid {line};background:{team_bg};border-radius:8px;padding:12px}}
.market span{{display:block;color:{muted};font-size:12px;font-weight:900;text-transform:uppercase}}
.market b{{display:block;margin-top:4px;font-size:18px}}
.section{{max-width:1320px;margin:0 auto;padding:56px 30px}}
.section-head{{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:22px}}
h2{{margin:0;font-size:38px;line-height:1.08;font-weight:900;letter-spacing:0}}
.sub{{margin:8px 0 0;color:{muted};font-size:16px;max-width:720px}}
.board{{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:16px}}
.card,.panel{{overflow:hidden;border:1px solid {line};background:{panel};border-radius:9px}}
.card img{{width:100%;height:220px;object-fit:cover}}
.card.feature img{{height:315px}}
.card-body{{padding:18px}}
.tag{{display:inline-flex;border-radius:999px;padding:5px 9px;background:{accent_wash};color:{kicker};font-size:12px;font-weight:900;text-transform:uppercase}}
.tag.blue{{background:rgba(78,161,255,.16);color:#b8dcff}}
.tag.red{{background:rgba(231,90,90,.16);color:#ffc0c0}}
.card h3{{margin:12px 0 8px;font-size:23px;line-height:1.12}}
.card:not(.feature) h3{{font-size:20px}}
.card p,.panel p{{margin:0;color:{muted};font-size:15px}}
.proof{{background:{proof_bg};color:{proof_text}}}
.proof .section{{display:grid;grid-template-columns:1.1fr repeat(3,1fr);gap:18px;align-items:stretch}}
.proof h2{{font-size:34px}}
.proof p{{color:{proof_muted};margin:8px 0 0}}
.proof-box{{border:1px solid {proof_line};background:{proof_box};border-radius:9px;padding:20px}}
.proof-box b{{display:block;font-size:28px}}
.proof-box span{{display:block;margin-top:8px;color:{proof_muted};font-size:12px;font-weight:900;text-transform:uppercase}}
.lower{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.panel{{padding:24px}}
.grid-links{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:16px}}
.grid-links a{{border:1px solid {line};background:{team_bg};border-radius:7px;padding:12px;color:{nav_text};font-size:14px;font-weight:850}}
.media-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}
.media{{position:relative;height:190px;border-radius:9px;overflow:hidden;border:1px solid {line};background:#111}}
.media img{{width:100%;height:100%;object-fit:cover;opacity:.78;transition:.2s ease}}
.media:hover img{{opacity:.95;transform:scale(1.04)}}
.media b{{position:absolute;left:14px;right:14px;bottom:14px;z-index:1;font-size:19px;text-shadow:0 2px 18px #000}}
.media:after{{content:"";position:absolute;inset:0;background:linear-gradient(180deg,transparent 35%,rgba(0,0,0,.86))}}
footer{{max-width:1320px;margin:0 auto;padding:38px 30px 50px;border-top:1px solid {line};display:flex;gap:24px;flex-wrap:wrap;color:{muted};font-size:14px}}
footer strong{{color:{text}}}
footer a{{font-weight:850;color:{nav_text}}}
@media(max-width:1080px){{.nav{{flex-wrap:wrap;padding:14px 22px}}.nav nav{{order:3;width:100%;gap:18px;flex-wrap:wrap}}.hero-inner{{grid-template-columns:1fr;min-height:0}}.ticket{{max-width:540px}}.board,.proof .section,.lower{{grid-template-columns:1fr}}.media-row{{grid-template-columns:repeat(2,1fr)}}}}
@media(max-width:680px){{.nav{{padding:12px 16px}}.brand{{font-size:23px}}.trial{{display:none}}.hero{{min-height:0}}.hero-inner{{padding:58px 18px 42px}}.stats,.markets,.match,.grid-links,.media-row{{grid-template-columns:1fr}}.section{{padding:42px 18px}}h1{{font-size:40px}}h2{{font-size:30px}}.card.feature img,.card img{{height:220px}}}}
</style>
</head>
<body>
<div class="note">Preview only. Nothing here changes the live homepage.</div>
"""


def page(config: dict, body: str) -> str:
    return BASE_HEAD.format(**config) + NAV + body + FOOTER + "\n</body>\n</html>\n"


common = {
    "font_url": "https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600;700;800;900&display=swap",
    "font": "Barlow, Arial, sans-serif",
    "green": "#38c172",
    "green_soft": "rgba(56,193,114,.16)",
}

stadium = {
    **common,
    "title": "BetLegend Preview A - Stadium Command Center",
    "bg": "#090d12",
    "text": "#f8fafc",
    "note_bg": "#f3ecdc",
    "note_text": "#101820",
    "nav_bg": "rgba(9,13,18,.88)",
    "nav_text": "#dbe4ed",
    "line": "rgba(255,255,255,.12)",
    "line_bright": "rgba(255,255,255,.2)",
    "accent": "#d9a441",
    "accent_soft": "rgba(217,164,65,.42)",
    "accent_wash": "rgba(217,164,65,.14)",
    "kicker": "#f6dda0",
    "muted": "#9aa9b8",
    "muted_light": "#d8e2ec",
    "button_bg": "#d9a441",
    "button_text": "#101820",
    "panel_alpha": "rgba(17,24,32,.78)",
    "ticket_bg": "rgba(17,24,32,.94)",
    "ticket_head": "rgba(255,255,255,.05)",
    "team_bg": "#0d141b",
    "panel": "#111a23",
    "hero_img": "images/nfl-betting-boom.png",
    "hero_pos": "center center",
    "hero_overlay": "linear-gradient(90deg,rgba(9,13,18,.97) 0%,rgba(9,13,18,.80) 42%,rgba(9,13,18,.28) 72%,rgba(9,13,18,.58) 100%)",
    "proof_bg": "#f3ecdc",
    "proof_text": "#101820",
    "proof_muted": "#55606b",
    "proof_line": "rgba(16,24,32,.14)",
    "proof_box": "#fffaf0",
}

market = {
    **common,
    "title": "BetLegend Preview B - Data Sportsbook",
    "bg": "#050b14",
    "text": "#f4fbff",
    "note_bg": "#071825",
    "note_text": "#bfeaff",
    "nav_bg": "rgba(5,11,20,.9)",
    "nav_text": "#c8e6f5",
    "line": "rgba(102,207,255,.16)",
    "line_bright": "rgba(102,207,255,.28)",
    "accent": "#51d6ff",
    "accent_soft": "rgba(81,214,255,.42)",
    "accent_wash": "rgba(81,214,255,.13)",
    "kicker": "#bbf0ff",
    "muted": "#8daabd",
    "muted_light": "#cbe1ef",
    "button_bg": "#51d6ff",
    "button_text": "#061018",
    "panel_alpha": "rgba(7,20,31,.78)",
    "ticket_bg": "rgba(7,20,31,.94)",
    "ticket_head": "rgba(81,214,255,.06)",
    "team_bg": "#081725",
    "panel": "#071522",
    "hero_img": "images/ai-moneyball.png",
    "hero_pos": "center center",
    "hero_overlay": "linear-gradient(90deg,rgba(5,11,20,.97) 0%,rgba(5,11,20,.86) 45%,rgba(5,11,20,.40) 72%,rgba(5,11,20,.78) 100%)",
    "proof_bg": "#071825",
    "proof_text": "#f4fbff",
    "proof_muted": "#9fc2d5",
    "proof_line": "rgba(102,207,255,.20)",
    "proof_box": "#0b2131",
}

magazine = {
    **common,
    "title": "BetLegend Preview C - Premium Sports Desk",
    "bg": "#10100e",
    "text": "#fbf7ed",
    "note_bg": "#211b14",
    "note_text": "#f5d18d",
    "nav_bg": "rgba(16,16,14,.9)",
    "nav_text": "#e8dfcf",
    "line": "rgba(255,238,203,.13)",
    "line_bright": "rgba(255,238,203,.24)",
    "accent": "#e8b85c",
    "accent_soft": "rgba(232,184,92,.42)",
    "accent_wash": "rgba(232,184,92,.14)",
    "kicker": "#f8dca2",
    "muted": "#aaa091",
    "muted_light": "#e6dccb",
    "button_bg": "#e8b85c",
    "button_text": "#16120c",
    "panel_alpha": "rgba(30,27,22,.80)",
    "ticket_bg": "rgba(30,27,22,.94)",
    "ticket_head": "rgba(255,255,255,.05)",
    "team_bg": "#181612",
    "panel": "#181612",
    "hero_img": "images/mlb-coors-field-diamondbacks-rockies-over.png",
    "hero_pos": "center center",
    "hero_overlay": "linear-gradient(90deg,rgba(16,16,14,.96) 0%,rgba(16,16,14,.78) 42%,rgba(16,16,14,.28) 74%,rgba(16,16,14,.58) 100%)",
    "proof_bg": "#f3ead8",
    "proof_text": "#16120c",
    "proof_muted": "#655d50",
    "proof_line": "rgba(22,18,12,.14)",
    "proof_box": "#fffaf0",
}

BODY = """
<main>
  <section class="hero">
    <div class="hero-inner">
      <div>
        <div class="kicker"><i></i> Verified sports betting analysis</div>
        <h1>{headline}</h1>
        <p class="lead">{lead}</p>
        <div class="actions">
          <a class="btn" href="best-bets-today.html">Today's Best Bets</a>
          <a class="btn secondary" href="mlb-previews.html">Game Previews</a>
          <a class="btn secondary" href="records.html">Audit the Record</a>
        </div>
        <div class="stats">
          <div class="stat"><b>10K</b><span>Simulations</span></div>
          <div class="stat"><b>Public</b><span>Pick history</span></div>
          <div class="stat"><b>Daily</b><span>Slate updates</span></div>
        </div>
      </div>
      <aside class="ticket">
        <div class="ticket-head"><strong>Featured Board</strong><span>April 15</span></div>
        <div class="ticket-body">
          <div class="match">
            <div class="team"><img src="{team_a_img}" alt=""><b>{team_a}</b></div>
            <div class="vs">@</div>
            <div class="team"><img src="{team_b_img}" alt=""><b>{team_b}</b></div>
          </div>
          <div class="markets">
            <div class="market"><span>Market</span><b>{market}</b></div>
            <div class="market"><span>Type</span><b>Preview</b></div>
            <div class="market"><span>Angle</span><b>Model</b></div>
          </div>
        </div>
      </aside>
    </div>
  </section>

  <section class="section">
    <div class="section-head">
      <div><h2>Today's board</h2><p class="sub">Image-first entry points into fresh previews, records, and daily picks.</p></div>
      <a class="btn secondary" href="blog.html">Latest Articles</a>
    </div>
    <div class="board">
      <a class="card feature" href="bayern-munich-vs-real-madrid-ucl-analysis-stats-preview-april-15-2026.html">
        <img src="{feature_img}" alt="">
        <div class="card-body"><span class="tag">Game of the Day</span><h3>{feature_title}</h3><p>{feature_text}</p></div>
      </a>
      <a class="card" href="play-in-elimination-warriors-clippers-magic-sixers-nba-april-15-2026.html">
        <img src="images/warriors-kings-kuminga-over-nov5-2025.png" alt="">
        <div class="card-body"><span class="tag blue">NBA</span><h3>Play-In elimination pressure</h3><p>Injury context, playoff urgency, and market notes.</p></div>
      </a>
      <a class="card" href="mlb-previews.html">
        <img src="images/mlb-picks-team-logos-july-11-2025.png" alt="">
        <div class="card-body"><span class="tag red">MLB</span><h3>Daily baseball preview hub</h3><p>Pitchers, totals, bullpens, run lines, and weather.</p></div>
      </a>
    </div>
  </section>

  <section class="proof">
    <div class="section">
      <div><h2>Trust before picks.</h2><p>Records and transparency are not buried below generic sales copy.</p></div>
      <div class="proof-box"><b>No deletes</b><span>Every pick remains visible</span></div>
      <div class="proof-box"><b>Units</b><span>Profit/loss by sport</span></div>
      <div class="proof-box"><b>Receipts</b><span>Audit before tailing</span></div>
    </div>
  </section>

  <section class="section">
    <div class="lower">
      <div class="panel"><h2>Record center</h2><p>Fast paths into all sport-specific results.</p><div class="grid-links"><a href="records.html">All</a><a href="mlb-records.html">MLB</a><a href="nba-records.html">NBA</a><a href="nhl-records.html">NHL</a><a href="nfl-records.html">NFL</a><a href="soccer-records.html">Soccer</a></div></div>
      <div class="panel"><h2>Tools and research</h2><p>Bet sizing, calculators, bankroll work, and handicapping education.</p><div class="grid-links"><a href="kelly-criterion.html">Kelly</a><a href="betting-calculators.html">Calculators</a><a href="bankroll.html">Bankroll</a><a href="handicapping-hub.html">Hub</a><a href="ev-calculator.html">EV</a><a href="live-odds.html">Odds</a></div></div>
    </div>
  </section>

  <section class="section">
    <div class="section-head"><div><h2>Latest intelligence</h2><p class="sub">The lower visuals represent the sports site instead of generic blocks.</p></div></div>
    <div class="media-row">
      <a class="media" href="nhl-previews.html"><img src="images/bruins-islanders-under-6-nhl-betting-pick-november-26-2025.png" alt=""><b>NHL Previews</b></a>
      <a class="media" href="nfl.html"><img src="images/detroit-lions-philadelphia-eagles-nfl-sunday-night-football-betting-pick-november-16-2025.png" alt=""><b>NFL Picks</b></a>
      <a class="media" href="soccer-previews.html"><img src="images/fifa.png" alt=""><b>Soccer Board</b></a>
      <a class="media" href="betting-calculators.html"><img src="images/ai-moneyball.png" alt=""><b>Betting Tools</b></a>
    </div>
  </section>
</main>
"""

pages = [
    ("homepage-preview-a-stadium.html", stadium, BODY.format(
        headline="Sharper daily picks. Cleaner data. Public results.",
        lead="A sportsbook-style command center for bettors who want today's games, transparent records, and tools without a cluttered homepage.",
        team_a="Board", team_b="Models", team_a_img="images/nfl-betting-boom.png", team_b_img="images/ai-moneyball.png",
        market="All Sports", feature_img="images/fifa.png", feature_title="Bayern Munich vs Real Madrid UCL preview",
        feature_text="Current daily coverage with matchup context, market notes, and clean internal links into soccer."
    )),
    ("homepage-preview-b-data.html", market, BODY.format(
        headline="Betting analysis built like a trading desk.",
        lead="A sharper, darker, more data-driven direction that leans into simulations, records, live odds, and pick accountability.",
        team_a="Model", team_b="Market", team_a_img="images/ai-moneyball.png", team_b_img="images/LIVE.png",
        market="Edge", feature_img="images/ai-moneyball.png", feature_title="AI-driven betting analysis hub",
        feature_text="A more technical front door for readers who care about probabilities, pricing, and discipline."
    )),
    ("homepage-preview-c-magazine.html", magazine, BODY.format(
        headline="Daily sports betting coverage with a premium edge.",
        lead="A more editorial, magazine-like homepage with strong sports photography, cleaner sections, and a less tech-heavy feel.",
        team_a="Slate", team_b="Record", team_a_img="images/mlb-coors-field-diamondbacks-rockies-over.png", team_b_img="images/proof-bet-screenshot-1000079685.jpg",
        market="Daily", feature_img="images/mlb-coors-field-diamondbacks-rockies-over.png", feature_title="MLB preview hub and daily board",
        feature_text="A visual sports-desk treatment for game previews, records, and betting resources."
    )),
]

for filename, config, body in pages:
    (ROOT / filename).write_text(page(config, body), encoding="utf-8", newline="\n")

gallery_cards = "\n".join(
    f'<a class="choice" href="{filename}"><iframe src="{filename}" loading="lazy"></iframe><div><b>{config["title"].replace("BetLegend Preview ", "Preview ")}</b><span>Open full preview</span></div></a>'
    for filename, config, _ in pages
)

gallery = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>BetLegend Homepage Preview Options</title>
<style>
body{{margin:0;background:#080d12;color:#f8fafc;font-family:Arial,sans-serif}}
header{{padding:28px;max-width:1500px;margin:0 auto}}
h1{{margin:0;font-size:34px}}p{{color:#aeb8c4}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;max-width:1500px;margin:0 auto;padding:0 28px 40px}}
.choice{{display:block;border:1px solid rgba(255,255,255,.14);border-radius:10px;overflow:hidden;background:#111820;color:#fff;text-decoration:none}}
iframe{{width:100%;height:520px;border:0;transform:scale(.62);transform-origin:top left;width:161%;pointer-events:none}}
.choice div{{margin-top:-198px;padding:18px;border-top:1px solid rgba(255,255,255,.14);background:#111820;position:relative}}
b{{display:block;font-size:20px}}span{{display:block;margin-top:6px;color:#d9a441;font-weight:700}}
@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}iframe{{height:620px;transform:scale(.74);width:135%}}.choice div{{margin-top:-150px}}}}
</style></head><body><header><h1>BetLegend homepage preview options</h1><p>These are separate preview files. The live homepage is not changed.</p></header><main class="grid">{gallery_cards}</main></body></html>"""
(ROOT / "homepage-preview-gallery.html").write_text(gallery, encoding="utf-8", newline="\n")
