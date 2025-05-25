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
    console.log(`✅ Pulled ${games.length} games from API`);

    let html = `
<!DOCTYPE html>
<html>
<head><title>Matchups</title></head>
<body><h1>LIVE MATCHUPS</h1><pre>${JSON.stringify(games, null, 2)}</pre></body>
</html>
    `;

    fs.writeFileSync("matchups.html", html, { flag: "w" });
    console.log("✅ Wrote matchups.html with raw JSON");
  })
  .catch((error) => {
    console.error("❌ API call failed:", error.message);
    let html = `<html><body><h1>API ERROR</h1><p>${error.message}</p></body></html>`;
    fs.writeFileSync("matchups.html", html, { flag: "w" });
  });
