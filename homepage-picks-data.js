// ============================================================
// HOMEPAGE PICKS DATA - BetLegend Latest Picks & Analysis
// ============================================================
//
// HOW THIS WORKS:
// - Homepage shows exactly 6 cards max (3 per row, 2 rows)
// - Cards display LEFT to RIGHT, newest first:
//     Row 1: [Newest] [2nd] [3rd]
//     Row 2: [4th]    [5th] [6th]
//
// - When a 7th post is added, the oldest card (6th) drops off
//   the homepage and becomes accessible via archive pagination.
//
// TO ADD A NEW PICK:
// 1. Add a new object at the TOP of the array below
// 2. Fill in ALL fields: sport, title, excerpt, date, url, image
// 3. Save this file - the homepage JS handles everything else
//
// REQUIRED FIELDS:
//   sport   - Sport label (NHL, NBA, MLB, NFL, NCAAB, Soccer)
//   title   - The pick headline
//   excerpt - 1-2 sentence description
//   date    - Human-readable date (e.g. "March 11, 2026")
//   url     - Link to the full blog post (with #anchor if needed)
//   image   - Action photo URL (16:9 aspect ratio preferred)
//             NEVER use team logos. Use real game action photos.
//
// ============================================================

var HOMEPAGE_PICKS = [
    {
        sport: "NHL",
        title: "Canadiens at Senators OVER 6.5 (-120)",
        excerpt: "Atlantic Division rivalry in Ottawa with both teams pushing pace. Montreal and Ottawa rank top-10 in goals per game over the last two weeks, and the total has gone over in 4 of the last 5 head-to-head meetings.",
        date: "March 11, 2026",
        url: "nba-college-basketball-picks-predictions-analysis-february-2026.html#post-20260311-mtl-ott-over",
        image: "https://media.d3.nhle.com/image/private/t_ratio16_9-size40/prd/xsfmqkkblaigpxgu5xky"
    }
];
