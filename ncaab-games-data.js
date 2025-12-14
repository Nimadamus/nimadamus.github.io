// NCAAB Games Data - All NCAAB analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NCAAB_GAMES = [
    { date: "2025-12-08", page: "ncaab-page11.html", title: "Statistical Analysis" },
    { date: "2025-12-09", page: "ncaab-page10.html", title: "Statistical Analysis" },
    { date: "2025-12-14", page: "ncaab.html", title: "NCAAB" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NCAAB_GAMES;
}
