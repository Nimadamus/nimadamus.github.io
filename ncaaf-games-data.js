// NCAAF Games Data - All NCAAF analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NCAAF_GAMES = [
    { date: "2025-09-10", page: "ncaaf-page18.html", title: "Rivalry Week - Saturday Edition" },
    { date: "2025-11-29", page: "ncaaf-page17.html", title: "Rivalry Week" },
    { date: "2025-12-06", page: "ncaaf-page14.html", title: "Championship Weekend" },
    { date: "2025-12-14", page: "ncaaf.html", title: "NCAAF" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NCAAF_GAMES;
}
