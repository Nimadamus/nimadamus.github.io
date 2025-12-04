"""
Content Generator using Claude API
Generates human-sounding sports articles from game data
"""

import os
import json
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

    def generate_daily_slate_intro(self, sport: str, games: List[Dict], date: str = None) -> str:
        """Generate the intro paragraph for a daily slate post."""
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")

        num_games = len(games)

        prompt = f"""Write a brief, engaging 2-3 sentence introduction for a {sport} betting preview article.

Date: {date}
Number of games: {num_games}

The intro should:
- Be conversational but professional
- Mention the number of games on the slate
- Build excitement without being over-the-top
- NOT include any specific picks or predictions yet
- Be suitable for a sports betting website

Write ONLY the intro paragraph, nothing else."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_game_article(self, game_data: Dict, sport: str) -> str:
        """Generate a conversational article for a single game."""

        # Build the game context
        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        game_context = f"""
MATCHUP: {away.get('name', 'Away')} @ {home.get('name', 'Home')}

HOME TEAM: {home.get('name')}
- Record: {home.get('record', 'N/A')}
- Last 10: {home.get('l10', home.get('l5', 'N/A'))}
- Win %: {home.get('win_pct', 0):.1f}%

AWAY TEAM: {away.get('name')}
- Record: {away.get('record', 'N/A')}
- Last 10: {away.get('l10', away.get('l5', 'N/A'))}
- Win %: {away.get('win_pct', 0):.1f}%

BETTING LINES:
- Spread: {odds.get('spread', 'N/A')}
- Total: {odds.get('total', 'N/A')}

VENUE: {game_data.get('venue', 'N/A')}
BROADCAST: {game_data.get('broadcast', 'N/A')}
"""

        # Sport-specific additions
        if sport.lower() == 'nhl':
            game_context += f"""
HOME POINTS: {home.get('points', 'N/A')}
AWAY POINTS: {away.get('points', 'N/A')}
"""
        elif sport.lower() == 'mlb':
            game_context += f"""
HOME PROBABLE PITCHER: {home.get('probable_pitcher', 'TBD')}
AWAY PROBABLE PITCHER: {away.get('probable_pitcher', 'TBD')}
"""
        elif sport.lower() == 'soccer':
            game_context += f"""
LEAGUE: {game_data.get('league', 'N/A')}
MATCHWEEK: {game_data.get('match_week', 'N/A')}
"""

        prompt = f"""Write a betting analysis article for this {sport} game. The article should be:

1. CONVERSATIONAL - Write like you're explaining to a friend who bets on sports
2. ANALYTICAL - Reference the actual stats and records provided
3. INFORMATIVE - Include relevant trends, matchup factors, situational angles
4. BALANCED - Discuss both sides before leaning one way
5. LENGTH: 200-300 words

GAME DATA:
{game_context}

IMPORTANT GUIDELINES:
- Use the actual stats provided - DO NOT make up numbers
- Be specific about WHY a team has an edge
- Mention the line/total and whether it looks right
- Include at least one trend or angle (home/away splits, recent form, etc.)
- End with a clear lean or pick, but keep it analytical not promotional
- NO emojis, NO excessive hype language
- Write naturally - vary sentence structure, use contractions

Write the article now. Do NOT include a title or headers - just the analysis paragraph(s)."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def generate_stat_grid_html(self, game_data: Dict, sport: str) -> str:
        """Generate HTML for the stat grid display."""
        home = game_data.get('home', {})
        away = game_data.get('away', {})
        odds = game_data.get('odds', {})

        # Different stat grids for different sports
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
        """Generate basketball-specific stat grid."""
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Record</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Record</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('l10', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} L10</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('l10', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} L10</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{odds.get('spread', 'N/A')}</div>
            <div class="stat-label">Spread</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total</div>
        </div>
    </div>
</div>"""

    def _generate_hockey_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        """Generate hockey-specific stat grid."""
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Record</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Record</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('points', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Points</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('points', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Points</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{odds.get('spread', 'N/A')}</div>
            <div class="stat-label">Puck Line</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total</div>
        </div>
    </div>
</div>"""

    def _generate_football_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        """Generate football-specific stat grid."""
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Record</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Record</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('win_pct', 0):.0f}%</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Win %</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('win_pct', 0):.0f}%</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Win %</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{odds.get('spread', 'N/A')}</div>
            <div class="stat-label">Spread</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total</div>
        </div>
    </div>
</div>"""

    def _generate_baseball_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        """Generate baseball-specific stat grid."""
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Record</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Record</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('probable_pitcher', 'TBD')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} SP</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('probable_pitcher', 'TBD')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} SP</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{odds.get('spread', 'N/A')}</div>
            <div class="stat-label">Run Line</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total</div>
        </div>
    </div>
</div>"""

    def _generate_soccer_stat_grid(self, home: Dict, away: Dict, odds: Dict, game_data: Dict) -> str:
        """Generate soccer-specific stat grid."""
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
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('points', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Points</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('points', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Points</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{game_data.get('league', 'N/A')}</div>
            <div class="stat-label">League</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total Goals</div>
        </div>
    </div>
</div>"""

    def _generate_generic_stat_grid(self, home: Dict, away: Dict, odds: Dict) -> str:
        """Generate generic stat grid for any sport."""
        return f"""<div class="stat-grid">
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{home.get('record', 'N/A')}</div>
            <div class="stat-label">{home.get('abbrev', 'HOME')} Record</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{away.get('record', 'N/A')}</div>
            <div class="stat-label">{away.get('abbrev', 'AWAY')} Record</div>
        </div>
    </div>
    <div class="stat-row">
        <div class="stat-item">
            <div class="stat-value">{odds.get('spread', 'N/A')}</div>
            <div class="stat-label">Spread</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{odds.get('total', 'N/A')}</div>
            <div class="stat-label">Total</div>
        </div>
    </div>
</div>"""

    def generate_full_game_section(self, game_data: Dict, sport: str) -> str:
        """Generate complete HTML section for a game (stat grid + article)."""
        home = game_data.get('home', {})
        away = game_data.get('away', {})

        matchup_title = f"{away.get('name', 'Away')} @ {home.get('name', 'Home')}"

        # Generate components
        stat_grid = self.generate_stat_grid_html(game_data, sport)
        article = self.generate_game_article(game_data, sport)

        # Build the full section
        html = f"""
<div class="game-section" id="game-{away.get('abbrev', 'away').lower()}-{home.get('abbrev', 'home').lower()}">
    <h3 class="game-title">{matchup_title}</h3>
    <div class="game-meta">
        <span class="game-time">{game_data.get('game_time', '')}</span>
        <span class="game-venue">{game_data.get('venue', '')}</span>
        <span class="game-broadcast">{game_data.get('broadcast', '')}</span>
    </div>
    {stat_grid}
    <div class="game-analysis">
        <p>{article}</p>
    </div>
</div>
"""
        return html


# Standalone test
if __name__ == "__main__":
    # Test with sample data
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

        # Test stat grid
        stat_grid = generator.generate_stat_grid_html(sample_game, 'nba')
        print("STAT GRID HTML:")
        print(stat_grid)
        print()

        # Test article generation
        print("GENERATED ARTICLE:")
        article = generator.generate_game_article(sample_game, 'nba')
        print(article)

    except ValueError as e:
        print(f"Error: {e}")
        print("Set ANTHROPIC_API_KEY environment variable to test content generation.")
