"""
Sports Data Scrapers Package
Provides unified access to all sport-specific scrapers
"""

from .nba_scraper import NBAScraper
from .nhl_scraper import NHLScraper
from .nfl_scraper import NFLScraper
from .ncaab_scraper import NCAABScraper
from .ncaaf_scraper import NCAAFScraper
from .mlb_scraper import MLBScraper
from .soccer_scraper import SoccerScraper
from .base_scraper import BaseScraper, GameData

# Mapping of sport codes to scraper classes
SCRAPERS = {
    'nba': NBAScraper,
    'nhl': NHLScraper,
    'nfl': NFLScraper,
    'ncaab': NCAABScraper,
    'ncaaf': NCAAFScraper,
    'mlb': MLBScraper,
    'soccer': SoccerScraper,
}

def get_scraper(sport: str):
    """Get the appropriate scraper for a sport.

    Args:
        sport: Sport code (nba, nhl, nfl, ncaab, ncaaf, mlb, soccer)

    Returns:
        Initialized scraper instance

    Raises:
        ValueError: If sport is not supported
    """
    sport_lower = sport.lower()
    if sport_lower not in SCRAPERS:
        raise ValueError(f"Unknown sport: {sport}. Supported: {list(SCRAPERS.keys())}")

    return SCRAPERS[sport_lower]()

def get_all_scrapers():
    """Get all available scrapers as a dictionary.

    Returns:
        Dict mapping sport codes to initialized scraper instances
    """
    return {sport: scraper_class() for sport, scraper_class in SCRAPERS.items()}

__all__ = [
    'NBAScraper',
    'NHLScraper',
    'NFLScraper',
    'NCAABScraper',
    'NCAAFScraper',
    'MLBScraper',
    'SoccerScraper',
    'BaseScraper',
    'GameData',
    'SCRAPERS',
    'get_scraper',
    'get_all_scrapers',
]
