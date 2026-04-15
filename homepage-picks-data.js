// ============================================================
// HOMEPAGE PICKS DATA - BetLegend Latest Picks & Analysis
// ============================================================
//
// HOW THIS WORKS:
// - First 3 picks show as large featured cards (title + image)
// - Picks 4+ show in compact grid (5 per row, 2 rows = 10 per page)
// - Cards display LEFT to RIGHT, newest first
// - Pagination handles older picks beyond the first 10
//
// RESULT FIELD:
// - "W" = Win (green badge)
// - "L" = Loss (red badge)
// - "P" = Push (gray badge)
// - omit or "" = no badge (game not yet graded)
//
// TO ADD A NEW PICK:
// 1. Add a new object at the TOP of the array below
// 2. Fill in ALL fields: sport, title, date, url, image
// 3. Add result once the game is graded
//
// ============================================================

var HOMEPAGE_PICKS = [
    {
        sport: "NHL",
        title: "Maple Leafs +1.5 (-145) at Senators 2.5u",
        date: "April 15, 2026",
        result: "",
        url: "maple-leafs-plus-1-5-puck-line-battle-of-ontario-senators-nhl.html",
        image: "images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg"
    },
    {
        sport: "NHL",
        title: "Kraken +1.5 (-108) at Golden Knights",
        date: "April 15, 2026",
        result: "",
        url: "kraken-plus-1-5-puck-line-daccord-tortorella-vegas-nhl.html",
        image: "images/utah-hockey-club-san-jose-sharks-nhl-betting-pick-prediction-november-18-2025.png"
    },
    {
        sport: "NHL",
        title: "Caps/Blue Jackets UNDER 6.5 (-115) 2u",
        date: "April 14, 2026",
        result: "",
        url: "capitals-blue-jackets-under-6-5-thompson-greaves-nationwide-arena-nhl.html",
        image: "images/penguins-plus-1-5-senators-december-18-2025.png"
    },
    {
        sport: "MLB",
        title: "Rangers ML (-111) at Athletics 2.5u",
        date: "April 14, 2026",
        result: "",
        url: "rangers-moneyline-gore-strikeouts-athletics-sacramento-mlb.html",
        image: "images/mlb-rangers-athletics-prediction-july.png"
    },
    {
        sport: "NHL",
        title: "Wild/Blues UNDER 5.5 (-105) 3u",
        date: "April 13, 2026",
        result: "",
        url: "wild-blues-under-5-5-gustavsson-hofer-enterprise-center-nhl.html",
        image: "images/wild-puck-line-oilers-december-2-2025.png"
    },
    {
        sport: "MLB",
        title: "Yankees/Angels UNDER 9.5 (-115)",
        date: "April 13, 2026",
        result: "",
        url: "yankees-angels-under-9-5-warren-kikuchi-yankee-stadium-mlb.html",
        image: "images/mlb-aaron-judge-yankees-batting.png"
    },
    {
        sport: "NHL",
        title: "Mammoth/Flames UNDER 6 (-110)",
        date: "April 12, 2026",
        result: "",
        url: "mammoth-flames-under-6-saddledome-calgary-nhl.html",
        image: "images/sharks-mammoth-nhl-picks-december-1-2025.png"
    },
    {
        sport: "MLB",
        title: "Giants ML -114 at Orioles (3u)",
        date: "April 11, 2026",
        result: "",
        url: "giants-moneyline-webb-orioles-camden-yards-mlb.html",
        image: "images/mlb-logan-webb-giants-guardians-moneyline.png"
    },
    {
        sport: "MLB",
        title: "Rangers/Dodgers UNDER 9 (-138)",
        date: "April 10, 2026",
        result: "",
        url: "rangers-dodgers-under-9-glasnow-rocker-dodger-stadium-mlb.html",
        image: "images/mlb-world-series-game1-dodgers-betting-pick-oct-24-2025.png"
    },
    {
        sport: "MLB",
        title: "Cardinals/Nationals OVER 8.5 (-110)",
        date: "April 8, 2026",
        result: "",
        url: "cardinals-nationals-over-8-5-runs-nationals-park-mlb.html",
        image: "images/mlb-twins-coors-field-betting-pick.png"
    },
    {
        sport: "NHL",
        title: "Blues +1.5 (-190) & ML (+130) vs Avalanche",
        date: "April 7, 2026",
        result: "",
        url: "blues-puck-line-moneyline-avalanche-enterprise-center-nhl.html",
        image: "images/blackhawks-blues-december-12-2025.jpg"
    },
    {
        sport: "MLB",
        title: "Braves F5 ML -150 at Angels",
        date: "April 6, 2026",
        result: "",
        url: "braves-f5-moneyline-sale-dominates-angels-mlb.html",
        image: "images/mlb-braves-rays-betting-pick-july.png"
    },
    {
        sport: "MLB",
        title: "Mariners ML -162 at Angels",
        date: "April 5, 2026",
        result: "",
        url: "mariners-moneyline-castillo-angels-rubber-match-mlb.html",
        image: "images/mlb-seattle-mariners-twins-betting-pick.png"
    },
    {
        sport: "MLB",
        title: "Red Sox ML -139 vs Padres",
        date: "April 4, 2026",
        result: "L",
        url: "red-sox-moneyline-early-padres-fenway-mlb.html",
        image: "images/mlb-red-sox-blue-jays-betting-pick.png"
    },
    {
        sport: "NHL",
        title: "Blues/Ducks UNDER 6 (-105)",
        date: "April 3, 2026",
        result: "L",
        url: "blues-ducks-under-6-honda-center-nhl.html",
        image: "images/utah-mammoth-vegas.png"
    },
    {
        sport: "MLB",
        title: "Twins/Royals UNDER 8.5 (-120)",
        date: "April 1, 2026",
        result: "L",
        url: "twins-royals-under-8-5-joe-ryan-kauffman-mlb.html",
        image: "images/mlb-great-american-ballpark-yankees-reds.png"
    },
    {
        sport: "MLB",
        title: "Giants ML -131 at Padres",
        date: "March 31, 2026",
        result: "W",
        url: "giants-moneyline-webb-padres-petco-park-mlb.html",
        image: "images/mlb-colorado-rockies-brewers-betting-pick.png"
    },
    {
        sport: "MLB",
        title: "Brewers ML -156 vs Rays",
        date: "March 30, 2026",
        result: "L",
        url: "brewers-moneyline-harrison-rays-series-opener-mlb.html",
        image: "images/mlb-giants-dodgers-oracle-park-under-sept-13-2025.png"
    },
    {
        sport: "MLB",
        title: "Brewers ML -157 vs White Sox",
        date: "March 29, 2026",
        result: "W",
        url: "brewers-moneyline-sproat-white-sox-sweep-mlb.html",
        image: "images/mlb-guardians-moneyline-pick-sept-19-2025.png"
    },
    {
        sport: "MLB",
        title: "Yankees at Giants UNDER 8.5 (-110)",
        date: "March 28, 2026",
        result: "W",
        url: "yankees-giants-under-8-5-oracle-park-mlb.html",
        image: "images/mlb-cubs-pirates-betting-pick-sept-17-2025.png"
    },
    {
        sport: "MLB",
        title: "Blue Jays ML -170 vs Athletics",
        date: "March 27, 2026",
        result: "W",
        url: "blue-jays-moneyline-gausman-athletics-opening-series-mlb.html",
        image: "images/mlb-garrett-crochet-fenway-park-sept-02-2025.png"
    },
    {
        sport: "MLB",
        title: "Red Sox ML -158 at Reds",
        date: "March 26, 2026",
        result: "W",
        url: "red-sox-moneyline-crochet-reds-opening-day-mlb.html",
        image: "images/mlb-yankees-bluejays-alds-game4-total-oct-08-2025.png"
    },
    {
        sport: "MLB",
        title: "Yankees at Giants OVER 7 (-110)",
        date: "March 25, 2026",
        result: "P",
        url: "yankees-giants-over-7-opening-day-mlb.html",
        image: "images/mlb-picks-team-logos-july-11-2025.png"
    },
    {
        sport: "NHL",
        title: "Blackhawks +1.5 (-170) / ML (+145)",
        date: "March 24, 2026",
        result: "W",
        url: "blackhawks-puck-line-moneyline-at-islanders-nhl.html",
        image: "images/blackhawks-puck-line-kings-december-4-2025.png"
    },
    {
        sport: "NHL",
        title: "Kraken vs Blue Jackets Under 6.5 (-120)",
        date: "March 21, 2026",
        result: "L",
        url: "kraken-blue-jackets-under-6-5-nhl.html",
        image: "images/nhl.png"
    },
    {
        sport: "NBA",
        title: "Hawks +2.5 at Rockets",
        date: "March 20, 2026",
        result: "L",
        url: "hawks-plus-2-5-at-rockets-nba.html",
        image: "images/warriors-kings-kuminga-over-nov5-2025.png"
    },
    {
        sport: "NHL",
        title: "Devils +110 at Capitals",
        date: "March 20, 2026",
        result: "L",
        url: "devils-moneyline-plus-110-at-capitals-nhl.html",
        image: "images/devils-team-total-under-dallas-december-3-2025.png"
    },
    {
        sport: "NHL",
        title: "Bruins TT Under 3.5 (-150)",
        date: "March 19, 2026",
        result: "L",
        url: "bruins-team-total-under-3-5-jets-nhl.html",
        image: "images/bruins-islanders-under-6-nhl-betting-pick-november-26-2025.png"
    },
    {
        sport: "NHL",
        title: "Senators TT Under 3.5 (-155)",
        date: "March 18, 2026",
        result: "W",
        url: "senators-team-total-under-3-5-at-capitals-nhl.html",
        image: "images/dallas-stars-edmonton-oilers-over-6-nhl-betting-pick-november-25-2025.png"
    },
    {
        sport: "NHL",
        title: "Panthers TT Under 3.5 (-135)",
        date: "March 17, 2026",
        result: "W",
        url: "panthers-team-total-under-3-5-at-canucks-nhl.html",
        image: "images/dallas-stars-team-total-under-minnesota-wild-december-11-2025.png"
    },
    {
        sport: "NHL",
        title: "Penguins at Avalanche OVER 6.5 (-120)",
        date: "March 16, 2026",
        result: "W",
        url: "penguins-avalanche-over-6-5-nhl.html",
        image: "images/anaheim-ducks-nhl-betting-pick-november-19-2025.jpg"
    },
    {
        sport: "NHL",
        title: "Sharks +180 (1u) / +1.5 -140 (3u)",
        date: "March 15, 2026",
        result: "L",
        url: "sharks-moneyline-puck-line-value-at-canadiens-nhl.html",
        image: "images/blackhawks-puck-line-kings-december-4-2025.png"
    },
    {
        sport: "NHL",
        title: "Rangers +167 / +1.5 -150 (3u)",
        date: "March 14, 2026",
        result: "W",
        url: "rangers-hot-streak-moneyline-puck-line-value-at-wild-nhl-march-14-2026.html",
        image: "images/boston-bruins-carolina-hurricanes-nhl-betting-pick-november-17-2025.png"
    },
    {
        sport: "NHL",
        title: "Blues +1.5 (-180)",
        date: "March 13, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260313-blues-puckline",
        image: "images/islanders-nhl-puck-line-betting-pick-nov-10-2025.png"
    },
    {
        sport: "NHL",
        title: "Canadiens at Senators OVER 6.5 (-120)",
        date: "March 11, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260311-mtl-ott-over",
        image: "images/islanders-puck-line-lightning-december-6-2025.png"
    },
    {
        sport: "NHL",
        title: "Sharks vs Sabres OVER 6.5 (-120)",
        date: "March 10, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260310-sharks-sabres-over",
        image: "images/kings-stars-under-5-5-nhl-december-15-2025.jpeg"
    },
    {
        sport: "NHL",
        title: "Kings vs Blue Jackets UNDER 6 (-105)",
        date: "March 9, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260309-kings-bluejackets-under",
        image: "images/los-angeles-kings-ml-utah-mammoth-december-8-2025.png"
    },
    {
        sport: "NHL",
        title: "Avalanche ML -175",
        date: "March 8, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260308-avalanche-moneyline",
        image: "images/montreal-canadiens-puck-line-rangers-december-13-2025.jpg"
    },
    {
        sport: "NHL",
        title: "Kings TT Under 3.5 (-160)",
        date: "March 7, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260307-kings-teamtotal-under",
        image: "images/sharks-flames-nhl-puck-line-nov-13-2025.png"
    },
    {
        sport: "NHL",
        title: "Red Wings ML -150",
        date: "March 6, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260306-redwings-moneyline",
        image: "images/sharksbruins.png"
    },
    {
        sport: "NHL",
        title: "Maple Leafs ML +105",
        date: "March 5, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260305-leafs-moneyline",
        image: "images/nhl-avalanche-utah-road-matchup-oct-21-2025.png"
    },
    {
        sport: "NHL",
        title: "Kraken ML -150",
        date: "March 4, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260304-kraken-moneyline",
        image: "images/nhl-oct19.png"
    },
    {
        sport: "NHL",
        title: "NHL + NCAAB 7-Play Card",
        date: "March 3, 2026",
        result: "6-1",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260303-nhl-ncaab-picks",
        image: "images/nhl.png"
    },
    {
        sport: "NHL",
        title: "Red Wings/Predators U 6.5",
        date: "March 2, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260302-redwings-predators-under",
        image: "images/utah-mammoth-vegas.png"
    },
    {
        sport: "NHL",
        title: "Ducks/Flames Under 6.5",
        date: "March 1, 2026",
        result: "W",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260301-ducks-flames-under",
        image: "images/bruins-islanders-under-6-nhl-betting-pick-november-26-2025.png"
    },
    {
        sport: "NHL",
        title: "NHL Saturday 7-Pick Card",
        date: "February 28, 2026",
        result: "5-2",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260228-nhl-saturday-card",
        image: "images/dallas-stars-edmonton-oilers-over-6-nhl-betting-pick-november-25-2025.png"
    },
    {
        sport: "NHL",
        title: "Sabres ML + Illinois +2.5",
        date: "February 27, 2026",
        result: "1-1",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260227-sabres-illinois",
        image: "images/wild-puck-line-oilers-december-2-2025.png"
    },
    {
        sport: "NHL",
        title: "VGK/Kings Under 5.5 (-115)",
        date: "February 25, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260225-vgk-lak-under",
        image: "images/dallas-stars-team-total-under-minnesota-wild-december-11-2025.png"
    },
    {
        sport: "NBA",
        title: "Raptors -1 vs Thunder",
        date: "February 24, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260224-raptors-minus1",
        image: "images/thunderwin.png"
    },
    {
        sport: "NBA",
        title: "Jazz +13.5 at Rockets",
        date: "February 23, 2026",
        result: "L",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260223-utah-jazz-plus-13",
        image: "images/sacramento-kings-oklahoma-city-thunder-nba-over-betting-pick-total-november-19-2025.png"
    }
];
