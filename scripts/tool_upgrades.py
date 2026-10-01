#!/usr/bin/env python3
"""Betting tool upgrades (Phase 5 SEO, Oct 1 2026).

  * /no-vig-calculator.html                new page: no vig (fair odds) calculator
  * kelly-criterion.html                   + Kelly bet size tables and related tools (TOOL-KELLY block)
  * kelly-criterion/fractional-vs-full.html + fractional Kelly calculator and growth table (TOOL-FRACTIONAL block)
    (this existing page already ranks for fractional Kelly queries, so it is upgraded rather than duplicated)
  * ev-calculator/how-to-calculate-ev.html  + worked EV tables (TOOL-EV block)

Every number in the tables is computed here from the formulas stated on the page.
Idempotent: blocks live between <!-- TOOL-xxx-START --> and <!-- TOOL-xxx-END --> markers.

Usage: python scripts/tool_upgrades.py [--dry-run]
"""
import datetime as dt
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mlb_team_pages as m  # noqa: E402

ROOT = m.ROOT
e = m.e


def dec(am):
    return 1 + (am / 100 if am > 0 else 100 / abs(am))


def american(d):
    if d >= 2:
        return f"+{round((d - 1) * 100)}"
    return f"{round(-100 / (d - 1))}"


def kelly(p, am):
    b = dec(am) - 1
    return max(0.0, (b * p - (1 - p)) / b)


def growth(p, am, f):
    b = dec(am) - 1
    return p * math.log(1 + b * f) + (1 - p) * math.log(1 - f)


def ev100(p, am):
    return p * (dec(am) - 1) * 100 - (1 - p) * 100


def fam(am):
    return f"+{am}" if am > 0 else str(am)


BLOCK_CSS = ("<style>.blp-tool{box-sizing:border-box;margin:36px 0;padding:22px;border:1px solid rgba(255,255,255,.14);border-radius:12px;"
             "background:#121620;color:#e8ecf2;text-align:left;line-height:1.6}.blp-tool h2{margin:0 0 8px;font-size:1.35rem;color:#fff}"
             ".blp-tool h3{margin:20px 0 8px;font-size:1.05rem;color:#fff}.blp-tool p{color:#c9d0da;max-width:76ch}"
             ".blp-tool .w{overflow-x:auto;-webkit-overflow-scrolling:touch}.blp-tool table{border-collapse:collapse;width:100%;min-width:520px;font-size:.92rem;font-variant-numeric:tabular-nums}"
             ".blp-tool th{font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;color:#d4af37;text-align:right;padding:8px;border-bottom:1px solid rgba(212,175,55,.35);white-space:nowrap}"
             ".blp-tool td{padding:8px;text-align:right;border-bottom:1px solid rgba(255,255,255,.08);white-space:nowrap}"
             ".blp-tool th:first-child,.blp-tool td:first-child{text-align:left}.blp-tool a{color:#f3d77a}"
             ".blp-tool .links{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px 18px;padding:0;list-style:none}"
             ".blp-tool .calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:12px 0}"
             ".blp-tool label{display:flex;flex-direction:column;font-size:.85rem;color:#c9d0da;gap:4px}"
             ".blp-tool input,.blp-tool select{padding:9px 10px;border-radius:7px;border:1px solid #2b3445;background:#0a0d13;color:#fff;font-size:1rem}"
             ".blp-tool .out{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:8px 0}"
             ".blp-tool .out div{background:#0d1119;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px}"
             ".blp-tool .out b{display:block;font-size:1.3rem;color:#fff}.blp-tool .out span{color:#9aa3af;font-size:.8rem}"
             ".blp-tool .neg{color:#ef7d6f}.blp-tool .pos{color:#6fd08f}</style>")


def put(path, name, block, anchor_re, dry):
    full = os.path.join(ROOT, path)
    s = open(full, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    start, end = f"<!-- TOOL-{name}-START (scripts/tool_upgrades.py) -->", f"<!-- TOOL-{name}-END -->"
    s0 = s
    s = re.sub(rf"<!-- TOOL-{name}-START.*?<!-- TOOL-{name}-END -->\r?\n?", "", s, count=1, flags=re.S)
    mm = re.search(anchor_re, s)
    if not mm:
        sys.exit(f"anchor not found in {path}")
    ls = s.rfind("\n", 0, mm.start()) + 1
    b = (f"{start}\n{BLOCK_CSS}\n{block}\n{end}\n").replace("\n", nl)
    s = s[:ls] + b + s[ls:]
    if s != s0:  # real content change: the page's dateModified (and so its sitemap lastmod) moves to today
        s = re.sub(r'("dateModified"\s*:\s*")\d{4}-\d{2}-\d{2}', lambda mm: mm.group(1) + dt.date.today().isoformat(), s)
    if s != s0 and not dry:
        open(full, "w", encoding="utf-8", newline="").write(s)
    print(f"  {path}: {'updated' if s != s0 else 'no change'}")


# ---------------------------------------------------------------- Kelly page

def kelly_block():
    rows = []
    for p in (0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.60):
        f = kelly(p, -110)
        rows.append(f"<tr><td>{p * 100:.0f}%</td><td>{ev100(p, -110):+.2f}</td><td>{f * 100:.2f}%</td><td>{f * 50:.2f}%</td><td>{f * 25:.2f}%</td><td>${f * 25 * 10:,.2f}</td></tr>")
    t1 = ("<div class=\"w\"><table><thead><tr><th>Your win probability</th><th>EV per $100</th><th>Full Kelly</th><th>Half Kelly</th><th>Quarter Kelly</th>"
          "<th>Quarter Kelly on $1,000</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    rows = []
    for am, p in ((150, 0.42), (150, 0.44), (150, 0.46), (200, 0.36), (200, 0.38), (-150, 0.62), (-150, 0.64), (-200, 0.69)):
        f = kelly(p, am)
        be = 1 / dec(am)
        rows.append(f"<tr><td>{fam(am)}</td><td>{be * 100:.1f}%</td><td>{p * 100:.0f}%</td><td>{ev100(p, am):+.2f}</td><td>{f * 100:.2f}%</td><td>{f * 50:.2f}%</td><td>{f * 25:.2f}%</td></tr>")
    t2 = ("<div class=\"w\"><table><thead><tr><th>Odds</th><th>Break even</th><th>Your win probability</th><th>EV per $100</th><th>Full Kelly</th><th>Half Kelly</th>"
          "<th>Quarter Kelly</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    links = [("Fractional Kelly calculator and growth table", "/kelly-criterion/fractional-vs-full.html"), ("Expected value calculator", "/ev-calculator.html"),
             ("How to calculate EV by hand", "/ev-calculator/how-to-calculate-ev.html"), ("No vig fair odds calculator", "/no-vig-calculator.html"),
             ("Kelly for parlays", "/kelly-criterion/parlays.html"), ("Bankroll management", "/bankroll.html"),
             ("Risk of ruin calculator", "/risk-of-ruin-calculator.html"), ("Risk of ruin explained", "/bankroll-management/risk-of-ruin.html"),
             ("Unit sizing", "/bankroll-management/unit-sizing.html"), ("Parlay calculator", "/parlay-calculator.html")]
    lk = '<ul class="links">' + "".join(f'<li><a href="{h}">{e(n)}</a></li>' for n, h in links if os.path.isfile(os.path.join(ROOT, h.lstrip("/")))) + "</ul>"
    return (f'<section class="blp-tool" id="kelly-bet-size-table"><h2>Kelly Bet Size Table</h2>'
            "<p>What the Kelly formula, f = (bp &minus; q) / b, says to stake at common prices. Here b is the decimal odds minus 1, p is your win probability and q = 1 &minus; p. "
            "A negative result means the bet has no edge, and Kelly says not to bet.</p>"
            "<h3>Standard -110 bets (spreads and totals)</h3>" + t1 +
            "<p>At -110 you need to win 52.38% just to break even, so even a strong 55% handicapper should only stake about 5.5% of the bankroll at full Kelly, "
            "and most bettors use half or quarter Kelly to cut the swings.</p>"
            "<h3>Underdogs and favorites</h3>" + t2 +
            "<h3>Related Kelly and bankroll tools</h3>" + lk + "</section>")


# ---------------------------------------------------------------- fractional Kelly

def fractional_block():
    p, am = 0.55, -110
    fstar = kelly(p, am)
    g_full = growth(p, am, fstar)
    rows = []
    for name, frac in (("Full Kelly", 1), ("Three quarter Kelly", .75), ("Half Kelly", .5), ("Quarter Kelly", .25), ("Eighth Kelly", .125), ("Double Kelly", 2)):
        f = fstar * frac
        g = growth(p, am, f)
        rows.append(f"<tr><td>{name}</td><td>{f * 100:.2f}%</td><td>{g * 1e4:.2f}</td><td>{g / g_full * 100:.0f}%</td><td>{frac:g}x</td>"
                    f"<td>{math.exp(g * 1000):.2f}x</td></tr>")
    table = ("<div class=\"w\"><table><thead><tr><th>Fraction</th><th>Stake per bet</th><th>Growth per bet (basis points)</th><th>Share of full Kelly growth</th>"
             "<th>Swing size vs full Kelly</th><th>Typical bankroll multiple after 1,000 bets</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    calc = """<div class="calc">
<label for="fk-bank">Bankroll ($)<input id="fk-bank" type="number" min="0" step="any" value="1000"></label>
<label for="fk-odds">American odds<input id="fk-odds" type="number" step="any" value="-110"></label>
<label for="fk-p">Your win probability (%)<input id="fk-p" type="number" min="0" max="100" step="any" value="55"></label>
<label for="fk-frac">Kelly fraction<select id="fk-frac"><option value="1">Full</option><option value="0.5" selected>Half</option><option value="0.25">Quarter</option><option value="0.125">Eighth</option></select></label>
</div>
<div class="out"><div><b id="fk-full">0</b><span>full Kelly, % of bankroll</span></div><div><b id="fk-pct">0</b><span>your fraction, % of bankroll</span></div>
<div><b id="fk-stake">0</b><span>stake in dollars</span></div><div><b id="fk-ev">0</b><span>EV per $100</span></div></div>
<script>(function(){function g(i){return parseFloat(document.getElementById(i).value)}function run(){var B=g('fk-bank'),o=g('fk-odds'),p=g('fk-p')/100,fr=parseFloat(document.getElementById('fk-frac').value);
if(!(o>=100||o<=-100)||!(p>0&&p<1)){document.getElementById('fk-full').textContent='check inputs';return}var d=o>0?1+o/100:1+100/Math.abs(o),b=d-1,f=(b*p-(1-p))/b;if(f<0)f=0;
var ev=p*b*100-(1-p)*100;document.getElementById('fk-full').textContent=(f*100).toFixed(2)+'%';document.getElementById('fk-pct').textContent=(f*fr*100).toFixed(2)+'%';
document.getElementById('fk-stake').textContent='$'+(B*f*fr).toFixed(2);var el=document.getElementById('fk-ev');el.textContent=(ev>=0?'+':'')+ev.toFixed(2);el.className=ev>=0?'pos':'neg'}
['fk-bank','fk-odds','fk-p','fk-frac'].forEach(function(i){document.getElementById(i).addEventListener('input',run)});run()})();</script>"""
    return (f'<section class="blp-tool" id="fractional-kelly-calculator"><h2>Fractional Kelly Calculator</h2>'
            "<p>Enter your bankroll, the price and your honest win probability. The calculator shows the full Kelly stake and the stake at the fraction you choose.</p>"
            + calc +
            f"<h3>What each fraction costs and buys</h3><p>Exact figures for a bettor who wins 55% of bets at -110 (full Kelly stake {fstar * 100:.2f}%). "
            "Growth is the expected log growth of the bankroll per bet, the number Kelly maximizes. Half Kelly keeps about three quarters of the growth with half the swing size; "
            "betting double Kelly brings growth back to zero while doubling the swings.</p>" + table +
            "<p>The last column compounds the per bet growth rate over 1,000 bets (1.00x means no growth). It is the middle outcome, not a guarantee. Real results spread widely around it, which is why the swing size column matters.</p>"
            "<p>Related: <a href=\"/kelly-criterion.html\">Kelly criterion calculator</a> &middot; <a href=\"/ev-calculator.html\">EV calculator</a> &middot; "
            "<a href=\"/risk-of-ruin-calculator.html\">Risk of ruin calculator</a> &middot; <a href=\"/kelly-criterion/parlays.html\">Kelly for parlays</a></p></section>")


# ---------------------------------------------------------------- EV how-to

def ev_block():
    ex = [(-110, .55), (-110, .50), (+150, .45), (+150, .38), (-150, .64), (-200, .65), (+250, .30), (+105, .52)]
    rows = []
    for am, p in ex:
        be = 1 / dec(am)
        v = ev100(p, am)
        rows.append(f"<tr><td>{fam(am)}</td><td>{dec(am):.3f}</td><td>{be * 100:.2f}%</td><td>{p * 100:.0f}%</td><td>${(dec(am) - 1) * 100:,.2f}</td>"
                    f"<td class=\"{'pos' if v > 0 else 'neg'}\">{v:+.2f}</td><td>{v:+.1f}%</td></tr>")
    t1 = ("<div class=\"w\"><table><thead><tr><th>Odds</th><th>Decimal</th><th>Implied probability</th><th>Your probability</th><th>Profit if it wins ($100)</th>"
          "<th>EV per $100</th><th>Edge (ROI)</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    rows = []
    for am in (-300, -200, -150, -120, -110, +100, +120, +150, +200, +300):
        rows.append(f"<tr><td>{fam(am)}</td><td>{100 / dec(am):.2f}%</td><td>{ev100(0.55, am):+.2f}</td><td>{ev100(1 / dec(am) + 0.03, am):+.2f}</td></tr>")
    t2 = ("<div class=\"w\"><table><thead><tr><th>Odds</th><th>Break even win rate</th><th>EV per $100 if you win 55%</th><th>EV per $100 with a 3 point edge</th></tr></thead><tbody>"
          + "".join(rows) + "</tbody></table></div>")
    am, p = -110, .55
    return ('<section class="blp-tool" id="ev-worked-tables"><h2>EV Worked Examples Table</h2>'
            "<p>Every row uses the same formula as the steps above: EV = (win probability &times; profit if it wins) &minus; (loss probability &times; stake), here on a $100 stake. "
            f"For example, at {fam(am)} with a {p * 100:.0f}% win probability: 0.55 &times; $90.91 &minus; 0.45 &times; $100 = {ev100(p, am):+.2f} per $100.</p>" + t1 +
            "<h3>Break even win rate and EV by price</h3>"
            "<p>The break even win rate is the implied probability: the share of bets you must win just to break even at that price. "
            "The last column shows what a 3 percentage point edge over the price is worth, which is why the same edge pays more on longer prices.</p>" + t2 +
            "<p>Run your own numbers in the <a href=\"/ev-calculator.html\">EV calculator</a>, strip the bookmaker margin with the <a href=\"/no-vig-calculator.html\">no vig calculator</a>, "
            "and size positive EV bets with the <a href=\"/kelly-criterion.html\">Kelly calculator</a>.</p></section>")


# ---------------------------------------------------------------- no vig page

def no_vig_page(now_pt):
    file = "no-vig-calculator.html"
    ex = [(-110, -110), (-120, +100), (-150, +130), (-200, +170), (-300, +250), (+105, -125)]
    rows = []
    for a, b in ex:
        pa, pb = 1 / dec(a), 1 / dec(b)
        s = pa + pb
        rows.append(f"<tr><td>{fam(a)} / {fam(b)}</td><td>{pa * 100:.2f}% / {pb * 100:.2f}%</td><td>{(s - 1) * 100:.2f}%</td>"
                    f"<td>{pa / s * 100:.2f}% / {pb / s * 100:.2f}%</td><td>{american(s / pa)} / {american(s / pb)}</td></tr>")
    table = ("<div class=\"tr-wrap\"><table><thead><tr><th>Two way odds</th><th>Implied probability</th><th>Vig (overround)</th><th>No vig probability</th>"
             "<th>Fair odds</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
    calc = """<div class="tool"><div class="calc">
<label for="nv-a">Side A odds (American)<input id="nv-a" type="number" step="any" value="-150"></label>
<label for="nv-b">Side B odds (American)<input id="nv-b" type="number" step="any" value="130"></label>
<label for="nv-c">Draw odds (optional, 3 way)<input id="nv-c" type="number" step="any" placeholder="leave blank"></label>
</div>
<div class="out"><div><b id="nv-vig">0</b><span>bookmaker margin (vig)</span></div><div><b id="nv-pa">0</b><span>side A fair probability</span></div>
<div><b id="nv-oa">0</b><span>side A fair odds</span></div><div><b id="nv-pb">0</b><span>side B fair probability</span></div><div><b id="nv-ob">0</b><span>side B fair odds</span></div>
<div id="nv-cbox" hidden><b id="nv-pc">0</b><span>draw fair probability, fair odds <strong id="nv-oc"></strong></span></div></div></div>
<script>(function(){function dec(o){return o>0?1+o/100:1+100/Math.abs(o)}function am(d){return d>=2?'+'+Math.round((d-1)*100):String(Math.round(-100/(d-1)))}
function v(i){var x=document.getElementById(i).value;return x===''?null:parseFloat(x)}function ok(o){return o!==null&&(o>=100||o<=-100)}
function run(){var a=v('nv-a'),b=v('nv-b'),c=v('nv-c');if(!ok(a)||!ok(b)||(c!==null&&!ok(c))){document.getElementById('nv-vig').textContent='check odds';return}
var ps=[1/dec(a),1/dec(b)];if(c!==null)ps.push(1/dec(c));var s=ps.reduce(function(x,y){return x+y},0);
document.getElementById('nv-vig').textContent=((s-1)*100).toFixed(2)+'%';document.getElementById('nv-pa').textContent=(ps[0]/s*100).toFixed(2)+'%';
document.getElementById('nv-oa').textContent=am(s/ps[0]);document.getElementById('nv-pb').textContent=(ps[1]/s*100).toFixed(2)+'%';document.getElementById('nv-ob').textContent=am(s/ps[1]);
var cb=document.getElementById('nv-cbox');if(c!==null){cb.hidden=false;document.getElementById('nv-pc').textContent=(ps[2]/s*100).toFixed(2)+'%';document.getElementById('nv-oc').textContent=am(s/ps[2])}else{cb.hidden=true}}
['nv-a','nv-b','nv-c'].forEach(function(i){document.getElementById(i).addEventListener('input',run)});run()})();</script>"""
    css = ("<style>.tool{margin:18px 0 8px;padding:20px;border:1px solid rgba(212,175,55,.35);border-radius:12px;background:#121620}"
           ".calc{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}.calc label{display:flex;flex-direction:column;gap:4px;font-size:.85rem;color:#c9d0da}"
           ".calc input{padding:10px;border-radius:7px;border:1px solid #2b3445;background:#0a0d13;color:#fff;font-size:1.05rem}"
           ".out{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:14px}.out div{background:#0d1119;border:1px solid rgba(255,255,255,.08);border-radius:10px;padding:12px}"
           ".out b{display:block;font-size:1.35rem;color:#fff;font-variant-numeric:tabular-nums}.out span{color:#9aa3af;font-size:.8rem}</style>")
    pa, pb = 1 / dec(-150), 1 / dec(130)
    s = pa + pb
    faq = [("What is a no vig calculator?", "It removes the sportsbook's margin from a market's prices and shows the fair probability and fair odds of each side, the price the book would post if it took no cut."),
           ("How is the vig removed?", "Convert each price to its implied probability (1 divided by the decimal odds), add them up, and divide each one by the total. The total above 100% is the vig. This is the multiplicative, or proportional, method."),
           ("What is the vig on -110 / -110?", "Each side implies 52.38%, which adds to 104.76%, so the vig is 4.76% and each side's fair probability is exactly 50% (fair odds +100)."),
           ("How do I use no vig odds to find value?", "Compare the fair odds from a sharp market with the price you can get elsewhere. If your price pays more than the fair odds, the bet has positive expected value; check the edge in the EV calculator."),
           ("Does it work for three way markets?", "Yes. Enter the draw price too and the calculator spreads the margin across all three outcomes.")]
    body = f"""<p class="lead">Enter both sides of a market to strip out the bookmaker's margin. You get the vig and each side's fair, no vig probability and odds. The example is -150 / +130: the vig is {(s - 1) * 100:.2f}% and the fair odds are {american(s / pa)} / {american(s / pb)}.</p>
<p class="upd">Updated {{UPDATED}}. Uses the proportional (multiplicative) method.</p>
{css}
{calc}
<section id="examples"><h2>No vig examples</h2>
<p>Common two way prices and what they work out to without the margin.</p>
{table}
</section>
<section id="how"><h2>How the no vig calculation works</h2>
<p>Convert each American price to decimal odds (for -150 that is 1 + 100/150 = 1.667; for +130 it is 2.30), then to implied probability (1/1.667 = 60.00% and 1/2.30 = 43.48%). The two add to 103.48%; the extra 3.48% is the vig. Divide each side by 1.0348 to get the fair probabilities, 57.98% and 42.02%, which convert back to fair odds of {american(s / pa)} and {american(s / pb)}.</p>
<p>The proportional method assumes the book spread its margin evenly across both sides. In practice books often shade the favorite less and the longshot more, so fair odds on big underdogs can be slightly optimistic.</p>
</section>
<section id="faq"><h2>No vig calculator FAQ</h2>
{"".join(f"<details><summary>{e(q)}</summary><p>{e(x)}</p></details>" for q, x in faq)}
</section>
<section id="related"><h2>Related tools</h2>
<ul class="links"><li><a href="ev-calculator.html">Expected value calculator</a></li><li><a href="ev-calculator/how-to-calculate-ev.html">How to calculate EV</a></li><li><a href="kelly-criterion.html">Kelly criterion calculator</a></li><li><a href="odds-converter.html">Odds converter</a></li><li><a href="implied-probability-calculator.html">Implied probability calculator</a></li><li><a href="parlay-calculator.html">Parlay calculator</a></li><li><a href="betting-calculators.html">All betting calculators</a></li></ul>
</section>"""
    title = "No Vig Calculator: Fair Odds and Vig Removal for Sports Betting"
    desc = "Free no vig calculator: enter two or three way odds to see the bookmaker's margin, the fair no vig probability of each side and the fair odds, with worked examples."
    h1 = "No Vig Calculator"
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "No Vig Calculator", "url": m.SITE + file, "applicationCategory": "FinanceApplication",
           "operatingSystem": "Any", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}, "description": desc},
          {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": x}} for q, x in faq]}]
    crumbs = [("Home", "/"), ("Betting Calculators", "betting-calculators.html"), ("No Vig Calculator", None)]
    return file, m.shell(file, title, desc, h1, body, ld, crumbs, now_pt)


def main():
    dry = "--dry-run" in sys.argv
    now_pt = dt.datetime.now(m.PT)
    f, page = no_vig_page(now_pt)
    if not dry:
        open(os.path.join(ROOT, f), "w", encoding="utf-8", newline="\n").write(page)
    print(f"  {f}: written")
    put("kelly-criterion.html", "KELLY", kelly_block(), r"<h2[^>]*>How to Use This Calculator", dry)
    put("kelly-criterion/fractional-vs-full.html", "FRACTIONAL", fractional_block(), r"<h2[^>]*>What the Numbers Actually Mean", dry)
    put("ev-calculator/how-to-calculate-ev.html", "EV", ev_block(), r"<h2[^>]*>Common Calculation Mistakes", dry)


if __name__ == "__main__":
    main()
