import React from 'react';
import { CheckCircle2, Shield, Zap, Sparkles, ArrowLeft } from 'lucide-react';
import { AuthFlow } from '../../components/auth/AuthFlow';
import { useAuth } from '../../context/AuthContext';
import './LoginPage.css';

export function LoginPage({ onNavigateToDashboard }) {
  const { isAuthenticated, user } = useAuth();

  return (
    <div className="login-page-container">
      {/* Background ambient lighting */}
      <div className="login-ambient-blob blob-1" aria-hidden="true" />
      <div className="login-ambient-blob blob-2" aria-hidden="true" />

      {/* Top Bar with Back to App link */}
      <header className="login-top-bar">
        <button
          type="button"
          className="login-back-btn"
          onClick={onNavigateToDashboard}
        >
          <ArrowLeft size={16} />
          <span>Return to Dashboard</span>
        </button>
      </header>

      <main className="login-page-content">
        {/* Left Side: Brand Value & Features (visible on desktop/laptop) */}
        <section className="login-showcase-panel">
          <div className="showcase-badge">
            <Sparkles size={14} className="badge-icon" />
            <span>Autonomous Intelligence & Productivity</span>
          </div>

          <h1 className="showcase-title">
            The workspace engine for high-performing teams.
          </h1>

          <p className="showcase-desc">
            Organize complex task pipelines, coordinate autonomous AI agents, sync external calendars,
            and monitor zero-trust security operations in one unified interface.
          </p>

          <ul className="showcase-feature-list">
            <li className="feature-item">
              <div className="feature-icon-wrap">
                <Zap size={16} className="feature-icon" />
              </div>
              <div className="feature-text">
                <strong>Passwordless Email OTP Verification</strong>
                <span>Secure single-use 6-digit codes delivered straight to your inbox.</span>
              </div>
            </li>

            <li className="feature-item">
              <div className="feature-icon-wrap">
                <CheckCircle2 size={16} className="feature-icon" />
              </div>
              <div className="feature-text">
                <strong>Continue with Google OAuth</strong>
                <span>One-tap instant authentication with verified identity and profile sync.</span>
              </div>
            </li>

            <li className="feature-item">
              <div className="feature-icon-wrap">
                <Shield size={16} className="feature-icon" />
              </div>
              <div className="feature-text">
                <strong>Enterprise Multi-Device Sessions</strong>
                <span>JWT rotation, active session auditing, and instant revocation across devices.</span>
              </div>
            </li>
          </ul>

          <div className="showcase-stats-row">
            <div className="stat-pill">
              <strong>99.9%</strong>
              <span>Uptime SLA</span>
            </div>
            <div className="stat-pill">
              <strong>256-bit</strong>
              <span>Encryption</span>
            </div>
            <div className="stat-pill">
              <strong>SOC 2 Type II</strong>
              <span>Compliant</span>
            </div>
          </div>
        </section>

        {/* Right Side: Interactive Auth Form */}
        <section className="login-form-panel">
          <AuthFlow
            standalone={true}
            onSuccess={onNavigateToDashboard}
            onCancel={onNavigateToDashboard}
          />
        </section>
      </main>

      <footer className="login-page-footer">
        <span>&copy; 2026 FocusBoard Inc. All rights reserved.</span>
        <div className="footer-links">
          <a href="#privacy" onClick={(e) => e.preventDefault()}>Privacy Policy</a>
          <span className="dot">&bull;</span>
          <a href="#terms" onClick={(e) => e.preventDefault()}>Terms of Service</a>
          <span className="dot">&bull;</span>
          <a href="#security" onClick={(e) => e.preventDefault()}>Security Trust Center</a>
        </div>
      </footer>
    </div>
  );
}

export default LoginPage;
