import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, Trash2, Clock, AlertTriangle, Sparkles, RefreshCw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import { notificationApi } from '../../services/notificationApi';
import './NotificationBell.css';

export function NotificationBell() {
  const { isAuthenticated } = useAuth();
  const { tasks } = useTasks();
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    if (isAuthenticated) {
      try {
        setLoading(true);
        const [notifData, countData] = await Promise.all([
          notificationApi.getNotifications(),
          notificationApi.getUnreadCount(),
        ]);
        setNotifications(notifData || []);
        setUnreadCount(countData?.unread_count || 0);
      } catch (err) {
        console.warn('Failed to load notifications from API:', err);
      } finally {
        setLoading(false);
      }
    } else {
      // Local fallback for guest mode: derive deadlines directly
      generateLocalNotifications();
    }
  };

  const generateLocalNotifications = () => {
    const todayStr = new Date().toISOString().split('T')[0];
    const localNotifs = [];

    tasks.forEach((t) => {
      if ((t.status || '').toLowerCase() === 'completed') return;

      if (t.dueDate) {
        if (t.dueDate < todayStr) {
          localNotifs.push({
            id: `local-overdue-${t.id}`,
            type: 'TASK_OVERDUE',
            title: `Task Overdue: ${t.title}`,
            message: `Was due on ${t.dueDate}. Review priority or reschedule.`,
            is_read: false,
            created_at: new Date().toISOString(),
          });
        } else if (t.dueDate === todayStr) {
          localNotifs.push({
            id: `local-today-${t.id}`,
            type: 'TASK_DUE_TODAY',
            title: `Due Today: ${t.title}`,
            message: 'Allocated for completion today.',
            is_read: false,
            created_at: new Date().toISOString(),
          });
        }
      }
    });

    setNotifications(localNotifs);
    setUnreadCount(localNotifs.length);
  };

  useEffect(() => {
    fetchNotifications();
  }, [isAuthenticated, tasks]);

  const handleMarkAsRead = async (notifId) => {
    if (isAuthenticated && typeof notifId === 'number') {
      try {
        await notificationApi.markAsRead(notifId);
      } catch (err) {
        console.error('Failed to mark read:', err);
      }
    }
    setNotifications((prev) =>
      prev.map((n) => (n.id === notifId ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
    );
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  const handleMarkAllRead = async () => {
    if (isAuthenticated) {
      try {
        await notificationApi.markAllAsRead();
      } catch (err) {
        console.error('Failed to mark all read:', err);
      }
    }
    setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() })));
    setUnreadCount(0);
  };

  const handleDelete = async (notifId, e) => {
    e.stopPropagation();
    if (isAuthenticated && typeof notifId === 'number') {
      try {
        await notificationApi.deleteNotification(notifId);
      } catch (err) {
        console.error('Failed to delete notification:', err);
      }
    }
    setNotifications((prev) => prev.filter((n) => n.id !== notifId));
    setUnreadCount((c) => Math.max(0, c - 1));
  };

  const handleTriggerCheck = async () => {
    if (isAuthenticated) {
      try {
        await notificationApi.triggerCheck();
        await fetchNotifications();
      } catch (err) {
        console.error('Failed to trigger deadline check:', err);
      }
    } else {
      generateLocalNotifications();
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'TASK_OVERDUE':
        return <AlertTriangle size={15} className="notif-icon overdue" />;
      case 'TASK_DUE_TODAY':
      case 'TASK_DUE_SOON':
        return <Clock size={15} className="notif-icon due" />;
      default:
        return <Sparkles size={15} className="notif-icon system" />;
    }
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
        <div className="notification-dropdown">
          <div className="notification-dropdown-header">
            <div className="notif-header-title">
              <h3>Notifications</h3>
              {unreadCount > 0 && <span className="unread-pill">{unreadCount} new</span>}
            </div>
            <div className="notif-header-actions">
              <button
                type="button"
                className="icon-text-btn"
                onClick={handleTriggerCheck}
                title="Check latest deadlines"
              >
                <RefreshCw size={13} className={loading ? 'spinning' : ''} />
              </button>
              {notifications.length > 0 && (
                <button
                  type="button"
                  className="icon-text-btn"
                  onClick={handleMarkAllRead}
                  title="Mark all as read"
                >
                  <Check size={13} />
                  <span>Mark all read</span>
                </button>
              )}
            </div>
          </div>

          <div className="notification-list">
            {notifications.length === 0 ? (
              <div className="empty-notifications">
                <Clock size={24} className="empty-icon" />
                <p>No new notifications</p>
                <span>You are all caught up on your deadlines.</span>
              </div>
            ) : (
              notifications.map((n) => {
                const isRead = !!n.read_at || n.is_read;
                return (
                  <div
                    key={n.id}
                    className={`notification-item ${isRead ? 'read' : 'unread'}`}
                    onClick={() => !isRead && handleMarkAsRead(n.id)}
                  >
                    <div className="notif-icon-col">{getNotificationIcon(n.type)}</div>
                    <div className="notif-content-col">
                      <h4 className="notif-title">{n.title}</h4>
                      <p className="notif-message">{n.message}</p>
                      <span className="notif-time">
                        {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Today'}
                      </span>
                    </div>
                    <div className="notif-actions-col">
                      {!isRead && <span className="unread-dot" title="Unread" />}
                      <button
                        type="button"
                        className="delete-notif-btn"
                        onClick={(e) => handleDelete(n.id, e)}
                        title="Dismiss notification"
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
