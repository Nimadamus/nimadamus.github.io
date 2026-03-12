// ============================================================
// HOMEPAGE PICKS DATA - BetLegend Latest Picks & Analysis
// ============================================================
//
// HOW THIS WORKS:
// - First 3 picks show as large featured cards (title + image)
// - Picks 4+ show in compact grid (10 per row, 2 rows, paginated)
// - Cards display LEFT to RIGHT, newest first
//
// TO ADD A NEW PICK:
// 1. Add a new object at the TOP of the array below
// 2. Fill in ALL fields: sport, title, date, url, image
// 3. The oldest featured card shifts into the compact grid
//
// ============================================================

var HOMEPAGE_PICKS = [
    {
        sport: "NHL",
        title: "Canadiens at Senators OVER 6.5 (-120)",
        date: "March 11, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260311-mtl-ott-over",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_png/prd/fheppawnueem5lvuoywk.png"
    },
    {
        sport: "NHL",
        title: "Sharks vs Sabres OVER 6.5 (-120)",
        date: "March 10, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260310-sharks-sabres-over",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/f_auto/prd/po2acmf2h1bkk60rcfu0.jpg"
    },
    {
        sport: "NHL",
        title: "Kings vs Blue Jackets UNDER 6 (-105)",
        date: "March 9, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260309-kings-bluejackets-under",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/v1772774164/prd/h2qw1ix5gixoeumq24wf"
    },
    {
        sport: "NHL",
        title: "Avalanche ML -175",
        date: "March 8, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260308-avalanche-moneyline",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/f_png/prd/fljwnnebgww50wd3v3nf.png"
    },
    {
        sport: "NHL",
        title: "Kings TT Under 3.5 (-160)",
        date: "March 7, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260307-kings-teamtotal-under",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/f_png/prd/zsxvhta34tlov2aq0nrq.png"
    },
    {
        sport: "NHL",
        title: "Red Wings ML -150",
        date: "March 6, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260306-redwings-moneyline",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1772488079/prd/jnkpqruayckihmwnj4yf"
    },
    {
        sport: "NHL",
        title: "Maple Leafs ML +105",
        date: "March 5, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260305-leafs-moneyline",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1767330717/prd/aryux4ugjuduxl6kshoi"
    },
    {
        sport: "NHL",
        title: "Kraken ML -150",
        date: "March 4, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260304-kraken-moneyline",
        image: "https://res.cloudinary.com/ybmedia/image/upload/c_crop,e_improve,h_618,w_1099,x_0,y_33/c_fill,f_auto,h_900,q_auto,w_1600/v1/m/c/e/ce8ff234985b43d63763844f9a0346969b51faad/28385063.jpg"
    },
    {
        sport: "NHL",
        title: "NHL + NCAAB 7-Play Card",
        date: "March 3, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260303-nhl-ncaab-picks",
        image: "https://i0.wp.com/www.diebytheblade.com/wp-content/uploads/sites/14/2026/03/USATSI_28313749.jpg?w=1600&ssl=1"
    },
    {
        sport: "NHL",
        title: "Red Wings/Predators U 6.5",
        date: "March 2, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260302-redwings-predators-under",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/v1772488079/prd/jnkpqruayckihmwnj4yf"
    },
    {
        sport: "NHL",
        title: "Ducks/Flames Under 6.5",
        date: "March 1, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260301-ducks-flames-under",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_auto/prd/h6qcahnl0ij28wf8wwrc.jpg"
    },
    {
        sport: "NHL",
        title: "NHL Saturday 7-Pick Card",
        date: "February 28, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260228-nhl-saturday-card",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/v1772161553/prd/vhyvosphmpikst65dbrt"
    },
    {
        sport: "NHL",
        title: "Sabres ML + Illinois +2.5",
        date: "February 27, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260227-sabres-illinois",
        image: "https://bloximages.chicago2.vip.townnews.com/hjnews.com/content/tncms/assets/v3/editorial/f/b6/fb67f7bb-8996-57f2-b5ae-0bb95ff35a98/6997cc8b042c1.image.jpg"
    },
    {
        sport: "NHL",
        title: "VGK/Kings Under 5.5 (-115)",
        date: "February 25, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260225-vgk-lak-under",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size20/f_png/prd/dmq6prh83otoftnougas.png"
    },
    {
        sport: "NBA",
        title: "Raptors -1 vs Thunder",
        date: "February 24, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260224-raptors-minus1",
        image: "https://media.assettype.com/outlookindia/2026-02-09/36ve1exd/Toronto-Raptors-vs-Indiana-Pacers-nba-basketball-game-4-Scottie-Barnes.jpg"
    },
    {
        sport: "NBA",
        title: "Jazz +13.5 at Rockets",
        date: "February 23, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260223-utah-jazz-plus-13",
        image: "https://cloudfront-us-east-1.images.arcpublishing.com/deseretnews/UGCR5NDVGNFF3OZBJVH5SHD64U.JPG"
    }
];
