const axios = require('axios');
const fs = require('fs');

const apiKey = process.env.API_KEY || 'c63a449bea9b087de00bc25f8fe42f7a';
const today = new Date().toISOString().split('T')[0];

const url = `https://v1.baseball.api-sports.io/games?date=${today}&league=1&season=2024`;

axios.get(url, {
  headers: {
    'x-rapidapi-key': apiKey,
    'x-rapidapi-host': 'v1.baseball.api-sports.io'
  }
})
.then(response => {
  const games = response.data.response;

  if (!games || games.length === 0) {
    fs.writeFileSync('odds-live.html', '<html><body style="background:black;color:yellow;font-size:30px;padding:40px">No games today</body></html>');
    return;
  }

  let html = `
    <html>
    <head>
      <title>MLB Matchups – Auto Updated</title>
      <style>
        body {
          background-color: black;
          color: yellow;
          font-family: Arial, sans-serif;
          padding: 40px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th, td {
          border: 1px solid yellow;
          padding: 10px;
          text-align: left;
        }
        th {
          background-color: #222;
        }
      </style>
    </head>
    <body>
      <h1>MLB Matchups – Auto Updated</h1>
      <table>
        <thead>
          <tr>
            <th>Matchup</th>
            <th>Time</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
  `;

  for (const game of games) {
    const home = game.teams?.home?.name || 'Unknown';
    const away = game.teams?.away?.name || 'Unknown';
    const time = game.time || 'TBD';
    const status = game.status?.short || 'TBD';

    html += `
      <tr>
        <td>${away} @ ${home}</td>
        <td>${time}</td>
        <td>${status}</td>
      </tr>
    `;
  }

  html += `
        </tbody>
      </table>
    </body>
    </html>
  `;

  fs.writeFileSync('odds-live.html', html);
  console.log("✅ odds-live.html updated successfully");
})
.catch(error => {
  console.
