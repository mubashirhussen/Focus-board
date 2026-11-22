import React, { useState } from 'react';
import {
  LayoutGrid,
  CheckSquare,
  Calendar,
  Settings,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { APP_CONFIG } from '../../app/appConfig';
import './Sidebar.css';

export function Sidebar({ activeTab = 'overview', onTabChange }) {
  const { stats, resetToSampleData } = useTasks();
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutGrid, count: null },
    { id: 'tasks', label: 'My Tasks', icon: CheckSquare, count: stats.total },
    { id: 'calendar', label: 'Calendar', icon: Calendar, count: null },
    { id: 'settings', label: 'Settings', icon: Settings, count: null },
  ];

  const handleReset = () => {
    if (window.confirm('Reset tasks back to initial demo data?')) {
      resetToSampleData();
    }
  };

  return (
    <>
      {/* Desktop & Tablet Sidebar */}
      <aside className="sidebar desktop-sidebar" aria-label="Main Navigation">
        {/* Brand Header */}
        <div className="sidebar-brand">
          <div className="brand-logo" aria-hidden="true">
            <span className="logo-dot dot-1" />
            <span className="logo-dot dot-2" />
            <span className="logo-dot dot-3" />
            <span className="logo-dot dot-4" />
          </div>
          <span className="brand-name">{APP_CONFIG.appName}</span>
        </div>

        {/* Navigation Section */}
        <div className="sidebar-section">
          <span className="sidebar-section-title">NAVIGATION</span>
          <nav className="sidebar-nav">
            <ul className="nav-list">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`nav-button ${isActive ? 'active' : ''}`}
                      onClick={() => onTabChange && onTabChange(item.id)}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className="nav-icon" size={18} aria-hidden="true" />
                      <span className="nav-label">{item.label}</span>
                      {item.count !== null && (
                        <span className="nav-badge" aria-label={`${item.count} tasks`}>
                          {item.count}
                        </span>
                      )}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>
        </div>

        {/* Sidebar Footer / Quick Reset */}
        <div className="sidebar-footer">
          <button
            type="button"
            className="sidebar-reset-btn"
            onClick={handleReset}
            title="Reset to sample data"
          >
            <RotateCcw size={14} aria-hidden="true" />
            <span>Reset Demo Data</span>
          </button>
        </div>
      </aside>

      {/* Mobile Bottom Navigation Bar (Matches Figma Mobile Spec) */}
      <nav className="mobile-bottom-nav" aria-label="Mobile Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`mobile-nav-btn ${isActive ? 'active' : ''}`}
              onClick={() => onTabChange && onTabChange(item.id)}
              aria-current={isActive ? 'page' : undefined}
              aria-label={item.label}
            >
              <div className="mobile-icon-wrapper">
                <Icon size={20} aria-hidden="true" />
                {item.count !== null && item.count > 0 && (
                  <span className="mobile-badge">{item.count}</span>
                )}
              </div>
              <span className="mobile-label">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}
