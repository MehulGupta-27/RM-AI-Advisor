"""
Market Intelligence Agent
Synthesizes live market data from multiple tools into factual, numbers-first summaries
"""

import httpx
import json
import os
from typing import Dict, Optional


SYSTEM_PROMPT = """You are a Market Intelligence Agent for an Indian investment advisory system.

Your job is to synthesize live market data into clear, factual summaries for Relationship Managers.

Rules:
1. **Numbers first** - Always lead with actual prices and values
2. **State what's available** - If data is missing, explicitly say "Data unavailable for X"
3. **No speculation** - Only report what the data shows, no predictions
4. **Context matters** - Compare to previous close, mention direction (up/down)
5. **Be concise** - 2-3 sentences per data point maximum
6. **INR-first for Indian context** - Show ₹ prices prominently, USD in parentheses

Format your response in markdown with clear sections if multiple data types are present.

Example good response for stock query:
"**Reliance Industries (RELIANCE.NS)**
Current Price: ₹2,450.50 (+₹12.30, +0.50%)
Day Range: ₹2,438 - ₹2,465
52-Week Range: ₹2,100 - ₹2,800
Volume: 1.2M shares

The stock is trading in positive territory today, up from yesterday's close of ₹2,438.20."

Example for unavailable data:
"Stock data unavailable for INVALID at this time. This could be due to market hours, ticker mismatch, or API connectivity. Please verify the ticker symbol."
"""


async def synthesize_market_data(
    market_data: Dict,
    query_context: Optional[str] = None
) -> str:
    """
    Synthesize market data into natural language summary
    
    Args:
        market_data: Dict containing tool outputs
            {
                'stock_data': {...} or None,
                'index_data': {...} or None,
                'mutual_fund_data': {...} or None,
                'commodity_data': {...} or None,
                'market_topic': str (optional)
            }
        query_context: Original user query for context
        
    Returns:
        Natural language market summary
    """
    
    # Build context for the LLM
    data_summary = []
    
    # Stock data
    if market_data.get('stock_data'):
        # Handle both single stock and multiple stocks
        if isinstance(market_data['stock_data'], dict) and not market_data['stock_data'].get('symbol'):
            # Multiple stocks (dictionary of ticker -> data)
            for ticker, stock in market_data['stock_data'].items():
                if stock and stock.get('symbol'):
                    price = stock.get('price')
                    change = stock.get('change')
                    change_pct = stock.get('change_percent')
                    day_low = stock.get('day_low')
                    day_high = stock.get('day_high')
                    prev_close = stock.get('previous_close')
                    
                    price_str = f"₹{price}" if price is not None else "N/A"
                    change_str = f"{change:+.2f}" if change is not None else "N/A"
                    change_pct_str = f"{change_pct:+.2f}" if change_pct is not None else "N/A"
                    day_low_str = f"₹{day_low}" if day_low is not None else "N/A"
                    day_high_str = f"₹{day_high}" if day_high is not None else "N/A"
                    prev_close_str = f"₹{prev_close}" if prev_close is not None else "N/A"
                    
                    data_summary.append(f"""
**Stock: {stock['symbol']}**
- Current Price: {price_str}
- Change: {change_str} ({change_pct_str}%)
- Day Range: {day_low_str} - {day_high_str}
- Previous Close: {prev_close_str}
""")
        else:
            # Single stock
            stock = market_data['stock_data']
            if stock and stock.get('symbol'):
                price = stock.get('price')
                change = stock.get('change')
                change_pct = stock.get('change_percent')
                day_low = stock.get('day_low')
                day_high = stock.get('day_high')
                prev_close = stock.get('previous_close')
                
                price_str = f"₹{price}" if price is not None else "N/A"
                change_str = f"{change:+.2f}" if change is not None else "N/A"
                change_pct_str = f"{change_pct:+.2f}" if change_pct is not None else "N/A"
                day_low_str = f"₹{day_low}" if day_low is not None else "N/A"
                day_high_str = f"₹{day_high}" if day_high is not None else "N/A"
                prev_close_str = f"₹{prev_close}" if prev_close is not None else "N/A"
                
                data_summary.append(f"""
**Stock: {stock['symbol']}**
- Current Price: {price_str}
- Change: {change_str} ({change_pct_str}%)
- Day Range: {day_low_str} - {day_high_str}
- Previous Close: {prev_close_str}
""")
            else:
                data_summary.append("Stock data unavailable.")
    
    # Index data
    if market_data.get('index_data'):
        index = market_data['index_data']
        if index.get('index'):
            level = index.get('level')
            change = index.get('change', 0)
            change_pct = index.get('change_percent', 0)
            day_low = index.get('day_low')
            day_high = index.get('day_high')
            prev_close = index.get('previous_close')
            
            level_str = f"{level:.2f}" if level is not None else "N/A"
            change_str = f"{change:+.2f}" if change is not None else "N/A"
            change_pct_str = f"{change_pct:+.2f}" if change_pct is not None else "N/A"
            day_low_str = f"{day_low:.2f}" if day_low is not None else "N/A"
            day_high_str = f"{day_high:.2f}" if day_high is not None else "N/A"
            prev_close_str = f"{prev_close:.2f}" if prev_close is not None else "N/A"
            
            data_summary.append(f"""
**Index: {index['index']}**
- Current Level: {level_str}
- Change: {change_str} ({change_pct_str}%)
- Day Range: {day_low_str} - {day_high_str}
- Previous Close: {prev_close_str}
""")
        else:
            data_summary.append("Index data unavailable.")
    
    # Mutual fund data
    if market_data.get('mutual_fund_data'):
        mf = market_data['mutual_fund_data']
        if mf.get('scheme_name'):
            nav = mf.get('nav')
            nav_str = f"{nav:.4f}" if nav is not None else "N/A"
            data_summary.append(f"""
**Mutual Fund: {mf['scheme_name']}**
- Latest NAV: ₹{nav_str}
- Date: {mf.get('date', 'N/A')}
- Category: {mf.get('scheme_category', 'N/A')}
- Fund House: {mf.get('fund_house', 'N/A')}
""")
        else:
            data_summary.append("Mutual fund data unavailable.")
    
    # Commodity data
    if market_data.get('commodity_data'):
        commodity = market_data['commodity_data']
        if commodity.get('commodity'):
            lines = [f"**Commodity: {commodity['commodity']}**"]
            lines.append(f"- Price: ${commodity.get('price_usd', 'N/A'):.2f}/oz")
            
            if 'price_inr_per_10g' in commodity:
                lines.append(f"- Price (INR): ₹{commodity['price_inr_per_10g']:.2f}/10g")
            elif 'price_inr_per_kg' in commodity:
                lines.append(f"- Price (INR): ₹{commodity['price_inr_per_kg']:.2f}/kg")
            
            lines.append(f"- Change: {commodity.get('change', 0):+.2f} ({commodity.get('change_percent', 0):+.2f}%)")
            
            # Add disclaimer if present
            if 'disclaimer' in commodity:
                lines.append(f"\n{commodity['disclaimer']}")
            
            data_summary.append("\n".join(lines))
        else:
            data_summary.append("Commodity data unavailable.")
    
    # Historical stock data (1-year)
    if market_data.get('stock_historical_data'):
        hist = market_data['stock_historical_data']
        if hist and hist.get('symbol'):
            lines = [f"**{hist['symbol']} - 1 Year Performance**"]
            lines.append(f"- Current Price: ₹{hist.get('current_price', 0):.2f}")
            lines.append(f"- Price 1 Year Ago: ₹{hist.get('price_1y_ago', 0):.2f}")
            lines.append(f"- 1-Year Change: ₹{hist.get('change_1y', 0):+.2f} ({hist.get('change_1y_percent', 0):+.2f}%)")
            lines.append(f"- 52-Week High: ₹{hist.get('high_1y', 0):.2f}")
            lines.append(f"- 52-Week Low: ₹{hist.get('low_1y', 0):.2f}")
            data_summary.append("\n".join(lines))
    
    # Historical commodity data (1-year)
    if market_data.get('commodity_historical_data'):
        hist = market_data['commodity_historical_data']
        if hist and hist.get('commodity'):
            lines = [f"**{hist['commodity']} - 1 Year Performance**"]
            lines.append(f"- Current Price: ${hist.get('current_price_usd', 0):.2f}/oz")
            lines.append(f"- Price 1 Year Ago: ${hist.get('price_1y_ago_usd', 0):.2f}/oz")
            lines.append(f"- 1-Year Change: ${hist.get('change_1y_usd', 0):+.2f} ({hist.get('change_1y_percent', 0):+.2f}%)")
            
            if 'current_price_inr_per_10g' in hist:
                lines.append(f"- Current Price (INR): ₹{hist['current_price_inr_per_10g']:.2f}/10g")
                lines.append(f"- Price 1 Year Ago (INR): ₹{hist['price_1y_ago_inr_per_10g']:.2f}/10g")
                lines.append(f"- 1-Year Change (INR): ₹{hist['change_1y_inr']:+.2f}")
            
            data_summary.append("\n".join(lines))
    
    if not data_summary:
        return "No market data was fetched. Please check your query and try again."
    
    # Prepare user prompt
    user_prompt = "Synthesize the following market data into a clear summary:\n\n"
    user_prompt += "\n".join(data_summary)
    
    if query_context:
        user_prompt += f"\n\nOriginal query context: {query_context}"
    
    # Call LLM for synthesis
    try:
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
                    "temperature": 0.3,  # Slightly higher for natural language
                    "max_tokens": 800
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            return content.strip()
    
    except Exception as e:
        print(f"Error in market intelligence synthesis: {e}")
        # Fallback: return raw data summary
        return "\n".join(data_summary)


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Mock market data
        test_data = {
            "stock_data": {
                "symbol": "RELIANCE",
                "price": 2450.50,
                "change": 12.30,
                "change_percent": 0.50,
                "day_low": 2438,
                "day_high": 2465,
                "52w_low": 2100,
                "52w_high": 2800,
                "previous_close": 2438.20
            },
            "index_data": {
                "index": "NIFTY",
                "level": 21580.50,
                "change": 45.30,
                "change_percent": 0.21,
                "day_low": 21520,
                "day_high": 21600,
                "previous_close": 21535.20
            }
        }
        
        summary = await synthesize_market_data(
            test_data,
            query_context="What's the current market situation?"
        )
        
        print(summary)
    
    asyncio.run(test())
