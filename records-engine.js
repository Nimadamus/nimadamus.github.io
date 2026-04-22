/*
  records-engine.js
  Shared data layer + stats calculator for every /records page on betlegendpicks.com.

  One source of truth. Every records page (hub + sport pages) loads the same
  data with the same dedup and P/L math, so totals never disagree.

  Data flow:
    1. Fetch Pick Tracker master sheet (live Google Sheets CSV).
    2. Fetch each sport-specific sheet (live Google Sheets CSV).
    3. Normalize rows -> { date, pick, line, result, sport, unitPL }.
    4. Dedup tracker-first by date|sport|normalizedPick|normalizedLine.
       (Tracker wins because its stake data is cleaner.)
    5. Expose filter + calculate helpers.

  Pick Tracker stores Units as STAKE; P/L is calculated from stake/odds/result.
  Sport sheets store Units as pre-calculated P/L and are used as-is.
*/
(function (global) {
  'use strict';

  var PICK_TRACKER_URL = 'https://docs.google.com/spreadsheets/d/1izhxwiiazn99SRqcK8QpUE4pfvDRIFpgSyw5ZlMsvmY/export?format=csv&gid=0';

  var SHEET_URLS = {
    NFL:    'https://docs.google.com/spreadsheets/d/e/2PACX-1vQgB4WcyyEpMBp_XI_ya6hC7Y8kRaHzrOvuLMq9voGF0nzfqi4lkmAWVb92nDkxUhLVhzr4RTWtZRxq/pub?output=csv',
    NBA:    'https://docs.google.com/spreadsheets/d/e/2PACX-1vSBoPl-dhj7ZAVpRIafqrFBf10r6sg3jpEKxmuymugAckdoMp-czkj1hscpDnV42GGJsIvNx5EniLVz/pub?output=csv',
    NHL:    'https://docs.google.com/spreadsheets/d/e/2PACX-1vRaRwsGOmbXrqAX0xqrDc9XwRCSaAOkuW68TArz3XQp7SMmLirKbdYqU5-zSM_A-MDNKG6sbdwZac6I/pub?output=csv',
    MLB:    'https://docs.google.com/spreadsheets/d/e/2PACX-1vQE9RjSNABgl0SxSA1ghp9soUs4gq7teoncN5GLmG5faXmH-sDwXgg0mrk0iQwmSEYExtx6xwFMflXv/pub?output=csv',
    NCAAF:  'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ9c45xiuXWNe-fAXYMoNb00kCBHfMf4Yn-Xr2LUqdCIiuoiXXDgrDa5mq1PZqxjg8hx-5KnS0L4uVU/pub?output=csv',
    NCAAB:  'https://docs.google.com/spreadsheets/d/e/2PACX-1vQrFb66HE90gCwliIBQlZ5cNBApJWtGuUV1WbS4pd12SMrs_3qlmSFZCLJ9vBmfgZKcaaGyg4G15J3Y/pub?output=csv',
    Soccer: 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQy0EQskvixsVQb1zzYtCKDa4F1Wl6WU5QuAFMit32vms-c4DxlhLik-k7U_EhuYntQrpw4BI6r0rns/pub?output=csv'
  };

  var DEFAULT_STAKES = { NFL: 2, NBA: 1, NHL: 3, MLB: 1, NCAAF: 3, NCAAB: 3, Soccer: 1 };

  function parseCSV(csvText) {
    var lines = csvText.split('\n');
    if (!lines.length) return [];
    var rawHeaders = parseCSVLine(lines[0]);
    var hasResult = false;
    for (var h = 0; h < rawHeaders.length; h++) {
      if (((rawHeaders[h] || '') + '').toLowerCase().indexOf('result') >= 0) { hasResult = true; break; }
    }
    var headers = rawHeaders.map(function (h, idx) {
      var name = (h || '').trim().replace(/"/g, '');
      if (name.toLowerCase() === 'odds') return 'Line';
      if (name === '') {
        if (!hasResult) { hasResult = true; return 'Result'; }
        return 'Column' + idx;
      }
      return name;
    });
    var rows = [];
    for (var i = 1; i < lines.length; i++) {
      if (!lines[i].trim()) continue;
      var values = parseCSVLine(lines[i]);
      if (values.length < 4) continue;
      var row = {};
      headers.forEach(function (h, idx) {
        if (h && values[idx] !== undefined) row[h] = (values[idx] || '').trim();
      });
      if (!row.Result) {
        for (var j = 0; j < values.length; j++) {
          var v = (values[j] || '').trim().toUpperCase();
          if (v === 'W' || v === 'L' || v === 'P' || v === 'WIN' || v === 'LOSS' || v === 'PUSH') {
            row.Result = v;
            break;
          }
        }
      }
      rows.push(row);
    }
    return rows;
  }

  function parseCSVLine(line) {
    var out = [];
    var cur = '';
    var inQ = false;
    for (var j = 0; j < line.length; j++) {
      var ch = line[j];
      if (ch === '"') { inQ = !inQ; continue; }
      if (ch === ',' && !inQ) { out.push(cur); cur = ''; continue; }
      cur += ch;
    }
    out.push(cur);
    return out.map(function (s) { return s.trim(); });
  }

  function normalizeDate(dateStr) {
    if (!dateStr) return '';
    dateStr = String(dateStr).trim();
    var parts = dateStr.split(/[-\/]/);
    if (parts.length !== 3) return dateStr;
    var m = parseInt(parts[0], 10);
    var d = parseInt(parts[1], 10);
    var yStr = parts[2].trim();
    var y = parseInt(yStr, 10);
    if (/^0\d+$/.test(yStr)) { y = parseInt(yStr.replace(/^0+/, ''), 10); }
    if (/^\d{3}$/.test(yStr) && yStr.indexOf('20') === 0) {
      y = parseInt(yStr.slice(0, 2) + '2' + yStr.slice(2), 10);
    }
    if (y > 2030 && y < 3000) { y = parseInt('20' + String(y).slice(-2), 10); }
    if (!isNaN(m) && !isNaN(d) && !isNaN(y) && y >= 2020 && y <= 2030) {
      return m + '/' + d + '/' + y;
    }
    return dateStr;
  }

  function normalizePick(s) {
    return String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function normalizeLine(s) {
    return String(s || '').replace(/,/g, '').trim().replace(/^\+/, '');
  }

  function detectSportFromTrackerRow(row) {
    var league = (row.League || '').toLowerCase().trim();
    var sport = (row.Sport || '').toLowerCase().trim();
    if (league === 'cross-sport') return null;
    if (league === 'nfl') return 'NFL';
    if (league === 'nba') return 'NBA';
    if (league === 'nhl') return 'NHL';
    if (league === 'mlb') return 'MLB';
    if (league === 'ncaaf' || league === 'cfb') return 'NCAAF';
    if (league === 'ncaab' || league === 'cbb') return 'NCAAB';
    if (league === 'soccer' || league === 'mls') return 'Soccer';
    if (sport === 'football') return 'NFL';
    if (sport === 'basketball') return 'NBA';
    if (sport === 'hockey') return 'NHL';
    if (sport === 'baseball') return 'MLB';
    return null;
  }

  var NFL_TEAM_NAMES = ['49ers','bears','bengals','bills','broncos','browns','buccaneers','bucs',
    'cardinals','chargers','chiefs','colts','commanders','cowboys','dolphins','eagles','falcons',
    'giants','jaguars','jets','lions','packers','panthers','patriots','raiders','rams','ravens',
    'saints','seahawks','steelers','texans','titans','vikings',
    'san francisco','chicago','cincinnati','buffalo','denver','cleveland','tampa bay','arizona',
    'kansas city','indianapolis','washington','dallas','philadelphia','atlanta',
    'jacksonville','detroit','green bay','carolina','new england','las vegas','baltimore',
    'new orleans','seattle','pittsburgh','houston','tennessee','minnesota'];
  var COLLEGE_ONLY_NAMES = ['alabama','auburn','clemson','oregon','michigan','ohio state',
    'texas tech','tcu','byu','missouri','army','uconn','new mexico','central michigan',
    'coastal carolina','illinois','miami florida','mississippi','indiana','boise state',
    'memphis','smu','tulane','unlv','fresno state','ole miss','notre dame','penn state',
    'lsu','georgia','florida','florida state','oklahoma','iowa','wisconsin','purdue',
    'northwestern','nebraska','maryland','rutgers','michigan state','james madison','liberty'];

  function parseOdds(val) {
    if (val === undefined || val === null) return NaN;
    var s = String(val).replace(/,/g, '').replace(/^\+/, '').trim();
    var n = parseFloat(s);
    return isNaN(n) ? NaN : n;
  }

  function calculateUnitResult(stake, odds, result) {
    var s = parseFloat(stake);
    var o = parseOdds(odds);
    if (isNaN(s)) return 0;
    if (isNaN(o)) o = -110;
    var r = (result || '').toUpperCase().trim();
    if (r.indexOf('W') === 0) return o < 0 ? s : s * (o / 100);
    if (r.indexOf('L') === 0) return o < 0 ? -s * (Math.abs(o) / 100) : -s;
    return 0;
  }

  function mapTrackerRow(row) {
    var sport = detectSportFromTrackerRow(row);
    if (!sport) return null;
    var result = (row.Result || '').toUpperCase().trim();
    if (!(result.indexOf('W') === 0 || result.indexOf('L') === 0 || result.indexOf('P') === 0)) return null;
    var date = row.Date || row.date || '';
    var pick = row.Pick || row.pick || '';
    var pickLower = pick.toLowerCase();
    if (sport === 'NFL') {
      var hasNFL = NFL_TEAM_NAMES.some(function (t) { return pickLower.indexOf(t) >= 0; });
      var hasCollege = COLLEGE_ONLY_NAMES.some(function (t) { return pickLower.indexOf(t) >= 0; });
      if (hasCollege && !hasNFL) return null;
    }
    var line = row.Odds || row.Line || '-110';
    var stakeRaw = (row.Units || '').trim();
    var stake = stakeRaw ? parseFloat(stakeRaw) : DEFAULT_STAKES[sport] || 1;
    if (isNaN(stake)) stake = DEFAULT_STAKES[sport] || 1;
    var pl = calculateUnitResult(stake, line, result);
    return {
      date: date,
      pick: pick,
      line: line,
      result: result.charAt(0),
      sport: sport,
      stake: stake,
      unitPL: pl,
      source: 'tracker'
    };
  }

  function mapSheetRow(row, sport) {
    var result = (row.Result || '').toUpperCase().trim();
    if (!(result.indexOf('W') === 0 || result.indexOf('L') === 0 || result.indexOf('P') === 0)) return null;
    var line = row.Line || row.Odds || '-110';
    var pl = parseFloat((row.Units || '0').toString().replace(/,/g, '')) || 0;
    return {
      date: row.Date || '',
      pick: row.Pick || '',
      line: line,
      result: result.charAt(0),
      sport: sport,
      stake: null,
      unitPL: pl,
      source: 'sheet'
    };
  }

  function dedupMerge(trackerRows, sheetRowsBySport) {
    var combined = [];
    trackerRows.forEach(function (r) { if (r) combined.push(r); });
    Object.keys(sheetRowsBySport).forEach(function (sport) {
      sheetRowsBySport[sport].forEach(function (r) { if (r) combined.push(r); });
    });
    var seen = Object.create(null);
    var out = [];
    for (var i = 0; i < combined.length; i++) {
      var r = combined[i];
      var key = normalizeDate(r.date) + '|' + r.sport + '|' + normalizePick(r.pick) + '|' + normalizeLine(r.line);
      if (seen[key]) continue;
      seen[key] = true;
      out.push(r);
    }
    return out;
  }

  function extractYear(dateStr) {
    var norm = normalizeDate(dateStr);
    var parts = norm.split(/[-\/]/);
    if (parts.length === 3) {
      var y = parseInt(parts[2], 10);
      if (y >= 2020 && y <= 2030) return y;
    }
    var m = String(dateStr || '').match(/20\d{2}/);
    return m ? parseInt(m[0], 10) : null;
  }

  function filterByYear(picks, year) {
    if (!year || year === 'all') return picks.slice();
    var target = parseInt(year, 10);
    return picks.filter(function (p) { return extractYear(p.date) === target; });
  }

  function filterBySport(picks, sport) {
    if (!sport) return picks.slice();
    return picks.filter(function (p) { return p.sport === sport; });
  }

  function calculateStats(picks) {
    var wins = 0, losses = 0, pushes = 0;
    var totalUnits = 0, totalRisked = 0;
    var totalDecimalOdds = 0, oddsCount = 0;

    picks.forEach(function (p) {
      var r = p.result;
      var odds = parseOdds(p.line);
      if (isNaN(odds)) odds = -110;
      var pl = typeof p.unitPL === 'number' ? p.unitPL : 0;
      var stake = p.stake;

      if (r === 'W') {
        wins++;
        totalUnits += pl;
        if (stake !== null && !isNaN(stake)) {
          totalRisked += odds < 0 ? stake * (Math.abs(odds) / 100) : stake;
        } else {
          totalRisked += odds < 0 ? pl * (Math.abs(odds) / 100) : (odds > 0 ? pl / (odds / 100) : pl);
        }
      } else if (r === 'L') {
        losses++;
        totalUnits += pl;
        if (stake !== null && !isNaN(stake)) {
          totalRisked += odds < 0 ? stake * (Math.abs(odds) / 100) : stake;
        } else {
          totalRisked += Math.abs(pl);
        }
      } else if (r === 'P') {
        pushes++;
        var effStake = (stake !== null && !isNaN(stake)) ? stake : 1;
        totalRisked += odds < 0 ? effStake * (Math.abs(odds) / 100) : effStake;
      }

      var pickLower = (p.pick || '').toLowerCase();
      var isParlayLike = pickLower.indexOf('parlay') >= 0 || pickLower.indexOf('teaser') >= 0 || pickLower.indexOf('tsr') >= 0;
      if (!isParlayLike && !isNaN(odds)) {
        var dec = odds > 0 ? (odds / 100) + 1 : (100 / Math.abs(odds)) + 1;
        totalDecimalOdds += dec;
        oddsCount++;
      }
    });

    var decided = wins + losses;
    var winRate = decided > 0 ? (wins / decided) * 100 : 0;
    var roi = totalRisked > 0 ? (totalUnits / totalRisked) * 100 : 0;

    var avgOdds = -110;
    if (oddsCount > 0) {
      var avgDecimal = totalDecimalOdds / oddsCount;
      avgOdds = avgDecimal >= 2.0
        ? Math.round((avgDecimal - 1) * 100)
        : Math.round(-100 / (avgDecimal - 1));
    }

    return {
      wins: wins,
      losses: losses,
      pushes: pushes,
      record: wins + '-' + losses + (pushes > 0 ? '-' + pushes : ''),
      winRate: winRate,
      units: totalUnits,
      totalRisked: totalRisked,
      roi: roi,
      avgOdds: avgOdds,
      count: decided + pushes
    };
  }

  function fetchCSV(url) {
    var cacheBuster = Date.now();
    var sep = url.indexOf('?') >= 0 ? '&' : '?';
    return fetch(url + sep + '_=' + cacheBuster)
      .then(function (res) { return res.ok ? res.text() : ''; })
      .catch(function () { return ''; });
  }

  var _cachedLoad = null;
  function loadAllPicks(options) {
    if (_cachedLoad && !(options && options.force)) return _cachedLoad;

    var trackerPromise = fetchCSV(PICK_TRACKER_URL).then(function (csv) {
      return parseCSV(csv).map(mapTrackerRow).filter(Boolean);
    });

    var sheetPromises = Object.keys(SHEET_URLS).map(function (sport) {
      return fetchCSV(SHEET_URLS[sport]).then(function (csv) {
        return { sport: sport, rows: parseCSV(csv).map(function (r) { return mapSheetRow(r, sport); }).filter(Boolean) };
      });
    });

    _cachedLoad = Promise.all([trackerPromise, Promise.all(sheetPromises)]).then(function (parts) {
      var trackerRows = parts[0];
      var sheetBundles = parts[1];
      var sheetBySport = {};
      sheetBundles.forEach(function (b) { sheetBySport[b.sport] = b.rows; });
      var merged = dedupMerge(trackerRows, sheetBySport);
      merged.sort(function (a, b) {
        var da = parseDateForSort(a.date);
        var db = parseDateForSort(b.date);
        return db - da;
      });
      return merged;
    });
    return _cachedLoad;
  }

  function parseDateForSort(dateStr) {
    var norm = normalizeDate(dateStr);
    var parts = norm.split('/');
    if (parts.length === 3) {
      var d = new Date(parseInt(parts[2], 10), parseInt(parts[0], 10) - 1, parseInt(parts[1], 10));
      if (!isNaN(d)) return d.getTime();
    }
    var d2 = new Date(dateStr);
    return isNaN(d2) ? 0 : d2.getTime();
  }

  function formatUnits(u) { return (u >= 0 ? '+' : '') + u.toFixed(2); }
  function formatPct(p) { return (p >= 0 ? '+' : '') + p.toFixed(2) + '%'; }
  function formatOdds(o) { return o > 0 ? ('+' + o) : String(o); }

  global.RecordsEngine = {
    loadAllPicks: loadAllPicks,
    filterBySport: filterBySport,
    filterByYear: filterByYear,
    calculateStats: calculateStats,
    normalizeDate: normalizeDate,
    normalizePick: normalizePick,
    normalizeLine: normalizeLine,
    extractYear: extractYear,
    parseOdds: parseOdds,
    calculateUnitResult: calculateUnitResult,
    formatUnits: formatUnits,
    formatPct: formatPct,
    formatOdds: formatOdds,
    _internal: {
      SHEET_URLS: SHEET_URLS,
      PICK_TRACKER_URL: PICK_TRACKER_URL,
      DEFAULT_STAKES: DEFAULT_STAKES,
      parseCSV: parseCSV
    }
  };
})(typeof window !== 'undefined' ? window : this);
