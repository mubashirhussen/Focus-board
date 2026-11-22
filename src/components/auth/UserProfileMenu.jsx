import React, { useState, useRef, useEffect } from 'react';
import { User, LogIn, LogOut, ShieldCheck, Database, ChevronDown } from 'lucide-react';
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
    if (!name) return 'JD';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const displayName = user?.name || 'John Doe';
  const displayEmail = user?.email || (isAuthenticated ? 'user@focusboard.io' : 'guest@focusboard.io');

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
        {isAuthenticated && <span className="online-indicator" title="Connected to Cloud Sync" />}
        <ChevronDown size={13} className={`avatar-chevron ${isOpen ? 'open' : ''}`} />
      </button>

      {isOpen && (
        <div className="user-dropdown-card" role="menu">
          {/* User Details Header with Absolute Alignment */}
          <div className="user-dropdown-header">
            <div className="user-dropdown-avatar" aria-hidden="true">
              <span>{getInitials(displayName)}</span>
            </div>
            <div className="user-dropdown-info">
              <span className="user-dropdown-name" title={displayName}>{displayName}</span>
              <span className="user-dropdown-email" title={displayEmail}>{displayEmail}</span>
            </div>
          </div>

          {/* Storage & Environment Status Badge */}
          <div className="user-dropdown-status">
            {isAuthenticated ? (
              <div className="status-badge cloud">
                <ShieldCheck size={14} className="status-badge-icon" />
                <div className="status-badge-text">
                  <span className="status-badge-sub">ENVIRONMENT</span>
                  <span className="status-badge-title">Cloud Multi-User Active</span>
                </div>
              </div>
            ) : (
              <div className="status-badge local">
                <Database size={14} className="status-badge-icon" />
                <div className="status-badge-text">
                  <span className="status-badge-sub">ENVIRONMENT</span>
                  <span className="status-badge-title">Local Storage Mode</span>
                </div>
              </div>
            )}
          </div>

          {/* Action Button with Clean Centering and Icon Spacing */}
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
                <LogOut size={15} className="dropdown-action-icon" />
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
                <LogIn size={15} className="dropdown-action-icon" />
                <span>Sign In / Create Account</span>
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
export default UserProfileMenu;
