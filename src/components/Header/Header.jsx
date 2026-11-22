import React from 'react';
import { APP_CONFIG } from '../../app/appConfig';
import { UserProfileMenu } from '../auth/UserProfileMenu';
import { NotificationBell } from '../notifications/NotificationBell';
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

      {/* Header action controls */}
      <div className="header-actions">
        <NotificationBell />
        <UserProfileMenu />
      </div>
    </header>
  );
}
