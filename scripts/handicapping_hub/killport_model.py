"""
KILLPORT PREDICTION MODEL
=========================
BetLegend's proprietary handicapping model that generates
composite scores for each matchup.

Model Components:
- Efficiency ratings (offensive/defensive)
- Recent form analysis
- Home/away adjustments
- Rest advantage
- Injury impact
- Historical trends

Output:
- Predicted winner
- Confidence level (1-5 stars)
- Edge rating (-10 to +10)
- Model pick (spread/ML/total recommendation)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime


class KillportModel:
    """
    The Killport Model - BetLegend's proprietary prediction system.

    Generates a composite score based on:
    1. Team efficiency (40%)
    2. Recent form (25%)
    3. Situational factors (20%)
    4. Line value (15%)
    """

    # Weight factors for different components
    WEIGHTS = {
        'efficiency': 0.40,
        'recent_form': 0.25,
        'situational': 0.20,
        'line_value': 0.15,
    }

    # Home court/field/ice advantage by sport
    HOME_ADVANTAGE = {
        'NBA': 2.5,
        'NHL': 0.25,
        'NFL': 2.5,
        'MLB': 0.3,  # Runs
        'NCAAB': 3.5,
        'NCAAF': 3.0,
    }

    def __init__(self, sport: str):
        self.sport = sport
        self.home_adv = self.HOME_ADVANTAGE.get(sport, 2.0)

    def generate_prediction(self, game_data: Dict) -> Dict:
        """
        Generate Killport Model prediction for a matchup.

        Args:
            game_data: Complete game data including stats, injuries, odds

        Returns:
            Dict with prediction details
        """
        game = game_data.get('game', {})
        away = game.get('away', {})
        home = game.get('home', {})

        # Calculate component scores
        efficiency_edge = self._calculate_efficiency_edge(game_data)
        form_edge = self._calculate_form_edge(game_data)
        situational_edge = self._calculate_situational_edge(game_data)

        # Combine edges
        raw_edge = (
            efficiency_edge * self.WEIGHTS['efficiency'] +
            form_edge * self.WEIGHTS['recent_form'] +
            situational_edge * self.WEIGHTS['situational']
        )

        # Add home advantage (positive = home team favored)
        adjusted_edge = raw_edge + self.home_adv

        # Determine prediction
        predicted_winner = home['name'] if adjusted_edge > 0 else away['name']
        predicted_loser = away['name'] if adjusted_edge > 0 else home['name']
        edge_magnitude = abs(adjusted_edge)

        # Calculate confidence (1-5 stars)
        confidence = self._calculate_confidence(edge_magnitude, game_data)

        # Generate model line (predicted spread from home perspective)
        model_line = -adjusted_edge  # Negative = home favored

        # Compare to market line if available
        odds = game_data.get('odds', {})
        market_spread = odds.get('spread_home')
        line_value = self._calculate_line_value(model_line, market_spread) if market_spread else None

        # Generate recommendation
        recommendation = self._generate_recommendation(
            adjusted_edge, model_line, market_spread, odds, home, away
        )

        return {
            'model_name': 'KILLPORT',
            'sport': self.sport,
            'matchup': f"{away['name']} @ {home['name']}",
            'predicted_winner': predicted_winner,
            'predicted_margin': round(edge_magnitude, 1),
            'model_line': round(model_line, 1),
            'confidence': confidence,
            'confidence_stars': '★' * confidence + '☆' * (5 - confidence),
            'edge_rating': round(adjusted_edge, 1),
            'components': {
                'efficiency_edge': round(efficiency_edge, 1),
                'form_edge': round(form_edge, 1),
                'situational_edge': round(situational_edge, 1),
                'home_advantage': round(self.home_adv, 1),
            },
            'line_value': round(line_value, 1) if line_value else None,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
        }

    def _calculate_efficiency_edge(self, game_data: Dict) -> float:
        """
        Calculate edge based on team efficiency ratings.
        Returns positive value if away team is better.
        """
        away_adv = game_data.get('away_advanced', {})
        home_adv = game_data.get('home_advanced', {})

        if self.sport in ['NBA', 'NCAAB']:
            # Use net rating
            away_net = self._safe_float(away_adv.get('net_rating', 0))
            home_net = self._safe_float(home_adv.get('net_rating', 0))
            return away_net - home_net

        elif self.sport == 'NHL':
            # Use goal differential per game
            away_diff = self._safe_float(away_adv.get('goal_diff_per_game', 0))
            home_diff = self._safe_float(home_adv.get('goal_diff_per_game', 0))
            return (away_diff - home_diff) * 2  # Scale to points

        elif self.sport in ['NFL', 'NCAAF']:
            # Use point differential + EPA
            away_diff = self._safe_float(away_adv.get('point_diff', 0))
            home_diff = self._safe_float(home_adv.get('point_diff', 0))
            away_epa = self._safe_float(away_adv.get('epa_per_play', 0)) * 10
            home_epa = self._safe_float(home_adv.get('epa_per_play', 0)) * 10
            return (away_diff - home_diff) / 2 + (away_epa - home_epa)

        elif self.sport == 'MLB':
            # Use run differential
            away_rs = self._safe_float(away_adv.get('runs_per_game', 4.5))
            home_rs = self._safe_float(home_adv.get('runs_per_game', 4.5))
            away_ra = self._safe_float(away_adv.get('runs_against_per_game', 4.5))
            home_ra = self._safe_float(home_adv.get('runs_against_per_game', 4.5))
            away_diff = away_rs - away_ra
            home_diff = home_rs - home_ra
            return away_diff - home_diff

        return 0

    def _calculate_form_edge(self, game_data: Dict) -> float:
        """
        Calculate edge based on recent form.
        """
        away_last = game_data.get('away_last10', game_data.get('away_last5', []))
        home_last = game_data.get('home_last10', game_data.get('home_last5', []))

        def calculate_form_score(games: List) -> float:
            if not games:
                return 0

            wins = sum(1 for g in games if g.get('result') == 'W')
            total = len(games)
            win_pct = wins / max(total, 1)

            # Weight recent games more
            weighted_wins = 0
            for i, g in enumerate(games):  # Most recent first
                weight = 1.5 - (i * 0.1)  # 1.5, 1.4, 1.3, etc.
                if g.get('result') == 'W':
                    weighted_wins += weight

            max_weighted = sum(1.5 - (i * 0.1) for i in range(len(games)))
            weighted_pct = weighted_wins / max(max_weighted, 1)

            # Convert to point scale
            return (weighted_pct - 0.5) * 6  # -3 to +3 range

        away_form = calculate_form_score(away_last)
        home_form = calculate_form_score(home_last)

        return away_form - home_form

    def _calculate_situational_edge(self, game_data: Dict) -> float:
        """
        Calculate edge based on situational factors.
        """
        edge = 0

        # Injury impact
        away_injuries = game_data.get('away_injuries', [])
        home_injuries = game_data.get('home_injuries', [])

        away_impact = self._assess_injury_impact(away_injuries)
        home_impact = self._assess_injury_impact(home_injuries)
        edge += (home_impact - away_impact)  # More injuries = negative

        # Weather impact (outdoor sports)
        weather = game_data.get('weather', {})
        if not weather.get('is_dome', True) and self.sport in ['NFL', 'NCAAF', 'MLB']:
            wind = weather.get('wind_speed', 0)
            temp = weather.get('temperature', 70)

            # Extreme cold affects passing games
            if temp < 35 and self.sport in ['NFL', 'NCAAF']:
                edge += 0.5  # Slight home advantage in cold

            # High wind affects kicking/passing
            if wind > 20:
                edge += 0.5  # Home team more comfortable

        # Rest advantage (would need schedule data)
        # Placeholder for now

        return edge

    def _assess_injury_impact(self, injuries: List) -> float:
        """
        Assess impact of injuries on team performance.
        Returns negative value (more injuries = worse).
        """
        if not injuries:
            return 0

        impact = 0
        for inj in injuries:
            status = inj.get('status', '').lower()
            position = inj.get('position', '').upper()

            # Weight by status
            if 'out' in status:
                base_impact = -1.0
            elif 'doubtful' in status:
                base_impact = -0.7
            elif 'questionable' in status:
                base_impact = -0.3
            else:
                base_impact = -0.1

            # Weight by position importance
            key_positions = {
                # NBA
                'PG': 1.2, 'SG': 1.0, 'SF': 1.0, 'PF': 1.0, 'C': 1.1,
                # NHL
                'G': 1.5, 'D': 0.8, 'LW': 0.7, 'RW': 0.7, 'C': 0.9,
                # NFL
                'QB': 2.0, 'RB': 0.8, 'WR': 0.7, 'TE': 0.6, 'OL': 0.5,
                'DL': 0.5, 'LB': 0.6, 'CB': 0.7, 'S': 0.6,
                # MLB
                'SP': 1.5, 'RP': 0.5, 'CP': 0.8,
            }

            pos_weight = key_positions.get(position, 0.5)
            impact += base_impact * pos_weight

        return impact

    def _calculate_confidence(self, edge_magnitude: float, game_data: Dict) -> int:
        """
        Calculate confidence level (1-5 stars).
        """
        # Base confidence on edge magnitude
        if edge_magnitude >= 8:
            base_conf = 5
        elif edge_magnitude >= 6:
            base_conf = 4
        elif edge_magnitude >= 4:
            base_conf = 3
        elif edge_magnitude >= 2:
            base_conf = 2
        else:
            base_conf = 1

        # Adjust for data quality
        has_advanced = bool(game_data.get('away_advanced')) and bool(game_data.get('home_advanced'))
        has_injuries = 'away_injuries' in game_data or 'home_injuries' in game_data

        if not has_advanced:
            base_conf = max(1, base_conf - 1)

        return min(5, max(1, base_conf))

    def _calculate_line_value(self, model_line: float, market_spread: float) -> float:
        """
        Calculate line value (difference between model and market).
        Positive = value on home team, Negative = value on away team.
        """
        return model_line - market_spread

    def _generate_recommendation(self, edge: float, model_line: float,
                                  market_spread: Optional[float], odds: Dict,
                                  home: Dict, away: Dict) -> Dict:
        """
        Generate betting recommendation based on model output.
        """
        recommendation = {
            'play': None,
            'side': None,
            'reasoning': '',
            'strength': 'LEAN',
        }

        if market_spread is not None:
            line_diff = model_line - market_spread

            if abs(line_diff) >= 3:
                recommendation['strength'] = 'STRONG'
            elif abs(line_diff) >= 1.5:
                recommendation['strength'] = 'MODERATE'
            else:
                recommendation['strength'] = 'LEAN'

            if line_diff <= -2:  # Value on away team
                recommendation['play'] = 'SPREAD'
                recommendation['side'] = away['abbreviation']
                recommendation['reasoning'] = f"Model sees {abs(round(line_diff, 1))} points of value on {away['abbreviation']}"
            elif line_diff >= 2:  # Value on home team
                recommendation['play'] = 'SPREAD'
                recommendation['side'] = home['abbreviation']
                recommendation['reasoning'] = f"Model sees {round(line_diff, 1)} points of value on {home['abbreviation']}"
            else:
                recommendation['play'] = 'PASS'
                recommendation['reasoning'] = 'No significant line value detected'

        else:
            # No market line available
            if abs(edge) >= 5:
                winner = home if edge > 0 else away
                recommendation['play'] = 'ML'
                recommendation['side'] = winner['abbreviation']
                recommendation['reasoning'] = f"Strong edge for {winner['abbreviation']}"
            else:
                recommendation['play'] = 'PASS'
                recommendation['reasoning'] = 'Edge not strong enough without line comparison'

        return recommendation

    def _safe_float(self, value, default=0) -> float:
        """Safely convert value to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.replace('%', '').replace('+', ''))
            except:
                return default
        return default


def generate_all_predictions(all_sports_data: Dict) -> Dict:
    """
    Generate Killport predictions for all sports.

    Args:
        all_sports_data: Dict of sport -> game data

    Returns:
        Dict of sport -> predictions
    """
    all_predictions = {}

    for sport, sport_data in all_sports_data.items():
        model = KillportModel(sport)
        predictions = []

        for game_data in sport_data.get('games', []):
            try:
                prediction = model.generate_prediction(game_data)
                predictions.append(prediction)
            except Exception as e:
                print(f"  Error generating prediction for {sport}: {e}")
                continue

        all_predictions[sport] = predictions

    return all_predictions
