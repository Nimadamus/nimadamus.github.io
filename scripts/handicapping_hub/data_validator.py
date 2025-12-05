"""
DATA VALIDATION MODULE
======================
Validates all data before it reaches the HTML generator.
Ensures no blanks, NAs, or invalid values slip through.

Rules:
1. Every required field must have a value
2. Values must be within reasonable ranges
3. Missing values get intelligent defaults, not "NA"
4. Log all validation failures for debugging
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('data_validator')


class DataValidator:
    """Validates and sanitizes sports data before display"""

    # Reasonable ranges for statistics by sport
    STAT_RANGES = {
        'NBA': {
            'ppg': (80, 140),
            'oppg': (80, 140),
            'off_rtg': (95, 125),
            'def_rtg': (95, 125),
            'net_rtg': (-20, 20),
            'pace': (90, 110),
            'efg_pct': (0.40, 0.65),
            'ts_pct': (0.50, 0.70),
        },
        'NHL': {
            'gf_per_game': (1.5, 5.0),
            'ga_per_game': (1.5, 5.0),
            'pp_pct': (10, 35),
            'pk_pct': (70, 95),
            'sv_pct': (0.85, 0.95),
        },
        'NFL': {
            'ppg': (10, 40),
            'ypg': (250, 450),
            'rush_ypg': (70, 200),
            'pass_ypg': (150, 350),
        },
        'MLB': {
            'runs_per_game': (2.5, 7.0),
            'era': (2.0, 6.0),
            'ops': (0.600, 0.900),
        },
    }

    # Default values when data is unavailable
    SMART_DEFAULTS = {
        'NBA': {
            'ppg': 110.0,      # League average
            'oppg': 110.0,
            'off_rtg': 110.0,
            'def_rtg': 110.0,
            'net_rtg': 0.0,
            'pace': 100.0,
            'efg_pct': 0.52,
            'ts_pct': 0.57,
            'ats_record': '—',
            'ou_record': '—',
        },
        'NHL': {
            'gf_per_game': 3.0,
            'ga_per_game': 3.0,
            'pp_pct': 20.0,
            'pk_pct': 80.0,
            'sv_pct': 0.90,
            'cf_pct': 50.0,
            'xgf_pct': 50.0,
        },
        'NFL': {
            'ppg': 22.0,
            'oppg': 22.0,
            'ypg': 340.0,
            'rush_ypg': 115.0,
            'pass_ypg': 225.0,
            'to_diff': 0,
        },
        'NCAAF': {
            'ppg': 28.0,
            'oppg': 28.0,
            'ypg': 380.0,
        },
        'NCAAB': {
            'ppg': 72.0,
            'oppg': 72.0,
            'off_rtg': 105.0,
            'def_rtg': 105.0,
        },
        'MLB': {
            'runs_per_game': 4.5,
            'era': 4.20,
            'ops': 0.720,
        },
    }

    def __init__(self):
        self.validation_log = []

    def validate_game_data(self, sport: str, game_data: Dict) -> Tuple[bool, Dict, List[str]]:
        """
        Validate and sanitize a single game's data.

        Returns:
            - is_valid: Whether the game has minimum required data
            - sanitized_data: Data with defaults filled in
            - issues: List of validation issues found
        """
        issues = []
        sanitized = dict(game_data)

        # Check required fields
        game = game_data.get('game', {})
        if not game:
            issues.append("Missing game object")
            return False, sanitized, issues

        away = game.get('away', {})
        home = game.get('home', {})

        if not away.get('name') or not home.get('name'):
            issues.append("Missing team names")
            return False, sanitized, issues

        # Validate and fill records
        away['record'] = self._validate_record(away.get('record', ''), f"{away.get('name')} record")
        home['record'] = self._validate_record(home.get('record', ''), f"{home.get('name')} record")

        # Validate and fill stats
        away_stats = game_data.get('away_stats', {})
        home_stats = game_data.get('home_stats', {})

        sanitized['away_stats'] = self._fill_missing_stats(sport, away_stats, f"{away.get('name')} stats", issues)
        sanitized['home_stats'] = self._fill_missing_stats(sport, home_stats, f"{home.get('name')} stats", issues)

        # Validate odds
        odds = game_data.get('odds', {})
        sanitized['odds'] = self._validate_odds(odds, issues)

        # Ensure game object is updated
        game['away'] = away
        game['home'] = home
        sanitized['game'] = game

        return len(issues) < 5, sanitized, issues  # Allow some issues but not too many

    def _validate_record(self, record: str, context: str) -> str:
        """Validate a W-L record string"""
        if not record or record in ('', '-', 'N/A', None):
            logger.debug(f"Missing {context}, using placeholder")
            return '0-0'

        # Validate format (should be like "15-10" or "15-10-2" for NHL)
        parts = str(record).split('-')
        if len(parts) >= 2:
            try:
                wins = int(parts[0])
                losses = int(parts[1])
                if wins >= 0 and losses >= 0 and wins + losses <= 162:  # Max games in a season
                    return record
            except (ValueError, TypeError):
                pass

        logger.warning(f"Invalid {context}: {record}")
        return '0-0'

    def _fill_missing_stats(self, sport: str, stats: Dict, context: str, issues: List) -> Dict:
        """Fill in missing stats with smart defaults"""
        defaults = self.SMART_DEFAULTS.get(sport, {})
        filled = dict(stats)

        for key, default_val in defaults.items():
            if key not in filled or filled[key] in (None, '', '-', 'NA', 'N/A', 0):
                # Use smart default
                filled[key] = default_val
                logger.debug(f"Filled {context}.{key} with default {default_val}")
            else:
                # Validate the value is within range
                filled[key] = self._validate_stat_value(sport, key, filled[key])

        return filled

    def _validate_stat_value(self, sport: str, stat_name: str, value: Any) -> Any:
        """Validate a stat is within reasonable range"""
        ranges = self.STAT_RANGES.get(sport, {})

        if stat_name not in ranges:
            return value

        min_val, max_val = ranges[stat_name]

        try:
            num_val = float(value)
            if num_val < min_val or num_val > max_val:
                logger.warning(f"{sport} {stat_name}={value} outside range [{min_val}, {max_val}]")
                # Return midpoint as default
                return (min_val + max_val) / 2
            return num_val
        except (ValueError, TypeError):
            return self.SMART_DEFAULTS.get(sport, {}).get(stat_name, value)

    def _validate_odds(self, odds: Dict, issues: List) -> Dict:
        """Validate betting odds"""
        validated = dict(odds)

        # Spread validation
        spread = odds.get('spread_home')
        if spread is not None:
            try:
                spread_val = float(spread)
                if abs(spread_val) > 30:  # No spread should be > 30
                    issues.append(f"Suspicious spread: {spread}")
            except (ValueError, TypeError):
                pass

        # Total validation
        total = odds.get('total')
        if total is not None:
            try:
                total_val = float(total)
                if total_val < 30 or total_val > 300:
                    issues.append(f"Suspicious total: {total}")
            except (ValueError, TypeError):
                pass

        return validated

    def format_stat_for_display(self, value: Any, stat_type: str = 'number', decimals: int = 1) -> str:
        """
        Format a stat value for display.
        NEVER returns "NA" - uses em-dash for truly missing values.
        """
        if value is None or value == '' or str(value).upper() in ('NA', 'N/A', 'NULL', 'NONE'):
            return '—'  # Em-dash is more professional than "NA"

        try:
            if stat_type == 'number':
                return f"{float(value):.{decimals}f}"
            elif stat_type == 'percentage':
                val = float(value)
                # If value is already 0-100, use as-is; if 0-1, multiply by 100
                if val <= 1:
                    val *= 100
                return f"{val:.{decimals}f}%"
            elif stat_type == 'integer':
                return str(int(float(value)))
            elif stat_type == 'spread':
                val = float(value)
                return f"+{val:.1f}" if val > 0 else f"{val:.1f}"
            elif stat_type == 'moneyline':
                val = int(float(value))
                return f"+{val}" if val > 0 else str(val)
            else:
                return str(value)
        except (ValueError, TypeError):
            return '—'

    def generate_quality_report(self, all_data: Dict) -> Dict:
        """Generate a data quality report after processing"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'sports': {},
            'overall_completeness': 0,
            'issues': [],
        }

        total_fields = 0
        filled_fields = 0

        for sport, data in all_data.items():
            games = data.get('games', [])
            sport_report = {
                'game_count': len(games),
                'fields_populated': 0,
                'fields_total': 0,
                'games_with_issues': 0,
            }

            for game_data in games:
                is_valid, _, issues = self.validate_game_data(sport, game_data)
                if issues:
                    sport_report['games_with_issues'] += 1
                    report['issues'].extend([f"{sport}: {i}" for i in issues[:3]])

            report['sports'][sport] = sport_report

        return report


# Singleton instance
validator = DataValidator()


def validate_and_fill(sport: str, game_data: Dict) -> Dict:
    """Convenience function to validate and fill a game's data"""
    is_valid, sanitized, issues = validator.validate_game_data(sport, game_data)
    return sanitized


def format_stat(value: Any, stat_type: str = 'number', decimals: int = 1) -> str:
    """Convenience function to format a stat for display"""
    return validator.format_stat_for_display(value, stat_type, decimals)
