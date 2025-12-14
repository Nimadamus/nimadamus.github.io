// NFL Games Data - All NFL analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NFL_GAMES = [
    // August 2025 - Preseason
    { date: "2025-08-15", page: "nfl-page24.html", title: "Preseason Analysis" },
    { date: "2025-08-20", page: "nfl-page23.html", title: "Season Preview" },

    // September 2025 - Early Season
    { date: "2025-09-07", page: "nfl-page22.html", title: "Week 1 Analysis" },
    { date: "2025-09-14", page: "nfl-page21.html", title: "Week 2 Analysis" },

    // October 2025
    { date: "2025-10-26", page: "nfl-page20.html", title: "Week 8 Sunday Slate" },
    { date: "2025-10-28", page: "nfl-page19.html", title: "Week 9 Preview" },
    { date: "2025-10-30", page: "nfl-page18.html", title: "Week 8 TNF - Ravens @ Dolphins" },

    // November 2025
    { date: "2025-11-16", page: "nfl-page17.html", title: "Week 11 Breakdown" },
    { date: "2025-11-23", page: "nfl-page16.html", title: "Week 12 Sunday" },
    { date: "2025-11-24", page: "nfl-page15.html", title: "Week 12 MNF" },
    { date: "2025-11-27", page: "nfl-page14.html", title: "Thanksgiving Day Games" },
    { date: "2025-11-27", page: "nfl-page27.html", title: "Thanksgiving Analysis" },
    { date: "2025-11-28", page: "nfl-page26.html", title: "Black Friday Games" },

    // December 2025
    { date: "2025-12-04", page: "nfl-page13.html", title: "Week 14 Preview" },
    { date: "2025-12-04", page: "nfl-page12.html", title: "TNF Analysis" },
    { date: "2025-12-05", page: "nfl-page11.html", title: "Week 14 Stats" },
    { date: "2025-12-05", page: "nfl-page10.html", title: "Week 14 Trends" },
    { date: "2025-12-05", page: "nfl-page9.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nfl-page28.html", title: "Advanced Stats" },
    { date: "2025-12-05", page: "nfl-page29.html", title: "Betting Trends" },
    { date: "2025-12-06", page: "nfl-page6.html", title: "Week 14 Games" },
    { date: "2025-12-07", page: "nfl-page7.html", title: "Sunday Slate Part 1" },
    { date: "2025-12-07", page: "nfl-page8.html", title: "Sunday Slate Part 2" },
    { date: "2025-12-08", page: "nfl-page5.html", title: "MNF Stats" },
    { date: "2025-12-08", page: "nfl-page4.html", title: "Week 14 MNF" },
    { date: "2025-12-08", page: "nfl-page3.html", title: "Eagles @ Chargers MNF" },
    { date: "2025-12-08", page: "nfl-page2.html", title: "MNF Analysis" },
    { date: "2025-12-14", page: "nfl.html", title: "Week 15 - 14-Game Slate" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NFL_GAMES;
}
