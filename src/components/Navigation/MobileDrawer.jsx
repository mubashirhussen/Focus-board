import React, { useEffect } from 'react';
import {
  X,
  Search,
  CheckSquare,
  Sparkles,
  Bot,
  Users,
  Calendar,
  Workflow,
  Layers,
  Server,
  Database,
  Shield,
  Sliders,
  Brain,
  ShieldCheck,
  DollarSign,
  Compass,
  Lightbulb,
  BookOpen,
  Lock,
  TrendingUp,
  Code,
  BarChart2,
  CreditCard,
  HelpCircle,
  RotateCcw,
  MessageSquare,
  ShieldAlert,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import { APP_CONFIG } from '../../app/appConfig';
import './MobileDrawer.css';

const FEATURE_SECTIONS = [
  {
    title: 'Workspaces & Projects',
    items: [
      { id: 'tasks', label: 'My Tasks', icon: CheckSquare },
      { id: 'team', label: 'Team Space', icon: Users },
      { id: 'calendar', label: 'Calendar Schedule', icon: Calendar },
    ],
  },
  {
    title: 'AI & Automation',
    items: [
      { id: 'ai', label: 'AI Planner & Assistant', icon: Sparkles },
      { id: 'agents', label: 'Autonomous Agents', icon: Bot },
      { id: 'automation', label: 'Automation Hub', icon: Workflow },
    ],
  },
  {
    title: 'Intelligence & Analytics',
    items: [
      { id: 'analytics', label: 'Productivity Analytics', icon: BarChart2 },
      { id: 'data-intelligence', label: 'Data Intelligence & BI', icon: Database },
      { id: 'product-lifecycle', label: 'Product Lifecycle', icon: Sliders },
      { id: 'intelligence', label: 'Behavioral Insights', icon: Brain },
      { id: 'executive', label: 'Executive BI', icon: TrendingUp },
    ],
  },
  {
    title: 'Security & Governance',
    items: [
      { id: 'soc', label: 'Security SOC & Zero Trust', icon: Shield },
      { id: 'enterprise', label: 'Enterprise Governance', icon: ShieldCheck },
      { id: 'compliance', label: 'Compliance & GRC', icon: ShieldAlert },
      { id: 'trust', label: 'Trust Center', icon: Lock },
    ],
  },
  {
    title: 'Strategy & Finance',
    items: [
      { id: 'finance', label: 'Financial Intelligence', icon: DollarSign },
      { id: 'strategy', label: 'Strategy & Markets', icon: Compass },
      { id: 'innovation', label: 'Innovation Lab', icon: Lightbulb },
      { id: 'knowledge', label: 'Knowledge Graph Hub', icon: BookOpen },
    ],
  },
  {
    title: 'Platform & Ecosystem',
    items: [
      { id: 'operations', label: 'Platform Operations', icon: Server },
      { id: 'integrations', label: 'Integrations Ecosystem', icon: Layers },
      { id: 'developer', label: 'Developer Platform', icon: Code },
      { id: 'billing', label: 'Plans & Usage Limits', icon: CreditCard },
      { id: 'support', label: 'Support & Help', icon: HelpCircle },
    ],
  },
];

export function MobileDrawer({
  isOpen,
  onClose,
  activeTab,
  onTabChange,
  onOpenSearch,
  onOpenFeedback,
}) {
  const { user } = useAuth();
  const { stats, resetToSampleData } = useTasks();

  // Escape key handler
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    }
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleSelect = (tabId) => {
    onTabChange(tabId);
    onClose();
  };

  return (
    <div className="mobile-drawer-overlay" onClick={onClose} role="dialog" aria-modal="true" aria-label="Mobile Navigation Menu">
      <div className="mobile-drawer-container" onClick={(e) => e.stopPropagation()}>
        {/* Top Header */}
        <div className="mobile-drawer-header">
          <div className="drawer-brand">
            <div className="drawer-logo" aria-hidden="true">
              <span className="dot dot-1" />
              <span className="dot dot-2" />
              <span className="dot dot-3" />
              <span className="dot dot-4" />
            </div>
            <div className="drawer-brand-text">
              <span className="drawer-brand-title">{APP_CONFIG.appName}</span>
              <span className="drawer-brand-badge">Full Feature Suite</span>
            </div>
          </div>
          <button
            type="button"
            className="drawer-close-btn"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* User Card */}
        <div className="drawer-user-card">
          <div className="drawer-avatar">
            {user?.name ? user.name.slice(0, 2).toUpperCase() : 'FB'}
          </div>
          <div className="drawer-user-info">
            <span className="drawer-user-name">{user?.name || 'Workspace User'}</span>
            <span className="drawer-user-role">{user?.role || 'Enterprise Admin'}</span>
          </div>
        </div>

        {/* Quick Search Button */}
        <div className="drawer-search-wrap">
          <button
            type="button"
            className="drawer-search-btn"
            onClick={() => {
              onClose();
              onOpenSearch?.();
            }}
          >
            <Search size={16} />
            <span>Search features & commands...</span>
            <span className="drawer-search-badge">⌘K</span>
          </button>
        </div>

        {/* Scrollable Navigation List */}
        <div className="drawer-nav-scroll">
          {FEATURE_SECTIONS.map((sec) => (
            <div key={sec.title} className="drawer-section">
              <div className="drawer-section-heading">{sec.title}</div>
              <div className="drawer-section-items">
                {sec.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  const count = item.id === 'tasks' ? stats.total : null;

                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={`drawer-nav-item ${isActive ? 'active' : ''}`}
                      onClick={() => handleSelect(item.id)}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <div className="drawer-item-icon-wrap">
                        <Icon size={18} />
                      </div>
                      <span className="drawer-item-label">{item.label}</span>
                      {count !== null && (
                        <span className="drawer-item-badge">{count}</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Footer Actions */}
        <div className="drawer-footer">
          <button
            type="button"
            className="drawer-footer-btn"
            onClick={() => {
              onClose();
              onOpenFeedback?.();
            }}
          >
            <MessageSquare size={15} />
            <span>Send Feedback</span>
          </button>
          <button
            type="button"
            className="drawer-footer-btn"
            onClick={() => {
              if (window.confirm('Reset tasks back to initial demo data?')) {
                resetToSampleData();
                onClose();
              }
            }}
          >
            <RotateCcw size={15} />
            <span>Reset Demo Data</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default MobileDrawer;
