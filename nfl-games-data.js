// NFL Games Data - All NFL analysis pages by date
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Description" }

const NFL_GAMES = [
    // August 2025 - Preseason
    { date: "2025-08-15", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-9.html", title: "Preseason Analysis" },
    { date: "2025-08-20", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-8.html", title: "Season Preview" },

    // September 2025 - Early Season
    { date: "2025-09-07", page: "nfl-picks-predictions-against-the-spread-december-26-2025.html", title: "Week 1 Analysis" },
    { date: "2025-09-14", page: "nfl-picks-predictions-against-the-spread-december-25-2025.html", title: "Week 2 Analysis" },

    // October 2025
    { date: "2025-10-26", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-7.html", title: "Week 8 Sunday Slate" },
    { date: "2025-10-28", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-5.html", title: "Week 9 Preview" },
    { date: "2025-10-30", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-4.html", title: "Week 8 TNF - Ravens @ Dolphins" },

    // November 2025
    { date: "2025-11-16", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-3.html", title: "Week 11 Breakdown" },
    { date: "2025-11-23", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-2.html", title: "Week 12 Sunday" },
    { date: "2025-11-24", page: "nfl-picks-predictions-against-the-spread-december-20-2025.html", title: "Week 12 MNF" },
    { date: "2025-11-27", page: "nfl-picks-predictions-against-the-spread-december-05-2025.html", title: "Thanksgiving Day Games" },
    { date: "2025-11-27", page: "nfl-picks-predictions-against-the-spread-january-03-2026.html", title: "Thanksgiving Analysis" },
    { date: "2025-11-28", page: "nfl-picks-predictions-against-the-spread-december-29-2025.html", title: "Black Friday Games" },

    // December 2025
    { date: "2025-12-04", page: "nfl-picks-predictions-against-the-spread-december-07-2025.html", title: "Week 14 Preview" },
    { date: "2025-12-04", page: "nfl-picks-predictions-against-the-spread-december-19-2025.html", title: "TNF Analysis" },
    { date: "2025-12-05", page: "nfl-picks-predictions-against-the-spread-december-21-2025.html", title: "Week 14 Stats" },
    { date: "2025-12-05", page: "nfl-picks-predictions-against-the-spread-november-28-2025.html", title: "Week 14 Trends" },
    { date: "2025-12-05", page: "nfl-picks-predictions-against-the-spread-september-10-2025.html", title: "Statistical Analysis" },
    { date: "2025-12-05", page: "nfl-picks-predictions-against-the-spread-january-04-2026.html", title: "Advanced Stats" },
    { date: "2025-12-05", page: "nfl-picks-predictions-against-the-spread-december-21-2025-saturday.html", title: "Betting Trends" },
    { date: "2025-12-06", page: "nfl-picks-predictions-against-the-spread-october-30-2025.html", title: "Week 14 Games" },
    { date: "2025-12-07", page: "nfl-picks-predictions-against-the-spread-october-28-2025.html", title: "Sunday Slate Part 1" },
    { date: "2025-12-07", page: "nfl-picks-predictions-against-the-spread-october-26-2025.html", title: "Sunday Slate Part 2" },
    { date: "2025-12-08", page: "nfl-picks-predictions-against-the-spread-november-01-2025.html", title: "MNF Stats" },
    { date: "2025-12-08", page: "nfl-picks-predictions-against-the-spread-november-16-2025.html", title: "Week 14 MNF" },
    { date: "2025-12-08", page: "nfl-picks-predictions-against-the-spread-november-23-2025.html", title: "Eagles @ Chargers MNF" },
    { date: "2025-12-08", page: "nfl-picks-predictions-against-the-spread-december-21-2025-part-6.html", title: "MNF Analysis" },
    { date: "2025-12-14", page: "nfl.html", title: "Week 15 - 14-Game Slate" },
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NFL_GAMES;
}
