import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  Trash2,
  Clock,
  AlertTriangle,
  Sparkles,
  RefreshCw,
  X,
  FolderKanban,
  ShieldCheck,
  ShieldAlert,
  Workflow,
  Users,
  MessageSquare,
  Inbox,
  AlertCircle,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import { notificationApi } from '../../services/notificationApi';
import './NotificationBell.css';

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'Just now';
  try {
    const date = new Date(dateStr);
    const diffMs = Date.now() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSec < 45) return 'Just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
}

export function NotificationBell({ onNavigate }) {
  const { isAuthenticated, user } = useAuth();
  const { tasks } = useTasks();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside or Escape
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    function handleKeyDown(event) {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const fetchNotifications = async () => {
    if (!isAuthenticated || !user || user.isGuest) {
      setNotifications([]);
      setUnreadCount(0);
      return;
    }

    setError(null);
    try {
      setLoading(true);
      const [notifData, countData] = await Promise.all([
        notificationApi.getNotifications(),
        notificationApi.getUnreadCount(),
      ]);
      const list = Array.isArray(notifData) ? notifData : notifData?.items || [];
      setNotifications(list);
      setUnreadCount(countData?.unread_count ?? list.filter((n) => !n.is_read && !n.read_at).length);
    } catch (err) {
      console.warn('Failed to load notifications from API:', err);
      setError('Could not connect to notification service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated && user && !user.isGuest) {
      fetchNotifications();
    } else {
      setNotifications([]);
      setUnreadCount(0);
    }
  }, [isAuthenticated, user]);

  // NEVER appear if user has not logged in
  if (!isAuthenticated || !user || user.isGuest) {
    return null;
  }

  const handleDelete = async (notifId, e) => {
    if (e) e.stopPropagation();
    const target = notifications.find((n) => n.id === notifId);
    const wasUnread = target && !target.is_read && !target.read_at;

    setNotifications((prev) => prev.filter((n) => n.id !== notifId));
    if (wasUnread) {
      setUnreadCount((c) => Math.max(0, c - 1));
    }

    if (typeof notifId === 'number') {
      try {
        await notificationApi.deleteNotification(notifId);
      } catch (err) {
        console.error('Failed to delete notification:', err);
      }
    }
  };

  const handleNotificationClick = (n) => {
    const target = n.target_tab || (n.category === 'Security' ? 'soc' : n.category === 'Governance' ? 'enterprise' : 'tasks');
    if (onNavigate) {
      onNavigate(target);
    }
    setIsOpen(false);
  };

  const getCategoryMeta = (notif) => {
    const type = notif.type || notif.notification_type || '';
    const cat = notif.category || '';

    if (type.includes('OVERDUE') || cat.toLowerCase() === 'overdue') {
      return { label: 'Overdue', color: 'danger', icon: AlertTriangle };
    }
    if (type.includes('TASK') || cat.toLowerCase() === 'tasks') {
      return { label: 'Tasks', color: 'primary', icon: Clock };
    }
    if (type.includes('PROJECT') || cat.toLowerCase() === 'projects') {
      return { label: 'Projects', color: 'info', icon: FolderKanban };
    }
    if (type.includes('SECURITY') || cat.toLowerCase() === 'security') {
      return { label: 'Security', color: 'danger', icon: ShieldAlert };
    }
    if (type.includes('GOVERNANCE') || cat.toLowerCase() === 'governance') {
      return { label: 'Governance', color: 'warning', icon: ShieldCheck };
    }
    if (type.includes('AUTOMATION') || cat.toLowerCase() === 'automation') {
      return { label: 'Automation', color: 'accent', icon: Workflow };
    }
    if (type.includes('INVITATION') || cat.toLowerCase() === 'collaboration') {
      return { label: 'Team', color: 'success', icon: Users };
    }
    if (type.includes('COMMENT') || cat.toLowerCase() === 'comments') {
      return { label: 'Comment', color: 'info', icon: MessageSquare };
    }
    return { label: 'System', color: 'neutral', icon: Sparkles };
  };

  return (
    <div className="notification-bell-container" ref={dropdownRef}>
      <button
        type="button"
        className={`notification-bell-btn ${unreadCount > 0 ? 'has-unread' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications, ${unreadCount} unread`}
        aria-expanded={isOpen}
      >
        <Bell size={18} />
        {unreadCount > 0 && (
          <span className="notification-badge" aria-hidden="true">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown" role="dialog" aria-label="Notification Center">
          {/* Header */}
          <div className="notification-dropdown-header">
            <div className="notif-header-title">
              <div className="notif-header-icon-wrap">
                <Bell size={16} />
              </div>
              <h3>Notifications</h3>
              {unreadCount > 0 ? (
                <span className="unread-pill">{unreadCount} new</span>
              ) : (
                <span className="caught-up-pill">All caught up</span>
              )}
            </div>

            <div className="notif-header-actions">
              <button
                type="button"
                className="icon-action-btn"
                onClick={fetchNotifications}
                title="Refresh notifications"
                aria-label="Refresh notifications"
              >
                <RefreshCw size={13} className={loading ? 'spinning' : ''} />
              </button>
              <button
                type="button"
                className="icon-action-btn close-btn"
                onClick={() => setIsOpen(false)}
                title="Close notification center"
                aria-label="Close notifications"
              >
                <X size={14} />
              </button>
            </div>
          </div>

          {/* Inline Error State if any */}
          {error && (
            <div className="notif-error-banner" role="alert">
              <AlertCircle size={14} />
              <span>{error}</span>
              <button type="button" onClick={fetchNotifications} className="retry-link">
                Retry
              </button>
            </div>
          )}

          {/* List Area */}
          <div className="notification-list">
            {loading ? (
              <div className="notif-skeletons" aria-label="Loading notifications">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="notif-skeleton-card">
                    <div className="skeleton-icon" />
                    <div className="skeleton-lines">
                      <div className="skeleton-title" />
                      <div className="skeleton-msg" />
                    </div>
                  </div>
                ))}
              </div>
            ) : notifications.length === 0 ? (
              <div className="empty-notifications">
                <div className="empty-icon-wrap">
                  <Inbox size={26} />
                </div>
                <p>No notifications yet</p>
                <span>You are fully caught up with all tasks and team activities.</span>
              </div>
            ) : (
              notifications.map((n) => {
                const isRead = Boolean(n.read_at || n.is_read);
                const { label, color, icon: CatIcon } = getCategoryMeta(n);

                return (
                  <div
                    key={n.id}
                    className={`notification-item ${isRead ? 'read' : 'unread'}`}
                    onClick={() => handleNotificationClick(n)}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        handleNotificationClick(n);
                      }
                    }}
                  >
                    {/* Left Icon with category color */}
                    <div className={`notif-icon-col icon-${color}`}>
                      <CatIcon size={16} />
                    </div>

                    {/* Content */}
                    <div className="notif-content-col">
                      <div className="notif-meta-row">
                        <span className={`notif-badge badge-${color}`}>{label}</span>
                        <span className="notif-time" title={n.created_at ? new Date(n.created_at).toLocaleString() : ''}>
                          {formatRelativeTime(n.created_at)}
                        </span>
                      </div>
                      <h4 className="notif-title">{n.title}</h4>
                      <p className="notif-message">{n.message}</p>
                    </div>

                    {/* Quick Card Delete Action */}
                    <div className="notif-actions-col">
                      <button
                        type="button"
                        className="action-btn-delete"
                        onClick={(e) => handleDelete(n.id, e)}
                        title="Delete notification"
                        aria-label="Delete notification"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
