import React, { useState, useEffect, useRef } from 'react';
import {
  Clock,
  Play,
  Pause,
  Square,
  X,
  Plus,
  CheckCircle2,
  AlertCircle,
  Calendar,
  DollarSign,
  TrendingUp,
  FileText,
  User,
  Users,
  Check,
  RotateCcw,
  Sliders,
  Filter,
  BarChart3,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { timeTrackingApi } from '../../services/timeTrackingApi';
import { taskApi } from '../../services/taskApi';
import { collaborationApi } from '../../services/collaborationApi';
import './TimeTrackingDashboard.css';

function formatDuration(seconds) {
  if (!seconds || seconds <= 0) return '00:00:00';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function TimeTrackingDashboard() {
  const { user, isAuthenticated } = useAuth();
  const isManager = ['ADMIN', 'OWNER', 'MANAGER'].includes(user?.role);

  // Active Tab
  const [activeTab, setActiveTab] = useState('entries'); // 'entries' | 'timesheet' | 'approvals' | 'reports' | 'settings'

  // Active Timer state
  const [activeTimer, setActiveTimer] = useState(null);
  const [timerSeconds, setTimerSeconds] = useState(0);
  const [timerProject, setTimerProject] = useState('');
  const [timerTask, setTimerTask] = useState('');
  const [timerDesc, setTimerDesc] = useState('');
  const [timerBillable, setTimerBillable] = useState(true);

  // Data states
  const [summary, setSummary] = useState(null);
  const [entries, setEntries] = useState([]);
  const [timesheets, setTimesheets] = useState([]);
  const [currentTimesheet, setCurrentTimesheet] = useState(null);
  const [teamTimesheets, setTeamTimesheets] = useState([]);
  const [projectReports, setProjectReports] = useState([]);
  const [billableReport, setBillableReport] = useState(null);
  const [settings, setSettings] = useState(null);
  const [projectsList, setProjectsList] = useState([]);
  const [tasksList, setTasksList] = useState([]);

  // Modals & UI States
  const [showManualModal, setShowManualModal] = useState(false);
  const [manualData, setManualData] = useState({
    project_id: '',
    task_id: '',
    description: '',
    start_time: new Date().toISOString().slice(0, 16),
    end_time: '',
    duration_hours: '1.0',
    billable: true,
    hourly_rate: 75,
  });
  const [reviewModal, setReviewModal] = useState({
    open: false,
    timesheetId: null,
    action: 'APPROVE', // 'APPROVE' | 'REJECT' | 'REOPEN'
    comments: '',
  });

  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);

  // Timer interval
  useEffect(() => {
    let interval = null;
    if (activeTimer && activeTimer.status === 'RUNNING') {
      interval = setInterval(() => {
        setTimerSeconds((prev) => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [activeTimer]);

  // Initial load
  useEffect(() => {
    if (isAuthenticated) {
      loadInitialData();
    }
  }, [isAuthenticated]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [sumRes, activeRes, entRes, projRes, taskRes, setRes] = await Promise.all([
        timeTrackingApi.getSummary().catch(() => null),
        timeTrackingApi.getActiveTimer().catch(() => null),
        timeTrackingApi.getEntries().catch(() => []),
        collaborationApi.getProjects().catch(() => []),
        taskApi.getTasks().catch(() => []),
        timeTrackingApi.getSettings().catch(() => null),
      ]);

      if (sumRes) setSummary(sumRes);
      if (activeRes) {
        setActiveTimer(activeRes);
        setTimerSeconds(activeRes.elapsed_seconds || 0);
        setTimerDesc(activeRes.description || '');
        setTimerProject(activeRes.project_id || '');
        setTimerTask(activeRes.task_id || '');
        setTimerBillable(activeRes.billable);
      }
      setEntries(entRes || []);
      setProjectsList(Array.isArray(projRes) ? projRes : projRes?.items || []);
      setTasksList(Array.isArray(taskRes) ? taskRes : taskRes?.items || []);
      if (setRes) setSettings(setRes);

      loadCurrentTimesheet();
    } catch (err) {
      console.warn('Error loading time tracking data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCurrentTimesheet = async () => {
    try {
      const today = new Date();
      const firstDay = new Date(today.setDate(today.getDate() - today.getDay() + 1));
      const lastDay = new Date(today.setDate(today.getDate() - today.getDay() + 7));
      const pStart = firstDay.toISOString().split('T')[0];
      const pEnd = lastDay.toISOString().split('T')[0];

      const ts = await timeTrackingApi.getOrCreateTimesheet({
        period_start: pStart,
        period_end: pEnd,
      });
      setCurrentTimesheet(ts);
    } catch (err) {
      console.warn('Failed to load current timesheet:', err);
    }
  };

  const loadApprovals = async () => {
    if (!isManager) return;
    try {
      const allTs = await timeTrackingApi.getTimesheets({ all_team: true, status: 'SUBMITTED' });
      setTeamTimesheets(allTs || []);
    } catch (err) {
      console.warn('Failed to load approvals:', err);
    }
  };

  const loadReports = async () => {
    try {
      const [projRep, billRep] = await Promise.all([
        timeTrackingApi.getProjectReports(),
        timeTrackingApi.getBillableReport(),
      ]);
      setProjectReports(projRep || []);
      setBillableReport(billRep);
    } catch (err) {
      console.warn('Failed to load reports:', err);
    }
  };

  useEffect(() => {
    if (activeTab === 'approvals') loadApprovals();
    if (activeTab === 'reports') loadReports();
  }, [activeTab]);

  // --- Active Timer Actions ---
  const handleStartTimer = async () => {
    try {
      const payload = {
        project_id: timerProject ? parseInt(timerProject) : null,
        task_id: timerTask || null,
        description: timerDesc.trim() || 'Focus Session',
        billable: timerBillable,
      };
      const newTimer = await timeTrackingApi.startTimer(payload);
      setActiveTimer(newTimer);
      setTimerSeconds(newTimer.elapsed_seconds || 0);
      showFlash('Timer started successfully.');
    } catch (err) {
      showFlash(err.response?.data?.detail || 'Failed to start timer.', 'error');
    }
  };

  const handlePauseTimer = async () => {
    try {
      const paused = await timeTrackingApi.pauseTimer();
      setActiveTimer(paused);
      showFlash('Timer paused.');
    } catch (err) {
      showFlash('Failed to pause timer.', 'error');
    }
  };

  const handleResumeTimer = async () => {
    try {
      const resumed = await timeTrackingApi.resumeTimer();
      setActiveTimer(resumed);
      showFlash('Timer resumed.');
    } catch (err) {
      showFlash('Failed to resume timer.', 'error');
    }
  };

  const handleStopTimer = async () => {
    try {
      const entry = await timeTrackingApi.stopTimer();
      setActiveTimer(null);
      setTimerSeconds(0);
      setTimerDesc('');
      setEntries((prev) => [entry, ...prev]);
      showFlash(`Logged ${entry.duration_formatted} to time records.`);
      loadInitialData();
    } catch (err) {
      showFlash('Failed to stop timer.', 'error');
    }
  };

  const handleCancelTimer = async () => {
    if (!window.confirm('Discard current timer without logging time?')) return;
    try {
      await timeTrackingApi.cancelTimer();
      setActiveTimer(null);
      setTimerSeconds(0);
      setTimerDesc('');
      showFlash('Timer discarded.');
    } catch (err) {
      showFlash('Failed to cancel timer.', 'error');
    }
  };

  // --- Manual Entry Actions ---
  const handleSaveManualEntry = async (e) => {
    e.preventDefault();
    try {
      const durSec = Math.round(parseFloat(manualData.duration_hours || 1) * 3600);
      const payload = {
        project_id: manualData.project_id ? parseInt(manualData.project_id) : null,
        task_id: manualData.task_id || null,
        description: manualData.description.trim(),
        start_time: new Date(manualData.start_time).toISOString(),
        duration_seconds: durSec,
        billable: manualData.billable,
        hourly_rate: parseFloat(manualData.hourly_rate) || 75.0,
      };
      const created = await timeTrackingApi.createEntry(payload);
      setEntries((prev) => [created, ...prev]);
      setShowManualModal(false);
      showFlash('Manual entry logged successfully.');
      loadInitialData();
    } catch (err) {
      showFlash(err.response?.data?.detail || 'Failed to create manual entry.', 'error');
    }
  };

  const handleDeleteEntry = async (entryId) => {
    if (!window.confirm('Are you sure you want to delete this time entry?')) return;
    try {
      await timeTrackingApi.deleteEntry(entryId);
      setEntries((prev) => prev.filter((e) => e.id !== entryId));
      showFlash('Time entry deleted.');
      loadInitialData();
    } catch (err) {
      showFlash('Failed to delete time entry.', 'error');
    }
  };

  // --- Timesheet Actions ---
  const handleSubmitCurrentTimesheet = async () => {
    if (!currentTimesheet) return;
    try {
      const submitted = await timeTrackingApi.submitTimesheet(currentTimesheet.id);
      setCurrentTimesheet(submitted);
      showFlash('Timesheet submitted for manager review.');
    } catch (err) {
      showFlash('Failed to submit timesheet.', 'error');
    }
  };

  const handleWithdrawCurrentTimesheet = async () => {
    if (!currentTimesheet) return;
    try {
      const withdrawn = await timeTrackingApi.withdrawTimesheet(currentTimesheet.id);
      setCurrentTimesheet(withdrawn);
      showFlash('Timesheet withdrawn back to draft.');
    } catch (err) {
      showFlash('Failed to withdraw timesheet.', 'error');
    }
  };

  // --- Review Actions ---
  const handleReviewTimesheet = async () => {
    const { timesheetId, action, comments } = reviewModal;
    try {
      if (action === 'APPROVE') {
        await timeTrackingApi.approveTimesheet(timesheetId, comments);
        showFlash('Timesheet approved.');
      } else if (action === 'REJECT') {
        await timeTrackingApi.rejectTimesheet(timesheetId, comments);
        showFlash('Timesheet rejected with feedback.');
      } else if (action === 'REOPEN') {
        await timeTrackingApi.reopenTimesheet(timesheetId, comments);
        showFlash('Timesheet reopened.');
      }
      setReviewModal({ open: false, timesheetId: null, action: 'APPROVE', comments: '' });
      loadApprovals();
    } catch (err) {
      showFlash('Failed to review timesheet.', 'error');
    }
  };

  // --- Settings Update ---
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      const updated = await timeTrackingApi.updateSettings(settings);
      setSettings(updated);
      showFlash('Time tracking preferences saved.');
    } catch (err) {
      showFlash('Failed to save settings.', 'error');
    }
  };

  const showFlash = (msg, type = 'success') => {
    setStatusMessage({ msg, type });
    setTimeout(() => setStatusMessage(null), 4000);
  };

  return (
    <div className="time-tracking-dashboard">
      {/* Toast Alert */}
      {statusMessage && (
        <div className={`time-toast ${statusMessage.type}`}>
          {statusMessage.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          <span>{statusMessage.msg}</span>
        </div>
      )}

      {/* ================= 1. ACTIVE TIMER BAR ================= */}
      <section className="timer-bar-container">
        <div className="timer-bar-left">
          <div className={`timer-clock-display ${activeTimer?.status === 'RUNNING' ? 'running' : ''}`}>
            <Clock size={20} className="timer-icon" />
            <span className="timer-digits">{formatDuration(timerSeconds)}</span>
          </div>

          <input
            type="text"
            className="timer-desc-input"
            placeholder="What are you working on right now?"
            value={timerDesc}
            onChange={(e) => setTimerDesc(e.target.value)}
          />
        </div>

        <div className="timer-bar-middle">
          <select
            className="timer-select"
            value={timerProject}
            onChange={(e) => setTimerProject(e.target.value)}
            disabled={activeTimer?.status === 'RUNNING'}
          >
            <option value="">Select Project</option>
            {projectsList.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          <select
            className="timer-select"
            value={timerTask}
            onChange={(e) => setTimerTask(e.target.value)}
            disabled={activeTimer?.status === 'RUNNING'}
          >
            <option value="">Select Task</option>
            {tasksList.map((t) => (
              <option key={t.id} value={t.id}>{t.title}</option>
            ))}
          </select>

          <label className="timer-billable-toggle">
            <input
              type="checkbox"
              checked={timerBillable}
              onChange={(e) => setTimerBillable(e.target.checked)}
            />
            <span>Billable</span>
          </label>
        </div>

        <div className="timer-bar-right">
          {!activeTimer ? (
            <button type="button" className="timer-btn play" onClick={handleStartTimer}>
              <Play size={16} /> <span>Start</span>
            </button>
          ) : activeTimer.status === 'RUNNING' ? (
            <>
              <button type="button" className="timer-btn pause" onClick={handlePauseTimer}>
                <Pause size={16} /> <span>Pause</span>
              </button>
              <button type="button" className="timer-btn stop" onClick={handleStopTimer}>
                <Square size={16} /> <span>Stop</span>
              </button>
              <button type="button" className="timer-btn cancel" onClick={handleCancelTimer} title="Cancel Timer">
                <X size={16} />
              </button>
            </>
          ) : (
            <>
              <button type="button" className="timer-btn resume" onClick={handleResumeTimer}>
                <Play size={16} /> <span>Resume</span>
              </button>
              <button type="button" className="timer-btn stop" onClick={handleStopTimer}>
                <Square size={16} /> <span>Stop</span>
              </button>
              <button type="button" className="timer-btn cancel" onClick={handleCancelTimer} title="Cancel Timer">
                <X size={16} />
              </button>
            </>
          )}
        </div>
      </section>

      {/* ================= 2. DASHBOARD KPI CARDS ================= */}
      <section className="time-kpi-grid">
        <div className="time-kpi-card">
          <div className="kpi-icon-box blue">
            <Clock size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">TODAY'S HOURS</span>
            <h3 className="kpi-value">{summary?.today_hours?.toFixed(1) || '0.0'}h</h3>
          </div>
        </div>

        <div className="time-kpi-card">
          <div className="kpi-icon-box indigo">
            <Calendar size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">THIS WEEK</span>
            <h3 className="kpi-value">{summary?.this_week_hours?.toFixed(1) || '0.0'}h</h3>
          </div>
        </div>

        <div className="time-kpi-card">
          <div className="kpi-icon-box green">
            <DollarSign size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">BILLABLE RATIO</span>
            <h3 className="kpi-value">
              {summary?.this_week_hours ? Math.round((summary.billable_hours / summary.this_week_hours) * 100) : 100}%
            </h3>
          </div>
        </div>

        <div className="time-kpi-card">
          <div className="kpi-icon-box purple">
            <FileText size={20} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">CURRENT TIMESHEET</span>
            <h3 className="kpi-value status-badge-kpi">{currentTimesheet?.status || 'DRAFT'}</h3>
          </div>
        </div>
      </section>

      {/* ================= 3. NAVIGATION TABS ================= */}
      <div className="time-tabs-row">
        <div className="time-tabs">
          <button
            type="button"
            className={`time-tab-btn ${activeTab === 'entries' ? 'active' : ''}`}
            onClick={() => setActiveTab('entries')}
          >
            <Clock size={16} />
            <span>Logged Entries</span>
          </button>
          <button
            type="button"
            className={`time-tab-btn ${activeTab === 'timesheet' ? 'active' : ''}`}
            onClick={() => setActiveTab('timesheet')}
          >
            <FileText size={16} />
            <span>Weekly Timesheet</span>
          </button>
          {isManager && (
            <button
              type="button"
              className={`time-tab-btn ${activeTab === 'approvals' ? 'active' : ''}`}
              onClick={() => setActiveTab('approvals')}
            >
              <CheckCircle2 size={16} />
              <span>Approvals ({teamTimesheets.length})</span>
            </button>
          )}
          <button
            type="button"
            className={`time-tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            <BarChart3 size={16} />
            <span>Reports & Billables</span>
          </button>
          {isManager && (
            <button
              type="button"
              className={`time-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
              onClick={() => setActiveTab('settings')}
            >
              <Sliders size={16} />
              <span>Preferences</span>
            </button>
          )}
        </div>

        {activeTab === 'entries' && (
          <button
            type="button"
            className="add-manual-btn"
            onClick={() => setShowManualModal(true)}
          >
            <Plus size={16} />
            <span>Log Time Manually</span>
          </button>
        )}
      </div>

      {/* ================= 4. TAB PANELS ================= */}

      {/* TAB 1: LOGGED ENTRIES */}
      {activeTab === 'entries' && (
        <section className="entries-table-section">
          {entries.length === 0 ? (
            <div className="empty-state-panel">
              <Clock size={40} className="empty-icon" />
              <h3>No Time Entries Recorded</h3>
              <p>Start the active timer above or log a manual entry to track your hours.</p>
            </div>
          ) : (
            <div className="entries-table-wrapper">
              <table className="time-table">
                <thead>
                  <tr>
                    <th>Date & Description</th>
                    <th>Project & Task</th>
                    <th>Source</th>
                    <th>Duration</th>
                    <th>Billable</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id}>
                      <td>
                        <div className="entry-desc-col">
                          <span className="entry-title">{entry.description || 'General Effort'}</span>
                          <span className="entry-time-meta">
                            {new Date(entry.start_time).toLocaleDateString()} at{' '}
                            {new Date(entry.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="entry-proj-col">
                          <span className="proj-badge">{entry.project_name || 'Independent'}</span>
                          {entry.task_title && <span className="task-subtext">{entry.task_title}</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`source-pill ${entry.entry_source?.toLowerCase()}`}>
                          {entry.entry_source}
                        </span>
                      </td>
                      <td>
                        <strong className="duration-text">{entry.duration_formatted}</strong>
                      </td>
                      <td>
                        <span className={`billable-pill ${entry.billable ? 'yes' : 'no'}`}>
                          {entry.billable ? `$${entry.billable_amount?.toFixed(2)}` : 'Non-Billable'}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="row-delete-btn"
                          onClick={() => handleDeleteEntry(entry.id)}
                          title="Delete entry"
                        >
                          <X size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* TAB 2: WEEKLY TIMESHEET */}
      {activeTab === 'timesheet' && (
        <section className="timesheet-view-section">
          {currentTimesheet && (
            <div className="timesheet-header-card">
              <div>
                <span className="ts-period-badge">
                  {currentTimesheet.period_start} to {currentTimesheet.period_end}
                </span>
                <h2>Weekly Timesheet Summary</h2>
                <p>Status: <span className={`status-pill ${currentTimesheet.status.toLowerCase()}`}>{currentTimesheet.status}</span></p>
              </div>

              <div className="ts-stats-group">
                <div className="ts-stat">
                  <span className="ts-stat-lbl">TOTAL HOURS</span>
                  <span className="ts-stat-val">{currentTimesheet.total_hours?.toFixed(1)}h</span>
                </div>
                <div className="ts-stat">
                  <span className="ts-stat-lbl">BILLABLE HOURS</span>
                  <span className="ts-stat-val">{currentTimesheet.billable_hours?.toFixed(1)}h</span>
                </div>

                {currentTimesheet.status === 'DRAFT' && (
                  <button
                    type="button"
                    className="submit-ts-btn"
                    onClick={handleSubmitCurrentTimesheet}
                  >
                    Submit for Approval
                  </button>
                )}

                {currentTimesheet.status === 'SUBMITTED' && (
                  <button
                    type="button"
                    className="withdraw-ts-btn"
                    onClick={handleWithdrawCurrentTimesheet}
                  >
                    Withdraw Timesheet
                  </button>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* TAB 3: APPROVALS */}
      {activeTab === 'approvals' && isManager && (
        <section className="approvals-section">
          <h3>Team Timesheets Pending Review</h3>
          {teamTimesheets.length === 0 ? (
            <div className="empty-state-panel">
              <CheckCircle2 size={40} className="empty-icon green" />
              <h3>All Caught Up</h3>
              <p>There are no timesheets awaiting approval right now.</p>
            </div>
          ) : (
            <div className="team-ts-list">
              {teamTimesheets.map((ts) => (
                <div key={ts.id} className="team-ts-card">
                  <div className="team-ts-info">
                    <h4>{ts.user_name || `Team Member #${ts.user_id}`}</h4>
                    <p>{ts.period_start} to {ts.period_end} • {ts.total_hours?.toFixed(1)} hours logged</p>
                  </div>
                  <div className="team-ts-actions">
                    <button
                      type="button"
                      className="approve-btn"
                      onClick={() => setReviewModal({ open: true, timesheetId: ts.id, action: 'APPROVE', comments: '' })}
                    >
                      <Check size={16} /> Approve
                    </button>
                    <button
                      type="button"
                      className="reject-btn"
                      onClick={() => setReviewModal({ open: true, timesheetId: ts.id, action: 'REJECT', comments: '' })}
                    >
                      <X size={16} /> Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* TAB 4: REPORTS & BILLABLES */}
      {activeTab === 'reports' && (
        <section className="reports-section">
          <div className="billable-overview-box">
            <h3>Billable & Revenue Analysis</h3>
            <div className="billable-kpis">
              <div className="b-kpi">
                <span>Total Billable Hours</span>
                <h4>{billableReport?.total_billable_hours || '0.0'}h</h4>
              </div>
              <div className="b-kpi">
                <span>Non-Billable Hours</span>
                <h4>{billableReport?.total_non_billable_hours || '0.0'}h</h4>
              </div>
              <div className="b-kpi">
                <span>Estimated Value</span>
                <h4>${billableReport?.total_billable_amount?.toFixed(2) || '0.00'}</h4>
              </div>
            </div>
          </div>

          <h3>Project Time Breakdown</h3>
          <div className="project-reports-grid">
            {projectReports.map((p) => (
              <div key={p.project_id || p.project_name} className="project-report-card">
                <h4>{p.project_name}</h4>
                <div className="proj-rep-details">
                  <span>Logged: {p.total_hours?.toFixed(1)}h</span>
                  <span>Billable: {p.billable_hours?.toFixed(1)}h</span>
                  <span>Entries: {p.entries_count}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* TAB 5: PREFERENCES & SETTINGS */}
      {activeTab === 'settings' && isManager && settings && (
        <section className="settings-section">
          <h3>Time Tracking & Timesheet Policy Settings</h3>
          <form onSubmit={handleSaveSettings} className="settings-form">
            <div className="form-group-row">
              <label>Default Daily Work Hours</label>
              <input
                type="number"
                step="0.5"
                value={settings.default_daily_hours}
                onChange={(e) => setSettings({ ...settings, default_daily_hours: parseFloat(e.target.value) })}
              />
            </div>
            <div className="form-group-row">
              <label>Default Hourly Billing Rate ($)</label>
              <input
                type="number"
                step="5"
                value={settings.default_hourly_rate}
                onChange={(e) => setSettings({ ...settings, default_hourly_rate: parseFloat(e.target.value) })}
              />
            </div>
            <div className="form-group-row">
              <label>Require Timesheet Approvals</label>
              <input
                type="checkbox"
                checked={settings.require_timesheet_approval}
                onChange={(e) => setSettings({ ...settings, require_timesheet_approval: e.target.checked })}
              />
            </div>
            <button type="submit" className="save-settings-btn">Save Preferences</button>
          </form>
        </section>
      )}

      {/* ================= MODAL: MANUAL TIME ENTRY ================= */}
      {showManualModal && (
        <div className="modal-backdrop" onClick={() => setShowManualModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Log Time Manually</h3>
              <button type="button" className="close-btn" onClick={() => setShowManualModal(false)}>✕</button>
            </div>
            <form onSubmit={handleSaveManualEntry} className="modal-form">
              <div className="form-field">
                <label>Description / Work Completed</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Design review with engineering"
                  value={manualData.description}
                  onChange={(e) => setManualData({ ...manualData, description: e.target.value })}
                />
              </div>

              <div className="form-field-row">
                <div className="form-field">
                  <label>Project</label>
                  <select
                    value={manualData.project_id}
                    onChange={(e) => setManualData({ ...manualData, project_id: e.target.value })}
                  >
                    <option value="">None / Independent</option>
                    {projectsList.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label>Task</label>
                  <select
                    value={manualData.task_id}
                    onChange={(e) => setManualData({ ...manualData, task_id: e.target.value })}
                  >
                    <option value="">None</option>
                    {tasksList.map((t) => (
                      <option key={t.id} value={t.id}>{t.title}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-field-row">
                <div className="form-field">
                  <label>Date & Start Time</label>
                  <input
                    type="datetime-local"
                    value={manualData.start_time}
                    onChange={(e) => setManualData({ ...manualData, start_time: e.target.value })}
                    required
                  />
                </div>
                <div className="form-field">
                  <label>Duration (Hours)</label>
                  <input
                    type="number"
                    step="0.25"
                    min="0.25"
                    max="24"
                    value={manualData.duration_hours}
                    onChange={(e) => setManualData({ ...manualData, duration_hours: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-field-checkbox">
                <label>
                  <input
                    type="checkbox"
                    checked={manualData.billable}
                    onChange={(e) => setManualData({ ...manualData, billable: e.target.checked })}
                  />
                  <span>Billable to Client</span>
                </label>
              </div>

              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setShowManualModal(false)}>Cancel</button>
                <button type="submit" className="btn-submit">Record Time Entry</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: TIMESHEET REVIEW ================= */}
      {reviewModal.open && (
        <div className="modal-backdrop" onClick={() => setReviewModal({ ...reviewModal, open: false })}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{reviewModal.action === 'APPROVE' ? 'Approve Timesheet' : 'Reject Timesheet'}</h3>
              <button type="button" className="close-btn" onClick={() => setReviewModal({ ...reviewModal, open: false })}>✕</button>
            </div>
            <div className="modal-form">
              <div className="form-field">
                <label>Reviewer Feedback / Comments</label>
                <textarea
                  rows="3"
                  placeholder="Enter comments or notes for the team member..."
                  value={reviewModal.comments}
                  onChange={(e) => setReviewModal({ ...reviewModal, comments: e.target.value })}
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-cancel" onClick={() => setReviewModal({ ...reviewModal, open: false })}>Cancel</button>
                <button
                  type="button"
                  className={reviewModal.action === 'APPROVE' ? 'btn-submit' : 'btn-danger'}
                  onClick={handleReviewTimesheet}
                >
                  Confirm {reviewModal.action}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default TimeTrackingDashboard;
