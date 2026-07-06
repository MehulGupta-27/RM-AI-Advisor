"""
Stock/MF Selector Agent - Determines which market data to fetch
LLM-powered, temperature 0.2, structured JSON output
"""

import json
import logging
from typing import Dict, Optional
from app.llm.groq_client import get_groq_client

logger = logging.getLogger(__name__)


STOCK_SELECTOR_PROMPT = """You are a stock and mutual fund selector for an Indian investment advisory system.

Given a client profile and their investment query, determine:
1. Which stocks (NSE tickers) should be fetched for live pricing
2. The relevant sector name if this is a sector-focused query
3. The risk level of recommendations to consider
4. Which mutual fund categories to include
5. Your rationale

CLIENT PROFILE:
{client_profile}

QUERY DETAILS:
- Goal: {goal}
- Query Type: {query_type}
- Ticker mentioned: {ticker}
- Time Period: {time_period}

SECTOR MAPPING (use these NSE stock codes):
- Technology: TCS.NS, INFY.NS, WIPRO.NS, HCLTECH.NS
- Banking: HDFCBANK.NS, ICICIBANK.NS, SBIN.NS, AXISBANK.NS
- Energy: RELIANCE.NS, ONGC.NS, BPCL.NS, POWERGRID.NS
- Pharma: SUNPHARMA.NS, DRREDDY.NS, CIPLA.NS, DIVISLAB.NS
- Auto: MARUTI.NS, TATAMOTORS.NS, M&M.NS, BAJAJ-AUTO.NS
- FMCG: HINDUNILVR.NS, ITC.NS, NESTLEIND.NS, BRITANNIA.NS
- Infrastructure: LT.NS, ULTRACEMCO.NS, ADANIPORTS.NS

MUTUAL FUND CATEGORIES BY GOAL:
- wealth_creation: Large Cap, Multi Cap, Flexi Cap
- retirement: Balanced Advantage, Hybrid, Debt funds
- tax_saving: ELSS (tax-saving equity funds)
- child_education: Balanced Hybrid, Children's funds
- home_purchase: Short Duration Debt, Liquid funds
- emergency_fund: Liquid funds, Ultra Short Duration

RISK LEVEL MAPPING:
- Client risk_factor HIGH → can suggest mid/small cap, sectoral funds
- Client risk_factor MEDIUM → large cap, diversified multi-cap
- Client risk_factor LOW → debt funds, conservative hybrid only

QUERY TYPE LOGIC:
- stock: User wants analysis of a specific stock → return that ticker only
- sector: User wants sector exposure → return 3-4 stocks from that sector
- general: Full portfolio plan → return diversified picks across 2-3 sectors

Return ONLY valid JSON, no markdown:
{{
    "stocks_to_fetch": ["TICKER1.NS", "TICKER2.NS"],
    "sector_name": "Technology" or null,
    "risk_level": "conservative" | "moderate" | "aggressive",
    "mf_categories": ["Large Cap", "ELSS"],
    "rationale": "Brief explanation of why these picks suit the client"
}}"""


async def select_stocks_and_mf(
    client_profile: Dict,
    goal: str,
    query_type: str,
    ticker: Optional[str],
    time_period: Optional[str]
) -> Dict:
    """
    Determine which stocks and MF categories to fetch based on client profile and query.
    """
    try:
        groq = get_groq_client()
        
        # Format client profile concisely
        profile_summary = f"""
Name: {client_profile.get('client_name', 'Unknown')}
Age: {client_profile.get('age', 'Unknown')}
Risk Factor: {client_profile.get('risk_factor', 'MEDIUM')}
Monthly Income: ₹{client_profile.get('monthly_income', 0):,.0f}
Portfolio Value: ₹{client_profile.get('current_portfolio_value', 0):,.0f}
"""
        
        prompt = STOCK_SELECTOR_PROMPT.format(
            client_profile=profile_summary,
            goal=goal or "wealth_creation",
            query_type=query_type,
            ticker=ticker or "None",
            time_period=time_period or "Not specified"
        )
        
        # Use LangChain for structured JSON output
        result_text = await groq.structured_output(
            system_prompt="You are a stock and mutual fund selector. Return ONLY valid JSON.",
            user_message=prompt,
            temperature=0.2
        )
        
        # Parse JSON
        # Remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        
        logger.info(f"Stock selector result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Stock selector error: {e}")
        # Fallback to conservative defaults
        return {
            "stocks_to_fetch": ["NIFTY50.NS"],
            "sector_name": None,
            "risk_level": "moderate",
            "mf_categories": ["Large Cap"],
            "rationale": "Using default conservative selection due to selector error"
        }
