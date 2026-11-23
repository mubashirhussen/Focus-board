import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  FolderKanban,
  Plus,
  BarChart2,
  Menu,
  WifiOff,
} from 'lucide-react';
import { syncEngine } from '../../services/offlineSyncEngine';
import './MobileBottomNav.css';

export function MobileBottomNav({
  activeTab,
  onTabChange,
  onOpenMobileDrawer,
  onNewTask,
}) {
  const [isOnline, setIsOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);

  useEffect(() => {
    return syncEngine.subscribe((onlineStatus) => {
      setIsOnline(onlineStatus);
    });
  }, []);

  return (
    <>
      {/* Offline Status Warning Pill */}
      {!isOnline && (
        <div className="mobile-offline-banner" role="status" aria-live="polite">
          <WifiOff size={14} />
          <span>Working Offline — Changes will auto-sync when connected</span>
        </div>
      )}

      {/* Touch-Friendly Bottom Bar Matching Reference Design */}
      <nav className="mobile-bottom-nav" aria-label="Mobile Navigation">
        {/* Tab 1: Dashboard */}
        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === 'tasks' ? 'mobile-nav-btn-active' : ''}`}
          onClick={() => onTabChange('tasks')}
          aria-current={activeTab === 'tasks' ? 'page' : undefined}
        >
          <LayoutDashboard size={20} className="mobile-nav-icon" />
          <span className="mobile-nav-label">Dashboard</span>
        </button>

        {/* Tab 2: Projects / Team */}
        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === 'team' ? 'mobile-nav-btn-active' : ''}`}
          onClick={() => onTabChange('team')}
          aria-current={activeTab === 'team' ? 'page' : undefined}
        >
          <FolderKanban size={20} className="mobile-nav-icon" />
          <span className="mobile-nav-label">Projects</span>
        </button>

        {/* Tab 3: Central Primary Action (+) */}
        <div className="mobile-nav-fab-wrap">
          <button
            type="button"
            className="mobile-nav-fab-btn"
            onClick={onNewTask}
            aria-label="Create New Task"
            title="Create New Task"
          >
            <Plus size={24} />
          </button>
        </div>

        {/* Tab 4: Analytics */}
        <button
          type="button"
          className={`mobile-nav-btn ${activeTab === 'analytics' ? 'mobile-nav-btn-active' : ''}`}
          onClick={() => onTabChange('analytics')}
          aria-current={activeTab === 'analytics' ? 'page' : undefined}
        >
          <BarChart2 size={20} className="mobile-nav-icon" />
          <span className="mobile-nav-label">Analytics</span>
        </button>

        {/* Tab 5: All Features Drawer Menu */}
        <button
          type="button"
          className="mobile-nav-btn"
          onClick={onOpenMobileDrawer}
          aria-label="Open Full Features Menu"
        >
          <Menu size={20} className="mobile-nav-icon" />
          <span className="mobile-nav-label">Menu</span>
        </button>
      </nav>
    </>
  );
}

export default MobileBottomNav;
