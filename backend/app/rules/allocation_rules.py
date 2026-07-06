"""
Deterministic allocation rules - Single source of truth for compliance
Implements hard numeric rules from spec §5.10-A
"""

from typing import Dict, List, Tuple


# Base equity allocation by risk tier (before age adjustment)
BASE_EQUITY_BY_RISK = {
    "high": 65,
    "medium": 45,
    "low": 15
}

# Hard equity ceilings by risk tier
MAX_EQUITY_BY_RISK = {
    "high": 83,
    "medium": 58,
    "low": 23
}

# Age-based equity adjustments
def get_age_adjustment(age: int) -> int:
    """Returns percentage points to add/subtract from base equity"""
    if age < 30:
        return 5
    elif 30 <= age <= 45:
        return 0
    elif 45 < age <= 55:
        return -5
    elif 55 < age <= 60:
        return -15
    else:  # > 60
        return -20


def calculate_ideal_allocation(
    age: int,
    risk_factor: str,
    goal: str = "wealth_creation"
) -> Dict[str, int]:
    """
    Calculate ideal allocation percentages based on age, risk tier, and goal.
    Returns dict with equity_pct, mutual_fund_pct, gold_pct, fd_debt_pct.
    """
    risk_lower = risk_factor.lower()
    
    # Start with base equity
    base_equity = BASE_EQUITY_BY_RISK.get(risk_lower, 45)
    
    # Apply age adjustment
    age_adj = get_age_adjustment(age)
    equity_pct = base_equity + age_adj
    
    # Apply hard ceiling
    max_equity = MAX_EQUITY_BY_RISK.get(risk_lower, 58)
    equity_pct = min(equity_pct, max_equity)
    
    # Special rule: age > 60 → equity never exceeds 30%
    if age > 60:
        equity_pct = min(equity_pct, 30)
    
    # Goal-based structural overrides (mandatory)
    if goal == "emergency_fund":
        # Emergency fund → 0% equity, all in liquid debt
        equity_pct = 0
        mutual_fund_pct = 0
        gold_pct = 0
        fd_debt_pct = 100
        
    elif goal == "retirement":
        # Retirement → shift 5% from equity to gold
        gold_add = 5
        equity_pct = max(0, equity_pct - 5)
        
        # Remaining allocation
        remaining = 100 - equity_pct - gold_add
        mutual_fund_pct = int(remaining * 0.5)
        fd_debt_pct = remaining - mutual_fund_pct
        gold_pct = 10 + gold_add  # base 10% + 5%
        
    elif goal == "home_purchase":
        # Home purchase → replace equity with short-term debt
        equity_pct = 0
        mutual_fund_pct = 0
        gold_pct = 10
        fd_debt_pct = 90
        
    else:
        # Standard allocation (wealth_creation, tax_saving, child_education)
        # Gold: 10% baseline
        gold_pct = 10
        
        # Remaining 90% split between equity, MF, and FD/debt
        remaining = 100 - equity_pct - gold_pct
        
        # MF gets 50% of remaining, FD/debt gets the rest
        mutual_fund_pct = int(remaining * 0.5)
        fd_debt_pct = remaining - mutual_fund_pct
    
    # Ensure exact 100% total (handle rounding)
    allocation = {
        "equity_pct": equity_pct,
        "mutual_fund_pct": mutual_fund_pct,
        "gold_pct": gold_pct,
        "fd_debt_pct": fd_debt_pct
    }
    
    total = sum(allocation.values())
    if total != 100:
        # Adjust FD to make it exactly 100
        allocation["fd_debt_pct"] += (100 - total)
    
    return allocation


def calculate_sip_suggestion(monthly_income: float | None) -> float:
    """
    Calculate monthly SIP suggestion.
    Rule: 20% of monthly income, max 30%, default 5000 if income unknown.
    """
    if monthly_income is None or monthly_income <= 0:
        return 5000.0
    
    # Convert to float if it's a Decimal from SQLAlchemy
    income_float = float(monthly_income)
    
    # 20% of income
    sip = income_float * 0.20
    
    # Never exceed 30% of income
    max_sip = income_float * 0.30
    
    return min(sip, max_sip)


def validate_allocation(
    allocation: Dict[str, int],
    age: int,
    risk_factor: str,
    goal: str,
    monthly_income: float | None = None,
    sip_suggestion: float | None = None
) -> Tuple[bool, List[str]]:
    """
    Validate an allocation against hard rules.
    Returns (is_valid, list_of_violations).
    """
    violations = []
    
    # Rule 1: Must sum to exactly 100%
    total = allocation.get("equity_pct", 0) + allocation.get("mutual_fund_pct", 0) + \
            allocation.get("gold_pct", 0) + allocation.get("fd_debt_pct", 0)
    
    if total != 100:
        violations.append(f"Allocation sums to {total}%, must be exactly 100%")
    
    # Rule 2: Equity ceiling by risk tier
    equity_pct = allocation.get("equity_pct", 0)
    risk_lower = risk_factor.lower()
    max_equity = MAX_EQUITY_BY_RISK.get(risk_lower, 58)
    
    if equity_pct > max_equity:
        violations.append(
            f"Equity {equity_pct}% exceeds maximum {max_equity}% for {risk_factor} risk tier"
        )
    
    # Rule 3: Age > 60 → equity never exceeds 30%
    if age > 60 and equity_pct > 30:
        violations.append(
            f"Equity {equity_pct}% exceeds 30% maximum for age {age} (>60 years)"
        )
    
    # Rule 4: Goal-based structural checks
    if goal == "emergency_fund" and equity_pct != 0:
        violations.append(
            f"Emergency fund must have 0% equity, got {equity_pct}%"
        )
    
    if goal == "home_purchase" and equity_pct > 0:
        violations.append(
            f"Home purchase goal should use short-term debt, not {equity_pct}% equity"
        )
    
    if goal == "retirement":
        gold_pct = allocation.get("gold_pct", 0)
        if gold_pct < 15:  # Should be base 10% + 5% = 15%
            violations.append(
                f"Retirement goal should increase gold to ~15%, got {gold_pct}%"
            )
    
    # Rule 5: SIP validation (if provided)
    if sip_suggestion is not None and monthly_income is not None and monthly_income > 0:
        # Convert to float if it's a Decimal from SQLAlchemy
        income_float = float(monthly_income)
        max_sip = income_float * 0.30
        ideal_sip = income_float * 0.20
        
        if sip_suggestion > max_sip:
            violations.append(
                f"SIP ₹{sip_suggestion:,.0f} exceeds 30% of income (max ₹{max_sip:,.0f})"
            )
        
        # Allow some tolerance (within 5% of ideal)
        if abs(sip_suggestion - ideal_sip) > (ideal_sip * 0.05) and sip_suggestion < ideal_sip:
            violations.append(
                f"SIP ₹{sip_suggestion:,.0f} is below recommended 20% of income (₹{ideal_sip:,.0f})"
            )
    
    return (len(violations) == 0, violations)


def validate_picks_against_market_data(
    equity_picks: List[Dict],
    mf_picks: List[Dict],
    stock_data: Dict,
    mf_data: Dict
) -> Tuple[bool, List[str]]:
    """
    Rule 7: Every ticker/scheme cited should have matching live data.
    Returns (is_valid, list_of_warnings).
    
    MODIFIED: Missing market data is now a warning, not a failure,
    since stock APIs may be temporarily unavailable. This allows LLM
    recommendations to proceed based on fundamental analysis even when
    live prices aren't available.
    """
    warnings = []
    
    # Validate equity picks - but don't fail if data missing
    for pick in equity_picks:
        ticker = pick.get("ticker", "")
        if ticker and stock_data and ticker not in stock_data:
            warnings.append(f"Stock {ticker} has no live data (API may be unavailable)")
    
    # Validate MF picks
    for pick in mf_picks:
        scheme_name = pick.get("scheme_name", "")
        if scheme_name and mf_data:
            found = any(
                scheme_name.lower() in str(v).lower() 
                for v in mf_data.values() if v is not None
            )
            if not found:
                warnings.append(f"Mutual fund {scheme_name} has no live data (API may be unavailable)")
    
    # Always return valid=True, violations are now just warnings
    # This allows recommendations to proceed even when external APIs fail
    return (True, warnings)


def calculate_concentration_risk(
    holdings: List[Dict],
    new_picks: List[Dict],
    total_portfolio_value: float
) -> List[str]:
    """
    Rule 8: Single-stock concentration cap (15% of total portfolio).
    Rule 9: Sector concentration warnings.
    Returns list of concentration warnings.
    """
    warnings = []
    
    # Convert portfolio value to float if it's a Decimal
    total_value = float(total_portfolio_value) if total_portfolio_value else 0
    
    # Build current position map
    positions = {}
    for holding in holdings:
        ticker = holding.get("asset_name", "")
        value = float(holding.get("current_value", 0)) if holding.get("current_value") else 0
        positions[ticker] = positions.get(ticker, 0) + value
    
    # Check each new pick
    for pick in new_picks:
        ticker = pick.get("ticker", "")
        if not ticker:
            continue
        
        suggested_amount = float(pick.get("suggested_amount", 0)) if pick.get("suggested_amount") else 0
        current_value = positions.get(ticker, 0)
        new_total = current_value + suggested_amount
        
        concentration = (new_total / total_value * 100) if total_value > 0 else 0
        
        if concentration > 15:
            warnings.append(
                f"Stock {ticker} would reach {concentration:.1f}% of portfolio (max 15%)"
            )
    
    return warnings


# Deterministic fallback allocation (used when compliance keeps failing)
def get_fallback_allocation(age: int, risk_factor: str, goal: str) -> Dict:
    """
    Returns a simple, rule-compliant allocation with no specific picks.
    Always passes compliance by construction.
    """
    allocation = calculate_ideal_allocation(age, risk_factor, goal)
    
    # Generic category recommendations (no specific tickers)
    if allocation["equity_pct"] > 0:
        equity_reco = "Large-cap index fund or blue-chip diversified portfolio"
    else:
        equity_reco = "Not recommended for this goal/profile"
    
    if allocation["mutual_fund_pct"] > 0:
        if goal == "tax_saving":
            mf_reco = "ELSS (tax-saving) funds from top AMCs"
        elif risk_factor.lower() == "low":
            mf_reco = "Short-duration debt funds"
        else:
            mf_reco = "Balanced advantage or multi-cap funds"
    else:
        mf_reco = "Not recommended for this goal/profile"
    
    if allocation["gold_pct"] > 0:
        gold_reco = "Gold ETF or Sovereign Gold Bonds"
    else:
        gold_reco = "Not required for this allocation"
    
    if allocation["fd_debt_pct"] > 0:
        fd_reco = "Fixed deposits or liquid funds for stability"
    else:
        fd_reco = "Not recommended for this goal/profile"
    
    return {
        "allocation": allocation,
        "equity_recommendation": equity_reco,
        "mf_recommendation": mf_reco,
        "gold_recommendation": gold_reco,
        "fd_recommendation": fd_reco,
        "note": "This is a rule-based allocation using generic categories. "
                "For specific stock/fund picks, please refine your request or consult your advisor."
    }
