import React, { useState, useRef, useEffect } from 'react';
import { User, LogIn, LogOut, ShieldCheck, Database, ChevronDown, Users, RefreshCw } from 'lucide-react';
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

  // When not logged in: show modern Sign In button instead of guest profile
  if (!isAuthenticated || !user || user.isGuest) {
    return (
      <button
        type="button"
        className="btn-header-signin"
        onClick={openAuthModal}
        aria-label="Sign in to your account"
      >
        <LogIn size={15} />
        <span>Sign In</span>
      </button>
    );
  }

  const getInitials = (name) => {
    if (!name) return 'JD';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const displayName = user.name || user.display_name || user.email?.split('@')[0] || 'User';
  const displayUsername = user.username
    ? `@${user.username}`
    : user.email
    ? `@${user.email.split('@')[0]}`
    : '@user';
  const displayEmail = user.email || 'user@focusboard.io';
  const displayRole = user.role || 'Member';

  return (
    <div className="user-profile-menu-container" ref={menuRef}>
      <button
        type="button"
        className="user-avatar-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="User profile and account options"
        aria-expanded={isOpen}
      >
        <span className="user-initials">{getInitials(displayName)}</span>
        <span className="online-indicator" title="Connected to Cloud Sync" />
        <ChevronDown size={13} className={`avatar-chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div className="user-dropdown-card" role="menu">
          {/* User Details Header */}
          <div className="user-dropdown-header">
            <div className="user-dropdown-avatar" aria-hidden="true">
              <span>{getInitials(displayName)}</span>
            </div>
            <div className="user-dropdown-info">
              <span className="user-dropdown-name">{displayName}</span>
              <span className="user-dropdown-username">{displayUsername}</span>
              <span className="user-dropdown-email">{displayEmail}</span>
            </div>
          </div>

          {/* Role Status */}
          <div className="user-dropdown-status">
            <div className="status-badge cloud">
              <ShieldCheck size={15} className="status-badge-icon" />
              <div className="status-badge-text">
                <span className="status-badge-sub">ROLE: {displayRole.toUpperCase()}</span>
                <span className="status-badge-title">Cloud Account Active</span>
              </div>
            </div>
          </div>

          {/* Action Buttons: Sign Out, Switch Account */}
          <div className="user-dropdown-actions">
            <button
              type="button"
              className="dropdown-action-btn switch-account"
              onClick={() => {
                openAuthModal();
                setIsOpen(false);
              }}
            >
              <RefreshCw size={14} />
              <span>Switch Account</span>
            </button>

            <button
              type="button"
              className="dropdown-action-btn sign-out"
              onClick={() => {
                logout();
                setIsOpen(false);
              }}
            >
              <LogOut size={14} />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default UserProfileMenu;
