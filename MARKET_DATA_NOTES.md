# Market Data - Important Notes

## 📊 Data Accuracy & Timeliness

### Current Implementation

The RM AI Advisory Platform fetches market data from **Yahoo Finance API**, which provides:

- **Stock Prices**: NSE stocks (with .NS suffix)
- **Index Levels**: Nifty, Sensex, Bank Nifty
- **Commodity Prices**: Gold, Silver, Crude Oil (international futures, not MCX)
- **Mutual Fund NAVs**: Fund NAVs

### ⚠️ Known Limitations

#### 1. **Yahoo Finance API Reliability**
- **Issue**: Yahoo Finance frequently returns 404 errors
- **Impact**: Stock quotes may fail to fetch
- **Workaround**: System continues with available data, doesn't fail completely
- **Status**: Known issue, alternative APIs being evaluated

#### 2. **Market Hours**
- **NSE Trading Hours**: 9:15 AM - 3:30 PM IST (Monday-Friday)
- **When Market is CLOSED**:
  - You will see **previous day's closing prices**
  - Prices are NOT updated in real-time outside market hours
  - This is EXPECTED behavior, not a bug

- **When Market is OPEN**:
  - Prices update with 5-minute cache
  - You get near real-time data (5-min delay)

#### 3. **Caching Strategy**
- **Stock Quotes**: 5-minute TTL
  - If you query same stock within 5 minutes, you get cached data
  - After 5 minutes, fresh data is fetched
  
- **Index Quotes**: 5-minute TTL
  
- **Commodity Prices**: 15-minute TTL
  - Gold, Silver, Crude Oil
  
- **Mutual Fund NAVs**: 1-day TTL
  - NAVs update once daily (after market close)

#### 4. **Commodity Prices - CRITICAL LIMITATION** ⚠️
- **Source**: 
  - **Gold & Silver**: GLD and SLV ETFs (international prices)
  - **Crude Oil & Natural Gas**: Yahoo Finance futures (CL=F, NG=F)
- **NOT INDIAN PRICES**: The prices shown are **international spot/ETF prices**
- **Indian Prices Are 30-50% HIGHER** due to:
  - Import duty: 15% on gold, 10% on silver
  - GST: 3% on gold and silver
  - Local premiums and distribution costs
  - MCX trading premiums
- **Example** (July 2026):
  - Our system shows: **₹115,736/10g** (international price)
  - Actual Indian retail: **₹149,945/10g** (Google/MCX price)
  - Difference: **30% higher** in Indian markets
- **Conversion**: USD prices converted to INR using live FX rate
- **Gold**: USD/oz → ₹/10g (1 oz = 31.1035 grams)
- **Silver**: USD/oz → ₹/kg
- **Crude**: USD/barrel (no conversion)
- **Recommendation**: For Indian commodity prices, users should check:
  - MCX India (mcxindia.com)
  - GoodReturns.in (gold rates by city)
  - Local jewelers for retail prices
  - Economic Times commodity section

### 🔍 How to Check if Data is Current

#### Check Market Status
```python
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)

# Market hours: 9:15 AM - 3:30 PM IST, Monday-Friday
is_weekday = now.weekday() < 5  # 0-4 = Mon-Fri
hour = now.hour
minute = now.minute
time_in_minutes = hour * 60 + minute

market_open_time = 9 * 60 + 15  # 9:15 AM
market_close_time = 15 * 60 + 30  # 3:30 PM

is_market_open = (
    is_weekday and 
    market_open_time <= time_in_minutes <= market_close_time
)

if is_market_open:
    print("Market is OPEN - Prices are near real-time (5-min cache)")
else:
    print("Market is CLOSED - Showing previous day's closing prices")
```

#### Check Data Timestamp
The system could be enhanced to include fetch timestamp in responses:
```json
{
    "price": 632.35,
    "fetched_at": "2026-07-05T14:30:00+05:30",
    "is_realtime": true,
    "cache_age_seconds": 120
}
```

### 🔧 Improving Data Accuracy

#### Option 1: Use NSE Official API (Recommended)
```python
# NSE provides official APIs (requires registration)
# URL: https://www.nseindia.com/api/quote-equity?symbol=RELIANCE
# Benefits: 
#   - Official data source
#   - More reliable than Yahoo Finance
#   - Real NSE prices
# Drawbacks:
#   - Requires headers management (cookies, user-agent)
#   - Rate limiting
```

#### Option 2: Use Paid Data Provider
- **AlphaVantage**: $49/month for real-time data
- **IEX Cloud**: $9/month starter plan
- **Polygon.io**: $29/month for Indian markets
- **Benefits**: Reliable, official, with SLA

#### Option 3: Use yfinance with Better Error Handling
```python
# Current implementation + improvements
import yfinance as yf

ticker = yf.Ticker("RELIANCE.NS")
info = ticker.info

# Check if data is fresh
hist = ticker.history(period="1d")
last_update = hist.index[-1]

# Compare with current time
age_minutes = (datetime.now() - last_update).total_seconds() / 60
is_fresh = age_minutes < 10  # Less than 10 minutes old
```

### 📝 Testing Market Data

#### Test Current Prices
```bash
cd backend
python app/tools/stock_quote.py
# Should show current prices if market is open
```

#### Test All Data Sources
```bash
# Stock quotes
curl "http://localhost:8000/api/chat" -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "what is Reliance stock price", "client_id": 1}'

# Index quotes
curl "http://localhost:8000/api/chat" -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "what is Nifty today", "client_id": 1}'

# Commodity prices
curl "http://localhost:8000/api/chat" -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "gold price today", "client_id": 1}'
```

### 🎯 Expected Behavior

#### During Market Hours (9:15 AM - 3:30 PM IST)
✅ Stock prices update every 5 minutes
✅ Index levels update every 5 minutes
✅ Commodity prices update every 15 minutes (futures trade 24/5)
⚠️ Yahoo Finance API may still return 404s (known issue)

#### Outside Market Hours
✅ Stock prices show previous close
✅ Index levels show previous close
✅ Commodity prices update (futures trade 24/5)
✅ System clearly states "Previous Close" in responses

#### Weekends & Holidays
✅ All prices show last trading day's close
✅ Commodity prices may update (international markets)
✅ System handles gracefully, no errors

### 🚀 Recommended Fixes (Priority Order)

1. **HIGH PRIORITY**: Switch to NSE official API for stocks
   - More reliable than Yahoo Finance
   - Actual NSE prices, not proxied data
   - Implementation time: 4-6 hours

2. **MEDIUM PRIORITY**: Add data freshness indicators
   - Show "Last updated: 5 minutes ago"
   - Show "Market closed - Previous close shown"
   - Implementation time: 2 hours

3. **MEDIUM PRIORITY**: Implement fallback data source
   - If Yahoo Finance fails, try alternative
   - Could use yfinance library as backup
   - Implementation time: 3 hours

4. **LOW PRIORITY**: Add WebSocket for real-time updates
   - Stream live prices during market hours
   - Requires significant architecture change
   - Implementation time: 2-3 days

### 📞 User Communication

When prices might appear outdated, communicate clearly:

**Example Response Enhancement**:
```markdown
# Stock Analysis: WIPRO for Rahul Sharma

⏰ **Market Status**: CLOSED (Last updated: 3:30 PM IST, 05-Jul-2026)
📊 **Price shown**: Previous day's closing price

## 🟢 YES - RECOMMENDED

### Stock Information
- **Current Price**: ₹632.35 *(as of market close)*
- **1-Year Performance**: +21.5%
...
```

### 🔬 Debugging Price Issues

If prices seem wrong, check:

1. **Is market open?** 
   - If no, prices are yesterday's close (expected)

2. **Check cache age**:
   ```python
   # In backend logs, look for:
   "Using cached data for stock_quote:RELIANCE (age: 3m 45s)"
   ```

3. **Check Yahoo Finance directly**:
   ```bash
   curl "https://query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS?interval=1d&range=1d"
   ```

4. **Check if API is returning 404**:
   ```
   # In backend logs:
   "Stock quote API error for RELIANCE: 404"
   ```

5. **Compare with official source**:
   - NSE: https://www.nseindia.com/get-quotes/equity?symbol=RELIANCE
   - BSE: https://www.bseindia.com/stock-share-price/reliance-industries-ltd/reliance/500325/

---

**Last Updated**: July 5, 2026  
**Maintained By**: RM AI Advisory Team
