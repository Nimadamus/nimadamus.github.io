# Kelly Authority Cluster

## Project Status: PHASE 2 COMPLETE (LOCKED)

**Last Updated:** January 21, 2026
**Status:** Monitoring & Consolidation Window

---

## Phase Summary

### Phase 1: COMPLETE ✓
- Kelly calculator established as pillar page
- Simulation page deployed as satellite
- No risky features merged into calculator
- Quiet internal link added (calculator → simulation)

### Phase 2: COMPLETE ✓
- 3 educational authority pages created
- All internal links flow inward to Kelly + Simulation
- No UI, JS, or behavioral changes to core tools

---

## Frozen Pages (DO NOT MODIFY)

The following pages are **READ-ONLY** until Phase 3 is explicitly greenlit:

| Page | URL | Role |
|------|-----|------|
| kelly-criterion.html | /kelly-criterion.html | **PILLAR** |
| kelly-simulation.html | /kelly-simulation.html | Satellite |

**No refactors. No optimizations. No "improvements." No behavioral changes.**

---

## Authority Cluster Pages

| Page | Purpose | Status |
|------|---------|--------|
| kelly-criterion.html | Calculator + guide (pillar) | FROZEN |
| kelly-simulation.html | Visual bankroll simulation | FROZEN |
| kelly-criterion-explained.html | Plain English explanation | Live |
| fractional-kelly-vs-full-kelly.html | Strategy comparison | Live |
| kelly-criterion-mistakes.html | Common errors guide | Live |

**Internal Linking:** All satellite pages link inward to pillar. Authority flows to kelly-criterion.html.

---

## Phase 3 Trigger Conditions

**DO NOT BEGIN PHASE 3** until 2-3 of these signals appear in Google Search Console:

- [ ] Impressions rising consistently (week-over-week)
- [ ] Ranking volatility narrowing (same positions holding)
- [ ] Same URLs consistently ranking for Kelly queries
- [ ] Early organic clicks appearing
- [ ] Faster crawl frequency observed

**Expected Timeline:** ~4-8 weeks after Phase 2, but signals matter more than time.

---

## Phase 3 Implementation Rules (WHEN GREENLIT)

1. **Only ONE feature at a time** - never bundle
2. **Allowed features (pick one):**
   - Local-only bankroll tracker (no accounts, no APIs)
   - Optional email capture (non-gated, post-calculation)
   - Live odds integration (SEPARATE page, not merged into calculator)

3. **Still forbidden:**
   - Modifying kelly-criterion.html core behavior
   - Adding accounts or login
   - API dependencies on the calculator
   - Popups, modals, or gated content
   - Slow page load additions

---

## Why This Pause Exists

This project is **not paused due to uncertainty**.

It is paused because:
- The correct work for Phase 2 has been completed
- Google needs time to crawl, index, and establish page identity
- Premature feature additions risk destabilizing rankings
- SEO authority compounds; patience is the strategy

---

## Handoff Notes for Future Sessions

When resuming this project:

1. Check Google Search Console for Phase 3 trigger signals
2. If signals present → implement ONE Phase 3 feature
3. If signals not present → do not modify frozen pages
4. Always preserve kelly-criterion.html as the pillar
5. All new pages should link inward, not outward from pillar

---

## File Locations

```
C:\Users\Nima\nimadamus.github.io\
├── kelly-criterion.html          (PILLAR - FROZEN)
├── kelly-simulation.html         (SATELLITE - FROZEN)
├── kelly-criterion-explained.html
├── fractional-kelly-vs-full-kelly.html
├── kelly-criterion-mistakes.html
├── kelly-widget.html             (PHASE 5 - NOT DEPLOYED)
└── KELLY_AUTHORITY_CLUSTER.md    (THIS FILE)
```

---

**Project Owner:** User
**Implementation:** Claude Code
**Strategy:** Phased SEO authority building with frozen pillar protection
