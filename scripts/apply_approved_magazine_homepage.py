from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "homepage-preview-c-magazine.html"
INDEX = ROOT / "index.html"

LIVE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta name="google-adsense-account" content="ca-pub-3995543166394162">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="canonical" href="https://www.betlegendpicks.com/">
<link rel="icon" href="newlogo.png">
<meta name="robots" content="index, follow">
<meta name="description" content="BetLegend runs 10,000 model-powered game simulations daily for NFL, NBA, NHL, MLB and college sports picks. Every pick posted pre-game, every result verified. See transparent records, daily previews, and betting tools.">
<meta name="keywords" content="sports betting picks, NFL picks, NBA picks, NHL picks, MLB picks, college basketball picks, soccer predictions, betting analysis, verified betting records">
<meta property="og:title" content="Model-Powered Sports Betting Simulations & Expert Picks | BetLegend">
<meta property="og:description" content="10,000 model-driven game simulations daily. NFL, NBA, NHL, MLB and college sports picks with verified transparent records.">
<meta property="og:url" content="https://www.betlegendpicks.com/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="BetLegend">
<meta property="og:image" content="https://www.betlegendpicks.com/newlogo.png">
<meta name="twitter:image" content="https://www.betlegendpicks.com/newlogo.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Model-Powered Sports Betting Simulations & Expert Picks | BetLegend">
<meta name="twitter:description" content="10,000 model-driven game simulations daily with verified transparent records.">
<title>Model-Powered Sports Betting Simulations & Expert Picks | BetLegend</title>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"Organization","name":"BetLegend Picks","url":"https://www.betlegendpicks.com","logo":"https://www.betlegendpicks.com/newlogo.png","description":"Expert sports betting picks, model-powered simulations, daily previews, betting tools, and verified records.","sameAs":["https://twitter.com/BetLegend2025","https://discord.gg/D2yRvgttOK"],"contactPoint":{"@type":"ContactPoint","email":"picks@mlbprops.com","contactType":"Customer Service"}}
</script>
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebSite","name":"BetLegend","url":"https://www.betlegendpicks.com","description":"Model-powered sports betting picks, daily previews, betting tools, and verified transparent records."}
</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-QS8L5TDNLY"></script>
<script>
window.dataLayer=window.dataLayer||[];
function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());
gtag('config','G-QS8L5TDNLY');
</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3995543166394162" crossorigin="anonymous"></script>
<link rel="stylesheet" href="/mobile-optimize.css" media="screen">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Oswald:wght@500;600;700&display=swap" rel="stylesheet">
"""


def main() -> None:
    html = PREVIEW.read_text(encoding="utf-8")
    style_start = html.index("<style>")
    body = html[style_start:]
    body = body.replace(
        '<div class="note">Preview only. Nothing here changes the live homepage.</div>\n\n',
        "",
    )
    body = body.replace(
        "<span>Preview only. The live homepage has not been changed. Model-powered sports betting simulations, expert picks, transparent records, tools, and education.</span>",
        "<span>Model-powered sports betting simulations, expert picks, transparent records, tools, and education.</span>",
    )
    body = body.replace(
        "</body>\n</html>\n",
        '<script async data-id="101485054" src="//static.getclicky.com/js"></script>\n</body>\n</html>\n',
    )
    INDEX.write_text(LIVE_HEAD + body, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
