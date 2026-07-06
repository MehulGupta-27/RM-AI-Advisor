"""
LangGraph State Machine for Investment Advisory Pipeline
Replaces manual orchestration in chat.py with proper state graph
"""

import asyncio
from typing import Dict, Literal
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph_state import AgentState, create_initial_state
from app.agents.query_understanding import understand_query
from app.agents.client_resolver import resolve_client
from app.agents.stock_selector import select_stocks_and_mf
from app.agents.investment_advisor import generate_investment_advice
from app.agents.compliance import check_compliance
from app.agents.risk import assess_risk
from app.agents.market_intelligence import synthesize_market_data
from app.rules.allocation_rules import (
    validate_allocation,
    get_fallback_allocation,
    validate_picks_against_market_data,
    calculate_concentration_risk
)
from app.tools.stock_quote import get_stock_quote
from app.tools.index_quote import get_index_quote


# ==================== NODE FUNCTIONS ====================

async def query_understanding_node(state: AgentState) -> AgentState:
    """Node 1: Understand user query and classify intent"""
    print("📍 Node: Query Understanding")
    
    try:
        understanding = await understand_query(
            message=state["user_message"],
            client_id=state["client_id"],
            goal=state["goal"],
            time_period=state["time_period"]
        )
        
        print(f"  ✓ Intent: {understanding.intent}")
        print(f"  ✓ Query Type: {understanding.query_type}")
        
        return {
            **state,
            "intent": understanding.intent,
            "query_type": understanding.query_type,
            "ticker": understanding.ticker,
            "scheme_name": understanding.scheme_name,
            "market_topic": understanding.market_topic,
            "db_filter": understanding.db_filter,
            "rationale": understanding.rationale
        }
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e), "intent": "error"}


async def client_resolver_node(state: AgentState, db: AsyncSession) -> AgentState:
    """Node 2: Resolve client data from database"""
    print("📍 Node: Client Resolver")
    
    if not state["client_id"]:
        return {**state, "error": "No client_id provided"}
    
    try:
        client_data = await resolve_client(
            client_id=state["client_id"],
            client_name=None,
            db=db
        )
        
        if not client_data:
            return {**state, "error": "Client not found"}
        
        print(f"  ✓ Client: {client_data['profile'].get('client_name')}")
        
        return {
            **state,
            "client_profile": client_data["profile"],
            "client_holdings": client_data["holdings"],
            "client_portfolio": client_data["portfolio"]
        }
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def stock_selector_node(state: AgentState) -> AgentState:
    """Node 3: Determine which stocks/MF to fetch"""
    print("📍 Node: Stock Selector")
    
    try:
        selector_output = await select_stocks_and_mf(
            client_profile=state["client_profile"],
            goal=state["goal"] or "wealth_creation",
            query_type=state["query_type"],
            ticker=state["ticker"],
            time_period=state["time_period"]
        )
        
        stocks = selector_output.get("stocks_to_fetch", [])
        print(f"  ✓ Stocks to fetch: {stocks}")
        
        return {
            **state,
            "stocks_to_fetch": stocks,
            "sector_name": selector_output.get("sector_name")
        }
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def market_data_node(state: AgentState) -> AgentState:
    """Node 4: Fetch live market data in parallel"""
    print("📍 Node: Market Data Fetcher")
    
    try:
        tool_calls = []
        
        # Always fetch index
        tool_calls.append(("index", get_index_quote("NIFTY")))
        
        # Fetch specific stocks
        for ticker in state.get("stocks_to_fetch", []):
            tool_calls.append((f"stock_{ticker}", get_stock_quote(ticker)))
        
        # Execute in parallel
        results = await asyncio.gather(
            *[call for _, call in tool_calls],
            return_exceptions=True
        )
        
        # Build market_data dict
        market_data = {}
        stock_data = {}
        
        for (data_type, _), result in zip(tool_calls, results):
            if isinstance(result, Exception):
                print(f"  ⚠️ Tool error for {data_type}: {result}")
                continue
            
            if data_type == "index":
                market_data["index_data"] = result
            elif data_type.startswith("stock_"):
                ticker = data_type.replace("stock_", "")
                stock_data[ticker] = result
        
        market_data["stock_data"] = stock_data
        
        print(f"  ✓ Fetched: index + {len(stock_data)} stocks")
        
        return {**state, "market_data": market_data}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def market_intelligence_node(state: AgentState) -> AgentState:
    """Node 5: Synthesize market data summary"""
    print("📍 Node: Market Intelligence")
    
    try:
        summary = await synthesize_market_data(
            market_data=state["market_data"],
            query_context=state["user_message"]
        )
        
        print(f"  ✓ Summary generated ({len(summary)} chars)")
        
        return {**state, "market_summary": summary}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def investment_advisor_node(state: AgentState) -> AgentState:
    """Node 6: Generate investment recommendations"""
    retry_count = state.get("compliance_retry_count", 0)
    print(f"📍 Node: Investment Advisor (attempt {retry_count + 1})")
    
    try:
        # Determine mode
        query_type = state["query_type"]
        if query_type == "sector":
            mode = "sector_analysis"
        elif query_type == "stock":
            mode = "stock_analysis"
        else:
            mode = "full_plan"
        
        # Get compliance feedback if this is a retry
        compliance_feedback = state.get("compliance_result") if retry_count > 0 else None
        
        advisor_output = await generate_investment_advice(
            mode=mode,
            client_profile=state["client_profile"],
            holdings=state["client_holdings"],
            portfolio=state["client_portfolio"],
            market_summary=state["market_summary"],
            goal=state["goal"] or "wealth_creation",
            time_period=state["time_period"],
            query_type=state["query_type"],
            ticker=state["ticker"],
            sector_name=state["sector_name"],
            compliance_feedback=compliance_feedback
        )
        
        print(f"  ✓ Recommendation generated (mode: {mode})")
        
        # Increment retry count for next iteration
        return {
            **state,
            "advisor_output": advisor_output,
            "advisor_mode": mode,
            "compliance_retry_count": retry_count + 1
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def capital_allocator_node(state: AgentState) -> AgentState:
    """Node 6.5: Allocate capital to specific instruments with amounts (NEW)"""
    print("📍 Node: Capital Allocator (Detailed Breakdown)")
    
    # Only run if investment_amount is provided
    if not state.get("investment_amount"):
        print("  ⊘ Skipping (no investment amount specified)")
        return state
    
    try:
        from app.agents.capital_allocator import allocate_capital_to_instruments
        
        result = await allocate_capital_to_instruments(
            advisor_output=state["advisor_output"],
            market_data=state.get("market_data", {}),
            client_profile=state["client_profile"],
            investment_amount=state["investment_amount"],
            goal=state.get("goal"),
            time_period=state.get("time_period"),
            risk_factor=state["client_profile"].get("risk_factor", "MEDIUM")
        )
        
        if result.get("success"):
            print(f"  ✓ Capital allocated across specific instruments")
            return {
                **state,
                "capital_allocation": result.get("capital_allocation")
            }
        else:
            print(f"  ⊘ Capital allocation failed: {result.get('error')}")
            return state
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        # Don't fail the whole pipeline if capital allocator fails
        return state


async def allocation_validator_node(state: AgentState) -> AgentState:
    """Node 7: Validate allocation with deterministic rules"""
    print("📍 Node: Allocation Validator")
    
    try:
        # Check if this is stock_analysis mode - skip allocation validation
        query_type = state.get("query_type", "general")
        recommendation = state["advisor_output"].get("recommendation")
        
        if query_type == "stock" and recommendation in ["YES", "NO", "BUY", "HOLD", "AVOID"]:
            # Stock analysis doesn't need allocation validation
            print(f"  ⊘ Skipping (stock_analysis mode - no allocation needed)")
            return {
                **state,
                "allocation_valid": True,  # Pass by default
                "allocation_violations": [],
                "concentration_warnings": []
            }
        
        allocation = state["advisor_output"].get("allocation", {})
        age = state["client_profile"].get("age", 40)
        risk_factor = state["client_profile"].get("risk_factor", "MEDIUM")
        goal = state["goal"] or "wealth_creation"
        monthly_income = state["client_profile"].get("monthly_income")
        
        sip_suggestion = state["advisor_output"].get("monthly_sip_suggestion") or \
                        next((pick.get("sip_per_month") for pick in state["advisor_output"].get("mf_picks", [])), None)
        
        # Validate allocation
        allocation_valid, allocation_violations = validate_allocation(
            allocation=allocation,
            age=age,
            risk_factor=risk_factor,
            goal=goal,
            monthly_income=monthly_income,
            sip_suggestion=sip_suggestion
        )
        
        # Validate picks
        equity_picks = state["advisor_output"].get("equity_picks", [])
        mf_picks = state["advisor_output"].get("mf_picks", [])
        stock_data = state["market_data"].get("stock_data", {})
        
        picks_valid, pick_violations = validate_picks_against_market_data(
            equity_picks=equity_picks,
            mf_picks=mf_picks,
            stock_data=stock_data,
            mf_data={}
        )
        
        if not picks_valid:
            allocation_violations.extend(pick_violations)
            allocation_valid = False
        
        # Check concentration (warnings only, don't fail allocation)
        total_value = state["client_portfolio"].get("current_portfolio_value", 0)
        concentration_warnings = calculate_concentration_risk(
            holdings=state["client_holdings"],
            new_picks=equity_picks,
            total_portfolio_value=total_value
        )
        
        # Add concentration warnings separately, don't block allocation
        # These go to compliance agent as informational only
        
        print(f"  ✓ Valid: {allocation_valid} ({len(allocation_violations)} violations)")
        if concentration_warnings:
            print(f"  ⚠️  {len(concentration_warnings)} concentration warnings (non-blocking)")
        
        return {
            **state,
            "allocation_valid": allocation_valid,
            "allocation_violations": allocation_violations or [],
            "concentration_warnings": concentration_warnings or []
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def compliance_node(state: AgentState) -> AgentState:
    """Node 8: Check compliance with soft rules"""
    print("📍 Node: Compliance Agent")
    
    try:
        # For stock_analysis, skip detailed compliance (already validated in advisor)
        query_type = state.get("query_type", "general")
        recommendation = state["advisor_output"].get("recommendation")
        
        if query_type == "stock" and recommendation in ["YES", "NO", "BUY", "HOLD", "AVOID"]:
            print(f"  ⊘ Skipping (stock_analysis has its own validation)")
            # Auto-pass compliance for stock analysis
            return {
                **state,
                "compliance_result": {
                    "compliance_status": "PASS",
                    "issues": [],
                    "suggestions_to_advisor": "",
                    "warnings": []
                }
            }
        
        compliance_result = await check_compliance(
            advisor_output=state["advisor_output"],
            client_profile=state["client_profile"],
            goal=state["goal"] or "wealth_creation",
            time_period=state["time_period"],
            allocation_valid=state["allocation_valid"],
            allocation_violations=state["allocation_violations"],
            concentration_warnings=state.get("concentration_warnings", [])
        )
        
        status = compliance_result.get("compliance_status", "UNKNOWN")
        print(f"  ✓ Status: {status}")
        
        return {**state, "compliance_result": compliance_result}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def fallback_node(state: AgentState) -> AgentState:
    """Node 9: Apply fallback allocation if compliance keeps failing"""
    print("📍 Node: Fallback Allocation")
    
    try:
        age = state["client_profile"].get("age", 40)
        risk_factor = state["client_profile"].get("risk_factor", "MEDIUM")
        goal = state["goal"] or "wealth_creation"
        
        fallback = get_fallback_allocation(age, risk_factor, goal)
        
        print(f"  ✓ Fallback allocation applied")
        
        return {
            **state,
            "advisor_output": fallback,
            "used_fallback": True,
            "allocation_valid": True,
            "allocation_violations": []
        }
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def risk_assessment_node(state: AgentState) -> AgentState:
    """Node 10: Assess risk across 5 dimensions"""
    print("📍 Node: Risk Assessment")
    
    try:
        risk_result = await assess_risk(
            advisor_output=state["advisor_output"],
            client_profile=state["client_profile"],
            holdings=state["client_holdings"],
            goal=state["goal"] or "wealth_creation",
            time_period=state["time_period"],
            used_fallback=state["used_fallback"]
        )
        
        risk_level = risk_result.get("risk_level", "UNKNOWN")
        print(f"  ✓ Risk Level: {risk_level}")
        
        return {**state, "risk_result": risk_result}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


async def response_formatter_node(state: AgentState) -> AgentState:
    """Node 11: Format final response"""
    print("📍 Node: Response Formatter")
    
    try:
        from app.api.chat import format_investment_response
        
        client_name = state["client_profile"].get("client_name", "Client")
        
        response = format_investment_response(
            client_name=client_name,
            advisor_output=state["advisor_output"],
            compliance_result=state["compliance_result"],
            risk_result=state["risk_result"],
            used_fallback=state["used_fallback"],
            goal=state["goal"] or "wealth_creation",
            time_period=state["time_period"],
            capital_allocation=state.get("capital_allocation"),  # NEW
            investment_amount=state.get("investment_amount")  # NEW
        )
        
        print(f"  ✓ Response formatted ({len(response)} chars)")
        
        return {**state, "response": response}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {**state, "error": str(e)}


# ==================== CONDITIONAL ROUTING ====================

def route_after_understanding(state: AgentState) -> Literal["client_resolver", "error", END]:
    """Route based on intent after query understanding"""
    intent = state.get("intent")
    
    if state.get("error"):
        return "error"
    
    if intent == "investment_advice":
        return "client_resolver"
    
    # For other intents (general_chat, db_query, market_query), skip to END
    # These will be handled by simple response logic
    return END


def route_after_compliance(state: AgentState) -> Literal["investment_advisor", "risk_assessment", END]:
    """Route after compliance check - retry or continue"""
    if state.get("error"):
        return END
    
    compliance_status = state.get("compliance_result", {}).get("compliance_status")
    retry_count = state.get("compliance_retry_count", 0)
    max_retries = 2
    
    # If compliant, move to risk assessment
    if compliance_status == "PASS":
        return "risk_assessment"
    
    # If not compliant but retries remain, go back to advisor
    if retry_count < max_retries:
        print(f"  → Retrying (attempt {retry_count + 1}/{max_retries})")
        return "investment_advisor"
    
    # Exhausted retries, use fallback
    print(f"  → Max retries reached, using fallback")
    return END  # Will trigger fallback node


def should_use_fallback(state: AgentState) -> bool:
    """Check if we should use fallback allocation"""
    retry_count = state.get("compliance_retry_count", 0)
    compliance_status = state.get("compliance_result", {}).get("compliance_status")
    
    return retry_count >= 2 and compliance_status != "PASS"


# ==================== GRAPH BUILDER ====================

def create_advisory_graph(db: AsyncSession) -> StateGraph:
    """
    Create the LangGraph state machine for investment advisory.
    
    Flow:
    1. Query Understanding → classify intent
    2. Client Resolver → fetch client data (if investment_advice)
    3. Stock Selector → determine what to fetch
    4. Market Data → parallel tool execution
    5. Market Intelligence → synthesize summary
    6. Investment Advisor → generate recommendations
    7. Allocation Validator → check hard rules
    8. Compliance Agent → check soft rules
    9. (Conditional) Retry advisor or apply fallback
    10. Risk Assessment → 5-dimension scoring
    11. Response Formatter → format output
    """
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("query_understanding", query_understanding_node)
    
    # Async node wrappers for nodes that need database access
    async def client_resolver_wrapper(state: AgentState) -> AgentState:
        return await client_resolver_node(state, db)
    
    workflow.add_node("client_resolver", client_resolver_wrapper)
    workflow.add_node("stock_selector", stock_selector_node)
    workflow.add_node("market_data", market_data_node)
    workflow.add_node("market_intelligence", market_intelligence_node)
    workflow.add_node("investment_advisor", investment_advisor_node)
    workflow.add_node("capital_allocator", capital_allocator_node)  # NEW: Specific instrument allocation
    workflow.add_node("allocation_validator", allocation_validator_node)
    workflow.add_node("compliance", compliance_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("response_formatter", response_formatter_node)
    
    # Set entry point
    workflow.set_entry_point("query_understanding")
    
    # Add edges
    workflow.add_conditional_edges(
        "query_understanding",
        route_after_understanding,
        {
            "client_resolver": "client_resolver",
            "error": END,
            END: END
        }
    )
    
    workflow.add_edge("client_resolver", "stock_selector")
    workflow.add_edge("stock_selector", "market_data")
    workflow.add_edge("market_data", "market_intelligence")
    workflow.add_edge("market_intelligence", "investment_advisor")
    workflow.add_edge("investment_advisor", "capital_allocator")  # NEW: Get detailed breakdown
    workflow.add_edge("capital_allocator", "allocation_validator")  # Then validate
    workflow.add_edge("allocation_validator", "compliance")
    
    # Compliance routing (retry or continue)
    workflow.add_conditional_edges(
        "compliance",
        route_after_compliance,
        {
            "investment_advisor": "investment_advisor",  # Retry
            "risk_assessment": "risk_assessment",  # Continue
            END: "fallback"  # Use fallback
        }
    )
    
    workflow.add_edge("fallback", "risk_assessment")
    workflow.add_edge("risk_assessment", "response_formatter")
    workflow.add_edge("response_formatter", END)
    
    return workflow.compile()


# ==================== HELPER FUNCTION ====================

async def run_advisory_graph(
    user_message: str,
    client_id: Optional[int],
    goal: Optional[str],
    time_period: Optional[str],
    investment_amount: Optional[float],  # NEW
    db: AsyncSession
) -> Dict:
    """
    Run the full advisory graph and return the final state.
    
    This replaces the manual orchestration in chat.py.
    """
    print("\n" + "="*60)
    print("🚀 Starting LangGraph Advisory Pipeline")
    print("="*60)
    
    # Create initial state
    initial_state = create_initial_state(
        user_message=user_message,
        client_id=client_id,
        goal=goal,
        time_period=time_period,
        investment_amount=investment_amount  # NEW
    )
    
    # Create and run graph
    graph = create_advisory_graph(db)
    final_state = await graph.ainvoke(initial_state)
    
    print("\n" + "="*60)
    print("✅ Pipeline Complete")
    print("="*60 + "\n")
    
    return final_state
