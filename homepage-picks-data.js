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
        sport: "MLB",
        title: "Mets ML -126 at Angels McLean Angel Stadium 2u",
        date: "May 2, 2026",
        result: "",
        url: "mets-moneyline-mclean-detmers-angel-stadium-pick-mlb.html",
        image: "images/mets-moneyline-mclean-detmers-angel-stadium-pick-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Sabres/Bruins Over 5.5 (-120) Game 6 TD Garden 3u",
        date: "May 1, 2026",
        result: "",
        url: "sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.html",
        image: "images/sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.jpg"
    },
    {
        sport: "MLB",
        title: "Padres Team Total Under 4.5 (-140) vs White Sox Petco Park 2.5u",
        date: "May 1, 2026",
        result: "",
        url: "padres-team-total-under-4-5-white-sox-marquez-schultz-petco-park-mlb.html",
        image: "images/padres-team-total-under-4-5-white-sox-marquez-schultz-petco-park-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Stars/Wild Over 5.5 (-120) Game 6 Grand Casino Arena 2u",
        date: "April 30, 2026",
        result: "W",
        url: "stars-wild-over-5-5-game-6-grand-casino-arena-nhl.html",
        image: "images/stars-wild-over-5-5-game-6-grand-casino-arena-nhl.jpg"
    },
    {
        sport: "MLB",
        title: "Pirates Team Total Under 4.5 (-135) vs Cardinals PNC Park 2.5u",
        date: "April 30, 2026",
        result: "L",
        url: "pirates-team-total-under-4-5-cardinals-dobbins-pnc-park-skenes-mlb.html",
        image: "images/pirates-team-total-under-4-5-cardinals-dobbins-pnc-park-skenes-mlb.jpg"
    },
    {
        sport: "NBA",
        title: "Lakers ML -175 vs Rockets Crypto.com Arena 3u",
        date: "April 29, 2026",
        result: "L",
        url: "lakers-moneyline-rockets-crypto-com-arena-nba.html",
        image: "images/lakers-moneyline-rockets-crypto-com-arena-nba.jpg"
    },
    {
        sport: "MLB",
        title: "Royals ML +108 at Athletics Sutter Health Park 1u",
        date: "April 29, 2026",
        result: "L",
        url: "royals-moneyline-plus-108-athletics-wacha-severino-sutter-health-park-mlb.html",
        image: "images/royals-moneyline-plus-108-athletics-wacha-severino-sutter-health-park-mlb.jpg"
    },
    {
        sport: "MLB",
        title: "Diamondbacks Team Total Under 4.5 (-140) at Brewers AFF 1.5u",
        date: "April 29, 2026",
        result: "L",
        url: "diamondbacks-team-total-under-sproat-american-family-field-mlb.html",
        image: "images/diamondbacks-team-total-under-sproat-american-family-field-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Ducks/Oilers Under 7 (-115) Game 5 Rogers Place 3u",
        date: "April 28, 2026",
        result: "W",
        url: "ducks-oilers-under-7-game-5-rogers-place-stanley-cup-playoffs-nhl.html",
        image: "images/oilers-mcdavid-ducks-game-5-rogers-place-nhl.png"
    },
    {
        sport: "MLB",
        title: "Tigers ML +106 at Braves Truist Park 1u",
        date: "April 28, 2026",
        result: "L",
        url: "tigers-moneyline-plus-106-braves-mize-perez-truist-park-mlb.html",
        image: "images/tigers-riley-greene-braves-truist-park-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Flyers +1.5 (-210) at Penguins Game 5 3u",
        date: "April 27, 2026",
        result: "W",
        url: "flyers-puck-line-plus-1-5-penguins-game-5-stanley-cup-playoffs-nhl.html",
        image: "images/flyers-celebration-puck-line-penguins-game-5-stanley-cup-playoffs.jpg"
    },
    {
        sport: "MLB",
        title: "Cubs ML +107 at Padres 1.5u",
        date: "April 27, 2026",
        result: "L",
        url: "cubs-moneyline-plus-107-padres-boyd-vasquez-petco-park-mlb.html",
        image: "images/cubs-pete-crow-armstrong-padres-petco-park-april-27-2026.jpg"
    },
    {
        sport: "NHL",
        title: "Ducks Puck Line +1.5 Game 4 at Honda Center 3u",
        date: "April 26, 2026",
        result: "W",
        url: "ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.html",
        image: "images/ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.jpg"
    },
    {
        sport: "MLB",
        title: "Phillies ML +150 vs Braves Nola Sale 1u",
        date: "April 26, 2026",
        result: "L",
        url: "phillies-ml-plus-150-braves-nola-sale-truist-park-mlb.html",
        image: "images/phillies-ml-plus-150-braves-nola-sale-truist-park-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Stars ML +115 Game 4 at Wild 1.5u",
        date: "April 25, 2026",
        result: "L",
        url: "stars-moneyline-plus-115-game-4-wild-grand-casino-arena-nhl.html",
        image: "images/stars-moneyline-plus-115-game-4-wild-grand-casino-arena-nhl.jpg"
    },
    {
        sport: "MLB",
        title: "Rockies / Mets Over 8 Quintana Senga 3u",
        date: "April 25, 2026",
        result: "L",
        url: "rockies-mets-over-8-quintana-senga-citi-field-mlb.html",
        image: "images/rockies-mets-over-8-quintana-senga-citi-field-mlb.jpg"
    },
    {
        sport: "NHL",
        title: "Mammoth ML -110 vs Golden Knights Game 3 3u",
        date: "April 24, 2026",
        result: "W",
        url: "mammoth-moneyline-minus-110-home-ice-golden-knights-game-3-delta-center-nhl.html",
        image: "images/utah-mammoth-home-ice-game-3-april-24-2026.jpg"
    },
    {
        sport: "MLB",
        title: "Reds ML +118 Home Dog vs Tigers 1.5u",
        date: "April 24, 2026",
        result: "W",
        url: "reds-moneyline-plus-118-home-dog-valdez-abbott-great-american-ballpark-mlb.html",
        image: "images/tyler-stephenson-reds-home-dog-tigers-april-24-2026.jpg"
    },
    {
        sport: "NHL",
        title: "Sabres ML -110 at Bruins Game 3 2u",
        date: "April 23, 2026",
        result: "W",
        url: "sabres-moneyline-minus-110-bruins-game-3-td-garden-nhl.html",
        image: "images/sabres-celebration-bruins-game-3-april-23-2026.jpg"
    },
    {
        sport: "MLB",
        title: "Full Card Free Release - 6 MLB Picks (10 Units)",
        date: "April 22, 2026",
        result: "W",
        url: "free-mlb-picks-today-full-card-release-wednesday-april-22-2026.html",
        image: "images/hero-mlb-full-card-free-release-april-22-2026.jpg"
    },
    {
        sport: "NHL",
        title: "Sabres Team Total Under 3.5 (-140) vs Bruins G2",
        date: "April 21, 2026",
        result: "W",
        url: "sabres-team-total-under-3-5-bruins-game-2-stanley-cup-playoffs-nhl.html",
        image: "images/sabres-lafferty-bench-celebration-bruins-g2-april-21-2026.jpg"
    },
    {
        sport: "MLB",
        title: "Giants ML +153 vs Dodgers 2.5u",
        date: "April 21, 2026",
        result: "W",
        url: "giants-moneyline-plus-153-roupp-dodgers-oracle-park-mlb.html",
        image: "images/landen-roupp-giants-pitcher-april-21-2026.jpg"
    },
    {
        sport: "NHL",
        title: "Ducks ML +160 (1.5u) & +1.5 -155 (3u) at Oilers G1",
        date: "April 20, 2026",
        result: "W",
        url: "ducks-moneyline-plus-160-puck-line-oilers-game-1-stanley-cup-playoffs-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_png/v1776402055/prd/yukw5jm35s8csetqt4xg.png"
    },
    {
        sport: "NHL",
        title: "Kings +1.5 (-125) at Avalanche Game 1 1u",
        date: "April 18, 2026",
        result: "W",
        url: "kings-plus-1-5-puck-line-avalanche-game-1-stanley-cup-playoffs-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/v1772774164/prd/h2qw1ix5gixoeumq24wf"
    },
    {
        sport: "MLB",
        title: "White Sox ML (+131) at Athletics 2u",
        date: "April 18, 2026",
        result: "W",
        url: "white-sox-moneyline-plus-131-fedde-athletics-sacramento-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/607200/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Rockies ML (+235) vs Dodgers 2u",
        date: "April 18, 2026",
        result: "W",
        url: "rockies-moneyline-plus-235-home-dog-sheehan-coors-field-dodgers-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/686668/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Reds ML (+154) at Twins 2.5u",
        date: "April 17, 2026",
        result: "W",
        url: "reds-moneyline-williamson-twins-target-field-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/668715/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Canucks/Oilers OVER 6.5 (-125) 2.5u",
        date: "April 16, 2026",
        result: "W",
        url: "canucks-oilers-over-6-5-total-edmonton-powerplay-rogers-place-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/f_auto/prd/rm9h99mderwz4cfkooqf.jpg"
    },
    {
        sport: "NHL",
        title: "Maple Leafs +1.5 (-145) at Senators 2.5u",
        date: "April 15, 2026",
        result: "L",
        url: "maple-leafs-plus-1-5-puck-line-battle-of-ontario-senators-nhl.html",
        image: "images/blackhawks-plus-1-5-maple-leafs-december-16-2025.jpeg"
    },
    {
        sport: "NHL",
        title: "Kraken +1.5 (-108) at Golden Knights",
        date: "April 15, 2026",
        result: "L",
        url: "kraken-plus-1-5-puck-line-daccord-tortorella-vegas-nhl.html",
        image: "https://images.foxtv.com/static.q13fox.com/www.q13fox.com/content/uploads/2026/01/764/432/gettyimages-2255003397-e1767763673947.jpg"
    },
    {
        sport: "NHL",
        title: "Caps/Blue Jackets UNDER 6.5 (-115) 2u",
        date: "April 14, 2026",
        result: "W",
        url: "capitals-blue-jackets-under-6-5-thompson-greaves-nationwide-arena-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1768186620/prd/jxstb4k7jjm1ky3yrlp1"
    },
    {
        sport: "MLB",
        title: "Rangers ML (-111) at Athletics 2.5u",
        date: "April 14, 2026",
        result: "L",
        url: "rangers-moneyline-gore-strikeouts-athletics-sacramento-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/656427/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Wild/Blues UNDER 5.5 (-105) 3u",
        date: "April 13, 2026",
        result: "L",
        url: "wild-blues-under-5-5-gustavsson-hofer-enterprise-center-nhl.html",
        image: "images/wild-puck-line-oilers-december-2-2025.png"
    },
    {
        sport: "MLB",
        title: "Yankees/Angels UNDER 9.5 (-115)",
        date: "April 13, 2026",
        result: "L",
        url: "yankees-angels-under-9-5-warren-kikuchi-yankee-stadium-mlb.html",
        image: "https://images2.minutemediacdn.com/image/upload/c_crop,x_0,y_239,w_3174,h_1785/c_fill,w_720,ar_16:9,f_auto,q_auto,g_auto/images/ImagnImages/mmsport/inside_the_pinstripes/01kk6p6ywmpepmzg6g9m.jpg"
    },
    {
        sport: "NHL",
        title: "Mammoth/Flames UNDER 6 (-110)",
        date: "April 12, 2026",
        result: "W",
        url: "mammoth-flames-under-6-saddledome-calgary-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/c1c01ufph2bsqfq0npsu.jpg"
    },
    {
        sport: "MLB",
        title: "Giants ML -114 at Orioles (3u)",
        date: "April 11, 2026",
        result: "L",
        url: "giants-moneyline-webb-orioles-camden-yards-mlb.html",
        image: "https://img.mlbstatic.com/mlb-images/image/upload/t_2x1/t_w1536/v1773507436/mlb/rsxmjlczbv0elpmrsm6c.jpg"
    },
    {
        sport: "MLB",
        title: "Rangers/Dodgers UNDER 9 (-138)",
        date: "April 10, 2026",
        result: "L",
        url: "rangers-dodgers-under-9-glasnow-rocker-dodger-stadium-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/607192/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cardinals/Nationals OVER 8.5 (-110)",
        date: "April 8, 2026",
        result: "L",
        url: "cardinals-nationals-over-8-5-runs-nationals-park-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/676475/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Blues +1.5 (-190) & ML (+130) vs Avalanche",
        date: "April 7, 2026",
        result: "L",
        url: "blues-puck-line-moneyline-avalanche-enterprise-center-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1775448838/prd/trepka02swudorxhugpg"
    },
    {
        sport: "MLB",
        title: "Braves F5 ML -150 at Angels",
        date: "April 6, 2026",
        result: "L",
        url: "braves-f5-moneyline-sale-dominates-angels-mlb.html",
        image: "https://a.espncdn.com/photo/2026/0401/r1637364_1296x729_16-9.jpg"
    },
    {
        sport: "MLB",
        title: "Mariners ML -162 at Angels",
        date: "April 5, 2026",
        result: "L",
        url: "mariners-moneyline-castillo-angels-rubber-match-mlb.html",
        image: "https://img.mlbstatic.com/mlb-images/image/upload/t_2x1/t_w1536/mlb/vtmwkwrwxgev9wnb0hwg.jpg"
    },
    {
        sport: "MLB",
        title: "Red Sox ML -139 vs Padres",
        date: "April 4, 2026",
        result: "L",
        url: "red-sox-moneyline-early-padres-fenway-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/813349/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Blues/Ducks UNDER 6 (-105)",
        date: "April 3, 2026",
        result: "L",
        url: "blues-ducks-under-6-honda-center-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/prd/btwtujci49zhm95003ov"
    },
    {
        sport: "MLB",
        title: "Twins/Royals UNDER 8.5 (-120)",
        date: "April 1, 2026",
        result: "L",
        url: "twins-royals-under-8-5-joe-ryan-kauffman-mlb.html",
        image: "http://res.cloudinary.com/ybmedia/image/upload/c_crop,e_improve,h_513,w_912,x_0,y_0/c_fill,f_auto,h_900,q_auto,w_1600/v1/m/9/e/9e1649e8af5186e9ea20d235baeb9c780cf47287/01kmp1d5y8pw48g3nscg.jpg"
    },
    {
        sport: "MLB",
        title: "Giants ML -131 at Padres",
        date: "March 31, 2026",
        result: "W",
        url: "giants-moneyline-webb-padres-petco-park-mlb.html",
        image: "https://img.mlbstatic.com/mlb-images/image/upload/t_2x1/t_w1536/v1773507436/mlb/rsxmjlczbv0elpmrsm6c.jpg"
    },
    {
        sport: "MLB",
        title: "Brewers ML -156 vs Rays",
        date: "March 30, 2026",
        result: "L",
        url: "brewers-moneyline-harrison-rays-series-opener-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/690986/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Brewers ML -157 vs White Sox",
        date: "March 29, 2026",
        result: "W",
        url: "brewers-moneyline-sproat-white-sox-sweep-mlb.html",
        image: "https://a.espncdn.com/photo/2026/0326/r1634325_1296x729_16-9.jpg"
    },
    {
        sport: "MLB",
        title: "Yankees at Giants UNDER 8.5 (-110)",
        date: "March 28, 2026",
        result: "W",
        url: "yankees-giants-under-8-5-oracle-park-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/701542/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Blue Jays ML -170 vs Athletics",
        date: "March 27, 2026",
        result: "W",
        url: "blue-jays-moneyline-gausman-athletics-opening-series-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/592332/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Red Sox ML -158 at Reds",
        date: "March 26, 2026",
        result: "W",
        url: "red-sox-moneyline-crochet-reds-opening-day-mlb.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/676979/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Yankees at Giants OVER 7 (-110)",
        date: "March 25, 2026",
        result: "P",
        url: "yankees-giants-over-7-opening-day-mlb.html",
        image: "https://img.mlbstatic.com/mlb-images/image/upload/t_16x9/t_w1024/mlb/i8rrz7i5pyfxit8mo78l"
    },
    {
        sport: "NHL",
        title: "Blackhawks +1.5 (-170) / ML (+145)",
        date: "March 24, 2026",
        result: "W",
        url: "blackhawks-puck-line-moneyline-at-islanders-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/p02oc3irhchowhosjttd"
    },
    {
        sport: "NHL",
        title: "Kraken vs Blue Jackets Under 6.5 (-120)",
        date: "March 21, 2026",
        result: "L",
        url: "kraken-blue-jackets-under-6-5-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/xrvcgou7nncebdksdrg1.jpg"
    },
    {
        sport: "NBA",
        title: "Hawks +2.5 at Rockets",
        date: "March 20, 2026",
        result: "L",
        url: "hawks-plus-2-5-at-rockets-nba.html",
        image: "https://www.orlandosentinel.com/wp-content/uploads/2026/03/Magic-Hawks-Basketball-5.jpg?w=1600&resize=1600,900"
    },
    {
        sport: "NHL",
        title: "Devils +110 at Capitals",
        date: "March 20, 2026",
        result: "L",
        url: "devils-moneyline-plus-110-at-capitals-nhl.html",
        image: "https://platform.allaboutthejersey.com/wp-content/uploads/sites/6/2026/03/gettyimages-2266728853.jpg"
    },
    {
        sport: "NHL",
        title: "Bruins TT Under 3.5 (-150)",
        date: "March 19, 2026",
        result: "L",
        url: "bruins-team-total-under-3-5-jets-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/mowaqhfcoindv24tzzax.jpg"
    },
    {
        sport: "NHL",
        title: "Senators TT Under 3.5 (-155)",
        date: "March 18, 2026",
        result: "W",
        url: "senators-team-total-under-3-5-at-capitals-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1773114872/prd/e3gfsrtvzz0kxmyd7vaa"
    },
    {
        sport: "NHL",
        title: "Panthers TT Under 3.5 (-135)",
        date: "March 17, 2026",
        result: "W",
        url: "panthers-team-total-under-3-5-at-canucks-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/al0kehobnis0ep3ehn3s.jpg"
    },
    {
        sport: "NHL",
        title: "Penguins at Avalanche OVER 6.5 (-120)",
        date: "March 16, 2026",
        result: "W",
        url: "penguins-avalanche-over-6-5-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/prd/hlvywrl77gjjekmzt3qg"
    },
    {
        sport: "NHL",
        title: "Sharks +180 (1u) / +1.5 -140 (3u)",
        date: "March 15, 2026",
        result: "L",
        url: "sharks-moneyline-puck-line-value-at-canadiens-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1772057935/prd/v3ftqvttong49pvykmt0"
    },
    {
        sport: "NHL",
        title: "Rangers +167 / +1.5 -150 (3u)",
        date: "March 14, 2026",
        result: "W",
        url: "rangers-hot-streak-moneyline-puck-line-value-at-wild-nhl-march-14-2026.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/prd/hlx0hqpifhq8kfmt1y9x"
    }
];
