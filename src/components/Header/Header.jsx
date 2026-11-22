import React from 'react';
import { APP_CONFIG } from '../../app/appConfig';
import './Header.css';

export function Header({ title = 'Overview' }) {
  return (
    <header className="app-header" role="banner">
      {/* Desktop breadcrumb */}
      <div className="header-context">
        <span className="context-breadcrumb">Application</span>
        <span className="context-separator" aria-hidden="true">/</span>
        <span className="context-current">{title}</span>
      </div>

      {/* Mobile brand header (shown on small screens) */}
      <div className="header-mobile-brand">
        <div className="brand-logo-small" aria-hidden="true">
          <span className="logo-dot dot-1" />
          <span className="logo-dot dot-2" />
          <span className="logo-dot dot-3" />
          <span className="logo-dot dot-4" />
        </div>
        <span className="brand-title">{APP_CONFIG.appName}</span>
      </div>

      {/* User profile avatar */}
      <div className="header-actions">
        <button
          type="button"
          className="user-avatar-btn"
          title={`${APP_CONFIG.user.name} (${APP_CONFIG.user.role})`}
          aria-label={`User profile for ${APP_CONFIG.user.name}`}
        >
          <span className="user-initials">{APP_CONFIG.user.initials}</span>
        </button>
      </div>
    </header>
  );
}
