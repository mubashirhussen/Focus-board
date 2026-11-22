import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  ShieldAlert,
  Server,
  RefreshCw,
  Plus,
  CheckCircle2,
  XCircle,
  Clock,
  Wrench,
  Search,
  ExternalLink,
  ChevronRight,
  Flame,
  Check,
  FileText,
  Calendar,
  Layers,
  Terminal,
} from 'lucide-react';
import { observabilityApi } from '../../services/observabilityApi';
import './OperationsConsole.css';

export default function OperationsConsole() {
  const [activeTab, setActiveTab] = useState('services');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Core Telemetry State
  const [overview, setOverview] = useState(null);
  const [services, setServices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [slos, setSlos] = useState([]);
  const [maintenanceWindows, setMaintenanceWindows] = useState([]);

  // Selected Incident & Modals
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [newIncident, setNewIncident] = useState({
    title: '',
    description: '',
    severity: 'SEV3',
    status: 'DETECTED',
    affected_services: ['api_core'],
  });

  // Diagnostics State
  const [diagWorkspaceId, setDiagWorkspaceId] = useState(1);
  const [diagnosticsResult, setDiagnosticsResult] = useState(null);
  const [diagnosing, setDiagnosing] = useState(false);

  const sampleServices = [
    {
      id: 1,
      name: 'FastAPI Production Core Gateway',
      service_key: 'api_gateway',
      service_type: 'API',
      status: 'HEALTHY',
      uptime_percentage: 99.98,
      latency_p95_ms: 28,
      error_rate_percentage: 0.02,
      last_health_check_at: new Date().toISOString(),
      dependencies: ['postgres_primary', 'redis_cache'],
    },
    {
      id: 2,
      name: 'PostgreSQL 16 Multi-Tenant Cluster',
      service_key: 'postgres_primary',
      service_type: 'DATABASE',
      status: 'HEALTHY',
      uptime_percentage: 99.99,
      latency_p95_ms: 4,
      error_rate_percentage: 0.00,
      last_health_check_at: new Date().toISOString(),
      dependencies: [],
    },
    {
      id: 3,
      name: 'WebSocket Live Collaborative Notification Bus',
      service_key: 'websocket_bus',
      service_type: 'REALTIME',
      status: 'HEALTHY',
      uptime_percentage: 99.95,
      latency_p95_ms: 12,
      error_rate_percentage: 0.01,
      last_health_check_at: new Date().toISOString(),
      dependencies: ['api_gateway'],
    },
  ];

  const sampleIncidents = [
    {
      id: 101,
      incident_number: 'INC-2026-08',
      title: 'VPC Inter-Region Peering Transient Latency Mitigation',
      severity: 'SEV3',
      status: 'RESOLVED',
      affected_services: ['api_gateway'],
      created_at: new Date(Date.now() - 86400000).toISOString(),
      resolved_at: new Date(Date.now() - 82800000).toISOString(),
    },
    {
      id: 102,
      incident_number: 'INC-2026-09',
      title: 'Database Schema Migration 013 Verification Routine',
      severity: 'SEV4',
      status: 'RESOLVED',
      affected_services: ['postgres_primary'],
      created_at: new Date(Date.now() - 172800000).toISOString(),
      resolved_at: new Date(Date.now() - 171000000).toISOString(),
    },
  ];

  const sampleOpsOverview = {
    overall_health: 'HEALTHY',
    system_status: 'OPERATIONAL',
    healthy_services_count: 3,
    total_services_count: 3,
    active_incidents_count: 0,
    active_alerts_count: 0,
    slo_metrics: [
      { name: 'API Latency P95', current_value: '28ms', target: '< 100ms', status: 'MET' },
      { name: 'Monthly Availability', current_value: '99.98%', target: '> 99.90%', status: 'MET' },
      { name: 'Error Budget Remaining', current_value: '94.2%', target: '> 50.0%', status: 'MET' },
    ],
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, srvRes, altRes, incRes, maintRes] = await Promise.all([
        observabilityApi.getOverview().catch(() => null),
        observabilityApi.listServices().catch(() => []),
        observabilityApi.listAlerts().catch(() => []),
        observabilityApi.listIncidents().catch(() => []),
        observabilityApi.listMaintenance().catch(() => []),
      ]);
      setOverview(ovRes || sampleOpsOverview);
      setServices(srvRes && srvRes.length > 0 ? srvRes : sampleServices);
      setAlerts(altRes || []);
      setIncidents(incRes && incRes.length > 0 ? incRes : sampleIncidents);
      setSlos(ovRes?.slo_metrics || sampleOpsOverview.slo_metrics);
      setMaintenanceWindows(maintRes || []);
    } catch {
      setOverview(sampleOpsOverview);
      setServices(sampleServices);
      setIncidents(sampleIncidents);
      setSlos(sampleOpsOverview.slo_metrics);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Alert Actions
  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await observabilityApi.acknowledgeAlert(alertId);
      loadData();
    } catch (err) {
      alert(`Acknowledge failed: ${err.message}`);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await observabilityApi.resolveAlert(alertId);
      loadData();
    } catch (err) {
      alert(`Resolve failed: ${err.message}`);
    }
  };

  // Create Incident
  const handleCreateIncident = async (e) => {
    e.preventDefault();
    try {
      await observabilityApi.createIncident({
        title: newIncident.title,
        description: newIncident.description,
        severity: newIncident.severity,
        status: newIncident.status,
        affected_services_json: JSON.stringify(newIncident.affected_services),
      });
      setShowIncidentModal(false);
      setNewIncident({
        title: '',
        description: '',
        severity: 'SEV3',
        status: 'DETECTED',
        affected_services: ['api_core'],
      });
      loadData();
      alert('Platform incident opened successfully.');
    } catch (err) {
      alert(`Failed to create incident: ${err.message}`);
    }
  };

  // Run Support Diagnostics
  const handleRunDiagnostics = async (e) => {
    e.preventDefault();
    setDiagnosing(true);
    try {
      const res = await observabilityApi.runSupportDiagnostics(Number(diagWorkspaceId), 'FULL');
      setDiagnosticsResult(res);
    } catch (err) {
      alert(`Diagnostics check failed: ${err.message}`);
    } finally {
      setDiagnosing(false);
    }
  };

  return (
    <div className="ops-container">
      {/* Header */}
      <div className="ops-header">
        <div className="ops-title-area">
          <h1>
            <Server size={28} color="#2563eb" />
            Platform Operations & Observability Console
          </h1>
          <p className="ops-subtitle">
            Unified service status, live component health diagnostics, alerting engine, incident management & post-mortems.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            Refresh Telemetry
          </button>
          <button className="btn-primary" onClick={() => setShowIncidentModal(true)}>
            <Plus size={16} />
            Declare Incident
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="ops-metrics-grid">
        <div className="ops-metric-card">
          <div className="metric-icon-wrap success">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.overall_health || 'OPERATIONAL'}</div>
            <div className="metric-lbl">Overall Health</div>
          </div>
        </div>

        <div className="ops-metric-card">
          <div className="metric-icon-wrap">
            <Clock size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.system_uptime_percentage ?? 99.98}%</div>
            <div className="metric-lbl">System Uptime (30d)</div>
          </div>
        </div>

        <div className="ops-metric-card">
          <div className="metric-icon-wrap warning">
            <AlertTriangle size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.active_alerts_count ?? 0}</div>
            <div className="metric-lbl">Active Alerts</div>
          </div>
        </div>

        <div className="ops-metric-card">
          <div className="metric-icon-wrap purple">
            <ShieldAlert size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.active_incidents_count ?? 0}</div>
            <div className="metric-lbl">Active Incidents</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="ops-tabs">
        <button
          className={`ops-tab-btn ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          <Server size={16} />
          Service Status ({services.length})
        </button>

        <button
          className={`ops-tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          <AlertTriangle size={16} />
          Alerts Inbox
          {alerts.filter((a) => a.status === 'ACTIVE').length > 0 && (
            <span className="ops-badge-count">{alerts.filter((a) => a.status === 'ACTIVE').length}</span>
          )}
        </button>

        <button
          className={`ops-tab-btn ${activeTab === 'incidents' ? 'active' : ''}`}
          onClick={() => setActiveTab('incidents')}
        >
          <ShieldAlert size={16} />
          Incidents & Post-Mortems ({incidents.length})
        </button>

        <button
          className={`ops-tab-btn ${activeTab === 'slos' ? 'active' : ''}`}
          onClick={() => setActiveTab('slos')}
        >
          <Activity size={16} />
          SLOs & Error Budgets
        </button>

        <button
          className={`ops-tab-btn ${activeTab === 'diagnostics' ? 'active' : ''}`}
          onClick={() => setActiveTab('diagnostics')}
        >
          <Terminal size={16} />
          Support Diagnostics
        </button>

        <button
          className={`ops-tab-btn ${activeTab === 'maintenance' ? 'active' : ''}`}
          onClick={() => setActiveTab('maintenance')}
        >
          <Wrench size={16} />
          Maintenance Windows
        </button>
      </div>

      {/* TAB: SERVICES */}
      {activeTab === 'services' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Service Name</th>
                <th>Category</th>
                <th>Status</th>
                <th>Latency (ms)</th>
                <th>Dependencies</th>
                <th>Last Checked</th>
              </tr>
            </thead>
            <tbody>
              {services.map((srv) => (
                <tr key={srv.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{srv.name}</div>
                    <code style={{ fontSize: '0.78rem', color: '#64748b' }}>{srv.id}</code>
                  </td>
                  <td>
                    <span className="feature-tag">{srv.category}</span>
                  </td>
                  <td>
                    <span className={`status-badge ${srv.status.toLowerCase()}`}>{srv.status}</span>
                  </td>
                  <td>{srv.response_time_ms} ms</td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {(srv.dependencies_list || []).map((dep, i) => (
                        <span key={i} className="feature-tag" style={{ fontSize: '0.72rem' }}>{dep}</span>
                      ))}
                      {(!srv.dependencies_list || srv.dependencies_list.length === 0) && (
                        <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>None</span>
                      )}
                    </div>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(srv.last_checked_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB: ALERTS */}
      {activeTab === 'alerts' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Summary & Details</th>
                <th>Service</th>
                <th>Status</th>
                <th>Triggered At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((alt) => (
                <tr key={alt.id}>
                  <td>
                    <span className={`sev-pill ${alt.severity.toLowerCase()}`}>{alt.severity}</span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{alt.summary}</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{alt.details}</div>
                  </td>
                  <td><code>{alt.related_service_id || 'system'}</code></td>
                  <td>
                    <span className={`status-badge ${alt.status.toLowerCase()}`}>{alt.status}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(alt.triggered_at).toLocaleTimeString()}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: 6 }}>
                      {alt.status === 'ACTIVE' && (
                        <button
                          className="btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '0.78rem' }}
                          onClick={() => handleAcknowledgeAlert(alt.id)}
                        >
                          Ack
                        </button>
                      )}
                      {alt.status !== 'RESOLVED' && (
                        <button
                          className="btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '0.78rem', color: '#16a34a' }}
                          onClick={() => handleResolveAlert(alt.id)}
                        >
                          Resolve
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB: INCIDENTS */}
      {activeTab === 'incidents' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Title</th>
                <th>Status</th>
                <th>Detected At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {incidents.map((inc) => (
                <tr key={inc.id}>
                  <td>
                    <span className={`sev-pill ${inc.severity.toLowerCase()}`}>{inc.severity}</span>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{inc.title}</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{inc.description}</div>
                  </td>
                  <td>
                    <span className={`status-badge ${inc.status.toLowerCase()}`}>{inc.status}</span>
                  </td>
                  <td style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    {new Date(inc.detected_at).toLocaleString()}
                  </td>
                  <td>
                    <button
                      className="btn-secondary"
                      style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                      onClick={() => setSelectedIncident(inc)}
                    >
                      View Details & Timeline
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB: SLOS */}
      {activeTab === 'slos' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
          {slos.map((slo) => (
            <div key={slo.id} className="slo-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="feature-tag">{slo.service_id}</span>
                <span style={{ fontWeight: 700, color: '#16a34a' }}>{slo.current_sli_percentage}%</span>
              </div>
              <h3 style={{ margin: '10px 0 4px', fontSize: '1.05rem' }}>{slo.name}</h3>
              <div style={{ fontSize: '0.84rem', color: '#64748b' }}>
                Target: {slo.target_percentage}% ({slo.measurement_window_days}-day window)
              </div>
              <div className="slo-progress-bar">
                <div
                  className={`slo-progress-fill ${slo.error_budget_remaining_percent < 20 ? 'danger' : ''}`}
                  style={{ width: `${slo.error_budget_remaining_percent}%` }}
                />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#64748b' }}>
                <span>Budget Remaining: <strong>{slo.error_budget_remaining_percent}%</strong></span>
                <span>Burn Rate: <strong>{slo.burn_rate}x</strong></span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* TAB: DIAGNOSTICS */}
      {activeTab === 'diagnostics' && (
        <div className="sandbox-card">
          <h3 style={{ marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Terminal size={20} color="#2563eb" />
            Support Diagnostics & Safe Tenant Integrity Verification
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: 20 }}>
            Inspect customer workspace health without exposing confidential task titles or sensitive tenant payload contents.
          </p>

          <form onSubmit={handleRunDiagnostics} style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
            <input
              type="number"
              className="form-input"
              style={{ width: 180 }}
              placeholder="Workspace ID"
              value={diagWorkspaceId}
              onChange={(e) => setDiagWorkspaceId(e.target.value)}
            />
            <button type="submit" className="btn-primary" disabled={diagnosing}>
              {diagnosing ? 'Running Diagnostics...' : 'Execute Health Scan'}
            </button>
          </form>

          {diagnosticsResult && (
            <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontWeight: 700 }}>Tenant Boundary Status: <span style={{ color: '#16a34a' }}>{diagnosticsResult.health_status}</span></span>
                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Scanned At: {new Date(diagnosticsResult.timestamp).toLocaleTimeString()}</span>
              </div>

              <h4>Diagnostic Checks:</h4>
              <ul style={{ paddingLeft: 20, margin: '8px 0 16px' }}>
                {diagnosticsResult.checks_performed.map((chk, idx) => (
                  <li key={idx} style={{ marginBottom: 4, fontSize: '0.88rem' }}>
                    <strong>{chk.check}:</strong> <span style={{ color: '#16a34a' }}>{chk.status}</span> ({chk.details})
                  </li>
                ))}
              </ul>

              <h4>Operational Recommendations:</h4>
              <ul style={{ paddingLeft: 20, margin: '8px 0 0', color: '#334155', fontSize: '0.85rem' }}>
                {diagnosticsResult.recommendations.map((rec, idx) => (
                  <li key={idx} style={{ marginBottom: 4 }}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* TAB: MAINTENANCE */}
      {activeTab === 'maintenance' && (
        <div className="automation-card">
          <table className="workflows-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Scheduled Start</th>
                <th>Scheduled End</th>
              </tr>
            </thead>
            <tbody>
              {maintenanceWindows.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{m.title}</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{m.description}</div>
                  </td>
                  <td>
                    <span className="status-badge active">{m.status}</span>
                  </td>
                  <td>{new Date(m.scheduled_start).toLocaleString()}</td>
                  <td>{new Date(m.scheduled_end).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Declare Incident Modal */}
      {showIncidentModal && (
        <div className="modal-overlay" onClick={() => setShowIncidentModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Declare Platform Incident</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setShowIncidentModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateIncident}>
              <div className="form-group">
                <label>Incident Title</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Inbound API Latency Spike"
                  value={newIncident.title}
                  onChange={(e) => setNewIncident({ ...newIncident, title: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Description & Scope</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  required
                  placeholder="Explain symptoms, affected services, and initial observations..."
                  value={newIncident.description}
                  onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Severity Level</label>
                <select
                  className="form-select"
                  value={newIncident.severity}
                  onChange={(e) => setNewIncident({ ...newIncident, severity: e.target.value })}
                >
                  <option value="SEV1">SEV1 - Critical Platform Outage</option>
                  <option value="SEV2">SEV2 - Major Service Degradation</option>
                  <option value="SEV3">SEV3 - Moderate Issue / Workaround Exists</option>
                  <option value="SEV4">SEV4 - Minor Operational Anomaly</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 16 }}>
                <button type="button" className="btn-secondary" onClick={() => setShowIncidentModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Declare Incident</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Incident Details & Timeline Drawer Modal */}
      {selectedIncident && (
        <div className="modal-overlay" onClick={() => setSelectedIncident(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedIncident.title}</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setSelectedIncident(null)}>✕</button>
            </div>
            <div>
              <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                <span className={`sev-pill ${selectedIncident.severity.toLowerCase()}`}>{selectedIncident.severity}</span>
                <span className={`status-badge ${selectedIncident.status.toLowerCase()}`}>{selectedIncident.status}</span>
                <span style={{ fontSize: '0.82rem', color: '#64748b' }}>Detected: {new Date(selectedIncident.detected_at).toLocaleString()}</span>
              </div>
              <p style={{ fontSize: '0.9rem', color: '#334155', marginBottom: 16 }}>{selectedIncident.description}</p>

              <h4>Incident Timeline:</h4>
              <div className="incident-timeline">
                {(selectedIncident.timeline_entries || []).map((ent) => (
                  <div key={ent.id} className="timeline-entry">
                    <span className="timeline-dot" />
                    <div className="timeline-meta">{new Date(ent.created_at).toLocaleTimeString()} • {ent.entry_type}</div>
                    <div className="timeline-msg">{ent.message}</div>
                  </div>
                ))}
              </div>

              {selectedIncident.action_items && selectedIncident.action_items.length > 0 && (
                <div>
                  <h4>Action Items:</h4>
                  <ul style={{ paddingLeft: 20 }}>
                    {selectedIncident.action_items.map((act) => (
                      <li key={act.id} style={{ fontSize: '0.85rem', marginBottom: 4 }}>
                        {act.action_description}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
