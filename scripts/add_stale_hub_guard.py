#!/usr/bin/env python3
"""
Insert a pre-paint stale-hub guard into each preview/hub page, right after its
window.FORCED_PAGE_DATE line. When the hub's baked date is not today (PT), the
guard hides the stale baked .game-preview board BEFORE it can paint; the sport
calendar JS then redirects to the newest valid preview (renderPreviewHub). On a
fresh hub (baked == today) the guard is inert. Idempotent.
"""
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUBS = ['nba-previews.html', 'nhl-previews.html', 'mlb-previews.html',
        'soccer-previews.html', 'college-basketball-previews.html', 'nfl.html']

GUARD = ('<script id="stale-hub-guard">/* hide stale baked board before paint when this hub\'s date isn\'t today (PT) */'
         '(function(){try{var pt=new Intl.DateTimeFormat("en-CA",{timeZone:"America/Los_Angeles"}).format(new Date());'
         'if(window.FORCED_PAGE_DATE&&window.FORCED_PAGE_DATE!==pt){var s=document.createElement("style");'
         's.textContent=".main-content .game-preview{display:none!important}";(document.head||document.documentElement).appendChild(s);}}catch(e){}})();</script>')

FORCED_LINE = re.compile(r"(<script>\s*window\.FORCED_PAGE_DATE\s*=\s*'[^']*';\s*</script>)")


def main():
    done = []
    for name in HUBS:
        fp = os.path.join(REPO, name)
        if not os.path.exists(fp):
            continue
        with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if 'id="stale-hub-guard"' in content:
            done.append(f"{name}: already present")
            continue
        m = FORCED_LINE.search(content)
        if not m:
            done.append(f"{name}: NO FORCED_PAGE_DATE line - skipped")
            continue
        new = content[:m.end()] + "\n" + GUARD + content[m.end():]
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(new)
        done.append(f"{name}: guard inserted")
    for d in done:
        print(" ", d)


if __name__ == '__main__':
    main()
