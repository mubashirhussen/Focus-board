import React, { useState } from 'react';
import { X, Lock, Mail, User, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './AuthModal.css';

export function AuthModal() {
  const { isAuthModalOpen, closeAuthModal, login, register, authError, isLoading } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState('');

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
    } catch (err) {
      // Auth error is captured in context
    }
  };

  const handleDemoLogin = async () => {
    setLocalError('');
    try {
      await login('demo@focusboard.io', 'password123');
    } catch {
      // If demo user does not exist, auto-register
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

        <div className="auth-header">
          <div className="auth-badge">FocusBoard Account</div>
          <h2 className="auth-title">
            {mode === 'login' ? 'Welcome Back' : 'Create an Account'}
          </h2>
          <p className="auth-subtitle">
            {mode === 'login'
              ? 'Sign in to access your synchronized tasks and productivity analytics.'
              : 'Sign up to manage your tasks across all devices securely.'}
          </p>
        </div>

        {(localError || authError) && (
          <div className="auth-error-banner" role="alert">
            {localError || authError}
          </div>
        )}

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
            <label htmlFor="auth-email" className="form-label">Email Address</label>
            <div className="input-with-icon">
              <Mail size={16} className="input-icon" />
              <input
                id="auth-email"
                type="email"
                className="auth-input"
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="auth-password" className="form-label">Password</label>
            <div className="input-with-icon">
              <Lock size={16} className="input-icon" />
              <input
                id="auth-password"
                type="password"
                className="auth-input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="auth-submit-btn"
            disabled={isLoading}
          >
            {isLoading ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Create Account'}
            {!isLoading && <ArrowRight size={16} />}
          </button>
        </form>

        <div className="auth-divider">
          <span>OR</span>
        </div>

        <button
          type="button"
          className="demo-account-btn"
          onClick={handleDemoLogin}
          disabled={isLoading}
        >
          <Sparkles size={16} />
          <span>Quick 1-Click Demo Login</span>
        </button>

        <div className="auth-footer-toggle">
          {mode === 'login' ? (
            <p>
              Don't have an account?{' '}
              <button
                type="button"
                className="toggle-mode-btn"
                onClick={() => {
                  setMode('register');
                  setLocalError('');
                }}
              >
                Sign up
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                className="toggle-mode-btn"
                onClick={() => {
                  setMode('login');
                  setLocalError('');
                }}
              >
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
