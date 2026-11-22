import React, { useState, useRef, useEffect } from 'react';
import { User, LogIn, LogOut, ShieldCheck, Database } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './UserProfileMenu.css';

export function UserProfileMenu() {
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getInitials = (name) => {
    if (!name) return 'FB';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className="user-profile-menu-container" ref={menuRef}>
      <button
        type="button"
        className="user-avatar-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User profile and account options"
        aria-expanded={isOpen}
      >
        <span className="user-initials">{getInitials(user?.name)}</span>
        {isAuthenticated && <span className="online-indicator" title="Connected to Cloud Sync" />}
      </button>

      {isOpen && (
        <div className="user-dropdown-card">
          <div className="user-dropdown-header">
            <div className="user-dropdown-avatar">
              <span>{getInitials(user?.name)}</span>
            </div>
            <div className="user-dropdown-info">
              <span className="user-dropdown-name">{user?.name}</span>
              <span className="user-dropdown-email">{user?.email}</span>
            </div>
          </div>

          <div className="user-dropdown-status">
            {isAuthenticated ? (
              <div className="status-badge cloud">
                <ShieldCheck size={14} />
                <span>Cloud Multi-User Active</span>
              </div>
            ) : (
              <div className="status-badge local">
                <Database size={14} />
                <span>Local Storage Mode</span>
              </div>
            )}
          </div>

          <div className="user-dropdown-actions">
            {isAuthenticated ? (
              <button
                type="button"
                className="dropdown-action-btn logout"
                onClick={() => {
                  logout();
                  setIsOpen(false);
                }}
              >
                <LogOut size={16} />
                <span>Sign Out</span>
              </button>
            ) : (
              <button
                type="button"
                className="dropdown-action-btn login"
                onClick={() => {
                  openAuthModal();
                  setIsOpen(false);
                }}
              >
                <LogIn size={16} />
                <span>Sign In / Create Account</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
