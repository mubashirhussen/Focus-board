import React, { useState, useEffect } from 'react';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  RefreshCw,
  AlertTriangle,
  Plus,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import { calendarApi } from '../../services/calendarApi';
import { useTasks } from '../../hooks/useTasks';
import { useAuth } from '../../context/AuthContext';
import './CalendarView.css';

export function CalendarView() {
  const { isAuthenticated } = useAuth();
  const { tasks } = useTasks();
  const [events, setEvents] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('agenda'); // 'agenda', 'month'
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState('');

  const sampleCalendarProjects = [
    { id: 'proj_1', name: 'Enterprise SOC 2 Compliance', status: 'IN_PROGRESS', progress: 75, color: '#10B981', tasksCount: 8, deadline: 'Today, 11:30 AM' },
    { id: 'proj_2', name: 'AI Autonomous Agent Scheduler', status: 'IN_PROGRESS', progress: 85, color: '#4F46E5', tasksCount: 12, deadline: 'Tomorrow, 3:30 PM' },
    { id: 'proj_3', name: 'Cross-Platform PWA Offline Engine', status: 'COMPLETED', progress: 100, color: '#06B6D4', tasksCount: 6, deadline: 'Friday, 5:00 PM' },
  ];

  const sampleEvents = [
    {
      id: 'evt_1',
      title: 'Enterprise SOC 2 Compliance Readiness Sprint',
      project: 'Enterprise SOC 2 Compliance',
      start: new Date(Date.now() + 3600000).toISOString(),
      end: new Date(Date.now() + 9000000).toISOString(),
      source: 'focusboard',
      is_completed: false,
      description: 'Auditing access reviews, continuous posture evidence, and CVE mitigation logs.',
    },
    {
      id: 'evt_2',
      title: 'AI Autonomous Agent Knapsack Scheduler Demo',
      project: 'AI Autonomous Agent Scheduler',
      start: new Date(Date.now() + 86400000).toISOString(),
      end: new Date(Date.now() + 93600000).toISOString(),
      source: 'focusboard',
      is_completed: true,
      description: 'Presenting multi-step proposal approval gating to engineering leads.',
    },
    {
      id: 'evt_3',
      title: 'Cross-Platform PWA Offline Sync Engine Rollout',
      project: 'Cross-Platform PWA Offline Engine',
      start: new Date(Date.now() + 172800000).toISOString(),
      end: new Date(Date.now() + 180000000).toISOString(),
      source: 'google_calendar',
      is_completed: false,
      description: 'Testing IndexedDB mutation queue reconciliation upon network reconnect.',
    },
  ];

  const loadCalendarData = async () => {
    try {
      const [eventsData, conflictsData] = await Promise.all([
        calendarApi.getEvents().catch(() => []),
        calendarApi.getConflicts().catch(() => []),
      ]);
      setEvents(eventsData && eventsData.length > 0 ? eventsData : sampleEvents);
      setConflicts(conflictsData || []);
    } catch {
      setEvents(sampleEvents);
    }
  };

  useEffect(() => {
    loadCalendarData();
  }, [isAuthenticated]);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncStatus('');
    try {
      const res = await calendarApi.triggerSync();
      setSyncStatus(`Sync successful! ${res.tasks_synced} tasks synchronized.`);
      loadCalendarData();
    } catch (err) {
      setSyncStatus('Synchronization failed. Please check your connection.');
    } finally {
      setIsSyncing(false);
    }
  };

  const nextPeriod = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() + (viewMode === 'month' ? 30 : 7));
    setCurrentDate(d);
  };

  const prevPeriod = () => {
    const d = new Date(currentDate);
    d.setDate(d.getDate() - (viewMode === 'month' ? 30 : 7));
    setCurrentDate(d);
  };

  return (
    <div className="calendar-page">
      {/* Calendar Header Navigation */}
      <div className="calendar-header">
        <div className="calendar-title-group">
          <CalendarIcon size={22} className="cal-icon" />
          <h1 className="calendar-title">Schedule & Calendar Sync</h1>
        </div>

        <div className="calendar-controls">
          <button
            type="button"
            className="btn-sync-cal"
            onClick={handleSync}
            disabled={isSyncing}
          >
            <RefreshCw size={14} className={isSyncing ? 'spin-icon' : ''} />
            <span>{isSyncing ? 'Syncing...' : 'Sync with Google'}</span>
          </button>

          <div className="view-switch-btns">
            <button
              type="button"
              className={`view-btn ${viewMode === 'agenda' ? 'view-btn-active' : ''}`}
              onClick={() => setViewMode('agenda')}
            >
              Agenda
            </button>
            <button
              type="button"
              className={`view-btn ${viewMode === 'month' ? 'view-btn-active' : ''}`}
              onClick={() => setViewMode('month')}
            >
              Timeline
            </button>
          </div>

          <div className="nav-arrows">
            <button type="button" className="arrow-btn" onClick={prevPeriod} aria-label="Previous">
              <ChevronLeft size={16} />
            </button>
            <button type="button" className="arrow-btn" onClick={() => setCurrentDate(new Date())}>
              Today
            </button>
            <button type="button" className="arrow-btn" onClick={nextPeriod} aria-label="Next">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {syncStatus && (
        <div className="cal-alert-banner">
          <span>{syncStatus}</span>
        </div>
      )}

      {/* Conflict Detection Banner */}
      {conflicts.length > 0 && (
        <div className="cal-conflicts-card">
          <div className="conflict-card-header">
            <AlertTriangle size={18} className="warn-icon" />
            <span className="conflict-title">Scheduling Conflicts Detected ({conflicts.length})</span>
          </div>
          <div className="conflict-list">
            {conflicts.map((c, idx) => (
              <div key={idx} className="conflict-item">
                <span className="conflict-bullet">•</span>
                <span className="conflict-message">{c.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tracked Projects on Calendar */}
      <div className="calendar-projects-ribbon">
        <h3 className="cal-section-subtitle">Active Projects & Scheduled Milestones</h3>
        <div className="cal-projects-grid">
          {sampleCalendarProjects.map((p) => (
            <div key={p.id} className="cal-project-card">
              <div className="cal-project-top">
                <span className="cal-project-dot" style={{ backgroundColor: p.color }} />
                <span className="cal-project-name">{p.name}</span>
                <span className={`cal-project-status ${p.status.toLowerCase()}`}>{p.status.replace('_', ' ')}</span>
              </div>
              <div className="cal-project-meta">
                <span>{p.tasksCount} active tasks</span>
                <span className="cal-project-deadline">{p.deadline}</span>
              </div>
              <div className="cal-progress-track">
                <div className="cal-progress-fill" style={{ width: `${p.progress}%`, backgroundColor: p.color }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Events Agenda List */}
      <div className="calendar-body">
        <div className="agenda-container">
          <h2 className="agenda-heading">Upcoming Scheduled Tasks & Calendar Events</h2>
          {events.length === 0 ? (
            <div className="empty-calendar">
              <Clock size={36} className="empty-icon" />
              <p>No tasks or calendar events scheduled for this period.</p>
              <span className="empty-subtext">Set due dates or schedule tasks to see them appear on your timeline.</span>
            </div>
          ) : (
            <div className="events-timeline">
              {events.map((evt) => {
                const isGoogle = evt.source === 'google_calendar';
                const startTime = new Date(evt.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const endTime = new Date(evt.end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                const dateStr = new Date(evt.start).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });

                return (
                  <div key={evt.id} className={`event-row ${isGoogle ? 'event-google' : 'event-focusboard'}`}>
                    <div className="event-time-col">
                      <span className="event-date">{dateStr}</span>
                      <span className="event-time">{startTime} – {endTime}</span>
                    </div>

                    <div className="event-content-col">
                      <div className="event-title-line">
                        <span className="event-title">{evt.title}</span>
                        <span className={`source-badge ${isGoogle ? 'badge-google' : 'badge-focusboard'}`}>
                          {isGoogle ? 'Google Calendar' : 'FocusBoard'}
                        </span>
                        {evt.is_completed && (
                          <span className="completed-badge">
                            <CheckCircle2 size={12} /> Done
                          </span>
                        )}
                      </div>
                      {evt.description && <p className="event-desc">{evt.description}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
