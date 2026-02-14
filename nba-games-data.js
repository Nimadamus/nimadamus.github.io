// NBA Games Data - All NBA analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NBA_GAMES = [
    { date: "2025-11-24", page: "nba-picks-analysis-against-the-spread-january-01-2026.html", title: "Analysis" },
    { date: "2025-11-26", page: "nba-picks-analysis-against-the-spread-december-31-2025-part-2.html", title: "Analysis" },
    { date: "2025-12-04", page: "nba-picks-analysis-against-the-spread-december-28-2025-part-3.html", title: "Statistical Analysis" },
    { date: "2025-12-04", page: "nba-picks-analysis-against-the-spread-december-28-2025-part-4.html", title: "Statistical Analysis" },
    { date: "2025-12-04", page: "nba-picks-analysis-against-the-spread-december-20-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-04", page: "nba-picks-analysis-against-the-spread-december-31-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-26-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-25-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-21-2025-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-27-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-28-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nba-picks-analysis-against-the-spread-december-28-2025-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-06", page: "nba-picks-analysis-against-the-spread-december-22-2025-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-06", page: "nba-picks-analysis-against-the-spread-december-22-2025-part-3.html", title: "Statistical Analysis" },
    { date: "2025-12-06", page: "nba-picks-analysis-against-the-spread-december-23-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-07", page: "nba-picks-analysis-against-the-spread-december-14-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-07", page: "nba-picks-analysis-against-the-spread-december-21-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-07", page: "nba-picks-analysis-against-the-spread-december-22-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-picks-analysis-against-the-spread-december-11-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-picks-analysis-against-the-spread-december-12-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-picks-analysis-against-the-spread-december-13-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-picks-analysis-against-the-spread-december-20-2025-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-09", page: "nba-picks-analysis-against-the-spread-december-10-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-09", page: "nba-picks-analysis-against-the-spread-december-19-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-10", page: "nba-picks-analysis-against-the-spread-january-01-2026-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-10", page: "nba-picks-analysis-against-the-spread-december-15-2025-part-2.html", title: "Statistical Analysis" },
    { date: "2025-12-10", page: "nba-picks-analysis-against-the-spread-december-17-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-10", page: "nba-picks-analysis-against-the-spread-december-18-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-12", page: "nba-picks-analysis-against-the-spread-january-03-2026.html", title: "Statistical Analysis" },
    { date: "2025-12-12", page: "nba-picks-analysis-against-the-spread-december-20-2025-part-4.html", title: "Statistical Analysis" },
    { date: "2025-12-12", page: "nba-picks-analysis-against-the-spread-december-21-2025-part-3.html", title: "Statistical Analysis" },
    { date: "2025-12-13", page: "nba-picks-analysis-against-the-spread-december-15-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-13", page: "nba-picks-analysis-against-the-spread-november-24-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-14", page: "nba.html", title: "NBA" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NBA_GAMES;
}
