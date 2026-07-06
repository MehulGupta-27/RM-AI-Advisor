"""
Query Understanding Agent
Classifies user intent and extracts entities from natural language queries

Intent types:
- db_query: Search/filter/count clients or look up holdings/portfolio
- investment_advice: Wants recommendation for a specific client
- market_query: Wants live stock/MF/gold/commodity/index data
- general_chat: Greetings, thanks, unclear requests
"""

import json
import httpx
import os
from typing import Optional, Literal
from pydantic import BaseModel


class QueryUnderstanding(BaseModel):
    """Structured output from Query Understanding Agent"""
    intent: Literal["db_query", "market_query", "investment_advice", "portfolio_review", "general_chat"]
    client_name: Optional[str] = None  # For db_query free-text roster search
    goal: Optional[str] = None
    time_period: Optional[str] = None
    query_type: Literal["stock", "mutual_fund", "sector", "commodity", "index", "general", "balance_check", "diversification_check", "rebalancing_check"] = "general"
    ticker: Optional[str] = None
    scheme_name: Optional[str] = None
    db_filter: Optional[str] = None
    market_topic: Optional[str] = None
    rationale: Optional[str] = None  # Why this classification


SYSTEM_PROMPT = """You are a strict JSON extractor for an Indian investment advisory system used by bank RMs.

Classify the user's message into exactly one intent:
1. db_query — search/filter/count clients or look up someone's holdings/portfolio
2. investment_advice — wants a NEW recommendation for a specific client (new money to invest, create a plan, which sector/stock to buy)
3. portfolio_review — wants to ANALYZE the portfolio the client ALREADY HAS (is it balanced? diversified? needs rebalancing?)
4. market_query — wants live stock/MF/gold/commodity/index data with NO investment recommendation
5. general_chat — greetings, thanks, unclear requests, or anything not covered above

CRITICAL Classification rules:
- "should X invest in [stock]" → investment_advice (requires both market data + personalized recommendation for NEW investment)
- "what is the price of [stock]" → market_query (only needs market data, no advice)
- "gold price", "nifty level", "reliance stock price" → market_query (just data)
- "where/how should X invest", "create plan for X", "X has 5 lakhs to invest" → investment_advice
- "show clients", "list high risk", "who has X" → db_query
- "hello", "thanks", unclear → general_chat

**NEW**: Distinguish investment_advice vs portfolio_review:
- "is X's portfolio balanced" → portfolio_review / balance_check (analyzes EXISTING allocation)
- "is X's portfolio diversified" → portfolio_review / diversification_check (analyzes EXISTING holdings)
- "does X need rebalancing" → portfolio_review / rebalancing_check (compares EXISTING vs IDEAL allocation)
- "where should X invest NEW capital" → investment_advice (generates NEW recommendations)
- "should X invest in [stock]" → investment_advice (NEW purchase decision)

For investment_advice with a specific stock:
- Set query_type = "stock"
- Extract ticker (NSE symbol like WIPRO, TCS, RELIANCE)
- This triggers: fetch market data + analyze client + give BUY/HOLD/AVOID recommendation

For portfolio_review:
- Set query_type = "balance_check" OR "diversification_check" OR "rebalancing_check"
- This triggers: analyze EXISTING portfolio WITHOUT generating new picks

For market_query:
- Only returns market data, NO investment advice
- Examples: "wipro price", "gold rate", "nifty today"

Return ONLY valid JSON matching this schema:
{
  "intent": "db_query" | "market_query" | "investment_advice" | "portfolio_review" | "general_chat",
  "client_name": string or null,
  "goal": string or null,
  "time_period": string or null,
  "query_type": "stock" | "mutual_fund" | "sector" | "commodity" | "index" | "general" | "balance_check" | "diversification_check" | "rebalancing_check",
  "ticker": string or null (NSE symbol WITHOUT .NS suffix),
  "scheme_name": string or null,
  "db_filter": string or null,
  "market_topic": string or null,
  "rationale": "brief explanation of classification"
}

EXAMPLES showing the distinction:

User: "is Vikas Gupta's portfolio balanced"
→ {"intent": "portfolio_review", "query_type": "balance_check", "rationale": "Asks to analyze existing portfolio allocation"}

User: "where should Vikas Gupta invest 5 lakhs"
→ {"intent": "investment_advice", "query_type": "general", "rationale": "Asks for new investment recommendation"}

User: "should Vikas Gupta invest in Wipro"
→ {"intent": "investment_advice", "query_type": "stock", "ticker": "WIPRO", "rationale": "Asks for new stock purchase decision"}

User: "is Vikas Gupta's portfolio diversified"
→ {"intent": "portfolio_review", "query_type": "diversification_check", "rationale": "Asks to analyze existing holdings diversification"}

User: "does Vikas Gupta need rebalancing"
→ {"intent": "portfolio_review", "query_type": "rebalancing_check", "rationale": "Asks if existing allocation needs adjustment"}

No markdown, no explanation, ONLY the JSON object."""


async def understand_query(
    message: str,
    client_id: Optional[int] = None,
    goal: Optional[str] = None,
    time_period: Optional[str] = None
) -> QueryUnderstanding:
    """
    Classify user intent and extract entities
    
    Args:
        message: User's natural language query
        client_id: Already selected client (from UI context)
        goal: Already selected goal (from UI selector)
        time_period: Already selected time period (from UI selector)
        
    Returns:
        QueryUnderstanding with classified intent and extracted entities
    """
    
    # Build context for the LLM
    context_lines = [f"User message: {message}"]
    
    if client_id:
        context_lines.append(f"Context: Client ID {client_id} is already selected in the UI")
    
    if goal:
        context_lines.append(f"Context: Goal already set to '{goal}'")
    
    if time_period:
        context_lines.append(f"Context: Time period already set to '{time_period}'")
    
    user_prompt = "\n".join(context_lines)
    
    # Call Groq API
    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{groq_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,  # Low temperature for consistent classification
                "max_tokens": 500
            },
            timeout=30.0
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract content
        content = result["choices"][0]["message"]["content"]
        
        # Parse JSON (handle potential markdown wrapping)
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        # Parse and validate
        data = json.loads(content)
        
        # Override with context values if provided
        if goal and not data.get("goal"):
            data["goal"] = goal
        if time_period and not data.get("time_period"):
            data["time_period"] = time_period
        
        return QueryUnderstanding(**data)


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test cases
        test_cases = [
            ("Hello, how can you help me?", None),
            ("Show me all high risk clients", None),
            ("What's the current Nifty level?", None),
            ("Create a plan for Rajesh Kumar", None),
            ("Should Priya invest in banking sector?", 5),
        ]
        
        for message, client_id in test_cases:
            print(f"\nMessage: {message}")
            if client_id:
                print(f"Context: Client {client_id} selected")
            
            result = await understand_query(message, client_id=client_id)
            print(f"Intent: {result.intent}")
            print(f"Query type: {result.query_type}")
            print(f"Rationale: {result.rationale}")
    
    asyncio.run(test())
