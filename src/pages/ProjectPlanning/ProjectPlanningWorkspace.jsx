import React, { useState, useEffect, useMemo } from 'react';
import {
  Calendar,
  Layers,
  GitBranch,
  TrendingUp,
  DollarSign,
  Play,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  Plus,
  Trash2,
  RefreshCw,
  Search,
  Filter,
  BarChart2,
  FileText,
  ShieldCheck,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Target,
  ArrowRight,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import { projectPlanningApi } from '../../services/projectPlanningApi';
import { apiClient } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import './ProjectPlanningWorkspace.css';

export function ProjectPlanningWorkspace() {
  const { isAuthenticated, user } = useAuth();
  const { tasks } = useTasks();

  // Navigation & Sub-views
  const [activeTab, setActiveTab] = useState('gantt'); // gantt, cpm, dependencies, baselines, budget, simulation, forecast
  const [zoomLevel, setZoomLevel] = useState('week'); // day, week, month
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Loading & status
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [actionNotice, setActionNotice] = useState(null);

  // Project context
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  // Planning data state
  const [planningData, setPlanningData] = useState(null);
  const [dependencies, setDependencies] = useState([]);
  const [criticalPath, setCriticalPath] = useState(null);
  const [baselines, setBaselines] = useState([]);
  const [budget, setBudget] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [scenarios, setScenarios] = useState([]);

  // Modals state
  const [showDepModal, setShowDepModal] = useState(false);
  const [showBaselineModal, setShowBaselineModal] = useState(false);
  const [showCostModal, setShowCostModal] = useState(false);
  const [showScenarioModal, setShowScenarioModal] = useState(false);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [activeComparison, setActiveComparison] = useState(null);

  // Form states
  const [depForm, setDepForm] = useState({
    task_id: '',
    depends_on_task_id: '',
    dependency_type: 'FINISH_TO_START',
    lag_duration: 0,
    lag_unit: 'DAYS',
  });
  const [baselineForm, setBaselineForm] = useState({ name: '', description: '' });
  const [costForm, setCostForm] = useState({ description: '', amount: '', record_type: 'ACTUAL', currency: 'USD' });
  const [scenarioForm, setScenarioForm] = useState({ name: '', description: '' });

  // 1. Initial Load: Fetch Projects
  useEffect(() => {
    async function loadProjects() {
      try {
        setLoading(true);
        const res = await apiClient.get('/projects').catch(() => []);
        const list = Array.isArray(res) ? res : res?.items || [];
        if (list.length > 0) {
          setProjects(list);
          setSelectedProjectId(list[0].id);
        } else {
          // Fallback sample project for instant interaction
          const sample = { id: 1, name: 'Core Platform Engineering', status: 'ACTIVE' };
          setProjects([sample]);
          setSelectedProjectId(1);
        }
      } catch (err) {
        console.error('Failed to load projects:', err);
      } finally {
        setLoading(false);
      }
    }
    loadProjects();
  }, []);

  // 2. Fetch Planning Data when Project Changes
  useEffect(() => {
    if (selectedProjectId) {
      loadProjectPlanning(selectedProjectId);
    }
  }, [selectedProjectId]);

  const loadProjectPlanning = async (projId) => {
    try {
      setLoading(true);
      const [planRes, depRes, cpmRes, baseRes, budRes, fcastRes, scenRes] = await Promise.all([
        projectPlanningApi.getPlanningOverview(projId).catch(() => null),
        projectPlanningApi.getDependencies(projId).catch(() => []),
        projectPlanningApi.getCriticalPath(projId).catch(() => null),
        projectPlanningApi.getBaselines(projId).catch(() => []),
        projectPlanningApi.getBudget(projId).catch(() => null),
        projectPlanningApi.getForecast(projId).catch(() => null),
        projectPlanningApi.getScenarios(projId).catch(() => []),
      ]);

      setPlanningData(planRes);
      setDependencies(Array.isArray(depRes) ? depRes : []);
      setCriticalPath(cpmRes);
      setBaselines(Array.isArray(baseRes) ? baseRes : []);
      setBudget(budRes);
      setForecast(fcastRes);
      setScenarios(Array.isArray(scenRes) ? scenRes : []);
    } catch (err) {
      console.error('Failed to load planning overview:', err);
    } finally {
      setLoading(false);
    }
  };

  const notify = (msg, type = 'success') => {
    setActionNotice({ text: msg, type });
    setTimeout(() => setActionNotice(null), 4000);
  };

  // Recalculate CPM
  const handleRecalculateCPM = async () => {
    if (!selectedProjectId) return;
    try {
      setRecalculating(true);
      const res = await projectPlanningApi.recalculateCriticalPath(selectedProjectId);
      setCriticalPath(res);
      const fcast = await projectPlanningApi.getForecast(selectedProjectId);
      setForecast(fcast);
      notify('Critical path and schedule forecasts recalculated successfully.');
    } catch (err) {
      notify('Failed to recalculate critical path: ' + err.message, 'error');
    } finally {
      setRecalculating(false);
    }
  };

  // Create Dependency
  const handleCreateDependency = async (e) => {
    e.preventDefault();
    if (!depForm.task_id || !depForm.depends_on_task_id) {
      notify('Please select both tasks.', 'error');
      return;
    }
    try {
      await projectPlanningApi.createDependency(selectedProjectId, depForm);
      notify('Task dependency linked successfully.');
      setShowDepModal(false);
      setDepForm({ task_id: '', depends_on_task_id: '', dependency_type: 'FINISH_TO_START', lag_duration: 0, lag_unit: 'DAYS' });
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Delete Dependency
  const handleDeleteDependency = async (depId) => {
    try {
      await projectPlanningApi.deleteDependency(depId);
      notify('Dependency removed.');
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify('Failed to remove dependency: ' + err.message, 'error');
    }
  };

  // Create Baseline
  const handleCreateBaseline = async (e) => {
    e.preventDefault();
    if (!baselineForm.name.trim()) return;
    try {
      await projectPlanningApi.createBaseline(selectedProjectId, baselineForm);
      notify('Project baseline snapshot captured.');
      setShowBaselineModal(false);
      setBaselineForm({ name: '', description: '' });
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Compare Baseline
  const handleOpenComparison = async (bId) => {
    try {
      const cmp = await projectPlanningApi.compareBaseline(bId);
      setActiveComparison(cmp);
      setShowComparisonModal(true);
    } catch (err) {
      notify('Failed to load baseline comparison: ' + err.message, 'error');
    }
  };

  // Record Cost
  const handleRecordCost = async (e) => {
    e.preventDefault();
    if (!costForm.description || !costForm.amount) return;
    try {
      await projectPlanningApi.recordCost(selectedProjectId, {
        description: costForm.description,
        amount: parseFloat(costForm.amount),
        record_type: costForm.record_type,
        currency: costForm.currency,
      });
      notify('Cost record added to budget.');
      setShowCostModal(false);
      setCostForm({ description: '', amount: '', record_type: 'ACTUAL', currency: 'USD' });
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Create Scenario
  const handleCreateScenario = async (e) => {
    e.preventDefault();
    if (!scenarioForm.name.trim()) return;
    try {
      await projectPlanningApi.createScenario(selectedProjectId, scenarioForm);
      notify('What-if simulation scenario created.');
      setShowScenarioModal(false);
      setScenarioForm({ name: '', description: '' });
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Run Simulation
  const handleRunSimulation = async (scenId) => {
    try {
      const res = await projectPlanningApi.simulateScenario(scenId);
      notify(`Simulation complete: ${res.outcomes?.variance_from_current_days >= 0 ? '+' : ''}${res.outcomes?.variance_from_current_days} days variance.`);
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Apply Scenario
  const handleApplyScenario = async (scenId) => {
    if (!window.confirm('Are you sure you want to apply this scenario? It will update real project task dates and estimates.')) {
      return;
    }
    try {
      await projectPlanningApi.applyScenario(scenId);
      notify('Scenario changes successfully applied to production project schedule.');
      loadProjectPlanning(selectedProjectId);
    } catch (err) {
      notify(err.response?.data?.detail || err.message, 'error');
    }
  };

  // Filtered Tasks for Gantt
  const filteredTasks = useMemo(() => {
    const list = tasks || [];
    return list.filter((t) => {
      const matchQ = t.title.toLowerCase().includes(searchQuery.toLowerCase());
      const matchS = statusFilter === 'ALL' || t.status.toLowerCase() === statusFilter.toLowerCase();
      return matchQ && matchS;
    });
  }, [tasks, searchQuery, statusFilter]);

  const scheduleHealth = planningData?.schedule?.schedule_health || 'ON_TRACK';

  return (
    <div className="project-planning-workspace" role="main">
      {/* Action Notification Banner */}
      {actionNotice && (
        <div className={`action-notice-toast ${actionNotice.type}`} role="alert">
          {actionNotice.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle2 size={16} />}
          <span>{actionNotice.text}</span>
        </div>
      )}

      {/* Top Header & Project Selection */}
      <div className="planning-header">
        <div className="header-left">
          <div className="header-title-row">
            <h1 className="planning-page-title">Advanced Project Planning & Scheduling</h1>
            <span className={`health-pill ${scheduleHealth.toLowerCase()}`}>
              {scheduleHealth === 'ON_TRACK' && <CheckCircle2 size={13} />}
              {scheduleHealth === 'AT_RISK' && <AlertTriangle size={13} />}
              {scheduleHealth === 'DELAYED' && <Clock size={13} />}
              {scheduleHealth === 'CRITICAL' && <AlertCircle size={13} />}
              <span>{scheduleHealth.replace('_', ' ')}</span>
            </span>
          </div>
          <p className="planning-page-subtitle">
            Gantt scheduling, critical path method (CPM), dependency acyclic DAGs, baselines, and what-if simulations.
          </p>
        </div>

        <div className="header-actions">
          {/* Project Dropdown Selector */}
          <div className="project-selector-wrap">
            <label htmlFor="planning-proj-select">Active Project:</label>
            <select
              id="planning-proj-select"
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="btn-recalc"
            onClick={handleRecalculateCPM}
            disabled={recalculating}
            title="Recalculate Critical Path & Dates"
          >
            <RefreshCw size={14} className={recalculating ? 'spinning' : ''} />
            <span>Recalculate CPM</span>
          </button>
        </div>
      </div>

      {/* KPI Overview Metric Cards */}
      <div className="planning-kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon-wrap primary">
            <Layers size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Project Tasks</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{planningData?.tasks_summary?.total ?? tasks.length}</span>
              <span className="kpi-sub">
                {planningData?.tasks_summary?.completed ?? 0} completed
              </span>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon-wrap critical">
            <GitBranch size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Critical Path Duration</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{criticalPath?.critical_path_duration_days ?? 0} days</span>
              <span className="kpi-sub highlight">
                {criticalPath?.critical_tasks_count ?? 0} zero-float tasks
              </span>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon-wrap warning">
            <Clock size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Forecast Completion</span>
            <div className="kpi-value-row">
              <span className="kpi-value">{forecast?.forecast_completion_date || 'On Target'}</span>
              <span className={`kpi-sub ${forecast?.schedule_variance_days > 0 ? 'text-danger' : 'text-success'}`}>
                {forecast?.schedule_variance_days > 0 ? `+${forecast.schedule_variance_days}d variance` : 'No delay'}
              </span>
            </div>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon-wrap success">
            <DollarSign size={18} />
          </div>
          <div className="kpi-content">
            <span className="kpi-label">Budget & Costs</span>
            <div className="kpi-value-row">
              <span className="kpi-value">
                ${(budget?.actual_cost ?? 0).toLocaleString()} / ${(budget?.total_budget ?? 0).toLocaleString()}
              </span>
              <span className={`kpi-sub ${budget?.is_over_budget ? 'text-danger' : 'text-muted'}`}>
                ${(budget?.remaining_budget ?? 0).toLocaleString()} remaining
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs */}
      <div className="planning-tab-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'gantt' ? 'active' : ''}`}
          onClick={() => setActiveTab('gantt')}
        >
          <Calendar size={15} />
          <span>Interactive Gantt Chart</span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'cpm' ? 'active' : ''}`}
          onClick={() => setActiveTab('cpm')}
        >
          <GitBranch size={15} />
          <span>Critical Path (CPM)</span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'dependencies' ? 'active' : ''}`}
          onClick={() => setActiveTab('dependencies')}
        >
          <Target size={15} />
          <span>Dependencies ({dependencies.length})</span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'baselines' ? 'active' : ''}`}
          onClick={() => setActiveTab('baselines')}
        >
          <ShieldCheck size={15} />
          <span>Baselines ({baselines.length})</span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'budget' ? 'active' : ''}`}
          onClick={() => setActiveTab('budget')}
        >
          <DollarSign size={15} />
          <span>Budget & Costs</span>
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'simulation' ? 'active' : ''}`}
          onClick={() => setActiveTab('simulation')}
        >
          <Sparkles size={15} />
          <span>What-If Simulations ({scenarios.length})</span>
        </button>
      </div>

      {/* ================= TAB 1: GANTT CHART ================= */}
      {activeTab === 'gantt' && (
        <div className="gantt-view-container">
          {/* Gantt Controls */}
          <div className="gantt-toolbar">
            <div className="toolbar-search">
              <Search size={14} />
              <input
                type="text"
                placeholder="Search tasks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="toolbar-actions">
              <div className="zoom-toggles">
                <button
                  type="button"
                  className={`zoom-btn ${zoomLevel === 'day' ? 'active' : ''}`}
                  onClick={() => setZoomLevel('day')}
                >
                  Day
                </button>
                <button
                  type="button"
                  className={`zoom-btn ${zoomLevel === 'week' ? 'active' : ''}`}
                  onClick={() => setZoomLevel('week')}
                >
                  Week
                </button>
                <button
                  type="button"
                  className={`zoom-btn ${zoomLevel === 'month' ? 'active' : ''}`}
                  onClick={() => setZoomLevel('month')}
                >
                  Month
                </button>
              </div>

              <button
                type="button"
                className="btn-create-dep"
                onClick={() => setShowDepModal(true)}
              >
                <Plus size={14} />
                <span>Add Dependency</span>
              </button>
            </div>
          </div>

          {/* Gantt Matrix Grid */}
          <div className="gantt-chart-table-wrap">
            <table className="gantt-table">
              <thead>
                <tr>
                  <th style={{ width: '260px' }}>Task & Priority</th>
                  <th style={{ width: '90px' }}>Duration</th>
                  <th style={{ width: '100px' }}>Status</th>
                  <th style={{ width: '110px' }}>Progress</th>
                  <th>Timeline Schedule (CPM Forward & Backward Pass)</th>
                </tr>
              </thead>
              <tbody>
                {filteredTasks.map((t, idx) => {
                  const scheduleItem = criticalPath?.tasks_schedule?.[t.id];
                  const isCrit = scheduleItem?.is_critical;
                  const dur = scheduleItem?.duration_days || (t.estimated_duration_minutes ? Math.round(t.estimated_duration_minutes / 480) || 1 : 1);
                  const progress = t.progress_percent || (t.status === 'Completed' ? 100 : t.status === 'In Progress' ? 50 : 0);

                  return (
                    <tr key={t.id} className={isCrit ? 'critical-row' : ''}>
                      <td>
                        <div className="gantt-task-cell">
                          {isCrit && <span className="crit-badge" title="Critical Path Task: Zero Total Float">CRIT</span>}
                          <span className="gantt-task-name">{t.title}</span>
                        </div>
                      </td>
                      <td>
                        <span className="gantt-meta-text">{dur}d</span>
                      </td>
                      <td>
                        <span className={`status-pill ${t.status.toLowerCase().replace(' ', '-')}`}>
                          {t.status}
                        </span>
                      </td>
                      <td>
                        <div className="progress-cell">
                          <div className="mini-progress-bar">
                            <div className="mini-progress-fill" style={{ width: `${progress}%` }} />
                          </div>
                          <span className="progress-num">{progress}%</span>
                        </div>
                      </td>
                      <td>
                        {/* Visual Gantt Bar */}
                        <div className="gantt-bar-lane">
                          <div
                            className={`gantt-bar ${isCrit ? 'critical-bar' : 'normal-bar'}`}
                            style={{
                              marginLeft: `${Math.min(70, idx * 8)}%`,
                              width: `${Math.max(12, Math.min(30, dur * 8))}%`,
                            }}
                          >
                            <span className="gantt-bar-label">
                              {scheduleItem?.calculated_start || 'Day ' + (idx + 1)}
                            </span>
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ================= TAB 2: CRITICAL PATH METHOD ================= */}
      {activeTab === 'cpm' && (
        <div className="cpm-view-container">
          <div className="cpm-header-banner">
            <div className="cpm-banner-info">
              <h3>Critical Path Analysis (Zero Float Sequence)</h3>
              <p>
                Tasks on the critical path directly dictate the total project completion timeline. Any delay in these tasks produces an immediate schedule slip.
              </p>
            </div>
            <div className="cpm-banner-stats">
              <span className="stat-label">Path Duration:</span>
              <span className="stat-value">{criticalPath?.critical_path_duration_days || 0} Working Days</span>
            </div>
          </div>

          <div className="cpm-chain-list">
            {criticalPath?.critical_path?.map((item, index) => (
              <div key={item.task_id} className="cpm-node-card">
                <div className="cpm-node-index">Step {index + 1}</div>
                <div className="cpm-node-body">
                  <div className="cpm-node-title-row">
                    <span className="cpm-node-title">{item.title}</span>
                    <span className="cpm-float-tag">Total Float: {item.total_float_days}d</span>
                  </div>
                  <div className="cpm-node-metrics">
                    <span><strong>Duration:</strong> {item.duration_days}d</span>
                    <span><strong>ES:</strong> Day {item.es_days}</span>
                    <span><strong>EF:</strong> Day {item.ef_days}</span>
                    <span><strong>LS:</strong> Day {item.ls_days}</span>
                    <span><strong>LF:</strong> Day {item.lf_days}</span>
                    <span><strong>Calculated:</strong> {item.calculated_start} → {item.calculated_end}</span>
                  </div>
                </div>
                {index < criticalPath.critical_path.length - 1 && (
                  <div className="cpm-arrow">
                    <ArrowRight size={18} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ================= TAB 3: DEPENDENCIES ================= */}
      {activeTab === 'dependencies' && (
        <div className="dependencies-view-container">
          <div className="dependencies-top-bar">
            <h3>Task Predecessor & Successor Graph</h3>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowDepModal(true)}
            >
              <Plus size={14} />
              <span>Link Task Dependency</span>
            </button>
          </div>

          {dependencies.length === 0 ? (
            <div className="empty-state-card">
              <GitBranch size={36} />
              <h4>No Task Dependencies Configured</h4>
              <p>Link task dependencies to calculate critical paths, float, and automated delivery schedules.</p>
            </div>
          ) : (
            <table className="dep-table">
              <thead>
                <tr>
                  <th>Predecessor (Depends On)</th>
                  <th>Dependency Type</th>
                  <th>Successor (Target Task)</th>
                  <th>Lag Duration</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {dependencies.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <strong>{tasks.find((t) => t.id === d.depends_on_task_id)?.title || d.depends_on_task_id}</strong>
                    </td>
                    <td>
                      <span className="dep-type-pill">{d.dependency_type}</span>
                    </td>
                    <td>
                      <strong>{tasks.find((t) => t.id === d.task_id)?.title || d.task_id}</strong>
                    </td>
                    <td>
                      <span>{d.lag_duration} {d.lag_unit}</span>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn-delete-icon"
                        onClick={() => handleDeleteDependency(d.id)}
                        title="Delete Dependency"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* ================= TAB 4: BASELINES ================= */}
      {activeTab === 'baselines' && (
        <div className="baselines-view-container">
          <div className="dependencies-top-bar">
            <div>
              <h3>Historical Project Baselines</h3>
              <p>Approved schedule snapshots saved for variance analysis and audit compliance.</p>
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowBaselineModal(true)}
            >
              <Plus size={14} />
              <span>Capture New Baseline</span>
            </button>
          </div>

          {baselines.length === 0 ? (
            <div className="empty-state-card">
              <ShieldCheck size={36} />
              <h4>No Baselines Captured Yet</h4>
              <p>Create a baseline to record the original approved schedule and compare live progress variance.</p>
            </div>
          ) : (
            <div className="baselines-grid">
              {baselines.map((b) => (
                <div key={b.id} className="baseline-card">
                  <div className="baseline-card-header">
                    <span className="version-pill">Version {b.version}</span>
                    <span className="baseline-date">{b.created_at?.slice(0, 10)}</span>
                  </div>
                  <h4 className="baseline-name">{b.name}</h4>
                  {b.description && <p className="baseline-desc">{b.description}</p>}
                  <div className="baseline-stats">
                    <span><strong>Duration:</strong> {b.total_duration_days} days</span>
                    <span><strong>Effort:</strong> {b.total_estimated_effort_hours}h</span>
                    <span><strong>Budget:</strong> ${b.total_budget?.toLocaleString()}</span>
                  </div>
                  <button
                    type="button"
                    className="btn-compare"
                    onClick={() => handleOpenComparison(b.id)}
                  >
                    <span>Compare with Current Plan</span>
                    <ChevronRight size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ================= TAB 5: BUDGET & COSTS ================= */}
      {activeTab === 'budget' && (
        <div className="budget-view-container">
          <div className="dependencies-top-bar">
            <div>
              <h3>Project Budget & Cost Records</h3>
              <p>Committed, actual, and remaining expenditure across resource categories.</p>
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowCostModal(true)}
            >
              <Plus size={14} />
              <span>Record Cost</span>
            </button>
          </div>

          <div className="budget-category-list">
            {budget?.categories?.map((cat) => (
              <div key={cat.id} className="category-budget-row">
                <div className="cat-name-col">
                  <strong>{cat.category_name}</strong>
                </div>
                <div className="cat-amounts-col">
                  <span>Actual: <strong>${cat.actual_amount?.toLocaleString()}</strong></span>
                  <span>Committed: <strong>${cat.committed_amount?.toLocaleString()}</strong></span>
                  <span>Budgeted: <strong>${cat.budgeted_amount?.toLocaleString()}</strong></span>
                </div>
                <div className="cat-variance-col">
                  <span className={`variance-tag ${cat.variance > 0 ? 'over' : 'under'}`}>
                    {cat.variance > 0 ? `+$${cat.variance.toLocaleString()} Over` : 'Within Budget'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ================= TAB 6: WHAT-IF SIMULATIONS ================= */}
      {activeTab === 'simulation' && (
        <div className="simulation-view-container">
          <div className="dependencies-top-bar">
            <div>
              <h3>What-If Schedule Simulations</h3>
              <p>Simulate schedule compressions, delays, and resource adjustments in-memory without altering production data.</p>
            </div>
            <button
              type="button"
              className="btn-primary"
              onClick={() => setShowScenarioModal(true)}
            >
              <Plus size={14} />
              <span>New Simulation Scenario</span>
            </button>
          </div>

          {scenarios.length === 0 ? (
            <div className="empty-state-card">
              <Sparkles size={36} />
              <h4>No Simulation Scenarios</h4>
              <p>Create a scenario to evaluate alternative project delivery timelines safely.</p>
            </div>
          ) : (
            <div className="scenarios-list">
              {scenarios.map((s) => (
                <div key={s.id} className="scenario-card">
                  <div className="scenario-card-header">
                    <span className={`status-pill ${s.status.toLowerCase()}`}>{s.status}</span>
                    <span className="scenario-date">{s.created_at?.slice(0, 10)}</span>
                  </div>
                  <h4>{s.name}</h4>
                  {s.description && <p className="scenario-desc">{s.description}</p>}
                  
                  {s.outcomes && (
                    <div className="scenario-outcomes">
                      <span><strong>Simulated Duration:</strong> {s.outcomes.simulated_critical_path_duration_days}d</span>
                      <span><strong>Variance:</strong> {s.outcomes.variance_from_current_days >= 0 ? `+${s.outcomes.variance_from_current_days}` : s.outcomes.variance_from_current_days}d</span>
                    </div>
                  )}

                  <div className="scenario-actions">
                    <button
                      type="button"
                      className="btn-sim-run"
                      onClick={() => handleRunSimulation(s.id)}
                    >
                      <Play size={13} />
                      <span>Run Simulation</span>
                    </button>
                    {s.status === 'SIMULATED' && (
                      <button
                        type="button"
                        className="btn-sim-apply"
                        onClick={() => handleApplyScenario(s.id)}
                      >
                        <CheckCircle2 size={13} />
                        <span>Apply to Project</span>
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* MODAL: ADD DEPENDENCY */}
      {showDepModal && (
        <div className="modal-backdrop" onClick={() => setShowDepModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Link Task Dependency</h3>
            <form onSubmit={handleCreateDependency}>
              <div className="form-group">
                <label>Predecessor Task (Must be completed/started first):</label>
                <select
                  value={depForm.depends_on_task_id}
                  onChange={(e) => setDepForm({ ...depForm, depends_on_task_id: e.target.value })}
                  required
                >
                  <option value="">Select Predecessor Task</option>
                  {tasks.map((t) => (
                    <option key={t.id} value={t.id}>{t.title}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Dependency Type:</label>
                <select
                  value={depForm.dependency_type}
                  onChange={(e) => setDepForm({ ...depForm, dependency_type: e.target.value })}
                >
                  <option value="FINISH_TO_START">Finish-to-Start (FS)</option>
                  <option value="START_TO_START">Start-to-Start (SS)</option>
                  <option value="FINISH_TO_FINISH">Finish-to-Finish (FF)</option>
                  <option value="START_TO_FINISH">Start-to-Finish (SF)</option>
                </select>
              </div>

              <div className="form-group">
                <label>Successor Task (Target Dependent Task):</label>
                <select
                  value={depForm.task_id}
                  onChange={(e) => setDepForm({ ...depForm, task_id: e.target.value })}
                  required
                >
                  <option value="">Select Successor Task</option>
                  {tasks.map((t) => (
                    <option key={t.id} value={t.id}>{t.title}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Lag Duration (Days):</label>
                <input
                  type="number"
                  step="0.5"
                  value={depForm.lag_duration}
                  onChange={(e) => setDepForm({ ...depForm, lag_duration: parseFloat(e.target.value) || 0 })}
                />
              </div>

              <div className="modal-btn-row">
                <button type="button" className="btn-secondary" onClick={() => setShowDepModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Link Dependency</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE BASELINE */}
      {showBaselineModal && (
        <div className="modal-backdrop" onClick={() => setShowBaselineModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Capture Project Baseline</h3>
            <form onSubmit={handleCreateBaseline}>
              <div className="form-group">
                <label>Baseline Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Q4 Sprint Baseline"
                  value={baselineForm.name}
                  onChange={(e) => setBaselineForm({ ...baselineForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Description / Reason:</label>
                <textarea
                  rows="3"
                  placeholder="Notes on the approved schedule..."
                  value={baselineForm.description}
                  onChange={(e) => setBaselineForm({ ...baselineForm, description: e.target.value })}
                />
              </div>
              <div className="modal-btn-row">
                <button type="button" className="btn-secondary" onClick={() => setShowBaselineModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Capture Snapshot</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: RECORD COST */}
      {showCostModal && (
        <div className="modal-backdrop" onClick={() => setShowCostModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>Record Project Expense</h3>
            <form onSubmit={handleRecordCost}>
              <div className="form-group">
                <label>Description:</label>
                <input
                  type="text"
                  placeholder="e.g. AWS Database Cluster"
                  value={costForm.description}
                  onChange={(e) => setCostForm({ ...costForm, description: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Amount ($):</label>
                <input
                  type="number"
                  step="0.01"
                  placeholder="0.00"
                  value={costForm.amount}
                  onChange={(e) => setCostForm({ ...costForm, amount: e.target.value })}
                  required
                />
              </div>
              <div className="modal-btn-row">
                <button type="button" className="btn-secondary" onClick={() => setShowCostModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Log Cost</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CREATE SCENARIO */}
      {showScenarioModal && (
        <div className="modal-backdrop" onClick={() => setShowScenarioModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>New Simulation Scenario</h3>
            <form onSubmit={handleCreateScenario}>
              <div className="form-group">
                <label>Scenario Name:</label>
                <input
                  type="text"
                  placeholder="e.g. Fast-Track Testing"
                  value={scenarioForm.name}
                  onChange={(e) => setScenarioForm({ ...scenarioForm, name: e.target.value })}
                  required
                />
              </div>
              <div className="form-group">
                <label>Assumptions & Scope:</label>
                <textarea
                  rows="3"
                  placeholder="Describe proposed timeline alterations..."
                  value={scenarioForm.description}
                  onChange={(e) => setScenarioForm({ ...scenarioForm, description: e.target.value })}
                />
              </div>
              <div className="modal-btn-row">
                <button type="button" className="btn-secondary" onClick={() => setShowScenarioModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Scenario</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: BASELINE COMPARISON */}
      {showComparisonModal && activeComparison && (
        <div className="modal-backdrop" onClick={() => setShowComparisonModal(false)}>
          <div className="modal-content large" onClick={(e) => e.stopPropagation()}>
            <h3>Baseline Comparison: {activeComparison.baseline_name}</h3>
            <div className="cmp-stats-summary">
              <span>Overall Variance: <strong>{activeComparison.overall_schedule_variance_days} days</strong></span>
              <span>Delayed Tasks: <strong>{activeComparison.delayed_tasks_count}</strong></span>
              <span>Advanced Tasks: <strong>{activeComparison.advanced_tasks_count}</strong></span>
              <span>Budget Variance: <strong>${activeComparison.budget_variance?.toLocaleString()}</strong></span>
            </div>

            <div className="cmp-table-wrap">
              <table className="cmp-table">
                <thead>
                  <tr>
                    <th>Task Title</th>
                    <th>Baseline Due</th>
                    <th>Current Due</th>
                    <th>Variance</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {activeComparison.task_variances?.map((tv) => (
                    <tr key={tv.task_id}>
                      <td><strong>{tv.title}</strong></td>
                      <td>{tv.baseline_due || '—'}</td>
                      <td>{tv.current_due || '—'}</td>
                      <td>
                        <span className={`variance-tag ${tv.is_delayed ? 'over' : tv.is_advanced ? 'under' : 'neutral'}`}>
                          {tv.schedule_variance_days > 0 ? `+${tv.schedule_variance_days}d` : `${tv.schedule_variance_days}d`}
                        </span>
                      </td>
                      <td>{tv.current_status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="modal-btn-row">
              <button type="button" className="btn-primary" onClick={() => setShowComparisonModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ProjectPlanningWorkspace;
