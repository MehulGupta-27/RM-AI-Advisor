"""
Mutual Fund Tool
Fetches NAV and fund data from mfapi.in (AMFI data source)
"""

import httpx
from typing import Optional, Dict, List
from app.tools.cache import get_cached, set_cached


async def search_mutual_fund(scheme_name: str) -> Optional[List[Dict]]:
    """
    Search for mutual fund schemes by name
    
    Args:
        scheme_name: Fund name or partial name to search
        
    Returns:
        List of matching schemes with scheme codes
    """
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.mfapi.in/mf/search",
                params={"q": scheme_name},
                timeout=10.0
            )
            
            if response.status_code != 200:
                return None
            
            return response.json()
    
    except Exception as e:
        print(f"Error searching mutual funds: {e}")
        return None


async def get_mutual_fund_nav(scheme_code: str) -> Optional[Dict]:
    """
    Fetch latest NAV for a mutual fund scheme
    
    Args:
        scheme_code: AMFI scheme code (6-digit number)
        
    Returns:
        Dict with fund data or None if failed
        {
            'scheme_code': str,
            'scheme_name': str,
            'nav': float,
            'date': str (DD-MM-YYYY),
            'scheme_type': str,
            'scheme_category': str,
            'fund_house': str
        }
    """
    
    # Check cache
    cached = get_cached("mutual_fund", scheme_code)
    if cached:
        return cached
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.mfapi.in/mf/{scheme_code}",
                timeout=10.0
            )
            
            if response.status_code != 200:
                print(f"MF API error for scheme {scheme_code}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Get latest NAV
            if not data.get("data"):
                return None
            
            latest = data["data"][0]  # Most recent NAV
            
            fund_data = {
                "scheme_code": scheme_code,
                "scheme_name": data.get("meta", {}).get("scheme_name"),
                "nav": float(latest.get("nav", 0)),
                "date": latest.get("date"),
                "scheme_type": data.get("meta", {}).get("scheme_type"),
                "scheme_category": data.get("meta", {}).get("scheme_category"),
                "fund_house": data.get("meta", {}).get("fund_house")
            }
            
            # Cache and return
            return set_cached("mutual_fund", scheme_code, fund_data)
    
    except Exception as e:
        print(f"Error fetching MF NAV for {scheme_code}: {e}")
        return None


async def get_mutual_fund_by_name(fund_name: str) -> Optional[Dict]:
    """
    Search for a fund by name and get its latest NAV
    Convenience function that combines search + NAV fetch
    
    Args:
        fund_name: Fund name to search for
        
    Returns:
        Dict with fund data or None if not found
    """
    
    # Search for the fund
    results = await search_mutual_fund(fund_name)
    
    if not results or len(results) == 0:
        return None
    
    # Get NAV for first matching result
    first_match = results[0]
    scheme_code = first_match.get("schemeCode")
    
    if not scheme_code:
        return None
    
    return await get_mutual_fund_nav(str(scheme_code))


async def get_multiple_funds(scheme_codes: List[str]) -> Dict[str, Optional[Dict]]:
    """
    Fetch NAV for multiple funds in parallel
    
    Args:
        scheme_codes: List of AMFI scheme codes
        
    Returns:
        Dict mapping scheme_code to fund data
    """
    import asyncio
    
    results = await asyncio.gather(
        *[get_mutual_fund_nav(code) for code in scheme_codes],
        return_exceptions=True
    )
    
    return {
        code: result if not isinstance(result, Exception) else None
        for code, result in zip(scheme_codes, results)
    }


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test search
        print("Searching for 'SBI Bluechip'...")
        results = await search_mutual_fund("SBI Bluechip")
        if results:
            print(f"Found {len(results)} funds")
            for i, fund in enumerate(results[:3], 1):
                print(f"{i}. {fund.get('schemeName')} (Code: {fund.get('schemeCode')})")
        
        # Test NAV fetch by name
        print("\nFetching NAV for HDFC Flexi Cap...")
        fund = await get_mutual_fund_by_name("HDFC Flexi Cap")
        if fund:
            print(f"Name: {fund['scheme_name']}")
            print(f"NAV: ₹{fund['nav']:.4f} (as of {fund['date']})")
            print(f"Category: {fund['scheme_category']}")
    
    asyncio.run(test())
