import React, { useState, useEffect } from 'react';
import {
  LayoutGrid,
  CheckSquare,
  Calendar,
  Sparkles,
  Layers,
  Wifi,
  WifiOff,
  CreditCard,
} from 'lucide-react';
import { syncEngine } from '../../services/offlineSyncEngine';
import './MobileBottomNav.css';

export function MobileBottomNav({ activeTab, onTabChange }) {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    return syncEngine.subscribe((onlineStatus) => {
      setIsOnline(onlineStatus);
    });
  }, []);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'tasks', label: 'Tasks', icon: CheckSquare },
    { id: 'calendar', label: 'Calendar', icon: Calendar },
    { id: 'ai', label: 'AI Planner', icon: Sparkles },
    { id: 'billing', label: 'Plans', icon: CreditCard },
  ];

  return (
    <>
      {/* Offline Status Warning Pill */}
      {!isOnline && (
        <div className="mobile-offline-banner" role="status" aria-live="polite">
          <WifiOff size={14} />
          <span>Working Offline — Changes will auto-sync when connected</span>
        </div>
      )}

      {/* Touch-Friendly Bottom Bar */}
      <nav className="mobile-bottom-nav" aria-label="Mobile Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              type="button"
              className={`mobile-nav-btn ${isActive ? 'mobile-nav-btn-active' : ''}`}
              onClick={() => onTabChange(item.id)}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon size={20} className="mobile-nav-icon" />
              <span className="mobile-nav-label">{item.label}</span>
            </button>
          );
        })}
      </nav>
    </>
  );
}
