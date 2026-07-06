"""
Top Movers Tool
Fetches and ranks stocks by performance over a period (screener functionality)
"""

import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.config.universes import get_universe
from app.tools.cache import get_cached, set_cached


async def get_top_movers(
    period: str = "1wk",
    universe: str = "nifty50",
    limit: int = 10,
    direction: str = "gainers"
) -> List[Dict]:
    """
    Fetch top gaining or losing stocks over a period.
    
    Args:
        period: Time period - "1d" (1 day), "1wk" (1 week), "1mo" (1 month)
        universe: Stock universe - "nifty50", "banknifty", "niftyit"
        limit: Number of stocks to return
        direction: "gainers" (top performers) or "losers" (worst performers)
        
    Returns:
        List of dicts with:
        {
            "symbol": str,
            "change_pct": float,
            "current_price": float,
            "start_price": float,
            "change": float,
            "volume": int
        }
    """
    
    # Check cache (5 minute TTL for screeners)
    cache_key = f"{universe}_{period}_{direction}"
    cached = get_cached("top_movers", cache_key)
    if cached:
        return cached[:limit]
    
    # Get ticker list
    tickers = get_universe(universe)
    
    # Map period to days
    period_map = {
        "1d": 1,
        "1wk": 7,
        "1mo": 30
    }
    days = period_map.get(period, 7)
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 5)  # Add buffer for market holidays
    
    results = []
    
    # Fetch data for each ticker
    for ticker in tickers:
        try:
            yahoo_symbol = f"{ticker}.NS"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                    params={
                        "interval": "1d",
                        "period1": int(start_date.timestamp()),
                        "period2": int(end_date.timestamp())
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                result = data.get("chart", {}).get("result", [])
                if not result:
                    continue
                
                quote = result[0]
                indicators = quote.get("indicators", {}).get("quote", [{}])[0]
                
                # Get close prices
                close_prices = indicators.get("close", [])
                volumes = indicators.get("volume", [])
                
                # Filter out None values
                valid_closes = [p for p in close_prices if p is not None]
                valid_volumes = [v for v in volumes if v is not None]
                
                if len(valid_closes) < 2:
                    continue
                
                # Start price (oldest) and end price (newest)
                start_price = valid_closes[0]
                current_price = valid_closes[-1]
                
                # Calculate change
                change = current_price - start_price
                change_pct = (change / start_price * 100) if start_price > 0 else 0
                
                # Get latest volume
                volume = valid_volumes[-1] if valid_volumes else 0
                
                results.append({
                    "symbol": ticker,
                    "change_pct": round(change_pct, 2),
                    "current_price": round(current_price, 2),
                    "start_price": round(start_price, 2),
                    "change": round(change, 2),
                    "volume": int(volume)
                })
        
        except Exception as e:
            # Silent fail for individual stocks - screener should return partial results
            print(f"[TOP MOVERS] Error fetching {ticker}: {e}")
            continue
    
    # Sort results
    if direction == "losers":
        results.sort(key=lambda x: x['change_pct'])  # Ascending (most negative first)
    else:  # gainers
        results.sort(key=lambda x: x['change_pct'], reverse=True)  # Descending (highest first)
    
    # Cache full results
    if results:
        set_cached("top_movers", cache_key, results)
    
    # Return top N
    return results[:limit]


async def format_top_movers(movers: List[Dict], period: str, direction: str) -> str:
    """
    Format top movers list for display.
    
    Args:
        movers: List of stock performance dicts
        period: Time period queried
        direction: "gainers" or "losers"
        
    Returns:
        Formatted string with table
    """
    if not movers:
        return f"No {direction} data available for the {period} period."
    
    period_labels = {
        "1d": "today",
        "1wk": "this week",
        "1mo": "this month"
    }
    period_label = period_labels.get(period, period)
    
    output = f"## Top {direction.title()} {period_label.title()}\n\n"
    output += "| Rank | Stock | Change % | Current Price | Change (₹) | Volume |\n"
    output += "|------|-------|----------|---------------|------------|--------|\n"
    
    for i, stock in enumerate(movers, 1):
        symbol = stock['symbol']
        change_pct = stock['change_pct']
        current_price = stock['current_price']
        change = stock['change']
        volume = stock['volume']
        
        # Format change with color indicator
        change_sign = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "⚪"
        
        output += f"| {i} | **{symbol}** | {change_sign} {change_pct:+.2f}% | ₹{current_price:.2f} | {change:+.2f} | {volume:,} |\n"
    
    output += f"\n*Based on {period_label} performance. Past performance is not indicative of future results.*"
    
    return output


# Testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing top movers tool...")
        
        # Test 1: Top gainers this week
        print("\n1. Top gainers this week (Nifty 50):")
        gainers = await get_top_movers(period="1wk", universe="nifty50", limit=5, direction="gainers")
        for stock in gainers:
            print(f"  {stock['symbol']}: {stock['change_pct']:+.2f}% (₹{stock['current_price']:.2f})")
        
        # Test 2: Top losers today
        print("\n2. Top losers today (Nifty 50):")
        losers = await get_top_movers(period="1d", universe="nifty50", limit=5, direction="losers")
        for stock in losers:
            print(f"  {stock['symbol']}: {stock['change_pct']:+.2f}% (₹{stock['current_price']:.2f})")
        
        # Test 3: Formatted output
        print("\n3. Formatted output:")
        formatted = await format_top_movers(gainers, "1wk", "gainers")
        print(formatted)
    
    asyncio.run(test())
