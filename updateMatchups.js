const fs = require("fs");
const axios = require("axios");
require("dotenv").config();

const API_KEY = process.env.API_KEY;
const DATE = new Date().toISOString().split("T")[0];

const options = {
  method: "GET",
  url: `https://v1.baseball.api-sports.io/games?date=${DATE}&league=1&season=2025`,
  headers: {
    "x-apisports-key": API_KEY
  }
};

axios
  .request(options)
  .then((response) => {
    const games = response.data.response;
    let html = `
<!DOCTYPE html>
<html>
<head>
  <title>MLB Matchups</title>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    body {
      background-color: black;
      color: #FFD700;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 30px;
    }
    h1 {
      text-align: center;
      font-size: 2.5rem;
      margin-bottom: 30px;
    }
    .matchups {
      max-width: 700px;
      margin: 0 auto;
      background-color: #111;
      border-radius: 10px;
      padding: 25px;
      box-shadow: 0 0 10px #222;
    }
    .matchup {
      padding: 12px;
      border-bottom: 1px solid #444;
    }
    .matchup:last-child {
      border-bottom: none;
    }
  </style>
</head>
<body>
  <h1>Today's MLB Matchups</h1>
  <div class="matchups">
`;

    if (games.length === 0) {
      html += `<div class="matchup">No matchups found for today.</div>`;
    } else {
      games.forEach((game) => {
        const home = game.teams.home.name;
        const away = game.teams.away.name;
        const time = new Date(game.fixture.date).toLocaleTimeString("en-US", {
          timeZone: "America/Los_Angeles"
        });
        html += `<div class="matchup">${away} @ ${home} – ${time}</div>`;
      });
    }

    html += `
  </div>
</body>
</html>
`;

    fs.writeFileSync("matchups.html", html);
    console.log("✅ matchups.html successfully written");
  })
  .catch((error) => {
    console.error("❌ API error:", error.message);
  });


