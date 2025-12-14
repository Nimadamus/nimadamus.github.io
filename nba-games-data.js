// NBA Games Data - All NBA analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NBA_GAMES = [
    { date: "2025-11-24", page: "nba-page31.html", title: "Analysis" },
    { date: "2025-11-26", page: "nba-page30.html", title: "Analysis" },
    { date: "2025-12-04", page: "nba-page29.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-page11.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nba-page32.html", title: "Statistical Analysis" },
    { date: "2025-12-14", page: "nba.html", title: "NBA" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NBA_GAMES;
}
