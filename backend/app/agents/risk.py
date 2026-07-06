"""
Risk Agent - 5-dimension risk scoring
LLM-powered, temperature 0.1, structured JSON output
"""

import json
import logging
from typing import Dict, List, Optional
from app.llm.groq_client import get_groq_client

logger = logging.getLogger(__name__)


RISK_SCORING_PROMPT = """You are a risk assessment specialist for an Indian investment advisory system.

INVESTMENT RECOMMENDATION:
{advisor_output}

CLIENT PROFILE:
Age: {age}
Risk Factor: {risk_factor}
Goal: {goal}
Time Period: {time_period}

CURRENT HOLDINGS:
{holdings_summary}

FALLBACK USED: {used_fallback}

YOUR TASK:
Score this recommendation on 5 risk dimensions (1-10 scale each):

1. MARKET RISK (1-10)
   - Higher equity % → higher score
   - Volatile sectors (tech, small-cap) → higher score
   - Diversified large-cap → lower score
   
2. LIQUIDITY RISK (1-10)
   - ELSS (3-yr lock) → adds risk
   - PPF (15-yr) → adds risk
   - NPS → adds risk
   - More locked capital relative to time horizon → higher score
   
3. CONCENTRATION RISK (1-10)
   - Single stock >15% of portfolio → high score
   - Single sector dominance → high score
   - Well-diversified → low score
   - Check current holdings + new recommendations
   
4. GOAL ALIGNMENT RISK (1-10)
   - Does instrument mix match goal and time horizon?
   - Equity for 6-month goal → very high score
   - Liquid funds for long-term wealth → moderate score
   - Perfect match → low score
   
5. BEHAVIORAL RISK (1-10)
   - Will client stay invested through volatility?
   - HIGH risk_factor + aggressive plan → some risk
   - LOW risk_factor + aggressive plan → very high risk
   - Plan within comfort zone → low risk

OVERALL RISK LEVELS:
- 1-3: LOW
- 4-5: MODERATE
- 6-7: HIGH
- 8-10: VERY_HIGH

SENIOR REVIEW REQUIRED if:
- Overall risk level is HIGH or VERY_HIGH, OR
- Fallback allocation was used (used_fallback=True)

Return ONLY valid JSON:
{{
    "market_risk": 6,
    "liquidity_risk": 4,
    "concentration_risk": 3,
    "goal_alignment_risk": 2,
    "behavioral_risk": 5,
    "overall_risk_score": 4.0,
    "risk_level": "moderate",
    "senior_review_required": false,
    "risk_summary": "Brief narrative explaining the score",
    "key_concerns": ["Concern 1", "Concern 2"]
}}"""


async def assess_risk(
    advisor_output: Dict,
    client_profile: Dict,
    holdings: List[Dict],
    goal: str,
    time_period: Optional[str],
    used_fallback: bool
) -> Dict:
    """
    Assess risk across 5 dimensions.
    Returns risk scores, level, and whether senior review is required.
    """
    try:
        groq = get_groq_client()
        
        age = client_profile.get("age", 40)
        risk_factor = client_profile.get("risk_factor", "MEDIUM")
        
        # Summarize holdings
        holdings_summary = "\n".join([
            f"- {h.get('asset_name')}: ₹{h.get('current_value', 0):,.0f} ({h.get('asset_class')})"
            for h in holdings[:10]
        ]) if holdings else "No existing holdings"
        
        prompt = RISK_SCORING_PROMPT.format(
            advisor_output=json.dumps(advisor_output, indent=2)[:1500],  # Truncate if too long
            age=age,
            risk_factor=risk_factor,
            goal=goal,
            time_period=time_period or "Not specified",
            holdings_summary=holdings_summary,
            used_fallback=used_fallback
        )
        
        # Use LangChain for structured JSON output
        result_text = await groq.structured_output(
            system_prompt="You are a risk assessment specialist. Return ONLY valid JSON.",
            user_message=prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        # Parse JSON
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
        
        result = json.loads(result_text)
        
        # Ensure senior review is required for fallback plans
        if used_fallback:
            result["senior_review_required"] = True
        
        # Ensure senior review for high/very_high risk
        if result.get("risk_level") in ["high", "very_high"]:
            result["senior_review_required"] = True
        
        logger.info(
            f"Risk assessment: {result.get('risk_level')} "
            f"(score: {result.get('overall_risk_score')}), "
            f"senior review: {result.get('senior_review_required')}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        # Conservative fallback
        return {
            "market_risk": 5,
            "liquidity_risk": 5,
            "concentration_risk": 5,
            "goal_alignment_risk": 5,
            "behavioral_risk": 5,
            "overall_risk_score": 5.0,
            "risk_level": "moderate",
            "senior_review_required": True,
            "risk_summary": "Risk assessment unavailable due to error. Manual review recommended.",
            "key_concerns": ["Unable to complete automated risk assessment"]
        }
