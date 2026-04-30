/*
  records-color.js
  Shared row-level color logic for every BetLegendPicks records table.

  All tables (Breakdown by Bet Type, Sport Breakdown, Monthly, Unit Sizing,
  Teaser, Parlay, Total Bets, Team Totals, etc.) must color the Record,
  Win %, Units and ROI cells using the SAME rule:

    1. Profitability wins: if Units > 0 OR ROI > 0  -> green
    2. Profitability wins: if Units < 0 OR ROI < 0  -> red
    3. Both Units and ROI exactly neutral -> fall back to W/L record
       (pushes are ignored in the W/L comparison).
    4. Empty bucket / no graded picks -> no class (muted/gray).
*/
(function () {
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
  ns.rowPerfClass = rowPerfClass;
})();
