"""
Chat API endpoint
Handles conversational queries through the multi-agent system
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import json

from app.db.session import get_db
from app.db.models import Conversation
from app.agents.query_understanding import understand_query

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    client_id: Optional[int] = None
    goal: Optional[str] = None
    time_period: Optional[str] = None
    investment_amount: Optional[float] = None  # NEW: Amount client wants to invest


class ChatResponse(BaseModel):
    response: str
    intent: str
    query_type: Optional[str] = None
    compliance_status: Optional[str] = None
    risk_level: Optional[str] = None
    senior_review_required: bool = False


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Process a chat message through the multi-agent system
    
    Flow:
    1. Query Understanding Agent - classify intent
    2. Route to appropriate branch:
       - db_query → SQL Query Builder + DB Responder
       - market_query → Market data tools + Market Intelligence Agent
       - investment_advice → Full advisory pipeline (Phase 3-4)
       - general_chat → General Chat Agent
    3. Persist conversation to database
    4. Return response with metadata
    """
    
    try:
        # Step 1: Understand query
        understanding = await understand_query(
            message=request.message,
            client_id=request.client_id,
            goal=request.goal,
            time_period=request.time_period
        )
        
        print(f"Intent classified: {understanding.intent}")
        print(f"Query type: {understanding.query_type}")
        print(f"Rationale: {understanding.rationale}")
        
        # Step 2: Route based on intent
        if understanding.intent == "general_chat":
            response_text = await handle_general_chat(request.message, understanding)
        
        elif understanding.intent == "db_query":
            response_text = await handle_db_query(request.message, understanding, db)
        
        elif understanding.intent == "market_query":
            response_text = await handle_market_query(request.message, understanding)
        
        elif understanding.intent == "investment_advice":
            # Use LangGraph for investment advice (Phase 5)
            response_text = await handle_investment_advice_with_graph(
                request.message, 
                understanding, 
                request.client_id,
                request.goal,
                request.time_period,
                request.investment_amount,  # NEW
                db
            )
        
        elif understanding.intent == "portfolio_review":
            # NEW: Handle portfolio review (balance, diversification, rebalancing)
            response_text = await handle_portfolio_review(
                request.message,
                understanding,
                request.client_id,
                db
            )
        
        else:
            response_text = "I'm not sure how to handle that request. Could you rephrase?"
        
        # Step 3: Persist conversation
        conversation = Conversation(
            client_id=request.client_id,
            rm_user_id="default_rm",  # TODO: Get from auth context
            role="user",
            intent=understanding.intent,
            content=request.message
        )
        db.add(conversation)
        
        assistant_message = Conversation(
            client_id=request.client_id,
            rm_user_id="default_rm",
            role="assistant",
            intent=understanding.intent,
            content=response_text,
            structured_output=understanding.dict()
        )
        db.add(assistant_message)
        
        await db.commit()
        
        # Step 4: Return response (with metadata if investment_advice)
        compliance_status = None
        risk_level = None
        senior_review = False
        
        # Extract metadata from response if available
        if understanding.intent == "investment_advice":
            # These would be set in the handle_investment_advice function
            # For now, we'll parse from the structured conversation data
            pass
        
        return ChatResponse(
            response=response_text,
            intent=understanding.intent,
            query_type=understanding.query_type,
            compliance_status=compliance_status,
            risk_level=risk_level,
            senior_review_required=senior_review
        )
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_general_chat(message: str, understanding) -> str:
    """
    Handle greetings, thanks, and unclear requests
    Phase 1 implementation: Simple responses
    Phase 2+: Proper General Chat Agent
    """
    
    message_lower = message.lower()
    
    if any(greeting in message_lower for greeting in ["hello", "hi", "hey"]):
        return ("Hello! I'm your AI investment advisor. I can help you with:\n\n"
                "• **Client information** - Search and view client portfolios\n"
                "• **Market data** - Get current prices for stocks, mutual funds, indices, and commodities\n"
                "• **Investment advice** - Generate personalized recommendations\n\n"
                "Try asking about a specific client or current market prices!")
    
    elif any(thanks in message_lower for thanks in ["thank", "thanks"]):
        return "You're welcome! Let me know if you need anything else."
    
    else:
        return ("I can help you with client information, market data, and investment advice. "
                "Could you please clarify what you'd like to know?")


async def handle_db_query(message: str, understanding, db: AsyncSession) -> str:
    """
    Handle database queries using LLM to understand the query and build appropriate response
    Supports: client filters, holdings queries, portfolio queries
    """
    
    from app.db.models import Client, Portfolio, Holding
    from sqlalchemy import select, func
    from app.llm.groq_client import get_groq_client
    import json
    
    # Use LLM to understand what data is being requested
    groq = get_groq_client()
    
    analysis_prompt = f"""Analyze this database query and extract the parameters:

User Query: "{message}"

Database Schema:
- clients: client_id, client_name, age, city, risk_factor (high/medium/low), category, monthly_income
- portfolios: client_id, current_portfolio_value, current_equity_pct, current_mutual_fund_pct, current_gold_pct, current_fd_debt_pct, return_percentage
- holdings: client_id, asset_name, asset_type (stock/mutual_fund/gold/fd_debt), asset_class, current_value, quantity

Identify:
1. query_type: "client_list" | "client_holdings" | "client_portfolio_detail"
2. filters: {{"client_name": string, "risk_factor": "high/medium/low", "asset_type": "stock/mutual_fund/gold/fd_debt", "city": string}}
3. specific_client_name: string if asking about a specific person

Return ONLY valid JSON:
{{
  "query_type": "client_list" or "client_holdings" or "client_portfolio_detail",
  "specific_client_name": "Name" or null,
  "filters": {{"risk_factor": "high", "asset_type": "stock"}},
  "rationale": "brief explanation"
}}"""

    try:
        analysis_text = await groq.structured_output(
            system_prompt="You extract database query parameters. Return ONLY JSON.",
            user_message=analysis_prompt,
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse JSON
        if analysis_text.startswith("```"):
            analysis_text = analysis_text.split("```")[1]
            if analysis_text.startswith("json"):
                analysis_text = analysis_text[4:]
        
        analysis = json.loads(analysis_text)
        
        query_type = analysis.get("query_type")
        specific_client_name = analysis.get("specific_client_name")
        filters = analysis.get("filters", {})
        
        # Handle different query types
        if query_type == "client_holdings":
            # Query holdings for a specific client
            if specific_client_name:
                # Find client by name
                client_query = select(Client).where(
                    func.lower(Client.client_name).like(f"%{specific_client_name.lower()}%")
                )
                client_result = await db.execute(client_query)
                client = client_result.scalar_one_or_none()
                
                if not client:
                    return f"No client found with name matching '{specific_client_name}'."
                
                # Get holdings for this client
                holdings_query = select(Holding).where(Holding.client_id == client.client_id)
                
                # Apply asset_type filter if specified
                if filters.get("asset_type"):
                    holdings_query = holdings_query.where(Holding.asset_type == filters["asset_type"])
                
                holdings_result = await db.execute(holdings_query)
                holdings = holdings_result.scalars().all()
                
                if not holdings:
                    filter_text = f" of type '{filters.get('asset_type')}'" if filters.get("asset_type") else ""
                    return f"No holdings{filter_text} found for {client.client_name}."
                
                # Format response
                filter_text = f" ({filters.get('asset_type').upper()})" if filters.get("asset_type") else ""
                response_lines = [f"## {client.client_name}'s Holdings{filter_text}\n"]
                
                total_value = 0
                for holding in holdings:
                    value = holding.current_value or 0
                    total_value += value
                    response_lines.append(
                        f"• **{holding.asset_name}** ({holding.asset_type}): ₹{value:,.2f}"
                    )
                
                response_lines.append(f"\n**Total Value**: ₹{total_value:,.2f}")
                
                return "\n".join(response_lines)
            else:
                return "Please specify which client's holdings you want to see."
        
        elif query_type == "client_portfolio_detail":
            # Get detailed portfolio info for a specific client
            if specific_client_name:
                client_query = select(Client, Portfolio).join(
                    Portfolio, Client.client_id == Portfolio.client_id
                ).where(
                    func.lower(Client.client_name).like(f"%{specific_client_name.lower()}%")
                )
                result = await db.execute(client_query)
                row = result.first()
                
                if not row:
                    return f"No client found with name matching '{specific_client_name}'."
                
                client, portfolio = row
                
                response = f"""## {client.client_name}'s Portfolio

**Total Value**: ₹{portfolio.current_portfolio_value:,.2f}
**Return**: {portfolio.return_percentage:.2f}%

**Allocation**:
- Equity: {portfolio.current_equity_pct:.1f}%
- Mutual Funds: {portfolio.current_mutual_fund_pct:.1f}%
- Gold: {portfolio.current_gold_pct:.1f}%
- FD/Debt: {portfolio.current_fd_debt_pct:.1f}%

**Client Profile**:
- Age: {client.age}
- Risk: {client.risk_factor.upper()}
- City: {client.city}
"""
                return response
            else:
                return "Please specify which client's portfolio you want to see."
        
        else:  # client_list
            # List clients matching filters
            query = select(Client, Portfolio.current_portfolio_value).join(
                Portfolio, Client.client_id == Portfolio.client_id
            )
            
            # Apply filters
            if filters.get("risk_factor"):
                query = query.where(func.lower(Client.risk_factor) == filters["risk_factor"].lower())
            
            if filters.get("city"):
                query = query.where(func.lower(Client.city).like(f"%{filters['city'].lower()}%"))
            
            result = await db.execute(query)
            rows = result.all()
            
            if not rows:
                filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()])
                return f"No clients found matching filters: {filter_desc}"
            
            # Format response
            filter_desc = ", ".join([f"{k.replace('_', ' ')}={v}" for k, v in filters.items()])
            response_lines = [f"Found {len(rows)} client(s) matching {filter_desc}:\n"]
            
            for client, portfolio_value in rows[:15]:  # Show up to 15
                response_lines.append(
                    f"• **{client.client_name}** ({client.age}, {client.city}) - "
                    f"Portfolio: ₹{portfolio_value:,.0f} | Risk: {client.risk_factor.upper()}"
                )
            
            if len(rows) > 15:
                response_lines.append(f"\n...and {len(rows) - 15} more clients.")
            
            return "\n".join(response_lines)
    
    except Exception as e:
        print(f"Error in DB query handler: {e}")
        import traceback
        traceback.print_exc()
        return f"I had trouble understanding that query. Please try rephrasing (e.g., 'show all high risk clients' or 'show stocks where Arjun has invested')."


async def handle_market_query(message: str, understanding) -> str:
    """
    Handle market data queries with live tools
    Phase 2: Implements parallel tool execution and Market Intelligence Agent
    Enhanced: Supports historical data queries (1 year, last year, etc.)
    Enhanced: Supports top movers/screener queries (this week's top performers)
    """
    import asyncio
    import re
    from app.tools.stock_quote import get_stock_quote
    from app.tools.index_quote import get_index_quote
    from app.tools.mutual_fund import get_mutual_fund_by_name
    from app.tools.commodity import get_commodity_price
    from app.tools.historical_prices import get_stock_historical, get_commodity_historical
    from app.tools.top_movers import get_top_movers, format_top_movers
    from app.agents.market_intelligence import synthesize_market_data
    
    query_type = understanding.query_type
    market_data = {}
    message_lower = message.lower()
    
    # Check if query asks for historical/time-period data
    is_historical_query = any(phrase in message_lower for phrase in [
        "1 year", "one year", "last year", "past year", "12 month", 
        "year ago", "increased", "decreased", "change", "gain", "loss"
    ])
    
    # Check if query asks for top performers/screener
    # IMPORTANT: Only trigger screener if query_type is NOT a specific type (stock/commodity/index/mutual_fund)
    is_screener_query = (query_type in ["general", "sector"]) and any(phrase in message_lower for phrase in [
        "top perform", "best perform", "top gain", "top los",
        "this week", "this month", "screener"
    ])
    
    # Determine which tools to call based on query_type
    tool_calls = []
    
    # Handle screener queries (only if not a specific query type)
    if is_screener_query:
        # Detect period
        if "today" in message_lower or "1 day" in message_lower:
            period = "1d"
        elif "month" in message_lower or "30 day" in message_lower:
            period = "1mo"
        else:  # Default to week
            period = "1wk"
        
        # Detect direction
        if "los" in message_lower or "worst" in message_lower or "declin" in message_lower:
            direction = "losers"
        else:
            direction = "gainers"
        
        # Fetch top movers
        try:
            movers = await get_top_movers(period=period, universe="nifty50", limit=10, direction=direction)
            if movers:
                formatted = await format_top_movers(movers, period, direction)
                return formatted
            else:
                return f"Unable to fetch top {direction} data for {period}. Please try again later."
        except Exception as e:
            print(f"Error in top movers query: {e}")
            return f"Error fetching top {direction} data: {str(e)}"
    
    elif query_type == "stock" and understanding.ticker:
        if is_historical_query:
            # Fetch both current and historical data
            tool_calls.append(("stock", get_stock_quote(understanding.ticker)))
            tool_calls.append(("stock_historical", get_stock_historical(understanding.ticker)))
        else:
            tool_calls.append(("stock", get_stock_quote(understanding.ticker)))
    
    elif query_type == "index":
        # Determine which index from market_topic or default to Nifty
        index_name = "NIFTY"
        if understanding.market_topic:
            topic_lower = understanding.market_topic.lower()
            if "sensex" in topic_lower:
                index_name = "SENSEX"
            elif "bank" in topic_lower:
                index_name = "BANKNIFTY"
        tool_calls.append(("index", get_index_quote(index_name)))
    
    elif query_type == "mutual_fund" and understanding.scheme_name:
        tool_calls.append(("mutual_fund", get_mutual_fund_by_name(understanding.scheme_name)))
    
    elif query_type == "commodity":
        # Determine commodity from market_topic
        commodity_name = "GOLD"  # default
        if understanding.market_topic:
            topic_lower = understanding.market_topic.lower()
            if "silver" in topic_lower:
                commodity_name = "SILVER"
            elif "crude" in topic_lower or "oil" in topic_lower:
                commodity_name = "CRUDE"
        
        if is_historical_query:
            # Fetch both current and historical data
            tool_calls.append(("commodity", get_commodity_price(commodity_name)))
            tool_calls.append(("commodity_historical", get_commodity_historical(commodity_name)))
        else:
            tool_calls.append(("commodity", get_commodity_price(commodity_name)))
    
    elif query_type == "sector":
        # For sector queries, we might want to fetch index + representative stocks
        # For now, just fetch the relevant index
        tool_calls.append(("index", get_index_quote("NIFTY")))
    
    elif query_type == "general":
        # General market overview - fetch Nifty + Gold
        tool_calls.append(("index", get_index_quote("NIFTY")))
        tool_calls.append(("commodity", get_commodity_price("GOLD")))
    
    # Execute all tool calls in parallel
    if tool_calls:
        try:
            results = await asyncio.gather(
                *[call for _, call in tool_calls],
                return_exceptions=True
            )
            
            # Map results to market_data dict
            for (data_type, _), result in zip(tool_calls, results):
                if isinstance(result, Exception):
                    print(f"Tool error for {data_type}: {result}")
                    market_data[f"{data_type}_data"] = None
                else:
                    market_data[f"{data_type}_data"] = result
        
        except Exception as e:
            print(f"Error in parallel tool execution: {e}")
            return f"Error fetching market data: {str(e)}"
    
    # Add context
    market_data["market_topic"] = understanding.market_topic
    market_data["is_historical_query"] = is_historical_query
    
    # Synthesize with Market Intelligence Agent
    try:
        summary = await synthesize_market_data(market_data, message)
        return summary
    except Exception as e:
        print(f"Error in market intelligence synthesis: {e}")
        # Fallback to simple format
        if not any(market_data.values()):
            return "Unable to fetch market data at this time. Please try again."
        
        # Simple fallback formatting
        response_lines = []
        for key, value in market_data.items():
            if value and isinstance(value, dict):
                response_lines.append(f"**{key.replace('_data', '').title()}**: {str(value)}")
        
        return "\n\n".join(response_lines) if response_lines else "No market data available."


async def handle_portfolio_review(
    message: str,
    understanding,
    client_id: Optional[int],
    db: AsyncSession
) -> str:
    """
    Handle portfolio review requests - analyzes EXISTING portfolio
    
    Types:
    - balance_check: Compare actual vs ideal allocation
    - diversification_check: Assess holdings spread
    - rebalancing_check: Determine if rebalancing needed
    """
    from app.agents.client_resolver import resolve_client
    from app.agents.portfolio_reviewer import (
        review_portfolio_balance,
        review_portfolio_diversification,
        review_rebalancing_need,
        format_portfolio_review
    )
    
    if not client_id:
        return ("To review a portfolio, please select a client from the roster first. "
                "I need to analyze their current holdings and allocation.")
    
    try:
        # Resolve client data
        client_data = await resolve_client(
            client_id=client_id,
            client_name=understanding.client_name,
            db=db
        )
        
        if not client_data:
            return "Client not found. Please select a valid client."
        
        profile = client_data["profile"]
        portfolio = client_data["portfolio"]
        holdings = client_data["holdings"]
        
        query_type = understanding.query_type
        
        # Route to appropriate review type
        if query_type == "balance_check":
            review_result = await review_portfolio_balance(profile, portfolio, query_type)
        elif query_type == "diversification_check":
            review_result = await review_portfolio_diversification(profile, holdings, portfolio)
        elif query_type == "rebalancing_check":
            review_result = await review_rebalancing_need(profile, portfolio, holdings)
        else:
            # Default to balance check
            review_result = await review_portfolio_balance(profile, portfolio, "balance_check")
            query_type = "balance_check"
        
        # Format response
        response = format_portfolio_review(review_result, query_type)
        return response
        
    except Exception as e:
        print(f"Error in portfolio review: {e}")
        import traceback
        traceback.print_exc()
        return f"Error reviewing portfolio: {str(e)}\n\nPlease try again or contact support."


async def handle_investment_advice_with_graph(
    message: str,
    understanding,
    client_id: Optional[int],
    goal: Optional[str],
    time_period: Optional[str],
    investment_amount: Optional[float],  # NEW
    db: AsyncSession
) -> str:
    """
    Handle investment advice using LangGraph state machine (Phase 5).
    This replaces the manual orchestration with a proper state graph.
    """
    from app.agents.advisory_graph import run_advisory_graph
    
    if not client_id:
        return ("To provide investment advice, please select a client from the roster first. "
                "I need to know the client's profile, current portfolio, and risk factors.")
    
    try:
        # Run the LangGraph pipeline
        final_state = await run_advisory_graph(
            user_message=message,
            client_id=client_id,
            goal=goal,
            time_period=time_period,
            investment_amount=investment_amount,  # NEW
            db=db
        )
        
        # Check for errors
        if final_state.get("error"):
            return f"Error generating investment advice: {final_state['error']}\n\nPlease try again or contact support."
        
        # Return the formatted response
        response = final_state.get("response")
        if response:
            return response
        else:
            return "Unable to generate recommendation. Please try again."
            
    except Exception as e:
        print(f"Error in LangGraph advisory pipeline: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating investment advice: {str(e)}\n\nPlease try again or contact support."


async def handle_investment_advice(
    message: str,
    understanding,
    client_id: Optional[int],
    goal: Optional[str],
    time_period: Optional[str],
    db: AsyncSession
) -> str:
    """
    Handle investment advice requests - Phase 3 Full Advisory Pipeline
    
    ⚠️ DEPRECATED in Phase 5: This manual orchestration is kept for reference.
    The active implementation now uses LangGraph (see handle_investment_advice_with_graph above).
    
    Pipeline:
    1. Client Data Resolver - SQL lookup
    2. Stock/MF Selector - LLM determines what to fetch
    3. Market data tools - parallel execution
    4. Investment Advisor - LLM generates recommendation
    5. Deterministic Allocation Validator - code checks hard rules
    6. Compliance Agent - LLM checks soft rules
    7. Risk Agent - 5-dimension scoring
    8. Fallback (if compliance fails after max retries)
    """
    import asyncio
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
    
    if not client_id:
        return ("To provide investment advice, please select a client from the roster first. "
                "I need to know the client's profile, current portfolio, and risk factors.")
    
    try:
        # Step 1: Resolve client data (SQL lookup, not table dump)
        client_data = await resolve_client(
            client_id=client_id,
            client_name=understanding.client_name,
            db=db
        )
        
        if not client_data:
            return "Client not found. Please select a valid client."
        
        profile = client_data["profile"]
        portfolio = client_data["portfolio"]
        holdings = client_data["holdings"]
        
        client_name = profile.get("client_name", "Client")
        goal = goal or understanding.goal or "wealth_creation"
        
        # Step 2: Stock/MF Selector - determine what to fetch
        selector_output = await select_stocks_and_mf(
            client_profile=profile,
            goal=goal,
            query_type=understanding.query_type,
            ticker=understanding.ticker,
            time_period=time_period
        )
        
        stocks_to_fetch = selector_output.get("stocks_to_fetch", [])
        sector_name = selector_output.get("sector_name")
        
        # Step 3: Fetch market data in parallel
        tool_calls = []
        
        # Always fetch index for context
        tool_calls.append(("index", get_index_quote("NIFTY")))
        
        # Fetch specific stocks
        for ticker in stocks_to_fetch:
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
                print(f"Tool error for {data_type}: {result}")
                continue
            
            if data_type == "index":
                market_data["index_data"] = result
            elif data_type.startswith("stock_"):
                ticker = data_type.replace("stock_", "")
                stock_data[ticker] = result
        
        market_data["stock_data"] = stock_data
        
        # Synthesize market summary
        market_summary = await synthesize_market_data(market_data, message)
        
        # Determine advisor mode
        query_type = understanding.query_type
        if query_type == "sector":
            advisor_mode = "sector_analysis"
        elif query_type == "stock":
            advisor_mode = "stock_analysis"
        else:
            advisor_mode = "full_plan"
        
        # Compliance retry loop
        MAX_RETRIES = 2
        compliance_retry_count = 0
        used_fallback = False
        advisor_output = None
        compliance_result = None
        
        while compliance_retry_count <= MAX_RETRIES:
            # Step 4: Investment Advisor - generate recommendation
            compliance_feedback = None if compliance_retry_count == 0 else compliance_result
            
            advisor_output = await generate_investment_advice(
                mode=advisor_mode,
                client_profile=profile,
                holdings=holdings,
                portfolio=portfolio,
                market_summary=market_summary,
                goal=goal,
                time_period=time_period,
                query_type=query_type,
                ticker=understanding.ticker,
                sector_name=sector_name,
                compliance_feedback=compliance_feedback
            )
            
            # Step 5: Deterministic Allocation Validator
            allocation = advisor_output.get("allocation", {})
            age = profile.get("age", 40)
            risk_factor = profile.get("risk_factor", "MEDIUM")
            monthly_income = profile.get("monthly_income")
            sip_suggestion = advisor_output.get("monthly_sip_suggestion") or \
                            next((pick.get("sip_per_month") for pick in advisor_output.get("mf_picks", [])), None)
            
            allocation_valid, allocation_violations = validate_allocation(
                allocation=allocation,
                age=age,
                risk_factor=risk_factor,
                goal=goal,
                monthly_income=monthly_income,
                sip_suggestion=sip_suggestion
            )
            
            # Validate picks against market data
            equity_picks = advisor_output.get("equity_picks", [])
            mf_picks = advisor_output.get("mf_picks", [])
            picks_valid, pick_violations = validate_picks_against_market_data(
                equity_picks=equity_picks,
                mf_picks=mf_picks,
                stock_data=stock_data,
                mf_data={}  # TODO: Add MF data once available
            )
            
            if not picks_valid:
                allocation_violations.extend(pick_violations)
                allocation_valid = False
            
            # Check concentration risk
            total_portfolio_value = portfolio.get("current_portfolio_value", 0)
            concentration_warnings = calculate_concentration_risk(
                holdings=holdings,
                new_picks=equity_picks,
                total_portfolio_value=total_portfolio_value
            )
            
            if concentration_warnings:
                allocation_violations.extend(concentration_warnings)
                # Concentration warnings don't fail allocation, but get noted
            
            # Step 6: Compliance Agent
            compliance_result = await check_compliance(
                advisor_output=advisor_output,
                client_profile=profile,
                goal=goal,
                time_period=time_period,
                allocation_valid=allocation_valid,
                allocation_violations=allocation_violations
            )
            
            # Check if compliant
            if compliance_result.get("compliance_status") == "PASS":
                break
            
            # If not compliant, increment retry counter
            compliance_retry_count += 1
            
            if compliance_retry_count > MAX_RETRIES:
                # Exhausted retries - use fallback
                print("Compliance retries exhausted, using fallback allocation")
                fallback = get_fallback_allocation(age, risk_factor, goal)
                advisor_output = fallback
                used_fallback = True
                allocation_valid = True
                allocation_violations = []
                break
        
        # Step 7: Risk Agent
        risk_result = await assess_risk(
            advisor_output=advisor_output,
            client_profile=profile,
            holdings=holdings,
            goal=goal,
            time_period=time_period,
            used_fallback=used_fallback
        )
        
        # Step 8: Format response
        response = format_investment_response(
            client_name=client_name,
            advisor_output=advisor_output,
            compliance_result=compliance_result,
            risk_result=risk_result,
            used_fallback=used_fallback,
            goal=goal,
            time_period=time_period
        )
        
        return response
    
    except Exception as e:
        print(f"Error in investment advice pipeline: {e}")
        import traceback
        traceback.print_exc()
        return f"Error generating investment advice: {str(e)}\n\nPlease try again or contact support."


def format_investment_response(
    client_name: str,
    advisor_output: dict,
    compliance_result: dict,
    risk_result: dict,
    used_fallback: bool,
    goal: str,
    time_period: Optional[str],
    capital_allocation: Optional[dict] = None,
    investment_amount: Optional[float] = None
) -> str:
    """Format the final investment response for the RM - Handles different advisor modes"""
    
    lines = []
    
    # Check if this is a stock-specific analysis
    is_stock_analysis = advisor_output.get("recommendation") in ["BUY", "HOLD", "AVOID", "YES", "NO"]
    ticker = advisor_output.get("ticker")
    
    if is_stock_analysis and ticker:
        # STOCK-SPECIFIC RESPONSE FORMAT
        recommendation = advisor_output.get("recommendation", "HOLD")
        current_price = advisor_output.get("current_price", 0)
        suggested_amount = advisor_output.get("suggested_amount", 0)
        suggested_time = advisor_output.get("suggested_time_horizon", time_period or "5-7 years")
        one_year_return = advisor_output.get("one_year_return", "N/A")
        key_reasons = advisor_output.get("key_reasons", [])
        detailed_rationale = advisor_output.get("detailed_rationale", advisor_output.get("rationale", ""))
        risks = advisor_output.get("risks", [])
        portfolio_impact = advisor_output.get("portfolio_impact", advisor_output.get("concentration_check", ""))
        alternative = advisor_output.get("alternative_suggestion", "")
        
        # Header with clear verdict
        lines.append(f"# Should {client_name} Invest in {ticker}?")
        
        if recommendation in ["YES", "BUY"]:
            lines.append(f"\n## 🟢 **YES - RECOMMENDED**")
        else:
            lines.append(f"\n## 🔴 **NO - NOT RECOMMENDED**")
        
        # Key Information
        lines.append(f"\n### Stock Information")
        lines.append(f"- **Current Price:** ₹{current_price:,.2f}")
        lines.append(f"- **1-Year Performance:** {one_year_return}")
        
        if suggested_amount and recommendation in ["YES", "BUY"]:
            shares = int(suggested_amount / current_price) if current_price > 0 else 0
            lines.append(f"- **Suggested Investment:** ₹{suggested_amount/100000:.1f}L (~{shares} shares)")
            lines.append(f"- **Recommended Time Horizon:** {suggested_time}")
        
        # Key Reasons (Bullet Points)
        if key_reasons:
            lines.append(f"\n### Key Reasons")
            for reason in key_reasons:
                lines.append(f"• {reason}")
        
        # Detailed Analysis
        lines.append(f"\n### Detailed Analysis")
        lines.append(detailed_rationale)
        
        # Portfolio Impact
        if portfolio_impact:
            lines.append(f"\n### Portfolio Impact")
            lines.append(portfolio_impact)
        
        # Risk Factors
        if risks:
            lines.append(f"\n### Risk Factors")
            for risk in risks:
                lines.append(f"• {risk}")
        
        # Alternative Suggestion
        if alternative:
            lines.append(f"\n### {('Diversification Strategy' if recommendation in ['YES', 'BUY'] else 'Alternative Suggestion')}")
            lines.append(alternative)
        
        # Investment Context
        context_parts = []
        if goal:
            context_parts.append(f"Goal: {goal.replace('_', ' ').title()}")
        if time_period:
            context_parts.append(f"Time Horizon: {time_period}")
        if context_parts:
            lines.append(f"\n**Investment Context:** {' | '.join(context_parts)}")
        
        
    else:
        # FULL PLAN RESPONSE FORMAT (Original compact format)
        header_parts = [f"**Goal:** {goal.replace('_', ' ').title()}"]
        if time_period:
            header_parts.append(f"**Time:** {time_period}")
        if investment_amount:
            header_parts.append(f"**Amount:** ₹{investment_amount/100000:.1f}L")
        
        lines.append(f"# Investment Plan for {client_name}")
        lines.append(" | ".join(header_parts))
        
        if used_fallback:
            lines.append(f"\n⚠️ Using rule-based allocation\n")
        
        # Capital allocation detail
        if capital_allocation and investment_amount:
            from app.agents.capital_allocator import format_capital_allocation
            lines.append(format_capital_allocation(capital_allocation, investment_amount))
        
        # Compact Allocation
        allocation = advisor_output.get("allocation", {})
        if allocation:
            lines.append(f"\n## Asset Allocation")
            alloc_parts = []
            if allocation.get('equity_pct', 0) > 0:
                alloc_parts.append(f"Equity {allocation.get('equity_pct')}%")
            if allocation.get('mutual_fund_pct', 0) > 0:
                alloc_parts.append(f"Mutual Funds {allocation.get('mutual_fund_pct')}%")
            if allocation.get('gold_pct', 0) > 0:
                alloc_parts.append(f"Gold {allocation.get('gold_pct')}%")
            if allocation.get('fd_debt_pct', 0) > 0:
                alloc_parts.append(f"Debt {allocation.get('fd_debt_pct')}%")
            lines.append(" • ".join(alloc_parts))
        
        # Detailed Equity picks
        equity_picks = advisor_output.get("equity_picks", [])
        if equity_picks and not used_fallback:
            lines.append(f"\n## Equity Recommendations")
            for pick in equity_picks:  # Show ALL picks, not just top 3
                ticker_sym = pick.get("ticker", "N/A")
                sector = pick.get("sector", "")
                amount = pick.get("suggested_amount", 0)
                price = pick.get("current_price", 0)
                rat = pick.get("rationale", "")  # Show FULL rationale
                
                lines.append(f"\n**{ticker_sym}** ({sector})")
                lines.append(f"- Investment: ₹{amount/1000:.0f}K @ ₹{price:.0f}/share")
                lines.append(f"- Rationale: {rat}")
        elif used_fallback and advisor_output.get("equity_recommendation"):
            lines.append(f"\n## Equity")
            lines.append(advisor_output.get("equity_recommendation"))
        
        # Detailed MF picks  
        mf_picks = advisor_output.get("mf_picks", [])
        if mf_picks and not used_fallback:
            lines.append(f"\n## Mutual Fund Recommendations")
            for pick in mf_picks:  # Show ALL picks
                scheme = pick.get("scheme_name", "N/A")
                category = pick.get("category", "")
                amount = pick.get("suggested_amount", 0)
                sip = pick.get("sip_per_month", 0)
                rat = pick.get("rationale", "")  # Show FULL rationale
                
                lines.append(f"\n**{scheme}** ({category})")
                if sip:
                    lines.append(f"- Options: ₹{amount/1000:.0f}K lumpsum OR ₹{sip/1000:.0f}K/month SIP")
                else:
                    lines.append(f"- Investment: ₹{amount/1000:.0f}K lumpsum")
                lines.append(f"- Rationale: {rat}")
        elif used_fallback and advisor_output.get("mf_recommendation"):
            lines.append(f"\n## Mutual Funds")
            lines.append(advisor_output.get("mf_recommendation"))
        
        # Gold recommendations (detailed)
        gold_reco = advisor_output.get("gold_recommendation")
        if gold_reco:
            lines.append(f"\n## Gold Investment")
            lines.append(gold_reco)
        
        # FD/Debt recommendations (detailed)
        fd_reco = advisor_output.get("fd_recommendation")
        if fd_reco:
            lines.append(f"\n## Fixed Deposits & Debt")
            lines.append(fd_reco)
        
        # Overall rationale (detailed)
        overall_rationale = advisor_output.get("rationale")
        if overall_rationale:
            lines.append(f"\n## Investment Strategy Rationale")
            lines.append(overall_rationale)
    
    # Risk assessment (common for both formats)
    lines.append(f"\n## Risk Profile")
    lines.append(f"**Level:** {risk_result.get('risk_level', 'unknown').upper()} "
                f"(Score: {risk_result.get('overall_risk_score', 0)}/10)")
    
    risk_breakdown = [
        f"Market {risk_result.get('market_risk', 0)}/10",
        f"Liquidity {risk_result.get('liquidity_risk', 0)}/10",
        f"Concentration {risk_result.get('concentration_risk', 0)}/10"
    ]
    lines.append(" • ".join(risk_breakdown))
    
    # Warnings (compact)
    warnings = []
    if risk_result.get("senior_review_required"):
        warnings.append("⚠️ Senior review required")
    if compliance_result.get("compliance_status") == "FAIL":
        issues = compliance_result.get("issues", [])
        if issues:
            warnings.append(f"⚠️ Compliance: {len(issues)} issue(s)")
    
    if warnings:
        lines.append(f"\n{' | '.join(warnings)}")
    
    lines.append(f"\n---")
    lines.append(f"*AI-generated recommendation. Review with client before implementation.*")
    
    return "\n".join(lines)
