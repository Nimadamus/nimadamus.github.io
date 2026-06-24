#!/usr/bin/env python3
"""
Guard against the featured/preview calendar-sidebar vs sticky-nav overlap bug.

ROOT CAUSE (June 24 2026): site-navbar.js swaps every page's static nav for the
canonical STICKY <header class="nav">. Pages built from the OLD fixed-nav template
also carry `body{padding-top:140px}`, which pushes that sticky header down to
y~140-232 and onto the fixed `.calendar-sidebar{top:160px}` left rail, hiding the
"Game Archive" title and floating a clipped "2026" above the calendar.

The canonical (correct) pages have NO `padding-top:140px` on body and use
`.calendar-sidebar{top:120px}`. This guard FAILS if any page combines:
    site-navbar.js  +  calendar-sidebar  +  body padding-top:140px
so the bug can never be reintroduced by a newly generated page.

Usage:
    python scripts/validate_nav_calendar_overlap.py [file1.html file2.html ...]
With no args it scans every *.html in the repo root.
Exit 0 = clean, Exit 1 = offending page(s) found.
"""
import os, sys, glob, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def is_broken(html):
    if 'site-navbar.js' not in html:
        return False
    if 'calendar-sidebar' not in html:
        return False
    # body rule that still reserves space for the retired fixed nav
    return re.search(r'padding-top:\s*140px', html) is not None

def main(argv):
    if argv:
        files = argv
    else:
        files = glob.glob(os.path.join(REPO, '*.html'))
    bad = []
    for f in files:
        path = f if os.path.isabs(f) else os.path.join(REPO, f)
        if not os.path.isfile(path):
            continue
        try:
            html = open(path, encoding='utf-8').read()
        except Exception:
            continue
        if is_broken(html):
            bad.append(os.path.basename(path))
    if bad:
        print('[FAIL] nav/calendar overlap guard: %d page(s) combine site-navbar.js + '
              'calendar-sidebar + body padding-top:140px (sticky nav will clip the '
              'calendar title / stray "2026"):' % len(bad))
        for b in bad:
            print('   -', b)
        print('   FIX: remove `padding-top:140px` from the body rule and set '
              '`.calendar-sidebar{top:120px}` (match the canonical featured pages).')
        return 1
    print('[PASSED] nav/calendar overlap guard: no page reserves 140px body padding '
          'under the sticky site-navbar header.')
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
