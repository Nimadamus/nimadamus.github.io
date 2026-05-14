// ============================================================
// HOMEPAGE PICKS DATA - BetLegend Latest Picks & Analysis
// ============================================================
//
// HOW THIS WORKS:
// - First 6 picks show as large featured cards (title + image)
// - Picks 7+ show in compact grid (4 per row, 2 rows = 8 per page)
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
        title: "Ducks Team Total Under 3.5 vs Golden Knights: Game 6 Scoring Ceiling",
        date: "May 14, 2026",
        url: "ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.html",
        image: "images/ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.jpg"
    },
    {
        sport: "MLB",
        title: "Brewers Moneyline -139 vs Padres: Harrison Edge At Home",
        date: "May 14, 2026",
        url: "brewers-moneyline-minus-139-padres-canning-harrison-mlb-pick-may-14-2026.html",
        image: "images/brewers.webp"
    },
    {
        sport: "NHL",
        title: "Canadiens at Sabres Game 5 Preview - May 14, 2026",
        date: "May 14, 2026",
        url: "canadiens-sabres-game-5-featured-game-of-the-day.html",
        image: "images/sabres-celebration-bruins-game-3-april-23-2026.jpg"
    },
    {
        sport: "MLB",
        title: "MLB Thursday Preview: Full 11-Game Board for May 14, 2026",
        date: "May 14, 2026",
        url: "mlb-preview-today-eleven-game-board-betting-analysis.html",
        image: "images/mlb-great-american-ballpark-yankees-reds.webp"
    },
    {
        sport: "NHL",
        title: "NHL Playoff Preview: Canadiens-Sabres Game 5 and Golden Knights-Ducks Game 6",
        date: "May 14, 2026",
        url: "canadiens-sabres-golden-knights-ducks-nhl-playoff-preview.html",
        image: "images/sabres-celebration-bruins-game-3-april-23-2026.jpg"
    },
    {
        sport: "NBA",
        title: "NBA Playoff Reset: No Games on Thursday, May 14, 2026",
        date: "May 14, 2026",
        url: "nba-playoff-reset-cavaliers-pistons-spurs-timberwolves-game-six.html",
        image: "images/thunderwin.webp"
    },
    {
        sport: "MLB",
        title: "Angels Team Total Under 3.5 vs Guardians: Parker Messick Sets The Bar",
        date: "May 13, 2026",
        url: "angels-team-total-under-3-5-guardians-messick-progressive-field-mlb-pick.html",
        image: "images/angels.webp"
    },
    {
        sport: "NHL",
        title: "Vegas Golden Knights Moneyline -150 vs Ducks Game 5",
        date: "May 12, 2026",
        url: "vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.html",
        image: "images/ducks-puck-line-plus-1-5-game-4-oilers-honda-center-nhl.jpg"
    },
    {
        sport: "NBA",
        title: "NBA Conference Semifinals Monday At Crypto.com Arena And Rocket Arena - Thunder At Lakers Sweep Watch And Pistons At Cavaliers Game 4",
        date: "May 11, 2026",
        url: "thunder-sweep-watch-pistons-cavs-game-4-east-west-semis-nba.html",
        image: "images/thunderwin.webp"
    },
    {
        sport: "NBA",
        title: "Lakers +11 vs Thunder Game 4, Elimination Spot Creates Double-Digit Spread Value",
        date: "May 11, 2026",
        url: "lakers-plus-11-thunder-game-4-elimination-spot-nba-pick.html",
        image: "images/thunderwin.webp"
    },
    {
        sport: "MLB",
        title: "Astros ML +124 vs Mariners, Peter Lambert Gives Houston A Live Home Underdog Path",
        date: "May 11, 2026",
        url: "astros-moneyline-plus-124-mariners-kirby-lambert-daikin-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/663567/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Avalanche vs Wild",
        date: "May 11, 2026",
        url: "avalanche-vs-wild-nhl-western-semis-game-4-analysis-stats-preview.html",
        image: "images/nhl-avalanche-utah-road-matchup-oct-21-2025.webp"
    },
    {
        sport: "Soccer",
        title: "Tottenham-Leeds And Rayo-Girona Turn Monday Into A Relegation-Stress Soccer Card",
        date: "May 11, 2026",
        url: "tottenham-leeds-survival-rayo-girona-relegation-soccer.html",
        image: "images/soccer-armenia-ireland-corner-betting-oct-14-2025.webp"
    },
    {
        sport: "MLB",
        title: "MLB Monday Six-Pack May 11 2026 - Sasaki Returns At Dodger Stadium, Kirby Travels To Daikin Park, Rasmussen At Rogers Centre, Eovaldi At Globe Life Field",
        date: "May 11, 2026",
        url: "sasaki-kirby-rasmussen-eovaldi-monday-six-pack-mlb.html",
        image: "images/mlb-bryan-woo-mariners-yankees-pitching.webp"
    },
    {
        sport: "NHL",
        title: "Stanley Cup Playoffs Round 2 Monday At Grand Casino Arena - Avalanche At Wild Game 4 After Minnesota's 5-1 Game 3 Thrashing",
        date: "May 11, 2026",
        url: "avalanche-wild-game-4-pivot-second-round-monday-nhl.html",
        image: "images/nhl-avalanche-utah-road-matchup-oct-21-2025.webp"
    },
    {
        sport: "MLB",
        title: "MLB Sunday Preview: Full 15-Game Board for May 10, 2026",
        date: "May 10, 2026",
        url: "sunday-fifteen-game-mlb-preview-may-10-2026.html",
        image: "images/mlb-great-american-ballpark-yankees-reds.webp"
    },
    {
        sport: "NHL",
        title: "NHL Playoff Preview: Sabres vs Canadiens and Golden Knights vs Ducks for May 10, 2026",
        date: "May 10, 2026",
        url: "sabres-canadiens-knights-ducks-game-3-4-nhl-may-10-2026.html",
        image: "images/sabres-celebration-bruins-game-3-april-23-2026.jpg"
    },
    {
        sport: "NBA",
        title: "NBA Playoff Preview: Knicks vs 76ers and Spurs vs Timberwolves for May 10, 2026",
        date: "May 10, 2026",
        url: "knicks-76ers-spurs-wolves-game-4-east-west-semis-nba-may-10-2026.html",
        image: "images/thunderwin.webp"
    },
    {
        sport: "MLB",
        title: "Nationals vs Marlins Pick: Washington Moneyline at loanDepot Park",
        date: "May 9, 2026",
        url: "nationals-moneyline-plus-139-marlins-littell-junk-loandepot-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/695578/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Braves vs Dodgers Pick: Atlanta Moneyline at Dodger Stadium",
        date: "May 9, 2026",
        url: "braves-moneyline-plus-152-dodgers-strider-snell-dodger-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/675911/action/hero/current"
    },
    {
        sport: "NBA",
        title: "Pistons vs Cavaliers Game 3 Preview: Cleveland Looks To Respond At Home",
        date: "May 9, 2026",
        url: "pistons-vs-cavaliers-eastern-semis-game-3-analysis-stats-preview-may-9-2026.html",
        image: "images/brooklyn-nets-pistons-nba-betting-analysis-nov7-2025.webp"
    },
    {
        sport: "NHL",
        title: "NHL Playoff Preview: Hurricanes vs Flyers and Avalanche vs Wild for May 9, 2026",
        date: "May 9, 2026",
        url: "hurricanes-flyers-avalanche-wild-nhl-may-9-2026.html",
        image: "images/sabres-celebration-bruins-game-3-april-23-2026.jpg"
    },
    {
        sport: "NBA",
        title: "Knicks vs 76ers Game 3 Preview: New York Looks To Extend Series Lead In Philadelphia",
        date: "May 8, 2026",
        url: "knicks-vs-76ers-eastern-semis-game-3-analysis-stats-preview-may-8-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Friday Fifteen-Game Slate Headlined By Sale Vs Sheehan At Dodger Stadium And Max Fried Vs Jacob Misiorowski At American Family Field",
        date: "May 8, 2026",
        url: "sale-fried-friday-fifteen-game-slate-mlb-may-8-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Stanley Cup Playoffs Round 2 Friday At KeyBank Center And Honda Center - Canadiens At Sabres With Buffalo Up 1-0 And Golden Knights At Ducks With The Series Tied 1-1",
        date: "May 8, 2026",
        url: "sabres-canadiens-knights-ducks-second-round-game-fest-nhl-may-8-2026.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_png/v1778649049/prd/e88hxynf2fqdg8iim4zc.png"
    },
    {
        sport: "NBA",
        title: "NBA Playoff Preview: Knicks vs 76ers and Spurs vs Timberwolves for May 8, 2026",
        date: "May 8, 2026",
        url: "knicks-76ers-spurs-wolves-game-3-east-west-semis-nba-may-8-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "Soccer",
        title: "Bundesliga Round 33 And La Liga Friday At Signal Iduna Park And Estadi Ciutat De Valencia - Dortmund Vs Frankfurt And Levante Vs Osasuna With Champions League Spots And Relegation On The Line",
        date: "May 8, 2026",
        url: "dortmund-frankfurt-bundesliga-levante-osasuna-laliga-soccer-may-8-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NBA",
        title: "Conference Semifinals Game 2 Thursday At Little Caesars Arena And Paycom Center - Cavaliers At Pistons With Detroit -3.5 And Lakers At Thunder With Oklahoma City -15.5 As Both Series Sit At 1-0",
        date: "May 7, 2026",
        url: "thunder-cavaliers-2-0-leads-east-west-semis-nba-may-7-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Hurricanes At Flyers Game 3 At Wells Fargo Center - Carolina Hunts The Road 3-0 Stranglehold While Philadelphia Plays The Series-Saving Home Game With The Total At 5.5",
        date: "May 7, 2026",
        url: "hurricanes-flyers-game-3-second-round-nhl-may-7-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Gore Vs Blackburn In The Bronx, Imanaga Hosts Lowder At Wrigley, And Scott Vs Quintana In The Coors Makeup Game Headline The Thursday Slate",
        date: "May 7, 2026",
        url: "gore-blackburn-yankees-rangers-thursday-mlb-may-7-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Sabres vs Canadiens Pick: Under 6.5 in Game 1",
        date: "May 6, 2026",
        url: "sabres-canadiens-under-6-5-game-1-second-round-keybank-center-nhl-pick.html",
        image: "images/sabres-canadiens-under-6-5-game-1-second-round-keybank-center-nhl-pick.jpg"
    },
    {
        sport: "MLB",
        title: "Athletics vs Phillies Pick: Oakland Moneyline at Citizens Bank Park",
        date: "May 6, 2026",
        url: "athletics-moneyline-plus-156-phillies-springs-wheeler-citizens-bank-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/667670/action/hero/current"
    },
    {
        sport: "NHL",
        title: "NHL Playoff Preview: Canadiens vs Sabres and Ducks vs Golden Knights for May 6, 2026",
        date: "May 6, 2026",
        url: "sabres-host-canadiens-game-1-knights-host-ducks-game-2-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_png/v1778649049/prd/e88hxynf2fqdg8iim4zc.png"
    },
    {
        sport: "NBA",
        title: "NBA Playoff Preview: 76ers vs Knicks and Timberwolves vs Spurs for May 6, 2026",
        date: "May 6, 2026",
        url: "knicks-host-sixers-spurs-host-wolves-conference-semis-nba.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "MLB Preview: Wednesday Eleven-Game Board for May 6, 2026",
        date: "May 6, 2026",
        url: "eovaldi-warren-ober-mikolas-eleven-game-wednesday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "DeGrom Heads Into Yankee Stadium With The Rangers, Alcantara Hosts Baltimore At LoanDepot Park, And Gausman Brings Toronto To Tampa Bay On A 10-Game Tuesday Slate",
        date: "May 5, 2026",
        url: "degrom-alcantara-gausman-tuesday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Yoshinobu Yamamoto Climbs The Mound At Daikin Park Opposite Colton Gordon As The Dodgers Open A Three-Game Series In Houston And A Twelve-Game Monday Carries Coast-To-Coast",
        date: "May 4, 2026",
        url: "yamamoto-gordon-twelve-game-monday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Wrobleski And Dustin May At Busch, Yesavage Climbs The Hill At Target Field, And Jack Leiter Anchors Sunday Night Baseball At Comerica As The MLB Sunday Slate Carries Fifteen Games Coast To Coast",
        date: "May 3, 2026",
        url: "wrobleski-yesavage-leiter-fifteen-game-sunday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Sasaki Anchors Dodgers-Cardinals At Busch, Painter Climbs The Hill In Miami, And A Coast-To-Coast Fifteen-Game MLB Saturday Carries Premium Pitching From The Afternoon Through The Late West Coast Window",
        date: "May 2, 2026",
        url: "sasaki-mclean-painter-fifteen-game-saturday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Sabres vs Bruins Game 6 Pick: Over 5.5 at TD Garden",
        date: "May 1, 2026",
        url: "sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.html",
        image: "images/sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.jpg"
    },
    {
        sport: "NBA",
        title: "Three Friday Game 6s With Houston Halfway To The First 3-0 Comeback In NBA History And Two Eastern Closeout Spots",
        date: "May 1, 2026",
        url: "three-friday-game-6s-rockets-history-bid-magic-cavs-elimination-nba.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Three Friday Game 6s With Closeout Spots In Montreal Boston And Salt Lake City",
        date: "May 1, 2026",
        url: "three-friday-game-6s-canadiens-sabres-knights-elimination-night-nhl.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Friday MLB Rotation With Yankees-Orioles At The Stadium And Dodgers-Cardinals Headlining The NL Slate",
        date: "May 1, 2026",
        url: "mlb-friday-rotation-yankees-cubs-pirates-divisional-action-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "NBA",
        title: "Celtics Visit Philadelphia For Game 6 With A 3-2 Series Lead And A Second-Round Ticket Within Reach At The Wells Fargo Center",
        date: "April 30, 2026",
        url: "celtics-vs-76ers-game-6-eastern-conference-philadelphia-nba-analysis-stats-preview.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Stars At Wild Game 6 In Saint Paul With Minnesota One Win From Eliminating The Western Conference Favorite",
        date: "April 30, 2026",
        url: "stars-wild-game-6-elimination-night-saint-paul-nhl.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Nine MLB Games On Thursday Headlined By Skenes At PNC Park Valdez In Atlanta And Gausman At Target Field",
        date: "April 30, 2026",
        url: "nine-game-thursday-skenes-valdez-gausman-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Skubal Headlines A 15-Game MLB Wednesday With Glasnow-Alcantara At Dodger Stadium And Webb Anchoring Phillies-Giants",
        date: "April 29, 2026",
        url: "midweek-rotation-arms-divisional-clashes-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "NBA",
        title: "Three Game 5s Anchor A Wednesday Elimination Night With Cavs-Raptors Tied 2-2 And Lakers-Rockets In A Closeout Spot",
        date: "April 29, 2026",
        url: "eastern-elimination-night-three-game-5s-nba.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Ohtani Returns To The Dodger Stadium Mound, deGrom Anchors Yankees-Rangers In Texas, And A Coast-To-Coast Fifteen-Game Tuesday Defines The Late-April Schedule",
        date: "April 28, 2026",
        url: "ohtani-degrom-bibee-burns-fifteen-game-tuesday-mlb.html",
        image: "newlogo.png"
    },
    {
        sport: "NBA",
        title: "Three NBA Game 5s Anchor A Tuesday Of Closeouts And A Tied Series With Knicks-Hawks Even At MSG, Tatum's Celtics Hunting A 4-1 Out, And Wembanyama Back To Lock The Spurs Sweep Window",
        date: "April 28, 2026",
        url: "knicks-hawks-tied-celtics-spurs-closeouts-tuesday-nba.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Three NHL Game 5s Anchor A Tuesday Of Eliminations With Bruins Facing The Wall In Buffalo, Wild-Stars Tied At American Airlines Center, And McDavid's Oilers Trailing Anaheim 1-3 At Home",
        date: "April 28, 2026",
        url: "bruins-elimination-night-wild-stars-tied-ducks-oilers-tuesday-nhl.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Flyers Puck Line +1.5 (-210) vs Penguins Game 5: Philadelphia One Win Away From A Cross-State Series Win",
        date: "April 27, 2026",
        url: "flyers-puck-line-plus-1-5-penguins-game-5-stanley-cup-playoffs-nhl.html",
        image: "images/flyers-celebration-puck-line-penguins-game-5-stanley-cup-playoffs.jpg"
    },
    {
        sport: "MLB",
        title: "Cubs Moneyline +107 vs Padres at Petco Park: Plus-Money Road Dog In A Pitcher's Park",
        date: "April 27, 2026",
        url: "cubs-moneyline-plus-107-padres-boyd-vasquez-petco-park-mlb.html",
        image: "images/cubs-pete-crow-armstrong-padres-petco-park-april-27-2026.jpg"
    },
    {
        sport: "NBA",
        title: "Wolves Chase A Closeout Without Edwards, Thunder Hunt The Sweep In Phoenix, And A Cunningham-Banchero Game 4 Anchors The Monday Slate",
        date: "April 27, 2026",
        url: "wolves-close-out-attempt-thunder-sweep-pistons-magic-monday-nba-april-27-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NBA",
        title: "Wolves at Nuggets - Game 5 Closeout Watch In Denver With Edwards Out And Dosunmu Riding A 43-Point Wave",
        date: "April 27, 2026",
        url: "wolves-vs-nuggets-nba-analysis-stats-preview-april-27-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "Soccer",
        title: "Manchester United Host Brentford At Old Trafford Chasing Champions League Qualification On A Three-Match European Monday",
        date: "April 27, 2026",
        url: "manchester-united-brentford-old-trafford-monday-soccer-april-27-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "Betting",
        title: "Handicapping and Trends Hub",
        date: "April 27, 2026",
        url: "handicapping-hub-archive/hub-2026-04-27.html",
        image: "newlogo.png"
    },
    {
        sport: "MLB",
        title: "Fried-Leiter Anchors Yankees-Rangers In Texas, Yamamoto Returns To The Dodger Stadium Mound, And A Coast-To-Coast Eight-Game Monday Defines The Late-April Schedule",
        date: "April 27, 2026",
        url: "fried-leiter-yankees-rangers-yamamoto-dodgers-monday-mlb-april-27-2026.html",
        image: "newlogo.png"
    },
    {
        sport: "NHL",
        title: "Flyers Hunt The Closeout In Pittsburgh, Vegas Tries To Stop Utah's First-Round Run, And Two Game-Day Series Pivots Anchor The Monday NHL Slate",
        date: "April 27, 2026",
        url: "flyers-clinch-bid-knights-mammoth-monday-nhl-april-27-2026.html",
        image: "newlogo.png"
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
        image: "images/wild-puck-line-oilers-december-2-2025.webp"
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
