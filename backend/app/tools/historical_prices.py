"""
Historical Price Tool
Fetches historical price data for stocks and commodities to calculate 1-year changes
"""

import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.tools.cache import get_cached, set_cached


async def get_stock_historical(ticker: str, days: int = 365) -> Optional[Dict]:
    """
    Fetch historical price data for a stock
    
    Args:
        ticker: NSE ticker symbol (e.g., RELIANCE, TCS, INFY)
        days: Number of days of history (default 365)
        
    Returns:
        Dict with historical data or None if failed
        {
            'symbol': str,
            'current_price': float,
            'price_1y_ago': float,
            'change_1y': float,
            'change_1y_percent': float,
            'high_1y': float,
            'low_1y': float
        }
    """
    
    # Check cache first (cache for 1 hour)
    cache_key = f"{ticker}_{days}d"
    cached = get_cached("stock_historical", cache_key)
    if cached:
        return cached
    
    try:
        # Yahoo Finance API expects .NS suffix for NSE stocks
        yahoo_symbol = f"{ticker.upper()}.NS"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)  # Add buffer for market holidays
        
        # Use Yahoo Finance chart endpoint for historical data
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
                timeout=15.0
            )
            
            if response.status_code != 200:
                print(f"Historical API error for {ticker}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Parse response
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            
            quote = result[0]
            meta = quote.get("meta", {})
            indicators = quote.get("indicators", {}).get("quote", [{}])[0]
            timestamps = quote.get("timestamp", [])
            
            # Get close prices
            close_prices = indicators.get("close", [])
            high_prices = indicators.get("high", [])
            low_prices = indicators.get("low", [])
            
            if not close_prices or len(close_prices) < 2:
                return None
            
            # Filter out None values
            valid_closes = [p for p in close_prices if p is not None]
            valid_highs = [p for p in high_prices if p is not None]
            valid_lows = [p for p in low_prices if p is not None]
            
            if not valid_closes:
                return None
            
            # Current price (most recent)
            current_price = valid_closes[-1]
            
            # Price from ~1 year ago (first valid price)
            price_1y_ago = valid_closes[0]
            
            # Calculate changes
            change_1y = current_price - price_1y_ago
            change_1y_percent = (change_1y / price_1y_ago * 100) if price_1y_ago else 0
            
            # Extract data
            historical_data = {
                "symbol": ticker.upper(),
                "current_price": current_price,
                "price_1y_ago": price_1y_ago,
                "change_1y": change_1y,
                "change_1y_percent": change_1y_percent,
                "high_1y": max(valid_highs) if valid_highs else current_price,
                "low_1y": min(valid_lows) if valid_lows else current_price,
                "data_points": len(valid_closes),
                "period_days": len(timestamps)
            }
            
            # Cache and return
            return set_cached("stock_historical", cache_key, historical_data)
    
    except Exception as e:
        print(f"Error fetching historical data for {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_commodity_historical(commodity: str, days: int = 365) -> Optional[Dict]:
    """
    Fetch historical price data for a commodity
    
    Args:
        commodity: Commodity name (GOLD, SILVER, CRUDE, etc.)
        days: Number of days of history (default 365)
        
    Returns:
        Dict with historical data or None if failed
    """
    
    # Commodity symbol mapping (Yahoo Finance futures symbols)
    COMMODITY_SYMBOLS = {
        "GOLD": "GC=F",
        "SILVER": "SI=F",
        "CRUDE": "CL=F",
        "CRUDE_OIL": "CL=F"
    }
    
    commodity_upper = commodity.upper()
    yahoo_symbol = COMMODITY_SYMBOLS.get(commodity_upper)
    
    if not yahoo_symbol:
        return None
    
    # Check cache
    cache_key = f"{commodity_upper}_{days}d"
    cached = get_cached("commodity_historical", cache_key)
    if cached:
        return cached
    
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 30)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={
                    "interval": "1d",
                    "period1": int(start_date.timestamp()),
                    "period2": int(end_date.timestamp())
                },
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15.0
            )
            
            if response.status_code != 200:
                print(f"Historical commodity API error for {commodity}: {response.status_code}")
                return None
            
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            
            quote = result[0]
            indicators = quote.get("indicators", {}).get("quote", [{}])[0]
            
            # Get close prices
            close_prices = indicators.get("close", [])
            valid_closes = [p for p in close_prices if p is not None]
            
            if not valid_closes or len(valid_closes) < 2:
                return None
            
            current_price = valid_closes[-1]
            price_1y_ago = valid_closes[0]
            change_1y = current_price - price_1y_ago
            change_1y_percent = (change_1y / price_1y_ago * 100) if price_1y_ago else 0
            
            historical_data = {
                "commodity": commodity_upper,
                "current_price_usd": current_price,
                "price_1y_ago_usd": price_1y_ago,
                "change_1y_usd": change_1y,
                "change_1y_percent": change_1y_percent,
                "data_points": len(valid_closes)
            }
            
            # Add INR conversion for gold
            if commodity_upper == "GOLD":
                # Get FX rate
                from app.tools.commodity import get_fx_rate
                fx_rate = await get_fx_rate()
                
                # Convert to ₹/10g
                current_inr = (current_price * fx_rate / 31.1035) * 10
                price_1y_ago_inr = (price_1y_ago * fx_rate / 31.1035) * 10
                
                historical_data["current_price_inr_per_10g"] = current_inr
                historical_data["price_1y_ago_inr_per_10g"] = price_1y_ago_inr
                historical_data["change_1y_inr"] = current_inr - price_1y_ago_inr
                historical_data["fx_rate"] = fx_rate
            
            # Cache and return
            return set_cached("commodity_historical", cache_key, historical_data)
    
    except Exception as e:
        print(f"Error fetching historical commodity data for {commodity}: {e}")
        return None


# Testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Testing TCS historical data...")
        tcs = await get_stock_historical("TCS")
        if tcs:
            print(f"TCS Current: ₹{tcs['current_price']:.2f}")
            print(f"TCS 1Y Ago: ₹{tcs['price_1y_ago']:.2f}")
            print(f"TCS Change: {tcs['change_1y_percent']:+.2f}%")
        else:
            print("Failed to fetch TCS data")
        
        print("\nTesting Gold historical data...")
        gold = await get_commodity_historical("GOLD")
        if gold:
            print(f"Gold Current: ${gold['current_price_usd']:.2f}/oz")
            print(f"Gold 1Y Ago: ${gold['price_1y_ago_usd']:.2f}/oz")
            print(f"Gold Change: {gold['change_1y_percent']:+.2f}%")
            if 'current_price_inr_per_10g' in gold:
                print(f"Gold Current (INR): ₹{gold['current_price_inr_per_10g']:.2f}/10g")
        else:
            print("Failed to fetch Gold data")
    
    asyncio.run(test())
