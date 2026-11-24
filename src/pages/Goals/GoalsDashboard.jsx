import React, { useState, useEffect, useCallback } from 'react';
import {
  Target,
  Flag,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Plus,
  Search,
  Filter,
  RefreshCw,
  ChevronRight,
  ChevronDown,
  Layers,
  Award,
  Calendar,
  MessageSquare,
  CheckSquare,
  Sparkles,
  Link2,
  X,
  FileText,
  Sliders,
  Send,
  ShieldAlert,
  ArrowUpRight,
  ArrowDownRight,
  PieChart,
} from 'lucide-react';
import { goalApi } from '../../services/goalApi';
import { useAuth } from '../../context/AuthContext';
import './GoalsDashboard.css';

export function GoalsDashboard() {
  const { user, isAuthenticated } = useAuth();

  // State
  const [activeTab, setActiveTab] = useState('okrs'); // 'okrs' | 'milestones' | 'checkins' | 'analytics'
  const [overview, setOverview] = useState(null);
  const [goals, setGoals] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [healthFilter, setHealthFilter] = useState('ALL');

  // Modals
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [showKrModal, setShowKrModal] = useState(false);
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [showCheckInModal, setShowCheckInModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [activeKrForProgress, setActiveKrForProgress] = useState(null);

  // Form states
  const [goalForm, setGoalForm] = useState({
    title: '',
    description: '',
    goal_level: 'ORGANIZATIONAL',
    priority: 'HIGH',
    status: 'ACTIVE',
    start_date: new Date().toISOString().slice(0, 10),
    target_date: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10),
    category: 'STRATEGY',
  });

  const [krForm, setKrForm] = useState({
    title: '',
    description: '',
    measurement_type: 'NUMERIC_INCREASE',
    starting_value: 0,
    current_value: 0,
    target_value: 100,
    unit: '%',
    weight: 1.0,
    due_date: '',
  });

  const [milestoneForm, setMilestoneForm] = useState({
    title: '',
    description: '',
    priority: 'MEDIUM',
    status: 'NOT_STARTED',
    due_date: new Date(Date.now() + 30 * 86400000).toISOString().slice(0, 10),
    notes: '',
  });

  const [checkInForm, setCheckInForm] = useState({
    progress_percent: 0,
    confidence_score: 4,
    summary: '',
    blockers: '',
    next_steps: '',
    support_needed: '',
  });

  const [progressForm, setProgressForm] = useState({
    new_value: 0,
    comment: '',
  });

  // Notification helper
  const notify = (msg) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 4000);
  };

  // Fetch overview & goals
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, goalsRes, msRes] = await Promise.allSettled([
        goalApi.getOverviewAnalytics(),
        goalApi.getGoals(),
        goalApi.getMilestones(),
      ]);

      if (ovRes.status === 'fulfilled' && ovRes.value?.data) {
        setOverview(ovRes.value.data);
      }
      if (goalsRes.status === 'fulfilled' && goalsRes.value?.data?.items) {
        setGoals(goalsRes.value.data.items);
      }
      if (msRes.status === 'fulfilled' && msRes.value?.data) {
        setMilestones(msRes.value.data);
      }
    } catch (err) {
      console.error('Failed to load goals:', err);
      setError('Could not connect to goals service.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Load single goal details
  const selectGoal = async (g) => {
    try {
      const res = await goalApi.getGoalDetail(g.id);
      setSelectedGoal(res.data);
    } catch {
      setSelectedGoal(g);
    }
  };

  // Handlers: Create Goal
  const handleCreateGoal = async (e) => {
    e.preventDefault();
    if (!goalForm.title.trim()) return;
    try {
      await goalApi.createGoal(goalForm);
      setShowGoalModal(false);
      setGoalForm({
        title: '',
        description: '',
        goal_level: 'ORGANIZATIONAL',
        priority: 'HIGH',
        status: 'ACTIVE',
        start_date: new Date().toISOString().slice(0, 10),
        target_date: new Date(Date.now() + 90 * 86400000).toISOString().slice(0, 10),
        category: 'STRATEGY',
      });
      notify('Strategic goal created successfully.');
      fetchData();
    } catch (err) {
      alert(`Error creating goal: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handlers: Create Key Result
  const handleCreateKr = async (e) => {
    e.preventDefault();
    if (!selectedGoal || !krForm.title.trim()) return;
    try {
      await goalApi.createKeyResult(selectedGoal.id, {
        ...krForm,
        starting_value: parseFloat(krForm.starting_value) || 0,
        current_value: parseFloat(krForm.current_value) || parseFloat(krForm.starting_value) || 0,
        target_value: parseFloat(krForm.target_value) || 100,
        weight: parseFloat(krForm.weight) || 1.0,
      });
      setShowKrModal(false);
      setKrForm({
        title: '',
        description: '',
        measurement_type: 'NUMERIC_INCREASE',
        starting_value: 0,
        current_value: 0,
        target_value: 100,
        unit: '%',
        weight: 1.0,
        due_date: '',
      });
      notify('Key result registered and parent goal velocity updated.');
      selectGoal(selectedGoal);
      fetchData();
    } catch (err) {
      alert(`Error adding key result: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handlers: Update KR Progress
  const handleUpdateProgress = async (e) => {
    e.preventDefault();
    if (!activeKrForProgress) return;
    try {
      await goalApi.updateKeyResultProgress(
        activeKrForProgress.id,
        parseFloat(progressForm.new_value) || 0,
        progressForm.comment
      );
      setShowProgressModal(false);
      setActiveKrForProgress(null);
      setProgressForm({ new_value: 0, comment: '' });
      notify('Key result progress updated and audit entry recorded.');
      if (selectedGoal) selectGoal(selectedGoal);
      fetchData();
    } catch (err) {
      alert(`Error updating progress: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handlers: Complete Milestone
  const handleCompleteMilestone = async (mId) => {
    try {
      await goalApi.completeMilestone(mId);
      notify('Milestone marked as completed.');
      if (selectedGoal) selectGoal(selectedGoal);
      fetchData();
    } catch (err) {
      alert(`Could not complete milestone: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Handlers: Submit Check-in
  const handleSubmitCheckIn = async (e) => {
    e.preventDefault();
    if (!selectedGoal || !checkInForm.summary.trim()) return;
    try {
      await goalApi.submitCheckIn(selectedGoal.id, checkInForm);
      setShowCheckInModal(false);
      setCheckInForm({
        progress_percent: selectedGoal.progress_percent || 0,
        confidence_score: 4,
        summary: '',
        blockers: '',
        next_steps: '',
        support_needed: '',
      });
      notify('Progress check-in submitted for leadership review.');
      selectGoal(selectedGoal);
      fetchData();
    } catch (err) {
      alert(`Check-in submission failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  // Filtered goals
  const filteredGoals = goals.filter((g) => {
    if (levelFilter !== 'ALL' && g.goal_level !== levelFilter) return false;
    if (statusFilter !== 'ALL' && g.status !== statusFilter) return false;
    if (healthFilter !== 'ALL' && g.health_status !== healthFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = g.title?.toLowerCase().includes(q);
      const matchDesc = g.description?.toLowerCase().includes(q);
      if (!matchTitle && !matchDesc) return false;
    }
    return true;
  });

  return (
    <div className="goals-dashboard-page" role="main" aria-label="Goals and OKRs Management">
      {/* Top Header */}
      <div className="goals-header-bar">
        <div className="goals-title-group">
          <div className="goals-icon-box">
            <Target size={24} />
          </div>
          <div>
            <h1 className="goals-main-heading">Goals, OKRs & Strategic Milestones</h1>
            <p className="goals-sub-heading">
              Track company objectives, team outcomes, measurable key results, delivery velocity, and critical path milestones.
            </p>
          </div>
        </div>

        <div className="goals-header-actions">
          <button
            type="button"
            className="btn-goals-secondary"
            onClick={fetchData}
            title="Refresh goals data"
          >
            <RefreshCw size={14} className={loading ? 'spin-icon' : ''} />
            <span>Refresh</span>
          </button>
          <button
            type="button"
            className="btn-goals-primary"
            onClick={() => setShowGoalModal(true)}
          >
            <Plus size={16} />
            <span>New Objective</span>
          </button>
        </div>
      </div>

      {actionNotice && (
        <div className="goals-toast-banner" role="status">
          <CheckCircle2 size={16} />
          <span>{actionNotice}</span>
        </div>
      )}

      {/* KPI Cards Row */}
      {overview && (
        <div className="goals-kpi-grid">
          <div className="kpi-metric-card">
            <div className="kpi-icon-wrap blue">
              <Target size={20} />
            </div>
            <div className="kpi-data">
              <span className="kpi-num">{overview.total_goals || 0}</span>
              <span className="kpi-label">Total Objectives</span>
            </div>
            <span className="kpi-badge neutral">{overview.active_goals || 0} Active</span>
          </div>

          <div className="kpi-metric-card">
            <div className="kpi-icon-wrap green">
              <TrendingUp size={20} />
            </div>
            <div className="kpi-data">
              <span className="kpi-num">{overview.average_progress || 0}%</span>
              <span className="kpi-label">Average Progress</span>
            </div>
            <span className="kpi-badge success">{overview.completed_goals || 0} Completed</span>
          </div>

          <div className="kpi-metric-card">
            <div className="kpi-icon-wrap amber">
              <AlertTriangle size={20} />
            </div>
            <div className="kpi-data">
              <span className="kpi-num">
                {(overview.at_risk_goals || 0) + (overview.behind_goals || 0)}
              </span>
              <span className="kpi-label">At Risk / Behind</span>
            </div>
            <span className="kpi-badge warning">{overview.behind_goals || 0} Overdue</span>
          </div>

          <div className="kpi-metric-card">
            <div className="kpi-icon-wrap purple">
              <Flag size={20} />
            </div>
            <div className="kpi-data">
              <span className="kpi-num">{overview.total_milestones || 0}</span>
              <span className="kpi-label">Milestones Tracked</span>
            </div>
            <span className="kpi-badge info">{overview.upcoming_milestones || 0} Upcoming</span>
          </div>
        </div>
      )}

      {/* Main Tab Controls */}
      <div className="goals-tab-nav">
        <button
          type="button"
          className={`goals-tab-btn ${activeTab === 'okrs' ? 'active' : ''}`}
          onClick={() => setActiveTab('okrs')}
        >
          <Layers size={16} />
          <span>Objectives & OKRs</span>
          <span className="tab-count-pill">{goals.length}</span>
        </button>
        <button
          type="button"
          className={`goals-tab-btn ${activeTab === 'milestones' ? 'active' : ''}`}
          onClick={() => setActiveTab('milestones')}
        >
          <Flag size={16} />
          <span>Milestone Roadmap</span>
          <span className="tab-count-pill">{milestones.length}</span>
        </button>
        <button
          type="button"
          className={`goals-tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <PieChart size={16} />
          <span>Health & Distribution</span>
        </button>
      </div>

      {/* ================= TAB 1: OBJECTIVES & OKRS ================= */}
      {activeTab === 'okrs' && (
        <div className="goals-view-container">
          {/* Filters Bar */}
          <div className="goals-filter-bar">
            <div className="search-input-box">
              <Search size={15} />
              <input
                type="text"
                placeholder="Search objectives and key results..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button type="button" className="clear-btn" onClick={() => setSearchQuery('')}>
                  <X size={13} />
                </button>
              )}
            </div>

            <div className="filter-select-group">
              <select value={levelFilter} onChange={(e) => setLevelFilter(e.target.value)}>
                <option value="ALL">All Levels</option>
                <option value="ORGANIZATIONAL">Organizational</option>
                <option value="TEAM">Team</option>
                <option value="INDIVIDUAL">Individual</option>
              </select>

              <select value={healthFilter} onChange={(e) => setHealthFilter(e.target.value)}>
                <option value="ALL">All Health</option>
                <option value="ON_TRACK">On Track</option>
                <option value="AT_RISK">At Risk</option>
                <option value="BEHIND">Behind</option>
                <option value="COMPLETED">Completed</option>
              </select>

              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="DRAFT">Draft</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          {/* Master-Detail Split Grid */}
          <div className="goals-split-layout">
            {/* Left: Goals Cards List */}
            <div className="goals-list-column">
              {filteredGoals.length === 0 ? (
                <div className="empty-goals-card">
                  <Target size={36} />
                  <h3>No matching goals found</h3>
                  <p>Create a strategic objective or adjust your active filters above.</p>
                  <button
                    type="button"
                    className="btn-goals-primary"
                    onClick={() => setShowGoalModal(true)}
                  >
                    <Plus size={15} />
                    <span>Create Objective</span>
                  </button>
                </div>
              ) : (
                filteredGoals.map((g) => {
                  const isSelected = selectedGoal?.id === g.id;
                  return (
                    <div
                      key={g.id}
                      className={`goal-summary-card ${isSelected ? 'selected' : ''}`}
                      onClick={() => selectGoal(g)}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="goal-card-top">
                        <span className={`level-pill level-${g.goal_level?.toLowerCase()}`}>
                          {g.goal_level}
                        </span>
                        <span className={`health-pill health-${g.health_status?.toLowerCase()}`}>
                          {g.health_status?.replace('_', ' ')}
                        </span>
                      </div>

                      <h3 className="goal-card-title">{g.title}</h3>
                      {g.description && <p className="goal-card-desc">{g.description}</p>}

                      {/* Progress Bar */}
                      <div className="goal-progress-section">
                        <div className="progress-labels">
                          <span>Progress</span>
                          <strong>{Math.round(g.progress_percent || 0)}%</strong>
                        </div>
                        <div className="progress-track">
                          <div
                            className={`progress-fill health-${g.health_status?.toLowerCase()}`}
                            style={{ width: `${Math.min(100, g.progress_percent || 0)}%` }}
                          />
                        </div>
                      </div>

                      <div className="goal-card-meta">
                        <span title="Key results attached">
                          <CheckSquare size={13} /> {g.key_results_count || 0} KRs
                        </span>
                        <span title="Milestones attached">
                          <Flag size={13} /> {g.milestones_count || 0} Milestones
                        </span>
                        {g.target_date && (
                          <span title="Target completion date">
                            <Calendar size={13} /> {g.target_date.slice(0, 10)}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            {/* Right: Selected Goal Detail Panel */}
            <div className="goal-detail-column">
              {selectedGoal ? (
                <div className="goal-detail-pane">
                  <div className="pane-header">
                    <div>
                      <div className="pane-badges-row">
                        <span className={`level-pill level-${selectedGoal.goal_level?.toLowerCase()}`}>
                          {selectedGoal.goal_level}
                        </span>
                        <span className={`health-pill health-${selectedGoal.health_status?.toLowerCase()}`}>
                          {selectedGoal.health_status?.replace('_', ' ')}
                        </span>
                        <span className="priority-pill">{selectedGoal.priority}</span>
                      </div>
                      <h2 className="pane-goal-title">{selectedGoal.title}</h2>
                    </div>

                    <div className="pane-top-actions">
                      <button
                        type="button"
                        className="btn-pane-action"
                        onClick={() => setShowCheckInModal(true)}
                        title="Submit progress check-in"
                      >
                        <Send size={14} />
                        <span>Check In</span>
                      </button>
                    </div>
                  </div>

                  {selectedGoal.health_reason && (
                    <div className={`health-explanation-box health-${selectedGoal.health_status?.toLowerCase()}`}>
                      <Sparkles size={16} />
                      <p>
                        <strong>Health Diagnosis:</strong> {selectedGoal.health_reason}
                      </p>
                    </div>
                  )}

                  {/* Overall Progress Widget */}
                  <div className="pane-progress-widget">
                    <div className="widget-header">
                      <span>Overall Objective Completion</span>
                      <h2>{Math.round(selectedGoal.progress_percent || 0)}%</h2>
                    </div>
                    <div className="progress-track big">
                      <div
                        className={`progress-fill health-${selectedGoal.health_status?.toLowerCase()}`}
                        style={{ width: `${Math.min(100, selectedGoal.progress_percent || 0)}%` }}
                      />
                    </div>
                  </div>

                  {/* Section: Key Results */}
                  <div className="pane-section">
                    <div className="section-header-row">
                      <div className="sec-title-wrap">
                        <CheckSquare size={16} />
                        <h3>Key Results ({selectedGoal.key_results?.length || 0})</h3>
                      </div>
                      <button
                        type="button"
                        className="btn-small-add"
                        onClick={() => setShowKrModal(true)}
                      >
                        <Plus size={13} /> Add Key Result
                      </button>
                    </div>

                    <div className="krs-list">
                      {!selectedGoal.key_results || selectedGoal.key_results.length === 0 ? (
                        <div className="pane-empty-notice">
                          No key results attached yet. Add measurable key results to track objective progress.
                        </div>
                      ) : (
                        selectedGoal.key_results.map((kr) => (
                          <div key={kr.id} className="kr-row-card">
                            <div className="kr-info-left">
                              <span className="kr-type-badge">{kr.measurement_type?.replace('_', ' ')}</span>
                              <h4 className="kr-title">{kr.title}</h4>
                              <div className="kr-values-meta">
                                <span>
                                  Start: {kr.starting_value} {kr.unit}
                                </span>
                                <span>
                                  Current: <strong>{kr.current_value} {kr.unit}</strong>
                                </span>
                                <span>
                                  Target: {kr.target_value} {kr.unit}
                                </span>
                              </div>
                            </div>

                            <div className="kr-progress-col">
                              <span className="kr-pct">{Math.round(kr.progress_percent || 0)}%</span>
                              <div className="progress-track small">
                                <div
                                  className="progress-fill primary"
                                  style={{ width: `${Math.min(100, kr.progress_percent || 0)}%` }}
                                />
                              </div>
                              <button
                                type="button"
                                className="btn-update-kr"
                                onClick={() => {
                                  setActiveKrForProgress(kr);
                                  setProgressForm({ new_value: kr.current_value, comment: '' });
                                  setShowProgressModal(true);
                                }}
                              >
                                Update Value
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Section: Milestones */}
                  <div className="pane-section">
                    <div className="section-header-row">
                      <div className="sec-title-wrap">
                        <Flag size={16} />
                        <h3>Milestones ({selectedGoal.milestones?.length || 0})</h3>
                      </div>
                      <button
                        type="button"
                        className="btn-small-add"
                        onClick={() => setShowMilestoneModal(true)}
                      >
                        <Plus size={13} /> Add Milestone
                      </button>
                    </div>

                    <div className="milestones-list">
                      {!selectedGoal.milestones || selectedGoal.milestones.length === 0 ? (
                        <div className="pane-empty-notice">No milestones defined for this goal.</div>
                      ) : (
                        selectedGoal.milestones.map((m) => {
                          const isDone = m.status === 'COMPLETED';
                          return (
                            <div key={m.id} className={`milestone-row-item ${isDone ? 'completed' : ''}`}>
                              <button
                                type="button"
                                className={`milestone-check-btn ${isDone ? 'checked' : ''}`}
                                onClick={() => !isDone && handleCompleteMilestone(m.id)}
                                title={isDone ? 'Milestone Completed' : 'Mark as Completed'}
                              >
                                <CheckCircle2 size={18} />
                              </button>
                              <div className="milestone-details">
                                <span className={`m-title ${isDone ? 'done-text' : ''}`}>{m.title}</span>
                                {m.due_date && (
                                  <span className="m-due">
                                    <Clock size={12} /> Due: {m.due_date.slice(0, 10)}
                                  </span>
                                )}
                              </div>
                              <span className={`status-tag status-${m.status?.toLowerCase()}`}>
                                {m.status}
                              </span>
                            </div>
                          );
                        })
                      )}
                    </div>
                  </div>

                  {/* Section: Check-In Audit Stream */}
                  <div className="pane-section">
                    <div className="sec-title-wrap">
                      <Calendar size={16} />
                      <h3>Recent Check-Ins ({selectedGoal.check_ins?.length || 0})</h3>
                    </div>

                    <div className="check-ins-stream">
                      {!selectedGoal.check_ins || selectedGoal.check_ins.length === 0 ? (
                        <div className="pane-empty-notice">No check-ins submitted yet.</div>
                      ) : (
                        selectedGoal.check_ins.map((chk) => (
                          <div key={chk.id} className="checkin-stream-card">
                            <div className="chk-top-row">
                              <span className="chk-author">
                                {chk.user_name || 'Team Member'}
                              </span>
                              <span className="chk-conf">
                                Confidence: {'★'.repeat(chk.confidence_score || 4)}
                              </span>
                              <span className="chk-date">{chk.created_at?.slice(0, 10)}</span>
                            </div>
                            <p className="chk-summary">{chk.summary}</p>
                            {chk.blockers && (
                              <div className="chk-blocker-alert">
                                <strong>Blocker:</strong> {chk.blockers}
                              </div>
                            )}
                            {chk.reviewer_feedback && (
                              <div className="chk-feedback-box">
                                <strong>Leadership Feedback:</strong> {chk.reviewer_feedback}
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="pane-placeholder">
                  <Target size={48} />
                  <h3>Select an objective</h3>
                  <p>Click on any objective from the list to inspect key results, velocity metrics, and milestones.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ================= TAB 2: MILESTONE ROADMAP ================= */}
      {activeTab === 'milestones' && (
        <div className="milestones-roadmap-view">
          <div className="roadmap-grid">
            {milestones.length === 0 ? (
              <div className="empty-goals-card">
                <Flag size={40} />
                <h3>No milestones recorded</h3>
                <p>Attach milestones to objectives and projects to track your critical path roadmap.</p>
              </div>
            ) : (
              milestones.map((m) => {
                const isCompleted = m.status === 'COMPLETED';
                return (
                  <div key={m.id} className={`roadmap-milestone-card ${isCompleted ? 'done' : ''}`}>
                    <div className="m-card-header">
                      <span className={`status-tag status-${m.status?.toLowerCase()}`}>
                        {m.status}
                      </span>
                      {m.due_date && (
                        <span className="m-card-date">
                          <Calendar size={13} /> {m.due_date.slice(0, 10)}
                        </span>
                      )}
                    </div>
                    <h3 className="m-card-title">{m.title}</h3>
                    {m.goal_title && <p className="m-card-goal">Objective: {m.goal_title}</p>}
                    {m.blocked_reason && (
                      <div className="m-card-blocked">
                        <AlertTriangle size={14} />
                        <span>{m.blocked_reason}</span>
                      </div>
                    )}
                    <div className="m-card-footer">
                      <span className="m-priority">Priority: {m.priority}</span>
                      {!isCompleted && (
                        <button
                          type="button"
                          className="btn-complete-ms"
                          onClick={() => handleCompleteMilestone(m.id)}
                        >
                          Complete
                        </button>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* ================= TAB 3: HEALTH & DISTRIBUTION ================= */}
      {activeTab === 'analytics' && overview && (
        <div className="goals-analytics-view">
          <div className="analytics-charts-grid">
            {/* Level Distribution */}
            <div className="analytics-card">
              <h3>Objectives by Level</h3>
              <div className="dist-list">
                {Object.entries(overview.level_breakdown || {}).map(([lvl, count]) => (
                  <div key={lvl} className="dist-row">
                    <span className="dist-label">{lvl}</span>
                    <div className="dist-bar-track">
                      <div
                        className="dist-bar-fill"
                        style={{
                          width: `${overview.total_goals ? (count / overview.total_goals) * 100 : 0}%`,
                        }}
                      />
                    </div>
                    <span className="dist-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Health Distribution */}
            <div className="analytics-card">
              <h3>Goal Health Breakdown</h3>
              <div className="dist-list">
                {Object.entries(overview.health_breakdown || {}).map(([h, count]) => (
                  <div key={h} className="dist-row">
                    <span className={`health-pill health-${h.toLowerCase()}`}>{h.replace('_', ' ')}</span>
                    <div className="dist-bar-track">
                      <div
                        className={`dist-bar-fill health-${h.toLowerCase()}`}
                        style={{
                          width: `${overview.total_goals ? (count / overview.total_goals) * 100 : 0}%`,
                        }}
                      />
                    </div>
                    <span className="dist-count">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= MODAL: CREATE GOAL ================= */}
      {showGoalModal && (
        <div className="modal-overlay" onClick={() => setShowGoalModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Strategic Objective</h3>
              <button type="button" onClick={() => setShowGoalModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreateGoal} className="modal-form">
              <div className="form-group">
                <label>Objective Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Elevate Core Platform Reliability & Performance"
                  value={goalForm.title}
                  onChange={(e) => setGoalForm({ ...goalForm, title: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  rows={3}
                  placeholder="Explain why this goal matters and what success looks like..."
                  value={goalForm.description}
                  onChange={(e) => setGoalForm({ ...goalForm, description: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Goal Level</label>
                  <select
                    value={goalForm.goal_level}
                    onChange={(e) => setGoalForm({ ...goalForm, goal_level: e.target.value })}
                  >
                    <option value="ORGANIZATIONAL">Organizational</option>
                    <option value="TEAM">Team</option>
                    <option value="INDIVIDUAL">Individual</option>
                    <option value="PROJECT">Project-Linked</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Priority</label>
                  <select
                    value={goalForm.priority}
                    onChange={(e) => setGoalForm({ ...goalForm, priority: e.target.value })}
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={goalForm.start_date}
                    onChange={(e) => setGoalForm({ ...goalForm, start_date: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Target Deadline</label>
                  <input
                    type="date"
                    value={goalForm.target_date}
                    onChange={(e) => setGoalForm({ ...goalForm, target_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowGoalModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-modal-submit">
                  Create Objective
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: ADD KEY RESULT ================= */}
      {showKrModal && selectedGoal && (
        <div className="modal-overlay" onClick={() => setShowKrModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Add Measurable Key Result</h3>
              <button type="button" onClick={() => setShowKrModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreateKr} className="modal-form">
              <div className="form-group">
                <label>Key Result Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Reduce API p95 response time to under 80ms"
                  value={krForm.title}
                  onChange={(e) => setKrForm({ ...krForm, title: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Measurement Formula</label>
                  <select
                    value={krForm.measurement_type}
                    onChange={(e) => setKrForm({ ...krForm, measurement_type: e.target.value })}
                  >
                    <option value="NUMERIC_INCREASE">Numeric Increase (Higher is better)</option>
                    <option value="NUMERIC_DECREASE">Numeric Decrease (Lower is better)</option>
                    <option value="PERCENTAGE">Percentage (%)</option>
                    <option value="BINARY">Binary Completion (Done / Not Done)</option>
                    <option value="TASK_COMPLETION">Task Completion Sync</option>
                    <option value="MILESTONE">Milestone Progress Sync</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Unit of Measure</label>
                  <input
                    type="text"
                    placeholder="e.g. %, ms, $, releases"
                    value={krForm.unit}
                    onChange={(e) => setKrForm({ ...krForm, unit: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Starting Value</label>
                  <input
                    type="number"
                    step="any"
                    value={krForm.starting_value}
                    onChange={(e) => setKrForm({ ...krForm, starting_value: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Target Value</label>
                  <input
                    type="number"
                    step="any"
                    value={krForm.target_value}
                    onChange={(e) => setKrForm({ ...krForm, target_value: e.target.value })}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowKrModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-modal-submit">
                  Save Key Result
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: UPDATE KR PROGRESS ================= */}
      {showProgressModal && activeKrForProgress && (
        <div className="modal-overlay" onClick={() => setShowProgressModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Update Progress: {activeKrForProgress.title}</h3>
              <button type="button" onClick={() => setShowProgressModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleUpdateProgress} className="modal-form">
              <div className="form-group">
                <label>
                  New Current Value ({activeKrForProgress.unit}) *
                </label>
                <input
                  type="number"
                  step="any"
                  required
                  value={progressForm.new_value}
                  onChange={(e) => setProgressForm({ ...progressForm, new_value: e.target.value })}
                />
                <span className="field-hint">
                  Target is {activeKrForProgress.target_value} {activeKrForProgress.unit}
                </span>
              </div>

              <div className="form-group">
                <label>Progress Notes / Context</label>
                <textarea
                  rows={3}
                  placeholder="Describe what work was delivered to achieve this milestone..."
                  value={progressForm.comment}
                  onChange={(e) => setProgressForm({ ...progressForm, comment: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowProgressModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-modal-submit">
                  Record Progress
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= MODAL: SUBMIT CHECK-IN ================= */}
      {showCheckInModal && selectedGoal && (
        <div className="modal-overlay" onClick={() => setShowCheckInModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Goal Check-In: {selectedGoal.title}</h3>
              <button type="button" onClick={() => setShowCheckInModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleSubmitCheckIn} className="modal-form">
              <div className="form-group">
                <label>Executive Progress Summary *</label>
                <textarea
                  rows={3}
                  required
                  placeholder="Summarize key accomplishments and delivery momentum..."
                  value={checkInForm.summary}
                  onChange={(e) => setCheckInForm({ ...checkInForm, summary: e.target.value })}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Self-Assessed Progress (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={checkInForm.progress_percent}
                    onChange={(e) => setCheckInForm({ ...checkInForm, progress_percent: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label>Confidence Score (1 to 5)</label>
                  <select
                    value={checkInForm.confidence_score}
                    onChange={(e) => setCheckInForm({ ...checkInForm, confidence_score: parseInt(e.target.value, 10) })}
                  >
                    <option value={5}>5 - High Confidence</option>
                    <option value={4}>4 - Good Velocity</option>
                    <option value={3}>3 - Moderate Risk</option>
                    <option value={2}>2 - Severe Obstacles</option>
                    <option value={1}>1 - Blocked</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Active Blockers / Challenges</label>
                <textarea
                  rows={2}
                  placeholder="Describe any technical, staffing, or vendor blockers..."
                  value={checkInForm.blockers}
                  onChange={(e) => setCheckInForm({ ...checkInForm, blockers: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Next Immediate Priorities</label>
                <input
                  type="text"
                  placeholder="What is the team executing next sprint?"
                  value={checkInForm.next_steps}
                  onChange={(e) => setCheckInForm({ ...checkInForm, next_steps: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowCheckInModal(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-modal-submit">
                  Submit Check-In
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default GoalsDashboard;
