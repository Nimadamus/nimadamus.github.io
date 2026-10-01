#!/usr/bin/env python3
"""Parlay payout chart on parlay-calculator.html (Phase 5, Oct 1 2026).

Search Console shows real demand for "parlay payouts chart", "2 team parlay payout",
"3 team parlay payout" and "3 game parlay payout" landing on the parlay calculator,
which had no chart. This writes an exact, computed chart (true odds, no book
reductions) between PARLAY-CHART markers, just above the strategy section.

Usage: python scripts/parlay_payout_chart.py [--dry-run]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "parlay-calculator.html")
START, END = "<!-- PARLAY-CHART-START (scripts/parlay_payout_chart.py) -->", "<!-- PARLAY-CHART-END -->"
BLOCK_RE = re.compile(r"<!-- PARLAY-CHART-START.*?<!-- PARLAY-CHART-END -->\r?\n?", re.S)
ANCHOR = re.compile(r"<h2[^>]*>Smart Parlay Strategy")


def dec(american):
    return 1 + (american / 100 if american > 0 else 100 / abs(american))


def to_american(d):
    return f"+{round((d - 1) * 100):,}" if d >= 2 else f"{round(-100 / (d - 1))}"


def block():
    legs = range(2, 11)
    rows = []
    for n in legs:
        d110, d100, d120 = dec(-110) ** n, dec(100) ** n, dec(-120) ** n
        be = (1 / dec(-110) ** n)
        rows.append(f'<tr id="parlay-{n}-team"><td>{n} team parlay</td><td>{to_american(d110)}</td><td>${(d110 - 1) * 100:,.2f}</td>'
                    f'<td>${(d100 - 1) * 100:,.2f}</td><td>${(d120 - 1) * 100:,.2f}</td><td>{be * 100:.2f}%</td></tr>')
    table = ("<div style=\"overflow-x:auto;-webkit-overflow-scrolling:touch\"><table style=\"width:100%;border-collapse:collapse;min-width:620px;font-variant-numeric:tabular-nums\">"
             "<thead><tr><th>Parlay</th><th>Odds (all legs -110)</th><th>Profit on $100, legs at -110</th><th>Profit on $100, legs at +100</th>"
             "<th>Profit on $100, legs at -120</th><th>Hit rate if each leg wins 52.38%</th></tr></thead><tbody>"
             + "".join(rows) + "</tbody></table></div>")
    two, three = (dec(-110) ** 2 - 1) * 100, (dec(-110) ** 3 - 1) * 100
    style = ("<style>.parlay-chart th{font-size:.75rem;text-transform:uppercase;letter-spacing:.05em;color:#d4af37;text-align:right;padding:8px;"
             "border-bottom:1px solid rgba(212,175,55,.35);white-space:nowrap}.parlay-chart td{padding:8px;text-align:right;border-bottom:1px solid "
             "rgba(255,255,255,.08);white-space:nowrap}.parlay-chart th:first-child,.parlay-chart td:first-child{text-align:left}"
             ".parlay-chart p{max-width:76ch}</style>")
    return (f"\n{START}\n{style}\n<section class=\"parlay-chart\" id=\"parlay-payout-chart\" style=\"margin:0 0 40px\">"
            "<h2 style=\"color: var(--primary-glow); font-size: 1.9rem; margin-bottom: 18px; font-family: 'Orbitron', sans-serif;\">Parlay Payout Chart</h2>"
            "<p>What a $100 parlay pays at true odds, from 2 to 10 legs. The middle column is the standard case, every leg at -110. "
            f"A 2 team parlay at -110 pays ${two:,.2f} profit (odds {to_american(dec(-110) ** 2)}), and a 3 team parlay at -110 pays ${three:,.2f} "
            f"(odds {to_american(dec(-110) ** 3)}). Some sportsbooks pay fixed parlay odds that are a little lower than these true odds, so check the "
            "payout on your slip against this chart or the calculator above.</p>"
            + table +
            "<p style=\"margin-top:14px\">The last column shows the catch. At -110 each leg has to win 52.38% of the time just to break even, "
            "and the chance that every leg wins falls fast: about 27% for a 2 team parlay at break even prices and about 1% by 7 legs. "
            "A parlay only has positive expected value when each leg wins more often than its price implies, which is what the "
            "<a href=\"ev-calculator.html\">expected value calculator</a> checks for a single bet.</p>"
            "<p>Mixed odds? Enter each leg in the calculator above, or convert prices with the <a href=\"odds-converter.html\">odds converter</a>.</p>"
            f"</section>\n{END}\n")


def main():
    dry = "--dry-run" in sys.argv
    s = open(PAGE, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    orig = s
    s = BLOCK_RE.sub("", s, count=1)
    m = ANCHOR.search(s)
    if not m:
        sys.exit("anchor not found")
    line_start = s.rfind("\n", 0, m.start()) + 1
    s = s[:line_start] + block().replace("\n", nl).lstrip() + s[line_start:]
    if s != orig and not dry:
        open(PAGE, "w", encoding="utf-8", newline="").write(s)
    print("[parlay_payout_chart]", "changed" if s != orig else "no change")


if __name__ == "__main__":
    main()
