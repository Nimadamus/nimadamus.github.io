const fs = require('fs');

const now = new Date().toLocaleString();

const html = `
<html>
  <head>
    <title>Debug Odds Output</title>
    <style>
      body {
        background-color: #000;
        color: #FFD700;
        font-family: sans-serif;
        padding: 40px;
      }
      .card {
        border: 1px solid #FFD700;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
      }
    </style>
  </head>
  <body>
    <h1>ODDS DEBUG: ${now}</h1>

    <div class="card">
      <h3>This proves odds.html was overwritten.</h3>
      <p>If you see this, the script worked.</p>
    </div>
  </body>
</html>
`;

fs.writeFileSync('odds.html', html.trim());
console.log('✅ odds.html overwritten for debug test');

