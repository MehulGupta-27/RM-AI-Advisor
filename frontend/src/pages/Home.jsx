import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import './Home.css';

function Home() {
  const fadeIn = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  const stagger = {
    visible: {
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="home-container">
      {/* Hero Section */}
      <motion.section 
        className="hero"
        initial="hidden"
        animate="visible"
        variants={fadeIn}
      >
        <div className="hero-content">
          <motion.h1 variants={fadeIn}>
            Every client deserves a portfolio built for them—not a template
          </motion.h1>
          <motion.p variants={fadeIn} className="hero-subtitle">
            AI-powered investment advisory with built-in compliance, risk scoring, and real-time market intelligence—all in seconds.
          </motion.p>
          <motion.div variants={fadeIn}>
            <Link to="/app" className="cta-button">
              Open RM Advisor →
            </Link>
          </motion.div>
        </div>
        <div className="hero-background"></div>
      </motion.section>

      {/* Problem Section */}
      <motion.section 
        className="problem-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeIn}
      >
        <div className="container">
          <p className="problem-text">
            Relationship Managers juggle dozens of clients across wildly different ages, risk appetites, and financial goals. Manually cross-referencing live market data against suitability rules for every conversation doesn't scale—and clients expect instant, personalized guidance.
          </p>
        </div>
      </motion.section>

      {/* How It Thinks Section */}
      <motion.section 
        className="agents-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={stagger}
      >
        <div className="container">
          <motion.h2 variants={fadeIn}>How it thinks—the agent team</motion.h2>
          <div className="agents-grid">
            <motion.div className="agent-card" variants={fadeIn}>
              <div className="agent-icon">🧠</div>
              <h3>Understands</h3>
              <p>Query Understanding classifies intent and extracts entities from natural language</p>
            </motion.div>
            <motion.div className="agent-card" variants={fadeIn}>
              <div className="agent-icon">📊</div>
              <h3>Researches</h3>
              <p>Market Intelligence fetches live NSE data, gold prices, and mutual fund NAVs in parallel</p>
            </motion.div>
            <motion.div className="agent-card" variants={fadeIn}>
              <div className="agent-icon">💡</div>
              <h3>Recommends</h3>
              <p>Investment Advisor generates personalized allocations based on age, risk, and goals</p>
            </motion.div>
            <motion.div className="agent-card" variants={fadeIn}>
              <div className="agent-icon">✓</div>
              <h3>Checks</h3>
              <p>Compliance Agent validates against deterministic rules and regulatory requirements</p>
            </motion.div>
            <motion.div className="agent-card" variants={fadeIn}>
              <div className="agent-icon">⚖️</div>
              <h3>Scores</h3>
              <p>Risk Agent evaluates across 5 dimensions: market, liquidity, concentration, alignment, behavior</p>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Compliance Guarantee */}
      <motion.section 
        className="compliance-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeIn}
      >
        <div className="container">
          <div className="compliance-panel">
            <h2>The guarantee</h2>
            <p>
              No recommendation reaches a client without passing an independent compliance check and a five-point risk score—automatically, every time.
            </p>
            <div className="compliance-features">
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span>9 deterministic allocation rules (code, not LLM guesses)</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span>Bounded retry with fallback (never stuck, always compliant)</span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">✓</span>
                <span>Senior review flagged for high-risk profiles</span>
              </div>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Coverage Section */}
      <motion.section 
        className="coverage-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={fadeIn}
      >
        <div className="container">
          <h2>What it covers</h2>
          <p className="coverage-intro">
            Live data across equities, mutual funds, commodities, and fixed deposits—unified in one conversation.
          </p>
          <div className="coverage-grid">
            <div className="coverage-item">
              <div className="coverage-icon">📈</div>
              <span>NSE Equities</span>
            </div>
            <div className="coverage-item">
              <div className="coverage-icon">🏦</div>
              <span>Mutual Funds</span>
            </div>
            <div className="coverage-item">
              <div className="coverage-icon">🪙</div>
              <span>Gold & Commodities</span>
            </div>
            <div className="coverage-item">
              <div className="coverage-icon">💰</div>
              <span>Fixed Deposits</span>
            </div>
          </div>
        </div>
      </motion.section>

      {/* Impact Section */}
      <motion.section 
        className="impact-section"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
        variants={stagger}
      >
        <div className="container">
          <h2>Built for real workflows</h2>
          <div className="impact-grid">
            <motion.div className="impact-card" variants={fadeIn}>
              <h3>Seconds, not spreadsheets</h3>
              <p>Answer portfolio questions instantly instead of manual lookups across multiple tools</p>
            </motion.div>
            <motion.div className="impact-card" variants={fadeIn}>
              <h3>Auditable rationale</h3>
              <p>Every recommendation carries a consistent, traceable explanation—no black boxes</p>
            </motion.div>
            <motion.div className="impact-card" variants={fadeIn}>
              <h3>One conversation</h3>
              <p>Cover stocks, funds, gold, and debt together instead of switching between four platforms</p>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="container">
          <p>RM AI Advisory Platform • Built with LangChain, FastAPI, and React</p>
          <Link to="/app" className="footer-link">Launch Application →</Link>
        </div>
      </footer>
    </div>
  );
}

export default Home;
