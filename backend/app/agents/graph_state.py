"""
LangGraph State Definition for Multi-Agent Orchestration
Defines the shared state that flows through all agent nodes
"""

from typing import Dict, List, Optional, TypedDict, Annotated
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    Shared state for the multi-agent workflow.
    Each agent reads from and writes to this state.
    """
    
    # Input from user
    messages: Annotated[List[BaseMessage], add_messages]  # Conversation history
    user_message: str
    client_id: Optional[int]
    goal: Optional[str]
    time_period: Optional[str]
    investment_amount: Optional[float]  # NEW: Amount to invest
    
    # Query understanding output
    intent: Optional[str]  # general_chat, db_query, market_query, investment_advice
    query_type: Optional[str]  # stock, index, sector, mutual_fund, commodity, etc.
    ticker: Optional[str]
    scheme_name: Optional[str]
    market_topic: Optional[str]
    db_filter: Optional[str]
    rationale: Optional[str]
    
    # Client data (from resolver)
    client_profile: Optional[Dict]
    client_holdings: Optional[List[Dict]]
    client_portfolio: Optional[Dict]
    
    # Market data
    market_data: Optional[Dict]
    market_summary: Optional[str]
    stocks_to_fetch: Optional[List[str]]
    sector_name: Optional[str]
    
    # Investment advisor output
    advisor_output: Optional[Dict]
    advisor_mode: Optional[str]  # full_plan, sector_analysis, stock_analysis
    
    # Capital allocation (detailed breakdown)
    capital_allocation: Optional[Dict]  # NEW: Specific instruments with amounts
    
    # Compliance validation
    allocation_valid: bool
    allocation_violations: Optional[List[str]]
    compliance_result: Optional[Dict]
    compliance_retry_count: int
    used_fallback: bool
    
    # Risk assessment
    risk_result: Optional[Dict]
    
    # Final response
    response: Optional[str]
    
    # Error handling
    error: Optional[str]
    next_node: Optional[str]  # For conditional routing


def create_initial_state(
    user_message: str,
    client_id: Optional[int] = None,
    goal: Optional[str] = None,
    time_period: Optional[str] = None,
    investment_amount: Optional[float] = None  # NEW
) -> AgentState:
    """Create initial state from user input"""
    return AgentState(
        messages=[],
        user_message=user_message,
        client_id=client_id,
        goal=goal,
        time_period=time_period,
        investment_amount=investment_amount,  # NEW
        intent=None,
        query_type=None,
        ticker=None,
        scheme_name=None,
        market_topic=None,
        db_filter=None,
        rationale=None,
        client_profile=None,
        client_holdings=None,
        client_portfolio=None,
        market_data=None,
        market_summary=None,
        stocks_to_fetch=None,
        sector_name=None,
        advisor_output=None,
        advisor_mode=None,
        capital_allocation=None,  # NEW
        allocation_valid=True,
        allocation_violations=None,
        compliance_result=None,
        compliance_retry_count=0,
        used_fallback=False,
        risk_result=None,
        response=None,
        error=None,
        next_node=None
    )
