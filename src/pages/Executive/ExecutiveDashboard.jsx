import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  FileText,
  Download,
  Plus,
  RefreshCw,
  ShieldAlert,
  Calendar,
  Layers,
  ArrowUpRight,
  ArrowDownRight,
  HelpCircle
} from 'lucide-react';
import { enterpriseAnalyticsApi } from '../../services/enterpriseAnalyticsApi';
import './ExecutiveDashboard.css';

export default function ExecutiveDashboard() {
  const [activeTab, setActiveTab] = useState('portfolio');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Data states
  const [kpis, setKpis] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [workload, setWorkload] = useState(null);
  const [reports, setReports] = useState([]);

  // Modals
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportTitle, setReportTitle] = useState('');
  const [reportType, setReportType] = useState('PORTFOLIO_HEALTH');
  const [reportFormat, setReportFormat] = useState('CSV');
  const [generatingReport, setGeneratingReport] = useState(false);

  // Capacity Edit Modal
  const [showCapacityModal, setShowCapacityModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [capacityHours, setCapacityHours] = useState(40);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [kpiRes, portfolioRes, workloadRes, reportsRes] = await Promise.all([
        enterpriseAnalyticsApi.getExecutiveSummary().catch(() => null),
        enterpriseAnalyticsApi.getPortfolioHealth().catch(() => null),
        enterpriseAnalyticsApi.getTeamWorkload().catch(() => null),
        enterpriseAnalyticsApi.listReports().catch(() => []),
      ]);
      setKpis(kpiRes);
      setPortfolio(portfolioRes);
      setWorkload(workloadRes);
      setReports(reportsRes || []);
    } catch (err) {
      setError('Failed to load enterprise analytics. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    if (!reportTitle.trim()) return;
    setGeneratingReport(true);
    try {
      await enterpriseAnalyticsApi.createReport({
        title: reportTitle,
        report_type: reportType,
        format: reportFormat,
      });
      setShowReportModal(false);
      setReportTitle('');
      const updated = await enterpriseAnalyticsApi.listReports();
      setReports(updated || []);
    } catch (err) {
      alert('Failed to generate report: ' + (err.message || 'Error'));
    } finally {
      setGeneratingReport(false);
    }
  };

  const handleUpdateCapacity = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;
    try {
      await enterpriseAnalyticsApi.setResourceCapacity({
        user_id: selectedUser.user_id,
        weekly_hours_capacity: parseFloat(capacityHours),
      });
      setShowCapacityModal(false);
      const updatedWorkload = await enterpriseAnalyticsApi.getTeamWorkload();
      setWorkload(updatedWorkload);
    } catch (err) {
      alert('Failed to update capacity: ' + err.message);
    }
  };

  const getHealthBadgeClass = (status) => {
    switch (status) {
      case 'HEALTHY': return 'badge-healthy';
      case 'AT_RISK': return 'badge-at-risk';
      case 'CRITICAL': return 'badge-critical';
      default: return 'badge-neutral';
    }
  };

  const getSeverityBadgeClass = (sev) => {
    switch (sev) {
      case 'CRITICAL': return 'risk-badge-critical';
      case 'HIGH': return 'risk-badge-high';
      case 'MEDIUM': return 'risk-badge-medium';
      default: return 'risk-badge-low';
    }
  };

  if (loading && !kpis) {
    return (
      <div className="exec-loading-container">
        <RefreshCw className="spin-icon" size={24} />
        <p>Aggregating Enterprise Business Intelligence...</p>
      </div>
    );
  }

  return (
    <div className="exec-dashboard-wrapper">
      {/* Top Header */}
      <div className="exec-header">
        <div>
          <h2 className="exec-title">Executive Intelligence & Portfolio Analytics</h2>
          <p className="exec-subtitle">
            Strategic decision-support, predictive delivery health, and enterprise capacity insights.
          </p>
        </div>
        <div className="exec-header-actions">
          <button className="exec-btn-secondary" onClick={loadAllData} title="Refresh Analytics">
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="exec-btn-primary" onClick={() => setShowReportModal(true)}>
            <FileText size={16} /> Generate Executive Report
          </button>
        </div>
      </div>

      {error && <div className="exec-error-banner">{error}</div>}

      {/* KPI Cards Banner */}
      <div className="exec-kpi-grid">
        <div className="exec-kpi-card">
          <div className="exec-kpi-header">
            <span>Portfolio Health</span>
            <TrendingUp size={18} className="exec-icon-teal" />
          </div>
          <div className="exec-kpi-value">{kpis?.portfolio_health_average ?? 100}%</div>
          <div className="exec-kpi-subtext">Avg health across active projects</div>
        </div>

        <div className="exec-kpi-card">
          <div className="exec-kpi-header">
            <span>Active Projects</span>
            <Layers size={18} className="exec-icon-blue" />
          </div>
          <div className="exec-kpi-value">{kpis?.active_projects ?? 0} / {kpis?.total_projects ?? 0}</div>
          <div className="exec-kpi-subtext">Portfolio projects in flight</div>
        </div>

        <div className="exec-kpi-card">
          <div className="exec-kpi-header">
            <span>On-Time Delivery</span>
            <CheckCircle2 size={18} className="exec-icon-green" />
          </div>
          <div className="exec-kpi-value">{kpis?.on_time_delivery_rate ?? 100}%</div>
          <div className="exec-kpi-subtext">{kpis?.overdue_tasks ?? 0} overdue tasks overall</div>
        </div>

        <div className="exec-kpi-card">
          <div className="exec-kpi-header">
            <span>Workload Saturation</span>
            <Users size={18} className="exec-icon-purple" />
          </div>
          <div className="exec-kpi-value">{kpis?.workload_saturation_rate ?? 0}%</div>
          <div className="exec-kpi-subtext">Team allocated vs capacity hours</div>
        </div>

        <div className="exec-kpi-card">
          <div className="exec-kpi-header">
            <span>Critical / Active Risks</span>
            <AlertTriangle size={18} className="exec-icon-amber" />
          </div>
          <div className="exec-kpi-value risk-val">
            {kpis?.critical_risks_count ?? 0} <span className="text-muted">/ {kpis?.active_risks_count ?? 0}</span>
          </div>
          <div className="exec-kpi-subtext">Blocking delivery milestones</div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="exec-tabs">
        <button
          className={`exec-tab-btn ${activeTab === 'portfolio' ? 'active' : ''}`}
          onClick={() => setActiveTab('portfolio')}
        >
          <Layers size={16} /> Portfolio Health & Forecasts ({portfolio?.total_projects ?? 0})
        </button>
        <button
          className={`exec-tab-btn ${activeTab === 'workload' ? 'active' : ''}`}
          onClick={() => setActiveTab('workload')}
        >
          <Users size={16} /> Team Capacity & Workload ({workload?.total_members ?? 0})
        </button>
        <button
          className={`exec-tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileText size={16} /> Executive Reports & Exports ({reports.length})
        </button>
      </div>

      {/* TAB CONTENT: Portfolio Health */}
      {activeTab === 'portfolio' && (
        <div className="exec-tab-content">
          <div className="exec-section-header">
            <div>
              <h3>Workspace Project Portfolio</h3>
              <p>Transparent health scores calculated from task completion velocity, deadline proximity, and active blockers.</p>
            </div>
            <div className="exec-summary-chips">
              <span className="chip chip-healthy">Healthy: {portfolio?.healthy_count ?? 0}</span>
              <span className="chip chip-at-risk">At Risk: {portfolio?.at_risk_count ?? 0}</span>
              <span className="chip chip-critical">Critical: {portfolio?.critical_count ?? 0}</span>
            </div>
          </div>

          {portfolio?.projects?.length === 0 ? (
            <div className="exec-empty-state">
              <Layers size={36} />
              <h4>No Projects Created Yet</h4>
              <p>Create projects in your team workspace to view automated portfolio analytics and forecasts.</p>
            </div>
          ) : (
            <div className="exec-table-card">
              <table className="exec-table">
                <thead>
                  <tr>
                    <th>Project Name</th>
                    <th>Health Status</th>
                    <th>Score</th>
                    <th>Completion</th>
                    <th>Velocity Trend</th>
                    <th>Explainable Signals</th>
                    <th>Delivery Forecast</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio?.projects?.map((proj) => (
                    <tr key={proj.project_id}>
                      <td className="font-semibold text-primary">{proj.project_name}</td>
                      <td>
                        <span className={`exec-badge ${getHealthBadgeClass(proj.health_status)}`}>
                          {proj.health_status.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <div className="exec-score-bar-wrapper">
                          <span className="score-num">{proj.health_score}</span>
                          <div className="score-bar-bg">
                            <div
                              className="score-bar-fill"
                              style={{
                                width: `${proj.health_score}%`,
                                backgroundColor:
                                  proj.health_score >= 80 ? '#10b981' : proj.health_score >= 50 ? '#f59e0b' : '#ef4444'
                              }}
                            />
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="task-progress-cell">
                          <span>{proj.completion_rate}%</span>
                          <small className="text-muted">
                            ({proj.completed_tasks}/{proj.total_tasks} tasks)
                          </small>
                        </div>
                      </td>
                      <td>
                        <span className={`trend-indicator trend-${proj.velocity_trend.toLowerCase()}`}>
                          {proj.velocity_trend}
                        </span>
                      </td>
                      <td>
                        <ul className="signals-list">
                          {proj.signals.slice(0, 2).map((sig, idx) => (
                            <li key={idx}>{sig}</li>
                          ))}
                        </ul>
                      </td>
                      <td>
                        {proj.forecast?.status === 'forecasted' ? (
                          <div className="forecast-cell">
                            <span className="forecast-range">{proj.forecast.completion_range}</span>
                            <small className="text-muted">{proj.forecast.message}</small>
                          </div>
                        ) : (
                          <span className="text-muted text-xs">
                            {proj.forecast?.message || 'Insufficient data'}
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: Team Workload & Capacity */}
      {activeTab === 'workload' && (
        <div className="exec-tab-content">
          <div className="exec-section-header">
            <div>
              <h3>Team Capacity & Resource Allocation</h3>
              <p>Weekly capacity hours vs estimated allocated tasks. Adjust capacity to prevent developer burnout.</p>
            </div>
            <div className="exec-capacity-stats">
              <span>Total Capacity: <strong>{workload?.total_capacity_hours ?? 0} hrs/wk</strong></span>
              <span>Allocated: <strong>{workload?.total_allocated_hours ?? 0} hrs</strong></span>
            </div>
          </div>

          <div className="exec-table-card">
            <table className="exec-table">
              <thead>
                <tr>
                  <th>Team Member</th>
                  <th>Assigned Tasks</th>
                  <th>Weekly Capacity</th>
                  <th>Allocated Hours</th>
                  <th>Utilization</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {workload?.members?.map((m) => (
                  <tr key={m.user_id}>
                    <td>
                      <div className="member-info-cell">
                        <strong>{m.user_name}</strong>
                        <small className="text-muted">{m.user_email}</small>
                      </div>
                    </td>
                    <td>
                      {m.assigned_tasks_count} active <small className="text-muted">({m.completed_tasks_count} done)</small>
                    </td>
                    <td>{m.weekly_capacity_hours} hrs/wk</td>
                    <td>{m.estimated_allocated_hours} hrs</td>
                    <td>
                      <div className="utilization-cell">
                        <span>{m.utilization_rate}%</span>
                        <div className="utilization-bar-bg">
                          <div
                            className="utilization-bar-fill"
                            style={{
                              width: `${Math.min(100, m.utilization_rate)}%`,
                              backgroundColor:
                                m.utilization_rate > 100 ? '#ef4444' : m.utilization_rate < 40 ? '#6366f1' : '#10b981'
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className={`exec-badge badge-${m.status.toLowerCase()}`}>
                        {m.status}
                      </span>
                    </td>
                    <td>
                      <button
                        className="exec-btn-sm"
                        onClick={() => {
                          setSelectedUser(m);
                          setCapacityHours(m.weekly_capacity_hours);
                          setShowCapacityModal(true);
                        }}
                      >
                        Adjust Capacity
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB CONTENT: Reports */}
      {activeTab === 'reports' && (
        <div className="exec-tab-content">
          <div className="exec-section-header">
            <div>
              <h3>Executive Reports & Archival Records</h3>
              <p>Download structured CSV or JSON snapshots for board meetings, compliance, and leadership syncs.</p>
            </div>
            <button className="exec-btn-primary" onClick={() => setShowReportModal(true)}>
              <Plus size={16} /> New Report
            </button>
          </div>

          {reports.length === 0 ? (
            <div className="exec-empty-state">
              <FileText size={36} />
              <h4>No Reports Generated</h4>
              <p>Generate your first Executive KPI or Portfolio Health report to download CSV data.</p>
            </div>
          ) : (
            <div className="exec-table-card">
              <table className="exec-table">
                <thead>
                  <tr>
                    <th>Report Title</th>
                    <th>Type</th>
                    <th>Format</th>
                    <th>Generated Date</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id}>
                      <td className="font-semibold">{r.title}</td>
                      <td>
                        <span className="report-type-badge">{r.report_type.replace('_', ' ')}</span>
                      </td>
                      <td><strong>{r.format}</strong></td>
                      <td>{new Date(r.created_at).toLocaleString()}</td>
                      <td>
                        <a
                          href={enterpriseAnalyticsApi.downloadReportUrl(r.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="exec-btn-download"
                        >
                          <Download size={14} /> Download {r.format}
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Generate Report Modal */}
      {showReportModal && (
        <div className="exec-modal-overlay">
          <div className="exec-modal">
            <div className="exec-modal-header">
              <h3>Generate Executive Report</h3>
              <button className="exec-close-btn" onClick={() => setShowReportModal(false)}>×</button>
            </div>
            <form onSubmit={handleGenerateReport}>
              <div className="exec-form-group">
                <label>Report Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Q4 Executive Portfolio Briefing"
                  value={reportTitle}
                  onChange={(e) => setReportTitle(e.target.value)}
                />
              </div>
              <div className="exec-form-group">
                <label>Report Type</label>
                <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
                  <option value="EXECUTIVE_KPI">Executive KPI Summary</option>
                  <option value="PORTFOLIO_HEALTH">Portfolio Health & Delivery Assessment</option>
                  <option value="TEAM_WORKLOAD">Team Capacity & Workload Balance</option>
                  <option value="RISK_ASSESSMENT">Portfolio Risk Register</option>
                </select>
              </div>
              <div className="exec-form-group">
                <label>Export Format</label>
                <select value={reportFormat} onChange={(e) => setReportFormat(e.target.value)}>
                  <option value="CSV">CSV (Spreadsheet / Excel compatible)</option>
                  <option value="JSON">JSON (Machine-readable)</option>
                </select>
              </div>
              <div className="exec-modal-actions">
                <button type="button" className="exec-btn-secondary" onClick={() => setShowReportModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="exec-btn-primary" disabled={generatingReport}>
                  {generatingReport ? 'Generating...' : 'Generate & Save'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Adjust Capacity Modal */}
      {showCapacityModal && selectedUser && (
        <div className="exec-modal-overlay">
          <div className="exec-modal">
            <div className="exec-modal-header">
              <h3>Adjust Member Capacity</h3>
              <button className="exec-close-btn" onClick={() => setShowCapacityModal(false)}>×</button>
            </div>
            <form onSubmit={handleUpdateCapacity}>
              <p className="text-muted text-sm mb-4">
                Update available weekly working hours for <strong>{selectedUser.user_name}</strong>.
              </p>
              <div className="exec-form-group">
                <label>Weekly Hours Capacity</label>
                <input
                  type="number"
                  min="1"
                  max="168"
                  step="0.5"
                  required
                  value={capacityHours}
                  onChange={(e) => setCapacityHours(e.target.value)}
                />
              </div>
              <div className="exec-modal-actions">
                <button type="button" className="exec-btn-secondary" onClick={() => setShowCapacityModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="exec-btn-primary">
                  Save Capacity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
