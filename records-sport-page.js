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
