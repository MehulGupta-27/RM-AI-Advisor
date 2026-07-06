"""
Portfolio Review Agent
Analyzes EXISTING client portfolios (balance, diversification, rebalancing needs)
Does NOT generate new recommendations - that's investment_advisor's job
"""

import json
from typing import Dict, List, Optional
from app.llm.groq_client import get_groq_client
from app.rules.allocation_rules import calculate_ideal_allocation


async def review_portfolio_balance(
    client_profile: Dict,
    portfolio: Dict,
    query_type: str
) -> Dict:
    """
    Review if client's EXISTING portfolio is balanced against their ideal allocation.
    
    Returns verdict with actual vs ideal allocation comparison.
    """
    
    age = client_profile.get("age", 40)
    risk_factor = client_profile.get("risk_factor", "MEDIUM")
    client_name = client_profile.get("client_name", "Client")
    
    # Get ACTUAL current allocation from portfolio table
    actual_equity = portfolio.get("current_equity_pct", 0)
    actual_mf = portfolio.get("current_mutual_fund_pct", 0)
    actual_gold = portfolio.get("current_gold_pct", 0)
    actual_debt = portfolio.get("current_fd_debt_pct", 0)
    
    # Calculate IDEAL allocation for this client
    ideal_allocation = calculate_ideal_allocation(age, risk_factor, goal="wealth_creation")
    ideal_equity = ideal_allocation["equity_pct"]
    ideal_mf = ideal_allocation["mutual_fund_pct"]
    ideal_gold = ideal_allocation["gold_pct"]
    ideal_debt = ideal_allocation["fd_debt_pct"]
    
    # Calculate gaps
    equity_gap = actual_equity - ideal_equity
    mf_gap = actual_mf - ideal_mf
    gold_gap = actual_gold - ideal_gold
    debt_gap = actual_debt - ideal_debt
    
    # Determine verdict based on gaps
    max_gap = max(abs(equity_gap), abs(mf_gap), abs(gold_gap), abs(debt_gap))
    
    if max_gap <= 5:
        verdict = "BALANCED"
        summary = f"{client_name}'s portfolio is well-balanced for their {risk_factor.lower()} risk profile."
    elif max_gap <= 10:
        verdict = "MINOR_IMBALANCE"
        summary = f"{client_name}'s portfolio has minor imbalances but is generally acceptable."
    else:
        verdict = "IMBALANCED"
        overweight = []
        underweight = []
        
        if equity_gap > 10:
            overweight.append(f"equity (over by {equity_gap:.0f}%)")
        elif equity_gap < -10:
            underweight.append(f"equity (under by {abs(equity_gap):.0f}%)")
            
        if mf_gap > 10:
            overweight.append(f"mutual funds (over by {mf_gap:.0f}%)")
        elif mf_gap < -10:
            underweight.append(f"mutual funds (under by {abs(mf_gap):.0f}%)")
            
        if gold_gap > 10:
            overweight.append(f"gold (over by {gold_gap:.0f}%)")
        elif gold_gap < -10:
            underweight.append(f"gold (under by {abs(gold_gap):.0f}%)")
            
        if debt_gap > 10:
            overweight.append(f"debt (over by {debt_gap:.0f}%)")
        elif debt_gap < -10:
            underweight.append(f"debt (under by {abs(debt_gap):.0f}%)")
        
        summary = f"{client_name}'s portfolio is imbalanced for their {risk_factor.lower()} risk profile. "
        if overweight:
            summary += f"Over-weighted in: {', '.join(overweight)}. "
        if underweight:
            summary += f"Under-weighted in: {', '.join(underweight)}."
    
    return {
        "verdict": verdict,
        "summary": summary,
        "actual_allocation": {
            "equity_pct": actual_equity,
            "mutual_fund_pct": actual_mf,
            "gold_pct": actual_gold,
            "fd_debt_pct": actual_debt
        },
        "ideal_allocation": ideal_allocation,
        "gaps": {
            "equity": equity_gap,
            "mutual_fund": mf_gap,
            "gold": gold_gap,
            "fd_debt": debt_gap
        },
        "max_gap": max_gap,
        "client_name": client_name,
        "age": age,
        "risk_factor": risk_factor
    }


async def review_portfolio_diversification(
    client_profile: Dict,
    holdings: List[Dict],
    portfolio: Dict
) -> Dict:
    """
    Review if client's portfolio is diversified across asset types and sectors.
    Now includes sector-level analysis using ticker→sector mapping.
    """
    from app.rules.sector_mapping import get_sector_breakdown, check_sector_concentration
    
    client_name = client_profile.get("client_name", "Client")
    risk_factor = client_profile.get("risk_factor", "MEDIUM")
    total_value = float(portfolio.get("current_portfolio_value", 0))
    
    # Count holdings by asset type
    asset_breakdown = {}
    for holding in holdings:
        asset_type = holding.get("asset_type", "unknown")
        current_value = float(holding.get("current_value", 0))
        
        if asset_type not in asset_breakdown:
            asset_breakdown[asset_type] = {
                "count": 0,
                "total_value": 0.0,
                "percentage": 0.0
            }
        
        asset_breakdown[asset_type]["count"] += 1
        asset_breakdown[asset_type]["total_value"] += current_value
    
    # Calculate percentages
    for asset_type in asset_breakdown:
        asset_breakdown[asset_type]["percentage"] = (
            (asset_breakdown[asset_type]["total_value"] / total_value * 100.0)
            if total_value > 0 else 0.0
        )
    
    # Get sector breakdown for stocks
    sector_breakdown = get_sector_breakdown(holdings, total_value)
    
    # Check for sector concentration violations
    sector_warnings = check_sector_concentration(holdings, total_value, risk_factor)
    
    # Check for single holding concentration risks
    concentration_issues = []
    for holding in holdings:
        holding_value = float(holding.get("current_value", 0))
        holding_pct = (holding_value / total_value * 100.0) if total_value > 0 else 0.0
        
        if holding_pct > 15:
            concentration_issues.append({
                "asset": holding.get("asset_name", "Unknown"),
                "percentage": holding_pct,
                "value": holding_value
            })
    
    # Determine verdict
    total_holdings = len(holdings)
    asset_types_count = len(asset_breakdown)
    has_concentration = len(concentration_issues) > 0
    has_sector_concentration = len(sector_warnings) > 0
    
    if total_holdings < 5:
        verdict = "UNDER_DIVERSIFIED"
        summary = f"{client_name}'s portfolio has only {total_holdings} holdings, which is insufficient for proper diversification."
    elif asset_types_count < 2:
        verdict = "UNDER_DIVERSIFIED"
        summary = f"{client_name}'s portfolio is concentrated in a single asset type. Consider diversifying across asset classes."
    elif has_sector_concentration:
        verdict = "SECTOR_CONCENTRATION"
        summary = f"{client_name}'s portfolio has sector concentration issues. " + sector_warnings[0]
    elif has_concentration:
        verdict = "CONCENTRATION_RISK"
        conc_assets = ", ".join([f"{c['asset']} ({c['percentage']:.1f}%)" for c in concentration_issues])
        summary = f"{client_name}'s portfolio has concentration risk. These holdings exceed 15%: {conc_assets}"
    elif total_holdings > 20:
        verdict = "OVER_DIVERSIFIED"
        summary = f"{client_name}'s portfolio has {total_holdings} holdings, which may be difficult to monitor. Consider consolidation."
    else:
        verdict = "WELL_DIVERSIFIED"
        summary = f"{client_name}'s portfolio is well-diversified with {total_holdings} holdings across {asset_types_count} asset types"
        if sector_breakdown:
            summary += f" and {len(sector_breakdown)} sectors."
        else:
            summary += "."
    
    return {
        "verdict": verdict,
        "summary": summary,
        "total_holdings": total_holdings,
        "asset_types_count": asset_types_count,
        "asset_breakdown": asset_breakdown,
        "sector_breakdown": sector_breakdown,
        "concentration_issues": concentration_issues,
        "sector_warnings": sector_warnings,
        "client_name": client_name
    }


async def review_rebalancing_need(
    client_profile: Dict,
    portfolio: Dict,
    holdings: List[Dict]
) -> Dict:
    """
    Determine if portfolio needs rebalancing based on actual vs ideal allocation gaps.
    Provides specific rebalancing actions if needed.
    """
    
    # First check balance
    balance_review = await review_portfolio_balance(client_profile, portfolio, "rebalancing_check")
    
    client_name = client_profile.get("client_name", "Client")
    verdict = balance_review["verdict"]
    max_gap = balance_review["max_gap"]
    gaps = balance_review["gaps"]
    last_review = portfolio.get("last_review_date", "Unknown")
    
    # Rebalancing threshold: >10% gap in any bucket
    REBALANCING_THRESHOLD = 10
    
    if max_gap <= REBALANCING_THRESHOLD:
        needs_rebalancing = False
        summary = f"{client_name}'s portfolio does NOT need rebalancing. "
        summary += f"Maximum allocation gap is {max_gap:.1f}%, which is within acceptable limits. "
        summary += f"Last review: {last_review}."
        actions = []
    else:
        needs_rebalancing = True
        summary = f"{client_name}'s portfolio NEEDS rebalancing. "
        summary += f"Maximum allocation gap is {max_gap:.1f}%, exceeding the {REBALANCING_THRESHOLD}% threshold. "
        
        # Generate specific actions
        actions = []
        
        equity_gap = gaps["equity"]
        mf_gap = gaps["mutual_fund"]
        gold_gap = gaps["gold"]
        debt_gap = gaps["fd_debt"]
        
        if equity_gap > REBALANCING_THRESHOLD:
            actions.append(f"REDUCE equity by ~{equity_gap:.0f}% (trim high-performing stock positions)")
        elif equity_gap < -REBALANCING_THRESHOLD:
            actions.append(f"INCREASE equity by ~{abs(equity_gap):.0f}% (add quality large-cap stocks or index funds)")
        
        if mf_gap > REBALANCING_THRESHOLD:
            actions.append(f"REDUCE mutual funds by ~{mf_gap:.0f}%")
        elif mf_gap < -REBALANCING_THRESHOLD:
            actions.append(f"INCREASE mutual funds by ~{abs(mf_gap):.0f}% (diversified equity funds)")
        
        if gold_gap > REBALANCING_THRESHOLD:
            actions.append(f"REDUCE gold by ~{gold_gap:.0f}% (book some profits if gold has appreciated)")
        elif gold_gap < -REBALANCING_THRESHOLD:
            actions.append(f"INCREASE gold by ~{abs(gold_gap):.0f}% (add Gold ETF or SGB)")
        
        if debt_gap > REBALANCING_THRESHOLD:
            actions.append(f"REDUCE debt by ~{debt_gap:.0f}% (redeploy to growth assets)")
        elif debt_gap < -REBALANCING_THRESHOLD:
            actions.append(f"INCREASE debt by ~{abs(debt_gap):.0f}% (add FDs or debt funds for stability)")
        
        summary += f"Last review: {last_review}."
    
    return {
        "needs_rebalancing": needs_rebalancing,
        "summary": summary,
        "actions": actions,
        "max_gap": max_gap,
        "threshold": REBALANCING_THRESHOLD,
        "balance_details": balance_review,
        "client_name": client_name
    }


# Format portfolio review response for client-facing output
def format_portfolio_review(review_result: Dict, query_type: str) -> str:
    """Format portfolio review results into natural language response"""
    
    client_name = review_result.get("client_name", "Client")
    
    if query_type == "balance_check":
        verdict = review_result["verdict"]
        summary = review_result["summary"]
        actual = review_result["actual_allocation"]
        ideal = review_result["ideal_allocation"]
        gaps = review_result["gaps"]
        
        response = f"# Portfolio Balance Review: {client_name}\n\n"
        response += f"**Verdict:** {verdict.replace('_', ' ').title()}\n\n"
        response += f"{summary}\n\n"
        response += f"## Current Allocation\n"
        response += f"- Equity: {actual['equity_pct']:.1f}%\n"
        response += f"- Mutual Funds: {actual['mutual_fund_pct']:.1f}%\n"
        response += f"- Gold: {actual['gold_pct']:.1f}%\n"
        response += f"- Debt/FD: {actual['fd_debt_pct']:.1f}%\n\n"
        response += f"## Ideal Allocation (for {review_result['risk_factor']} risk, age {review_result['age']})\n"
        response += f"- Equity: {ideal['equity_pct']}%\n"
        response += f"- Mutual Funds: {ideal['mutual_fund_pct']}%\n"
        response += f"- Gold: {ideal['gold_pct']}%\n"
        response += f"- Debt/FD: {ideal['fd_debt_pct']}%\n\n"
        response += f"## Gaps\n"
        response += f"- Equity: {gaps['equity']:+.1f}%\n"
        response += f"- Mutual Funds: {gaps['mutual_fund']:+.1f}%\n"
        response += f"- Gold: {gaps['gold']:+.1f}%\n"
        response += f"- Debt/FD: {gaps['fd_debt']:+.1f}%\n"
        
    elif query_type == "diversification_check":
        verdict = review_result["verdict"]
        summary = review_result["summary"]
        total_holdings = review_result["total_holdings"]
        asset_breakdown = review_result["asset_breakdown"]
        sector_breakdown = review_result.get("sector_breakdown", {})
        concentration_issues = review_result["concentration_issues"]
        sector_warnings = review_result.get("sector_warnings", [])
        
        response = f"# Portfolio Diversification Review: {client_name}\n\n"
        response += f"**Verdict:** {verdict.replace('_', ' ').title()}\n\n"
        response += f"{summary}\n\n"
        response += f"## Holdings Summary\n"
        response += f"- Total Holdings: {total_holdings}\n"
        response += f"- Asset Types: {len(asset_breakdown)}\n"
        if sector_breakdown:
            response += f"- Sectors (in stocks): {len(sector_breakdown)}\n"
        response += f"\n## Asset Type Breakdown\n"
        for asset_type, data in asset_breakdown.items():
            response += f"- **{asset_type.upper()}**: {data['count']} holdings, {data['percentage']:.1f}% of portfolio\n"
        
        if sector_breakdown:
            response += f"\n## Sector Breakdown (Stocks Only)\n"
            for sector, data in sorted(sector_breakdown.items(), key=lambda x: x[1]['percentage'], reverse=True):
                stocks_str = ", ".join([s['ticker'] for s in data['stocks'][:3]])
                if len(data['stocks']) > 3:
                    stocks_str += f" +{len(data['stocks'])-3} more"
                response += f"- **{sector}**: {data['percentage']:.1f}% ({stocks_str})\n"
        
        if sector_warnings:
            response += f"\n## ⚠️ Sector Concentration Warnings\n"
            for warning in sector_warnings:
                response += f"- {warning}\n"
        
        if concentration_issues:
            response += f"\n## ⚠️ Individual Holding Concentration Risks\n"
            for issue in concentration_issues:
                response += f"- **{issue['asset']}**: {issue['percentage']:.1f}% of portfolio (exceeds 15% limit)\n"
    
    elif query_type == "rebalancing_check":
        needs_rebalancing = review_result["needs_rebalancing"]
        summary = review_result["summary"]
        actions = review_result["actions"]
        
        response = f"# Rebalancing Review: {client_name}\n\n"
        response += f"**Needs Rebalancing:** {'YES' if needs_rebalancing else 'NO'}\n\n"
        response += f"{summary}\n\n"
        
        if needs_rebalancing and actions:
            response += f"## Recommended Actions\n"
            for i, action in enumerate(actions, 1):
                response += f"{i}. {action}\n"
            response += f"\n**Note:** Consult with your advisor before implementing these changes.\n"
    
    else:
        response = f"Portfolio review completed for {client_name}."
    
    return response
