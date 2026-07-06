import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion, useAnimation, useInView } from 'framer-motion';
import './HomeNew.css';

// Animated counter component
function AnimatedCounter({ end, duration = 2, suffix = '' }) {
  const [count, setCount] = useState(0);
  const ref = React.useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;
    
    let startTime;
    const animate = (currentTime) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / (duration * 1000), 1);
      setCount(Math.floor(progress * end));
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }, [isInView, end, duration]);

  return <span ref={ref}>{count}{suffix}</span>;
}

function HomeNew() {
  const [activeAgent, setActiveAgent] = useState(0);
  const agents = [
    { icon: '🔍', name: 'Query Understanding', desc: 'Classifies intent and extracts entities' },
    { icon: '👤', name: 'Client Resolver', desc: 'Fetches profile and portfolio data' },
    { icon: '📊', name: 'Market Intelligence', desc: 'Pulls live NSE, MF, commodity data' },
    { icon: '💡', name: 'Investment Advisor', desc: 'Generates personalized recommendations' },
    { icon: '✓', name: 'Compliance Agent', desc: 'Validates against 9 hard rules' },
    { icon: '⚖️', name: 'Risk Agent', desc: 'Scores across 5 risk dimensions' },
    { icon: '📝', name: 'Response Formatter', desc: 'Formats final recommendation' }
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveAgent((prev) => (prev + 1) % agents.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="home-new">
      {/* Hero with Gradient Background */}
      <section className="hero-section">
        <div className="hero-gradient"></div>
        <div className="hero-grid"></div>
        
        <motion.div
          className="hero-content"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1 }}
        >
          <motion.div
            className="hero-badge"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span>Real-time Multi-Agent Intelligence</span>
          </motion.div>
          
          <motion.h1
            className="hero-title"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.8 }}
          >
            Investment Advisory
            <br />
            <span className="gradient-text">Governed by AI Agents</span>
          </motion.h1>
          
          <motion.p
            className="hero-subtitle"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5, duration: 0.8 }}
          >
            7 specialized AI agents work together to generate compliant, personalized
            <br />
            investment recommendations—with every plan independently validated for risk
          </motion.p>
          
          <motion.div
            className="hero-cta-group"
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.8 }}
          >
            <Link to="/app" className="cta-primary">
              <span>Launch RM Advisor</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </Link>
            <a href="#how-it-works" className="cta-secondary">
              See How It Works
            </a>
          </motion.div>
          
          {/* Floating stats */}
          <motion.div
            className="hero-stats"
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.9, duration: 0.8 }}
          >
            <div className="stat-item">
              <div className="stat-value"><AnimatedCounter end={7} /></div>
              <div className="stat-label">AI Agents</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value"><AnimatedCounter end={30} />+</div>
              <div className="stat-label">Clients Analyzed</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value"><AnimatedCounter end={100} suffix="%" /></div>
              <div className="stat-label">Compliance Rate</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value">&lt;<AnimatedCounter end={15} />s</div>
              <div className="stat-label">Avg Response</div>
            </div>
          </motion.div>
        </motion.div>
        
        {/* Animated orbs */}
        <div className="hero-orb orb-1"></div>
        <div className="hero-orb orb-2"></div>
        <div className="hero-orb orb-3"></div>
      </section>

      {/* Problem Statement */}
      <section className="problem-section" id="how-it-works">
        <motion.div
          className="container"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="section-title">The Challenge</h2>
          <p className="problem-text">
            Relationship Managers serve clients across <strong>vastly different ages, risk appetites, and financial goals</strong>. 
            Manually cross-referencing live market data, compliance rules, and suitability requirements for every conversation doesn't scale—and 
            <strong> clients expect instant, personalized guidance</strong>.
          </p>
        </motion.div>
      </section>

      {/* Agent Showcase */}
      <section className="agents-showcase">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="section-title">7-Agent Architecture</h2>
            <p className="section-subtitle">
              Not one monolithic prompt—a coordinated team where each agent has a specific role
            </p>
          </motion.div>

          <div className="agent-pipeline">
            {agents.map((agent, index) => (
              <motion.div
                key={index}
                className={`agent-node ${index === activeAgent ? 'active' : ''}`}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                onMouseEnter={() => setActiveAgent(index)}
              >
                <div className="agent-number">{index + 1}</div>
                <div className="agent-icon-large">{agent.icon}</div>
                <h3>{agent.name}</h3>
                <p>{agent.desc}</p>
                {index < agents.length - 1 && <div className="agent-arrow">→</div>}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Guarantee */}
      <section className="guarantee-section">
        <motion.div
          className="container"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <div className="guarantee-card">
            <div className="guarantee-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L3 7v6c0 5.5 3.8 10.7 9 12 5.2-1.3 9-6.5 9-12V7l-9-5z" stroke="currentColor" strokeWidth="2" fill="none"/>
                <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
            <h2>100% Compliance Guarantee</h2>
            <p className="guarantee-desc">
              No recommendation reaches a client without passing independent compliance validation
              and a five-dimension risk assessment—<strong>automatically, every time</strong>.
            </p>
            <div className="guarantee-features">
              <div className="feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17l-5-5" stroke="#4ade80" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span><strong>9 hard rules</strong> enforced by deterministic code</span>
              </div>
              <div className="feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17l-5-5" stroke="#4ade80" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span><strong>Bounded retry</strong> with fallback (never stuck)</span>
              </div>
              <div className="feature">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17l-5-5" stroke="#4ade80" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                <span><strong>Senior review</strong> flagged for high-risk profiles</span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Data Coverage */}
      <section className="coverage-section">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="section-title">Live Market Intelligence</h2>
            <p className="section-subtitle">
              Real-time data across all asset classes—unified in one conversation
            </p>
          </motion.div>

          <div className="coverage-grid">
            {[
              { icon: '📈', title: 'NSE Equities', desc: 'Live stock prices via Yahoo Finance' },
              { icon: '🏦', title: 'Mutual Funds', desc: 'NAVs from mfapi.in' },
              { icon: '🪙', title: 'Commodities', desc: 'Gold, Silver, Crude prices' },
              { icon: '📊', title: 'Indices', desc: 'Nifty, Sensex, Bank Nifty' }
            ].map((item, index) => (
              <motion.div
                key={index}
                className="coverage-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1, duration: 0.5 }}
                whileHover={{ scale: 1.05, boxShadow: '0 10px 40px rgba(123, 156, 255, 0.3)' }}
              >
                <div className="coverage-card-icon">{item.icon}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="usecases-section">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="section-title">Built for Real Workflows</h2>
          </motion.div>

          <div className="usecases-grid">
            {[
              { 
                title: 'Seconds, not spreadsheets', 
                desc: 'Answer portfolio questions instantly instead of manual lookups across multiple tools',
                metric: '15s',
                label: 'Avg Response'
              },
              { 
                title: 'Auditable rationale', 
                desc: 'Every recommendation carries consistent, traceable reasoning—no black boxes',
                metric: '100%',
                label: 'Transparency'
              },
              { 
                title: 'One conversation', 
                desc: 'Cover stocks, funds, gold, and debt together instead of switching platforms',
                metric: '4',
                label: 'Asset Classes'
              }
            ].map((item, index) => (
              <motion.div
                key={index}
                className="usecase-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15, duration: 0.6 }}
              >
                <div className="usecase-metric">
                  <span className="metric-value">{item.metric}</span>
                  <span className="metric-label">{item.label}</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="tech-section">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <h2 className="section-title">Powered By</h2>
            <div className="tech-stack">
              {['LangGraph', 'FastAPI', 'React', 'PostgreSQL', 'Groq (Llama 3.3)'].map((tech, index) => (
                <motion.div
                  key={index}
                  className="tech-item"
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  whileHover={{ scale: 1.1 }}
                >
                  {tech}
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <motion.div
          className="container"
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8 }}
        >
          <h2>Ready to see it in action?</h2>
          <p>Experience the full 7-agent advisory pipeline with live market data</p>
          <Link to="/app" className="cta-primary-large">
            <span>Launch RM Advisor</span>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="home-footer">
        <div className="container">
          <div className="footer-content">
            <div>
              <h3>RM AI Advisory</h3>
              <p>Multi-agent investment advisory platform with built-in compliance governance</p>
            </div>
            <div>
              <Link to="/app" className="footer-link">Launch Application →</Link>
            </div>
          </div>
          <div className="footer-bottom">
            <p>© 2026 RM AI Advisory. Built for demonstration purposes.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default HomeNew;
