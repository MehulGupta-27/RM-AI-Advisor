"""
Stock Quote Tool
Fetches live NSE stock prices using Yahoo Finance
"""

import httpx
from typing import Optional, Dict
from app.tools.cache import get_cached, set_cached


async def get_stock_quote(ticker: str) -> Optional[Dict]:
    """
    Fetch current stock price from Yahoo Finance
    
    Args:
        ticker: NSE ticker symbol (e.g., RELIANCE, TCS, INFY)
        
    Returns:
        Dict with stock data or None if failed
        {
            'symbol': str,
            'price': float,
            'change': float,
            'change_percent': float,
            'day_high': float,
            'day_low': float,
            'open': float,
            'previous_close': float,
            '52w_high': float,
            '52w_low': float,
            'volume': int,
            'market_cap': float (optional),
            'pe_ratio': float (optional)
        }
    """
    
    # Check cache first
    cached = get_cached("stock_quote", ticker)
    if cached:
        return cached
    
    try:
        # Yahoo Finance API expects .NS suffix for NSE stocks
        yahoo_symbol = f"{ticker.upper()}.NS"
        
        # Use Yahoo Finance quote endpoint
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
                print(f"Stock quote API error for {ticker}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Parse response
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            
            quote = result[0]
            meta = quote.get("meta", {})
            
            # Extract data
            stock_data = {
                "symbol": ticker.upper(),
                "price": meta.get("regularMarketPrice"),
                "change": meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0),
                "change_percent": ((meta.get("regularMarketPrice", 0) - meta.get("previousClose", 0)) / meta.get("previousClose", 1)) * 100 if meta.get("previousClose") else 0,
                "day_high": meta.get("regularMarketDayHigh"),
                "day_low": meta.get("regularMarketDayLow"),
                "open": meta.get("regularMarketOpen"),
                "previous_close": meta.get("previousClose"),
                "52w_high": meta.get("fiftyTwoWeekHigh"),
                "52w_low": meta.get("fiftyTwoWeekLow"),
                "volume": meta.get("regularMarketVolume"),
                "currency": meta.get("currency", "INR")
            }
            
            # Cache and return
            return set_cached("stock_quote", ticker, stock_data)
    
    except Exception as e:
        print(f"Error fetching stock quote for {ticker}: {e}")
        return None


async def get_multiple_stock_quotes(tickers: list) -> Dict[str, Optional[Dict]]:
    """
    Fetch quotes for multiple stocks in parallel
    
    Args:
        tickers: List of NSE ticker symbols
        
    Returns:
        Dict mapping ticker to stock data (or None if failed)
    """
    import asyncio
    
    # Fetch all in parallel
    results = await asyncio.gather(
        *[get_stock_quote(ticker) for ticker in tickers],
        return_exceptions=True
    )
    
    # Build response dict
    return {
        ticker: result if not isinstance(result, Exception) else None
        for ticker, result in zip(tickers, results)
    }


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test single stock
        print("Fetching RELIANCE...")
        quote = await get_stock_quote("RELIANCE")
        if quote:
            print(f"Price: ₹{quote['price']:.2f}")
            print(f"Change: {quote['change']:+.2f} ({quote['change_percent']:+.2f}%)")
        else:
            print("Failed to fetch")
        
        # Test multiple stocks
        print("\nFetching TCS, INFY, HDFCBANK...")
        quotes = await get_multiple_stock_quotes(["TCS", "INFY", "HDFCBANK"])
        for ticker, data in quotes.items():
            if data:
                print(f"{ticker}: ₹{data['price']:.2f}")
            else:
                print(f"{ticker}: Failed")
    
    asyncio.run(test())
