"""
Index Quote Tool
Fetches live index levels for Nifty, Sensex
"""

import httpx
from typing import Optional, Dict
from app.tools.cache import get_cached, set_cached


# Index symbol mapping
INDEX_SYMBOLS = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY_50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "BANK_NIFTY": "^NSEBANK"
}


async def get_index_quote(index_name: str) -> Optional[Dict]:
    """
    Fetch current index level from Yahoo Finance
    
    Args:
        index_name: Index name (NIFTY, SENSEX, BANKNIFTY)
        
    Returns:
        Dict with index data or None if failed
        {
            'index': str,
            'level': float,
            'change': float,
            'change_percent': float,
            'day_high': float,
            'day_low': float,
            'open': float,
            'previous_close': float
        }
    """
    
    # Normalize index name
    index_upper = index_name.upper().replace(" ", "_")
    yahoo_symbol = INDEX_SYMBOLS.get(index_upper)
    
    if not yahoo_symbol:
        print(f"Unknown index: {index_name}")
        return None
    
    # Check cache
    cached = get_cached("index_quote", index_upper)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={
                    "interval": "1d",
                    "range": "1d"
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"Index quote API error for {index_name}: {response.status_code}")
                return None
            
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            
            quote = result[0]
            meta = quote.get("meta", {})
            
            # Extract data
            index_data = {
                "index": index_name.upper(),
                "level": meta.get("regularMarketPrice"),
                "change": meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0),
                "change_percent": ((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)) / meta.get("previousClose", 1)) * 100 if meta.get("previousClose") else 0,
                "day_high": meta.get("regularMarketDayHigh"),
                "day_low": meta.get("regularMarketDayLow"),
                "open": meta.get("regularMarketOpen"),
                "previous_close": meta.get("previousClose")
            }
            
            # Cache and return
            return set_cached("index_quote", index_upper, index_data)
    
    except Exception as e:
        print(f"Error fetching index quote for {index_name}: {e}")
        return None


async def get_all_major_indices() -> Dict[str, Optional[Dict]]:
    """Fetch all major Indian indices"""
    import asyncio
    
    indices = ["NIFTY", "SENSEX", "BANKNIFTY"]
    
    results = await asyncio.gather(
        *[get_index_quote(idx) for idx in indices],
        return_exceptions=True
    )
    
    return {
        idx: result if not isinstance(result, Exception) else None
        for idx, result in zip(indices, results)
    }


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Fetching Nifty...")
        nifty = await get_index_quote("NIFTY")
        if nifty:
            print(f"Nifty: {nifty['level']:.2f}")
            print(f"Change: {nifty['change']:+.2f} ({nifty['change_percent']:+.2f}%)")
        
        print("\nFetching all major indices...")
        indices = await get_all_major_indices()
        for name, data in indices.items():
            if data:
                print(f"{name}: {data['level']:.2f} ({data['change_percent']:+.2f}%)")
    
    asyncio.run(test())
