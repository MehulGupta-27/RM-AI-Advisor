"""
Commodity Tool
Fetches commodity prices (gold, silver, crude oil) using Yahoo Finance futures as proxy
Note: These are international futures, not exact MCX prices (as stated in spec limitations)
"""

import httpx
from typing import Optional, Dict
from app.tools.cache import get_cached, set_cached


# Commodity symbol mapping
# Using ETFs for gold/silver (more accurate than futures which may be far-dated contracts)
# Using front-month futures for oil/gas
COMMODITY_SYMBOLS = {
    "GOLD": "GLD",      # SPDR Gold Shares ETF (tracks physical gold)
    "SILVER": "SLV",    # iShares Silver Trust ETF (tracks physical silver)
    "COPPER": "HG=F",   # Copper futures
    "CRUDE": "CL=F",    # Crude oil futures
    "CRUDE_OIL": "CL=F",
    "OIL": "CL=F",
    "NATURAL_GAS": "NG=F",
    "GAS": "NG=F"
}

# Conversion factors: ETF price to actual commodity price
# GLD: Each share represents approximately 1/10th oz of gold
# SLV: Each share represents approximately 1 oz of silver
ETF_TO_COMMODITY = {
    "GLD": {"multiplier": 10.0, "unit": "oz"},      # GLD price * 10 ≈ gold price per oz
    "SLV": {"multiplier": 1.0, "unit": "oz"}        # SLV price ≈ silver price per oz
}


async def get_fx_rate() -> Optional[float]:
    """
    Get current USD to INR exchange rate
    Needed to convert commodity prices to rupees
    """
    
    cached = get_cached("fx_rate", "USDINR")
    if cached:
        return cached.get("rate")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/INR=X",
                params={"interval": "1d", "range": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                return 83.0  # Fallback rate
            
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return 83.0
            
            meta = result[0].get("meta", {})
            rate = meta.get("regularMarketPrice", 83.0)
            
            # Cache the rate
            set_cached("fx_rate", "USDINR", {"rate": rate})
            return rate
    
    except Exception as e:
        print(f"Error fetching FX rate: {e}")
        return 83.0  # Fallback


async def get_commodity_price(commodity: str) -> Optional[Dict]:
    """
    Fetch current commodity price
    
    Args:
        commodity: Commodity name (GOLD, SILVER, CRUDE, etc.)
        
    Returns:
        Dict with commodity data or None if failed
        {
            'commodity': str,
            'price_usd': float,
            'price_inr': float (for gold/silver),
            'unit': str,
            'change': float,
            'change_percent': float,
            'currency': str
        }
    """
    
    # Normalize commodity name
    commodity_upper = commodity.upper().replace(" ", "_")
    yahoo_symbol = COMMODITY_SYMBOLS.get(commodity_upper)
    
    if not yahoo_symbol:
        print(f"Unknown commodity: {commodity}")
        return None
    
    # Check cache
    cached = get_cached("commodity", commodity_upper)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={"interval": "1d", "range": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"Commodity API error for {commodity}: {response.status_code}")
                return None
            
            data = response.json()
            result = data.get("chart", {}).get("result", [])
            if not result:
                return None
            
            quote = result[0]
            meta = quote.get("meta", {})
            
            price_usd = meta.get("regularMarketPrice")
            previous_close = meta.get("previousClose") or meta.get("chartPreviousClose") or price_usd
            
            # For ETFs (GLD, SLV), convert to actual commodity price
            if yahoo_symbol in ETF_TO_COMMODITY:
                conversion = ETF_TO_COMMODITY[yahoo_symbol]
                price_usd = price_usd * conversion["multiplier"]
                if previous_close:
                    previous_close = previous_close * conversion["multiplier"]
            
            commodity_data = {
                "commodity": commodity.upper(),
                "price_usd": price_usd,
                "change": price_usd - previous_close if price_usd and previous_close else 0,
                "change_percent": ((price_usd - previous_close) / previous_close * 100) if price_usd and previous_close else 0,
                "currency": "USD"
            }
            
            # Add INR conversion for gold and silver
            if commodity_upper in ["GOLD", "SILVER"]:
                fx_rate = await get_fx_rate()
                
                if commodity_upper == "GOLD":
                    # Gold: USD/oz → ₹/10g
                    # 1 oz = 31.1035 grams
                    price_inr_per_10g = (price_usd * fx_rate / 31.1035) * 10
                    commodity_data["price_inr_per_10g"] = price_inr_per_10g
                    commodity_data["unit"] = "per 10 grams"
                    commodity_data["disclaimer"] = "⚠️ IMPORTANT: This is the international gold price. Indian retail prices (MCX/market) are typically 30-50% higher due to import duties (15%), GST (3%), and local premiums. For actual Indian prices, check MCX, local jewelers, or GoodReturns.in"
                
                elif commodity_upper == "SILVER":
                    # Silver: USD/oz → ₹/kg
                    price_inr_per_kg = (price_usd * fx_rate / 31.1035) * 1000
                    commodity_data["price_inr_per_kg"] = price_inr_per_kg
                    commodity_data["unit"] = "per kg"
                    commodity_data["disclaimer"] = "⚠️ IMPORTANT: This is the international silver price. Indian retail prices (MCX/market) are typically 30-50% higher due to import duties and GST. For actual Indian prices, check MCX or local dealers"
                
                commodity_data["fx_rate"] = fx_rate
            
            elif commodity_upper in ["CRUDE", "CRUDE_OIL", "OIL"]:
                commodity_data["unit"] = "per barrel"
            
            elif commodity_upper in ["NATURAL_GAS", "GAS"]:
                commodity_data["unit"] = "per MMBtu"
            
            # Cache and return
            return set_cached("commodity", commodity_upper, commodity_data)
    
    except Exception as e:
        print(f"Error fetching commodity price for {commodity}: {e}")
        return None


async def get_all_commodities() -> Dict[str, Optional[Dict]]:
    """Fetch all major commodities in parallel"""
    import asyncio
    
    commodities = ["GOLD", "SILVER", "CRUDE"]
    
    results = await asyncio.gather(
        *[get_commodity_price(c) for c in commodities],
        return_exceptions=True
    )
    
    return {
        c: result if not isinstance(result, Exception) else None
        for c, result in zip(commodities, results)
    }


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("Fetching Gold price...")
        gold = await get_commodity_price("GOLD")
        if gold:
            print(f"Gold: ${gold['price_usd']:.2f}/oz")
            if 'price_inr_per_10g' in gold:
                print(f"      ₹{gold['price_inr_per_10g']:.2f}/10g")
        
        print("\nFetching all commodities...")
        commodities = await get_all_commodities()
        for name, data in commodities.items():
            if data:
                print(f"{name}: ${data['price_usd']:.2f} {data.get('unit', '')}")
    
    asyncio.run(test())
