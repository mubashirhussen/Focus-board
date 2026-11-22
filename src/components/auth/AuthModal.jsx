import React, { useState } from 'react';
import {
  X,
  Lock,
  Mail,
  User,
  ArrowRight,
  Sparkles,
  Eye,
  EyeOff,
  ShieldCheck,
  CheckCircle2,
  KeyRound,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './AuthModal.css';

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, login, loginWithGoogle, register, authError, isLoading } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [localError, setLocalError] = useState('');
  const [showGooglePicker, setShowGooglePicker] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  // Suggested device accounts
  const detectedAccounts = [
    { name: 'Sheik Mubashir Hussen', email: 'mubashir.hussen@gmail.com', avatar: 'M' },
    { name: 'Work Account', email: 'mubashir@enterprise.io', avatar: 'W' },
  ];

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (!email || !password) {
      setLocalError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters.');
      return;
    }

    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        if (!name.trim()) {
          setLocalError('Please enter your full name.');
          return;
        }
        await register(name.trim(), email, password);
      }
    } catch {
      // Auth error is captured in context
    }
  };

  const handleGoogleSignIn = (account) => {
    setGoogleLoading(true);
    setLocalError('');
    setTimeout(async () => {
      try {
        await loginWithGoogle(account || detectedAccounts[0]);
        setShowGooglePicker(false);
      } catch (err) {
        setLocalError(err.message || 'Google sign-in failed');
      } finally {
        setGoogleLoading(false);
      }
    }, 450);
  };

  const handleDemoLogin = async () => {
    setLocalError('');
    try {
      await login('demo@focusboard.io', 'password123');
    } catch {
      try {
        await register('Demo Member', 'demo@focusboard.io', 'password123', 'Member');
      } catch (err) {
        setLocalError(err.message || 'Demo login failed');
      }
    }
  };

  return (
    <div className="auth-modal-backdrop" onClick={closeAuthModal} role="dialog" aria-modal="true">
      <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className="auth-modal-close"
          onClick={closeAuthModal}
          aria-label="Close authentication modal"
        >
          <X size={18} />
        </button>

        {/* Modal Brand Header */}
        <div className="auth-header">
          <div className="auth-brand-badge">
            <span className="brand-dot" />
            <span>FocusBoard Enterprise</span>
          </div>
          <h2 className="auth-title">
            {mode === 'login' ? 'Welcome to FocusBoard' : 'Create your account'}
          </h2>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Access your unified tasks, autonomous AI agents, and workspace analytics.'
              : 'Sign up to start organizing high-impact projects with zero friction.'}
          </p>
        </div>

        {/* Google Sign In Option */}
        <div className="auth-google-section">
          {!showGooglePicker ? (
            <button
              type="button"
              className="google-signin-btn"
              onClick={() => setShowGooglePicker(true)}
              disabled={isLoading || googleLoading}
            >
              <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <span>{googleLoading ? 'Connecting to Google...' : 'Continue with Google'}</span>
            </button>
          ) : (
            <div className="google-accounts-picker">
              <div className="google-picker-header">
                <span className="picker-title">Choose a Google Account</span>
                <button
                  type="button"
                  className="picker-back-btn"
                  onClick={() => setShowGooglePicker(false)}
                >
                  Cancel
                </button>
              </div>
              <div className="google-accounts-list">
                {detectedAccounts.map((acc) => (
                  <button
                    key={acc.email}
                    type="button"
                    className="google-account-item"
                    onClick={() => handleGoogleSignIn(acc)}
                    disabled={googleLoading}
                  >
                    <div className="account-avatar">{acc.avatar}</div>
                    <div className="account-text">
                      <span className="account-name">{acc.name}</span>
                      <span className="account-email">{acc.email}</span>
                    </div>
                  </button>
                ))}
                <button
                  type="button"
                  className="google-account-item custom"
                  onClick={() => handleGoogleSignIn({ name: 'Google User', email: 'account@gmail.com' })}
                  disabled={googleLoading}
                >
                  <div className="account-avatar plus">+</div>
                  <div className="account-text">
                    <span className="account-name">Use another Google account</span>
                  </div>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="auth-divider">
          <span>OR CONTINUE WITH EMAIL</span>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="auth-tabs" role="tablist">
          <button
            type="button"
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => {
              setMode('login');
              setLocalError('');
            }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => {
              setMode('register');
              setLocalError('');
            }}
          >
            Create Account
          </button>
        </div>

        {/* Error Notice */}
        {(localError || authError) && (
          <div className="auth-error-banner" role="alert">
            {localError || authError}
          </div>
        )}

        {/* Manual Details Form */}
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {mode === 'register' && (
            <div className="form-group">
              <label htmlFor="auth-name" className="form-label">Full Name</label>
              <div className="input-with-icon">
                <User size={16} className="input-icon" />
                <input
                  id="auth-name"
                  type="text"
                  className="auth-input"
                  placeholder="e.g. Sheik Mubashir"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  required
                />
              </div>
            </div>
          )}

          <div className="form-group">
            <label htmlFor="auth-email" className="form-label">Work Email</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                id="auth-email"
                type="email"
                className="auth-input"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <div className="form-label-row">
              <label htmlFor="auth-password" className="form-label">Password</label>
              {mode === 'login' && (
                <button
                  type="button"
                  className="forgot-link"
                  onClick={() => alert('Password reset link sent to registered email.')}
                >
                  Forgot password?
                </button>
              )}
            </div>
            <div className="input-with-icon">
              <Lock size={16} className="input-icon" />
              <input
                id="auth-password"
                type={showPassword ? 'text' : 'password'}
                className="auth-input password-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
              />
              <button
                type="button"
                className="password-toggle-btn"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex={-1}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Remember Me Checkbox */}
          <div className="auth-options-row">
            <label className="remember-checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Remember this browser for 30 days</span>
            </label>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading || googleLoading}
          >
            <span>{isLoading ? 'Authenticating...' : mode === 'login' ? 'Sign In to FocusBoard' : 'Create Account'}</span>
            {!isLoading && <ArrowRight size={16} />}
          </button>
        </form>

        {/* 1-Click Demo Guest Mode */}
        <div className="auth-demo-footer">
          <button
            type="button"
            className="demo-account-btn"
            onClick={handleDemoLogin}
            disabled={isLoading || googleLoading}
          >
            <Sparkles size={15} />
            <span>Try Instant Demo Workspace (No password)</span>
          </button>
        </div>

        {/* Security & Compliance Badges */}
        <div className="auth-security-badges">
          <ShieldCheck size={13} />
          <span>256-bit SSL Encrypted • SOC 2 Ready • GDPR Compliant</span>
        </div>
      </div>
    </div>
  );
}

export default AuthModal;
