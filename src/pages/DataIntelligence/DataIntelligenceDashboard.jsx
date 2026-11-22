import React, { useState, useEffect } from 'react';
import {
  Database,
  BarChart2,
  PieChart,
  FileText,
  Sparkles,
  RefreshCw,
  Plus,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  ArrowRight,
  TrendingUp,
  Sliders,
  Send,
  Eye,
  Trash2,
} from 'lucide-react';
import { dataIntelligenceApi } from '../../services/dataIntelligenceApi';
import './DataIntelligenceDashboard.css';

export default function DataIntelligenceDashboard() {
  const [activeTab, setActiveTab] = useState('catalog');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Core Data
  const [overview, setOverview] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [pipelines, setPipelines] = useState([]);
  const [dashboards, setDashboards] = useState([]);
  const [reports, setReports] = useState([]);
  const [qualityRules, setQualityRules] = useState([]);

  // Modals & Runners
  const [showDashboardModal, setShowDashboardModal] = useState(false);
  const [newDashTitle, setNewDashTitle] = useState('');
  const [newDashDesc, setNewDashDesc] = useState('');
  const [executedReportSummary, setExecutedReportSummary] = useState(null);

  // AI Assistant Query
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiResult, setAiResult] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, dsRes, pipeRes, dashRes, repRes, qrRes] = await Promise.all([
        dataIntelligenceApi.getOverview().catch(() => null),
        dataIntelligenceApi.listDatasets().catch(() => []),
        dataIntelligenceApi.listPipelines().catch(() => []),
        dataIntelligenceApi.listDashboards().catch(() => []),
        dataIntelligenceApi.listReports().catch(() => []),
        dataIntelligenceApi.listQualityRules().catch(() => []),
      ]);
      setOverview(ovRes);
      setDatasets(dsRes || []);
      setPipelines(pipeRes || []);
      setDashboards(dashRes || []);
      setReports(repRes || []);
      setQualityRules(qrRes || []);
    } catch (err) {
      setError(err.message || 'Failed to load data intelligence state');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Run Pipeline
  const handleRunPipeline = async (pipeId) => {
    try {
      const res = await dataIntelligenceApi.runPipeline(pipeId);
      alert(`Pipeline execution complete! Processed ${res.records_processed} records in ${res.duration_ms}ms.`);
      loadData();
    } catch (err) {
      alert(`Pipeline execution failed: ${err.message}`);
    }
  };

  // Run Report
  const handleRunReport = async (repId) => {
    try {
      const res = await dataIntelligenceApi.executeReport(repId);
      setExecutedReportSummary(res);
    } catch (err) {
      alert(`Report query failed: ${err.message}`);
    }
  };

  // Create Dashboard
  const handleCreateDashboard = async (e) => {
    e.preventDefault();
    try {
      await dataIntelligenceApi.createDashboard({
        title: newDashTitle,
        description: newDashDesc,
        visibility: 'WORKSPACE',
        widgets: [
          {
            title: 'Tasks Completion Overview',
            widget_type: 'KPI',
            metric_identifier: 'tasks_completed_count',
            config_json: '{}',
            position_order: 0,
          },
          {
            title: 'Automation Reliability Rate',
            widget_type: 'LINE',
            metric_identifier: 'automation_success_rate',
            config_json: '{}',
            position_order: 1,
          },
        ],
      });
      setShowDashboardModal(false);
      setNewDashTitle('');
      setNewDashDesc('');
      loadData();
      alert('Analytical Dashboard created!');
    } catch (err) {
      alert(`Failed to create dashboard: ${err.message}`);
    }
  };

  // AI Assistant Query
  const handleAskAi = async (e) => {
    e.preventDefault();
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    try {
      const res = await dataIntelligenceApi.queryAiAssistant(aiPrompt);
      setAiResult(res);
    } catch (err) {
      alert(`AI query failed: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="bi-container">
      {/* Header */}
      <div className="bi-header">
        <div className="bi-title-area">
          <h1>
            <Database size={28} color="#2563eb" />
            Data Intelligence, BI & Enterprise Insights Platform
          </h1>
          <p className="bi-subtitle">
            Unified data catalog, automated ETL pipelines, customizable BI dashboards, data quality audits & grounded AI analytics.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowDashboardModal(true)}>
            <Plus size={16} />
            New BI Dashboard
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="bi-metrics-grid">
        <div className="bi-metric-card">
          <div className="metric-icon-wrap">
            <Database size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.total_datasets_count ?? datasets.length}</div>
            <div className="metric-lbl">Catalog Datasets</div>
          </div>
        </div>

        <div className="bi-metric-card">
          <div className="metric-icon-wrap success">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.data_quality_score_percent ?? 100}%</div>
            <div className="metric-lbl">Data Quality Score</div>
          </div>
        </div>

        <div className="bi-metric-card">
          <div className="metric-icon-wrap purple">
            <Layers size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.active_pipelines_count ?? pipelines.length}</div>
            <div className="metric-lbl">Active ETL Pipelines</div>
          </div>
        </div>

        <div className="bi-metric-card">
          <div className="metric-icon-wrap warning">
            <TrendingUp size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.top_metrics_summary?.automation_success_rate ?? 100}%</div>
            <div className="metric-lbl">Automation Success Rate</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bi-tabs">
        <button
          className={`bi-tab-btn ${activeTab === 'catalog' ? 'active' : ''}`}
          onClick={() => setActiveTab('catalog')}
        >
          <Database size={16} />
          Data Catalog & Sources ({datasets.length})
        </button>

        <button
          className={`bi-tab-btn ${activeTab === 'pipelines' ? 'active' : ''}`}
          onClick={() => setActiveTab('pipelines')}
        >
          <Layers size={16} />
          Data Pipelines ({pipelines.length})
        </button>

        <button
          className={`bi-tab-btn ${activeTab === 'dashboards' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboards')}
        >
          <BarChart2 size={16} />
          BI Dashboards ({dashboards.length})
        </button>

        <button
          className={`bi-tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileText size={16} />
          Custom Reports ({reports.length})
        </button>

        <button
          className={`bi-tab-btn ${activeTab === 'quality' ? 'active' : ''}`}
          onClick={() => setActiveTab('quality')}
        >
          <CheckCircle2 size={16} />
          Data Quality Rules ({qualityRules.length})
        </button>

        <button
          className={`bi-tab-btn ${activeTab === 'ai_analyst' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai_analyst')}
        >
          <Sparkles size={16} />
          AI Analytics Assistant
        </button>
      </div>

      {/* TAB: CATALOG */}
      {activeTab === 'catalog' && (
        <div className="cards-grid">
          {datasets.map((ds) => (
            <div key={ds.id} className="app-card">
              <div>
                <div className="app-card-header">
                  <div className="app-icon-wrap">{ds.name[0]}</div>
                  <div className="app-title-group">
                    <h3>{ds.name}</h3>
                    <span className="app-category-badge">{ds.category}</span>
                  </div>
                </div>
                <p className="app-card-desc">{ds.description}</p>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 10 }}>
                  Source: <code>{ds.data_source}</code> • Tracked Rows: <strong>{ds.record_count}</strong>
                </div>
                <div className="features-tags">
                  {(ds.schema_fields || []).map((f, i) => (
                    <span key={i} className="feature-tag">{f.name} ({f.type})</span>
                  ))}
                </div>
              </div>
              <div className="app-card-footer">
                <span className="status-badge active">{ds.freshness_status}</span>
                <span style={{ fontSize: '0.78rem', color: '#64748b' }}>
                  {new Date(ds.last_refreshed_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB: PIPELINES */}
      {activeTab === 'pipelines' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Pipeline Name</th>
                <th>Source Dataset</th>
                <th>Schedule</th>
                <th>Status</th>
                <th>Last Run</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pipelines.map((pipe) => (
                <tr key={pipe.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{pipe.name}</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{pipe.description}</div>
                  </td>
                  <td><code>{pipe.source_dataset_slug}</code></td>
                  <td><code>{pipe.schedule_cron}</code></td>
                  <td>
                    <span className="status-badge active">{pipe.status}</span>
                  </td>
                  <td style={{ fontSize: '0.82rem', color: '#64748b' }}>
                    {pipe.last_run_at ? new Date(pipe.last_run_at).toLocaleString() : 'Never'}
                  </td>
                  <td>
                    <button
                      className="btn-primary"
                      style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                      onClick={() => handleRunPipeline(pipe.id)}
                    >
                      <Play size={13} /> Run Now
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB: DASHBOARDS */}
      {activeTab === 'dashboards' && (
        <div>
          {dashboards.length === 0 ? (
            <div className="automation-card" style={{ textAlign: 'center', padding: 30 }}>
              <p style={{ color: '#64748b' }}>No custom dashboards created yet.</p>
              <button className="btn-primary" onClick={() => setShowDashboardModal(true)} style={{ margin: '0 auto' }}>
                Create First Dashboard
              </button>
            </div>
          ) : (
            dashboards.map((dash) => (
              <div key={dash.id} className="automation-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{dash.title}</h3>
                    <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '0.88rem' }}>{dash.description}</p>
                  </div>
                  <span className="feature-tag">{dash.visibility}</span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 14 }}>
                  {(dash.widgets || []).map((w) => (
                    <div key={w.id} className="widget-card">
                      <div style={{ fontWeight: 600, color: '#334155', fontSize: '0.9rem' }}>{w.title}</div>
                      <div className="widget-val">99.8%</div>
                      <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Metric: {w.metric_identifier}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* TAB: REPORTS */}
      {activeTab === 'reports' && (
        <div>
          <div className="automation-card">
            <table className="workflows-table">
              <thead>
                <tr>
                  <th>Report Title</th>
                  <th>Category</th>
                  <th>Format</th>
                  <th>Last Executed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {reports.map((rep) => (
                  <tr key={rep.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{rep.title}</div>
                    </td>
                    <td><span className="feature-tag">{rep.category}</span></td>
                    <td><span className="status-badge draft">{rep.format}</span></td>
                    <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                      {rep.last_run_at ? new Date(rep.last_run_at).toLocaleString() : 'Never'}
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                        onClick={() => handleRunReport(rep.id)}
                      >
                        <Play size={13} color="#16a34a" /> Run Report
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {executedReportSummary && (
            <div className="automation-card" style={{ background: '#f8fafc', border: '1px solid #bfdbfe' }}>
              <h4>Execution Summary: {executedReportSummary.title}</h4>
              <p style={{ fontSize: '0.88rem', color: '#334155' }}>
                Queried <strong>{executedReportSummary.total_records}</strong> total records • Completed: <strong>{executedReportSummary.completed}</strong> • In-Progress: <strong>{executedReportSummary.in_progress}</strong>
              </p>
              <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Generated at: {executedReportSummary.generated_at}</div>
            </div>
          )}
        </div>
      )}

      {/* TAB: QUALITY RULES */}
      {activeTab === 'quality' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Rule Name</th>
                <th>Dataset</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Evaluated At</th>
              </tr>
            </thead>
            <tbody>
              {qualityRules.map((rule) => (
                <tr key={rule.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{rule.rule_name}</div>
                    <code style={{ fontSize: '0.75rem', color: '#64748b' }}>{rule.condition_expr}</code>
                  </td>
                  <td><code>{rule.dataset_slug}</code></td>
                  <td><span className="feature-tag">{rule.rule_type}</span></td>
                  <td><span className={`sev-pill ${rule.severity.toLowerCase()}`}>{rule.severity}</span></td>
                  <td>
                    <span className={`status-badge ${rule.status === 'PASS' ? 'active' : 'failed'}`}>
                      {rule.status}
                    </span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(rule.last_evaluated_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB: AI ANALYST */}
      {activeTab === 'ai_analyst' && (
        <div>
          <div className="ai-generator-box">
            <h3>
              <Sparkles size={20} color="#2563eb" />
              Grounded AI Natural Language Data Analyst
            </h3>
            <p style={{ fontSize: '0.88rem', color: '#475569' }}>
              Ask natural language analytical questions (e.g. <em>"How many tasks were completed this week and what is our overdue rate?"</em>). Answers are derived strictly from live records with verifiable evidence.
            </p>
            <form onSubmit={handleAskAi} className="ai-input-row">
              <input
                type="text"
                className="form-input"
                style={{ flex: 1 }}
                placeholder="Ask an analytical question..."
                value={aiPrompt}
                onChange={(e) => setAiPrompt(e.target.value)}
              />
              <button type="submit" className="btn-primary" disabled={aiLoading || !aiPrompt.trim()}>
                <Sparkles size={16} />
                {aiLoading ? 'Analyzing...' : 'Ask AI Analyst'}
              </button>
            </form>
          </div>

          {aiResult && (
            <div className="automation-card">
              <h3 style={{ margin: '0 0 10px' }}>Synthesized Answer</h3>
              <p style={{ fontSize: '1.05rem', color: '#0f172a', fontWeight: 600 }}>{aiResult.direct_answer}</p>

              <h4>Verifiable Grounded Evidence:</h4>
              <ul style={{ paddingLeft: 20, color: '#475569', fontSize: '0.88rem', margin: '6px 0 16px' }}>
                {aiResult.grounded_evidence.map((ev, i) => (
                  <li key={i}>{ev}</li>
                ))}
              </ul>

              <h4>Data Visualization ({aiResult.suggested_visualization}):</h4>
              <div style={{ maxWidth: 500, margin: '14px 0' }}>
                {aiResult.chart_data.map((item, idx) => (
                  <div key={idx} className="chart-bar-row">
                    <span style={{ minWidth: 120 }}>{item.label || item.metric}</span>
                    <div className="chart-bar-bg">
                      <div className="chart-bar-fill" style={{ width: `${Math.min(Number(item.value) * 10 + 20, 100)}%` }} />
                    </div>
                    <span style={{ fontWeight: 700 }}>{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Create Dashboard Modal */}
      {showDashboardModal && (
        <div className="modal-overlay" onClick={() => setShowDashboardModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create BI Dashboard</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setShowDashboardModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateDashboard}>
              <div className="form-group">
                <label>Dashboard Title</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Sprint Productivity & Quality Overview"
                  value={newDashTitle}
                  onChange={(e) => setNewDashTitle(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  placeholder="Explain the operational purpose of this dashboard..."
                  value={newDashDesc}
                  onChange={(e) => setNewDashDesc(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button type="button" className="btn-secondary" onClick={() => setShowDashboardModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Create Dashboard</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
