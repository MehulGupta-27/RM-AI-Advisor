/**
 * API Client for RM AI Advisory Backend
 * Handles all HTTP communication with FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };
  
  const config = { ...defaultOptions, ...options };
  
  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

/**
 * Fetch all clients with portfolio metrics
 */
export async function fetchClients(search = '', riskFilter = null) {
  let endpoint = '/api/clients';
  const params = new URLSearchParams();
  
  if (search) params.append('search', search);
  if (riskFilter) params.append('risk_factor', riskFilter);
  
  if (params.toString()) {
    endpoint += `?${params.toString()}`;
  }
  
  return apiFetch(endpoint);
}

/**
 * Fetch detailed client profile
 */
export async function fetchClientDetails(clientId) {
  return apiFetch(`/api/clients/${clientId}`);
}

/**
 * Fetch client holdings breakdown
 */
export async function fetchClientHoldings(clientId) {
  return apiFetch(`/api/clients/${clientId}/holdings`);
}

/**
 * Fetch conversation history for a client
 */
export async function fetchClientMessages(clientId) {
  return apiFetch(`/api/clients/${clientId}/messages`);
}

/**
 * Send a chat message
 */
export async function sendChatMessage({ message, clientId, goal, timePeriod, investmentAmount }) {
  return apiFetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      message,
      client_id: clientId,
      goal,
      time_period: timePeriod,
      investment_amount: investmentAmount,
    }),
  });
}

/**
 * Health check
 */
export async function healthCheck() {
  return apiFetch('/api/health');
}

export default {
  fetchClients,
  fetchClientDetails,
  fetchClientHoldings,
  fetchClientMessages,
  sendChatMessage,
  healthCheck,
};
