#!/usr/bin/env python3
"""BetLegend email signup module (Nima, Oct 1 2026: Brevo, double opt in, no popups).

One module per page at the end of the page content (after the Pro module when
the page has one): picks, records, calculators and sport hubs. The form posts
to the TrustMyRecord Brevo endpoint via /blp-email.js; a confirmation email
finishes the signup, and every email carries an unsubscribe link.

Idempotent: the block lives between <!-- EMAIL-SIGNUP-START --> and <!-- EMAIL-SIGNUP-END -->.
Usage: python scripts/email_signup.py [--dry-run]
"""
import html
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# mlb-picks-today.html gets the module from scripts/picks_today.py, which rebuilds that page.
PAGES = {
    "blog.html": ("picks", "all"),
    "records.html": ("records", "all"),
    "betlegend-verified-records.html": ("records", "all"),
    "mlb-records.html": ("records", "MLB"),
    "nfl-records.html": ("records", "NFL"),
    "nba-records.html": ("records", "NBA"),
    "nhl-records.html": ("records", "NHL"),
    "ncaaf-records.html": ("records", "NCAAF"),
    "ncaab-records.html": ("records", "NCAAB"),
    "soccer-records.html": ("records", "Soccer"),
    "ev-calculator.html": ("calculator", "all"),
    "kelly-criterion.html": ("calculator", "all"),
    "betting-calculators.html": ("calculator", "all"),
    "parlay-calculator.html": ("calculator", "all"),
    "risk-of-ruin-calculator.html": ("calculator", "all"),
    "bankroll-simulator.html": ("calculator", "all"),
    "bankroll.html": ("calculator", "all"),
    "odds-converter.html": ("calculator", "all"),
    "mlb.html": ("hub", "MLB"),
    "nfl.html": ("hub", "NFL"),
    "nba.html": ("hub", "NBA"),
    "nhl.html": ("hub", "NHL"),
    "ncaaf.html": ("hub", "NCAAF"),
    "ncaab.html": ("hub", "NCAAB"),
    "soccer.html": ("hub", "Soccer"),
}

START, END = "<!-- EMAIL-SIGNUP-START (scripts/email_signup.py) -->", "<!-- EMAIL-SIGNUP-END -->"
BLOCK_RE = re.compile(r"<!-- EMAIL-SIGNUP-START.*?<!-- EMAIL-SIGNUP-END -->\r?\n?", re.S)
CSS = ("<style>.blp-email{box-sizing:border-box;max-width:880px;margin:32px auto 40px;padding:22px 24px;border:1px solid rgba(120,170,255,.35);"
       "border-radius:12px;background:linear-gradient(160deg,#0f1520,#0d1016);color:#e8ecf2;font-family:inherit;text-align:left}"
       ".blp-email .k{margin:0 0 6px;font-size:.72rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#7fb2ff}"
       ".blp-email h2{margin:0 0 8px;font-size:1.3rem;line-height:1.25;color:#fff}"
       ".blp-email p{margin:0 0 12px;color:#c9d0da;line-height:1.55;font-size:.98rem}"
       ".blp-email ul{list-style:none;margin:0 0 14px;padding:0}"
       ".blp-email li{margin:0 0 8px}.blp-email li label{display:flex;gap:10px;align-items:flex-start;cursor:pointer;color:#dfe5ee;line-height:1.45}"
       ".blp-email li input{margin-top:4px;accent-color:#7fb2ff}.blp-email li b{color:#fff}"
       ".blp-email .row{display:flex;gap:10px;flex-wrap:wrap}"
       ".blp-email input[type=email]{flex:1 1 240px;min-width:0;padding:11px 12px;border-radius:7px;border:1px solid #2b3445;background:#0a0d13;color:#fff;font-size:1rem}"
       ".blp-email button{padding:11px 18px;border:0;border-radius:7px;background:#7fb2ff;color:#0b1220;font-weight:700;font-size:1rem;cursor:pointer}"
       ".blp-email button:disabled{opacity:.6;cursor:default}"
       ".blp-email button:focus-visible,.blp-email input:focus-visible{outline:2px solid #fff;outline-offset:2px}"
       ".blp-email .hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}"
       ".blp-email .s{display:block;margin-top:10px;font-size:.8rem;color:#9aa3af}.blp-email .s a{color:#9fc3ff}"
       ".blp-email-msg{margin:10px 0 0;font-size:.95rem}.blp-email-msg.ok{color:#8fe3a8}.blp-email-msg.err{color:#ff9a9a}"
       "@media(max-width:600px){.blp-email{margin:24px 12px 32px;padding:18px 16px}}</style>")


def block(path, page_type, sport):
    depth = path.count("/")
    up = "../" * depth
    e = lambda s: html.escape(s, quote=True)
    return (f"\n{START}\n{CSS}\n"
            f"<section class=\"blp-email\" aria-label=\"BetLegend email\" data-source=\"betlegendpicks\" "
            f"data-page-type=\"{e(page_type)}\" data-sport=\"{e(sport)}\">"
            "<p class=\"k\">Free by email</p><h2>Get our picks and the weekly record in your inbox</h2>"
            "<form novalidate><ul>"
            "<li><label><input type=\"checkbox\" name=\"list\" value=\"betlegend_card\" checked> <span><b>The BetLegend Card.</b> "
            "The day's picks with the posted price and size, plus yesterday's results, on days we post.</span></label></li>"
            "<li><label><input type=\"checkbox\" name=\"list\" value=\"monday_report\" checked> <span><b>Monday Record Report.</b> "
            "Every graded result from the past week, wins and losses, with the running record.</span></label></li>"
            "</ul><div class=\"row\"><label class=\"hp\" aria-hidden=\"true\">Website<input type=\"text\" name=\"website\" tabindex=\"-1\" autocomplete=\"off\"></label>"
            "<input type=\"email\" name=\"email\" required autocomplete=\"email\" placeholder=\"you@example.com\" aria-label=\"Email address\">"
            "<button type=\"submit\">Sign me up</button></div></form>"
            "<p class=\"blp-email-msg\" role=\"status\" aria-live=\"polite\"></p>"
            f"<span class=\"s\">Free. We email you a confirmation link first, and every email has a one click unsubscribe. "
            f"<a href=\"{up}privacy.html\">Privacy</a></span></section>\n"
            f"<script src=\"{up}blp-events.js\" defer></script>\n"
            f"<script src=\"{up}blp-email.js\" defer></script>\n{END}\n")


def apply(path, cfg, dry):
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        print(f"  MISSING {path}")
        return False
    with open(full, encoding="utf-8", newline="") as f:
        s = f.read()
    nl = "\r\n" if "\r\n" in s else "\n"
    orig = s
    s = BLOCK_RE.sub("", s, count=1)
    b = block(path, *cfg).replace("\n", nl).lstrip()
    # After the Pro module when present, else inside <main>, else before the footer.
    pe = s.find("<!-- PRO-CTA-END -->")
    mm = s.lower().rfind("</main>")
    m = re.search(r"<footer\b", s, re.I)
    if pe >= 0:
        i = s.index("\n", pe) + 1 if "\n" in s[pe:] else len(s)
        s = s[:i] + b + s[i:]
    elif mm >= 0:
        s = s[:mm] + b + s[mm:]
    elif m:
        s = s[:m.start()] + b + s[m.start():]
    else:
        i = s.lower().rfind("</body>")
        if i < 0:
            print(f"  NO </body> {path}")
            return False
        s = s[:i] + b + s[i:]
    if s == orig:
        return False
    if not dry:
        with open(full, "w", encoding="utf-8", newline="") as f:
            f.write(s)
    return True


def main():
    dry = "--dry-run" in sys.argv
    changed = [p for p, cfg in PAGES.items() if apply(p, cfg, dry)]
    print(f"[email_signup] {'would update' if dry else 'updated'} {len(changed)} of {len(PAGES)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
