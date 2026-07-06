-- Additional tables for RM AI Advisory Platform
-- To be run after the main schema (clients, portfolios, holdings already exist)

-- Conversation history for audit trail and multi-turn context
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id   BIGSERIAL PRIMARY KEY,
    client_id         INTEGER REFERENCES clients(client_id),
    rm_user_id        VARCHAR(80),
    role              VARCHAR(20) NOT NULL,      -- 'user' | 'assistant'
    intent            VARCHAR(30),               -- db_query | market_query | investment_advice | general_chat
    content           TEXT NOT NULL,
    structured_output JSONB,                     -- raw agent JSON for audit/debug
    compliance_status VARCHAR(10),               -- PASS | FAIL | N/A
    risk_score        NUMERIC(3,1),
    risk_level        VARCHAR(20),
    created_at        TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_conversations_client ON conversations(client_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- FD rates: no reliable free live API exists, seed manually
CREATE TABLE IF NOT EXISTS fd_rates (
    bank_name           VARCHAR(80) NOT NULL,
    tenure_months       INTEGER NOT NULL,
    interest_rate       NUMERIC(5,2) NOT NULL,
    senior_citizen_rate NUMERIC(5,2),
    updated_at          DATE NOT NULL DEFAULT CURRENT_DATE,
    PRIMARY KEY (bank_name, tenure_months)
);

-- Seed initial FD rates (example data - update quarterly)
INSERT INTO fd_rates (bank_name, tenure_months, interest_rate, senior_citizen_rate) VALUES
('SBI', 12, 6.50, 7.00),
('SBI', 24, 6.75, 7.25),
('SBI', 36, 6.75, 7.25),
('SBI', 60, 6.50, 7.50),
('HDFC Bank', 12, 7.00, 7.50),
('HDFC Bank', 24, 7.00, 7.50),
('HDFC Bank', 36, 7.00, 7.50),
('HDFC Bank', 60, 7.00, 7.50),
('ICICI Bank', 12, 6.70, 7.20),
('ICICI Bank', 24, 7.00, 7.50),
('ICICI Bank', 36, 7.00, 7.50),
('ICICI Bank', 60, 7.00, 7.50),
('Axis Bank', 12, 7.00, 7.50),
('Axis Bank', 24, 7.00, 7.50),
('Axis Bank', 36, 7.10, 7.60),
('Axis Bank', 60, 7.10, 7.60)
ON CONFLICT (bank_name, tenure_months) DO NOTHING;
