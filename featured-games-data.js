// Featured Games Data - Add new entries here when creating new featured game pages
// Format: { date: "YYYY-MM-DD", page: "filename.html", title: "Game Title" }
// The calendar will auto-populate from this data

const FEATURED_GAMES = [
    // October 2025
    { date: "2025-10-25", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-29", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-30", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-10-31", page: "featured-game-of-the-day.html", title: "Archive" },

    // November 2025
    { date: "2025-11-01", page: "featured-game-of-the-day.html", title: "Vanderbilt @ Texas" },
    { date: "2025-11-03", page: "featured-game-of-the-day.html", title: "Evening Slate" },
    { date: "2025-11-05", page: "featured-game-of-the-day.html", title: "NHL Game" },
    { date: "2025-11-06", page: "featured-game-of-the-day.html", title: "NHL Analysis" },
    { date: "2025-11-07", page: "featured-game-of-the-day.html", title: "USC Game" },
    { date: "2025-11-09", page: "featured-game-of-the-day.html", title: "49ers Game" },
    { date: "2025-11-11", page: "featured-game-of-the-day.html", title: "Avalanche Game" },
    { date: "2025-11-12", page: "featured-game-of-the-day.html", title: "NHL Tampa" },
    { date: "2025-11-13", page: "featured-game-of-the-day.html", title: "Jets vs Patriots TNF" },
    { date: "2025-11-15", page: "featured-game-of-the-day.html", title: "Alabama Game" },
    { date: "2025-11-16", page: "featured-game-of-the-day.html", title: "Seahawks @ Rams" },
    { date: "2025-11-17", page: "featured-game-of-the-day.html", title: "MNF" },
    { date: "2025-11-19", page: "featured-game-of-the-day.html", title: "Wild Game" },
    { date: "2025-11-21", page: "featured-game-of-the-day.html", title: "Archive" },
    { date: "2025-11-22", page: "featured-game-of-the-day-page2.html", title: "USC vs Oregon" },
    { date: "2025-11-23", page: "featured-game-of-the-day-page3.html", title: "Rams vs Buccaneers SNF" },
    { date: "2025-11-24", page: "featured-game-of-the-day-page4.html", title: "Panthers vs 49ers MNF" },
    { date: "2025-11-25", page: "featured-game-of-the-day-page5.html", title: "Clippers vs Lakers" },
    { date: "2025-11-26", page: "featured-game-of-the-day-page6.html", title: "Rockets vs Warriors" },
    { date: "2025-11-27", page: "featured-game-of-the-day-page7.html", title: "Steelers vs Browns Thanksgiving" },
    { date: "2025-11-29", page: "featured-game-of-the-day-page8.html", title: "Vanderbilt vs Tennessee" },
    { date: "2025-11-30", page: "featured-game-of-the-day-page9.html", title: "Texans vs Colts" },

    // December 2025
    { date: "2025-12-01", page: "featured-game-of-the-day-page10.html", title: "Giants vs Patriots MNF" },
    { date: "2025-12-03", page: "featured-game-of-the-day-page11.html", title: "Pistons vs Bucks" },
    { date: "2025-12-04", page: "featured-game-of-the-day-page12.html", title: "Cowboys vs Lions TNF" },
    { date: "2025-12-06", page: "featured-game-of-the-day-page13.html", title: "Georgia vs Alabama SEC Championship" },
    { date: "2025-12-07", page: "featured-game-of-the-day-page14.html", title: "Bengals vs Bills" },
    { date: "2025-12-08", page: "featured-game-of-the-day-page15.html", title: "Eagles vs Chargers MNF" },
    { date: "2025-12-10", page: "featured-game-of-the-day-page16.html", title: "Lakers vs Spurs NBA Cup" },
    { date: "2025-12-11", page: "featured-game-of-the-day-page17.html", title: "Falcons vs Buccaneers TNF" },
    { date: "2025-12-13", page: "featured-game-of-the-day-page18.html", title: "Army vs Navy" },
    { date: "2025-12-17", page: "featured-game-of-the-day-page19.html", title: "South Florida vs Old Dominion Cure Bowl" },
    { date: "2025-12-18", page: "featured-game-of-the-day-page20.html", title: "Dallas Stars vs San Jose Sharks" },
    { date: "2025-12-19", page: "featured-game-of-the-day-page21.html", title: "#9 Alabama vs #8 Oklahoma CFP" },
    { date: "2025-12-21", page: "featured-game-of-the-day-page22.html", title: "Buccaneers vs Panthers" },
    { date: "2025-12-22", page: "featured-game-of-the-day-page23.html", title: "49ers vs Colts MNF" },
    { date: "2025-12-23", page: "featured-game-of-the-day-page24.html", title: "WKU vs Southern Miss New Orleans Bowl" },
    { date: "2025-12-24", page: "featured-game-of-the-day-page25.html", title: "Cal vs Hawaii Hawaii Bowl" },
    { date: "2025-12-25", page: "featured-game-of-the-day-page26.html", title: "Lions vs Vikings Christmas Day" },
    { date: "2025-12-26", page: "featured-game-of-the-day-page27.html", title: "New Mexico vs Minnesota Rate Bowl" },
    { date: "2025-12-27", page: "featured-game-of-the-day-page28.html", title: "Texans vs Chargers Week 17" },
    { date: "2025-12-28", page: "featured-game-of-the-day-page29.html", title: "Eagles vs Bills Week 17" },
    { date: "2025-12-29", page: "featured-game-of-the-day-page30.html", title: "Rams vs Falcons MNF" },
    { date: "2025-12-30", page: "featured-game-of-the-day-page31.html", title: "Tennessee vs Illinois Music City Bowl" },

    // January 2026
    { date: "2025-12-31", page: "featured-game-of-the-day-page32.html", title: "Miami vs Ohio State Cotton Bowl CFP" },
    { date: "2026-01-01", page: "featured-game-of-the-day-2026-01-01.html", title: "Indiana vs Alabama Rose Bowl CFP" },
    { date: "2026-01-02", page: "featured-game-of-the-day-page33.html", title: "Arizona vs SMU Holiday Bowl" },
    { date: "2026-01-03", page: "featured-game-of-the-day-page34.html", title: "49ers vs Seahawks NFC West Title" },
    { date: "2026-01-04", page: "featured-game-of-the-day-page35.html", title: "Ravens vs Steelers AFC North Title" },
    { date: "2026-01-05", page: "featured-game-of-the-day-page36.html", title: "Bulls vs Celtics" },
    { date: "2026-01-06", page: "featured-game-of-the-day-page37.html", title: "Devils vs Islanders" },
    { date: "2026-01-15", page: "featured-game-of-the-day-page46.html", title: "Knicks vs Warriors" },
    { date: "2026-01-16", page: "featured-game-of-the-day-page47.html", title: "Panthers vs Hurricanes" },
    { date: "2026-01-17", page: "featured-game-of-the-day-page48.html", title: "NFL Divisional Round" },
    { date: "2026-01-18", page: "featured-game-of-the-day-page49.html", title: "Texans vs Patriots AFC Divisional" },
    { date: "2026-01-19", page: "featured-game-of-the-day-page50.html", title: "Indiana vs Miami CFP National Championship" },
    { date: "2026-01-20", page: "featured-game-of-the-day-page51.html", title: "Spurs vs Rockets NBA" },
    { date: "2026-01-21", page: "featured-game-of-the-day-page52.html", title: "Thunder vs Bucks NBA" },
    { date: "2026-01-22", page: "featured-game-of-the-day-page53.html", title: "Warriors vs Mavericks NBA" },
    { date: "2026-01-23", page: "featured-game-of-the-day-page54.html", title: "Pacers vs Thunder NBA Finals Rematch" },
    { date: "2026-01-24", page: "featured-game-of-the-day-page55.html", title: "Canadiens vs Bruins Original Six Rivalry" },
    { date: "2026-01-25", page: "featured-game-of-the-day-page56.html", title: "Patriots vs Broncos AFC Championship" },

    // February 2026
    { date: "2026-02-01", page: "featured-game-of-the-day-page63.html", title: "Lightning vs Bruins Stadium Series" },

    // ADD NEW FEATURED GAMES HERE (format: date, page, title)
];

// Export for use in calendar
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FEATURED_GAMES;
}
