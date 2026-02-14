# Auto-generated helper to create terms.html
import os
REPO = os.path.normpath("C:/Users/Nima/nimadamus.github.io")
target = os.path.join(REPO, "terms.html")
nav_src = os.path.join(REPO, "bankroll-management.html")
with open(nav_src, "r", encoding="utf-8") as fh:
    bm = fh.read()
ns = bm.find("<nav class=")
ne = bm.find("</nav>") + 6
nav = bm[ns:ne]
