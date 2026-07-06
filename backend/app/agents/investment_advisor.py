"""
Investment Advisor Agent - Core recommendation engine
LLM-powered, temperature 0.3, structured JSON output
Three modes: full_plan / sector_analysis / stock_analysis
"""

import json
import logging
from typing import Dict, Optional, List
from app.llm.groq_client import get_groq_client
from app.rules.allocation_rules import calculate_ideal_allocation, calculate_sip_suggestion

logger = logging.getLogger(__name__)


def get_advisor_prompt_for_mode(mode: str) -> str:
    """Returns the appropriate prompt based on query type"""
    
    if mode == "full_plan":
        return """You are an expert Indian investment advisor creating a DETAILED personalized portfolio plan.

CLIENT PROFILE:
{client_profile}

CURRENT HOLDINGS:
{holdings}

CURRENT PORTFOLIO:
{portfolio}

INVESTMENT CONTEXT:
- Goal: {goal}
- Time Period: {time_period}
- Query Type: {query_type}

MARKET DATA (live):
{market_summary}

IDEAL ALLOCATION (rule-based reference):
{ideal_allocation}
Base equity: {base_equity}%%, Age adjustment: {age_adj}, Max equity ceiling: {max_equity}%%
SIP suggestion: Rs {sip_suggestion:,.0f}/month (20%% of income)

YOUR TASK - CREATE COMPREHENSIVE PLAN:

1. **Asset Allocation** (must sum to 100%%):
   - Equity %%
   - Mutual Funds %%
   - Gold %%
   - FD/Debt %%
   
2. **Specific Equity Picks** (3-5 stocks):
   - Company name, sector, ticker
   - Suggested investment amount (Rs)
   - Current price from market data
   - WHY this stock (rationale with fundamentals)
   - How it fits client goal and risk profile

3. **Specific Mutual Fund Picks** (2-3 funds):
   - Fund name, category (Large Cap/Mid Cap/ELSS/etc)
   - Lumpsum amount OR Monthly SIP amount
   - WHY this fund (rationale)
   - Tax benefits if applicable

4. **Gold Investment** (specify instruments):
   - Sovereign Gold Bonds (Rs X)
   - Gold ETF (Rs Y)
   - Digital Gold (Rs Z)
   - WHY gold and how much

5. **Debt/FD Investment** (specify instruments):
   - Bank FDs with tenure and rate
   - Debt mutual funds
   - PPF/NSC if tax-saving goal
   - WHY these instruments

6. **Overall Rationale** (200 words):
   - Why this specific mix for client goal
   - Risk alignment explanation
   - Time horizon considerations
   - Expected returns range
   - Diversification strategy

COMPLIANCE RULES (CRITICAL - MUST INCLUDE ALL):
- Allocation must sum to EXACTLY 100%%
- Equity <= {max_equity}%% (hard ceiling for risk tier)
- If age > 60: equity <= 30%%
- SIP <= 30%% of monthly income
- Goal-specific overrides:
  * emergency_fund -> 0%% equity, 100%% liquid
  * retirement -> +5%% gold, -5%% equity
  * home_purchase (< 3 years) -> 0%% equity
  * tax_saving -> MUST include ELSS fund
- Every stock must have live price from market data
- Must explicitly connect to stated {goal} goal

REQUIRED DISCLAIMERS (MUST INCLUDE IN JSON):
You MUST include these in the "disclaimers" array:
1. "IMPORTANT DISCLAIMER: Market-linked instruments (equity, mutual funds, gold) are subject to market risks and DO NOT guarantee returns. Past performance does not indicate future returns."
2. "GOAL ALIGNMENT: This recommendation specifically supports your {goal} goal by [explain how allocation supports goal] over your {time_period} time horizon."
3. "SENIOR REVIEW REQUIRED: This recommendation requires review by a senior advisor before implementation."

If portfolio has >50%% in stocks, also add:
4. "CONCENTRATION ACKNOWLEDGMENT: This portfolio has significant equity exposure. Monitor sector concentration and individual stock weightage."

RETURN DETAILED JSON:
{{
    "allocation": {{
        "equity_pct": 45,
        "mutual_fund_pct": 25,
        "gold_pct": 15,
        "fd_debt_pct": 15
    }},
    "equity_picks": [
        {{
            "ticker": "RELIANCE.NS",
            "sector": "Energy & Petrochemicals",
            "suggested_amount": 150000,
            "current_price": 1304.50,
            "rationale": "Reliance is a diversified conglomerate with strong fundamentals. Recent Q2 results show 12%% YoY revenue growth. P/E of 24.5 is reasonable. Telecom and retail segments provide growth. Suitable for {goal} goal with {time_period} horizon. Adds blue-chip stability to portfolio."
        }},
        {{
            "ticker": "TCS.NS",
            "sector": "Information Technology",
            "suggested_amount": 120000,
            "current_price": 4102.30,
            "rationale": "TCS is the largest IT services company with consistent dividend payout (1.8%% yield). Strong order book, digital transformation deals. Low beta stock suitable for moderate risk. Export revenue provides dollar hedge. Matches {goal} with stable long-term growth."
        }},
        {{
            "ticker": "HDFC.NS",
            "sector": "Banking & Finance",
            "suggested_amount": 100000,
            "current_price": 1685.20,
            "rationale": "Post-merger HDFC Bank is the largest private bank. Asset quality strong with NPA < 1%%. ROE of 18%%+. Benefits from economic growth. Banking sector underweight in current portfolio, adds diversification. {time_period} horizon allows riding market cycles."
        }}
    ],
    "mf_picks": [
        {{
            "scheme_name": "Axis Bluechip Fund",
            "category": "Large Cap Equity",
            "suggested_amount": 150000,
            "sip_per_month": 15000,
            "rationale": "Consistent top-quartile performer over 5 years. Portfolio of 30-40 quality large-caps. Suitable for moderate risk with {time_period} horizon. Can do lumpsum of Rs 150K or monthly SIP of Rs 15K. Large-cap focus aligns with wealth creation goal."
        }},
        {{
            "scheme_name": "Parag Parikh Flexi Cap Fund",
            "category": "Flexi Cap (Multi Cap)",
            "suggested_amount": 100000,
            "sip_per_month": 10000,
            "rationale": "Unique fund with 35%% international exposure (US stocks). Adds global diversification. Managed by experienced team. Flexi-cap approach allows dynamic allocation. Suitable for {goal} with long-term view."
        }}
    ],
    "gold_recommendation": "Allocate Rs 150,000 to gold: Rs 80K in Sovereign Gold Bonds (SGB) for 2.5%% interest + potential price appreciation (NOT GUARANTEED), Rs 50K in Gold ETF for liquidity, Rs 20K in digital gold for easy accumulation. Gold provides hedge against market volatility and inflation protection over {time_period}. DISCLAIMER: Gold prices are subject to market fluctuations and do not guarantee returns.",
    "fd_recommendation": "Allocate Rs 150,000 to debt: Rs 100K in top-rated bank FDs (7-7.5%% for {time_period}), Rs 50K in short-term debt fund for liquidity. Provides stability and capital preservation. Suitable for emergency needs while other investments grow.",
    "rationale": "This comprehensive plan allocates 45%% to equity (3 quality stocks + broad market via MFs) suitable for your {goal} goal and {risk_factor} risk profile. GOAL CONNECTION: This allocation directly supports {goal} by maximizing growth potential through equity while managing risk with debt and gold. Equity allocation within {max_equity}%% ceiling. Time horizon of {time_period} allows riding market cycles. Diversified across sectors (Energy, IT, Banking) and instruments (stocks, MFs, gold, debt). Gold and debt provide downside protection. Expected returns: 10-12%% CAGR over {time_period} (NOT GUARANTEED - market risks apply). Monthly SIP of Rs {sip_suggestion:,.0f} within your income capacity. Portfolio is well-diversified with concentration checks (no single stock > 15%%). Includes defensive plays (TCS, HDFC) and growth plays (Reliance). SECTOR CONCENTRATION: Monitor IT and Banking sector exposure to avoid over-concentration. Aligns with stated goal of {goal}.",
    "disclaimers": [
        "IMPORTANT DISCLAIMER: Market-linked instruments (equity, mutual funds, gold) are subject to market risks and DO NOT guarantee returns. These are NOT risk-free investments. Past performance is not indicative of future returns.",
        "GOAL ALIGNMENT: This recommendation specifically supports your {goal} goal by allocating growth-oriented equity investments balanced with stable debt instruments over your {time_period} time horizon. Expected returns range from 10-12%% CAGR but are not guaranteed.",
        "SENIOR REVIEW REQUIRED: This recommendation requires review by a senior advisor before implementation, especially given the {risk_factor} risk profile.",
        "CONCENTRATION ACKNOWLEDGMENT: This portfolio has significant equity exposure (45%% in stocks + 25%% in equity mutual funds = 70%% total equity). Monitor sector concentration and individual stock weightage to maintain diversification."
    ]
}}

CRITICAL: Make each rationale SPECIFIC with numbers, percentages, and clear reasoning tied to client profile."""
    
    elif mode == "sector_analysis":
        return """You are an expert Indian investment advisor analyzing a specific sector.

CLIENT PROFILE:
{client_profile}

CURRENT HOLDINGS:
{holdings}

SECTOR FOCUS: {sector_name}

MARKET DATA (live sector stocks):
{market_summary}

INVESTMENT CONTEXT:
- Goal: {goal}
- Time Period: {time_period}
- Risk Factor: {risk_factor}

YOUR TASK:
Analyze this sector for the client and recommend 2-3 specific stocks with allocation amounts.
Consider:
1. Sector outlook and why it suits (or does not suit) this client profile
2. Concentration risk (sector should not exceed 30%% for high risk, 20%% medium, 10%% low)
3. Current holdings (do not pile on if already overweight)
4. Stock-specific rationale

Return ONLY valid JSON:
{{
    "sector_name": "Technology",
    "sector_outlook": "Brief outlook for this sector",
    "recommended_stocks": [
        {{"ticker": "TCS.NS", "suggested_amount": 30000, "current_price": 2092.3, "rationale": "..."}}
    ],
    "concentration_warning": "Sector would be X%% of portfolio" or null,
    "rationale": "Why this sector suits or does not suit the client"
}}"""
    
    else:  # stock_analysis
        return '''You are an expert Indian investment advisor providing DETAILED stock analysis.

**CRITICAL**: You MUST return the stock analysis JSON format below. DO NOT return allocation percentages.

CLIENT PROFILE:
{client_profile}

CURRENT HOLDINGS (to check concentration):
{holdings}

CURRENT PORTFOLIO VALUE: {portfolio_value}

STOCK TO ANALYZE: {ticker}

LIVE MARKET DATA:
{market_summary}

INVESTMENT CONTEXT:
- Goal: {goal}
- Time Period: {time_period}  
- Risk Factor: {risk_factor}

YOUR TASK - PROVIDE COMPREHENSIVE ANALYSIS:

1. **Fundamental Analysis**:
   - Current price, P/E ratio, market cap
   - Recent performance (1-year gain/loss from market data)
   - Revenue growth, profit margins
   - Competitive position

2. **Client Fit Analysis**:
   - Does risk profile match (Low/Medium/High)?
   - Does time horizon match investment needs?
   - Does it align with stated goal?
   - Current sector exposure in portfolio

3. **Recommendation**:
   - BUY: Good opportunity, suitable for client, fair price
   - HOLD: Marginal fit or timing is not ideal
   - AVOID: High risk for client or overvalued

4. **Investment Amount** (if BUY):
   - Specific rupee amount (e.g., Rs 250,000)
   - Should not exceed 15%% of portfolio value
   - Consider client existing exposure

5. **Risk Assessment**:
   - List 3-4 specific risk factors
   - Sector-specific risks
   - Market volatility considerations

6. **Portfolio Impact**:
   - What %% of portfolio would this be?
   - Does it add diversification?
   - Concentration risk check

RETURN THIS EXACT JSON (NO OTHER FORMAT):
{{
    "ticker": "{ticker}",
    "recommendation": "YES" or "NO",
    "suggested_amount": 250000,
    "suggested_time_horizon": "5-7 years",
    "current_price": 456.75,
    "one_year_return": "+15.2%" or "-8.5%",
    "key_reasons": [
        "Reason 1 why YES or NO - be specific with numbers from market data",
        "Reason 2 - relate to client's {risk_factor} risk profile",
        "Reason 3 - mention portfolio fit and concentration",
        "Reason 4 - market timing and valuation perspective"
    ],
    "detailed_rationale": "Write a comprehensive 250-350 word analysis: (1) Stock fundamentals with SPECIFIC numbers from market data (price, 1-year return, trends) (2) How it matches or DOES NOT match client's risk profile, goal, and time horizon (3) Current market timing - is entry point attractive? (4) Portfolio impact - diversification vs concentration (5) Expected returns and specific risks (6) Clear final verdict with reasoning",
    "risks": [
        "Specific risk factor 1 with numbers/context",
        "Specific risk factor 2 with numbers/context", 
        "Specific risk factor 3 with numbers/context",
        "Specific risk factor 4 with numbers/context"
    ],
    "portfolio_impact": "This investment of Rs X would represent Y%% of your Rs {portfolio_value:,.0f} portfolio. Currently you have Z%% in [sector] sector. This would [add diversification / increase concentration].",
    "alternative_suggestion": "If NO: suggest better option. If YES: suggest complementary investments for balance."
}}

CRITICAL REMINDERS:
- recommendation MUST be "YES" or "NO" (not BUY/HOLD/AVOID)
- Use ACTUAL numbers from market_summary
- If stock already held, mention current position
- If would exceed 15%% portfolio limit, recommend NO
- If doesn't match {risk_factor} risk or {goal} goal, recommend NO
- detailed_rationale must be 250+ words with specific reasoning
'''


async def generate_investment_advice(
    mode: str,
    client_profile: Dict,
    holdings: List[Dict],
    portfolio: Dict,
    market_summary: str,
    goal: str,
    time_period: Optional[str],
    query_type: str,
    ticker: Optional[str] = None,
    sector_name: Optional[str] = None,
    compliance_feedback: Optional[Dict] = None
) -> Dict:
    """
    Generate investment advice in one of three modes.
    If compliance_feedback is provided, this is a retry attempt.
    """
    try:
        groq = get_groq_client()
        
        # Calculate ideal allocation for reference
        age = client_profile.get("age", 40)
        risk_factor = client_profile.get("risk_factor", "MEDIUM")
        ideal_allocation = calculate_ideal_allocation(age, risk_factor, goal)
        
        # Calculate base equity and adjustments for transparency
        from app.rules.allocation_rules import BASE_EQUITY_BY_RISK, get_age_adjustment, MAX_EQUITY_BY_RISK
        base_equity = BASE_EQUITY_BY_RISK.get(risk_factor.lower(), 45)
        age_adj = get_age_adjustment(age)
        max_equity = MAX_EQUITY_BY_RISK.get(risk_factor.lower(), 58)
        
        # Calculate SIP
        monthly_income = client_profile.get("monthly_income")
        sip_suggestion = calculate_sip_suggestion(monthly_income)
        
        # Format client profile
        monthly_income_display = monthly_income if monthly_income else 0
        profile_str = f"""
Name: {client_profile.get('client_name')}
Age: {age}
Risk Factor: {risk_factor}
Monthly Income: Rs {monthly_income_display:,.0f}
Category: {client_profile.get('category')}
City: {client_profile.get('city')}
"""
        
        # Format holdings
        holdings_str = "\n".join([
            f"- {h.get('asset_name')}: Rs {h.get('current_value', 0):,.0f} ({h.get('asset_class')})"
            for h in holdings[:10]  # Limit to top 10
        ]) if holdings else "No existing holdings"
        
        # Format portfolio
        portfolio_str = f"""
Total Value: Rs {portfolio.get('current_portfolio_value', 0):,.0f}
Return: {portfolio.get('return_percentage', 0):.1f}%%
"""
        
        # Get appropriate prompt
        prompt_template = get_advisor_prompt_for_mode(mode)
        
        # Format the prompt with error handling
        try:
            prompt = prompt_template.format(
                client_profile=profile_str,
                holdings=holdings_str,
                portfolio=portfolio_str,
                portfolio_value=portfolio.get('current_portfolio_value', 0),
                market_summary=market_summary,
                goal=goal,
                time_period=time_period or "Not specified",
                query_type=query_type,
                ideal_allocation=json.dumps(ideal_allocation, indent=2),
                base_equity=base_equity,
                age_adj=age_adj,
                max_equity=max_equity,
                sip_suggestion=sip_suggestion,
                risk_factor=risk_factor,
                ticker=ticker or "Not specified",
                sector_name=sector_name or "Not specified"
            )
        except Exception as format_error:
            print(f"[ERROR] Format string error: {format_error}")
            print(f"[ERROR] Mode: {mode}")
            print(f"[ERROR] Error type: {type(format_error).__name__}")
            import traceback
            traceback.print_exc()
            # Return fallback
            raise ValueError(f"invalid format string")
        
        # Add compliance feedback if this is a retry
        if compliance_feedback:
            prompt += f"\n\nCOMPLIANCE FEEDBACK (FIX THESE ISSUES):\n"
            prompt += f"Issues: {json.dumps(compliance_feedback.get('issues', []))}\n"
            prompt += f"Suggestions: {compliance_feedback.get('suggestions_to_advisor', '')}\n"
        
        # Use LangChain for structured JSON output
        result_text = await groq.structured_output(
            system_prompt="You are an investment advisor. Return ONLY valid JSON.",
            user_message=prompt,
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse JSON
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        
        # POST-PROCESSING: Inject compliance-required fields
        if mode == "full_plan":
            # Ensure disclaimers have required compliance language
            if "disclaimers" not in result or not result["disclaimers"]:
                result["disclaimers"] = []
            
            # Add required disclaimers if missing
            required_disclaimers = [
                f"IMPORTANT: Market-linked instruments (equity, mutual funds, gold) are subject to market risks and DO NOT guarantee returns. These are NOT risk-free investments.",
                f"GOAL CONNECTION: This recommendation specifically supports your {goal} goal through diversified asset allocation over your {time_period} time horizon.",
                f"REVIEW REQUIRED: This recommendation requires review by a senior advisor before implementation."
            ]
            
            for req_disc in required_disclaimers:
                # Check if similar disclaimer exists
                has_similar = any(
                    ("market risk" in disc.lower() and "DO NOT guarantee" in req_disc) or
                    ("goal" in disc.lower() and "GOAL CONNECTION" in req_disc) or
                    ("review" in disc.lower() and "REVIEW REQUIRED" in req_disc)
                    for disc in result["disclaimers"]
                )
                if not has_similar:
                    result["disclaimers"].append(req_disc)
            
            # Add sector concentration warning to rationale if not present
            if "rationale" in result:
                if "concentration" not in result["rationale"].lower():
                    result["rationale"] += " SECTOR CONCENTRATION NOTE: Please monitor sector exposure to avoid over-concentration in any single sector."
                if "NOT GUARANTEED" not in result["rationale"] and "not guaranteed" not in result["rationale"].lower():
                    result["rationale"] += " RISK DISCLAIMER: All returns mentioned are NOT GUARANTEED and subject to market conditions."
            
            # Add concentration warning to gold recommendation if mentions "appreciation"
            if "gold_recommendation" in result:
                if "appreciation" in result["gold_recommendation"].lower() and "NOT GUARANTEED" not in result["gold_recommendation"]:
                    result["gold_recommendation"] += " DISCLAIMER: Price appreciation is NOT GUARANTEED."
        
        # POST-PROCESSING: Ensure stock_analysis returns correct format
        if mode == "stock_analysis":
            # If LLM returned allocation format instead of stock analysis format
            if "allocation" in result and ticker:
                print(f"[WARNING] LLM returned allocation format for stock analysis. Converting...")
                result = {
                    "ticker": ticker,
                    "recommendation": "HOLD",
                    "suggested_amount": None,
                    "current_price": 0,
                    "rationale": result.get("rationale", "Stock analysis: Consider current market conditions and client risk profile."),
                    "risks": ["Market volatility", "Sector-specific risks", "Concentration risk"],
                    "concentration_check": f"Portfolio concentration check pending for {ticker}"
                }
            
            # Ensure all required fields exist
            if "recommendation" not in result:
                result["recommendation"] = "HOLD"
            if "risks" not in result or not result["risks"]:
                result["risks"] = ["Market volatility", "Company-specific risks", "Sector risks"]
            if "concentration_check" not in result:
                result["concentration_check"] = "Portfolio impact analysis pending"
        
        logger.info(f"Investment advisor result ({mode}): {json.dumps(result, indent=2)[:500]}")
        return result
        
    except Exception as e:
        print(f"[ERROR] Investment advisor outer exception: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        logger.error(f"Investment advisor error: {e}")
        # Return minimal fallback
        return {
            "error": str(e),
            "allocation": ideal_allocation,
            "rationale": "Error generating detailed advice. Please try again."
        }

