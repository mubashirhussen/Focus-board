import React from 'react';
import { Search } from 'lucide-react';
import { APP_CONFIG } from '../../app/appConfig';
import { UserProfileMenu } from '../auth/UserProfileMenu';
import { NotificationBell } from '../notifications/NotificationBell';
import './Header.css';

export function Header({ title = 'Task Management', onOpenCommandPalette }) {
  const isMac = typeof navigator !== 'undefined' && navigator.platform?.toUpperCase().indexOf('MAC') >= 0;
  const shortcutLabel = isMac ? '⌘K' : 'Ctrl+K';

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
        {/* Command Palette Quick Trigger */}
        <button
          type="button"
          className="header-cmd-trigger"
          onClick={onOpenCommandPalette}
          aria-label={`Open Command Palette (${shortcutLabel})`}
        >
          <Search size={14} className="cmd-trigger-icon" />
          <span className="cmd-trigger-text">Search & commands...</span>
          <kbd className="cmd-trigger-badge">{shortcutLabel}</kbd>
        </button>

        <NotificationBell />
        <UserProfileMenu />
      </div>
    </header>
  );
}
