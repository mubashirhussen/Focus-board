import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  FileText,
  AlertTriangle,
  Users,
  Lock,
  Plus,
  CheckCircle2,
  Clock,
  ExternalLink,
  RefreshCw,
  Search,
  Filter,
  Download,
  AlertCircle
} from 'lucide-react';
import { securityComplianceApi } from '../../services/securityComplianceApi';
import './SecurityComplianceDashboard.css';

export default function SecurityComplianceDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [overview, setOverview] = useState(null);
  const [controls, setControls] = useState([]);
  const [frameworkFilter, setFrameworkFilter] = useState('');
  const [policies, setPolicies] = useState([]);
  const [risks, setRisks] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [privacyRequests, setPrivacyRequests] = useState([]);

  // Modals
  const [selectedControl, setSelectedControl] = useState(null);
  const [controlEvidence, setControlEvidence] = useState([]);
  const [evidenceName, setEvidenceName] = useState('');
  const [evidenceType, setEvidenceType] = useState('AUDIT_LOG');
  const [evidenceUrl, setEvidenceUrl] = useState('');

  const [showRiskModal, setShowRiskModal] = useState(false);
  const [newRisk, setNewRisk] = useState({
    risk_code: '',
    title: '',
    description: '',
    category: 'APP_SEC',
    severity: 'MEDIUM',
    likelihood: 'MEDIUM',
    impact: 'MEDIUM',
    mitigation_plan: ''
  });

  const [showIncidentModal, setShowIncidentModal] = useState(false);
  const [newIncident, setNewIncident] = useState({
    incident_code: '',
    title: '',
    summary: '',
    severity: 'MEDIUM',
    category: 'UNAUTHORIZED_ACCESS'
  });

  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [actionSuccess, setActionSuccess] = useState('');

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ovData, ctrlData, polData, rskData, incData, privData] = await Promise.all([
        securityComplianceApi.getOverview(),
        securityComplianceApi.listControls(frameworkFilter),
        securityComplianceApi.listPolicies(),
        securityComplianceApi.listRisks(),
        securityComplianceApi.listIncidents(),
        securityComplianceApi.listPrivacyRequests()
      ]);
      setOverview(ovData);
      setControls(ctrlData);
      setPolicies(polData);
      setRisks(rskData);
      setIncidents(incData);
      setPrivacyRequests(privData);
    } catch (err) {
      console.error('Failed to load compliance data:', err);
      setError('Unable to load security compliance data. Please verify your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [frameworkFilter]);

  const handleOpenEvidenceModal = async (ctrl) => {
    setSelectedControl(ctrl);
    try {
      const evList = await securityComplianceApi.listEvidence(ctrl.id);
      setControlEvidence(evList);
    } catch (err) {
      console.error('Failed to load evidence:', err);
    }
  };

  const handleAddEvidence = async (e) => {
    e.preventDefault();
    if (!evidenceName || !selectedControl) return;
    try {
      await securityComplianceApi.addEvidence(selectedControl.id, {
        control_id: selectedControl.id,
        name: evidenceName,
        evidence_type: evidenceType,
        file_url: evidenceUrl || 'internal://verified-telemetry',
        status: 'VALIDATED'
      });
      setEvidenceName('');
      setEvidenceUrl('');
      const evList = await securityComplianceApi.listEvidence(selectedControl.id);
      setControlEvidence(evList);
      setActionSuccess('Evidence record attached successfully');
      setTimeout(() => setActionSuccess(''), 3000);
      loadAllData();
    } catch (err) {
      console.error('Evidence upload failed:', err);
    }
  };

  const handleAcknowledgePolicy = async (pol) => {
    try {
      await securityComplianceApi.acknowledgePolicy(pol.id, pol.version);
      setActionSuccess(`Policy ${pol.title} acknowledged successfully.`);
      setTimeout(() => setActionSuccess(''), 3500);
      const polData = await securityComplianceApi.listPolicies();
      setPolicies(polData);
    } catch (err) {
      console.error('Acknowledgment failed:', err);
    }
  };

  const handleCreateRisk = async (e) => {
    e.preventDefault();
    try {
      await securityComplianceApi.createRisk({
        ...newRisk,
        risk_code: newRisk.risk_code || `RSK-${Math.floor(100 + Math.random() * 900)}`
      });
      setShowRiskModal(false);
      setNewRisk({
        risk_code: '',
        title: '',
        description: '',
        category: 'APP_SEC',
        severity: 'MEDIUM',
        likelihood: 'MEDIUM',
        impact: 'MEDIUM',
        mitigation_plan: ''
      });
      setActionSuccess('Risk logged to enterprise register.');
      setTimeout(() => setActionSuccess(''), 3000);
      const rskData = await securityComplianceApi.listRisks();
      setRisks(rskData);
    } catch (err) {
      console.error('Failed to create risk:', err);
    }
  };

  const handleCreateIncident = async (e) => {
    e.preventDefault();
    try {
      await securityComplianceApi.createIncident({
        ...newIncident,
        incident_code: newIncident.incident_code || `INC-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        status: 'DETECTED'
      });
      setShowIncidentModal(false);
      setNewIncident({
        incident_code: '',
        title: '',
        summary: '',
        severity: 'MEDIUM',
        category: 'UNAUTHORIZED_ACCESS'
      });
      setActionSuccess('Security incident recorded.');
      setTimeout(() => setActionSuccess(''), 3000);
      const incData = await securityComplianceApi.listIncidents();
      setIncidents(incData);
    } catch (err) {
      console.error('Failed to create incident:', err);
    }
  };

  if (loading && !overview) {
    return (
      <div className="security-loading-container">
        <RefreshCw className="animate-spin text-primary" size={32} />
        <p>Loading Enterprise Security & Compliance Center...</p>
      </div>
    );
  }

  return (
    <div className="security-dashboard-container">
      {/* Header */}
      <div className="security-header">
        <div>
          <h1 className="security-title">
            <ShieldCheck className="title-icon" /> Enterprise Security & Compliance
          </h1>
          <p className="security-subtitle">
            SOC 2 / ISO 27001 readiness posture, risk registers, incident response, and privacy governance.
          </p>
        </div>
        <div className="security-header-actions">
          <button className="btn-secondary" onClick={loadAllData} title="Refresh Telemetry">
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert-banner success-banner">
          <CheckCircle2 size={18} /> {actionSuccess}
        </div>
      )}

      {error && (
        <div className="alert-banner error-banner">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Tabs */}
      <div className="security-tabs">
        <button
          className={`sec-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <ShieldCheck size={16} /> Readiness Overview
        </button>
        <button
          className={`sec-tab-btn ${activeTab === 'controls' ? 'active' : ''}`}
          onClick={() => setActiveTab('controls')}
        >
          <FileText size={16} /> Control Register ({controls.length})
        </button>
        <button
          className={`sec-tab-btn ${activeTab === 'risks' ? 'active' : ''}`}
          onClick={() => setActiveTab('risks')}
        >
          <AlertTriangle size={16} /> Risk Register ({risks.length})
        </button>
        <button
          className={`sec-tab-btn ${activeTab === 'incidents' ? 'active' : ''}`}
          onClick={() => setActiveTab('incidents')}
        >
          <ShieldAlert size={16} /> Incidents ({incidents.length})
        </button>
        <button
          className={`sec-tab-btn ${activeTab === 'policies' ? 'active' : ''}`}
          onClick={() => setActiveTab('policies')}
        >
          <Lock size={16} /> Security Policies ({policies.length})
        </button>
        <button
          className={`sec-tab-btn ${activeTab === 'privacy' ? 'active' : ''}`}
          onClick={() => setActiveTab('privacy')}
        >
          <Users size={16} /> Privacy Requests ({privacyRequests.length})
        </button>
      </div>

      {/* TAB 1: READINESS OVERVIEW */}
      {activeTab === 'overview' && overview && (
        <div className="sec-tab-content">
          <div className="overview-cards-grid">
            <div className="sec-card readiness-hero-card">
              <span className="card-label">Overall Compliance Readiness</span>
              <div className="readiness-score-display">
                <span className="big-percentage">{overview.overall_readiness_percentage}%</span>
                <span className="readiness-sublabel">Controls Implemented & Validated</span>
              </div>
              <div className="progress-bar-bg">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${overview.overall_readiness_percentage}%` }}
                />
              </div>
              <div className="readiness-meta-row">
                <span>{overview.implemented_controls} of {overview.total_controls} Controls Active</span>
                <span>Audit Readiness: High</span>
              </div>
            </div>

            <div className="sec-card framework-card">
              <span className="card-label">Framework Breakdown</span>
              <div className="frameworks-list">
                {overview.frameworks.map((fw) => (
                  <div key={fw.framework} className="fw-item">
                    <div className="fw-header">
                      <strong>{fw.framework}</strong>
                      <span>{fw.readiness_percentage}%</span>
                    </div>
                    <div className="progress-bar-bg small">
                      <div
                        className="progress-bar-fill accent"
                        style={{ width: `${fw.readiness_percentage}%` }}
                      />
                    </div>
                    <div className="fw-footer">
                      {fw.implemented_controls} / {fw.total_controls} Implemented
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="sec-card quick-stats-card">
              <span className="card-label">Operational Posture</span>
              <div className="quick-stats-grid">
                <div className="stat-box">
                  <span className="stat-num">{overview.active_risks_count}</span>
                  <span className="stat-desc">Active Risks</span>
                </div>
                <div className="stat-box">
                  <span className="stat-num">{overview.open_incidents_count}</span>
                  <span className="stat-desc">Open Incidents</span>
                </div>
                <div className="stat-box">
                  <span className="stat-num">{overview.approved_policies_count}</span>
                  <span className="stat-desc">Active Policies</span>
                </div>
                <div className="stat-box">
                  <span className="stat-num">{overview.verified_vendors_count}</span>
                  <span className="stat-desc">Audited Vendors</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: CONTROLS REGISTER */}
      {activeTab === 'controls' && (
        <div className="sec-tab-content">
          <div className="controls-filter-bar">
            <div className="pill-group">
              <button
                className={`pill-btn ${frameworkFilter === '' ? 'active' : ''}`}
                onClick={() => setFrameworkFilter('')}
              >
                All Frameworks
              </button>
              <button
                className={`pill-btn ${frameworkFilter === 'SOC2' ? 'active' : ''}`}
                onClick={() => setFrameworkFilter('SOC2')}
              >
                SOC 2
              </button>
              <button
                className={`pill-btn ${frameworkFilter === 'ISO27001' ? 'active' : ''}`}
                onClick={() => setFrameworkFilter('ISO27001')}
              >
                ISO 27001
              </button>
              <button
                className={`pill-btn ${frameworkFilter === 'GDPR' ? 'active' : ''}`}
                onClick={() => setFrameworkFilter('GDPR')}
              >
                GDPR
              </button>
            </div>
          </div>

          <div className="sec-table-wrapper">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Control ID</th>
                  <th>Framework</th>
                  <th>Title & Description</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Evidence</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {controls.map((ctrl) => (
                  <tr key={ctrl.id}>
                    <td><strong className="code-tag">{ctrl.control_id}</strong></td>
                    <td><span className="badge-framework">{ctrl.framework}</span></td>
                    <td>
                      <div className="ctrl-title">{ctrl.title}</div>
                      <div className="ctrl-desc">{ctrl.description}</div>
                    </td>
                    <td><span className="category-tag">{ctrl.category}</span></td>
                    <td>
                      <span className={`status-pill ${ctrl.status.toLowerCase()}`}>
                        {ctrl.status}
                      </span>
                    </td>
                    <td>
                      <span className="evidence-badge">
                        {ctrl.evidence_count} attached
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn-sm btn-outline"
                        onClick={() => handleOpenEvidenceModal(ctrl)}
                      >
                        Evidence
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: RISKS REGISTER */}
      {activeTab === 'risks' && (
        <div className="sec-tab-content">
          <div className="tab-actions-header">
            <h3>Enterprise Risk Register</h3>
            <button className="btn-primary" onClick={() => setShowRiskModal(true)}>
              <Plus size={16} /> Log Security Risk
            </button>
          </div>

          <div className="sec-table-wrapper">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Risk Code</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Likelihood</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                  <th>Mitigation Plan</th>
                </tr>
              </thead>
              <tbody>
                {risks.map((rsk) => (
                  <tr key={rsk.id}>
                    <td><strong className="code-tag">{rsk.risk_code}</strong></td>
                    <td>{rsk.title}</td>
                    <td><span className="category-tag">{rsk.category}</span></td>
                    <td><span className={`badge-severity ${rsk.severity.toLowerCase()}`}>{rsk.severity}</span></td>
                    <td>{rsk.likelihood}</td>
                    <td>
                      <span className={`score-badge ${rsk.risk_score >= 12 ? 'high' : 'normal'}`}>
                        {rsk.risk_score}
                      </span>
                    </td>
                    <td><span className={`status-pill ${rsk.status.toLowerCase()}`}>{rsk.status}</span></td>
                    <td><div className="mitigation-text">{rsk.mitigation_plan || 'Pending formulation'}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: INCIDENTS */}
      {activeTab === 'incidents' && (
        <div className="sec-tab-content">
          <div className="tab-actions-header">
            <h3>Security Incidents & Response Lifecycle</h3>
            <button className="btn-primary" onClick={() => setShowIncidentModal(true)}>
              <Plus size={16} /> Report Incident
            </button>
          </div>

          <div className="sec-table-wrapper">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Incident Code</th>
                  <th>Title & Summary</th>
                  <th>Severity</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Detected At</th>
                  <th>Root Cause</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((inc) => (
                  <tr key={inc.id}>
                    <td><strong className="code-tag">{inc.incident_code}</strong></td>
                    <td>
                      <div className="ctrl-title">{inc.title}</div>
                      <div className="ctrl-desc">{inc.summary}</div>
                    </td>
                    <td><span className={`badge-severity ${inc.severity.toLowerCase()}`}>{inc.severity}</span></td>
                    <td><span className="category-tag">{inc.category}</span></td>
                    <td><span className={`status-pill ${inc.status.toLowerCase()}`}>{inc.status}</span></td>
                    <td>{new Date(inc.detected_at).toLocaleDateString()}</td>
                    <td><div className="mitigation-text">{inc.root_cause || 'Investigation active'}</div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 5: POLICIES */}
      {activeTab === 'policies' && (
        <div className="sec-tab-content">
          <div className="tab-actions-header">
            <h3>Approved Information Security & Privacy Policies</h3>
          </div>

          <div className="policies-cards-grid">
            {policies.map((pol) => (
              <div key={pol.id} className="sec-card policy-card">
                <div className="policy-header">
                  <span className="category-tag">{pol.category}</span>
                  <span className="version-tag">v{pol.version}</span>
                </div>
                <h4 className="policy-title">{pol.title}</h4>
                <p className="policy-desc">{pol.content.slice(0, 160)}...</p>
                <div className="policy-footer">
                  <button
                    className="btn-sm btn-outline"
                    onClick={() => setSelectedPolicy(pol)}
                  >
                    View Document
                  </button>
                  <button
                    className="btn-sm btn-primary"
                    onClick={() => handleAcknowledgePolicy(pol)}
                  >
                    <CheckCircle2 size={14} /> Acknowledge
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: PRIVACY REQUESTS */}
      {activeTab === 'privacy' && (
        <div className="sec-tab-content">
          <div className="tab-actions-header">
            <h3>GDPR & CCPA Data Subject Requests</h3>
          </div>

          <div className="sec-table-wrapper">
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Type</th>
                  <th>Requester</th>
                  <th>Status</th>
                  <th>Requested At</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {privacyRequests.map((req) => (
                  <tr key={req.id}>
                    <td><strong className="code-tag">{req.id.slice(0, 12)}</strong></td>
                    <td><span className="badge-framework">{req.request_type}</span></td>
                    <td>{req.requester_email}</td>
                    <td><span className={`status-pill ${req.status.toLowerCase()}`}>{req.status}</span></td>
                    <td>{new Date(req.requested_at).toLocaleDateString()}</td>
                    <td>{req.details || 'Standard user subject request'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* MODAL: EVIDENCE */}
      {selectedControl && (
        <div className="sec-modal-overlay" onClick={() => setSelectedControl(null)}>
          <div className="sec-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Evidence Management: {selectedControl.control_id}</h3>
              <button className="close-btn" onClick={() => setSelectedControl(null)}>×</button>
            </div>
            <div className="modal-body">
              <p><strong>{selectedControl.title}</strong></p>
              <div className="existing-evidence-list">
                <h4>Attached Evidence ({controlEvidence.length})</h4>
                {controlEvidence.length === 0 ? (
                  <p className="empty-hint">No audit evidence attached yet.</p>
                ) : (
                  controlEvidence.map((ev) => (
                    <div key={ev.id} className="evidence-item-row">
                      <div>
                        <strong>{ev.name}</strong> ({ev.evidence_type})
                        <div className="ev-subtext">{ev.file_url || 'Internal Telemetry'}</div>
                      </div>
                      <span className="badge-framework">{ev.status}</span>
                    </div>
                  ))
                )}
              </div>

              <form onSubmit={handleAddEvidence} className="add-evidence-form">
                <h4>Attach New Evidence</h4>
                <div className="form-group">
                  <label>Evidence Title</label>
                  <input
                    type="text"
                    required
                    value={evidenceName}
                    onChange={(e) => setEvidenceName(e.target.value)}
                    placeholder="e.g. IAM Least Privilege Report Q1"
                  />
                </div>
                <div className="form-group">
                  <label>Evidence Type</label>
                  <select
                    value={evidenceType}
                    onChange={(e) => setEvidenceType(e.target.value)}
                  >
                    <option value="AUDIT_LOG">Audit Log Extract</option>
                    <option value="CONFIG_RECORD">Configuration Record</option>
                    <option value="POLICY_DOCUMENT">Policy Document</option>
                    <option value="TEST_REPORT">Automated Test Report</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Artifact Location / URI</label>
                  <input
                    type="text"
                    value={evidenceUrl}
                    onChange={(e) => setEvidenceUrl(e.target.value)}
                    placeholder="s3://focusboard-audit/... or internal link"
                  />
                </div>
                <button type="submit" className="btn-primary">Attach Evidence</button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: LOG RISK */}
      {showRiskModal && (
        <div className="sec-modal-overlay" onClick={() => setShowRiskModal(false)}>
          <div className="sec-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Log Security Risk</h3>
              <button className="close-btn" onClick={() => setShowRiskModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateRisk} className="modal-body form-grid">
              <div className="form-group">
                <label>Risk Title</label>
                <input
                  type="text"
                  required
                  value={newRisk.title}
                  onChange={(e) => setNewRisk({ ...newRisk, title: e.target.value })}
                  placeholder="e.g. Unauthenticated API Rate Spikes"
                />
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newRisk.category}
                  onChange={(e) => setNewRisk({ ...newRisk, category: e.target.value })}
                >
                  <option value="APP_SEC">Application Security</option>
                  <option value="INFRASTRUCTURE">Cloud Infrastructure</option>
                  <option value="DATA_PROTECTION">Data Protection</option>
                  <option value="PRIVACY">User Privacy</option>
                  <option value="AI_SECURITY">AI & Copilot Safety</option>
                </select>
              </div>
              <div className="form-group">
                <label>Severity</label>
                <select
                  value={newRisk.severity}
                  onChange={(e) => setNewRisk({ ...newRisk, severity: e.target.value })}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
              <div className="form-group">
                <label>Likelihood</label>
                <select
                  value={newRisk.likelihood}
                  onChange={(e) => setNewRisk({ ...newRisk, likelihood: e.target.value })}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                </select>
              </div>
              <div className="form-group full-width">
                <label>Mitigation Strategy</label>
                <textarea
                  rows={3}
                  value={newRisk.mitigation_plan}
                  onChange={(e) => setNewRisk({ ...newRisk, mitigation_plan: e.target.value })}
                  placeholder="Planned countermeasures and architectural safeguards..."
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowRiskModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Record Risk</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: REPORT INCIDENT */}
      {showIncidentModal && (
        <div className="sec-modal-overlay" onClick={() => setShowIncidentModal(false)}>
          <div className="sec-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Report Security Incident</h3>
              <button className="close-btn" onClick={() => setShowIncidentModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateIncident} className="modal-body form-grid">
              <div className="form-group full-width">
                <label>Incident Summary Title</label>
                <input
                  type="text"
                  required
                  value={newIncident.title}
                  onChange={(e) => setNewIncident({ ...newIncident, title: e.target.value })}
                  placeholder="e.g. Abnormal token usage detected on enterprise endpoint"
                />
              </div>
              <div className="form-group">
                <label>Severity</label>
                <select
                  value={newIncident.severity}
                  onChange={(e) => setNewIncident({ ...newIncident, severity: e.target.value })}
                >
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newIncident.category}
                  onChange={(e) => setNewIncident({ ...newIncident, category: e.target.value })}
                >
                  <option value="UNAUTHORIZED_ACCESS">Unauthorized Access</option>
                  <option value="DATA_EXPOSURE">Data Exposure</option>
                  <option value="API_ABUSE">API Abuse / Rate Spike</option>
                  <option value="AI_EXPLOIT">AI / Model Exploit</option>
                </select>
              </div>
              <div className="form-group full-width">
                <label>Incident Description & Initial Observations</label>
                <textarea
                  rows={3}
                  required
                  value={newIncident.summary}
                  onChange={(e) => setNewIncident({ ...newIncident, summary: e.target.value })}
                  placeholder="Describe timeline, affected components, and initial triage..."
                />
              </div>
              <div className="modal-footer">
                <button type="button" className="btn-secondary" onClick={() => setShowIncidentModal(false)}>Cancel</button>
                <button type="submit" className="btn-primary">Initiate Incident Response</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: VIEW POLICY */}
      {selectedPolicy && (
        <div className="sec-modal-overlay" onClick={() => setSelectedPolicy(null)}>
          <div className="sec-modal-box" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedPolicy.title} (v{selectedPolicy.version})</h3>
              <button className="close-btn" onClick={() => setSelectedPolicy(null)}>×</button>
            </div>
            <div className="modal-body policy-content-view">
              <pre>{selectedPolicy.content}</pre>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setSelectedPolicy(null)}>Close</button>
              <button
                className="btn-primary"
                onClick={() => {
                  handleAcknowledgePolicy(selectedPolicy);
                  setSelectedPolicy(null);
                }}
              >
                Acknowledge Policy
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
