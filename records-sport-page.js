/*
  records-sport-page.js
  Shared renderer for every per-sport *-records.html page.

  Data pipeline:
    1. If window.RecordsEngine is available, fetch LIVE picks from the
       Pick Tracker + sport sheets. This is the source of truth and
       matches records.html (the hub) exactly.
    2. Otherwise fall back to all-records.json (pre-built snapshot).

  Every sport page loads the same picks with the same stats math so that
  records.html and the individual sport pages can never disagree.
*/
(function () {
  const DATA_URL = 'all-records.json';

  function normalizeResult(value) {
    const result = String(value || '').trim().toUpperCase();
    return result ? result.charAt(0) : '';
  }

  function normalizeDateString(value) {
    const raw = String(value || '').trim();
    if (!raw) return '';
    const parts = raw.split(/[-\/]/);
    if (parts.length !== 3) return raw;
    const month = parseInt(parts[0], 10);
    const day = parseInt(parts[1], 10);
    let yearText = String(parts[2]).trim();
    if (/^0\d+$/.test(yearText)) yearText = yearText.replace(/^0+/, '');
    if (/^\d{3}$/.test(yearText) && yearText.startsWith('20')) {
      yearText = yearText.slice(0, 2) + '2' + yearText.slice(2);
    }
    let year = parseInt(yearText, 10);
    if (year > 2030 && year < 3000) year = parseInt('20' + String(year).slice(-2), 10);
    if ([month, day, year].some(Number.isNaN)) return raw;
    return month + '/' + day + '/' + year;
  }

  function parseDate(value) {
    const normalized = normalizeDateString(value);
    const parts = normalized.split('/');
    if (parts.length === 3) {
      const month = parseInt(parts[0], 10);
      const day = parseInt(parts[1], 10);
      const year = parseInt(parts[2], 10);
      if (![month, day, year].some(Number.isNaN)) {
        return new Date(year, month - 1, day);
      }
    }
    const fallback = new Date(normalized);
    return Number.isNaN(fallback.getTime()) ? null : fallback;
  }

  function parseOdds(value) {
    const parsed = parseFloat(String(value || '').replace(/,/g, '').replace(/^\+/, ''));
    return Number.isNaN(parsed) ? null : parsed;
  }

  function parseProfitLoss(value) {
    const parsed = parseFloat(String(value || '').replace(/,/g, '').replace(/^\+/, ''));
    return Number.isNaN(parsed) ? 0 : parsed;
  }

  function getYear(value) {
    const date = parseDate(value);
    return date ? date.getFullYear() : null;
  }

  // Stake-aware risk: use the known stake when present (live engine rows),
  // otherwise reverse-engineer from the pre-calculated P/L and odds.
  // Pushes still count as risked capital at an assumed 1-unit stake when
  // no explicit stake is recorded - matches records.html behavior so ROI
  // stays consistent across pages.
  function calculateRisk(row) {
    const odds = parseOdds(row.odds);
    const stake = row.stake;
    if (stake !== null && stake !== undefined && !Number.isNaN(stake)) {
      if (!odds) return Math.abs(stake);
      return odds < 0 ? stake * (Math.abs(odds) / 100) : stake;
    }
    const profitLoss = row.profitLoss;
    if (row.result === 'P') {
      const assumedStake = 1;
      if (!odds) return assumedStake;
      return odds < 0 ? assumedStake * (Math.abs(odds) / 100) : assumedStake;
    }
    if (!odds || !profitLoss) return 0;
    if (profitLoss < 0) return Math.abs(profitLoss);
    if (odds < 0) return profitLoss * (Math.abs(odds) / 100);
    return profitLoss / (odds / 100);
  }

  function calculateStats(rows) {
    let wins = 0;
    let losses = 0;
    let pushes = 0;
    let units = 0;
    let risk = 0;

    rows.forEach((row) => {
      if (row.result === 'W') wins += 1;
      else if (row.result === 'L') losses += 1;
      else if (row.result === 'P') pushes += 1;
      units += row.profitLoss;
      risk += calculateRisk(row);
    });

    const graded = wins + losses;
    const winPct = graded ? (wins / graded) * 100 : 0;
    const roi = risk ? (units / risk) * 100 : 0;

    return { wins, losses, pushes, units, winPct, roi };
  }

  function buildChartSeries(rows) {
    const ordered = rows
      .slice()
      .sort((a, b) => {
        const aDate = parseDate(a.date);
        const bDate = parseDate(b.date);
        return (aDate ? aDate.getTime() : 0) - (bDate ? bDate.getTime() : 0);
      });

    let runningUnits = 0;
    const labels = [];
    const dates = [];
    const cumulative = [];

    ordered.forEach((row) => {
      runningUnits += row.profitLoss;
      const date = parseDate(row.date);
      labels.push(date ? (date.getMonth() + 1) + '/' + date.getDate() : row.date);
      dates.push(row.date);
      cumulative.push(Number(runningUnits.toFixed(2)));
    });

    return { ordered, labels, dates, cumulative };
  }

  function renderTableRows(rows, tbody) {
    tbody.innerHTML = rows
      .map((row) => {
        const unitsClass = row.profitLoss > 0 ? 'win' : (row.profitLoss < 0 ? 'loss' : 'result-P');
        const unitsText = (row.profitLoss > 0 ? '+' : '') + row.profitLoss.toFixed(2);
        return `<tr>
  <td>${row.date}</td>
  <td>${row.pick}</td>
  <td>${row.odds}</td>
  <td class="result-${row.result}">${row.result}</td>
  <td class="${unitsClass}">${unitsText}</td>
</tr>`;
      })
      .join('');
  }

  function updateSummary(rows) {
    const stats = calculateStats(rows);
    const recordEl = document.getElementById('summary-record');
    if (recordEl) recordEl.textContent = stats.wins + '-' + stats.losses + '-' + stats.pushes;

    const unitsEl = document.getElementById('summary-units');
    if (unitsEl) {
      unitsEl.textContent = (stats.units >= 0 ? '+' : '') + stats.units.toFixed(2);
      unitsEl.className = stats.units >= 0 ? 'units-win' : 'units-loss';
    }

    const winPctEl = document.getElementById('summary-win-pct');
    if (winPctEl) winPctEl.textContent = stats.winPct.toFixed(1) + '%';

    const roiEl = document.getElementById('summary-roi');
    if (roiEl) {
      roiEl.textContent = (stats.roi >= 0 ? '+' : '') + stats.roi.toFixed(2) + '%';
      roiEl.className = stats.roi >= 0 ? 'roi-win' : 'roi-loss';
    }
  }

  function updateChart(rows, chartStateKey) {
    const chartData = buildChartSeries(rows);
    const currentUnits = chartData.cumulative.length
      ? chartData.cumulative[chartData.cumulative.length - 1]
      : 0;
    const peakUnits = chartData.cumulative.length ? Math.max(...chartData.cumulative) : 0;
    const startDate = chartData.ordered.length ? chartData.ordered[0].date : '--';

    const startDateEl = document.getElementById('chart-start-date');
    if (startDateEl) startDateEl.textContent = startDate;
    const totalBetsEl = document.getElementById('chart-total-bets');
    if (totalBetsEl) totalBetsEl.textContent = String(rows.length);
    const currentUnitsEl = document.getElementById('chart-current-units');
    if (currentUnitsEl) {
      currentUnitsEl.textContent = (currentUnits >= 0 ? '+' : '') + currentUnits.toFixed(2);
      currentUnitsEl.style.color = currentUnits >= 0 ? '#39FF14' : '#FF3131';
    }
    const peakUnitsEl = document.getElementById('chart-peak-units');
    if (peakUnitsEl) peakUnitsEl.textContent = (peakUnits >= 0 ? '+' : '') + peakUnits.toFixed(2);

    if (!window.Chart) return;
    const canvas = document.getElementById('unitsChart');
    if (!canvas) return;

    if (window[chartStateKey]) {
      window[chartStateKey].destroy();
    }

    window[chartStateKey] = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Units',
          data: chartData.cumulative,
          borderColor: '#00e0ff',
          backgroundColor: 'transparent',
          borderWidth: 2,
          fill: false,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointHoverBackgroundColor: '#00e0ff',
          pointHoverBorderColor: '#ffffff',
          pointHoverBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        scales: {
          x: {
            ticks: { color: '#b9c7d6', maxRotation: 0, autoSkip: false, font: { family: 'Roboto', size: 10 } },
            grid: { display: true, color: 'rgba(255,255,255,0.1)' },
            border: { color: 'rgba(0, 224, 255, 0.3)' }
          },
          y: {
            beginAtZero: false,
            ticks: {
              color: '#b9c7d6',
              font: { family: 'Roboto', size: 12 },
              stepSize: 5,
              callback: function (value) {
                return (value >= 0 ? '+' : '') + value;
              }
            },
            grid: { color: 'rgba(255,255,255,0.15)' },
            border: { color: 'rgba(0, 224, 255, 0.3)' }
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(12, 18, 32, 0.95)',
            titleColor: '#00e0ff',
            bodyColor: '#ffffff',
            borderColor: '#00e0ff',
            borderWidth: 1,
            cornerRadius: 8,
            titleFont: { family: 'Orbitron', size: 12, weight: 'bold' },
            bodyFont: { family: 'Roboto', size: 11 },
            callbacks: {
              title: function (context) {
                const index = context[0].dataIndex;
                return chartData.dates[index] || context[0].label;
              },
              label: function (context) {
                const value = context.parsed.y;
                return 'Total Units: ' + (value >= 0 ? '+' : '') + value.toFixed(2);
              }
            }
          }
        }
      }
    });
  }

  // ---- Bet-type breakdown (Record By Bet Type) ----
  // Mirrors scripts/categorize_picks_verify.py exactly so on-page numbers
  // match the verifier output. Always renders 2025 / 2026 / Total columns,
  // independent of the year-filter tabs.

  const BET_TYPE_GROUPS = {
    NHL: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Puck Line',          rows: [{key:'Puck Line', label:'Puck Line'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: '3-Way / Regulation', rows: [{key:'3-Way / Regulation', label:'3-Way'}], showTotal: false },
      { label: 'Parlays',            rows: [{key:'Parlay', label:'Parlay'}, {key:'Teaser', label:'Teaser'}], showTotal: true }
    ],
    MLB: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Run Line',           rows: [{key:'Run Line', label:'Run Line'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: 'First 5 Innings',    rows: [{key:'F5 Moneyline', label:'F5 Moneyline'}, {key:'F5 Total', label:'F5 Total'}], showTotal: true },
      { label: 'NRFI / YRFI',        rows: [{key:'NRFI/YRFI', label:'NRFI/YRFI'}], showTotal: false },
      { label: 'Futures',            rows: [{key:'Futures', label:'Futures'}], showTotal: false },
      { label: 'Parlays',            rows: [{key:'Parlay', label:'Parlay'}, {key:'Teaser', label:'Teaser'}], showTotal: true }
    ],
    NFL: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Spread',             rows: [{key:'Spread', label:'Spread'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: 'Teasers / Parlays',  rows: [{key:'Teaser', label:'Teaser'}, {key:'Parlay', label:'Parlay'}], showTotal: true }
    ],
    NCAAF: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Spread',             rows: [{key:'Spread', label:'Spread'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: 'Teasers / Parlays',  rows: [{key:'Teaser', label:'Teaser'}, {key:'Parlay', label:'Parlay'}], showTotal: true }
    ],
    NBA: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Spread',             rows: [{key:'Spread', label:'Spread'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: '1st / 2nd Half',     rows: [{key:'1H/2H Spread', label:'Spread'}, {key:'1H/2H Total', label:'Total'}], showTotal: true },
      { label: 'Parlays / Teasers',  rows: [{key:'Parlay', label:'Parlay'}, {key:'Teaser', label:'Teaser'}], showTotal: true }
    ],
    NCAAB: [
      { label: 'Moneyline',          rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Spread',             rows: [{key:'Spread', label:'Spread'}], showTotal: false },
      { label: 'Game Totals',        rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Team Totals',        rows: [{key:'Team Total Over', label:'Overs'}, {key:'Team Total Under', label:'Unders'}], showTotal: true },
      { label: '1st / 2nd Half',     rows: [{key:'1H/2H Spread', label:'Spread'}, {key:'1H/2H Total', label:'Total'}], showTotal: true },
      { label: 'Parlays / Teasers',  rows: [{key:'Parlay', label:'Parlay'}, {key:'Teaser', label:'Teaser'}], showTotal: true }
    ],
    Soccer: [
      { label: 'Moneyline / 3-Way',  rows: [{key:'Moneyline', label:'Moneyline'}], showTotal: false },
      { label: 'Goals O/U',          rows: [{key:'Game Total Over', label:'Overs'}, {key:'Game Total Under', label:'Unders'}], showTotal: true },
      { label: 'Corners O/U',        rows: [{key:'Corners O/U', label:'Corners'}], showTotal: false },
      { label: 'Parlays',            rows: [{key:'Parlay', label:'Parlay'}, {key:'Teaser', label:'Teaser'}], showTotal: true }
    ]
  };

  function categorizeBetType(sport, pick) {
    const p = String(pick || '').replace(/\s+/g, ' ').trim();
    const pl = p.toLowerCase();
    const hasOver  = /\bover\b/.test(pl);
    const hasUnder = /\bunder\b/.test(pl);

    if (pl.indexOf('teaser') !== -1) return 'Teaser';
    if (pl.indexOf('parlay') !== -1) return 'Parlay';
    const mlCount = (pl.match(/ ml\b/g) || []).length;
    if (mlCount >= 2 && (pl.indexOf(',') !== -1 || pl.indexOf('+') !== -1)) return 'Parlay';
    const mlnCount = (pl.match(/moneyline/g) || []).length;
    if (mlnCount >= 2 && (pl.indexOf(',') !== -1 || pl.indexOf('+') !== -1)) return 'Parlay';

    if (/to win (the )?(world series|stanley cup|super bowl|nba finals|world cup|championship|mvp|cy young|nl |al )/.test(pl)) {
      return 'Futures';
    }
    if (sport === 'NHL' && pl.indexOf('regulation') !== -1 && pl.indexOf('win') !== -1) {
      return '3-Way / Regulation';
    }
    if (sport === 'MLB') {
      if (/\b(f5|first 5|first five)\b/.test(pl)) {
        if (hasOver || hasUnder) return 'F5 Total';
        return 'F5 Moneyline';
      }
      if (/\b(nrfi|yrfi)\b/.test(pl)) return 'NRFI/YRFI';
    }
    if (sport === 'NBA' || sport === 'NCAAB') {
      if (/\b(1st half|first half|2nd half|second half|1h|2h)\b/.test(pl)) {
        if (hasOver || hasUnder) return '1H/2H Total';
        return '1H/2H Spread';
      }
    }
    if (sport === 'Soccer' && pl.indexOf('corner') !== -1) return 'Corners O/U';

    if (pl.indexOf('team total') !== -1) {
      if (hasOver)  return 'Team Total Over';
      if (hasUnder) return 'Team Total Under';
      return 'Team Total';
    }
    if (hasOver || hasUnder) {
      if (hasOver && !hasUnder) return 'Game Total Over';
      if (hasUnder && !hasOver) return 'Game Total Under';
    }
    if (/\bml\b/.test(pl) || pl.indexOf('moneyline') !== -1 || /\sml$/.test(pl)) return 'Moneyline';
    if (/[+-]\d+(\.\d+)?\b/.test(p)) {
      if (sport === 'NHL') return 'Puck Line';
      if (sport === 'MLB') return 'Run Line';
      return 'Spread';
    }
    if (/\bpk\b/.test(pl) && (sport === 'NBA' || sport === 'NFL' || sport === 'NCAAB' || sport === 'NCAAF')) {
      return 'Spread';
    }
    if (/^[A-Za-z\.\s]+$/.test(p)) return 'Moneyline';
    return 'Other';
  }

  function aggregateBucket(rows) {
    let W = 0, L = 0, P = 0, units = 0, risk = 0;
    rows.forEach(function (r) {
      if (r.result === 'W') W += 1;
      else if (r.result === 'L') L += 1;
      else if (r.result === 'P') P += 1;
      units += r.profitLoss;
      risk += calculateRisk(r);
    });
    const graded = W + L;
    const winPct = graded ? (W / graded) * 100 : 0;
    const roi = risk ? (units / risk) * 100 : 0;
    return { W: W, L: L, P: P, units: units, winPct: winPct, roi: roi, n: rows.length };
  }

  function fmtCell(b) {
    if (!b || b.n === 0) {
      return '<span class="bt-empty">&mdash;</span>';
    }
    const us = (b.units >= 0 ? '+' : '') + b.units.toFixed(2);
    const rs = (b.roi   >= 0 ? '+' : '') + b.roi.toFixed(2);
    const unitsClass = b.units >= 0 ? 'bt-units-win' : 'bt-units-loss';
    const roiClass   = b.roi   >= 0 ? 'bt-units-win' : 'bt-units-loss';
    return (
      '<div class="bt-record">' + b.W + '-' + b.L + '-' + b.P + '</div>' +
      '<div class="' + unitsClass + '">' + us + 'u</div>' +
      '<div class="bt-meta">' + b.winPct.toFixed(1) + '% &middot; <span class="' + roiClass + '">' + rs + '%</span></div>'
    );
  }

  function getYearFromRow(row) {
    return getYear(row.date);
  }

  function injectBetTypeStyles() {
    if (document.getElementById('bet-type-breakdown-styles')) return;
    // Visual style mirrors records.html table aesthetic: gradient cyan->gold
    // thead, generous padding, soft row dividers, cyan hover tint, gold
    // section titles. No heavy bordered "boxes" - groups blend into the page.
    const css = '' +
      '#bet-type-breakdown { margin: 40px 0; }' +
      '#bet-type-breakdown .bt-section-title { font-family: Orbitron, sans-serif; font-size: 32px; text-align: center; color: var(--neon-gold, #FFD700); letter-spacing: 2px; text-transform: uppercase; margin: 30px 0 6px 0; text-shadow: 0 0 12px rgba(255, 215, 0, 0.35); }' +
      '#bet-type-breakdown .bt-subtitle { text-align: center; color: #9bb3c9; font-family: Roboto, sans-serif; font-size: 15px; margin: 0 0 28px 0; }' +
      '#bet-type-breakdown .bt-group { margin: 0 0 36px 0; padding: 0; background: transparent; border: 0; box-shadow: none; }' +
      '#bet-type-breakdown .bt-group h3 { font-family: Orbitron, sans-serif; font-size: 22px; color: var(--neon-gold, #FFD700); letter-spacing: 2px; text-transform: uppercase; margin: 0 0 14px 0; padding: 0 0 10px 0; text-align: left; border-bottom: 2px solid rgba(255, 215, 0, 0.35); display: flex; align-items: center; gap: 12px; }' +
      '#bet-type-breakdown .bt-group h3::before { content: ""; display: inline-block; width: 36px; height: 3px; background: linear-gradient(90deg, var(--glow-color, #00e0ff), var(--neon-gold, #FFD700)); border-radius: 2px; }' +
      '#bet-type-breakdown table.bt-table { width: 100%; border-collapse: collapse; font-family: Roboto, sans-serif; background: rgba(12, 18, 32, 0.55); border-radius: 10px; overflow: hidden; }' +
      '#bet-type-breakdown table.bt-table thead { background: linear-gradient(135deg, rgba(0, 224, 255, 0.18) 0%, rgba(255, 215, 0, 0.18) 100%); }' +
      '#bet-type-breakdown table.bt-table thead th { font-family: Orbitron, sans-serif; font-size: 14px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--glow-color, #00e0ff); padding: 18px 22px; text-align: left; font-weight: 700; border-bottom: 2px solid var(--glow-color, #00e0ff); }' +
      '#bet-type-breakdown table.bt-table thead th + th { text-align: center; }' +
      '#bet-type-breakdown table.bt-table tbody td { padding: 18px 22px; border-bottom: 1px solid rgba(255, 255, 255, 0.08); color: #e6edf5; font-size: 16px; vertical-align: middle; text-align: center; }' +
      '#bet-type-breakdown table.bt-table tbody td:first-child { text-align: left; font-family: Orbitron, sans-serif; font-size: 15px; letter-spacing: 0.5px; color: #fff; font-weight: 700; }' +
      '#bet-type-breakdown table.bt-table tbody tr { transition: background 0.2s ease; }' +
      '#bet-type-breakdown table.bt-table tbody tr:hover { background: rgba(0, 224, 255, 0.06); }' +
      '#bet-type-breakdown table.bt-table tbody tr:last-child td { border-bottom: 0; }' +
      '#bet-type-breakdown table.bt-table tr.bt-total td { background: linear-gradient(135deg, rgba(0, 224, 255, 0.07) 0%, rgba(255, 215, 0, 0.07) 100%); border-top: 2px solid rgba(0, 224, 255, 0.35); border-bottom: 0; }' +
      '#bet-type-breakdown table.bt-table tr.bt-total td:first-child { color: var(--neon-gold, #FFD700); text-transform: uppercase; letter-spacing: 1px; }' +
      '#bet-type-breakdown .bt-record { font-family: Orbitron, sans-serif; font-weight: 700; color: #fff; font-size: 18px; letter-spacing: 0.5px; }' +
      '#bet-type-breakdown .bt-units-win { color: var(--win-color, #39FF14); font-weight: 700; }' +
      '#bet-type-breakdown .bt-units-loss { color: var(--loss-color, #FF3131); font-weight: 700; }' +
      '#bet-type-breakdown .bt-meta { color: #9bb3c9; font-size: 13px; margin-top: 4px; font-family: Roboto, sans-serif; }' +
      '#bet-type-breakdown .bt-empty { color: #4a5568; font-size: 18px; }' +
      '@media (max-width: 768px) {' +
      '  #bet-type-breakdown { margin: 30px 0; }' +
      '  #bet-type-breakdown .bt-section-title { font-size: 26px; }' +
      '  #bet-type-breakdown .bt-group h3 { font-size: 18px; }' +
      '  #bet-type-breakdown table.bt-table thead th { padding: 12px 10px; font-size: 11px; letter-spacing: 1px; }' +
      '  #bet-type-breakdown table.bt-table tbody td { padding: 12px 10px; font-size: 13px; }' +
      '  #bet-type-breakdown table.bt-table tbody td:first-child { font-size: 12px; }' +
      '  #bet-type-breakdown .bt-record { font-size: 14px; }' +
      '  #bet-type-breakdown .bt-meta { font-size: 11px; }' +
      '}';
    const style = document.createElement('style');
    style.id = 'bet-type-breakdown-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function renderBetTypeBreakdown(rows, sport) {
    const container = document.getElementById('bet-type-breakdown');
    if (!container) return;
    const groups = BET_TYPE_GROUPS[sport];
    if (!groups) {
      container.innerHTML = '';
      return;
    }
    injectBetTypeStyles();

    const years = [2025, 2026];
    // Index rows by category, then by year
    const byCat = {};
    rows.forEach(function (row) {
      const c = categorizeBetType(sport, row.pick);
      if (!byCat[c]) byCat[c] = [];
      byCat[c].push(row);
    });

    function rowsFor(catKey, year) {
      const arr = byCat[catKey] || [];
      if (year == null) return arr;
      return arr.filter(function (r) { return getYearFromRow(r) === year; });
    }

    let html = '';
    html += '<h2 class="bt-section-title">Record By Bet Type</h2>';
    html += '<p class="bt-subtitle">Win-Loss-Push, units, win rate and ROI for each bet category. Year-by-year and overall.</p>';

    groups.forEach(function (group) {
      const subRows = group.rows;
      // Skip the entire group if it has zero picks across all sub-rows
      let total = 0;
      subRows.forEach(function (sr) { total += (byCat[sr.key] || []).length; });
      if (total === 0) return;

      html += '<div class="bt-group">';
      html += '<h3>' + group.label + '</h3>';
      html += '<table class="bt-table"><thead><tr>';
      html += '<th>Type</th><th>2025</th><th>2026</th><th>Total</th>';
      html += '</tr></thead><tbody>';

      subRows.forEach(function (sr) {
        const all2025 = rowsFor(sr.key, 2025);
        const all2026 = rowsFor(sr.key, 2026);
        const allTime = rowsFor(sr.key, null);
        if (allTime.length === 0) return;
        html += '<tr>';
        html += '<td>' + sr.label + '</td>';
        html += '<td>' + fmtCell(aggregateBucket(all2025)) + '</td>';
        html += '<td>' + fmtCell(aggregateBucket(all2026)) + '</td>';
        html += '<td>' + fmtCell(aggregateBucket(allTime)) + '</td>';
        html += '</tr>';
      });

      if (group.showTotal) {
        const allKeys = subRows.map(function (sr) { return sr.key; });
        const all2025 = []; const all2026 = []; const allTime = [];
        allKeys.forEach(function (k) {
          (byCat[k] || []).forEach(function (r) {
            allTime.push(r);
            const y = getYearFromRow(r);
            if (y === 2025) all2025.push(r);
            else if (y === 2026) all2026.push(r);
          });
        });
        html += '<tr class="bt-total">';
        html += '<td>Total</td>';
        html += '<td>' + fmtCell(aggregateBucket(all2025)) + '</td>';
        html += '<td>' + fmtCell(aggregateBucket(all2026)) + '</td>';
        html += '<td>' + fmtCell(aggregateBucket(allTime)) + '</td>';
        html += '</tr>';
      }

      html += '</tbody></table></div>';
    });

    container.innerHTML = html;
  }

  // ---- Data loaders ----

  async function loadLiveRows(sport) {
    const all = await window.RecordsEngine.loadAllPicks();
    return all
      .filter((p) => p.sport === sport)
      .map((p) => ({
        sport: p.sport,
        date: normalizeDateString(p.date),
        pick: p.pick,
        odds: p.line,
        result: p.result,
        profitLoss: typeof p.unitPL === 'number' ? p.unitPL : parseProfitLoss(p.unitPL),
        stake: typeof p.stake === 'number' ? p.stake : null
      }));
  }

  async function loadJsonRows(sport) {
    const response = await fetch(DATA_URL + '?v=' + Date.now(), { cache: 'no-store' });
    if (!response.ok) {
      throw new Error('Failed to load ' + DATA_URL + ': ' + response.status);
    }
    const rows = await response.json();
    return rows
      .filter((row) => String(row.Sport || row.sport || '').trim() === sport)
      .map((row) => ({
        sport: String(row.Sport || row.sport || '').trim(),
        date: normalizeDateString(row.Date || row.date || ''),
        pick: String(row.Picks || row.Pick || row.pick || '').trim(),
        odds: String(row.Odds || row.Line || row.line || '').trim(),
        result: normalizeResult(row.Result || row.result || ''),
        profitLoss: parseProfitLoss(row.ProfitLoss || row.Units || row.unitPL || 0),
        stake: null
      }));
  }

  async function loadSportRows(sport) {
    if (window.RecordsEngine && typeof window.RecordsEngine.loadAllPicks === 'function') {
      try {
        const live = await loadLiveRows(sport);
        if (live && live.length) return live;
      } catch (err) {
        console.warn('[records-sport-page] live fetch failed, falling back to ' + DATA_URL, err);
      }
    }
    return loadJsonRows(sport);
  }

  function filterRows(rows, year) {
    if (year === 'all') return rows.slice();
    const targetYear = parseInt(year, 10);
    return rows.filter((row) => getYear(row.date) === targetYear);
  }

  function initYearButtons(render, defaultYear) {
    const buttons = Array.from(document.querySelectorAll('.year-filter-btn'));
    buttons.forEach((button) => {
      button.classList.toggle('active', button.getAttribute('data-year') === defaultYear);
      button.addEventListener('click', function () {
        buttons.forEach((item) => item.classList.remove('active'));
        this.classList.add('active');
        render(this.getAttribute('data-year') || 'all');
      });
    });
  }

  function initDropdownMenus() {
    const dropdowns = Array.from(document.querySelectorAll('.dropdown'));
    dropdowns.forEach((dropdown) => {
      const button = dropdown.querySelector('.dropbtn');
      if (!button) return;
      button.addEventListener('click', function (event) {
        event.preventDefault();
        event.stopPropagation();
        dropdowns.forEach((item) => {
          if (item !== dropdown) item.classList.remove('active');
        });
        dropdown.classList.toggle('active');
      });
    });

    document.addEventListener('click', function (event) {
      if (event.target.closest('.dropdown')) return;
      dropdowns.forEach((dropdown) => dropdown.classList.remove('active'));
    });
  }

  async function initSportPage(config) {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) loadingMessage.style.display = 'block';
    initDropdownMenus();

    try {
      const sportRows = (await loadSportRows(config.sport))
        .filter((row) => row.result)
        .sort((a, b) => {
          const aDate = parseDate(a.date);
          const bDate = parseDate(b.date);
          return (bDate ? bDate.getTime() : 0) - (aDate ? aDate.getTime() : 0);
        });

      const tbody = document.getElementById('picks-table-body');
      const render = function (year) {
        const filtered = filterRows(sportRows, year);
        if (tbody) renderTableRows(filtered, tbody);
        updateSummary(filtered);
        updateChart(filtered, config.chartStateKey || '__betlegendRecordsChart');
      };

      initYearButtons(render, config.defaultYear || 'all');
      render(config.defaultYear || 'all');

      // Bet-type breakdown is independent of the year filter - it always
      // shows 2025 / 2026 / Total side-by-side.
      try {
        renderBetTypeBreakdown(sportRows, config.sport);
      } catch (err) {
        console.warn('[records-sport-page] bet-type breakdown failed:', err);
      }
    } catch (err) {
      console.error('[records-sport-page] fatal:', err);
      const tbody = document.getElementById('picks-table-body');
      if (tbody) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:20px;color:#FF3131;">Records failed to load. Please refresh the page.</td></tr>';
      }
    } finally {
      if (loadingMessage) loadingMessage.style.display = 'none';
    }
  }

  window.BetLegendRecords = {
    initSportPage: initSportPage
  };
})();
