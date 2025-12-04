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
        """Generate articles matching BetLegend's actual voice - sharp, colorful, opinionated."""

        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        game_info = f"""{away.get('name')} ({away.get('record', '?')}) @ {home.get('name')} ({home.get('record', '?')})
Away L10: {away.get('l10', '?')} | Home L10: {home.get('l10', '?')}
Line: {odds.get('spread', 'N/A')} | Total: {odds.get('total', 'N/A')}"""

        if sport.lower() == 'nhl':
            game_info += f"\nStandings: {home.get('name')} {home.get('points', '?')} pts | {away.get('name')} {away.get('points', '?')} pts"

        # Sample of ACTUAL BetLegend writing for style reference - ANALYSIS ONLY, NO PICKS
        style_examples = """
REAL EXAMPLES OF THE VOICE I WANT:
- "The public's sleeping on Golden State here."
- "55% is barely above mediocre - that's not some fortress we're talking about."
- "Philly's been fool's gold at home - they beat the teams they're supposed to beat and fold against quality opposition."
- "Washington? They couldn't stop a nosebleed if their lives depended on it."
- "The Wizards are giving up 118 per game at home, which is pathetic even by their rock-bottom standards."
- "Boston's been Swiss cheese on the road."
- "Washington desperate for any excitement to keep the dozen fans awake."
- "Two teams that can't guard a traffic cone."
- "This total feels inflated given how both defenses have been playing."
- "The line here doesn't account for the scheduling disadvantage."
"""

        # Pick a unique opening style for variety
        openers = [
            "Start with a bold observation about the matchup",
            "Start by calling out what the public is missing",
            "Start with the one number that tells the whole story",
            "Start by highlighting the weaker team's struggles",
            "Start with the interesting line movement angle",
            "Start with the trap game potential",
            "Start with recent form - who's hot, who's not",
            "Start with a question that frames the analysis",
            "Start by highlighting the underdog's strengths",
            "Start with the total and what it suggests",
            "Start with a scheduling/rest angle",
            "Start with why the favorite might be overvalued",
        ]
        chosen_opener = random.choice(openers)

        prompt = f"""You write sharp sports analysis with REAL personality. Study these examples of the voice I need:

{style_examples}

NOW WRITE ANALYSIS FOR THIS GAME:
{game_info}

OPENING INSTRUCTION: {chosen_opener}

RULES:
1. Write 3-4 short paragraphs (150-200 words total)
2. Use vivid metaphors and colorful language like the examples
3. Be OPINIONATED and insightful - share strong observations
4. Include specific numbers from the data naturally
5. This is ANALYSIS ONLY - DO NOT include any picks, leans, or betting recommendations
6. DO NOT end with "Lean:" or "Hammer the over" or any betting suggestion
7. End with an insightful observation about what to watch for in this game
8. Sound like a sharp analyst, not a robot
9. Mock bad teams, praise good ones, identify key storylines
10. NEVER start with "Listen" or "Here's the thing" or "Look" - find a unique opening
11. NO generic phrases like "it's worth noting" or "at the end of the day"
12. NO emojis
13. NO PICKS - this is informational analysis only

Write it now. Just the paragraphs, no title."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=400,
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
