/*
  first-inning-records.js
  Dedicated "First Inning Yes/No Bets" subsection for mlb-records.html.

  Reads the SAME live source as the rest of the MLB records page
  (window.RecordsEngine -> BetLegend Picks Tracker Google Sheet), filters
  MLB rows whose pick text is a first-inning yes/no market, and renders
  record / units / ROI / avg odds / avg units risked, plus a
  Yes Runs First Inning vs No Runs First Inning breakdown.

  Auto-updates as new sheet rows are added. Nothing is hardcoded.
  Follows the active year-filter tab, exactly like the bet-type breakdown.
*/
(function () {
  'use strict';

  var CONTAINER_ID = 'first-inning-breakdown';

  // --- Filter: is this pick a first-inning yes/no bet? ---
  // Include:  "No Runs First Inning", "Yes Runs First Inning", NRFI, YRFI,
  //           any "First Inning" market (e.g. First Inning Over/Under 0.5).
  // Exclude:  First 5 / First Five / F5 innings markets (those are separate),
  //           and anything without a first-inning signal (full-game totals,
  //           team totals, moneylines, run lines, props, etc.).
  function isFirstInningYesNo(pick) {
    var pl = String(pick || '').toLowerCase();
    if (/\bf5\b|first 5|first five/.test(pl)) return false; // not first-inning
    return /no runs first inning|yes runs first inning|\bnrfi\b|\byrfi\b|first inning/.test(pl);
  }

  // Yes (runs will score) vs No (no runs). Returns 'YES' | 'NO' | null.
  function yesNoSide(pick) {
    var pl = String(pick || '').toLowerCase();
    if (/\byrfi\b|yes runs first inning/.test(pl)) return 'YES';
    if (/\bnrfi\b|no runs first inning/.test(pl)) return 'NO';
    // Generic "first inning" total: over => runs (YES), under => no runs (NO).
    if (/first inning/.test(pl)) {
      if (/\bover\b/.test(pl)) return 'YES';
      if (/\bunder\b/.test(pl)) return 'NO';
    }
    return null;
  }

  function parseOdds(val) {
    if (window.RecordsEngine && typeof window.RecordsEngine.parseOdds === 'function') {
      return window.RecordsEngine.parseOdds(val);
    }
    var n = parseFloat(String(val || '').replace(/,/g, '').replace(/^\+/, ''));
    return isNaN(n) ? NaN : n;
  }

  // Amount at risk for one bet (matches records-sport-page.js calculateRisk):
  // negative odds risk stake*(|odds|/100); positive odds risk the stake.
  function riskFor(stake, odds) {
    var s = (typeof stake === 'number' && !isNaN(stake)) ? stake : 1;
    var o = parseOdds(odds);
    if (isNaN(o) || o === 0) return Math.abs(s);
    return o < 0 ? s * (Math.abs(o) / 100) : s;
  }

  function aggregate(rows) {
    var W = 0, L = 0, P = 0, units = 0, risk = 0;
    var stakeSum = 0, stakeCount = 0;
    var decOddsSum = 0, oddsCount = 0;
    rows.forEach(function (r) {
      if (r.result === 'W') W += 1;
      else if (r.result === 'L') L += 1;
      else if (r.result === 'P') P += 1;
      units += (typeof r.unitPL === 'number' ? r.unitPL : 0);
      risk += riskFor(r.stake, r.line);
      var s = (typeof r.stake === 'number' && !isNaN(r.stake)) ? r.stake : null;
      if (s !== null) { stakeSum += s; stakeCount += 1; }
      var o = parseOdds(r.line);
      if (!isNaN(o)) {
        decOddsSum += o > 0 ? (o / 100) + 1 : (100 / Math.abs(o)) + 1;
        oddsCount += 1;
      }
    });
    var graded = W + L;
    var winPct = graded ? (W / graded) * 100 : 0;
    var roi = risk ? (units / risk) * 100 : 0;
    var avgStake = stakeCount ? stakeSum / stakeCount : 0;
    var avgOdds = -110;
    if (oddsCount) {
      var avgDec = decOddsSum / oddsCount;
      avgOdds = avgDec >= 2.0 ? Math.round((avgDec - 1) * 100) : Math.round(-100 / (avgDec - 1));
    }
    return {
      n: rows.length, W: W, L: L, P: P, units: units, winPct: winPct,
      roi: roi, avgStake: avgStake, avgOdds: avgOdds
    };
  }

  function fmtUnits(u) { return (u >= 0 ? '+' : '') + u.toFixed(2); }
  function fmtPct(p) { return (p >= 0 ? '+' : '') + p.toFixed(2) + '%'; }
  function fmtOdds(o) { return o > 0 ? ('+' + o) : String(o); }
  function unitsCls(u) { return u > 0 ? 'win' : (u < 0 ? 'loss' : ''); }
  function recCls(b) { return b.W > b.L ? 'win' : (b.L > b.W ? 'loss' : ''); }

  function injectStyles() {
    if (document.getElementById('first-inning-breakdown-styles')) return;
    var css = '' +
      '#first-inning-breakdown { margin: 40px 0; }' +
      '#first-inning-breakdown .fi-section { background: rgba(26,26,26,0.6); border: 1px solid rgba(0,224,255,0.3); border-radius: 15px; padding: 40px; backdrop-filter: blur(10px); }' +
      '#first-inning-breakdown .fi-title { font-family: Orbitron, sans-serif; font-size: 44px; font-weight: 700; color: var(--neon-gold,#FFD700); margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 2px; display: flex; align-items: center; gap: 15px; }' +
      '#first-inning-breakdown .fi-title::before { content: ""; width: 50px; height: 4px; background: linear-gradient(90deg,var(--glow-color,#00e0ff),var(--neon-gold,#FFD700)); border-radius: 2px; flex: 0 0 50px; }' +
      '#first-inning-breakdown .fi-subtitle { color: #aaa; font-size: 14px; margin: 0 0 24px 0; font-family: Roboto, sans-serif; }' +
      '#first-inning-breakdown .fi-stats { display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 16px; margin-bottom: 28px; }' +
      '#first-inning-breakdown .fi-box { background: rgba(17,17,17,0.8); padding: 18px; border-radius: 8px; border: 1px solid var(--glow-color,#00e0ff); text-align: center; }' +
      '#first-inning-breakdown .fi-box h4 { margin: 0 0 8px 0; font-size: 13px; color: var(--glow-color,#00e0ff); text-transform: uppercase; letter-spacing: 1px; font-family: Orbitron, sans-serif; }' +
      '#first-inning-breakdown .fi-box p { margin: 0; font-family: Roboto, sans-serif; font-size: 24px; font-weight: 700; color: #fff; }' +
      '#first-inning-breakdown .fi-table-container { overflow-x: auto; }' +
      '#first-inning-breakdown table.fi-table { width: 100%; border-collapse: collapse; font-family: Roboto, sans-serif; min-width: 560px; }' +
      '#first-inning-breakdown table.fi-table thead { background: linear-gradient(135deg,rgba(0,224,255,0.2) 0%,rgba(255,215,0,0.2) 100%); }' +
      '#first-inning-breakdown table.fi-table th { font-family: Orbitron, sans-serif; padding: 18px 16px; text-align: left; font-weight: 700; color: var(--glow-color,#00e0ff); text-transform: uppercase; font-size: 15px; letter-spacing: 1px; border-bottom: 2px solid var(--glow-color,#00e0ff); white-space: nowrap; }' +
      '#first-inning-breakdown table.fi-table td { padding: 18px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); font-size: 18px; color: #fff; white-space: nowrap; }' +
      '#first-inning-breakdown table.fi-table tbody tr:last-child td { border-bottom: 0; }' +
      '#first-inning-breakdown .win { color: var(--win-color,#39FF14); font-weight: 700; }' +
      '#first-inning-breakdown .loss { color: var(--loss-color,#FF3131); font-weight: 700; }' +
      '#first-inning-breakdown .fi-empty { color: #888; font-family: Roboto, sans-serif; font-size: 16px; padding: 10px 0; }' +
      '#first-inning-breakdown .fi-note { color: #888; font-size: 12px; font-family: Roboto, sans-serif; margin-top: 18px; }' +
      '@media (max-width: 768px) {' +
      '  #first-inning-breakdown .fi-section { padding: 24px 18px; }' +
      '  #first-inning-breakdown .fi-title { font-size: 26px; gap: 10px; }' +
      '  #first-inning-breakdown .fi-title::before { width: 36px; flex: 0 0 36px; height: 3px; }' +
      '  #first-inning-breakdown table.fi-table th { padding: 12px 10px; font-size: 12px; }' +
      '  #first-inning-breakdown table.fi-table td { padding: 12px 10px; font-size: 14px; }' +
      '}';
    var style = document.createElement('style');
    style.id = 'first-inning-breakdown-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function statBox(label, value, cls) {
    return '<div class="fi-box"><h4>' + label + '</h4><p' +
      (cls ? ' class="' + cls + '"' : '') + '>' + value + '</p></div>';
  }

  function breakdownRow(name, b) {
    if (!b || b.n === 0) {
      return '<tr><td>' + name + '</td><td colspan="6" class="fi-empty">No graded bets yet</td></tr>';
    }
    return '<tr>' +
      '<td>' + name + '</td>' +
      '<td class="' + recCls(b) + '">' + b.W + '-' + b.L + '-' + b.P + '</td>' +
      '<td>' + b.winPct.toFixed(1) + '%</td>' +
      '<td class="' + unitsCls(b.units) + '">' + fmtUnits(b.units) + 'u</td>' +
      '<td class="' + (b.roi >= 0 ? 'win' : 'loss') + '">' + fmtPct(b.roi) + '</td>' +
      '<td>' + fmtOdds(b.avgOdds) + '</td>' +
      '<td>' + b.avgStake.toFixed(2) + 'u</td>' +
    '</tr>';
  }

  function render(fiRows) {
    var container = document.getElementById(CONTAINER_ID);
    if (!container) return;
    injectStyles();

    var overall = aggregate(fiRows);
    var yesRows = fiRows.filter(function (r) { return yesNoSide(r.pick) === 'YES'; });
    var noRows = fiRows.filter(function (r) { return yesNoSide(r.pick) === 'NO'; });
    var yes = aggregate(yesRows);
    var no = aggregate(noRows);

    var statsHtml;
    if (overall.n === 0) {
      statsHtml = '<p class="fi-empty">No first-inning yes/no bets graded for this period yet. This section fills in automatically as First Inning / NRFI / YRFI picks are added to the tracker.</p>';
    } else {
      statsHtml =
        '<div class="fi-stats">' +
          statBox('Record', overall.W + '-' + overall.L + '-' + overall.P, recCls(overall)) +
          statBox('Wins', String(overall.W), 'win') +
          statBox('Losses', String(overall.L), 'loss') +
          statBox('Pushes', String(overall.P)) +
          statBox('Win %', overall.winPct.toFixed(1) + '%') +
          statBox('Units', fmtUnits(overall.units) + 'u', unitsCls(overall.units)) +
          statBox('ROI', fmtPct(overall.roi), overall.roi >= 0 ? 'win' : 'loss') +
          statBox('Avg Odds', fmtOdds(overall.avgOdds)) +
          statBox('Avg Units Risked', overall.avgStake.toFixed(2) + 'u') +
        '</div>' +
        '<div class="fi-table-container">' +
          '<table class="fi-table">' +
            '<thead><tr>' +
              '<th>Market</th><th>Record</th><th>Win %</th><th>Units</th><th>ROI</th><th>Avg Odds</th><th>Avg Risked</th>' +
            '</tr></thead>' +
            '<tbody>' +
              breakdownRow('Yes Runs First Inning (YRFI)', yes) +
              breakdownRow('No Runs First Inning (NRFI)', no) +
            '</tbody>' +
          '</table>' +
        '</div>';
    }

    container.innerHTML =
      '<div class="fi-section">' +
        '<h2 class="fi-title">First Inning Yes/No Bets</h2>' +
        '<p class="fi-subtitle">Standalone tracking for first-inning run markets (NRFI / YRFI / First Inning Over-Under), pulled live from the BetLegend Picks Tracker. Full-game totals, team totals, moneylines, run lines, First 5 Innings and props are excluded. Follows the year tabs above.</p>' +
        statsHtml +
      '</div>';
  }

  // --- Data + year filtering (mirrors records-sport-page.js) ---
  var _allMlbFiRows = null;

  function getYear(dateStr) {
    if (window.RecordsEngine && typeof window.RecordsEngine.extractYear === 'function') {
      return window.RecordsEngine.extractYear(dateStr);
    }
    var m = String(dateStr || '').match(/(20\d{2})/);
    return m ? parseInt(m[1], 10) : null;
  }

  function visibleYears() {
    return Array.from(document.querySelectorAll('.year-filter-btn'))
      .map(function (b) { return b.getAttribute('data-year'); })
      .filter(function (y) { return y && y !== 'all' && !isNaN(parseInt(y, 10)); })
      .map(function (y) { return parseInt(y, 10); });
  }

  function filterByYear(rows, year) {
    if (year === 'all') {
      var vis = visibleYears();
      if (!vis.length) return rows.slice();
      var allowed = {};
      vis.forEach(function (y) { allowed[y] = true; });
      return rows.filter(function (r) { return allowed[getYear(r.date)]; });
    }
    var target = parseInt(year, 10);
    return rows.filter(function (r) { return getYear(r.date) === target; });
  }

  function renderForYear(year) {
    if (!_allMlbFiRows) return;
    render(filterByYear(_allMlbFiRows, year));
  }

  function activeYear() {
    var active = document.querySelector('.year-filter-btn.active');
    return (active && active.getAttribute('data-year')) || 'all';
  }

  function wireYearButtons() {
    Array.from(document.querySelectorAll('.year-filter-btn')).forEach(function (btn) {
      btn.addEventListener('click', function () {
        // Let records-sport-page.js flip the .active class first.
        setTimeout(function () { renderForYear(activeYear()); }, 0);
      });
    });
  }

  async function init() {
    var container = document.getElementById(CONTAINER_ID);
    if (!container) return;
    if (!window.RecordsEngine || typeof window.RecordsEngine.loadAllPicks !== 'function') {
      console.warn('[first-inning-records] RecordsEngine unavailable; section skipped.');
      return;
    }
    try {
      var all = await window.RecordsEngine.loadAllPicks();
      _allMlbFiRows = all
        .filter(function (p) { return p.sport === 'MLB'; })
        .filter(function (p) { return isFirstInningYesNo(p.pick); })
        .map(function (p) {
          return {
            date: p.date,
            pick: p.pick,
            line: p.line,
            result: p.result,
            unitPL: (typeof p.unitPL === 'number' ? p.unitPL : parseFloat(p.unitPL) || 0),
            stake: (typeof p.stake === 'number' ? p.stake : null)
          };
        });
      wireYearButtons();
      renderForYear(activeYear());
    } catch (err) {
      console.warn('[first-inning-records] load failed:', err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
