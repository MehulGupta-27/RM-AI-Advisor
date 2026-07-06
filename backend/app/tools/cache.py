"""
Caching layer for market data tools
TTL-based in-memory cache to avoid rate limits and improve performance
"""

from cachetools import TTLCache
import os

# Cache configuration
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "90"))  # 90 seconds default

# Global cache instance
# Key: (tool_name, symbol)
# Value: tool response data
market_data_cache = TTLCache(maxsize=500, ttl=CACHE_TTL)


def get_cache_key(tool_name: str, symbol: str) -> str:
    """Generate cache key from tool name and symbol"""
    return f"{tool_name}:{symbol.upper()}"


def get_cached(tool_name: str, symbol: str):
    """Get cached data if available"""
    key = get_cache_key(tool_name, symbol)
    return market_data_cache.get(key)


def set_cached(tool_name: str, symbol: str, data):
    """Store data in cache"""
    key = get_cache_key(tool_name, symbol)
    market_data_cache[key] = data
    return data


def clear_cache():
    """Clear all cached data (useful for testing)"""
    market_data_cache.clear()
