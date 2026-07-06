# RM AI Advisory Platform

An intelligent AI-powered investment advisory system for Relationship Managers (RMs) in banking institutions. Built with a multi-agent LLM architecture using LangGraph for orchestration and powered by Groq's fast inference.

## 🌟 Overview

The RM AI Advisory Platform is a sophisticated investment advisory system that helps relationship managers provide personalized investment recommendations to their clients. It uses multiple specialized AI agents working together to analyze client profiles, market data, and portfolio holdings to generate comprehensive, compliant investment advice.

### Key Features

- **Multi-Agent Architecture**: 11 specialized AI agents working in orchestrated workflows
- **Real-Time Market Data**: Integration with Yahoo Finance for live stock, index, commodity, and mutual fund data
- **Dynamic Query Understanding**: Natural language processing to understand complex advisory queries
- **Regulatory Compliance**: Built-in compliance checks and risk assessment
- **Portfolio Analysis**: Comprehensive portfolio review, rebalancing, and diversification analysis
- **Intelligent Recommendations**: Context-aware investment suggestions based on client profiles
- **Interactive Dashboard**: Modern React-based UI with real-time chat interface

---

## 📋 Table of Contents

- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [AI Agents](#-ai-agents)
- [Tools & Data Sources](#-tools--data-sources)
- [Supported Queries](#-supported-queries)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI 0.109.0
- **Server**: Uvicorn with async support
- **Database**: PostgreSQL with AsyncPG
- **ORM**: SQLAlchemy 2.0
- **AI/LLM**: 
  - LangChain & LangGraph (Multi-agent orchestration)
  - Groq API (llama-3.3-70b-versatile)
- **Market Data**: yfinance (Yahoo Finance API)
- **Caching**: cachetools for API response caching
- **HTTP Client**: httpx for async API calls

### Frontend
- **Framework**: React 18.2
- **Build Tool**: Vite 5.0
- **Routing**: React Router DOM 6.21
- **UI/UX**: 
  - Framer Motion (animations)
  - Recharts (data visualization)
- **Markdown**: react-markdown with GitHub Flavored Markdown support

### Database Schema
- **Tables**: clients, portfolios, holdings
- **Features**: Multi-asset support, real-time portfolio tracking, historical returns

---

## 🏗 System Architecture

### LangGraph Multi-Agent Pipeline

```
User Query
    ↓
[Query Understanding Agent] → Classifies intent and extracts entities
    ↓
┌──────────────┬──────────────┬──────────────┬────────────────┐
│              │              │              │                │
│ Investment   │ Portfolio    │ Market       │ DB Query       │
│ Advice       │ Review       │ Query        │                │
│              │              │              │                │
├──────────────┤              │              │                │
│              │              │              │                │
│ [Client      │ [Portfolio   │ [Market      │ [SQL Builder]  │
│  Resolver]   │  Reviewer]   │  Tools]      │                │
│      ↓       │      ↓       │      ↓       │      ↓         │
│ [Stock       │ • Balance    │ • Stocks     │ [Formatter]    │
│  Selector]   │ • Diversif.  │ • Indices    │                │
│      ↓       │ • Rebalance  │ • Commodity  │                │
│ [Market      │              │ • MF NAV     │                │
│  Intelligence│              │ • Top Movers │                │
│      ↓       │              │              │                │
│ [Investment  │              │              │                │
│  Advisor]    │              │              │                │
│      ↓       │              │              │                │
│ [Capital     │              │              │                │
│  Allocator]  │              │              │                │
│      ↓       │              │              │                │
│ [Allocation  │              │              │                │
│  Validator]  │              │              │                │
│      ↓       │              │              │                │
│ [Compliance  │              │              │                │
│  Agent]      │              │              │                │
│      ↓       │              │              │                │
│ [Risk        │              │              │                │
│  Assessment] │              │              │                │
│      ↓       │              │              │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
    ↓
[Response Formatter]
    ↓
Formatted Response to User
```

### Request Flow

1. **Query Understanding**: NLP analysis to determine intent (investment advice, portfolio review, market query, or DB query)
2. **Context Resolution**: Fetch relevant client data, portfolio holdings, and market information
3. **Agent Execution**: Route to appropriate agent pipeline based on intent
4. **Validation**: Apply business rules, compliance checks, and risk assessment
5. **Response Generation**: Format results into user-friendly markdown output

---

## 🤖 AI Agents

### 1. Query Understanding Agent
- **Purpose**: Classifies user queries and extracts entities
- **Capabilities**:
  - Intent classification (5 types)
  - Entity extraction (client names, tickers, goals, time periods)
  - Context-aware parsing
- **Output**: Structured query understanding with intent, entities, and rationale

### 2. Client Resolver Agent
- **Purpose**: Resolves client identity from various inputs
- **Capabilities**:
  - Fuzzy name matching
  - Client ID resolution
  - Profile and portfolio data retrieval
- **Output**: Complete client profile with holdings and portfolio state

### 3. Stock Selector Agent
- **Purpose**: Determines which stocks/assets to fetch for analysis
- **Capabilities**:
  - Context-based stock selection
  - Sector-based recommendations
  - Diversification-aware picking
- **Output**: List of tickers to fetch, sector focus, rationale

### 4. Market Intelligence Agent
- **Purpose**: Synthesizes market data into actionable insights
- **Capabilities**:
  - Multi-source data aggregation
  - Trend analysis
  - Market context generation
- **Output**: Natural language market summary with key insights

### 5. Investment Advisor Agent
- **Purpose**: Generates personalized investment recommendations
- **Modes**:
  - **Full Plan**: Complete portfolio allocation with specific picks
  - **Stock Analysis**: YES/NO recommendation for specific stocks
  - **Sector Analysis**: Sector-level investment opportunities
- **Capabilities**:
  - Client profile analysis
  - Risk-return optimization
  - Goal-based asset allocation
  - Specific stock/MF recommendations with rationales
- **Output**: Structured recommendation with allocation, picks, and detailed rationale

### 6. Capital Allocator Agent
- **Purpose**: Breaks down investment amount into specific allocations
- **Capabilities**:
  - Rupee-level allocation across asset classes
  - Stock-by-stock investment amounts
  - SIP vs lumpsum recommendations
- **Output**: Detailed capital allocation table

### 7. Compliance Agent
- **Purpose**: Ensures recommendations meet regulatory requirements
- **Capabilities**:
  - Soft rule validation (disclosure requirements)
  - Risk disclosure checks
  - Goal alignment verification
  - Review requirement flagging
- **Output**: Pass/fail status with specific issues and suggestions

### 8. Portfolio Reviewer Agent
- **Purpose**: Analyzes existing client portfolios
- **Capabilities**:
  - Balance check (actual vs ideal allocation)
  - Diversification analysis (asset types, sectors, concentration)
  - Rebalancing recommendations
- **Output**: Portfolio assessment with actionable recommendations

### 9. Risk Assessment Agent
- **Purpose**: Evaluates investment risk across 5 dimensions
- **Dimensions**:
  - Market risk (volatility, correlation)
  - Liquidity risk (exit flexibility)
  - Concentration risk (single-asset exposure)
  - Credit risk (counterparty risk)
  - Compliance risk (regulatory issues)
- **Output**: Risk level (VERY_LOW to VERY_HIGH) with scores and breakdown

### 10. Allocation Validator
- **Purpose**: Validates allocation against hard business rules
- **Rules**:
  - Allocation sums to 100%
  - Equity within ceiling by risk tier
  - Age-based equity limits
  - Goal-specific structural requirements
  - SIP within income capacity
- **Output**: Valid/invalid with specific violations

### 11. SQL Builder Agent
- **Purpose**: Translates natural language to SQL queries
- **Capabilities**:
  - Intent classification (client list, holdings, portfolio detail)
  - Dynamic filter extraction
  - Fuzzy name matching
  - Query result formatting
- **Output**: Formatted query results

---

## 🔧 Tools & Data Sources

### Market Data Tools

#### 1. Stock Quote Tool
- **Function**: `get_stock_quote(ticker)`
- **Source**: Yahoo Finance API
- **Data**: Current price, P/E ratio, market cap, 52-week range
- **Caching**: 5 minutes TTL

#### 2. Index Quote Tool
- **Function**: `get_index_quote(index_name)`
- **Supported Indices**: NIFTY, SENSEX, BANKNIFTY
- **Data**: Current level, change, percentage change
- **Caching**: 5 minutes TTL

#### 3. Commodity Price Tool
- **Function**: `get_commodity_price(commodity)`
- **Supported**: Gold, Silver, Crude Oil
- **Data**: Current price in INR
- **Caching**: 15 minutes TTL

#### 4. Mutual Fund Tool
- **Function**: `get_mutual_fund_by_name(scheme_name)`
- **Data**: Latest NAV, fund category, returns
- **Caching**: 1 day TTL

#### 5. Historical Prices Tool
- **Function**: `get_stock_historical(ticker, period)` / `get_commodity_historical(commodity, period)`
- **Periods**: 1 month, 3 months, 6 months, 1 year
- **Data**: Date, price, returns, trends
- **Caching**: 1 hour TTL

#### 6. Top Movers Screener
- **Function**: `get_top_movers(period, direction, universe, limit)`
- **Universe**: Nifty 50, Bank Nifty, Nifty IT
- **Direction**: Gainers or Losers
- **Periods**: 1 day, 1 week, 1 month
- **Data**: Ranked list with % change, volume
- **Caching**: 5 minutes TTL

### Configuration & Rules

#### 1. Allocation Rules (`allocation_rules.py`)
- Base equity by risk tier (HIGH: 65%, MEDIUM: 45%, LOW: 15%)
- Age-based adjustments (+5% under 30, -20% over 60)
- Hard equity ceilings (HIGH: 83%, MEDIUM: 58%, LOW: 23%)
- Goal-based structural overrides
- SIP calculation (20% of income, max 30%)

#### 2. Sector Mapping (`sector_mapping.py`)
- 100+ NSE stocks mapped to 12 sectors
- Sector concentration limits by risk tier
- Portfolio sector breakdown calculation
- Diversification analysis

#### 3. Universe Lists (`universes.py`)
- Nifty 50 constituents
- Bank Nifty constituents
- Nifty IT constituents

---

## 💬 Supported Queries

### 1. Investment Advice Queries

**Full Investment Plan**:
```
"where should Rahul Sharma invest"
"create investment plan for Vikas Gupta"
"Priya Patel wants to invest 5 lakhs"
"suggest investment strategy for Sneha Iyer"
```

**Stock-Specific Analysis** (YES/NO recommendations):
```
"should Rahul Sharma invest in Wipro"
"is TCS a good investment for Vikas Gupta"
"analyze Reliance stock for Priya Patel"
"recommend HDFC Bank for Arjun Malhotra"
```

**Goal-Specific Plans**:
```
"Rahul wants 10 lakhs for child education in 5 years"
"retirement plan for Vikas aged 55"
"tax saving investments for Priya"
"emergency fund strategy for Sneha"
```

### 2. Portfolio Review Queries

**Balance Check**:
```
"is Vikas Gupta's portfolio balanced"
"check Rahul Sharma's asset allocation"
"analyze balance of Priya's portfolio"
```

**Diversification Analysis**:
```
"is my portfolio diversified"
"check diversification for Vikas Gupta"
"analyze sector concentration in Rahul's portfolio"
```

**Rebalancing Recommendations**:
```
"does Vikas need portfolio rebalancing"
"should Rahul rebalance his investments"
"rebalancing check for Priya Patel"
```

### 3. Market Data Queries

**Stock Prices**:
```
"what is Wipro stock price"
"TCS current price"
"Reliance stock quote"
```

**Index Levels**:
```
"what is Nifty today"
"current Sensex level"
"Bank Nifty index"
```

**Commodity Prices**:
```
"gold price today"
"how much has gold increased in last 1 year"
"silver rate"
"crude oil price"
```

**Top Movers**:
```
"what are this week's top performing shares"
"show me today's biggest gainers"
"worst performing stocks this month"
```

**Mutual Funds**:
```
"HDFC Flexi Cap NAV"
"latest NAV of Axis Bluechip Fund"
"SBI Small Cap fund details"
```

### 4. Database Queries

**Client Lists**:
```
"show all high risk clients"
"list clients from Mumbai"
"clients with medium risk profile"
```

**Holdings Queries**:
```
"show me all stocks where Arjun Malhotra has invested"
"list Vikas Gupta's mutual fund holdings"
"what equity does Rahul Sharma hold"
```

**Portfolio Details**:
```
"show Priya Patel's portfolio"
"Sneha Iyer's total investment value"
"portfolio summary for Vikas Gupta"
```

### 5. General Chat

```
"hello"
"thank you"
"what can you help me with"
```

---

## 📦 Installation

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 16 or higher
- **PostgreSQL**: 14 or higher
- **Groq API Key**: Sign up at [Groq Console](https://console.groq.com)

### Backend Setup

1. **Clone the repository**:
```bash
git clone <repository-url>
cd rm-ai-advisory
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

4. **Setup database**:
```bash
# Create PostgreSQL database
createdb rm_advisory

# Run migration scripts
python scripts/setup_tables.py
```

5. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

6. **Start backend server**:
```bash
python app/main.py
# Server runs on http://localhost:8000
```

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with API URL
```

3. **Start development server**:
```bash
npm run dev
# Frontend runs on http://localhost:5173
```

---

## ⚙️ Configuration

### Backend Configuration (`.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rm_advisory

# Groq LLM
GROQ_API_KEY=your_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile

# API Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend Configuration (`.env`)

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Business Rules Configuration

Edit `backend/app/rules/allocation_rules.py` to customize:
- Base equity percentages by risk tier
- Age-based equity adjustments
- Equity ceiling limits
- Goal-specific allocation overrides
- SIP calculation parameters

Edit `backend/app/rules/sector_mapping.py` to add:
- New stock-to-sector mappings
- Sector concentration limits
- Universe constituent lists

---

## 🚀 Usage

### Starting the Application

**Option 1: Manual Start**
```bash
# Terminal 1 - Backend
cd backend
python app/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**Option 2: Using Start Script** (Windows)
```bash
START_SERVERS.bat
```

### Using the Web Interface

1. Open browser to `http://localhost:5173`
2. Select a client from the roster
3. Type your query in the chat input
4. View AI-generated recommendations

### Using the API Directly

**Example: Investment Advice**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "should Rahul Sharma invest in Wipro",
    "client_id": 1,
    "goal": "wealth_creation",
    "time_period": "5-7 years"
  }'
```

**Example: Portfolio Review**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "is portfolio balanced",
    "client_id": 1
  }'
```

---

## 📚 API Documentation

### Endpoints

#### POST `/api/chat`
Main chat endpoint for all queries.

**Request Body**:
```json
{
  "message": "user query",
  "client_id": 1,
  "goal": "wealth_creation",  // optional
  "time_period": "5-7 years",  // optional
  "investment_amount": 500000  // optional
}
```

**Response**:
```json
{
  "response": "markdown formatted response",
  "intent": "investment_advice",
  "query_type": "stock",
  "client_id": 1,
  "compliance_status": "PASS",
  "risk_level": "moderate"
}
```

#### GET `/api/clients`
List all clients.

**Response**:
```json
{
  "clients": [
    {
      "client_id": 1,
      "client_name": "Rahul Sharma",
      "age": 32,
      "city": "Mumbai",
      "risk_factor": "high",
      "monthly_income": 250000
    }
  ]
}
```

#### GET `/api/clients/{client_id}`
Get specific client details with portfolio.

**Response**:
```json
{
  "client": {...},
  "portfolio": {...},
  "holdings": [...]
}
```

### Interactive API Docs

Visit `http://localhost:8000/docs` for Swagger UI documentation.

---

## 📁 Project Structure

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed file-by-file documentation.

---

## 🧪 Testing

Run test suite:
```bash
cd backend
python -m pytest tests/
```

Test specific agents:
```bash
python scripts/test_groq.py
python scripts/validate_schema.py
```

---

## 🔒 Security Considerations

- API keys stored in `.env` files (not committed to git)
- Database credentials secured
- Input validation on all endpoints
- SQL injection prevention via ORM
- CORS configured for specific origins
- Rate limiting on external API calls

---

## 🚧 Known Limitations

1. **Stock API**: Yahoo Finance API occasionally returns 404s - [See Market Data Notes](MARKET_DATA_NOTES.md)
2. **Market Hours**: Outside trading hours (9:15 AM - 3:30 PM IST), system shows previous day's closing prices
3. **Real-time Data**: 5-minute cache on market data during market hours (near real-time, not tick-by-tick)
4. **Commodity Prices**: Using international futures (not exact MCX prices) - converted to INR
5. **Limited MF Coverage**: Mutual fund data availability varies by fund
6. **Single Currency**: Only supports INR currently
7. **No Authentication**: Auth layer not yet implemented (recommended for production)

**📊 Important**: For detailed information about market data accuracy and timeliness, please read [MARKET_DATA_NOTES.md](MARKET_DATA_NOTES.md)

---

## 🛣 Roadmap

- [ ] Add user authentication and authorization
- [ ] Implement real-time notifications
- [ ] Add portfolio performance tracking
- [ ] Integrate with actual trading APIs
- [ ] Multi-language support
- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Backtesting capabilities

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Initial Development**: RM AI Advisory Team
- **Architecture**: Multi-agent LLM system with LangGraph
- **Powered by**: Groq (fast LLM inference)

---

## 🙏 Acknowledgments

- **Groq**: Fast LLM inference engine
- **LangChain/LangGraph**: Multi-agent orchestration framework
- **Yahoo Finance**: Market data provider
- **FastAPI**: High-performance Python web framework
- **React**: Frontend library

---

## 📞 Support

For issues, questions, or suggestions:
- Create an issue in the GitHub repository
- Contact the development team

---

**Built with ❤️ for Relationship Managers**
