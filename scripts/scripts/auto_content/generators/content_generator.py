"""
Content Generator using Claude API
Generates ORIGINAL, VARIED sports articles - not cookie-cutter garbage
"""

import os
import json
import random
from datetime import datetime
from typing import Dict, List, Optional
import anthropic

# Import config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, ARTICLE_STYLE


class ContentGenerator:
    """Generates sports content using Claude API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Set it as environment variable or pass to constructor.")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = CLAUDE_MODEL

    def generate_game_article(self, game_data: Dict, sport: str) -> str:
        """Generate an ORIGINAL article - different angle every time."""

        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        # Compact game data
        game_info = f"""
{away.get('name')} ({away.get('record', '?')}) @ {home.get('name')} ({home.get('record', '?')})
Away L10: {away.get('l10', '?')} | Home L10: {home.get('l10', '?')}
Away Win%: {away.get('win_pct', 0):.0f}% | Home Win%: {home.get('win_pct', 0):.0f}%
Line: {odds.get('spread', 'N/A')} | Total: {odds.get('total', 'N/A')}
Venue: {game_data.get('venue', '?')}"""

        # Sport-specific data
        if sport.lower() == 'nhl':
            game_info += f"\nStandings Points - {home.get('name')}: {home.get('points', '?')} | {away.get('name')}: {away.get('points', '?')}"
        elif sport.lower() == 'soccer':
            game_info += f"\nLeague: {game_data.get('league', '?')} | Matchweek: {game_data.get('match_week', '?')}"

        # Pick a random angle - this is what makes each article DIFFERENT
        angles = [
            ("TRAP GAME ALERT", "Look for the trap. Why might the favorite stumble here? Or is the dog getting too much love?"),
            ("FOLLOW THE MONEY", "Sharps vs squares. Where's the smart money going and why?"),
            ("SCHEDULING SPOT", "Rest, travel, motivation - what situational factors matter most here?"),
            ("KEY NUMBER ANALYSIS", "Is this line sitting on a key number? What's the vig telling us?"),
            ("REVENGE NARRATIVE", "Any bad blood? Recent embarrassments? Teams with something to prove?"),
            ("PACE & STYLE CLASH", "How do these teams' styles match up? Fast vs slow, offense vs defense?"),
            ("HOME COOKING", "How much does home court/ice/field actually matter in this specific matchup?"),
            ("FORM CHECK", "Forget the season record - what have these teams done in the last 2 weeks?"),
            ("OVERREACTION TEST", "Is the market overreacting to recent results? Time to fade the public?"),
            ("TOTAL BREAKDOWN", "Forget the side - is the total the real play here?"),
        ]

        angle_name, angle_focus = random.choice(angles)

        # Pick a random voice/style
        voices = [
            "You're a crusty old Vegas handicapper who's seen it all. Cynical but sharp.",
            "You're a young analytics guy who sees patterns others miss. Data-driven but not boring.",
            "You're a former player who understands the game from inside. Real talk, no BS.",
            "You're a contrarian who loves fading public opinion. Always looking for the other side.",
            "You're a situational bettor who cares more about context than talent. Schedule, rest, motivation.",
        ]

        voice = random.choice(voices)

        # Pick opening style
        openers = [
            "Start with your strongest opinion about this game",
            "Start with what everyone else is getting wrong",
            "Start with the one stat that actually matters here",
            "Start with a rhetorical question that frames your take",
            "Start by calling out the line - is it right or not?",
            "Start with what you'd tell a friend who asked about this game",
        ]

        opener = random.choice(openers)

        prompt = f"""VOICE: {voice}

ANGLE: {angle_name}
{angle_focus}

GAME DATA:
{game_info}

INSTRUCTIONS:
- {opener}
- 120-180 words MAXIMUM. Tight. Every word earns its place.
- Have a TAKE. Don't hedge with "could go either way" garbage
- Reference the actual numbers but don't just list stats
- Sound like a human with opinions, not a content algorithm
- End with a clear lean (side or total) - make it punchy

BANNED PHRASES (instant fail if you use these):
- "In this matchup"
- "Let's dive in" / "Let's break it down"
- "At the end of the day"
- "It's worth noting"
- "All things considered"
- "That being said"
- "Moving forward"
- Any sentence starting with "This is"

Write the take. No title. No headers. Just the analysis."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=350,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_stat_grid_html(self, game_data: Dict, sport: str) -> str:
        """Generate HTML for the stat grid display."""
        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        if sport.lower() in ['nba', 'ncaab']:
            return self._generate_basketball_stat_grid(home, away, odds)
        elif sport.lower() == 'nhl':
            return self._generate_hockey_stat_grid(home, away, odds)
        elif sport.lower() in ['nfl', 'ncaaf']:
            return self._generate_football_stat_grid(home, away, odds)
        elif sport.lower() == 'mlb':
            return self._generate_baseball_stat_grid(home, away, odds)
        elif sport.lower() == 'soccer':
            return self._generate_soccer_stat_grid(home, away, odds, game_data)
        else:
            return self._generate_generic_stat_grid(home, away, odds)

    def _generate_basketball_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{home.get('l10', 'N/A')}</div>
            <div class="stat-label">L10</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('l10', 'N/A')}</div>
            <div class="stat-label">L10</div>
        </div>
    </div>
</div>"""

    def _generate_hockey_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{home.get('points', 'N/A')} pts</div>
            <div class="stat-label">Standing</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('points', 'N/A')} pts</div>
            <div class="stat-label">Standing</div>
        </div>
    </div>
</div>"""

    def _generate_football_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{home.get('win_pct', 0):.0f}%</div>
            <div class="stat-label">Win%</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('win_pct', 0):.0f}%</div>
            <div class="stat-label">Win%</div>
        </div>
    </div>
</div>"""

    def _generate_baseball_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{home.get('probable_pitcher', 'TBD')}</div>
            <div class="stat-label">Starter</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('probable_pitcher', 'TBD')}</div>
            <div class="stat-label">Starter</div>
        </div>
    </div>
</div>"""

    def _generate_soccer_stat_grid(self, home: Dict, away: Dict, odds: Dict, game_data: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} W-D-L</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} W-D-L</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{home.get('points', 'N/A')}</div>
            <div class="stat-label">Points</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('points', 'N/A')}</div>
            <div class="stat-label">Points</div>
        </div>
    </div>
</div>"""

    def _generate_generic_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')}</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')}</div>
        </div>
    </div>
</div>"""


# Standalone test
if __name__ == "__main__":
    sample_game = {
        'matchup': 'Los Angeles Lakers @ Boston Celtics',
        'game_time': '7:30 PM ET',
        'venue': 'TD Garden',
        'broadcast': 'ESPN',
        'home': {
            'name': 'Boston Celtics',
            'abbrev': 'BOS',
            'record': '15-4',
            'l10': '8-2',
            'win_pct': 78.9
        },
        'away': {
            'name': 'Los Angeles Lakers',
            'abbrev': 'LAL',
            'record': '12-7',
            'l10': '6-4',
            'win_pct': 63.2
        },
        'odds': {
            'spread': 'BOS -6.5',
            'total': '224.5'
        }
    }

    try:
        generator = ContentGenerator()
        print("Testing content generation...")
        print("="*60)

        stat_grid = generator.generate_stat_grid_html(sample_game, 'nba')
        print("STAT GRID HTML:")
        print(stat_grid)
        print()

        print("GENERATED ARTICLE:")
        article = generator.generate_game_article(sample_game, 'nba')
        print(article)

    except ValueError as e:
        print(f"Error: {e}")
        print("Set ANTHROPIC_API_KEY environment variable to test content generation.")
