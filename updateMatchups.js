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
    const html = `
<!DOCTYPE html>
<html>
<head>
  <title>Matchups Debug</title>
</head>
<body style="background:black;color:gold;padding:40px;font-family:sans-serif">
  <h1>✅ API CONNECTED</h1>
  <p>Total games found: ${games.length}</p>
  <pre>${JSON.stringify(games, null, 2)}</pre>
</body>
</html>
    `;
    fs.writeFileSync("matchups.html", html, { flag: "w" });
    console.log("✅ matchups.html written.");
  })
  .catch((error) => {
    const html = `
<!DOCTYPE html>
<html>
<head><title>Error</title></head>
<body style="background:black;color:red;padding:40px;font-family:sans-serif">
  <h1>❌ API ERROR</h1>
  <p>${error.message}</p>
</body>
</html>
    `;
    fs.writeFileSync("matchups.html", html, { flag: "w" });
    console.error("❌ API call failed:", error.message);
  });
