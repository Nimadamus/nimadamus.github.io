// NHL Games Data - All NHL analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NHL_GAMES = [
    { date: "2025-11-24", page: "nhl-page29.html", title: "Analysis" },
    { date: "2025-11-26", page: "nhl-page28.html", title: "Analysis" },
    { date: "2025-11-28", page: "nhl-page30.html", title: "Archive" },
    { date: "2025-11-28", page: "nhl-page31.html", title: "Archive" },
    { date: "2025-12-04", page: "nhl-page27.html", title: "NHL Analysis" },
    { date: "2025-12-06", page: "nhl-page33.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nhl-page11.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nhl-page34.html", title: "Statistical Analysis" },
    { date: "2025-12-08", page: "nhl-page36.html", title: "Statistical Analysis" },
    { date: "2025-12-09", page: "nhl-page10.html", title: "Statistical Analysis" },
    { date: "2025-12-12", page: "nhl-page5.html", title: "Statistical Analysis" },
    { date: "2025-12-14", page: "nhl.html", title: "NHL" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NHL_GAMES;
}
