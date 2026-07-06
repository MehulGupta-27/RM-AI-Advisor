"""
Stock Universe Configurations
Defines watchlists for screener queries
"""

# Nifty 50 Constituents (as of 2024)
# Source: NSE India official list
NIFTY_50_CONSTITUENTS = [
    # Banking & Financial Services
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN", "INDUSINDBK",
    
    # Information Technology
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM", "LTIM",
    
    # Energy & Petrochemicals
    "RELIANCE", "ONGC", "BPCL", "IOC",
    
    # FMCG
    "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA",
    
    # Automotive
    "MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "EICHERMOT",
    
    # Pharmaceuticals
    "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB",
    
    # Capital Goods & Infrastructure
    "LT", "ULTRACEMCO", "ADANIPORTS", "GRASIM",
    
    # Telecom
    "BHARTIARTL",
    
    # Metals & Mining
    "TATASTEEL", "HINDALCO", "JSWSTEEL", "COALINDIA",
    
    # Cement
    "SHREECEM",
    
    # Consumer Durables
    "TITAN", "BAJAJFINSV",
    
    # Power
    "POWERGRID", "NTPC",
    
    # Others
    "HEROMOTOCO", "ASIANPAINT", "ADANIENT"
]

# Bank Nifty Constituents
BANK_NIFTY_CONSTITUENTS = [
    "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN",
    "INDUSINDBK", "BANDHANBNK", "FEDERALBNK", "IDFCFIRSTB",
    "PNB", "BANKBARODA", "AUBANK"
]

# Nifty IT Constituents
NIFTY_IT_CONSTITUENTS = [
    "TCS", "INFY", "WIPRO", "HCLTECH", "TECHM",
    "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "LTTS"
]


def get_universe(name: str = "nifty50") -> list:
    """
    Get stock universe by name.
    
    Args:
        name: Universe identifier (nifty50, banknifty, niftyit)
        
    Returns:
        List of ticker symbols (NSE format, no .NS suffix)
    """
    universes = {
        "nifty50": NIFTY_50_CONSTITUENTS,
        "nifty_50": NIFTY_50_CONSTITUENTS,
        "banknifty": BANK_NIFTY_CONSTITUENTS,
        "bank_nifty": BANK_NIFTY_CONSTITUENTS,
        "niftyit": NIFTY_IT_CONSTITUENTS,
        "nifty_it": NIFTY_IT_CONSTITUENTS,
    }
    
    return universes.get(name.lower(), NIFTY_50_CONSTITUENTS)
