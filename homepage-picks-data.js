// ============================================================
// HOMEPAGE PICKS DATA - BetLegend Latest Sheet Picks
// ============================================================
//
// HOW THIS WORKS:
// - First 6 picks show as large featured cards (title + image)
// - Picks 7+ show in compact grid (4 per row, 2 rows = 8 per page)
// - Cards display LEFT to RIGHT, newest first
// - Pagination handles older picks beyond the first 10
// - Only Google Sheet betting picks belong here.
// - Do not add Featured Game of the Day articles, sport preview/slate articles,
//   news, guide, or hub pages to this feed. Route those through their proper
//   navigation surfaces instead.
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
        title: "Cubs, Guardians, Astros Moneylines and Mariners Run Line (-1.5): Four Home Favorites Behind The Better Arm",
        date: "June 29, 2026",
        url: "cubs-guardians-astros-moneyline-mariners-run-line-card-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/669923/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Rangers Under 3.6, Dodgers Under 5.5, and Red Sox Over 4.5: Three Pitching-Driven Team Totals",
        date: "June 29, 2026",
        url: "rangers-dodgers-team-total-unders-red-sox-over-card-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/641778/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Braves and Giants Under 7.5: Two Veteran Lefties Meet At Oracle Park",
        date: "June 28, 2026",
        url: "braves-giants-under-7-5-sale-ray-oracle-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/592662/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Mariners and Guardians Under 7.5: A Pitcher-Friendly Afternoon In Cleveland",
        date: "June 28, 2026",
        url: "mariners-guardians-under-7-5-hancock-williams-progressive-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/668909/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Brewers ML (-152) and Cubs Team Total Under 3.5 (-115): Kyle Harrison's 2.50 ERA And The NL-Best 50-29 Brewers Host David Peterson And The Cubs",
        date: "June 27, 2026",
        url: "brewers-moneyline-cubs-team-total-under-harrison-peterson-american-family-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/656849/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Giants ML (-125) and Braves Team Total Under 3.5 (-115): Logan Webb And Oracle Park Slow Atlanta's Bats As San Francisco Plays Home Favorite",
        date: "June 27, 2026",
        url: "giants-moneyline-braves-team-total-under-webb-elder-oracle-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/693821/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Padres Team Total Under 3.5 (-145) and Mariners/Guardians Under 7.5 (-120): Yamamoto And Logan Gilbert Anchor A Two-Game Unders Card In Pitcher-Friendly Parks",
        date: "June 27, 2026",
        url: "padres-team-total-under-mariners-guardians-under-yamamoto-gilbert-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/669302/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Brewers Run Line -1 (-185): Jacob Misiorowski And The NL-Best 49-29 Brewers Lay A Run On The Cubs At American Family Field",
        date: "June 26, 2026",
        url: "brewers-run-line-cubs-team-total-under-misiorowski-rea-american-family-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/694192/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Dodgers ML (-137): The Best Record In Baseball Behind Roki Sasaki Visits Walker Buehler And The Padres At Petco Park",
        date: "June 26, 2026",
        url: "dodgers-moneyline-padres-team-total-under-sasaki-buehler-petco-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/605141/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Red Sox Team Total Under 3.5 (-130): Cam Schlittler's 1.71 ERA Smothers A 32-46 Boston Lineup As The Yankees Visit Fenway",
        date: "June 25, 2026",
        url: "yankees-moneyline-red-sox-team-total-under-schlittler-fenway-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/693645/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Phillies ML (-158): Cristopher Sanchez's 1.80 ERA And A 44-36 Phillies Club Against Cade Cavalli At Nationals Park",
        date: "June 25, 2026",
        url: "phillies-moneyline-nationals-team-total-under-sanchez-cavalli-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/650911/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Rays ML (-146): A 43-33 Tampa Bay Club Hosts A 34-46 Royals Lineup As Griffin Jax Takes The Ball At The Trop",
        date: "June 24, 2026",
        url: "rays-moneyline-royals-jax-cameron-tropicana-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/643377/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Twins Team Total Under 3.5 (-150): Minnesota's Strikeout-Heavy Lineup Against Shohei Ohtani's 1.47 ERA And 0.88 WHIP",
        date: "June 24, 2026",
        url: "twins-team-total-under-dodgers-ohtani-target-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/621439/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Rays ML (-180): Shane McClanahan's Strikeout Arm Against A 33-46 Royals Lineup And Luinder Avila's 1.71 WHIP",
        date: "June 23, 2026",
        url: "rays-moneyline-royals-mcclanahan-avila-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/691406/action/hero/current",
        result: "L"
    },
    {
        sport: "MLB",
        title: "Giants/Athletics Under 9 (-115): Oracle Park Run-Suppression With Robbie Ray And Aaron Civale In Baseball's Toughest Park To Score",
        date: "June 23, 2026",
        url: "giants-athletics-under-9-civale-ray-oracle-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/671218/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Brewers ML (-144): The NL-Best Brewers And Brandon Woodruff's 3.60 ERA Against Brady Singer At Great American Ball Park",
        date: "June 22, 2026",
        url: "brewers-moneyline-reds-woodruff-singer-great-american-ball-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/605540/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Astros/Blue Jays Under 7 (+105): Hunter Brown's 1.10 ERA Against Dylan Cease's 110 Strikeouts At Rogers Centre",
        date: "June 22, 2026",
        url: "astros-blue-jays-under-7-brown-cease-rogers-centre-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/686613/action/hero/current",
        result: "W"
    },
    {
        sport: "MLB",
        title: "Phillies ML (-167): Zack Wheeler's 2.01 ERA Against A 5.91 Arm In David Peterson At Citizens Bank Park",
        date: "June 21, 2026",
        result: "W",
        url: "phillies-moneyline-mets-wheeler-peterson-citizens-bank-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/656941/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Angels/Athletics Over 9 (-120): Jack Perkins' 6.15 ERA And A Hitter-Friendly Sutter Health Park",
        date: "June 21, 2026",
        result: "W",
        url: "angels-athletics-over-9-detmers-perkins-sutter-health-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/545361/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cardinals ML (-123): Dustin May's 3.75 ERA Backs The Better Team Against A 32-45 Royals Club At Kauffman Stadium",
        date: "June 21, 2026",
        result: "W",
        url: "cardinals-moneyline-royals-may-kolek-kauffman-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/669160/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Mets Team Total Under 3.5 (-150): A Lineup Without Lindor And Alvarez Faces Cristopher Sanchez's 1.82 ERA In Philadelphia",
        date: "June 20, 2026",
        result: "W",
        url: "mets-team-total-under-3-5-phillies-sanchez-citizens-bank-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/665742/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Rockies Team Total Under 4.5 (-152): Paul Skenes And A 0.93 WHIP Quiet A Depleted Colorado Lineup At Coors Field",
        date: "June 20, 2026",
        result: "W",
        url: "rockies-team-total-under-4-5-pirates-skenes-coors-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/696100/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Dodgers Run Line -1.5 (-106): The Best Team In Baseball Lays The Run At Near Pick-Em Against Trey Gibson's 5.91 ERA",
        date: "June 19, 2026",
        result: "L",
        url: "dodgers-run-line-orioles-sasaki-gibson-dodger-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/808963/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Brewers ML (-160): Jacob Misiorowski's 1.34 ERA And 131 Strikeouts Make Milwaukee Worth Laying In Atlanta",
        date: "June 19, 2026",
        result: "L",
        url: "brewers-moneyline-braves-misiorowski-perez-truist-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/592885/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Yankees ML (-161): A 45-27 Juggernaut And A 109-Homer Offense Host The White Sox At Yankee Stadium",
        date: "June 18, 2026",
        result: "L",
        url: "yankees-moneyline-white-sox-weathers-burke-yankee-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/677960/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Red Sox Team Total Under 4.5 (-114): Boston's Quietest Bats Meet Trey Yesavage's .207 Opponent Average At Fenway",
        date: "June 18, 2026",
        result: "W",
        url: "red-sox-team-total-under-4-5-blue-jays-yesavage-fenway-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/702056/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Rays Team Total Under 3.5 (-148): Tampa Bay Runs Into Shohei Ohtani's 1.06 ERA At Dodger Stadium",
        date: "June 17, 2026",
        result: "L",
        url: "rays-team-total-under-ohtani-dodger-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/663556/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Pirates/Athletics Over 10 (-118): Hitter-Friendly Sutter Health Park And Aaron Civale's 1.47 WHIP",
        date: "June 17, 2026",
        result: "W",
        url: "pirates-athletics-over-civale-sutter-health-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/650644/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cubs -1 Run Line (-145): Javier Assad And A 1.02 WHIP Host The NL-Worst Rockies At Wrigley",
        date: "June 17, 2026",
        result: "W",
        url: "cubs-run-line-assad-rockies-wrigley-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/665871/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cubs ML (-187): Edward Cabrera Hosts The NL-Worst Rockies And Ryan Feltner At Wrigley",
        date: "June 16, 2026",
        result: "L",
        url: "cubs-moneyline-cabrera-rockies-feltner-wrigley-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/665795/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Red Sox/Blue Jays Under 7.5 (-115): Dylan Cease's 13.63 K/9 And Payton Tolle's 2.70 ERA Anchor A Fenway Duel",
        date: "June 16, 2026",
        result: "W",
        url: "red-sox-blue-jays-under-cease-tolle-fenway-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/656302/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cubs ML (-210): Shota Imanaga's 1.06 WHIP Hosts The NL-Worst Rockies And Michael Lorenzen At Wrigley",
        date: "June 15, 2026",
        result: "W",
        url: "cubs-moneyline-imanaga-rockies-wrigley-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/684007/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Phillies ML (-184): Zack Wheeler's 2.22 ERA And 0.85 WHIP Anchor The NL East Opener vs Miami",
        date: "June 15, 2026",
        result: "W",
        url: "phillies-moneyline-wheeler-marlins-citizens-bank-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/547180/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Hurricanes ML (-115): One Road Win From The Cup In Stanley Cup Final Game 6, Carolina Up 3-2",
        date: "June 14, 2026",
        result: "W",
        url: "hurricanes-moneyline-stanley-cup-final-game-6-clinch-nhl-pick.html",
        image: "images/hurricanes-moneyline-stanley-cup-final-game-6-clinch-nhl-pick.jpg"
    },
    {
        sport: "MLB",
        title: "Marlins, Brewers, Cubs And Rockies Team Total Unders: Skenes And Sanchez Anchor A Pitching-Heavy Sunday",
        date: "June 14, 2026",
        result: "L",
        url: "mlb-unders-skenes-sanchez-team-totals-pitching-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/676974/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Mariners ML (-129): Emerson Hancock And A 0.95 WHIP Carry Seattle In Washington",
        date: "June 14, 2026",
        result: "L",
        url: "mariners-moneyline-hancock-nationals-road-favorite-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/676106/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Hurricanes/Golden Knights Over 5.5 (-130): A High-Event Stanley Cup Final Game 6 With Carolina Up 3-2",
        date: "June 13, 2026",
        result: "L",
        url: "hurricanes-golden-knights-stanley-cup-final-game-6-over-nhl-pick.html",
        image: "images/hurricanes-golden-knights-stanley-cup-final-game-6-over-nhl-pick.jpg"
    },
    {
        sport: "MLB",
        title: "Tigers First 5 Innings ML (-158): Tarik Skubal's 2.70 ERA Out-Pitches Joey Cantillo In Cleveland",
        date: "June 13, 2026",
        result: "L",
        url: "tigers-first-five-moneyline-skubal-guardians-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/669373/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Nationals Under 3.5 (+113) and Angels Under 3.5 (-125): Bryce Miller and Shane McClanahan Headline Two Team Total Unders",
        date: "June 12, 2026",
        result: "L",
        url: "nationals-angels-team-total-unders-miller-mcclanahan-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/682243/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Mariners ML (-142), Giants ML (-114), and Braves/Mets Under 8: Roupp and Strider Anchor Friday's Board",
        date: "June 12, 2026",
        result: "W",
        url: "mariners-giants-moneylines-braves-mets-under-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/694738/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Braves ML (-112) at White Sox: Martin Perez's 1.06 WHIP Control vs A .242 Lineup",
        date: "June 11, 2026",
        result: "P",
        url: "braves-moneyline-road-favorite-white-sox-perez-control-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/621566/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Dodgers ML (-187) at Pirates: Shohei Ohtani Carries A 0.74 ERA Into Pittsburgh",
        date: "June 10, 2026",
        result: "L",
        url: "padres-dodgers-astros-moneylines-yankees-rays-unders-white-sox-team-total-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/660271/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Red Sox/Rays Under 7.5 (-125) at Tropicana Field: Rasmussen Caps A Cold Boston Bat",
        date: "June 10, 2026",
        result: "L",
        url: "padres-dodgers-astros-moneylines-yankees-rays-unders-white-sox-team-total-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/656876/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Red Sox/Rays Under 7.5 (-120) at Tropicana Field: Two Sub-2.30 ERAs In A Dome",
        date: "June 9, 2026",
        result: "W",
        url: "dodgers-team-total-under-yankees-moneyline-phillies-red-sox-unders-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/607259/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Yankees ML (-119) at Guardians: Gerrit Cole Returns Without Allowing A Run",
        date: "June 9, 2026",
        result: "W",
        url: "dodgers-team-total-under-yankees-moneyline-phillies-red-sox-unders-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/677944/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Giants ML (-140) vs Nationals: Logan Webb Draws A Mikolas Who Cannot Finish Five",
        date: "June 8, 2026",
        result: "L",
        url: "road-favorites-giants-brewers-harrison-outs-athletics-team-total-under-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/657277/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Athletics Team Total Under 4.5 (+100) vs Brewers: A Cold A's Bat Meets Kyle Harrison",
        date: "June 8, 2026",
        result: "L",
        url: "road-favorites-giants-brewers-harrison-outs-athletics-team-total-under-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/668678/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Astros Team Total Under 4.5 (-125) vs Athletics: Gage Jump Cools A Streaking Houston Bat",
        date: "June 7, 2026",
        result: "W",
        url: "mlb-team-total-unders-card-tigers-astros-blue-jays-rockies-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/695611/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Tigers Team Total Under 3.5 (+100) vs Mariners: Line Steamed As Detroit's Cold Bats Get Capped",
        date: "June 7, 2026",
        result: "L",
        url: "mlb-team-total-unders-card-tigers-astros-blue-jays-rockies-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/622491/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Yankees Team Total Under 4.5 (-140) vs Red Sox: Ranger Suarez Quiets The Bronx Bats",
        date: "June 6, 2026",
        result: "P",
        url: "yankees-team-total-under-red-sox-warren-yankee-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/665862/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Braxton Ashcraft Over 5.5 Strikeouts (-102) vs Braves: The Whiff Rate Points Over",
        date: "June 6, 2026",
        result: "L",
        url: "braxton-ashcraft-over-strikeouts-pirates-braves-strider-truist-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/677952/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Blue Jays Team Total Under 3.5 (-190) vs Braves: Chris Sale Smothers A Cold Toronto Lineup",
        date: "June 4, 2026",
        result: "L",
        url: "blue-jays-team-total-under-braves-chris-sale-truist-park-mlb-pick.html",
        image: "images/blue-jays-team-total-under-braves-chris-sale-truist-park-mlb-pick.jpg"
    },
    {
        sport: "NBA",
        title: "Spurs Moneyline (-185) vs Knicks: Wembanyama Opens The Finals At Home",
        date: "June 3, 2026",
        result: "L",
        url: "spurs-moneyline-knicks-nba-finals-game-1-wembanyama-frost-bank-center-nba-pick.html",
        image: "images/spurs-moneyline-knicks-nba-finals-game-1-wembanyama-frost-bank-center-nba-pick-june-3-2026.jpg"
    },
    {
        sport: "Soccer",
        title: "Italy Moneyline (-233) vs Luxembourg: Baldini's New Era Starts With A Win",
        date: "June 3, 2026",
        result: "W",
        url: "italy-moneyline-luxembourg-baldini-new-era-friendly-soccer-pick.html",
        image: "images/italy-moneyline-luxembourg-baldini-new-era-friendly-soccer-pick-june-3-2026.webp"
    },
    {
        sport: "MLB",
        title: "Yankees Run Line -1.5 (-115) vs Guardians: Schlittler Sets Up The Lay",
        date: "June 2, 2026",
        result: "L",
        url: "yankees-run-line-guardians-schlittler-cantillo-yankee-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/693645/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Brewers Moneyline (-200) vs Giants: Harrison Anchors The Home Favorite",
        date: "June 2, 2026",
        result: "W",
        url: "brewers-moneyline-giants-harrison-mcdonald-american-family-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/690916/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Dodgers Moneyline (-150) vs Diamondbacks: Los Angeles Rolls At Chase Field",
        date: "June 1, 2026",
        result: "L",
        url: "dodgers-moneyline-diamondbacks-sheehan-rodriguez-chase-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/571970/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Marlins Moneyline (+125) vs Nationals: Plus-Money Value Behind Alcantara",
        date: "June 1, 2026",
        result: "W",
        url: "marlins-moneyline-nationals-alcantara-cavalli-nationals-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/645261/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Blue Jays/Orioles Over 8 (-120) at Camden Yards: Leaky Birds Staff Fuels The Total",
        date: "May 31, 2026",
        result: "W",
        url: "blue-jays-orioles-over-8-bradish-miles-camden-yards-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/680694/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Astros +1.5 (-110) vs Brewers: Run Line Cushion Against Misiorowski At Daikin Park",
        date: "May 31, 2026",
        result: "L",
        url: "astros-plus-1-5-runline-brewers-misiorowski-imai-daikin-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/694819/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Braves Team Total Over 4.5 (-140) vs Reds: Atlanta Bats Heat Up At Great American",
        date: "May 30, 2026",
        result: "L",
        url: "braves-reds-team-total-over-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/660670/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Padres Moneyline -121 vs Nationals: San Diego Takes The Series At Petco",
        date: "May 30, 2026",
        result: "L",
        url: "padres-nationals-moneyline-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/665487/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Yankees Moneyline -143 at Athletics: Rodon Holds Off Severino At Sutter Health Park",
        date: "May 29, 2026",
        result: "W",
        url: "yankees-moneyline-athletics-rodon-severino-sutter-health-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/607074/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cubs Team Total Under 3.5 (-145): Skenes Caps Chicago At PNC",
        date: "May 28, 2026",
        result: "L",
        url: "cubs-team-total-under-3-5-pirates-skenes-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/607067/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Padres Team Total Under 3.5: Sanchez Dominant At Petco Park",
        date: "May 27, 2026",
        result: "W",
        url: "padres-team-total-under-3-5-phillies-cristopher-sanchez-petco-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/650911/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Cubs Team Total Under 4.5 at Pirates: Cold Road Bats",
        date: "May 27, 2026",
        result: "L",
        url: "cubs-team-total-under-4-5-pirates-jameson-taillon-pnc-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/543037/action/hero/current"
    },

    {
        sport: "NBA",
        title: "Thunder Moneyline -170 vs Spurs: The Champions Defend Home Court In Game 5",
        date: "May 26, 2026",
        result: "W",
        url: "thunder-moneyline-spurs-game-5-western-conference-final-paycom-center-nba-pick.html",
        image: "images/thunderwin.webp"
    },

    {
        sport: "MLB",
        title: "Braves vs Red Sox Under 8.5: Strider And Suarez Headline The Night's Best Arms At Fenway",
        date: "May 26, 2026",
        result: "L",
        url: "braves-red-sox-under-8-5-strider-suarez-fenway-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/624133/action/hero/current"
    },

    {
        sport: "MLB",
        title: "Guardians Moneyline -169 vs Nationals: Bibee And The AL Central Leader Hold Serve",
        date: "May 25, 2026",
        result: "L",
        url: "guardians-moneyline-nationals-bibee-littell-progressive-field-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/608070/action/hero/current"
    },

    {
        sport: "MLB",
        title: "Yankees Team Total Under 4.5 at Royals: Wacha Caps A Cold Bronx Lineup At Kauffman",
        date: "May 25, 2026",
        result: "W",
        url: "yankees-team-total-under-4-5-royals-wacha-warren-kauffman-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/592450/action/hero/current"
    },

    {
        sport: "NHL",
        title: "Canadiens +1.5 vs Hurricanes Game 2: Montreal Covers The Puck Line",
        date: "May 23, 2026",
        result: "W",
        url: "canadiens-puck-line-plus-1-5-hurricanes-game-2-eastern-conference-final-nhl-pick.html",
        image: "images/canadiens-puck-line-plus-1-5-hurricanes-game-2-eastern-conference-final-nhl-pick.jpg"
    },

    {
        sport: "MLB",
        title: "Pirates-Blue Jays Under 7.5: Skenes vs Corbin At Rogers Centre",
        date: "May 23, 2026",
        result: "W",
        url: "pirates-blue-jays-under-7-5-skenes-corbin-rogers-centre-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/694973/action/hero/current"
    },

    {
        sport: "NHL",
        title: "Canadiens Team Total Under 2.5 vs Hurricanes: ECF Game 1 Scoring Ceiling",
        date: "May 21, 2026",
        result: "L",
        url: "canadiens-team-total-under-2-5-hurricanes-game-1-nhl-pick.html",
        image: "images/canadiens-team-total-under-2-5-hurricanes-game-1-nhl-pick-may-21-2026.jpg"
    },

    {
        sport: "MLB",
        title: "Guardians Moneyline -121 at Tigers: Parker Messick Takes The Hill At Comerica",
        date: "May 19, 2026",
        result: "W",
        url: "guardians-moneyline-minus-121-tigers-messick-montero-comerica-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/800048/action/hero/current"
    },

    {
        sport: "MLB",
        title: "Dodgers-Padres First Five Under 4.5: Yamamoto vs King At Petco",
        date: "May 18, 2026",
        result: "W",
        url: "dodgers-padres-first-five-innings-under-4-5-yamamoto-king-petco-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/808967/action/hero/current"
    },
    
    {
        sport: "MLB",
        title: "Phillies/Pirates First 5 Under 4.5: Wheeler and Skenes Define the Early Window",
        date: "May 17, 2026",
        result: "W",
        url: "phillies-pirates-first-five-under-4-5-wheeler-skenes-pnc.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/554430/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Rangers Team Total Under 4.5: Lambert and Daikin Park Set the Run Ceiling",
        date: "May 17, 2026",
        result: "L",
        url: "rangers-team-total-under-4-5-eovaldi-lambert-daikin-park.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/543135/action/hero/current"
    },
{
        sport: "NHL",
        title: "Ducks Team Total Under 3.5 vs Golden Knights: Game 6 Scoring Ceiling",
        date: "May 14, 2026",
        result: "W",
        url: "ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick.html",
        image: "images/ducks-team-total-under-3-5-golden-knights-game-6-nhl-pick-may-14-2026.png"
    },
    {
        sport: "MLB",
        title: "Brewers Moneyline -139 vs Padres: Harrison Edge At Home",
        date: "May 14, 2026",
        result: "W",
        url: "brewers-moneyline-minus-139-padres-canning-harrison-mlb-pick.html",
        image: "images/brewers.webp"
    },
    {
        sport: "MLB",
        title: "Angels Team Total Under 3.5 vs Guardians: Parker Messick Sets The Bar",
        date: "May 13, 2026",
        result: "W",
        url: "angels-team-total-under-3-5-guardians-messick-progressive-field-mlb-pick.html",
        image: "images/angels.webp"
    },
    {
        sport: "NHL",
        title: "Vegas Golden Knights Moneyline -150 vs Ducks Game 5",
        date: "May 12, 2026",
        result: "W",
        url: "vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.html",
        image: "images/vegas-golden-knights-moneyline-minus-150-ducks-game-5-nhl-pick.webp"
    },
    {
        sport: "NBA",
        title: "Lakers +11 vs Thunder Game 4, Elimination Spot Creates Double-Digit Spread Value",
        date: "May 11, 2026",
        result: "W",
        url: "lakers-plus-11-thunder-game-4-elimination-spot-nba-pick.html",
        image: "images/sacramento-kings-oklahoma-city-thunder-nba-over-betting-pick-total-november-19-2025.webp"
    },
    {
        sport: "MLB",
        title: "Astros ML +124 vs Mariners, Peter Lambert Gives Houston A Live Home Underdog Path",
        date: "May 11, 2026",
        result: "L",
        url: "astros-moneyline-plus-124-mariners-kirby-lambert-daikin-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/663567/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Nationals vs Marlins Pick: Washington Moneyline at loanDepot Park",
        date: "May 9, 2026",
        result: "L",
        url: "nationals-moneyline-plus-139-marlins-littell-junk-loandepot-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/695578/action/hero/current"
    },
    {
        sport: "MLB",
        title: "Braves vs Dodgers Pick: Atlanta Moneyline at Dodger Stadium",
        date: "May 9, 2026",
        result: "W",
        url: "braves-moneyline-plus-152-dodgers-strider-snell-dodger-stadium-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/675911/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Sabres vs Canadiens Pick: Under 6.5 in Game 1",
        date: "May 6, 2026",
        result: "W",
        url: "sabres-canadiens-under-6-5-game-1-second-round-keybank-center-nhl-pick.html",
        image: "images/sabres-lafferty-bench-celebration-bruins-g2-april-21-2026.jpg"
    },
    {
        sport: "MLB",
        title: "Athletics vs Phillies Pick: Oakland Moneyline at Citizens Bank Park",
        date: "May 6, 2026",
        result: "L",
        url: "athletics-moneyline-plus-156-phillies-springs-wheeler-citizens-bank-park-mlb-pick.html",
        image: "https://img.mlbstatic.com/mlb-photos/image/upload/w_1024,q_auto:best/v1/people/667670/action/hero/current"
    },
    {
        sport: "NHL",
        title: "Sabres vs Bruins Game 6 Pick: Over 5.5 at TD Garden",
        date: "May 1, 2026",
        result: "L",
        url: "sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.html",
        image: "images/sabres-bruins-over-5-5-game-6-td-garden-stanley-cup-playoffs-nhl.jpg"
    },
    {
        sport: "NHL",
        title: "Flyers Puck Line +1.5 (-210) vs Penguins Game 5: Philadelphia One Win Away From A Cross-State Series Win",
        date: "April 27, 2026",
        result: "W",
        url: "flyers-puck-line-plus-1-5-penguins-game-5-stanley-cup-playoffs-nhl.html",
        image: "images/flyers-celebration-puck-line-penguins-game-5-stanley-cup-playoffs.jpg"
    },
    {
        sport: "MLB",
        title: "Cubs Moneyline +107 vs Padres at Petco Park: Plus-Money Road Dog In A Pitcher's Park",
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
        image: "images/dallas-stars-edmonton-oilers-over-6-nhl-betting-pick-november-25-2025.webp"
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
        url: "free-mlb-picks-today-full-card-release-wednesday.html",
        image: "images/hero-mlb-full-card-free-release-april-22-2026.jpg"
    },
    {
        sport: "NHL",
        title: "Sabres Team Total Under 3.5 (-140) vs Bruins G2",
        date: "April 21, 2026",
        result: "W",
        url: "sabres-team-total-under-3-5-bruins-game-2-stanley-cup-playoffs-nhl.html",
        image: "images/bruins-islanders-under-6-nhl-betting-pick-november-26-2025.webp"
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
        image: "images/giantsoracle.webp"
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
        title: "Penguins Team Total Over 2.5 Goals",
        date: "March 22, 2026",
        result: "L",
        url: "penguins-team-total-over-2-5-hurricanes-nhl.html",
        image: "images/penguins-plus-1-5-senators-december-18-2025.webp"
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
        url: "rangers-hot-streak-moneyline-puck-line-value-at-wild-nhl.html",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/prd/hlx0hqpifhq8kfmt1y9x"
    }
];
