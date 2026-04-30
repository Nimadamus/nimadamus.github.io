/*
  records-color.js
  Shared per-cell color helpers for every BetLegendPicks records table.

  Each metric column (Record, Win %, Units, ROI) is colored independently
  based on its OWN value, not on the row's overall profitability:

    Record:  W > L -> green, L > W -> red, equal -> neutral (pushes ignored)
    Win %:   > 50  -> green, < 50  -> red, exactly 50 -> neutral
    Units:   > 0   -> green, < 0   -> red, 0 -> neutral
    ROI:     > 0   -> green, < 0   -> red, 0 -> neutral
    Empty bucket / no graded picks -> no class (muted/gray).
*/
(function () {
  function recordClass(wins, losses) {
    var w = Number(wins) || 0;
    var l = Number(losses) || 0;
    if (w > l) return 'win';
    if (l > w) return 'loss';
    return '';
  }
  function winPctClass(pct) {
    var p = Number(pct);
    if (!isFinite(p)) return '';
    if (p > 50) return 'win';
    if (p < 50) return 'loss';
    return '';
  }
  function unitsClass(units) {
    var u = Number(units);
    if (!isFinite(u) || u === 0) return '';
    return u > 0 ? 'win' : 'loss';
  }
  function roiClass(roi) {
    var r = Number(roi);
    if (!isFinite(r) || r === 0) return '';
    return r > 0 ? 'win' : 'loss';
  }

  // Legacy row-level helper kept so older callers keep working until they
  // migrate to the per-cell helpers above.
  function rowPerfClass(units, roi, wins, losses) {
    var u = Number(units) || 0;
    var r = Number(roi) || 0;
    var w = Number(wins) || 0;
    var l = Number(losses) || 0;
    if (u > 0 || r > 0) return 'win';
    if (u < 0 || r < 0) return 'loss';
    if (w > l) return 'win';
    if (l > w) return 'loss';
    return '';
  }

  var ns = window.BetLegendRecords || (window.BetLegendRecords = {});
  ns.recordClass = recordClass;
  ns.winPctClass = winPctClass;
  ns.unitsClass = unitsClass;
  ns.roiClass = roiClass;
  ns.rowPerfClass = rowPerfClass;
})();
