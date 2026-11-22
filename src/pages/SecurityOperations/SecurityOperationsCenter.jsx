import React, { useState, useEffect } from 'react';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Lock,
  UserCheck,
  Key,
  Terminal,
  Activity,
  Search,
  RefreshCw,
  Plus,
  CheckCircle2,
  XCircle,
  Eye,
  FileText,
  Sparkles,
  ChevronRight,
  Filter,
} from 'lucide-react';
import { securityIntelligenceApi } from '../../services/securityIntelligenceApi';
import './SecurityOperationsCenter.css';

export default function SecurityOperationsCenter() {
  const [activeTab, setActiveTab] = useState('posture');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [posture, setPosture] = useState(null);
  const [events, setEvents] = useState([]);
  const [rules, setRules] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [identityRisks, setIdentityRisks] = useState([]);
  const [accessReviews, setAccessReviews] = useState([]);
  const [vulnerabilities, setVulnerabilities] = useState([]);

  // AI Assistant State
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);

  // Filters
  const [eventFilter, setEventFilter] = useState('');
  const [alertSeverityFilter, setAlertSeverityFilter] = useState('');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [posRes, evRes, rleRes, altRes, irRes, arRes, vulnRes] = await Promise.all([
        securityIntelligenceApi.getPosture().catch(() => null),
        securityIntelligenceApi.listEvents({ limit: 40 }).catch(() => null),
        securityIntelligenceApi.listDetectionRules().catch(() => null),
        securityIntelligenceApi.listAlerts().catch(() => null),
        securityIntelligenceApi.listIdentityRisks().catch(() => null),
        securityIntelligenceApi.listAccessReviews().catch(() => null),
        securityIntelligenceApi.listVulnerabilities().catch(() => null),
      ]);

      if (posRes?.data) setPosture(posRes.data);
      if (evRes?.data) setEvents(evRes.data);
      if (rleRes?.data) setRules(rleRes.data);
      if (altRes?.data) setAlerts(altRes.data);
      if (irRes?.data) setIdentityRisks(irRes.data);
      if (arRes?.data) setAccessReviews(arRes.data);
      if (vulnRes?.data) setVulnerabilities(vulnRes.data);
    } catch (err) {
      setError(err?.message || 'Failed to load security intelligence records');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleResolveAlert = async (alertId) => {
    try {
      await securityIntelligenceApi.updateAlert(alertId, { status: 'RESOLVED' });
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'RESOLVED', resolved_at: new Date().toISOString() } : a))
      );
    } catch (err) {
      alert('Failed to resolve alert: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAccessDecision = async (campaignId, recordId, decision) => {
    try {
      await securityIntelligenceApi.recordAccessDecision(campaignId, recordId, {
        decision,
        justification: `Decision recorded from SOC Console (${decision})`,
      });
      loadData();
    } catch (err) {
      alert('Failed to record review decision: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleToggleVuln = async (vulnId, currentStatus) => {
    const newStatus = currentStatus === 'RESOLVED' ? 'OPEN' : 'RESOLVED';
    try {
      await securityIntelligenceApi.updateVulnerability(vulnId, { remediation_status: newStatus });
      setVulnerabilities((prev) =>
        prev.map((v) => (v.id === vulnId ? { ...v, remediation_status: newStatus } : v))
      );
    } catch (err) {
      alert('Failed to update vulnerability: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAskAssistant = async (e) => {
    e?.preventDefault();
    if (!aiQuery.trim()) return;
    setAiLoading(true);
    setAiResponse(null);
    try {
      const res = await securityIntelligenceApi.askAssistant(aiQuery);
      setAiResponse(res.data);
    } catch (err) {
      alert('AI Assistant failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAiLoading(false);
    }
  };

  return (
    <div className="soc-container">
      {/* Header */}
      <div className="soc-header">
        <div className="soc-title-area">
          <div className="soc-icon-badge">
            <Shield className="soc-icon" />
          </div>
          <div>
            <h1>Security Operations Center (SOC)</h1>
            <p className="soc-subtitle">
              Zero-Trust continuous security posture, threat detection, identity risk, and compliance operations.
            </p>
          </div>
        </div>
        <div className="soc-header-actions">
          <button className="soc-btn-outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`soc-btn-icon ${loading ? 'spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="soc-tabs">
        <button
          className={`soc-tab ${activeTab === 'posture' ? 'active' : ''}`}
          onClick={() => setActiveTab('posture')}
        >
          <ShieldCheck className="tab-icon" /> Posture & Overview
        </button>
        <button
          className={`soc-tab ${activeTab === 'events' ? 'active' : ''}`}
          onClick={() => setActiveTab('events')}
        >
          <Activity className="tab-icon" /> Security Events ({events.length})
        </button>
        <button
          className={`soc-tab ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          <ShieldAlert className="tab-icon" /> Alerts ({alerts.filter((a) => a.status === 'OPEN').length})
        </button>
        <button
          className={`soc-tab ${activeTab === 'threats' ? 'active' : ''}`}
          onClick={() => setActiveTab('threats')}
        >
          <Lock className="tab-icon" /> Threat Rules ({rules.length})
        </button>
        <button
          className={`soc-tab ${activeTab === 'identity' ? 'active' : ''}`}
          onClick={() => setActiveTab('identity')}
        >
          <UserCheck className="tab-icon" /> Identity & Access Reviews
        </button>
        <button
          className={`soc-tab ${activeTab === 'vulnerabilities' ? 'active' : ''}`}
          onClick={() => setActiveTab('vulnerabilities')}
        >
          <AlertTriangle className="tab-icon" /> Vulnerabilities ({vulnerabilities.length})
        </button>
        <button
          className={`soc-tab ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <Sparkles className="tab-icon" /> AI Security Assistant
        </button>
      </div>

      {error && <div className="soc-banner-error">{error}</div>}

      {/* TAB 1: POSTURE & OVERVIEW */}
      {activeTab === 'posture' && (
        <div className="soc-tab-content">
          <div className="soc-kpi-grid">
            <div className="soc-kpi-card posture-score-card">
              <span className="kpi-label">Zero-Trust Posture Score</span>
              <div className="score-display">
                <span className="score-number">{posture?.overall_posture_score ?? 88}</span>
                <span className="score-max">/100</span>
              </div>
              <span className="kpi-subtext">Continuous real-time policy evaluation</span>
            </div>
            <div className="soc-kpi-card">
              <span className="kpi-label">MFA Adoption Rate</span>
              <div className="kpi-value">{posture?.mfa_adoption_pct ?? 0}%</div>
              <span className="kpi-subtext">Enforced on admin & privileged roles</span>
            </div>
            <div className="soc-kpi-card">
              <span className="kpi-label">Open Critical Alerts</span>
              <div className="kpi-value warning-text">{posture?.open_critical_alerts ?? 0}</div>
              <span className="kpi-subtext">Requiring active SOC investigation</span>
            </div>
            <div className="soc-kpi-card">
              <span className="kpi-label">Vulnerability Resolution</span>
              <div className="kpi-value">{posture?.vulnerability_resolution_pct ?? 100}%</div>
              <span className="kpi-subtext">Patched within SLA timeframe</span>
            </div>
          </div>

          <div className="soc-section-card">
            <h3>Control Domain Assessments</h3>
            <div className="category-scores-grid">
              {posture?.category_scores &&
                Object.entries(posture.category_scores).map(([cat, score]) => (
                  <div key={cat} className="category-score-item">
                    <div className="category-header">
                      <span className="category-name">{cat.replace('_', ' ')}</span>
                      <span className="category-val">{score}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div className="progress-bar-fill" style={{ width: `${score}%` }}></div>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: SECURITY EVENTS */}
      {activeTab === 'events' && (
        <div className="soc-tab-content">
          <div className="soc-filter-bar">
            <input
              type="text"
              placeholder="Filter by event type (e.g. LOGIN_SUCCESS, MFA_ENABLED)..."
              value={eventFilter}
              onChange={(e) => setEventFilter(e.target.value)}
              className="soc-search-input"
            />
          </div>
          <div className="soc-table-wrapper">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Event Type</th>
                  <th>Severity</th>
                  <th>Actor Email</th>
                  <th>Target Entity</th>
                  <th>Source</th>
                  <th>Evidence</th>
                </tr>
              </thead>
              <tbody>
                {events
                  .filter((ev) => !eventFilter || ev.event_type.toLowerCase().includes(eventFilter.toLowerCase()))
                  .map((ev) => (
                    <tr key={ev.id}>
                      <td className="time-cell">{new Date(ev.created_at).toLocaleString()}</td>
                      <td>
                        <span className="event-type-badge">{ev.event_type}</span>
                      </td>
                      <td>
                        <span className={`badge-severity ${ev.severity.toLowerCase()}`}>{ev.severity}</span>
                      </td>
                      <td>{ev.actor_email || 'System'}</td>
                      <td>{ev.target_entity || 'N/A'}</td>
                      <td>{ev.source}</td>
                      <td className="code-cell">{ev.evidence_json}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: SECURITY ALERTS */}
      {activeTab === 'alerts' && (
        <div className="soc-tab-content">
          <div className="alerts-list">
            {alerts.length === 0 ? (
              <div className="empty-state">No active security alerts registered.</div>
            ) : (
              alerts.map((alt) => (
                <div key={alt.id} className={`alert-card ${alt.status.toLowerCase()}`}>
                  <div className="alert-card-header">
                    <div className="alert-header-left">
                      <span className={`badge-severity ${alt.severity.toLowerCase()}`}>{alt.severity}</span>
                      <span className="alert-code">{alt.alert_code}</span>
                      <h4>{alt.title}</h4>
                    </div>
                    <span className={`badge-status ${alt.status.toLowerCase()}`}>{alt.status}</span>
                  </div>
                  <p className="alert-desc">{alt.description}</p>
                  <div className="alert-footer">
                    <span className="alert-time">Created: {new Date(alt.created_at).toLocaleString()}</span>
                    {alt.status === 'OPEN' && (
                      <button className="soc-btn-sm" onClick={() => handleResolveAlert(alt.id)}>
                        <CheckCircle2 className="btn-icon-sm" /> Mark Resolved
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* TAB 4: THREAT DETECTION RULES */}
      {activeTab === 'threats' && (
        <div className="soc-tab-content">
          <div className="rules-grid">
            {rules.map((rule) => (
              <div key={rule.id} className="rule-card">
                <div className="rule-card-header">
                  <span className="rule-code">{rule.rule_code}</span>
                  <span className={`badge-severity ${rule.severity.toLowerCase()}`}>{rule.severity}</span>
                </div>
                <h4>{rule.name}</h4>
                <p className="rule-desc">{rule.description}</p>
                <div className="rule-meta">
                  <span>Event: <code>{rule.event_type}</code></span>
                  <span>Threshold: <strong>{rule.threshold_count} in {rule.time_window_seconds}s</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 5: IDENTITY & ACCESS REVIEWS */}
      {activeTab === 'identity' && (
        <div className="soc-tab-content">
          <div className="soc-section-card">
            <h3>Privileged Access Review Campaigns</h3>
            {accessReviews.map((camp) => (
              <div key={camp.id} className="campaign-box">
                <div className="campaign-header">
                  <div>
                    <h4>{camp.title}</h4>
                    <p className="campaign-sub">Scope: {camp.scope_type} | Status: {camp.status}</p>
                  </div>
                  <span className={`badge-status ${camp.status.toLowerCase()}`}>{camp.status}</span>
                </div>
                {camp.records && camp.records.length > 0 && (
                  <table className="soc-table-inner">
                    <thead>
                      <tr>
                        <th>Role / Entitlement</th>
                        <th>Resource Name</th>
                        <th>Decision</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {camp.records.map((rec) => (
                        <tr key={rec.id}>
                          <td><code>{rec.role_or_permission}</code></td>
                          <td>{rec.resource_name}</td>
                          <td>
                            <span className={`badge-decision ${rec.decision.toLowerCase()}`}>
                              {rec.decision}
                            </span>
                          </td>
                          <td>
                            {rec.decision === 'PENDING' && (
                              <div className="action-btn-group">
                                <button
                                  className="btn-approve-sm"
                                  onClick={() => handleAccessDecision(camp.id, rec.id, 'APPROVED')}
                                >
                                  Approve
                                </button>
                                <button
                                  className="btn-revoke-sm"
                                  onClick={() => handleAccessDecision(camp.id, rec.id, 'REVOKED')}
                                >
                                  Revoke
                                </button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 6: VULNERABILITIES */}
      {activeTab === 'vulnerabilities' && (
        <div className="soc-tab-content">
          <div className="soc-table-wrapper">
            <table className="soc-table">
              <thead>
                <tr>
                  <th>CVE / Advisory</th>
                  <th>Title</th>
                  <th>Component</th>
                  <th>Severity</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {vulnerabilities.map((v) => (
                  <tr key={v.id}>
                    <td><strong>{v.cve_id}</strong></td>
                    <td>{v.title}</td>
                    <td><code>{v.component}</code></td>
                    <td>
                      <span className={`badge-severity ${v.severity.toLowerCase()}`}>{v.severity}</span>
                    </td>
                    <td>{v.source}</td>
                    <td>
                      <span className={`badge-status ${v.remediation_status.toLowerCase()}`}>
                        {v.remediation_status}
                      </span>
                    </td>
                    <td>
                      <button
                        className="soc-btn-sm"
                        onClick={() => handleToggleVuln(v.id, v.remediation_status)}
                      >
                        {v.remediation_status === 'RESOLVED' ? 'Reopen' : 'Mark Patched'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 7: AI SECURITY ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="soc-tab-content">
          <div className="ai-assistant-card">
            <div className="ai-header">
              <Sparkles className="ai-icon" />
              <div>
                <h3>Grounded AI Security Analyst</h3>
                <p>Natural language answers backed strictly by verified security logs, telemetry, and CVE records.</p>
              </div>
            </div>

            <form onSubmit={handleAskAssistant} className="ai-query-form">
              <input
                type="text"
                placeholder="Ask about active alerts, zero-trust posture score, or patch recommendations..."
                value={aiQuery}
                onChange={(e) => setAiQuery(e.target.value)}
                className="ai-input"
              />
              <button type="submit" className="soc-btn-primary" disabled={aiLoading || !aiQuery.trim()}>
                {aiLoading ? 'Analyzing...' : 'Ask Analyst'}
              </button>
            </form>

            {aiResponse && (
              <div className="ai-response-box">
                <div className="response-header">
                  <span className="badge-grounded">Verified Grounded Telemetry</span>
                  <span className="posture-chip">Current Score: {aiResponse.posture_score}/100</span>
                </div>
                <p className="ai-answer-text">{aiResponse.answer}</p>
                {aiResponse.recommended_actions?.length > 0 && (
                  <div className="recommendations-box">
                    <strong>Recommended Actions:</strong>
                    <ul>
                      {aiResponse.recommended_actions.map((act, idx) => (
                        <li key={idx}>{act}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
