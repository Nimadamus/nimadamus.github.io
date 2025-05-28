const fs = require('fs');
const axios = require('axios');

const API_KEY = 'c63a449bea9b087de00bc25f8fe42f7a';
const API_URL = 'https://v1.baseball.api-sports.io/games';
const today = new Date().toISOString().split('T')[0];

axios.get(`${API_URL}?date=${today}&league=1&season=2025`, {
  headers: { 'x-apisports-key': API_KEY }
})
.then(response => {
  const games = response.data.response;
  if (!games.length) throw new Error('No games found.');

  const rows = games.map(game => {
    const away = game.teams.away.name;
    const home = game.teams.home.name;
    const time = game.time || '';
    const status = game.status.long || '';
    return `<tr><td>${away}</td><td>${home}</td><td>${time}</td><td>${status}</td></tr>`;
  }).join('\n');

  const html = `
  <html>
    <head>
      <title>MLB Odds – Auto</title>
      <style>
        body {
          background: #000;
          color: #FFD700;
          font-family: sans-serif;
          padding: 40px;
