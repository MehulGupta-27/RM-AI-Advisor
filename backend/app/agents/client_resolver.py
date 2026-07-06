"""
Client Data Resolver - SQL-based lookup (not table dump)
Fixes Bug #2 from spec: no more dumping entire client roster into prompts
"""

from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text


async def resolve_client(
    client_id: Optional[int],
    client_name: Optional[str],
    db: AsyncSession
) -> Optional[Dict]:
    """
    Resolve client by ID or name, return profile + portfolio + holdings.
    This is the ONLY way client data enters the advisory pipeline.
    """
    print(f"[CLIENT RESOLVER] Input: client_id={client_id}, client_name={client_name}")
    
    # If no client_id but we have a name, look it up
    if client_id is None and client_name:
        query = text(
            "SELECT client_id FROM clients WHERE lower(client_name) = lower(:name) LIMIT 1"
        )
        result = await db.execute(query, {"name": client_name})
        row = result.fetchone()
        if row:
            client_id = row[0]
            print(f"[CLIENT RESOLVER] Looked up '{client_name}' → client_id={client_id}")
    
    # If still no client_id, we can't resolve
    if client_id is None:
        print(f"[CLIENT RESOLVER] No client_id available, returning None")
        return None
    
    # Fetch profile
    profile_query = text("SELECT * FROM clients WHERE client_id = :id")
    profile_result = await db.execute(profile_query, {"id": client_id})
    profile_row = profile_result.fetchone()
    
    if not profile_row:
        print(f"[CLIENT RESOLVER] client_id={client_id} not found in database")
        return None
    
    # Fetch portfolio
    portfolio_query = text("SELECT * FROM portfolios WHERE client_id = :id")
    portfolio_result = await db.execute(portfolio_query, {"id": client_id})
    portfolio_row = portfolio_result.fetchone()
    
    # Fetch holdings
    holdings_query = text("SELECT * FROM holdings WHERE client_id = :id")
    holdings_result = await db.execute(holdings_query, {"id": client_id})
    holdings_rows = holdings_result.fetchall()
    
    # Convert to dicts
    profile_dict = dict(profile_row._mapping) if profile_row else {}
    portfolio_dict = dict(portfolio_row._mapping) if portfolio_row else {}
    holdings_list = [dict(h._mapping) for h in holdings_rows]
    
    resolved_name = profile_dict.get('client_name', 'Unknown')
    print(f"[CLIENT RESOLVER] Resolved to: {resolved_name} (ID: {client_id})")
    
    return {
        "profile": profile_dict,
        "portfolio": portfolio_dict,
        "holdings": holdings_list
    }
