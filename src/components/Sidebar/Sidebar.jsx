import React, { useState } from 'react';
import {
  LayoutGrid,
  CheckSquare,
  Sparkles,
  Users,
  BarChart2,
  Calendar,
  Layers,
  CreditCard,
  Brain,
  ShieldCheck,
  Settings,
  RotateCcw,
  HelpCircle,
  MessageSquare,
  Bot,
  Globe,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { useI18n } from '../../i18n/I18nContext';
import { APP_CONFIG } from '../../app/appConfig';
import './Sidebar.css';

export function Sidebar({ activeTab = 'overview', onTabChange, onOpenFeedback }) {
  const { stats, resetToSampleData } = useTasks();
  const { t } = useI18n();

  const navItems = [
    { id: 'overview', label: t('nav.overview', 'Overview'), icon: LayoutGrid, count: null },
    { id: 'tasks', label: t('nav.tasks', 'My Tasks'), icon: CheckSquare, count: stats.total },
    { id: 'ai', label: t('nav.ai', 'AI Planner'), icon: Sparkles, count: null },
    { id: 'agents', label: t('nav.agents', 'AI Agents'), icon: Bot, count: null },
    { id: 'team', label: t('nav.team', 'Team Space'), icon: Users, count: null },
    { id: 'calendar', label: t('nav.calendar', 'Calendar'), icon: Calendar, count: null },
    { id: 'integrations', label: t('nav.integrations', 'Integrations'), icon: Layers, count: null },
    { id: 'billing', label: t('nav.billing', 'Plans & Billing'), icon: CreditCard, count: null },
    { id: 'intelligence', label: t('nav.intelligence', 'Intelligence'), icon: Brain, count: null },
    { id: 'enterprise', label: t('nav.enterprise', 'Enterprise Admin'), icon: ShieldCheck, count: null },
    { id: 'analytics', label: t('nav.analytics', 'Analytics'), icon: BarChart2, count: null },
    { id: 'support', label: t('nav.support', 'Support & Help'), icon: HelpCircle, count: null },
    { id: 'settings', label: t('nav.settings', 'Regional Settings'), icon: Globe, count: null },
  ];

  const handleReset = () => {
    if (window.confirm('Reset tasks back to initial demo data?')) {
      resetToSampleData();
    }
  };

  return (
    <>
      {/* Desktop & Tablet Navigation Sidebar */}
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

        {/* Sidebar Footer / Quick Reset & Feedback */}
        <div className="sidebar-footer">
          {onOpenFeedback && (
            <button
              type="button"
              className="sidebar-reset-btn"
              onClick={onOpenFeedback}
              title="Share feedback"
              style={{ marginBottom: '0.375rem' }}
            >
              <MessageSquare size={14} aria-hidden="true" />
              <span>Feedback</span>
            </button>
          )}
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

      {/* Mobile Bottom Navigation Bar (Matches Figma Mobile Spec 390px) */}
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
              {isActive && <span className="mobile-active-indicator" aria-hidden="true" />}
            </button>
          );
        })}
      </nav>
    </>
  );
}
