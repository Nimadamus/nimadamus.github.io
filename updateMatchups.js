const fs = require("fs");
const axios = require("axios");
require("dotenv").config();

const API_KEY = process.env.API_KEY;
const DATE = new Date().toISOString().split("T")[0];

const options = {
  method: "GET",
  url: `https://v1.baseball.api-sports.io/games?date=${DATE}&league=1&season=2025`,
  headers: { "x-apisports-key": API_KEY }
};

axios.request(options).then(response => {
  const games = response.data.response;
  let html = `
<!DOCTYPE html>
<html>
<head><title>Today's MLB Matchups</title></head>
<body style="background:black;color:gold;font-family:sans-serif;padding:40px">
<h1>TODAY'S MLB MATCHUPS</h1>
`;

  games.forEach(game => {
    const home = game.teams.home.name.toUpperCase();
    const away = game.teams.away.name.toUpperCase();
    const time = new Date(game.time).toLocaleTimeString("en-US", { timeZone: "America/Los_Angeles", hour: "numeric", minute: "2-digit" });
    html += `<div style="margin-bottom:12px;background:#111;padding:15px;border-radius:8px">${away} @ ${home} — ${time}</div>`;
  });

  html += `</body></html>`;
  fs.writeFileSync("matchups.html", html);
  console.log("✅ Matchups page updated.");
}).catch(err => {
  console.error("❌ API error:", err.message);
});
