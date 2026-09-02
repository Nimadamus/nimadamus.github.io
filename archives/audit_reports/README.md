# BetLegend Picks

[![Content Validation](https://github.com/Nimadamus/nimadamus.github.io/actions/workflows/validate-content.yml/badge.svg)](https://github.com/Nimadamus/nimadamus.github.io/actions/workflows/validate-content.yml)

Sports betting analysis and picks at [betlegendpicks.com](https://www.betlegendpicks.com)

## Content Validation

This repository uses automated content validation on every push. The validator checks for:

- Player-team roster accuracy (via MLB Stats API)
- Structural HTML issues
- Placeholder content
- Broken internal links
- Statistical anomalies

**Deployment is blocked if validation fails.**

### Running Validation Locally

```bash
python betlegend_validator.py .
```

### Known Whitelisted Files

The following old archive files contain outdated roster information and are whitelisted (don't block deployment):

- `mlb-page2.html` - Old MLB content with outdated player teams
- `nfl-page16.html` - Old NFL content with API mismatch
