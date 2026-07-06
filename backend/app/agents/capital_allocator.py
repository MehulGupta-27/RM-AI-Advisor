"""
Capital Allocator Agent - Specific Stock/MF/Commodity Selection with Amount Allocation
Translates percentage allocations into specific instruments with exact rupee amounts
"""

from typing import Dict, List, Optional
from app.llm.groq_client import get_groq_client


async def allocate_capital_to_instruments(
    advisor_output: Dict,
    market_data: Dict,
    client_profile: Dict,
    investment_amount: Optional[float],
    goal: Optional[str],
    time_period: Optional[str],
    risk_factor: str
) -> Dict:
    """
    Convert percentage allocations into specific instruments with rupee amounts.
    
    Input: advisor_output with allocation percentages
    Output: Detailed capital allocation across specific stocks, MFs, and commodities
    
    This agent provides the "how much to invest where" breakdown.
    """
    
    llm = get_groq_client()
    
    # Extract allocation percentages
    allocation = advisor_output.get("allocation", {})
    equity_pct = allocation.get("equity", 0)
    mf_pct = allocation.get("mutual_funds", 0)
    gold_pct = allocation.get("gold", 0)
    debt_pct = allocation.get("fd_debt", 0)
    
    # Calculate rupee amounts if investment_amount is provided
    total_amount = investment_amount or 500000  # Default fallback
    
    equity_amount = (equity_pct / 100) * total_amount
    mf_amount = (mf_pct / 100) * total_amount
    gold_amount = (gold_pct / 100) * total_amount
    debt_amount = (debt_pct / 100) * total_amount
    
    # Get live prices from market_data
    stock_prices = {}
    if market_data:
        for key, data in market_data.items():
            if 'price' in data:
                stock_prices[key] = data['price']
    
    # Build prompt for capital allocator
    prompt = f"""You are a Capital Allocation Specialist. Given the high-level allocation percentages, 
you must provide SPECIFIC INSTRUMENT RECOMMENDATIONS with EXACT RUPEE AMOUNTS.

CLIENT PROFILE:
- Name: {client_profile.get('client_name')}
- Age: {client_profile.get('age')}
- Risk Factor: {risk_factor}
- Goal: {goal or 'Wealth Creation'}
- Time Horizon: {time_period or 'Not specified'}

TOTAL INVESTMENT AMOUNT: ₹{total_amount:,.0f}

HIGH-LEVEL ALLOCATION (from Investment Advisor):
- Equity: {equity_pct}% → ₹{equity_amount:,.0f}
- Mutual Funds: {mf_pct}% → ₹{mf_amount:,.0f}
- Gold: {gold_pct}% → ₹{gold_amount:,.0f}
- FD/Debt: {debt_pct}% → ₹{debt_amount:,.0f}

LIVE MARKET PRICES AVAILABLE:
{stock_prices if stock_prices else "No live prices available - use representative amounts"}

YOUR TASK:
Provide a detailed breakdown of SPECIFIC STOCKS, MUTUAL FUNDS, and COMMODITIES to invest in, 
along with EXACT AMOUNTS for each instrument.

RULES:
1. For EQUITY (₹{equity_amount:,.0f}):
   - Recommend 3-5 specific stocks (NSE listed)
   - Allocate exact rupee amount to each stock
   - Provide brief rationale for each pick (sector, fundamentals, growth potential)
   - Consider: Blue chips (40-50%), Mid caps (30-40%), Small caps (10-20%)
   - Use live prices if available to calculate number of shares

2. For MUTUAL FUNDS (₹{mf_amount:,.0f}):
   - Recommend 2-3 specific mutual fund schemes (Indian MFs)
   - Allocate exact amount or SIP amount per month
   - Mix: Large cap fund (50%), Mid/Small cap fund (30%), Sector/Thematic (20%)
   - Specify fund house and scheme name

3. For GOLD (₹{gold_amount:,.0f}):
   - Recommend specific instruments: Sovereign Gold Bonds (SGBs), Gold ETFs, Digital Gold
   - Allocate amounts across instruments
   - Mention current gold price: ₹{market_data.get('GOLD', {}).get('price', '~75,000')}/10g

4. For FD/DEBT (₹{debt_amount:,.0f}):
   - Recommend: Fixed Deposits (banks), Debt Mutual Funds, or Govt Bonds
   - Suggest tenure based on goal
   - Mention indicative interest rates (7-8% for FDs)

OUTPUT FORMAT (JSON):
{{
  "equity": {{
    "total_amount": {equity_amount},
    "instruments": [
      {{
        "name": "Reliance Industries Ltd (RELIANCE.NS)",
        "sector": "Diversified",
        "amount": 50000,
        "shares": 38,
        "current_price": 1304,
        "rationale": "Market leader with presence in telecom, retail, and energy. Strong cash flows."
      }},
      ...
    ]
  }},
  "mutual_funds": {{
    "total_amount": {mf_amount},
    "instruments": [
      {{
        "name": "HDFC Top 100 Fund - Direct Growth",
        "category": "Large Cap",
        "amount": 40000,
        "sip_monthly": 5000,
        "rationale": "Consistent performer tracking top 100 companies. Low expense ratio."
      }},
      ...
    ]
  }},
  "gold": {{
    "total_amount": {gold_amount},
    "instruments": [
      {{
        "name": "Sovereign Gold Bonds (SGB)",
        "amount": 50000,
        "grams": 6.5,
        "rationale": "Govt backed, 2.5% interest, tax benefits on maturity after 8 years."
      }},
      {{
        "name": "Gold ETF (e.g., Nippon India Gold ETF)",
        "amount": 25000,
        "rationale": "High liquidity, can sell anytime, tracks gold prices accurately."
      }}
    ]
  }},
  "debt": {{
    "total_amount": {debt_amount},
    "instruments": [
      {{
        "name": "Fixed Deposit - SBI/HDFC Bank",
        "amount": 50000,
        "tenure": "3 years",
        "rate": "7.5%",
        "rationale": "Capital protection, predictable returns, suitable for emergency fund portion."
      }},
      {{
        "name": "ICICI Prudential Banking & PSU Debt Fund",
        "amount": 40000,
        "rationale": "Better than FDs over long term, invests in high-quality bonds."
      }}
    ]
  }},
  "summary": {{
    "total_instruments": 12,
    "monthly_commitment": 15000,
    "one_time_investment": 485000,
    "diversification_score": "High - 4 asset classes, 12 instruments across sectors"
  }}
}}

Be specific with instrument names, use Indian instruments only, and ensure amounts add up exactly.
"""
    
    try:
        response = await llm.ainvoke(prompt)
        
        # Try to parse JSON from response
        import json
        import re
        
        # Extract JSON from response
        content = response.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            allocation_detail = json.loads(json_match.group())
            return {
                "success": True,
                "capital_allocation": allocation_detail,
                "raw_response": content
            }
        else:
            # Fallback: return structured text
            return {
                "success": True,
                "capital_allocation": None,
                "raw_response": content
            }
            
    except Exception as e:
        print(f"Capital allocator error: {e}")
        return {
            "success": False,
            "error": str(e),
            "capital_allocation": None
        }


def format_capital_allocation(capital_allocation: Optional[Dict], total_amount: float) -> str:
    """
    Format the capital allocation output into readable markdown.
    """
    if not capital_allocation:
        return "\n## Investment Breakdown\n\n(Detailed breakdown unavailable - using percentage allocations only)\n"
    
    output = f"\n## Detailed Investment Breakdown (Total: ₹{total_amount:,.0f})\n\n"
    
    # Equity
    if "equity" in capital_allocation:
        equity = capital_allocation["equity"]
        output += f"### 💼 Equity Allocation: ₹{equity.get('total_amount', 0):,.0f}\n\n"
        for inst in equity.get("instruments", []):
            output += f"**{inst['name']}** - {inst['sector']}\n"
            output += f"- Amount: ₹{inst['amount']:,.0f}"
            if 'shares' in inst:
                output += f" ({inst['shares']} shares @ ₹{inst.get('current_price', 0)})"
            output += f"\n- Why: {inst['rationale']}\n\n"
    
    # Mutual Funds
    if "mutual_funds" in capital_allocation:
        mf = capital_allocation["mutual_funds"]
        output += f"### 📊 Mutual Fund Allocation: ₹{mf.get('total_amount', 0):,.0f}\n\n"
        for inst in mf.get("instruments", []):
            output += f"**{inst['name']}** - {inst['category']}\n"
            output += f"- Lumpsum: ₹{inst['amount']:,.0f}"
            if 'sip_monthly' in inst:
                output += f" OR SIP: ₹{inst['sip_monthly']}/month"
            output += f"\n- Why: {inst['rationale']}\n\n"
    
    # Gold
    if "gold" in capital_allocation:
        gold = capital_allocation["gold"]
        output += f"### 🥇 Gold Allocation: ₹{gold.get('total_amount', 0):,.0f}\n\n"
        for inst in gold.get("instruments", []):
            output += f"**{inst['name']}**\n"
            output += f"- Amount: ₹{inst['amount']:,.0f}"
            if 'grams' in inst:
                output += f" (~{inst['grams']}g)"
            output += f"\n- Why: {inst['rationale']}\n\n"
    
    # Debt
    if "debt" in capital_allocation:
        debt = capital_allocation["debt"]
        output += f"### 🏦 Debt/FD Allocation: ₹{debt.get('total_amount', 0):,.0f}\n\n"
        for inst in debt.get("instruments", []):
            output += f"**{inst['name']}**\n"
            output += f"- Amount: ₹{inst['amount']:,.0f}"
            if 'tenure' in inst:
                output += f" | Tenure: {inst['tenure']}"
            if 'rate' in inst:
                output += f" | Rate: {inst['rate']}"
            output += f"\n- Why: {inst['rationale']}\n\n"
    
    # Summary
    if "summary" in capital_allocation:
        summary = capital_allocation["summary"]
        output += "\n### 📋 Investment Summary\n\n"
        output += f"- **Total Instruments:** {summary.get('total_instruments', 'N/A')}\n"
        output += f"- **Monthly Commitment (SIPs):** ₹{summary.get('monthly_commitment', 0):,.0f}\n"
        output += f"- **One-time Investment:** ₹{summary.get('one_time_investment', 0):,.0f}\n"
        output += f"- **Diversification:** {summary.get('diversification_score', 'Good')}\n\n"
    
    return output
