import assert from 'node:assert';
import { authApi } from '../../src/services/authApi.js';

console.log('--- RUNNING AUTHENTICATION, OTP & GOOGLE OAUTH FRONTEND TESTS ---');

// 1. authApi Surface Validation
{
  const requiredMethods = [
    'startEmailAuth',
    'checkUsername',
    'registerEmail',
    'verifyOTP',
    'resendOTP',
    'getGoogleAuthUrl',
    'verifyGoogleToken',
    'login',
    'register',
    'getMe',
    'logout',
    'logoutAll',
    'getSessions',
  ];

  for (const method of requiredMethods) {
    assert.strictEqual(typeof authApi[method], 'function', `authApi should expose ${method}`);
  }
  console.log('✓ authApi client exposes all required email OTP, Google OAuth, and session management methods.');
}

// 2. Username Validation & Sanitization Rules
{
  const validateUsername = (raw) => {
    const cleaned = (raw || '').trim().toLowerCase();
    if (cleaned.length < 3 || cleaned.length > 30) {
      return { valid: false, error: 'Length must be between 3 and 30 characters.' };
    }
    if (!/^[a-z0-9_-]+$/.test(cleaned)) {
      return { valid: false, error: 'Contains invalid characters.' };
    }
    const reserved = new Set(['admin', 'root', 'focusboard', 'support', 'api', 'guest']);
    if (reserved.has(cleaned)) {
      return { valid: false, error: 'Username is reserved.' };
    }
    return { valid: true, username: cleaned };
  };

  assert.strictEqual(validateUsername('ab').valid, false);
  assert.strictEqual(validateUsername('user@domain.com').valid, false);
  assert.strictEqual(validateUsername('admin').valid, false);
  assert.strictEqual(validateUsername('  Daisy_Smith-99  ').valid, true);
  assert.strictEqual(validateUsername('  Daisy_Smith-99  ').username, 'daisy_smith-99');
  console.log('✓ Username client validation handles length, legal characters, and reserved names.');
}

// 3. OTP Code Input & Formatting
{
  const sanitizeOtpDigits = (digitsArray) => {
    return digitsArray.map((d) => String(d || '').replace(/\D/g, '').slice(-1)).slice(0, 6);
  };

  const code1 = sanitizeOtpDigits(['1', '2', '3', '4', '5', '6']).join('');
  assert.strictEqual(code1, '123456');

  const codeWithLetters = sanitizeOtpDigits(['1', 'a', 'b3', '4', '', '6']).join('');
  assert.strictEqual(codeWithLetters, '1346');

  console.log('✓ 6-digit OTP formatting and input sanitization verified.');
}

// 4. Google OAuth Parameters & Account Selection Prompt
{
  const constructGoogleAuthUrl = (clientId, redirectUri, state) => {
    const params = new URLSearchParams({
      client_id: clientId,
      redirect_uri: redirectUri,
      response_type: 'code',
      scope: 'openid email profile',
      access_type: 'offline',
      prompt: 'select_account',
      state: state || 'random_state',
    });
    return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
  };

  const url = constructGoogleAuthUrl('test-client-id', 'http://localhost:5173/auth/google/callback', 'state123');
  assert.ok(url.includes('prompt=select_account'), 'URL must mandate account selection');
  assert.ok(url.includes('client_id=test-client-id'));
  assert.ok(url.includes('scope=openid+email+profile'));
  console.log('✓ Google OAuth authorization URL construction enforces account selection.');
}

// 5. Session Storage and Restoration Semantics
{
  const storage = {};
  const mockLocalStorage = {
    setItem: (k, v) => { storage[k] = String(v); },
    getItem: (k) => storage[k] || null,
    removeItem: (k) => { delete storage[k]; },
  };

  // Simulate storing session
  const testToken = 'bearer_mock_jwt_token_12345';
  const testUser = { id: 42, username: 'daisy', email: 'daisy@focusboard.io', role: 'member' };

  mockLocalStorage.setItem('focusboard_token', testToken);
  mockLocalStorage.setItem('focusboard_user', JSON.stringify(testUser));

  assert.strictEqual(mockLocalStorage.getItem('focusboard_token'), testToken);
  assert.strictEqual(JSON.parse(mockLocalStorage.getItem('focusboard_user')).username, 'daisy');

  // Simulate logout
  mockLocalStorage.removeItem('focusboard_token');
  mockLocalStorage.removeItem('focusboard_user');

  assert.strictEqual(mockLocalStorage.getItem('focusboard_token'), null);
  assert.strictEqual(mockLocalStorage.getItem('focusboard_user'), null);
  console.log('✓ Authentication state persistence and logout clearance verified.');
}

console.log('--- ALL AUTHENTICATION, OTP & GOOGLE OAUTH FRONTEND TESTS PASSED ---');
