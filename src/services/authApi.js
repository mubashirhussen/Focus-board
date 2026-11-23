import { api } from './api.js';

export const authApi = {
  /**
   * Step 1: Start email passwordless auth.
   * Checks whether the email belongs to an existing user or a new user.
   */
  startEmailAuth: async (email) => {
    return api.post('/auth/email/start', { email });
  },

  /**
   * Live validation of username uniqueness, format, and reserved words.
   */
  checkUsername: async (username) => {
    return api.get(`/auth/username/check?username=${encodeURIComponent(username)}`);
  },

  /**
   * Step 2: Register user with Full Name, Username, and Email.
   * Sends 6-digit registration OTP to the provided email.
   */
  registerEmail: async (name, username, email, role = 'member') => {
    return api.post('/auth/email/register', { name, username, email, role });
  },

  /**
   * Step 3: Verifies 6-digit OTP code for either registration or login.
   * On success, returns authenticated user profile and JWT tokens.
   */
  verifyOTP: async (email, otp, verificationSessionId, purpose = 'login', deviceName = 'Web Browser') => {
    return api.post('/auth/email/verify-otp', {
      email,
      otp,
      verification_session_id: verificationSessionId,
      purpose,
      device_name: deviceName,
    });
  },

  /**
   * Resends a fresh OTP code subject to cooldown throttling.
   */
  resendOTP: async (email, verificationSessionId, purpose = 'login') => {
    return api.post('/auth/email/resend-otp', {
      email,
      verification_session_id: verificationSessionId,
      purpose,
    });
  },

  /**
   * Fetches Google OAuth authorization URL configured with prompt=select_account.
   */
  getGoogleAuthUrl: async (state = '') => {
    return api.get(`/auth/google/url${state ? `?state=${encodeURIComponent(state)}` : ''}`);
  },

  /**
   * Verifies Google token or Google account profile and signs the user in.
   */
  verifyGoogleToken: async (googlePayload) => {
    return api.post('/auth/google/verify', googlePayload);
  },

  /**
   * Legacy password login endpoint (retained for backward compatibility).
   */
  login: async (email, password, deviceName = 'Web Browser') => {
    return api.post('/auth/login', { email, password, device_name: deviceName });
  },

  /**
   * Legacy password registration endpoint.
   */
  register: async (name, email, password, role = 'Member') => {
    return api.post('/auth/register', { name, email, password, role });
  },

  /**
   * Retrieves profile data of currently authenticated user.
   */
  getMe: async () => {
    return api.get('/auth/me');
  },

  /**
   * Revokes current user session and clears authentication.
   */
  logout: async () => {
    try {
      return await api.post('/auth/logout');
    } catch {
      return { message: 'Logged out locally' };
    }
  },

  /**
   * Revokes all active sessions across all devices for the current user.
   */
  logoutAll: async () => {
    return api.post('/auth/logout-all');
  },

  /**
   * Lists active sessions for current user.
   */
  getSessions: async () => {
    return api.get('/auth/sessions');
  },
};
