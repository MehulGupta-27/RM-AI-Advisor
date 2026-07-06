"""
SQLAlchemy models for existing tables
Note: clients, portfolios, holdings tables already exist in the database
These models just map to the existing schema for ORM access
"""

from sqlalchemy import Column, Integer, String, Numeric, Date, BigInteger, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class Client(Base):
    """Client profile - maps to existing clients table"""
    __tablename__ = "clients"
    
    client_id = Column(Integer, primary_key=True)
    client_name = Column(String(100), nullable=False)
    age = Column(Integer)
    risk_factor = Column(String(20))  # HIGH, MEDIUM, LOW
    monthly_income = Column(Numeric(12, 2))
    city = Column(String(50))
    gender = Column(String(10))
    occupation = Column(String(100))
    annual_income = Column(Numeric(15, 2))
    risk_score = Column(Numeric(5, 2))


class Portfolio(Base):
    """Portfolio summary - maps to existing portfolios table"""
    __tablename__ = "portfolios"
    
    portfolio_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    current_portfolio_value = Column(Numeric(15, 2))
    total_invested = Column(Numeric(15, 2))
    total_returns = Column(Numeric(15, 2))
    return_percentage = Column(Numeric(5, 2))
    current_equity_pct = Column(Numeric(5, 2))
    current_mutual_fund_pct = Column(Numeric(5, 2))
    current_gold_pct = Column(Numeric(5, 2))
    current_fd_debt_pct = Column(Numeric(5, 2))
    last_review_date = Column(Date)


class Holding(Base):
    """Individual holdings - maps to existing holdings table"""
    __tablename__ = "holdings"
    
    holding_id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    asset_type = Column(String(30))  # equity, mutual_fund, gold, fd
    asset_name = Column(String(200))
    quantity = Column(Numeric(15, 4))
    buy_price = Column(Numeric(15, 2))
    current_price = Column(Numeric(15, 2))
    current_value = Column(Numeric(15, 2))
    invested_amount = Column(Numeric(15, 2))
    data_source = Column(String(50))
    profit_loss = Column(Numeric(15, 2))


class Conversation(Base):
    """Conversation history - NEW table for audit trail"""
    __tablename__ = "conversations"
    
    conversation_id = Column(BigInteger, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    rm_user_id = Column(String(80))
    role = Column(String(20), nullable=False)  # 'user' | 'assistant'
    intent = Column(String(30))  # db_query | market_query | investment_advice | general_chat
    content = Column(Text, nullable=False)
    structured_output = Column(JSONB)
    compliance_status = Column(String(10))  # PASS | FAIL | N/A
    risk_score = Column(Numeric(3, 1))
    risk_level = Column(String(20))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class FDRate(Base):
    """Fixed Deposit rates - NEW table, manually maintained"""
    __tablename__ = "fd_rates"
    
    bank_name = Column(String(80), primary_key=True)
    tenure_months = Column(Integer, primary_key=True)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    senior_citizen_rate = Column(Numeric(5, 2))
    updated_at = Column(Date, nullable=False, server_default=func.current_date())
