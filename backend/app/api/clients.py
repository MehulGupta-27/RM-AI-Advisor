"""
Client API endpoints
Provides client roster and individual client details with live portfolio metrics
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import Client, Portfolio, Holding

router = APIRouter()


# Response models
class ClientListItem(BaseModel):
    client_id: int
    client_name: str
    age: int
    risk_factor: str
    city: str
    
    # Computed metrics
    category: str  # Derived from AUM tier
    current_portfolio_value: float
    ytd_return: float
    holdings_count: int
    
    class Config:
        from_attributes = True


class ClientDetail(BaseModel):
    # Profile
    client_id: int
    client_name: str
    age: int
    risk_factor: str
    monthly_income: float
    annual_income: float
    city: str
    gender: str
    occupation: str
    risk_score: float
    
    # Portfolio summary
    current_portfolio_value: float
    total_invested: float
    total_returns: float
    return_percentage: float
    current_equity_pct: float
    current_mutual_fund_pct: float
    current_gold_pct: float
    current_fd_debt_pct: float
    
    # Holdings
    holdings_count: int
    
    class Config:
        from_attributes = True


class HoldingItem(BaseModel):
    holding_id: int
    asset_type: str
    asset_name: str
    quantity: float
    current_price: float
    current_value: float
    invested_amount: float
    profit_loss: float
    
    class Config:
        from_attributes = True


def get_category_from_aum(aum: float) -> str:
    """Derive client category from AUM tier"""
    if aum >= 10000000:  # 1 crore+
        return "Premium"
    elif aum >= 5000000:  # 50 lakhs+
        return "High Value"
    elif aum >= 1000000:  # 10 lakhs+
        return "Affluent"
    else:
        return "Retail"


@router.get("/clients", response_model=List[ClientListItem])
async def get_clients(
    search: Optional[str] = None,
    risk_factor: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all clients with live portfolio metrics
    
    Query params:
    - search: Filter by name or city (optional)
    - risk_factor: Filter by risk tier HIGH/MEDIUM/LOW (optional)
    """
    
    # Build query
    query = select(
        Client,
        Portfolio.current_portfolio_value,
        Portfolio.return_percentage,
        func.count(Holding.holding_id).label('holdings_count')
    ).join(
        Portfolio, Client.client_id == Portfolio.client_id
    ).outerjoin(
        Holding, Client.client_id == Holding.client_id
    ).group_by(
        Client.client_id,
        Portfolio.portfolio_id
    )
    
    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Client.client_name.ilike(search_term)) | 
            (Client.city.ilike(search_term))
        )
    
    if risk_factor:
        query = query.where(Client.risk_factor == risk_factor.upper())
    
    # Execute
    result = await db.execute(query)
    rows = result.all()
    
    # Format response
    clients = []
    for row in rows:
        client = row[0]
        portfolio_value = float(row[1] or 0)
        ytd_return = float(row[2] or 0)
        holdings_count = row[3]
        
        clients.append(ClientListItem(
            client_id=client.client_id,
            client_name=client.client_name,
            age=client.age,
            risk_factor=client.risk_factor,
            city=client.city,
            category=get_category_from_aum(portfolio_value),
            current_portfolio_value=portfolio_value,
            ytd_return=ytd_return,
            holdings_count=holdings_count
        ))
    
    return clients


@router.get("/clients/{client_id}", response_model=ClientDetail)
async def get_client_detail(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed client profile, portfolio summary, and holdings
    """
    
    # Get client
    result = await db.execute(
        select(Client).where(Client.client_id == client_id)
    )
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get portfolio
    result = await db.execute(
        select(Portfolio).where(Portfolio.client_id == client_id)
    )
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Get holdings count
    result = await db.execute(
        select(func.count(Holding.holding_id)).where(Holding.client_id == client_id)
    )
    holdings_count = result.scalar()
    
    # Format response
    return ClientDetail(
        # Profile
        client_id=client.client_id,
        client_name=client.client_name,
        age=client.age,
        risk_factor=client.risk_factor,
        monthly_income=float(client.monthly_income or 0),
        annual_income=float(client.annual_income or 0),
        city=client.city,
        gender=client.gender or "",
        occupation=client.occupation or "",
        risk_score=float(client.risk_score or 0),
        
        # Portfolio
        current_portfolio_value=float(portfolio.current_portfolio_value or 0),
        total_invested=float(portfolio.total_invested or 0),
        total_returns=float(portfolio.total_returns or 0),
        return_percentage=float(portfolio.return_percentage or 0),
        current_equity_pct=float(portfolio.current_equity_pct or 0),
        current_mutual_fund_pct=float(portfolio.current_mutual_fund_pct or 0),
        current_gold_pct=float(portfolio.current_gold_pct or 0),
        current_fd_debt_pct=float(portfolio.current_fd_debt_pct or 0),
        
        holdings_count=holdings_count
    )


@router.get("/clients/{client_id}/holdings", response_model=List[HoldingItem])
async def get_client_holdings(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all holdings for a specific client
    """
    
    result = await db.execute(
        select(Holding).where(Holding.client_id == client_id)
    )
    holdings = result.scalars().all()
    
    return [
        HoldingItem(
            holding_id=h.holding_id,
            asset_type=h.asset_type,
            asset_name=h.asset_name,
            quantity=float(h.quantity or 0),
            current_price=float(h.current_price or 0),
            current_value=float(h.current_value or 0),
            invested_amount=float(h.invested_amount or 0),
            profit_loss=float(h.profit_loss or 0)
        )
        for h in holdings
    ]


@router.get("/clients/{client_id}/messages")
async def get_client_messages(
    client_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get conversation history for a specific client
    For chat replay when client is reselected
    """
    from app.db.models import Conversation
    
    result = await db.execute(
        select(Conversation)
        .where(Conversation.client_id == client_id)
        .order_by(Conversation.created_at.desc())
        .limit(limit)
    )
    
    messages = result.scalars().all()
    
    return [
        {
            "conversation_id": m.conversation_id,
            "role": m.role,
            "content": m.content,
            "intent": m.intent,
            "compliance_status": m.compliance_status,
            "risk_level": m.risk_level,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in reversed(list(messages))  # Reverse to get chronological order
    ]
