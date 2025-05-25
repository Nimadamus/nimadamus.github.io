const fs = require('fs');
const axios = require('axios');
require('dotenv').config();

const API_KEY = process.env.API_SPORTS_KEY;
const DATE = new Date().toISOString().split('T')[0]; // Format: YYYY-MM-DD

const fetchMatchups = async () => {
  try {
    const response = await axios.get(`https://v1.baseball.api-sports.io/games?date=${DATE}`, {
      headers: {
        'x-apisports-key': API_KEY
      }
    });

    const games = response.data.response;

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MLB MATCHUPS</title>
  <style>
    body {
      background-color: #000;
      color: #FFD700;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      text-align: center;
      padding: 40px 20px;
    }
    h1 {
      font-size: 2.5rem;
      margin-bottom: 40px;
    }
    .matchup {
      background-color: #111;
      margin: 15px auto;
      padding: 15px 30px;
      border-radius: 10px;
      max-width: 600px;
      box-shadow: 0 0 10px #222;
    }
  </style>
</head>
<body>
  <h1>TODAY'S MLB MATCHUPS</h1>
  ${games.map(game => {
    const home = game.teams.home.name.toUpperCase();
    const away = game.teams.away.name.toUpperCase();
    const time = new Date(game.time).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
      timeZone: 'America/Los_Angeles'
    });
    return `<div class="matchup">${away} @ ${home} – ${time}</div>`;
  }).join('\n')}
</body>
</html>
    `;

    fs.writeFileSync('matchups.html', html);
    console.log('✅ matchups.html successfully updated');
  } catch (error) {
    console.error('❌ Failed to fetch or write matchups:', error.message);
  }
};

fetchMatchups();

