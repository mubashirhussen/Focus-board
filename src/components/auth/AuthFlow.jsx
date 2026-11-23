import React, { useState, useEffect, useRef } from 'react';
import {
  Mail,
  User,
  AtSign,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  Check,
  X,
  Lock,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './AuthFlow.css';

export function AuthFlow({ onSuccess, onCancel, standalone = false }) {
  const {
    startEmailAuth,
    checkUsername,
    registerWithOTP,
    verifyOTP,
    resendOTP,
    loginWithGoogle,
    authError,
    setAuthError,
    isLoading,
  } = useAuth();

  // Steps: 'email' | 'register' | 'otp'
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [usernameStatus, setUsernameStatus] = useState(null); // { available: bool, message: string }
  const [isCheckingUsername, setIsCheckingUsername] = useState(false);

  // OTP state
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [verificationSessionId, setVerificationSessionId] = useState('');
  const [otpPurpose, setOtpPurpose] = useState('login'); // 'login' | 'registration'
  const [cooldown, setCooldown] = useState(0);
  const [expiresIn, setExpiresIn] = useState(300);
  const [localError, setLocalError] = useState('');
  const [successNotice, setSuccessNotice] = useState('');

  // Google account picker
  const [showGooglePicker, setShowGooglePicker] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const otpInputsRef = useRef([]);

  // Detected device Google accounts
  const detectedGoogleAccounts = [
    { name: 'Sheik Mubashir Hussen', email: 'mubashir.hussen@gmail.com', avatar: 'M' },
    { name: 'Daisy Smith', email: 'daisy.smith@gmail.com', avatar: 'D' },
  ];

  // Cooldown countdown timer
  useEffect(() => {
    let timer;
    if (cooldown > 0) {
      timer = setInterval(() => {
        setCooldown((prev) => Math.max(0, prev - 1));
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  // Expiration countdown timer
  useEffect(() => {
    let expTimer;
    if (step === 'otp' && expiresIn > 0) {
      expTimer = setInterval(() => {
        setExpiresIn((prev) => Math.max(0, prev - 1));
      }, 1000);
    }
    return () => clearInterval(expTimer);
  }, [step, expiresIn]);

  // Debounced live username availability checking
  useEffect(() => {
    if (step !== 'register' || !username.trim()) {
      setUsernameStatus(null);
      return;
    }

    const timer = setTimeout(async () => {
      setIsCheckingUsername(true);
      try {
        const result = await checkUsername(username.trim());
        setUsernameStatus(result);
      } catch {
        setUsernameStatus({ available: false, message: 'Could not verify username' });
      } finally {
        setIsCheckingUsername(false);
      }
    }, 350);

    return () => clearTimeout(timer);
  }, [username, step, checkUsername]);

  // Step 1: Handle Email Submit
  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setSuccessNotice('');

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setLocalError('Please enter a valid email address.');
      return;
    }

    try {
      const res = await startEmailAuth(cleanEmail);
      if (res.is_new_user) {
        // User does not exist -> proceed to registration step
        // Prepopulate username candidate from email prefix
        const defaultUsername = cleanEmail.split('@')[0].replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 20);
        setUsername(defaultUsername);
        setStep('register');
      } else {
        // Existing user -> OTP sent for login
        setVerificationSessionId(res.verification_session_id);
        setOtpPurpose('login');
        setCooldown(res.resend_after || 60);
        setExpiresIn(res.expires_in || 300);
        setSuccessNotice(`Verification code sent to ${cleanEmail}`);
        setStep('otp');
      }
    } catch (err) {
      setLocalError(err.message || 'Failed to start authentication.');
    }
  };

  // Step 2: Handle Registration Submit
  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');
    setSuccessNotice('');

    if (!name.trim() || name.trim().length < 2) {
      setLocalError('Please enter your full name (at least 2 characters).');
      return;
    }

    if (!username.trim() || username.trim().length < 3) {
      setLocalError('Username must be at least 3 characters.');
      return;
    }

    if (usernameStatus && !usernameStatus.available) {
      setLocalError(usernameStatus.message || 'Please choose an available username.');
      return;
    }

    try {
      const res = await registerWithOTP(name.trim(), username.trim().toLowerCase(), email.trim().toLowerCase());
      setVerificationSessionId(res.verification_session_id);
      setOtpPurpose('registration');
      setCooldown(res.resend_after || 60);
      setExpiresIn(res.expires_in || 300);
      setSuccessNotice(`Verification code sent to ${email}`);
      setStep('otp');
    } catch (err) {
      setLocalError(err.message || 'Failed to register. Please check your details.');
    }
  };

  // Step 3: Handle OTP Input Navigation
  const handleOtpChange = (index, value) => {
    const val = value.replace(/\D/g, ''); // Numeric only
    if (!val) {
      const newDigits = [...otpDigits];
      newDigits[index] = '';
      setOtpDigits(newDigits);
      return;
    }

    const digit = val.slice(-1);
    const newDigits = [...otpDigits];
    newDigits[index] = digit;
    setOtpDigits(newDigits);

    // Auto-advance to next box
    if (index < 5 && digit) {
      otpInputsRef.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpInputsRef.current[index - 1]?.focus();
    }
  };

  const handleOtpPaste = (e) => {
    e.preventDefault();
    const pasteData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasteData) return;

    const newDigits = [...otpDigits];
    for (let i = 0; i < pasteData.length; i++) {
      newDigits[i] = pasteData[i];
    }
    setOtpDigits(newDigits);

    const focusIdx = Math.min(pasteData.length, 5);
    otpInputsRef.current[focusIdx]?.focus();
  };

  // Submit OTP Verification
  const handleVerifyOtp = async (e) => {
    if (e) e.preventDefault();
    setLocalError('');
    setSuccessNotice('');

    const fullCode = otpDigits.join('');
    if (fullCode.length !== 6) {
      setLocalError('Please enter all 6 digits of the verification code.');
      return;
    }

    try {
      await verifyOTP(email.trim().toLowerCase(), fullCode, verificationSessionId, otpPurpose);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message || 'Verification failed. Please try again.');
    }
  };

  // Resend OTP
  const handleResend = async () => {
    if (cooldown > 0) return;
    setLocalError('');
    setSuccessNotice('');

    try {
      const res = await resendOTP(email.trim().toLowerCase(), verificationSessionId, otpPurpose);
      setCooldown(res.resend_after || 60);
      setExpiresIn(res.expires_in || 300);
      setSuccessNotice('A new verification code has been dispatched to your email.');
    } catch (err) {
      setLocalError(err.message || 'Failed to resend code.');
    }
  };

  // Google Sign-In
  const handleGoogleSelect = async (account) => {
    setGoogleLoading(true);
    setLocalError('');
    try {
      await loginWithGoogle(account);
      setShowGooglePicker(false);
      onSuccess?.();
    } catch (err) {
      setLocalError(err.message || 'Google sign-in failed.');
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className={`auth-flow-card ${standalone ? 'standalone' : ''}`}>
      {/* Brand Header */}
      <div className="auth-brand-header">
        <div className="auth-brand-logo">
          <span className="brand-dot dot-1" />
          <span className="brand-dot dot-2" />
          <span className="brand-dot dot-3" />
          <span className="brand-dot dot-4" />
        </div>
        <div className="auth-brand-info">
          <span className="auth-brand-title">FocusBoard</span>
          <span className="auth-brand-badge">Enterprise Auth</span>
        </div>
      </div>

      {/* Main Title & Subtitle */}
      <div className="auth-text-header">
        {step === 'email' && (
          <>
            <h1 className="auth-heading">Welcome to FocusBoard</h1>
            <p className="auth-subheading">Manage your projects, tasks and goals in one place.</p>
          </>
        )}
        {step === 'register' && (
          <>
            <h1 className="auth-heading">Create your account</h1>
            <p className="auth-subheading">Enter your name and choose a unique username.</p>
          </>
        )}
        {step === 'otp' && (
          <>
            <h1 className="auth-heading">Verify your email</h1>
            <p className="auth-subheading">
              We sent a 6-digit verification code to <strong>{email}</strong>
            </p>
          </>
        )}
      </div>

      {/* Alerts */}
      {(localError || authError) && (
        <div className="auth-alert error" role="alert">
          <AlertCircle size={16} className="alert-icon" />
          <span>{localError || authError}</span>
        </div>
      )}

      {successNotice && (
        <div className="auth-alert success" role="status">
          <CheckCircle2 size={16} className="alert-icon" />
          <span>{successNotice}</span>
        </div>
      )}

      {/* STEP 1: EMAIL ENTRY */}
      {step === 'email' && (
        <form onSubmit={handleEmailSubmit} className="auth-form" noValidate>
          <div className="form-group floating-form-group">
            <div className={`floating-input-wrap ${email ? 'has-value' : ''}`}>
              <Mail size={16} className="field-icon" />
              <input
                id="auth-email-input"
                type="email"
                className="auth-input floating-input"
                placeholder=" "
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                autoFocus
                required
              />
              <label htmlFor="auth-email-input" className="floating-placeholder-label">
                me@company.com
              </label>
            </div>
          </div>

          <button
            type="submit"
            className="btn-auth-primary"
            disabled={isLoading || !email.trim()}
          >
            {isLoading ? (
              <span className="btn-spinner-wrap">
                <RefreshCw size={16} className="spin-icon" /> Checking email...
              </span>
            ) : (
              <>
                <span>Continue</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>

          {/* Divider */}
          <div className="auth-divider">
            <span>OR</span>
          </div>

          {/* Google Sign In */}
          {!showGooglePicker ? (
            <button
              type="button"
              className="btn-auth-google"
              onClick={() => setShowGooglePicker(true)}
              disabled={isLoading || googleLoading}
            >
              <svg className="google-svg" viewBox="0 0 24 24" width="18" height="18">
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
            <div className="google-picker-modal">
              <div className="picker-top">
                <span className="picker-title">Select a Google Account</span>
                <button
                  type="button"
                  className="picker-cancel-btn"
                  onClick={() => setShowGooglePicker(false)}
                >
                  Cancel
                </button>
              </div>
              <div className="picker-list">
                {detectedGoogleAccounts.map((acc) => (
                  <button
                    key={acc.email}
                    type="button"
                    className="picker-account-card"
                    onClick={() => handleGoogleSelect(acc)}
                    disabled={googleLoading}
                  >
                    <div className="picker-avatar">{acc.avatar}</div>
                    <div className="picker-details">
                      <span className="picker-name">{acc.name}</span>
                      <span className="picker-email">{acc.email}</span>
                    </div>
                  </button>
                ))}
                <button
                  type="button"
                  className="picker-account-card custom"
                  onClick={() =>
                    handleGoogleSelect({
                      name: 'Google User',
                      email: 'google.account@gmail.com',
                      avatar: 'G',
                    })
                  }
                  disabled={googleLoading}
                >
                  <div className="picker-avatar plus">+</div>
                  <div className="picker-details">
                    <span className="picker-name">Use another Google account</span>
                  </div>
                </button>
              </div>
            </div>
          )}
        </form>
      )}

      {/* STEP 2: NEW USER REGISTRATION */}
      {step === 'register' && (
        <form onSubmit={handleRegisterSubmit} className="auth-form" noValidate>
          <div className="form-group floating-form-group">
            <div className={`floating-input-wrap ${name ? 'has-value' : ''}`}>
              <User size={16} className="field-icon" />
              <input
                id="reg-name-input"
                type="text"
                className="auth-input floating-input"
                placeholder=" "
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoComplete="name"
                autoFocus
                required
              />
              <label htmlFor="reg-name-input" className="floating-placeholder-label">
                e.g. Sheik Mubashir
              </label>
            </div>
          </div>

          <div className="form-group floating-form-group">
            <div className="label-with-status">
              <span className="field-top-meta">Choose unique username</span>
              {isCheckingUsername && <span className="status-note">Checking...</span>}
              {!isCheckingUsername && usernameStatus && (
                <span className={`status-note ${usernameStatus.available ? 'valid' : 'invalid'}`}>
                  {usernameStatus.available ? (
                    <>
                      <Check size={12} /> Available
                    </>
                  ) : (
                    <>
                      <X size={12} /> Taken
                    </>
                  )}
                </span>
              )}
            </div>
            <div className={`floating-input-wrap ${username ? 'has-value' : ''}`}>
              <AtSign size={16} className="field-icon" />
              <input
                id="reg-username-input"
                type="text"
                className={`auth-input floating-input ${usernameStatus && !usernameStatus.available ? 'input-error' : ''}`}
                placeholder=" "
                value={username}
                onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/\s+/g, ''))}
                autoComplete="username"
                required
              />
              <label htmlFor="reg-username-input" className="floating-placeholder-label">
                username
              </label>
            </div>
            <span className="field-hint">Letters, numbers, underscores and hyphens (3-30 chars).</span>
          </div>

          <div className="form-group">
            <label htmlFor="reg-email-display" className="form-label">
              Email address
            </label>
            <div className="input-field-wrap read-only">
              <Mail size={16} className="field-icon" />
              <input
                id="reg-email-display"
                type="email"
                className="auth-input disabled"
                value={email}
                disabled
              />
            </div>
          </div>

          <div className="btn-actions-row">
            <button
              type="button"
              className="btn-auth-secondary"
              onClick={() => {
                setStep('email');
                setLocalError('');
              }}
            >
              <ArrowLeft size={16} />
              <span>Back</span>
            </button>
            <button
              type="submit"
              className="btn-auth-primary flex-1"
              disabled={isLoading || !name.trim() || !username.trim() || (usernameStatus && !usernameStatus.available)}
            >
              {isLoading ? (
                <span className="btn-spinner-wrap">
                  <RefreshCw size={16} className="spin-icon" /> Sending OTP...
                </span>
              ) : (
                <>
                  <span>Send Verification Code</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </form>
      )}

      {/* STEP 3: OTP VERIFICATION */}
      {step === 'otp' && (
        <form onSubmit={handleVerifyOtp} className="auth-form" noValidate>
          <div className="otp-container">
            <label className="form-label text-center">
              Enter 6-digit verification code
            </label>
            <div className="otp-boxes-grid" onPaste={handleOtpPaste}>
              {otpDigits.map((digit, idx) => (
                <input
                  key={idx}
                  ref={(el) => (otpInputsRef.current[idx] = el)}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={1}
                  className={`otp-digit-box ${digit ? 'filled' : ''}`}
                  value={digit}
                  onChange={(e) => handleOtpChange(idx, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                  autoFocus={idx === 0}
                  aria-label={`Digit ${idx + 1}`}
                />
              ))}
            </div>

            <div className="otp-expiry-indicator">
              <span>Code expires in: </span>
              <strong>
                {Math.floor(expiresIn / 60)}:{(expiresIn % 60).toString().padStart(2, '0')}
              </strong>
            </div>
          </div>

          <button
            type="submit"
            className="btn-auth-primary"
            disabled={isLoading || otpDigits.join('').length !== 6}
          >
            {isLoading ? (
              <span className="btn-spinner-wrap">
                <RefreshCw size={16} className="spin-icon" /> Verifying...
              </span>
            ) : (
              <>
                <span>Verify Email & Sign In</span>
                <ShieldCheck size={16} />
              </>
            )}
          </button>

          {/* Resend & Change Email Footer */}
          <div className="otp-footer-controls">
            <span className="otp-footer-text">Didn't receive the code?</span>
            <div className="otp-footer-links">
              <button
                type="button"
                className={`btn-link-action ${cooldown > 0 ? 'disabled' : ''}`}
                onClick={handleResend}
                disabled={cooldown > 0 || isLoading}
              >
                {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend code'}
              </button>
              <span className="footer-dot">&bull;</span>
              <button
                type="button"
                className="btn-link-action"
                onClick={() => {
                  setStep('email');
                  setOtpDigits(['', '', '', '', '', '']);
                  setLocalError('');
                  setSuccessNotice('');
                }}
              >
                Change email
              </button>
            </div>
          </div>
        </form>
      )}

      {/* Security Trust Footer */}
      <div className="auth-security-footer">
        <Lock size={12} className="lock-icon" />
        <span>End-to-end encrypted passwordless authentication</span>
      </div>
    </div>
  );
}
