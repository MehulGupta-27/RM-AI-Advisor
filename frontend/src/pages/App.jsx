import React, { useState, useEffect } from 'react';
import { fetchClients, sendChatMessage, fetchClientDetails, fetchClientHoldings } from '../api/client';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import './App.css';

// Simple markdown formatter
function formatMarkdown(text) {
  if (!text) return '';
  
  let html = text
    // Headers
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Lists
    .replace(/^\- (.*$)/gm, '<li>$1</li>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr>')
    // Line breaks
    .replace(/\n/g, '<br>');
  
  // Wrap consecutive <li> in <ul>
  html = html.replace(/(<li>.*?<\/li><br>)+/g, (match) => {
    return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
  });
  
  return html;
}

// Dashboard Component
function Dashboard({ clientDetails, holdings }) {
  if (!clientDetails) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading portfolio data...</p>
      </div>
    );
  }

  // Prepare allocation data for pie chart
  const allocationData = [
    { name: 'Equity', value: clientDetails.current_equity_pct, color: '#7b9cff' },
    { name: 'Mutual Funds', value: clientDetails.current_mutual_fund_pct, color: '#4ade80' },
    { name: 'Gold', value: clientDetails.current_gold_pct, color: '#fbbf24' },
    { name: 'Debt/FD', value: clientDetails.current_fd_debt_pct, color: '#a78bfa' },
  ].filter(item => item.value > 0);

  // Group holdings by asset type
  const holdingsByType = holdings.reduce((acc, holding) => {
    if (!acc[holding.asset_type]) {
      acc[holding.asset_type] = [];
    }
    acc[holding.asset_type].push(holding);
    return acc;
  }, {});

  // Calculate total values by asset type for bar chart
  const assetTypeData = Object.keys(holdingsByType).map(type => ({
    name: type,
    value: holdingsByType[type].reduce((sum, h) => sum + h.current_value, 0),
  }));

  // Risk dimensions for radar chart
  const riskData = [
    { dimension: 'Market Risk', value: clientDetails.risk_score * 10 || 50 },
    { dimension: 'Liquidity', value: (clientDetails.current_equity_pct + clientDetails.current_mutual_fund_pct) * 0.8 },
    { dimension: 'Concentration', value: holdings.length > 20 ? 40 : 70 },
    { dimension: 'Age Suitability', value: clientDetails.age < 40 ? 80 : clientDetails.age < 60 ? 60 : 40 },
    { dimension: 'Diversification', value: Object.keys(holdingsByType).length * 20 },
  ];

  // Top holdings by value
  const topHoldings = [...holdings]
    .sort((a, b) => b.current_value - a.current_value)
    .slice(0, 10);

  return (
    <div className="dashboard-container">
      {/* Summary Cards */}
      <div className="dashboard-summary">
        <div className="summary-card">
          <div className="summary-label">Total AUM</div>
          <div className="summary-value">₹{clientDetails.current_portfolio_value.toLocaleString('en-IN')}</div>
          <div className="summary-sublabel">Current Portfolio Value</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Total Returns</div>
          <div className={`summary-value ${clientDetails.total_returns >= 0 ? 'positive' : 'negative'}`}>
            ₹{Math.abs(clientDetails.total_returns).toLocaleString('en-IN')}
          </div>
          <div className="summary-sublabel">{clientDetails.return_percentage.toFixed(2)}% Return</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Total Invested</div>
          <div className="summary-value">₹{clientDetails.total_invested.toLocaleString('en-IN')}</div>
          <div className="summary-sublabel">Principal Amount</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Holdings</div>
          <div className="summary-value">{holdings.length}</div>
          <div className="summary-sublabel">Across {Object.keys(holdingsByType).length} Asset Types</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="dashboard-charts">
        {/* Allocation Pie Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Portfolio Allocation</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={allocationData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {allocationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `${value.toFixed(2)}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Asset Type Bar Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Asset Type Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={assetTypeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="name" stroke="#8a8f9e" tick={{ fontSize: 12 }} />
              <YAxis stroke="#8a8f9e" tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value) => `₹${value.toLocaleString('en-IN')}`}
                contentStyle={{ background: '#1c1f26', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
              />
              <Bar dataKey="value" fill="#7b9cff" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Radar Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Risk Profile</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={riskData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis dataKey="dimension" stroke="#8a8f9e" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} stroke="#8a8f9e" tick={false} />
              <Radar name="Risk Score" dataKey="value" stroke="#7b9cff" fill="#7b9cff" fillOpacity={0.6} />
              <Tooltip
                contentStyle={{ background: '#1c1f26', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="holdings-section">
        <h3 className="section-title">Top 10 Holdings</h3>
        <div className="holdings-table-wrapper">
          <table className="holdings-table">
            <thead>
              <tr>
                <th>Asset Name</th>
                <th>Type</th>
                <th>Quantity</th>
                <th>Current Price</th>
                <th>Current Value</th>
                <th>Invested</th>
                <th>P&L</th>
                <th>Return %</th>
              </tr>
            </thead>
            <tbody>
              {topHoldings.map((holding) => {
                const returnPct = ((holding.profit_loss / holding.invested_amount) * 100).toFixed(2);
                return (
                  <tr key={holding.holding_id}>
                    <td className="asset-name">{holding.asset_name}</td>
                    <td>
                      <span className={`asset-type-badge ${holding.asset_type.toLowerCase().replace(/\s+/g, '-')}`}>
                        {holding.asset_type}
                      </span>
                    </td>
                    <td>{holding.quantity.toFixed(2)}</td>
                    <td>₹{holding.current_price.toLocaleString('en-IN')}</td>
                    <td className="amount">₹{holding.current_value.toLocaleString('en-IN')}</td>
                    <td className="amount">₹{holding.invested_amount.toLocaleString('en-IN')}</td>
                    <td className={`amount ${holding.profit_loss >= 0 ? 'positive' : 'negative'}`}>
                      {holding.profit_loss >= 0 ? '+' : ''}₹{holding.profit_loss.toLocaleString('en-IN')}
                    </td>
                    <td className={`amount ${parseFloat(returnPct) >= 0 ? 'positive' : 'negative'}`}>
                      {returnPct >= 0 ? '+' : ''}{returnPct}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Asset Type Breakdown */}
      <div className="asset-breakdown">
        <h3 className="section-title">Holdings by Asset Type</h3>
        <div className="breakdown-grid">
          {Object.entries(holdingsByType).map(([type, typeHoldings]) => {
            const totalValue = typeHoldings.reduce((sum, h) => sum + h.current_value, 0);
            const totalInvested = typeHoldings.reduce((sum, h) => sum + h.invested_amount, 0);
            const totalPL = typeHoldings.reduce((sum, h) => sum + h.profit_loss, 0);
            const returnPct = ((totalPL / totalInvested) * 100).toFixed(2);

            return (
              <div key={type} className="breakdown-card">
                <div className="breakdown-header">
                  <span className={`asset-type-badge ${type.toLowerCase().replace(/\s+/g, '-')}`}>{type}</span>
                  <span className="breakdown-count">{typeHoldings.length} holdings</span>
                </div>
                <div className="breakdown-value">₹{totalValue.toLocaleString('en-IN')}</div>
                <div className="breakdown-stats">
                  <div>Invested: ₹{totalInvested.toLocaleString('en-IN')}</div>
                  <div className={parseFloat(returnPct) >= 0 ? 'positive' : 'negative'}>
                    {returnPct >= 0 ? '+' : ''}{returnPct}% return
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState(null);
  const [clientDetails, setClientDetails] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [goal, setGoal] = useState('wealth_creation');
  const [timePeriod, setTimePeriod] = useState('5-7 years');
  const [investmentAmount, setInvestmentAmount] = useState('');
  const [activeTab, setActiveTab] = useState('chat');

  // Load clients on mount
  useEffect(() => {
    loadClients();
  }, []);

  // Load client details and holdings when selected
  useEffect(() => {
    if (selectedClient) {
      loadClientDetails();
      loadClientHoldings();
    }
  }, [selectedClient]);

  async function loadClients() {
    try {
      const data = await fetchClients();
      setClients(data);
    } catch (error) {
      console.error('Failed to load clients:', error);
    }
  }

  async function loadClientDetails() {
    if (!selectedClient) return;
    try {
      const data = await fetchClientDetails(selectedClient.client_id);
      setClientDetails(data);
    } catch (error) {
      console.error('Failed to load client details:', error);
    }
  }

  async function loadClientHoldings() {
    if (!selectedClient) return;
    try {
      const data = await fetchClientHoldings(selectedClient.client_id);
      setHoldings(data);
    } catch (error) {
      console.error('Failed to load holdings:', error);
    }
  }

  async function handleSendMessage() {
    if (!inputMessage.trim() || loading) return;
    
    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    
    try {
      const response = await sendChatMessage({
        message: inputMessage,
        clientId: selectedClient?.client_id,
        goal,
        timePeriod,
        investmentAmount: investmentAmount ? parseFloat(investmentAmount) : null,
      });
      
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        intent: response.intent,
        timestamp: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        error: true,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  }

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="logo">
            <div className="logo-icon">RM</div>
            <span className="logo-text">RM Advisor</span>
            <span className="ai-badge">AI</span>
          </div>
        </div>
        <nav className="header-nav">
          <button className={`nav-tab ${activeTab === 'chat' ? 'active' : ''}`} onClick={() => setActiveTab('chat')}>
            💬 Chat
          </button>
          <button className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveTab('dashboard')}>
            📊 Dashboard
          </button>
        </nav>
        <div className="header-right">
          <div className="user-avatar">RM</div>
        </div>
      </header>

      <div className="app-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-header">
            <h3>Clients</h3>
          </div>
          <div className="client-list">
            {clients.map(client => (
              <div
                key={client.client_id}
                className={`client-card ${selectedClient?.client_id === client.client_id ? 'active' : ''}`}
                onClick={() => setSelectedClient(client)}
              >
                <div className="client-avatar">
                  {client.client_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                </div>
                <div className="client-info">
                  <div className="client-name">{client.client_name}</div>
                  <div className="client-meta">
                    <span className={`risk-badge risk-${client.risk_factor?.toLowerCase()}`}>
                      {client.risk_factor}
                    </span>
                    {(client.ytd_return !== undefined && client.ytd_return !== null) && (
                      <span className={`return-badge ${client.ytd_return >= 0 ? 'positive' : 'negative'}`}>
                        {client.ytd_return >= 0 ? '+' : ''}{client.ytd_return.toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main content */}
        <main className="main-content">
          {!selectedClient ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h2>Select a client to start</h2>
              <p>Choose a client from the sidebar to begin providing investment advice</p>
            </div>
          ) : activeTab === 'dashboard' ? (
            <Dashboard clientDetails={clientDetails} holdings={holdings} />
          ) : (
            <>
              {/* Context bar */}
              <div className="context-bar">
                <div className="context-client">
                  <div className="context-avatar">
                    {selectedClient.client_name?.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="context-name">{selectedClient.client_name}</div>
                    <div className="context-details">
                      Age {selectedClient.age} • {selectedClient.city}
                    </div>
                  </div>
                </div>
                <span className={`risk-badge risk-${selectedClient.risk_factor?.toLowerCase()}`}>
                  {selectedClient.risk_factor} Risk
                </span>
              </div>

              {/* Metric bar */}
              <div className="metric-bar">
                <div className="metric-card">
                  <div className="metric-label">AUM</div>
                  <div className="metric-value">
                    ₹{selectedClient.current_portfolio_value?.toLocaleString('en-IN')}
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">YTD Return</div>
                  <div className={`metric-value ${selectedClient.return_percentage >= 0 ? 'positive' : 'negative'}`}>
                    {selectedClient.return_percentage >= 0 ? '+' : ''}{selectedClient.return_percentage?.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Risk Level</div>
                  <div className="metric-value">{selectedClient.risk_factor}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Holdings</div>
                  <div className="metric-value">{selectedClient.holdings_count || 0}</div>
                </div>
              </div>

              {/* Chat area */}
              <div className="chat-area">
                {messages.length === 0 ? (
                  <div className="chat-empty">
                    <p>Ask me anything about {selectedClient.client_name}'s portfolio or investment strategy</p>
                    <div className="demo-queries-section">
                      <h4 className="demo-title">Demo Queries</h4>
                      <div className="demo-queries-list">
                        <button onClick={() => setInputMessage('show me all clients with low risk')}>
                          show me all clients with low risk
                        </button>
                        <button onClick={() => setInputMessage('what are this week\'s top performing shares')}>
                          what are this week's top performing shares
                        </button>
                        <button onClick={() => setInputMessage('how much has gold price increased in the last 1 year')}>
                          how much has gold price increased in the last 1 year
                        </button>
                        <button onClick={() => setInputMessage(`where should ${selectedClient.client_name} invest their capital`)}>
                          where should {selectedClient.client_name} invest their capital
                        </button>
                        <button onClick={() => setInputMessage(`should ${selectedClient.client_name} invest in Wipro`)}>
                          should {selectedClient.client_name} invest in Wipro
                        </button>
                        <button onClick={() => setInputMessage(`is ${selectedClient.client_name}'s portfolio balanced`)}>
                          is {selectedClient.client_name}'s portfolio balanced
                        </button>
                        <button onClick={() => setInputMessage(`show me all the stocks where ${selectedClient.client_name} has invested`)}>
                          show me all the stocks where {selectedClient.client_name} has invested
                        </button>
                        <button onClick={() => setInputMessage(`is ${selectedClient.client_name}'s portfolio diversified`)}>
                          is {selectedClient.client_name}'s portfolio diversified
                        </button>
                        <button onClick={() => setInputMessage(`does ${selectedClient.client_name} need portfolio rebalancing`)}>
                          does {selectedClient.client_name} need portfolio rebalancing
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="messages">
                    {messages.map((msg, idx) => (
                      <div key={idx} className={`message message-${msg.role}`}>
                        {msg.role === 'assistant' && (
                          <div className="message-header">
                            <span className="message-label">AI Analysis</span>
                            {msg.intent && (
                              <span className="intent-badge">{msg.intent}</span>
                            )}
                          </div>
                        )}
                        <div className="message-content" dangerouslySetInnerHTML={{
                          __html: formatMarkdown(msg.content)
                        }} />
                      </div>
                    ))}
                    {loading && (
                      <div className="message message-assistant">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Goal + Time + Amount bar */}
              <div className="query-bar">
                <span className="qc-label">Goal</span>
                <select value={goal} onChange={(e) => setGoal(e.target.value)} className="goal-select">
                  <option value="">— None —</option>
                  <option value="retirement">Retirement</option>
                  <option value="wealth_creation">Wealth Creation</option>
                  <option value="tax_saving">Tax Saving</option>
                  <option value="child_education">Child Education</option>
                  <option value="home_purchase">Home Purchase</option>
                  <option value="emergency_fund">Emergency Fund</option>
                </select>
                <div className="divider-vertical"></div>
                <span className="qc-label">Time Period</span>
                <select value={timePeriod} onChange={(e) => setTimePeriod(e.target.value)} className="period-select">
                  <option value="< 1 year">&lt; 1 year</option>
                  <option value="1-3 years">1-3 years</option>
                  <option value="3-5 years">3-5 years</option>
                  <option value="5-7 years">5-7 years</option>
                  <option value="7-10 years">7-10 years</option>
                  <option value="10+ years">10+ years</option>
                </select>
                <div className="divider-vertical"></div>
                <span className="qc-label">Investment Amount (₹)</span>
                <input 
                  type="number" 
                  value={investmentAmount} 
                  onChange={(e) => setInvestmentAmount(e.target.value)}
                  placeholder="e.g., 500000"
                  className="amount-input"
                  min="0"
                  step="10000"
                />
              </div>
              {/* Input area */}
              <div className="input-area">
                  <textarea
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about investments, market data, or portfolio recommendations..."
                    rows={1}
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || loading}
                    className="send-button"
                  >
                    Send
                  </button>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
