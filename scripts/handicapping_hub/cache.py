"""
CACHING SYSTEM
==============
File-based caching with TTL support for efficient data retrieval
and fallback when APIs are unavailable.
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib


class DataCache:
    """File-based cache with TTL and fallback support"""

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), 'cache_data')
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, key: str) -> str:
        """Get file path for cache key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Get cached data if not expired.

        Args:
            key: Cache key
            max_age_hours: Maximum age in hours before data is stale

        Returns:
            Cached data or None if not found/expired
        """
        cache_path = self._get_cache_path(key)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            cached_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
            max_age = timedelta(hours=max_age_hours)

            if datetime.now() - cached_time < max_age:
                return cached.get('data')

            return None

        except Exception as e:
            print(f"Cache read error for {key}: {e}")
            return None

    def set(self, key: str, data: Any) -> bool:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache

        Returns:
            True if successful
        """
        cache_path = self._get_cache_path(key)

        try:
            cached = {
                'timestamp': datetime.now().isoformat(),
                'key': key,
                'data': data
            }

            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cached, f, indent=2, default=str)

            return True

        except Exception as e:
            print(f"Cache write error for {key}: {e}")
            return False

    def get_or_fetch(self, key: str, fetch_func, max_age_hours: int = 6) -> Any:
        """
        Get from cache or fetch fresh data.

        Args:
            key: Cache key
            fetch_func: Function to call if cache miss
            max_age_hours: Maximum cache age

        Returns:
            Data from cache or fresh fetch
        """
        cached = self.get(key, max_age_hours)
        if cached is not None:
            return cached

        try:
            fresh_data = fetch_func()
            if fresh_data:
                self.set(key, fresh_data)
            return fresh_data
        except Exception as e:
            print(f"Fetch error for {key}: {e}")
            # Return stale cache as fallback
            return self.get(key, max_age_hours=168)  # 7 days fallback

    def clear_old(self, max_age_days: int = 7):
        """Remove cache files older than specified days"""
        cutoff = datetime.now() - timedelta(days=max_age_days)

        for filename in os.listdir(self.cache_dir):
            filepath = os.path.join(self.cache_dir, filename)
            if os.path.isfile(filepath):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if mtime < cutoff:
                        os.remove(filepath)
                except:
                    pass


# Global cache instance
cache = DataCache()
