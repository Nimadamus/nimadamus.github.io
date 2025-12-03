"""
HISTORICAL PERFORMANCE TRACKER
==============================
Track Killport Model predictions and actual results.
Build a database of model performance for credibility.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import csv

from .cache import cache


class HistoricalTracker:
    """
    Track model predictions vs actual results.
    Maintains records for:
    - Daily predictions
    - Actual outcomes
    - Win/Loss records by sport
    - ROI calculations
    - Streak tracking
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), 'history')
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.predictions_file = os.path.join(data_dir, 'predictions.json')
        self.results_file = os.path.join(data_dir, 'results.json')
        self.summary_file = os.path.join(data_dir, 'summary.json')

    def save_prediction(self, prediction: Dict):
        """
        Save a Killport Model prediction for later verification.

        Args:
            prediction: Full prediction dict from Killport Model
        """
        predictions = self._load_json(self.predictions_file, default=[])

        # Add metadata
        prediction['saved_at'] = datetime.now().isoformat()
        prediction['verified'] = False

        predictions.append(prediction)

        # Keep last 1000 predictions
        predictions = predictions[-1000:]

        self._save_json(self.predictions_file, predictions)

    def record_result(self, game_id: str, sport: str, result: Dict):
        """
        Record actual game result for verification.

        Args:
            game_id: Unique game identifier
            sport: Sport code
            result: {
                'winner': str,
                'home_score': int,
                'away_score': int,
                'spread_result': 'home' | 'away' | 'push',
                'total_result': 'over' | 'under' | 'push',
                'final_spread': float,
                'final_total': float,
            }
        """
        results = self._load_json(self.results_file, default={})

        key = f"{sport}_{game_id}"
        results[key] = {
            **result,
            'recorded_at': datetime.now().isoformat(),
        }

        self._save_json(self.results_file, results)

        # Verify pending predictions
        self._verify_predictions(sport, game_id, result)

    def _verify_predictions(self, sport: str, game_id: str, result: Dict):
        """Verify predictions against actual results"""
        predictions = self._load_json(self.predictions_file, default=[])

        for pred in predictions:
            if pred.get('verified'):
                continue

            # Match by sport and approximate game
            if pred.get('sport') != sport:
                continue

            # Check if this prediction matches the result
            matchup = pred.get('matchup', '')
            if game_id in matchup or self._fuzzy_match_game(pred, result):
                pred['verified'] = True
                pred['actual_result'] = result
                pred['correct'] = self._evaluate_prediction(pred, result)

        self._save_json(self.predictions_file, predictions)
        self._update_summary()

    def _fuzzy_match_game(self, prediction: Dict, result: Dict) -> bool:
        """Try to match prediction to result"""
        # Would implement fuzzy matching logic here
        return False

    def _evaluate_prediction(self, prediction: Dict, result: Dict) -> Dict:
        """
        Evaluate if prediction was correct.

        Returns:
            {
                'winner_correct': bool,
                'spread_correct': bool,
                'units_won': float,
            }
        """
        evaluation = {
            'winner_correct': False,
            'spread_correct': False,
            'units_won': 0,
        }

        pred_winner = prediction.get('predicted_winner', '')
        actual_winner = result.get('winner', '')

        if pred_winner and actual_winner:
            evaluation['winner_correct'] = pred_winner.lower() in actual_winner.lower()

        recommendation = prediction.get('recommendation', {})
        if recommendation.get('play') == 'SPREAD':
            spread_result = result.get('spread_result')
            pred_side = recommendation.get('side', '').lower()

            if spread_result == 'push':
                evaluation['spread_correct'] = None
                evaluation['units_won'] = 0
            elif spread_result and pred_side:
                # Check if prediction side matches spread result
                evaluation['spread_correct'] = pred_side in spread_result
                evaluation['units_won'] = 1.0 if evaluation['spread_correct'] else -1.1

        return evaluation

    def _update_summary(self):
        """Update overall performance summary"""
        predictions = self._load_json(self.predictions_file, default=[])

        summary = {
            'last_updated': datetime.now().isoformat(),
            'total_predictions': len(predictions),
            'verified_predictions': 0,
            'by_sport': {},
            'by_confidence': {},
            'by_strength': {},
            'recent_record': {'wins': 0, 'losses': 0, 'pushes': 0},
            'roi': 0,
            'streak': {'type': None, 'count': 0},
        }

        units_won = 0
        total_bets = 0
        recent_results = []

        for pred in predictions:
            if not pred.get('verified'):
                continue

            summary['verified_predictions'] += 1
            sport = pred.get('sport', 'Unknown')
            confidence = pred.get('confidence', 0)
            strength = pred.get('recommendation', {}).get('strength', 'LEAN')

            # Initialize sport stats
            if sport not in summary['by_sport']:
                summary['by_sport'][sport] = {'wins': 0, 'losses': 0, 'pushes': 0, 'units': 0}

            # Initialize confidence stats
            conf_key = str(confidence)
            if conf_key not in summary['by_confidence']:
                summary['by_confidence'][conf_key] = {'wins': 0, 'losses': 0, 'units': 0}

            # Initialize strength stats
            if strength not in summary['by_strength']:
                summary['by_strength'][strength] = {'wins': 0, 'losses': 0, 'units': 0}

            # Count results
            correct = pred.get('correct', {})
            spread_correct = correct.get('spread_correct')
            units = correct.get('units_won', 0)

            if spread_correct is True:
                summary['by_sport'][sport]['wins'] += 1
                summary['by_confidence'][conf_key]['wins'] += 1
                summary['by_strength'][strength]['wins'] += 1
                recent_results.append('W')
            elif spread_correct is False:
                summary['by_sport'][sport]['losses'] += 1
                summary['by_confidence'][conf_key]['losses'] += 1
                summary['by_strength'][strength]['losses'] += 1
                recent_results.append('L')
            else:
                summary['by_sport'][sport]['pushes'] += 1
                recent_results.append('P')

            summary['by_sport'][sport]['units'] += units
            summary['by_confidence'][conf_key]['units'] += units
            summary['by_strength'][strength]['units'] += units
            units_won += units
            total_bets += 1 if spread_correct is not None else 0

        # Calculate recent record (last 20)
        recent_results = recent_results[-20:]
        summary['recent_record']['wins'] = recent_results.count('W')
        summary['recent_record']['losses'] = recent_results.count('L')
        summary['recent_record']['pushes'] = recent_results.count('P')

        # Calculate ROI
        if total_bets > 0:
            summary['roi'] = round((units_won / total_bets) * 100, 1)

        # Calculate current streak
        if recent_results:
            current = recent_results[-1]
            count = 1
            for r in reversed(recent_results[:-1]):
                if r == current:
                    count += 1
                else:
                    break
            summary['streak'] = {'type': current, 'count': count}

        self._save_json(self.summary_file, summary)

    def get_summary(self) -> Dict:
        """Get current performance summary"""
        return self._load_json(self.summary_file, default={
            'total_predictions': 0,
            'verified_predictions': 0,
            'by_sport': {},
            'roi': 0,
            'streak': {'type': None, 'count': 0},
        })

    def get_recent_predictions(self, limit: int = 20) -> List[Dict]:
        """Get most recent predictions"""
        predictions = self._load_json(self.predictions_file, default=[])
        return predictions[-limit:]

    def generate_record_html(self) -> str:
        """Generate HTML showing model record"""
        summary = self.get_summary()

        if not summary.get('verified_predictions'):
            return '''
            <div class="model-record">
                <div class="record-title">KILLPORT MODEL RECORD</div>
                <div class="record-content">
                    <p>Tracking begins today. Check back for verified results!</p>
                </div>
            </div>
            '''

        by_sport_html = ''
        for sport, stats in summary.get('by_sport', {}).items():
            w, l, p = stats['wins'], stats['losses'], stats['pushes']
            total = w + l
            win_pct = round((w / total) * 100, 1) if total > 0 else 0
            units = stats['units']
            units_class = 'positive' if units > 0 else 'negative' if units < 0 else ''

            by_sport_html += f'''
            <div class="sport-record">
                <span class="sport-name">{sport}</span>
                <span class="record">{w}-{l}{f'-{p}' if p else ''}</span>
                <span class="win-pct">{win_pct}%</span>
                <span class="units {units_class}">{units:+.1f}u</span>
            </div>
            '''

        streak = summary.get('streak', {})
        streak_html = ''
        if streak.get('type') and streak.get('count', 0) >= 2:
            streak_type = 'win-streak' if streak['type'] == 'W' else 'loss-streak'
            streak_html = f'<span class="streak {streak_type}">{streak["count"]} {streak["type"]} STREAK</span>'

        return f'''
        <div class="model-record">
            <div class="record-header">
                <span class="record-title">KILLPORT MODEL RECORD</span>
                {streak_html}
            </div>
            <div class="record-stats">
                <div class="stat-box">
                    <span class="label">TOTAL</span>
                    <span class="value">{summary.get('verified_predictions', 0)} picks</span>
                </div>
                <div class="stat-box">
                    <span class="label">ROI</span>
                    <span class="value {'positive' if summary.get('roi', 0) > 0 else 'negative'}">{summary.get('roi', 0):+.1f}%</span>
                </div>
            </div>
            <div class="by-sport">
                {by_sport_html}
            </div>
        </div>
        '''

    def _load_json(self, filepath: str, default=None):
        """Load JSON file safely"""
        if not os.path.exists(filepath):
            return default if default is not None else {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default if default is not None else {}

    def _save_json(self, filepath: str, data):
        """Save data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving {filepath}: {e}")


# Global tracker instance
tracker = HistoricalTracker()
