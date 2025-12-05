"""
INTELLIGENT GAME ANALYSIS GENERATOR
===================================
Creates unique, human-sounding analysis for each game with:
- Varied narrative styles and openings
- Real statistical context
- Conversational, analytical tone
- Contextual awareness of matchup significance
- Natural language that doesn't sound templated

Each analysis is unique based on the specific game context.
"""

import os
import sys
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Narrative building blocks for natural variation
OPENING_STYLES = {
    'direct': [
        "This one has all the makings of a classic.",
        "Circle this one on your calendar.",
        "Here's a matchup that deserves your attention.",
        "Don't sleep on this one.",
        "This game could be more interesting than the spread suggests.",
        "There's real value hiding in this line.",
        "The sharps have been all over this one.",
        "Let's break down what makes this matchup tick.",
    ],
    'contextual': [
        "Recent form matters a lot in this matchup.",
        "Both teams come into this with something to prove.",
        "Two teams heading in opposite directions meet tonight.",
        "The recent stretch has been telling for both squads.",
        "This game could serve as a measuring stick for both sides.",
    ],
    'analytical': [
        "The numbers tell an interesting story here.",
        "When you dig into the advanced metrics, this game looks different than the surface suggests.",
        "Sharp money has been moving this line, and there's a reason why.",
        "The market seems to be overreacting to recent results.",
        "There's a statistical mismatch here that the betting public hasn't caught onto yet.",
    ],
    'emotional': [
        "This is the kind of game that defines seasons.",
        "Desperation meets opportunity tonight.",
        "Someone's streak has to end here.",
        "Pride is on the line in this one.",
        "This feels like a statement game waiting to happen.",
    ],
}

# Trend descriptions for natural language
TREND_DESCRIPTORS = {
    'hot': ['rolling', 'on fire', 'clicking on all cylinders', 'playing their best ball', 'surging', 'locked in'],
    'cold': ['struggling', 'in a slump', 'searching for answers', 'trying to find their footing', 'reeling', 'ice cold'],
    'mixed': ['inconsistent', 'up and down', 'hard to read', 'unpredictable', 'showing flashes', 'a mixed bag'],
    'improving': ['trending up', 'starting to figure it out', 'building momentum', 'showing signs of life', 'turning the corner'],
    'declining': ['fading', 'losing steam', 'showing cracks', 'coming back to earth', 'regressing'],
}

# Statistical context phrases
STAT_PHRASES = {
    'offense_good': [
        "putting up {ppg} points per game",
        "averaging an impressive {ppg} PPG",
        "lighting up scoreboards at {ppg} per night",
        "one of the league's most potent offenses at {ppg} PPG",
    ],
    'offense_bad': [
        "struggling to score at just {ppg} PPG",
        "managing only {ppg} points per game",
        "one of the league's least efficient offenses at {ppg} PPG",
    ],
    'defense_good': [
        "holding opponents to just {oppg} PPG",
        "with a stingy defense allowing only {oppg} points",
        "defensively elite, surrendering just {oppg} per game",
    ],
    'defense_bad': [
        "giving up {oppg} points per game",
        "defensively porous at {oppg} PPG allowed",
        "struggling to get stops, allowing {oppg} nightly",
    ],
    'ats_good': [
        "covering at a {ats_pct}% clip",
        "{ats_record} against the spread",
        "one of the best ATS teams in the league at {ats_record}",
    ],
    'ats_bad': [
        "just {ats_record} ATS",
        "struggling to cover at {ats_pct}%",
        "a lean-against ATS at {ats_record}",
    ],
}

# Injury impact phrases
INJURY_PHRASES = {
    'major_out': [
        "The absence of {player} looms large here.",
        "Without {player}, this team looks fundamentally different.",
        "Missing {player} changes everything about how they play.",
        "The {player} injury is impossible to overlook.",
    ],
    'multiple_out': [
        "The injury report is brutal - {players} are all sidelined.",
        "They're dealing with significant absences: {players}.",
        "The health situation is dire with {players} out.",
    ],
    'questionable': [
        "{player}'s status is up in the air, which adds uncertainty.",
        "Keep an eye on {player}'s availability - it matters.",
        "If {player} sits, this line moves.",
    ],
    'healthy': [
        "Both teams come in relatively healthy, which is rare.",
        "No major injury concerns on either side.",
        "Health advantage goes to neither team here.",
    ],
}

# Betting angle phrases
BETTING_PHRASES = {
    'sharp_play': [
        "Sharp money has hammered the {side}.",
        "The wise guys are all over {side}.",
        "Professional bettors have moved this line toward {side}.",
        "Follow the smart money here - it's on {side}.",
    ],
    'public_fade': [
        "The public is pounding {side}, which historically is a fade.",
        "{pct}% of bets are on {side} - that's a contrarian signal.",
        "When the public is this one-sided ({pct}% on {side}), sharps take notice.",
    ],
    'line_movement': [
        "This line has moved from {open} to {current} - significant action.",
        "Watch the line movement: opened {open}, now sitting at {current}.",
        "The {direction} line move tells you where the money is going.",
    ],
    'value_spot': [
        "This feels like a value spot on {side}.",
        "The market might be undervaluing {team} here.",
        "There's an edge to be found on {side}.",
    ],
}


class IntelligentAnalysisGenerator:
    """Generates unique, human-sounding game analysis"""

    def __init__(self):
        self.used_openings = set()  # Track used openings to avoid repetition within a day

    def _get_team_trend(self, stats: Dict) -> str:
        """Determine team's current trend based on recent performance"""
        last10 = stats.get('last10', {})
        record = last10.get('record', '5-5')
        try:
            wins, losses = map(int, record.split('-'))
            win_pct = wins / (wins + losses) if (wins + losses) > 0 else 0.5
        except:
            win_pct = 0.5

        streak = stats.get('streak', '')
        # Ensure streak is a string (can be float/NaN from data)
        if not isinstance(streak, str):
            streak = ''

        if win_pct >= 0.7:
            return 'hot'
        elif win_pct <= 0.3:
            return 'cold'
        elif streak and 'W' in streak:
            try:
                streak_len = int(streak.replace('W', '').replace('L', '') or 0)
                if streak_len >= 3:
                    return 'improving'
            except:
                pass
        elif streak and 'L' in streak:
            try:
                streak_len = int(streak.replace('W', '').replace('L', '') or 0)
                if streak_len >= 3:
                    return 'declining'
            except:
                pass

        return 'mixed'

    def _get_random_phrase(self, category: str, subcategory: str, **kwargs) -> str:
        """Get a random phrase from a category with variable substitution"""
        phrases_dict = {
            'opening': OPENING_STYLES,
            'trend': TREND_DESCRIPTORS,
            'stat': STAT_PHRASES,
            'injury': INJURY_PHRASES,
            'betting': BETTING_PHRASES,
        }

        phrases = phrases_dict.get(category, {}).get(subcategory, [])
        if not phrases:
            return ""

        phrase = random.choice(phrases)

        # Substitute variables
        for key, value in kwargs.items():
            phrase = phrase.replace('{' + key + '}', str(value))

        return phrase

    def _generate_opening(self, sport: str, away_name: str, home_name: str,
                          away_stats: Dict, home_stats: Dict, context: Dict) -> str:
        """Generate a unique, contextual opening paragraph"""

        away_trend = self._get_team_trend(away_stats)
        home_trend = self._get_team_trend(home_stats)

        # Choose opening style based on game context
        if context.get('is_rivalry') or context.get('is_marquee'):
            style = 'emotional'
        elif context.get('sharp_action'):
            style = 'analytical'
        elif away_trend in ['hot', 'cold'] or home_trend in ['hot', 'cold']:
            style = 'contextual'
        else:
            style = random.choice(['direct', 'analytical', 'contextual'])

        openings = OPENING_STYLES.get(style, OPENING_STYLES['direct'])

        # Find an unused opening
        available = [o for o in openings if o not in self.used_openings]
        if not available:
            self.used_openings.clear()
            available = openings

        opening = random.choice(available)
        self.used_openings.add(opening)

        # Build the contextual opening
        away_trend_desc = random.choice(TREND_DESCRIPTORS.get(away_trend, ['playing']))
        home_trend_desc = random.choice(TREND_DESCRIPTORS.get(home_trend, ['playing']))

        away_record = away_stats.get('record', '')
        home_record = home_stats.get('record', '')

        paragraphs = [opening]

        # Add context about the matchup
        if away_trend == 'hot' and home_trend == 'cold':
            paragraphs.append(f"The {away_name} come in {away_trend_desc} while {home_name} have been {home_trend_desc}. That disparity in form is the headline here.")
        elif home_trend == 'hot' and away_trend == 'cold':
            paragraphs.append(f"Home cooking could be the difference as {home_name} have been {home_trend_desc}, facing a {away_name} team that's been {away_trend_desc} lately.")
        elif away_trend == 'hot' and home_trend == 'hot':
            paragraphs.append(f"Both teams enter this one {away_trend_desc}. When two hot teams collide, something has to give.")
        else:
            paragraphs.append(f"The {away_name} ({away_record}) visit {home_name} ({home_record}) in what shapes up to be a {random.choice(['competitive', 'intriguing', 'telling', 'fascinating'])} matchup.")

        return ' '.join(paragraphs)

    def _generate_stats_analysis(self, sport: str, away_name: str, home_name: str,
                                  away_stats: Dict, home_stats: Dict,
                                  away_abbrev: str, home_abbrev: str) -> str:
        """Generate statistical analysis with natural language"""

        paragraphs = []

        # Get key stats
        away_ppg = away_stats.get('ppg', 0)
        home_ppg = home_stats.get('ppg', 0)
        away_oppg = away_stats.get('oppg', 0)
        home_oppg = home_stats.get('oppg', 0)

        # Offensive comparison
        if away_ppg and home_ppg:
            if float(away_ppg) > float(home_ppg) + 5:
                para = f"{away_name} bring the firepower, {self._get_random_phrase('stat', 'offense_good', ppg=away_ppg)}. "
                para += f"Meanwhile, {home_name} have been more modest offensively at {home_ppg} PPG."
            elif float(home_ppg) > float(away_ppg) + 5:
                para = f"{home_name} have the offensive edge, {self._get_random_phrase('stat', 'offense_good', ppg=home_ppg)}. "
                para += f"{away_name} have been scoring {away_ppg} per game."
            else:
                para = f"Offensively, these teams are evenly matched - {away_name} at {away_ppg} PPG vs {home_name}'s {home_ppg}."
            paragraphs.append(para)

        # Defensive comparison
        if away_oppg and home_oppg:
            if float(away_oppg) < float(home_oppg) - 3:
                para = f"Defensively, {away_name} have the clear advantage, {self._get_random_phrase('stat', 'defense_good', oppg=away_oppg)}. "
                para += f"{home_name} have been more vulnerable, allowing {home_oppg}."
            elif float(home_oppg) < float(away_oppg) - 3:
                para = f"{home_name}'s defense has been the story, {self._get_random_phrase('stat', 'defense_good', oppg=home_oppg)}."
            else:
                para = f"Both defenses have been comparable - {away_name} allowing {away_oppg}, {home_name} at {home_oppg}."
            paragraphs.append(para)

        # Pace/style analysis for NBA/NCAAB
        if sport in ['NBA', 'NCAAB']:
            away_pace = away_stats.get('pace', 0)
            home_pace = home_stats.get('pace', 0)
            if away_pace and home_pace:
                if float(away_pace) > 100 and float(home_pace) > 100:
                    paragraphs.append("Both teams like to push the pace, so expect an up-tempo affair with plenty of possessions.")
                elif float(away_pace) < 98 and float(home_pace) < 98:
                    paragraphs.append("This projects as a grind-it-out, half-court battle. Don't expect a track meet.")

        return '\n\n'.join(paragraphs)

    def _generate_injury_analysis(self, away_injuries: List, home_injuries: List,
                                   away_name: str, home_name: str,
                                   away_abbrev: str, home_abbrev: str) -> str:
        """Generate injury impact analysis"""

        if not away_injuries and not home_injuries:
            return self._get_random_phrase('injury', 'healthy')

        paragraphs = []

        # Away team injuries
        away_out = [i for i in away_injuries if 'out' in i.get('status', '').lower()]
        away_quest = [i for i in away_injuries if 'questionable' in i.get('status', '').lower()]

        if away_out:
            if len(away_out) >= 3:
                players = ', '.join([i.get('name', '') for i in away_out[:3]])
                paragraphs.append(f"{away_name} are decimated by injuries. {self._get_random_phrase('injury', 'multiple_out', players=players)}")
            else:
                player = away_out[0].get('name', 'a key player')
                paragraphs.append(f"For {away_name}: {self._get_random_phrase('injury', 'major_out', player=player)}")

        if away_quest and len(away_out) < 2:
            player = away_quest[0].get('name', 'a starter')
            paragraphs.append(self._get_random_phrase('injury', 'questionable', player=player))

        # Home team injuries
        home_out = [i for i in home_injuries if 'out' in i.get('status', '').lower()]
        home_quest = [i for i in home_injuries if 'questionable' in i.get('status', '').lower()]

        if home_out:
            if len(home_out) >= 3:
                players = ', '.join([i.get('name', '') for i in home_out[:3]])
                paragraphs.append(f"{home_name}'s injury situation is equally concerning. {self._get_random_phrase('injury', 'multiple_out', players=players)}")
            else:
                player = home_out[0].get('name', 'a key player')
                paragraphs.append(f"On the {home_name} side: {self._get_random_phrase('injury', 'major_out', player=player)}")

        return '\n\n'.join(paragraphs) if paragraphs else ""

    def _generate_betting_analysis(self, odds: Dict, away_ats: Dict, home_ats: Dict,
                                    public_betting: Dict, sharp_money: Dict,
                                    away_name: str, home_name: str,
                                    away_abbrev: str, home_abbrev: str) -> str:
        """Generate betting trends analysis"""

        paragraphs = []

        spread = odds.get('spread', 'N/A')
        total = odds.get('total', 'N/A')

        # ATS records
        away_ats_rec = away_ats.get('ats_overall', '')
        home_ats_rec = home_ats.get('ats_overall', '')

        if away_ats_rec and home_ats_rec:
            para = f"Against the spread, {away_name} are {away_ats_rec} while {home_name} sit at {home_ats_rec}. "

            # Identify if there's an edge
            try:
                away_wins = int(away_ats_rec.split('-')[0])
                away_losses = int(away_ats_rec.split('-')[1])
                home_wins = int(home_ats_rec.split('-')[0])
                home_losses = int(home_ats_rec.split('-')[1])

                away_pct = away_wins / (away_wins + away_losses) if (away_wins + away_losses) > 0 else 0.5
                home_pct = home_wins / (home_wins + home_losses) if (home_wins + home_losses) > 0 else 0.5

                if away_pct > 0.55 and home_pct < 0.45:
                    para += f"That's a notable edge for {away_name} as a covering team."
                elif home_pct > 0.55 and away_pct < 0.45:
                    para += f"The home side has been money against the number."
            except:
                pass

            paragraphs.append(para)

        # Public betting
        if public_betting:
            spread_pct = public_betting.get('spread_pct', {})
            if spread_pct:
                away_pct = spread_pct.get('away', 50)
                home_pct = spread_pct.get('home', 50)
                if away_pct > 65:
                    paragraphs.append(self._get_random_phrase('betting', 'public_fade', side=away_name, pct=away_pct))
                elif home_pct > 65:
                    paragraphs.append(self._get_random_phrase('betting', 'public_fade', side=home_name, pct=home_pct))

        # Sharp money
        if sharp_money and sharp_money.get('sharp_side'):
            side = sharp_money.get('sharp_side')
            team = away_name if 'away' in side.lower() else home_name
            paragraphs.append(self._get_random_phrase('betting', 'sharp_play', side=team))

        # Line info
        if spread != 'N/A' and total != 'N/A':
            paragraphs.append(f"Current line: {spread} with a total of {total}.")

        return '\n\n'.join(paragraphs)

    def _generate_prediction_angle(self, sport: str, away_name: str, home_name: str,
                                    away_stats: Dict, home_stats: Dict,
                                    odds: Dict, context: Dict) -> str:
        """Generate a prediction angle/lean without explicit picks"""

        angles = []

        away_trend = self._get_team_trend(away_stats)
        home_trend = self._get_team_trend(home_stats)

        # Trend-based angle
        if away_trend == 'hot' and home_trend == 'cold':
            angles.append(f"Momentum clearly favors {away_name}, and that tends to matter on the road.")
        elif home_trend == 'hot' and away_trend == 'cold':
            angles.append(f"Home court plus hot play is a powerful combination for {home_name}.")

        # Statistical angle
        away_ppg = float(away_stats.get('ppg', 100) or 100)
        home_oppg = float(home_stats.get('oppg', 100) or 100)
        home_ppg = float(home_stats.get('ppg', 100) or 100)
        away_oppg = float(away_stats.get('oppg', 100) or 100)

        away_proj = (away_ppg + home_oppg) / 2
        home_proj = (home_ppg + away_oppg) / 2

        total = odds.get('total', 0)
        if total and total != 'N/A':
            try:
                total_num = float(str(total).replace('o', '').replace('u', ''))
                proj_total = away_proj + home_proj
                if proj_total > total_num + 5:
                    angles.append(f"The total feels low based on how these offenses have been playing.")
                elif proj_total < total_num - 5:
                    angles.append(f"This total might be inflated given recent defensive performances.")
            except:
                pass

        # Add analytical closer
        closers = [
            "Do your own research, but there's something here worth exploring.",
            "The value might not be where the public thinks.",
            "Sharp bettors are paying attention to this one for a reason.",
            "This game has trap written all over it - proceed carefully.",
            "Sometimes the obvious play is the right one. Sometimes it isn't.",
        ]
        angles.append(random.choice(closers))

        return ' '.join(angles)

    def generate_analysis(self, sport: str, game_data: Dict, advanced_data: Dict = None) -> str:
        """Generate complete, unique analysis for a game"""

        game = game_data.get('game', {})
        away = game.get('away', {})
        home = game.get('home', {})

        away_name = away.get('displayName', away.get('name', 'Away Team'))
        home_name = home.get('displayName', home.get('name', 'Home Team'))
        away_abbrev = away.get('abbreviation', 'AWY')
        home_abbrev = home.get('abbreviation', 'HME')

        away_stats = game_data.get('away_stats', {})
        home_stats = game_data.get('home_stats', {})

        # Ensure record is available in stats (fallback to game object)
        if 'record' not in away_stats or not away_stats['record']:
            away_stats['record'] = away.get('record', '')
        if 'record' not in home_stats or not home_stats['record']:
            home_stats['record'] = home.get('record', '')

        odds = game_data.get('odds', {})
        away_injuries = game_data.get('away_injuries', [])
        home_injuries = game_data.get('home_injuries', [])
        away_ats = game_data.get('away_ats', {})
        home_ats = game_data.get('home_ats', {})
        public_betting = game_data.get('public_betting', {})
        sharp_money = game_data.get('sharp_money', {})

        # Build context
        context = {
            'is_rivalry': False,  # Could detect based on team matchups
            'is_marquee': any(t in away_name + home_name for t in ['Lakers', 'Celtics', 'Warriors', 'Cowboys', 'Chiefs']),
            'sharp_action': bool(sharp_money and sharp_money.get('sharp_side')),
        }

        # Generate each section
        sections = []

        # Opening
        opening = self._generate_opening(sport, away_name, home_name, away_stats, home_stats, context)
        if opening:
            sections.append(f'<div class="analysis-section"><h4>The Matchup</h4><p>{opening}</p></div>')

        # Stats Analysis
        stats_analysis = self._generate_stats_analysis(sport, away_name, home_name, away_stats, home_stats, away_abbrev, home_abbrev)
        if stats_analysis:
            sections.append(f'<div class="analysis-section"><h4>By The Numbers</h4><p>{stats_analysis}</p></div>')

        # Injury Analysis
        injury_analysis = self._generate_injury_analysis(away_injuries, home_injuries, away_name, home_name, away_abbrev, home_abbrev)
        if injury_analysis:
            sections.append(f'<div class="analysis-section"><h4>Health Report</h4><p>{injury_analysis}</p></div>')

        # Betting Analysis
        betting_analysis = self._generate_betting_analysis(odds, away_ats, home_ats, public_betting, sharp_money, away_name, home_name, away_abbrev, home_abbrev)
        if betting_analysis:
            sections.append(f'<div class="analysis-section"><h4>Betting Trends</h4><p>{betting_analysis}</p></div>')

        # Prediction Angle
        prediction = self._generate_prediction_angle(sport, away_name, home_name, away_stats, home_stats, odds, context)
        if prediction:
            sections.append(f'<div class="analysis-section"><h4>The Angle</h4><p>{prediction}</p></div>')

        return '\n'.join(sections)


# Create singleton instance
_generator = IntelligentAnalysisGenerator()


def generate_game_analysis(sport: str, game_data: Dict, advanced_data: Dict = None) -> str:
    """Convenience function to generate analysis"""
    return _generator.generate_analysis(sport, game_data, advanced_data)


# Alias for compatibility
class GameAnalysisGenerator(IntelligentAnalysisGenerator):
    pass
