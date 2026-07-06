"""
Ticker to Sector Mapping
Maps NSE stock tickers to their industry sectors
Used for diversification analysis and sector concentration checks
"""

from typing import Dict, List


# Comprehensive ticker→sector mapping for major NSE stocks
TICKER_SECTOR_MAP = {
    # Information Technology
    "TCS": "Information Technology",
    "INFY": "Information Technology",
    "WIPRO": "Information Technology",
    "HCLTECH": "Information Technology",
    "TECHM": "Information Technology",
    "LTIM": "Information Technology",
    "PERSISTENT": "Information Technology",
    "COFORGE": "Information Technology",
    "MPHASIS": "Information Technology",
    "LTTS": "Information Technology",
    
    # Banking & Financial Services
    "HDFCBANK": "Banking & Financial Services",
    "ICICIBANK": "Banking & Financial Services",
    "KOTAKBANK": "Banking & Financial Services",
    "AXISBANK": "Banking & Financial Services",
    "SBIN": "Banking & Financial Services",
    "INDUSINDBK": "Banking & Financial Services",
    "BANDHANBNK": "Banking & Financial Services",
    "FEDERALBNK": "Banking & Financial Services",
    "IDFCFIRSTB": "Banking & Financial Services",
    "PNB": "Banking & Financial Services",
    "BANKBARODA": "Banking & Financial Services",
    "AUBANK": "Banking & Financial Services",
    "BAJFINANCE": "Banking & Financial Services",
    "BAJAJFINSV": "Banking & Financial Services",
    "HDFC": "Banking & Financial Services",
    
    # Energy & Petrochemicals
    "RELIANCE": "Energy & Petrochemicals",
    "ONGC": "Energy & Petrochemicals",
    "BPCL": "Energy & Petrochemicals",
    "IOC": "Energy & Petrochemicals",
    "GAIL": "Energy & Petrochemicals",
    "HINDPETRO": "Energy & Petrochemicals",
    
    # FMCG (Fast Moving Consumer Goods)
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "DABUR": "FMCG",
    "MARICO": "FMCG",
    "GODREJCP": "FMCG",
    "COLPAL": "FMCG",
    
    # Automotive
    "MARUTI": "Automotive",
    "M&M": "Automotive",
    "TATAMOTORS": "Automotive",
    "BAJAJ-AUTO": "Automotive",
    "EICHERMOT": "Automotive",
    "HEROMOTOCO": "Automotive",
    "BOSCHLTD": "Automotive",
    "MOTHERSON": "Automotive",
    
    # Pharmaceuticals
    "SUNPHARMA": "Pharmaceuticals",
    "DRREDDY": "Pharmaceuticals",
    "CIPLA": "Pharmaceuticals",
    "DIVISLAB": "Pharmaceuticals",
    "LUPIN": "Pharmaceuticals",
    "BIOCON": "Pharmaceuticals",
    "TORNTPHARM": "Pharmaceuticals",
    "ALKEM": "Pharmaceuticals",
    
    # Capital Goods & Infrastructure
    "LT": "Capital Goods & Infrastructure",
    "ULTRACEMCO": "Capital Goods & Infrastructure",
    "ADANIPORTS": "Capital Goods & Infrastructure",
    "GRASIM": "Capital Goods & Infrastructure",
    "ABB": "Capital Goods & Infrastructure",
    "SIEMENS": "Capital Goods & Infrastructure",
    "CUMMINSIND": "Capital Goods & Infrastructure",
    
    # Telecommunications
    "BHARTIARTL": "Telecommunications",
    "TATACOMM": "Telecommunications",
    
    # Metals & Mining
    "TATASTEEL": "Metals & Mining",
    "HINDALCO": "Metals & Mining",
    "JSWSTEEL": "Metals & Mining",
    "COALINDIA": "Metals & Mining",
    "VEDL": "Metals & Mining",
    "NMDC": "Metals & Mining",
    "HINDZINC": "Metals & Mining",
    
    # Cement
    "SHREECEM": "Cement",
    "AMBUJACEM": "Cement",
    "ACC": "Cement",
    "RAMCOCEM": "Cement",
    
    # Consumer Durables
    "TITAN": "Consumer Durables",
    "VOLTAS": "Consumer Durables",
    "HAVELLS": "Consumer Durables",
    "DIXON": "Consumer Durables",
    
    # Paints & Chemicals
    "ASIANPAINT": "Paints & Chemicals",
    "PIDILITIND": "Paints & Chemicals",
    "BERGEPAINT": "Paints & Chemicals",
    
    # Power & Utilities
    "POWERGRID": "Power & Utilities",
    "NTPC": "Power & Utilities",
    "TATAPOWER": "Power & Utilities",
    "ADANIGREEN": "Power & Utilities",
    "ADANIPOWER": "Power & Utilities",
    
    # Diversified Conglomerates
    "ADANIENT": "Diversified Conglomerates",
    "TATA": "Diversified Conglomerates",
}


def get_sector(ticker: str) -> str:
    """
    Get sector for a ticker.
    
    Args:
        ticker: NSE ticker symbol (e.g., "TCS", "RELIANCE")
        
    Returns:
        Sector name, or "Other" if ticker not mapped
    """
    # Normalize ticker (uppercase, remove .NS suffix if present)
    ticker_normalized = ticker.upper().replace(".NS", "")
    return TICKER_SECTOR_MAP.get(ticker_normalized, "Other")


def get_sector_breakdown(holdings: List[Dict], total_portfolio_value: float = None) -> Dict[str, Dict]:
    """
    Calculate sector-wise breakdown of stock holdings.
    
    Args:
        holdings: List of holding dicts from database
        total_portfolio_value: Total portfolio value for percentage calculation
        
    Returns:
        Dict of {sector: {count, total_value, percentage, stocks}}
    """
    sector_breakdown = {}
    stock_holdings_value = 0
    
    # First pass: aggregate by sector (only for stocks)
    for holding in holdings:
        if holding.get('asset_type') == 'stock':
            ticker = holding.get('asset_name', '')
            sector = get_sector(ticker)
            value = float(holding.get('current_value', 0))
            stock_holdings_value += value
            
            if sector not in sector_breakdown:
                sector_breakdown[sector] = {
                    'count': 0,
                    'total_value': 0,
                    'percentage': 0,
                    'stocks': []
                }
            
            sector_breakdown[sector]['count'] += 1
            sector_breakdown[sector]['total_value'] += value
            sector_breakdown[sector]['stocks'].append({
                'ticker': ticker,
                'value': value
            })
    
    # Second pass: calculate percentages
    base_value = float(total_portfolio_value) if total_portfolio_value else stock_holdings_value
    if base_value > 0:
        for sector in sector_breakdown:
            sector_breakdown[sector]['percentage'] = round(
                (sector_breakdown[sector]['total_value'] / base_value) * 100.0,
                2
            )
    
    return sector_breakdown


def check_sector_concentration(
    holdings: List[Dict],
    total_portfolio_value: float,
    risk_factor: str = "MEDIUM"
) -> List[str]:
    """
    Check for sector concentration violations.
    
    Args:
        holdings: List of holding dicts
        total_portfolio_value: Total portfolio value
        risk_factor: Client risk factor (HIGH/MEDIUM/LOW)
        
    Returns:
        List of concentration warning strings
    """
    # Sector concentration limits by risk tier
    SECTOR_LIMITS = {
        "high": 40,    # High risk: max 40% in any sector
        "medium": 30,  # Medium risk: max 30% in any sector
        "low": 20      # Low risk: max 20% in any sector
    }
    
    sector_limit = SECTOR_LIMITS.get(risk_factor.lower(), 30)
    
    # Get sector breakdown
    sector_breakdown = get_sector_breakdown(holdings, total_portfolio_value)
    
    # Check for violations
    warnings = []
    for sector, data in sector_breakdown.items():
        if data['percentage'] > sector_limit:
            stock_list = ", ".join([s['ticker'] for s in data['stocks'][:3]])
            if len(data['stocks']) > 3:
                stock_list += f" and {len(data['stocks']) - 3} more"
            
            warnings.append(
                f"Sector '{sector}' concentration at {data['percentage']:.1f}% "
                f"exceeds {sector_limit}% limit for {risk_factor} risk "
                f"({stock_list})"
            )
    
    return warnings


def get_stocks_by_sector(sector: str) -> List[str]:
    """
    Get all tickers in a given sector.
    
    Args:
        sector: Sector name (e.g., "Information Technology")
        
    Returns:
        List of ticker symbols in that sector
    """
    return [
        ticker for ticker, sec in TICKER_SECTOR_MAP.items()
        if sec == sector
    ]


def get_all_sectors() -> List[str]:
    """Get list of all unique sectors."""
    return sorted(set(TICKER_SECTOR_MAP.values()))


# Testing
if __name__ == "__main__":
    print("Sector Mapping Utility\n")
    
    # Test 1: Get sector for tickers
    test_tickers = ["TCS", "RELIANCE", "HDFCBANK", "MARUTI", "UNKNOWN"]
    print("1. Ticker to Sector Mapping:")
    for ticker in test_tickers:
        sector = get_sector(ticker)
        print(f"   {ticker} → {sector}")
    
    # Test 2: Mock holdings breakdown
    mock_holdings = [
        {"asset_type": "stock", "asset_name": "TCS", "current_value": 100000},
        {"asset_type": "stock", "asset_name": "INFY", "current_value": 80000},
        {"asset_type": "stock", "asset_name": "HDFCBANK", "current_value": 120000},
        {"asset_type": "stock", "asset_name": "RELIANCE", "current_value": 150000},
        {"asset_type": "mutual_fund", "asset_name": "Some MF", "current_value": 50000},
    ]
    
    print("\n2. Sector Breakdown:")
    breakdown = get_sector_breakdown(mock_holdings, 500000)
    for sector, data in breakdown.items():
        print(f"   {sector}: {data['count']} stocks, {data['percentage']:.1f}% of portfolio")
    
    # Test 3: Concentration check
    print("\n3. Concentration Check (MEDIUM risk):")
    warnings = check_sector_concentration(mock_holdings, 500000, "MEDIUM")
    if warnings:
        for warning in warnings:
            print(f"   ⚠️  {warning}")
    else:
        print("   ✓ No concentration violations")
    
    # Test 4: All sectors
    print(f"\n4. Total Sectors Mapped: {len(get_all_sectors())}")
    print(f"   Total Tickers Mapped: {len(TICKER_SECTOR_MAP)}")
