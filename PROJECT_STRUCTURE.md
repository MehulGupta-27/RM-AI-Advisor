# Project Structure Documentation

This document provides a comprehensive overview of all files and directories in the RM AI Advisory Platform.

## 📂 Root Directory

```
rm-ai-advisory/
├── backend/           # Python FastAPI backend
├── frontend/          # React frontend
├── README.md          # Main project documentation
├── PROJECT_STRUCTURE.md  # This file
└── .gitignore         # Git ignore rules
```

---

## 🔙 Backend Structure

### `/backend`

Main backend directory containing the FastAPI application.

```
backend/
├── app/               # Application code
├── db/                # Database scripts
├── scripts/           # Utility scripts
├── requirements.txt   # Python dependencies
├── .env              # Environment variables (not in git)
└── .env.example      # Example environment configuration
```

### `/backend/app`

Core application code organized by functionality.

**Main Application Files**:

- **`main.py`**: FastAPI application entry point
  - Initializes FastAPI app
  - Configures CORS middleware
  - Registers API routers
  - Sets up database connection
  - Starts Uvicorn server on port 8000

- **`__init__.py`**: Package initialization


### `/backend/app/agents`

AI agents that form the multi-agent system.

- **`advisory_graph.py`**: LangGraph state machine orchestration
  - Creates the advisory pipeline workflow
  - Defines node functions for each agent
  - Implements conditional routing logic
  - Manages state transitions between agents
  - Handles retry logic and error handling

- **`query_understanding.py`**: Query classification and entity extraction
  - Classifies user intent (5 types)
  - Extracts entities (client names, tickers, goals)
  - Returns structured QueryUnderstanding object
  - Uses Groq LLM for NLP analysis

- **`client_resolver.py`**: Client identity resolution
  - Resolves client from ID or name
  - Fetches profile, portfolio, and holdings from database
  - Handles fuzzy name matching
  - Returns complete client context

- **`stock_selector.py`**: Determines stocks to fetch
  - Analyzes query and client profile
  - Suggests relevant stocks for analysis
  - Returns list of tickers and rationale

- **`market_intelligence.py`**: Market data synthesis
  - Aggregates data from multiple market tools
  - Generates natural language market summary
  - Provides context for investment decisions

- **`investment_advisor.py`**: Core recommendation engine
  - Three modes: full_plan, stock_analysis, sector_analysis
  - Generates detailed investment recommendations
  - Creates specific stock/MF picks with rationales
  - Applies goal-based and risk-based allocation logic

- **`capital_allocator.py`**: Investment amount breakdown
  - Distributes rupee amounts across asset classes
  - Calculates stock-by-stock investment amounts
  - Determines SIP vs lumpsum recommendations
  - Formats detailed allocation table


- **`portfolio_reviewer.py`**: Portfolio analysis agent
  - Reviews portfolio balance (actual vs ideal allocation)
  - Analyzes diversification (asset types, sectors, concentration)
  - Determines rebalancing needs (10% threshold)
  - Uses sector mapping for diversification analysis
  - Returns formatted portfolio assessment

- **`compliance.py`**: Regulatory compliance checker
  - Validates soft compliance rules
  - Checks disclosure requirements
  - Verifies risk disclaimers present
  - Ensures goal alignment mentioned
  - Returns pass/fail with specific issues

- **`risk.py`**: Multi-dimensional risk assessment
  - Evaluates 5 risk dimensions (market, liquidity, concentration, credit, compliance)
  - Calculates overall risk score (0-10)
  - Determines risk level (VERY_LOW to VERY_HIGH)
  - Flags senior review requirements

- **`graph_state.py`**: TypedDict definitions for LangGraph state

- **`__init__.py`**: Package initialization

### `/backend/app/api`

API endpoints and route handlers.

- **`chat.py`**: Main chat API endpoint
  - POST `/api/chat`: Handles all query types
  - Routes to appropriate handlers based on intent
  - Investment advice handler (LangGraph pipeline)
  - Portfolio review handler
  - Market query handler (tools execution)
  - DB query handler (SQL builder with LLM)
  - Response formatting functions

- **`clients.py`**: Client management endpoints
  - GET `/api/clients`: List all clients
  - GET `/api/clients/{id}`: Get specific client details
  - Returns client profile, portfolio, and holdings

- **`__init__.py`**: Package initialization


### `/backend/app/db`

Database models and session management.

- **`models.py`**: SQLAlchemy ORM models
  - Client table definition (profile data)
  - Portfolio table definition (allocation and returns)
  - Holding table definition (individual assets)
  - Relationships between tables

- **`session.py`**: Database connection management
  - AsyncEngine creation
  - Session factory setup
  - Dependency injection for FastAPI
  - Connection pooling configuration

- **`__init__.py`**: Package initialization

### `/backend/app/llm`

LLM client and utilities.

- **`groq_client.py`**: Groq API client wrapper
  - Async chat completion method
  - Structured output with JSON parsing
  - Retry logic with exponential backoff
  - Error handling and logging
  - Temperature and token limit configuration

- **`__init__.py`**: Package initialization

### `/backend/app/rules`

Business rules and configuration.

- **`allocation_rules.py`**: Deterministic allocation rules
  - Base equity percentages by risk tier (HIGH: 65%, MEDIUM: 45%, LOW: 15%)
  - Age-based adjustments (+5% under 30, -20% over 60)
  - Hard equity ceilings (HIGH: 83%, MEDIUM: 58%, LOW: 23%)
  - Goal-based structural overrides (emergency_fund, retirement, home_purchase)
  - SIP calculation (20% of income, max 30%)
  - Allocation validator (checks hard rules)
  - Concentration risk calculator
  - Fallback allocation generator


- **`sector_mapping.py`**: Stock-to-sector mapping
  - 100+ NSE stocks mapped to 12 sectors
  - Sector functions:
    - `get_sector(ticker)`: Returns sector for a stock
    - `get_sector_breakdown(holdings)`: Calculates sector-wise portfolio breakdown
    - `check_sector_concentration(holdings, risk_factor)`: Validates sector limits
    - `get_stocks_by_sector(sector)`: Reverse lookup
  - Sector concentration limits by risk tier (HIGH: 40%, MEDIUM: 30%, LOW: 20%)

- **`__init__.py`**: Package initialization

### `/backend/app/tools`

Market data fetching tools.

- **`stock_quote.py`**: Stock price fetcher
  - `get_stock_quote(ticker)`: Fetches current price, P/E, market cap
  - Uses Yahoo Finance API
  - 5-minute cache TTL
  - Error handling for API failures

- **`index_quote.py`**: Index level fetcher
  - `get_index_quote(index_name)`: Fetches Nifty, Sensex, Bank Nifty
  - Returns current level, change, percentage
  - 5-minute cache TTL

- **`commodity.py`**: Commodity price fetcher
  - `get_commodity_price(commodity)`: Gold, Silver, Crude Oil prices
  - Converts to INR
  - 15-minute cache TTL

- **`mutual_fund.py`**: Mutual fund NAV fetcher
  - `get_mutual_fund_by_name(scheme_name)`: Latest NAV and details
  - 1-day cache TTL

- **`historical_prices.py`**: Historical data fetcher
  - `get_stock_historical(ticker, period)`: Stock price history
  - `get_commodity_historical(commodity, period)`: Commodity price history
  - Periods: 1m, 3m, 6m, 1y
  - Returns date, price, returns, trends
  - 1-hour cache TTL


- **`top_movers.py`**: Top performers/losers screener
  - `get_top_movers(period, direction, universe, limit)`: Ranked stock list
  - Universes: Nifty 50, Bank Nifty, Nifty IT
  - Direction: gainers or losers
  - Periods: 1d, 1wk, 1mo
  - `format_top_movers()`: Markdown table formatter
  - 5-minute cache TTL

- **`cache.py`**: Caching utilities
  - TTLCache implementation
  - Cache key generators
  - Expiry management

- **`__init__.py`**: Package initialization

### `/backend/app/config`

Configuration files.

- **`universes.py`**: Stock universe definitions
  - NIFTY_50: List of Nifty 50 constituent tickers
  - BANK_NIFTY: List of Bank Nifty constituent tickers
  - NIFTY_IT: List of Nifty IT constituent tickers

- **`__init__.py`**: Package initialization

### `/backend/db`

Database setup scripts.

- **`additional_tables.sql`**: SQL schema for tables
  - clients table definition
  - portfolios table definition
  - holdings table definition
  - Sample data inserts (30 clients)

### `/backend/scripts`

Utility and test scripts.

- **`setup_tables.py`**: Database initialization
  - Creates tables
  - Loads sample data
  - Sets up relationships

- **`validate_schema.py`**: Schema validation
  - Checks table structure
  - Validates relationships
  - Verifies data integrity

- **`test_groq.py`**: Groq API connectivity test
  - Tests LLM connection
  - Validates API key
  - Checks response format


### Configuration Files

- **`requirements.txt`**: Python package dependencies
  - FastAPI, Uvicorn (web framework)
  - SQLAlchemy, AsyncPG (database)
  - LangChain, LangGraph (AI orchestration)
  - httpx (async HTTP client)
  - yfinance (market data)
  - cachetools (caching)

- **`.env.example`**: Example environment configuration
  - DATABASE_URL template
  - GROQ_API_KEY placeholder
  - Server configuration examples
  - CORS settings

- **`.env`**: Actual environment variables (not in git)
  - Sensitive credentials
  - API keys
  - Database connection strings

---

## 🎨 Frontend Structure

### `/frontend`

React-based frontend application.

```
frontend/
├── src/               # Source code
├── node_modules/      # NPM dependencies
├── index.html         # HTML entry point
├── package.json       # NPM configuration
├── vite.config.js     # Vite build configuration
├── .env              # Environment variables (not in git)
└── .env.example      # Example environment configuration
```

### `/frontend/src`

Frontend source code.

**Main Files**:

- **`main.jsx`**: Application entry point
  - React app initialization
  - Router setup
  - Global styles import

- **`index.css`**: Global CSS styles
  - Base styles
  - CSS variables
  - Utility classes


### `/frontend/src/pages`

Page components.

- **`App.jsx`**: Main application component
  - Router configuration
  - Route definitions
  - Layout wrapper

- **`App.css`**: Application-level styles

- **`Home.jsx`**: Home/chat page component
  - Client roster display
  - Chat interface
  - Message history
  - Input handling
  - API integration
  - Real-time updates

- **`Home.css`**: Home page styles
  - Chat layout
  - Message bubbles
  - Client roster styles
  - Responsive design

- **`HomeNew.jsx`**: Alternative home page (experimental)

- **`HomeNew.css`**: Alternative styles

### `/frontend/src/api`

API client utilities.

- **`client.js`**: HTTP client wrapper
  - Axios/fetch configuration
  - Base URL setup
  - Request/response interceptors
  - Error handling

### `/frontend/src/theme`

Theme and styling utilities.

- Theme configuration
- Color schemes
- Typography settings

### Configuration Files

- **`package.json`**: NPM package configuration
  - Dependencies: React, React Router, Framer Motion, Recharts
  - Dev dependencies: Vite, Vite React plugin
  - Scripts: dev, build, preview

- **`vite.config.js`**: Vite bundler configuration
  - React plugin setup
  - Build optimization
  - Dev server configuration

- **`index.html`**: HTML template
  - Root div for React mount
  - Meta tags
  - Title


- **`.env.example`**: Example environment configuration
  - VITE_API_BASE_URL template

- **`.env`**: Actual environment variables (not in git)
  - API endpoint URL

---

## 📊 Data Flow

### Investment Advice Query Flow

```
User: "should Rahul invest in Wipro"
  ↓
Frontend (Home.jsx)
  ↓
POST /api/chat
  ↓
chat.py → handle_chat()
  ↓
LangGraph Pipeline (advisory_graph.py)
  ↓
1. Query Understanding Agent
   - Classifies as "investment_advice / stock"
   - Extracts: client_name="Rahul", ticker="WIPRO"
  ↓
2. Client Resolver Agent
   - Finds client_id=1 (Rahul Sharma)
   - Fetches profile, portfolio, holdings from DB
  ↓
3. Stock Selector Agent
   - Decides to fetch [WIPRO, TCS, INFY] for comparison
  ↓
4. Market Data Fetcher
   - Calls get_stock_quote() for each ticker
   - Calls get_index_quote("NIFTY")
   - Aggregates results
  ↓
5. Market Intelligence Agent
   - Synthesizes market data into summary
   - "WIPRO at ₹632, +21.5% YoY, NIFTY bullish"
  ↓
6. Investment Advisor Agent (stock_analysis mode)
   - Analyzes fundamentals vs client profile
   - Checks portfolio impact
   - Generates YES/NO recommendation with reasoning
  ↓
7. Allocation Validator
   - Skipped for stock_analysis (not needed)
  ↓
8. Compliance Agent
   - Skipped for stock_analysis (has own validation)
  ↓
9. Risk Assessment Agent
   - Evaluates 5 dimensions
   - Returns "MODERATE 4.4/10"
  ↓
10. Response Formatter
    - Formats as markdown with YES/NO verdict
    - Includes key reasons, analysis, risks
  ↓
Response JSON
  ↓
Frontend displays formatted markdown
```


### Portfolio Review Query Flow

```
User: "is portfolio balanced"
  ↓
Frontend → POST /api/chat
  ↓
chat.py → handle_chat()
  ↓
Query Understanding: "portfolio_review / balance_check"
  ↓
handle_portfolio_review()
  ↓
1. Client Resolver
   - Fetches client profile, portfolio, holdings
  ↓
2. Portfolio Reviewer Agent
   - Calls review_portfolio_balance()
   - Compares actual vs ideal allocation
   - Calculates gaps
   - Determines verdict (BALANCED/IMBALANCED)
  ↓
3. Response Formatter
   - format_portfolio_review()
   - Shows actual allocation, ideal allocation, gaps
  ↓
Response with detailed balance analysis
```

### DB Query Flow

```
User: "show stocks where Arjun invested"
  ↓
Frontend → POST /api/chat
  ↓
chat.py → handle_chat()
  ↓
Query Understanding: "db_query / general"
  ↓
handle_db_query()
  ↓
1. LLM Analysis
   - Extracts: query_type="client_holdings"
   - Extracts: specific_client_name="Arjun Malhotra"
   - Extracts: filters={"asset_type": "stock"}
  ↓
2. SQL Builder
   - Finds client by fuzzy name match
   - Builds holdings query with filters
   - Executes SQL
  ↓
3. Formatter
   - Formats as markdown list
   - Includes totals
  ↓
Response with Arjun's stock holdings only
```

---

## 🔑 Key Design Patterns

### 1. Multi-Agent Orchestration (LangGraph)
- State machine with typed state
- Conditional routing between agents
- Retry mechanisms with state preservation
- Parallel tool execution where possible

### 2. Separation of Concerns
- Agents: Business logic and AI reasoning
- Tools: External data fetching
- Rules: Deterministic validation
- API: Request/response handling
- DB: Data persistence


### 3. Caching Strategy
- Market data: 5-minute TTL (balance freshness vs API limits)
- Historical data: 1-hour TTL (less volatile)
- Mutual funds: 1-day TTL (NAV updates once daily)
- LRU cache with size limits

### 4. Error Handling
- Graceful degradation (continue with partial data)
- Retry with exponential backoff (LLM API)
- Fallback mechanisms (generic allocation if all else fails)
- Detailed error logging

### 5. Dynamic Query Handling
- LLM-based intent classification
- Entity extraction with context
- No hardcoded query patterns
- Fuzzy matching for robustness

---

## 🔄 State Management

### LangGraph State (AgentState TypedDict)
```python
{
    "user_message": str,              # Original query
    "client_id": int,                 # Client identifier
    "goal": str,                      # Investment goal
    "time_period": str,               # Time horizon
    "investment_amount": float,       # Optional amount
    
    # Query understanding
    "intent": str,                    # db_query, market_query, etc.
    "query_type": str,                # stock, general, etc.
    "ticker": str,                    # Extracted ticker
    
    # Client context
    "client_profile": dict,           # From database
    "client_portfolio": dict,         # Current allocation
    "client_holdings": list,          # Individual positions
    
    # Market data
    "stocks_to_fetch": list,          # Tickers to fetch
    "market_data": dict,              # Fetched market data
    "market_summary": str,            # Synthesized summary
    
    # Recommendations
    "advisor_output": dict,           # LLM recommendations
    "capital_allocation": dict,       # Rupee-level breakdown
    
    # Validation
    "allocation_valid": bool,         # Hard rules check
    "allocation_violations": list,    # Specific issues
    "concentration_warnings": list,   # Non-blocking warnings
    "compliance_result": dict,        # Soft rules check
    "risk_result": dict,              # Risk assessment
    
    # Control flow
    "compliance_retry_count": int,    # Retry tracker
    "used_fallback": bool,            # Fallback flag
    "error": str,                     # Error message if any
    "response": str                   # Final formatted response
}
```

---

## 📈 Performance Considerations

### Backend Optimizations
- Async database queries (AsyncPG)
- Parallel tool execution (asyncio.gather)
- Response caching (cachetools)
- Connection pooling (SQLAlchemy)
- Efficient JSON parsing

### Frontend Optimizations
- Code splitting (React.lazy)
- Memoization (useMemo, useCallback)
- Virtual scrolling for long lists
- Debounced input handling
- Optimized re-renders

### API Optimizations
- Streaming responses (future enhancement)
- Batch requests support
- Compression (gzip)
- CDN for static assets

---

## 🧪 Testing Strategy

### Unit Tests
- Individual agent functions
- Tool functions with mocked APIs
- Rule validation logic
- Database models

### Integration Tests
- End-to-end query flows
- LangGraph pipeline execution
- API endpoint responses
- Database operations

### Test Files Location
- Backend: `backend/tests/` (to be created)
- Scripts: `backend/scripts/test_*.py`

---

## 📝 Configuration Management

### Environment Variables
- **Development**: `.env` files (not in git)
- **Production**: Environment variables or secrets manager
- **Defaults**: Fallback values in code

### Business Rules
- **Code-based**: `rules/*.py` files
- **Database-based**: Future enhancement for dynamic rules
- **Configuration files**: `config/*.py` files

---

## 🔐 Security Architecture

### Authentication (Future)
- JWT tokens
- Role-based access control (RBAC)
- Session management

### Data Protection
- Environment variables for secrets
- SQL injection prevention (ORM)
- Input validation (Pydantic)
- CORS configuration

### API Security
- Rate limiting (future enhancement)
- Request size limits
- Timeout configurations
- Error message sanitization

---

## 🚀 Deployment Considerations

### Backend Deployment
- Docker containerization (Dockerfile to be created)
- Gunicorn/Uvicorn workers
- Nginx reverse proxy
- PostgreSQL managed service

### Frontend Deployment
- Static build (`npm run build`)
- CDN distribution
- Environment-specific builds

### Environment Separation
- Development (localhost)
- Staging (pre-production testing)
- Production (live system)

---

**Document Version**: 1.0  
**Last Updated**: July 5, 2026  
**Maintained By**: RM AI Advisory Team
