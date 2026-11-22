import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Search,
  LayoutDashboard,
  CheckSquare,
  Sparkles,
  Users,
  BarChart3,
  Plus,
  Download,
  HelpCircle,
  Folder,
  Briefcase,
  Brain,
  ShieldCheck,
  X,
  ArrowRight,
  Bot,
  Globe,
  TrendingUp,
  Code,
  DollarSign,
  ShieldAlert,
  Lock,
  Compass,
  Lightbulb,
  BookOpen,
} from 'lucide-react';
import { searchApi } from '../../services/searchApi';
import { userPrivacyApi } from '../../services/userPrivacyApi';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import './CommandPalette.css';

export function CommandPalette({
  isOpen,
  onClose,
  onNavigate,
  onNewTask,
  onOpenShortcuts,
}) {
  const { isAuthenticated } = useAuth();
  const { tasks, handleExportCSV } = useTasks();
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isSearching, setIsSearching] = useState(false);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Auto-focus input when palette opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setSearchResults([]);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Handle GDPR data download
  const handleDownloadGDPR = async () => {
    try {
      const data = await userPrivacyApi.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `focusboard_user_data_${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      onClose();
    } catch (err) {
      console.error('Failed to export GDPR data:', err);
      alert('Unable to export data. Please ensure you are logged in.');
    }
  };

  // Static Navigation Commands
  const navigationCommands = useMemo(() => [
    {
      id: 'nav-overview',
      category: 'Navigation',
      label: 'Go to Overview Dashboard',
      icon: LayoutDashboard,
      action: () => { onNavigate('overview'); onClose(); },
    },
    {
      id: 'nav-tasks',
      category: 'Navigation',
      label: 'Go to Tasks Management',
      icon: CheckSquare,
      action: () => { onNavigate('tasks'); onClose(); },
    },
    {
      id: 'nav-ai',
      category: 'Navigation',
      label: 'Open AI Productivity Assistant',
      icon: Sparkles,
      action: () => { onNavigate('ai'); onClose(); },
    },
    {
      id: 'nav-team',
      category: 'Navigation',
      label: 'Open Team Workspace & Projects',
      icon: Users,
      action: () => { onNavigate('team'); onClose(); },
    },
    {
      id: 'nav-calendar',
      category: 'Navigation',
      label: 'Open Calendar Schedule & Google Sync',
      icon: Folder,
      action: () => { onNavigate('calendar'); onClose(); },
    },
    {
      id: 'nav-integrations',
      category: 'Navigation',
      label: 'Open Integrations Hub & Automations',
      icon: Briefcase,
      action: () => { onNavigate('integrations'); onClose(); },
    },
    {
      id: 'nav-billing',
      category: 'Navigation',
      label: 'View Subscription Plans & Quota Limits',
      icon: Download,
      action: () => { onNavigate('billing'); onClose(); },
    },
    {
      id: 'nav-intelligence',
      category: 'Navigation',
      label: 'Open Product Intelligence & AI Insights',
      icon: Brain,
      action: () => { onNavigate('intelligence'); onClose(); },
    },
    {
      id: 'nav-enterprise',
      category: 'Navigation',
      label: 'Open Enterprise Governance & Security RBAC',
      icon: ShieldCheck,
      action: () => { onNavigate('enterprise'); onClose(); },
    },
    {
      id: 'nav-executive',
      category: 'Navigation',
      label: 'Open Executive Intelligence & Portfolio BI',
      icon: TrendingUp,
      action: () => { onNavigate('executive'); onClose(); },
    },
    {
      id: 'nav-developer',
      category: 'Navigation',
      label: 'Open Developer Platform, Public API & Webhooks',
      icon: Code,
      action: () => { onNavigate('developer'); onClose(); },
    },
    {
      id: 'nav-compliance',
      category: 'Navigation',
      label: 'Open Security Compliance, SOC 2 / ISO Controls & Risks',
      icon: ShieldAlert,
      action: () => { onNavigate('compliance'); onClose(); },
    },
    {
      id: 'nav-finance',
      category: 'Navigation',
      label: 'Open SaaS Financial Intelligence, MRR & FinOps',
      icon: DollarSign,
      action: () => { onNavigate('finance'); onClose(); },
    },
    {
      id: 'nav-strategy',
      category: 'Navigation',
      label: 'Open Strategic Intelligence & Market Decision Engine',
      icon: Compass,
      action: () => { onNavigate('strategy'); onClose(); },
    },
    {
      id: 'nav-innovation',
      category: 'Navigation',
      label: 'Open Innovation Lab & Feature Validation Pipeline',
      icon: Lightbulb,
      action: () => { onNavigate('innovation'); onClose(); },
    },
    {
      id: 'nav-knowledge',
      category: 'Navigation',
      label: 'Open Organizational Knowledge Intelligence & Graph Hub',
      icon: BookOpen,
      action: () => { onNavigate('knowledge'); onClose(); },
    },
    {
      id: 'nav-trust',
      category: 'Navigation',
      label: 'Open FocusBoard Public Trust Center',
      icon: Lock,
      action: () => { onNavigate('trust'); onClose(); },
    },
    {
      id: 'nav-analytics',
      category: 'Navigation',
      label: 'Open Productivity Analytics',
      icon: BarChart3,
      action: () => { onNavigate('analytics'); onClose(); },
    },
    {
      id: 'nav-support',
      category: 'Navigation',
      label: 'Open Customer Support, Knowledge Base & Roadmap',
      icon: HelpCircle,
      action: () => { onNavigate('support'); onClose(); },
    },
    {
      id: 'nav-agents',
      category: 'Navigation',
      label: 'Launch Autonomous AI Agents & Task Orchestration',
      icon: Bot,
      action: () => { onNavigate('agents'); onClose(); },
    },
    {
      id: 'nav-settings',
      category: 'Navigation',
      label: 'Open Regional Settings, Multi-Currency & Languages',
      icon: Globe,
      action: () => { onNavigate('settings'); onClose(); },
    },
  ], [onNavigate, onClose]);

  // Static Action Commands
  const actionCommands = useMemo(() => [
    {
      id: 'act-new-task',
      category: 'Actions',
      label: 'Create New Task',
      shortcut: 'N',
      icon: Plus,
      action: () => { onClose(); onNewTask(); },
    },
    {
      id: 'act-export-csv',
      category: 'Actions',
      label: 'Export Tasks as CSV',
      icon: Download,
      action: () => { handleExportCSV?.(); onClose(); },
    },
    ...(isAuthenticated ? [{
      id: 'act-gdpr-export',
      category: 'Actions',
      label: 'Export My Personal Data (GDPR JSON)',
      icon: Download,
      action: handleDownloadGDPR,
    }] : []),
    {
      id: 'act-shortcuts',
      category: 'Actions',
      label: 'View Keyboard Shortcuts',
      shortcut: '?',
      icon: HelpCircle,
      action: () => { onClose(); onOpenShortcuts(); },
    },
  ], [isAuthenticated, onClose, onNewTask, handleExportCSV, onOpenShortcuts]);

  // Debounced search query for backend / local search
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      if (isAuthenticated) {
        try {
          const res = await searchApi.search({ q: query, page_size: 8 });
          const items = (res?.results || []).map((r) => ({
            id: `search-${r.type}-${r.id}`,
            category: `Search Results (${r.type})`,
            label: r.title,
            sublabel: r.description || r.category || r.status,
            type: r.type,
            icon: r.type === 'WORKSPACE' ? Briefcase : r.type === 'PROJECT' ? Folder : CheckSquare,
            action: () => {
              if (r.type === 'TASK') onNavigate('overview');
              else if (r.type === 'WORKSPACE' || r.type === 'PROJECT') onNavigate('team');
              onClose();
            },
          }));
          setSearchResults(items);
        } catch (err) {
          console.warn('Backend search failed, fallback to local tasks:', err);
          fallbackLocalSearch();
        } finally {
          setIsSearching(false);
        }
      } else {
        fallbackLocalSearch();
        setIsSearching(false);
      }
    }, 200);

    const fallbackLocalSearch = () => {
      const q = query.toLowerCase();
      const localMatches = (tasks || [])
        .filter((t) => t.title.toLowerCase().includes(q) || (t.description && t.description.toLowerCase().includes(q)))
        .slice(0, 8)
        .map((t) => ({
          id: `local-task-${t.id}`,
          category: 'Tasks',
          label: t.title,
          sublabel: `${t.category} • ${t.status}`,
          type: 'TASK',
          icon: CheckSquare,
          action: () => { onNavigate('overview'); onClose(); },
        }));
      setSearchResults(localMatches);
    };

    return () => clearTimeout(timer);
  }, [query, isAuthenticated, tasks, onNavigate, onClose]);

  // Filter commands by query
  const filteredCommands = useMemo(() => {
    const q = query.toLowerCase().trim();
    if (!q) {
      return [...navigationCommands, ...actionCommands];
    }
    const filteredNav = navigationCommands.filter((c) => c.label.toLowerCase().includes(q));
    const filteredAct = actionCommands.filter((c) => c.label.toLowerCase().includes(q));
    return [...searchResults, ...filteredNav, ...filteredAct];
  }, [query, navigationCommands, actionCommands, searchResults]);

  // Keep selected index within bounds
  useEffect(() => {
    setSelectedIndex((prev) => Math.min(prev, Math.max(0, filteredCommands.length - 1)));
  }, [filteredCommands]);

  // Handle keyboard navigation within palette
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < filteredCommands.length - 1 ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filteredCommands.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = filteredCommands[selectedIndex];
      if (selected?.action) {
        selected.action();
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="cmd-palette-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="cmd-palette-dialog"
        role="dialog"
        aria-modal="true"
        aria-label="Command Palette"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Input Bar */}
        <div className="cmd-input-wrapper">
          <Search size={18} className="cmd-search-icon" />
          <input
            ref={inputRef}
            type="text"
            className="cmd-input"
            placeholder="Type a command or search tasks, projects..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-autocomplete="list"
            aria-expanded={filteredCommands.length > 0}
          />
          {query && (
            <button
              type="button"
              className="cmd-clear-btn"
              onClick={() => setQuery('')}
              aria-label="Clear query"
            >
              <X size={16} />
            </button>
          )}
          <span className="cmd-esc-badge" aria-hidden="true">ESC</span>
        </div>

        {/* Command / Search Results List */}
        <div className="cmd-results-list" ref={listRef} role="listbox">
          {filteredCommands.length === 0 ? (
            <div className="cmd-empty-state">
              <p>No matching commands or results found.</p>
            </div>
          ) : (
            filteredCommands.map((cmd, index) => {
              const Icon = cmd.icon || ArrowRight;
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={cmd.id}
                  role="option"
                  aria-selected={isSelected}
                  className={`cmd-item ${isSelected ? 'cmd-item-selected' : ''}`}
                  onClick={() => cmd.action && cmd.action()}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="cmd-item-left">
                    <span className="cmd-item-icon-box">
                      <Icon size={16} />
                    </span>
                    <div className="cmd-item-text">
                      <span className="cmd-item-label">{cmd.label}</span>
                      {cmd.sublabel && (
                        <span className="cmd-item-sublabel">{cmd.sublabel}</span>
                      )}
                    </div>
                  </div>
                  <div className="cmd-item-right">
                    {cmd.category && (
                      <span className="cmd-item-tag">{cmd.category}</span>
                    )}
                    {cmd.shortcut && (
                      <kbd className="cmd-shortcut-key">{cmd.shortcut}</kbd>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer shortcuts hint */}
        <div className="cmd-footer" aria-hidden="true">
          <span><kbd>↑</kbd> <kbd>↓</kbd> to navigate</span>
          <span><kbd>↵</kbd> to select</span>
          <span><kbd>esc</kbd> to close</span>
        </div>
      </div>
    </div>
  );
}
