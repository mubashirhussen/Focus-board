import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/authApi';
import { APP_CONFIG } from '../app/appConfig';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('focusboard_token') || null);
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('focusboard_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [isLoading, setIsLoading] = useState(false);
  const [authError, setAuthError] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Validate active session on mount
  useEffect(() => {
    if (token) {
      authApi.getMe()
        .then((userData) => {
          setUser(userData);
          localStorage.setItem('focusboard_user', JSON.stringify(userData));
        })
        .catch(() => {
          // Token expired or invalid
          console.warn('Session verification failed. Reverting to guest session.');
          logout();
        });
    }
  }, [token]);

  const login = useCallback(async (email, password) => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await authApi.login(email, password);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('focusboard_token', data.access_token);
      localStorage.setItem('focusboard_user', JSON.stringify(data.user));
      setIsAuthModalOpen(false);
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Login failed. Please check your credentials.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (name, email, password, role = 'Member') => {
    setIsLoading(true);
    setAuthError(null);
    try {
      const data = await authApi.register(name, email, password, role);
      setToken(data.access_token);
      setUser(data.user);
      localStorage.setItem('focusboard_token', data.access_token);
      localStorage.setItem('focusboard_user', JSON.stringify(data.user));
      setIsAuthModalOpen(false);
      return data.user;
    } catch (err) {
      setAuthError(err.message || 'Registration failed.');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('focusboard_token');
    localStorage.removeItem('focusboard_user');
  }, []);

  const openAuthModal = useCallback(() => setIsAuthModalOpen(true), []);
  const closeAuthModal = useCallback(() => {
    setIsAuthModalOpen(false);
    setAuthError(null);
  }, []);

  // Display user (either authenticated user or default demo profile)
  const currentUser = user || {
    name: APP_CONFIG.user.name,
    email: 'guest@focusboard.io',
    role: APP_CONFIG.user.role,
    initials: APP_CONFIG.user.initials,
    isGuest: true,
  };

  const value = {
    user: currentUser,
    isAuthenticated: !!token && !currentUser.isGuest,
    token,
    isLoading,
    authError,
    login,
    register,
    logout,
    isAuthModalOpen,
    openAuthModal,
    closeAuthModal,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
