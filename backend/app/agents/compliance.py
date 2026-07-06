"""
Compliance Agent - Reviews investment recommendations for regulatory compliance
LLM-powered, temperature 0.1, structured JSON output
Works in tandem with deterministic allocation validator
"""

import json
import logging
from typing import Dict, List, Optional
from app.llm.groq_client import get_groq_client

logger = logging.getLogger(__name__)


COMPLIANCE_PROMPT = """You are a compliance officer for an Indian investment advisory system. 
You review recommendations to ensure they meet regulatory standards while being pragmatic about exact wording.

INVESTMENT RECOMMENDATION TO REVIEW:
{advisor_output}

CLIENT PROFILE:
Age: {age}
Risk Factor: {risk_factor}
Goal: {goal}
Time Period: {time_period}

DETERMINISTIC VALIDATOR RESULTS:
Allocation Valid: {allocation_valid}
Violations Found: {allocation_violations}
Concentration Warnings (non-blocking): {concentration_warnings}

YOUR TASK:
Review this recommendation for SOFT COMPLIANCE RULES (substance over exact wording):

SOFT RULES TO CHECK:
10. If risk_level will be HIGH or VERY_HIGH, must include explicit review disclosure
    ✓ ACCEPT: "review required", "senior review", "advisor approval", "needs review", "recommendation requires review"
    ✓ ACCEPT: ANY mention of review or approval in disclaimers or rationale
    
11. Must mention market risks and non-guaranteed returns for market-linked instruments
    ✓ ACCEPT: "market risks", "subject to risk", "not guaranteed", "may fluctuate", "volatile"
    ✓ ACCEPT: Any disclaimer mentioning risk and lack of guarantee ANYWHERE in the output
    ✓ ACCEPT: Presence of disclaimers array with ANY risk-related content
    ✗ REJECT: Language like "guaranteed returns", "risk-free", "assured returns" without disclaimers
    
12. If client has heavy concentration, should acknowledge it
    ✓ ACCEPT: Any mention of "concentration", "diversification", "sector balance", "exposure", "monitor", "weightage"
    ✓ ACCEPT: Concentration mentioned in rationale, disclaimers, or pick descriptions
    ✓ ACCEPT: Concentration_warnings exist in validator output (already flagged separately)
    ✓ OPTIONAL: Not a blocking issue - concentration warnings are tracked separately
    ✓ PASS if concentration is mentioned OR if concentration_warnings array is not empty
    
13. If time_period is shorter than minimum horizon for suggested instrument, flag as violation
    - Equity/ELSS needs minimum 3-5 years
    - Short-term goals (<1 year) should use liquid/debt only
    ✓ ACCEPT: If time_period is "5-7 years" or longer, equity is ALWAYS appropriate
    
14. Should connect recommendation to client's stated goal
    ✓ ACCEPT: Goal mentioned ANYWHERE in the output (rationale, disclaimers, pick descriptions)
    ✓ ACCEPT: "supports {goal}", "aligns with {goal}", "suitable for {goal}", "for {goal} goal"
    ✓ ACCEPT: Goal word appears in context even without explicit "connection" statement
    ✓ LENIENT: As long as goal is mentioned, consider this passed

GOAL-SPECIFIC CHECKS:
- emergency_fund: Must have 0% equity, 100% in liquid instruments
- retirement: Should have reasonable gold allocation (~5-15%)
- home_purchase: Should use short-term debt, minimal/no equity
- tax_saving: Must include at least one ELSS fund or tax-saving instrument

RISK FACTOR CHECKS (GUIDANCE, NOT STRICT):
- HIGH risk can have mid/small cap, sectoral exposure
- MEDIUM risk should stick to large cap, diversified
- LOW risk should be conservative debt/hybrid only

OUTPUT FORMAT (ONLY valid JSON):
{{
    "compliance_status": "PASS" or "FAIL",
    "issues": [
        "Specific rule violation with rule number - ONLY if truly missing or wrong"
    ],
    "suggestions_to_advisor": "Concrete fix instructions if status is FAIL, empty if PASS",
    "warnings": [
        "Non-blocking concerns that should be noted but don't fail compliance"
    ]
}}

CRITICAL GUIDELINES:
- If allocation_valid is False, compliance_status MUST be "FAIL"
- Concentration warnings are tracked separately and are NOT blocking issues
- Focus on SUBSTANCE over EXACT WORDING - accept variations and synonyms
- If disclaimers array exists with ANY content, rule 11 is PASSED
- If goal word appears ANYWHERE in output, rule 14 is PASSED
- If any review/approval language appears ANYWHERE, rule 10 is PASSED
- If concentration_warnings array is not empty OR concentration is mentioned, rule 12 is PASSED
- Only fail if truly missing critical elements (no disclaimers at all, wrong asset allocation for goal)
- Warnings are for minor issues that don't block recommendation
- Be pragmatic and lenient: if the spirit of the rule is met in ANY form, PASS"""


async def check_compliance(
    advisor_output: Dict,
    client_profile: Dict,
    goal: str,
    time_period: Optional[str],
    allocation_valid: bool,
    allocation_violations: List[str],
    concentration_warnings: List[str] = None
) -> Dict:
    """
    Check investment recommendation for compliance.
    Returns dict with compliance_status, issues, suggestions_to_advisor.
    """
    try:
        groq = get_groq_client()
        
        age = client_profile.get("age", 40)
        risk_factor = client_profile.get("risk_factor", "MEDIUM")
        
        prompt = COMPLIANCE_PROMPT.format(
            advisor_output=json.dumps(advisor_output, indent=2),
            age=age,
            risk_factor=risk_factor,
            goal=goal,
            time_period=time_period or "Not specified",
            allocation_valid=allocation_valid,
            allocation_violations=json.dumps(allocation_violations, indent=2),
            concentration_warnings=json.dumps(concentration_warnings or [], indent=2)
        )
        
        # Use LangChain for structured JSON output
        result_text = await groq.structured_output(
            system_prompt="You are a compliance officer. Return ONLY valid JSON.",
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
        
        # If deterministic validator failed, force FAIL status
        if not allocation_valid and result.get("compliance_status") != "FAIL":
            result["compliance_status"] = "FAIL"
            result.setdefault("issues", []).extend(allocation_violations)
        
        logger.info(f"Compliance check result: {result['compliance_status']}")
        if result.get("issues"):
            logger.warning(f"Compliance issues: {result['issues']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        # On error, fail safe (assume non-compliant)
        return {
            "compliance_status": "FAIL",
            "issues": [f"Compliance check error: {str(e)}"],
            "suggestions_to_advisor": "Unable to complete compliance check. Please review manually.",
            "warnings": []
        }
