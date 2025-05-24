const fs = require("fs");
const axios = require("axios");
require("dotenv").config();

const API_KEY = process.env.API_KEY;
const API_URL = "https://v1.baseball.api-sports.io/games";
const DATE = new Date().toISOString().split("T")[0]; // e.g., 2025-05-24

const options = {
  method: "GET",
  url: `${API_URL}?date=${DATE}&league=1&season=2025`,
  headers: {
    "x-apisports-key": API_KEY,
  },
};

axios
  .request(options)
  .then((response) => {
    const games = response.data.response;
    let html = "<html><head><title>Matchups</title></head><body><h1>MLB Matchups</h1><ul>";
    games.forEach((game) => {
      const home = game.teams.home.name;
      const away = game.teams.away.name;
      const time = new Date(game.fixture.date).toLocaleTimeString("en-US", {
        timeZone: "America/Los_Angeles",
      });
      html += `<li>${away} @ ${home} - ${time}</li>`;
    });
    html += "</ul></body></html>";
    fs.writeFileSync("matchups.html", html);
    console.log("✅ matchups.html updated");
  })
  .catch((error) => {
    console.error("API error:", error);
  });

