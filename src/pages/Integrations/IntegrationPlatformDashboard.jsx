import React, { useState, useEffect } from 'react';
import {
  Layers,
  Calendar,
  MessageSquare,
  GitBranch,
  Power,
  RefreshCw,
  Plus,
  CheckCircle2,
  XCircle,
  AlertCircle,
  ExternalLink,
  ShieldCheck,
  Send,
  Sliders,
  Check,
  Activity,
  Terminal,
  Download,
  Key,
} from 'lucide-react';
import { integrationPlatformApi } from '../../services/integrationPlatformApi';
import './IntegrationPlatformDashboard.css';

export default function IntegrationPlatformDashboard() {
  const [activeTab, setActiveTab] = useState('connectors');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data
  const [providers, setProviders] = useState([]);
  const [marketplaceListings, setMarketplaceListings] = useState([]);
  const [installations, setInstallations] = useState([]);
  const [connectors, setConnectors] = useState([]);
  const [analytics, setAnalytics] = useState(null);

  // Consent & Install Modal
  const [selectedListing, setSelectedListing] = useState(null);
  const [consentGranted, setConsentGranted] = useState(true);
  const [installing, setInstalling] = useState(false);

  // Webhook Simulator
  const [webhookUrl, setWebhookUrl] = useState('https://webhook.site/mock-focusboard-receiver');
  const [webhookSecret, setWebhookSecret] = useState('sec_fb_enterprise_key_98234');
  const [webhookEvent, setWebhookEvent] = useState('task.created');
  const [webhookResult, setWebhookResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [provRes, listRes, instRes, connRes, anaRes] = await Promise.all([
        integrationPlatformApi.listProviders().catch(() => []),
        integrationPlatformApi.listMarketplaceListings().catch(() => []),
        integrationPlatformApi.listWorkspaceInstallations(1).catch(() => []),
        integrationPlatformApi.listConnectors(1).catch(() => []),
        integrationPlatformApi.getPlatformAnalytics().catch(() => null),
      ]);
      setProviders(provRes || []);
      setMarketplaceListings(listRes || []);
      setInstallations(instRes || []);
      setConnectors(connRes || []);
      setAnalytics(anaRes);
    } catch (err) {
      setError(err.message || 'Failed to load integration ecosystem data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Connect / Disconnect Provider
  const handleToggleConnector = async (providerId, currentStatus, connectorId) => {
    try {
      if (currentStatus === 'CONNECTED' && connectorId) {
        await integrationPlatformApi.disconnectConnector(connectorId);
        alert('Connector disconnected');
      } else {
        await integrationPlatformApi.connectConnector(providerId, 1, `workspace-admin-${providerId}`);
        alert('Provider authorized and connected!');
      }
      loadData();
    } catch (err) {
      alert(`Connector action failed: ${err.message}`);
    }
  };

  // Install Marketplace App
  const handleInstallApp = async () => {
    if (!selectedListing || !consentGranted) return;
    setInstalling(true);
    try {
      await integrationPlatformApi.installMarketplaceApp(
        selectedListing.id,
        1,
        selectedListing.permissions_list || ['tasks:read']
      );
      setSelectedListing(null);
      setActiveTab('installed');
      loadData();
      alert(`${selectedListing.title} successfully installed to workspace!`);
    } catch (err) {
      alert(`Installation failed: ${err.message}`);
    } finally {
      setInstalling(false);
    }
  };

  // Test Webhook Delivery
  const handleTestWebhook = async (e) => {
    e.preventDefault();
    setSimulating(true);
    try {
      const res = await integrationPlatformApi.testWebhookDelivery(
        webhookUrl,
        webhookSecret,
        webhookEvent
      );
      setWebhookResult(res);
    } catch (err) {
      alert(`Webhook test simulation failed: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="platform-container">
      {/* Header */}
      <div className="platform-header">
        <div className="platform-title-area">
          <h1>
            <Layers size={28} color="#3b82f6" />
            Integrations Ecosystem & Developer API Platform
          </h1>
          <p className="platform-subtitle">
            Enterprise third-party application connectivity, OAuth connectors, verified marketplace catalog, HMAC-SHA256 webhooks, and developer platform analytics.
          </p>
        </div>
        <div>
          <button className="btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="platform-metrics-grid">
        <div className="platform-metric-card">
          <div className="metric-icon-wrap">
            <Activity size={20} />
          </div>
          <div>
            <div className="metric-val">{analytics?.total_requests ?? 0}</div>
            <div className="metric-lbl">Total API Requests</div>
          </div>
        </div>

        <div className="platform-metric-card">
          <div className="metric-icon-wrap success">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="metric-val">{analytics?.avg_response_time_ms ?? 28}ms</div>
            <div className="metric-lbl">Average Latency</div>
          </div>
        </div>

        <div className="platform-metric-card">
          <div className="metric-icon-wrap warning">
            <Key size={20} />
          </div>
          <div>
            <div className="metric-val">{analytics?.active_webhooks_count ?? 2}</div>
            <div className="metric-lbl">Active Webhooks</div>
          </div>
        </div>

        <div className="platform-metric-card">
          <div className="metric-icon-wrap purple">
            <Layers size={20} />
          </div>
          <div>
            <div className="metric-val">{analytics?.installed_marketplace_apps_count ?? installations.length}</div>
            <div className="metric-lbl">Installed Apps</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="platform-tabs">
        <button
          className={`platform-tab-btn ${activeTab === 'connectors' ? 'active' : ''}`}
          onClick={() => setActiveTab('connectors')}
        >
          <Power size={16} />
          OAuth Connectors ({providers.length})
        </button>

        <button
          className={`platform-tab-btn ${activeTab === 'marketplace' ? 'active' : ''}`}
          onClick={() => setActiveTab('marketplace')}
        >
          <Layers size={16} />
          App Marketplace ({marketplaceListings.length})
        </button>

        <button
          className={`platform-tab-btn ${activeTab === 'installed' ? 'active' : ''}`}
          onClick={() => setActiveTab('installed')}
        >
          <CheckCircle2 size={16} />
          Installed Apps ({installations.length})
        </button>

        <button
          className={`platform-tab-btn ${activeTab === 'webhook_simulator' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhook_simulator')}
        >
          <Terminal size={16} />
          Webhook Testing Sandbox
        </button>

        <button
          className={`platform-tab-btn ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          <Activity size={16} />
          Platform Analytics
        </button>
      </div>

      {/* TAB: CONNECTORS */}
      {activeTab === 'connectors' && (
        <div className="cards-grid">
          {providers.map((prov) => {
            const connector = connectors.find((c) => c.provider_id === prov.id);
            const isConnected = connector?.connection_status === 'CONNECTED';

            return (
              <div key={prov.id} className="app-card">
                <div>
                  <div className="app-card-header">
                    <div className="app-icon-wrap">
                      {prov.name[0]}
                    </div>
                    <div className="app-title-group">
                      <h3>{prov.name}</h3>
                      <span className="app-category-badge">{prov.category}</span>
                    </div>
                  </div>
                  <p className="app-card-desc">{prov.description}</p>
                  <div className="features-tags">
                    {(prov.features_list || []).map((feat, idx) => (
                      <span key={idx} className="feature-tag">{feat}</span>
                    ))}
                  </div>
                </div>

                <div className="app-card-footer">
                  <span className={`status-badge ${isConnected ? 'active' : 'draft'}`}>
                    {isConnected ? 'CONNECTED' : 'AVAILABLE'}
                  </span>
                  <button
                    className={isConnected ? 'btn-secondary' : 'btn-primary'}
                    onClick={() => handleToggleConnector(prov.id, connector?.connection_status, connector?.id)}
                  >
                    {isConnected ? 'Disconnect' : 'Connect'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB: MARKETPLACE */}
      {activeTab === 'marketplace' && (
        <div className="cards-grid">
          {marketplaceListings.map((listing) => {
            const isInstalled = installations.some((inst) => inst.listing_id === listing.id);

            return (
              <div key={listing.id} className="app-card">
                <div>
                  <div className="app-card-header">
                    <div className="app-icon-wrap">{listing.title[0]}</div>
                    <div className="app-title-group">
                      <h3>
                        {listing.title}
                        {listing.is_official && (
                          <ShieldCheck size={16} color="#2563eb" title="Official Verified App" />
                        )}
                      </h3>
                      <span className="app-category-badge">{listing.category}</span>
                    </div>
                  </div>
                  <p className="app-card-desc">{listing.description}</p>
                  <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 12 }}>
                    Developed by <strong>{listing.developer_name}</strong> • Rating: {listing.rating} ★
                  </div>
                </div>

                <div className="app-card-footer">
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>v{listing.version}</span>
                  {isInstalled ? (
                    <span className="status-badge active">
                      <Check size={13} /> Installed
                    </span>
                  ) : (
                    <button className="btn-primary" onClick={() => setSelectedListing(listing)}>
                      <Download size={14} /> Install App
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TAB: INSTALLED APPS */}
      {activeTab === 'installed' && (
        <div className="automation-card">
          {installations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 30 }}>
              <p style={{ color: '#64748b' }}>No apps installed yet from the marketplace.</p>
            </div>
          ) : (
            <table className="workflows-table">
              <thead>
                <tr>
                  <th>Installed App</th>
                  <th>Status</th>
                  <th>Granted Scopes</th>
                  <th>Installed At</th>
                </tr>
              </thead>
              <tbody>
                {installations.map((inst) => (
                  <tr key={inst.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{inst.listing_title || inst.listing_id}</div>
                      <code style={{ fontSize: '0.78rem', color: '#64748b' }}>{inst.id}</code>
                    </td>
                    <td>
                      <span className="status-badge active">{inst.status}</span>
                    </td>
                    <td>
                      <code style={{ fontSize: '0.8rem' }}>{inst.granted_scopes_json}</code>
                    </td>
                    <td style={{ fontSize: '0.82rem', color: '#64748b' }}>
                      {new Date(inst.installed_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* TAB: WEBHOOK SIMULATOR */}
      {activeTab === 'webhook_simulator' && (
        <div className="sandbox-card">
          <h3 style={{ marginBottom: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Terminal size={20} color="#2563eb" />
            Outbound Webhook Delivery & HMAC-SHA256 Signature Sandbox
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#64748b', marginBottom: 20 }}>
            Simulate and verify outbound webhook event delivery. FocusBoard cryptographically signs payloads with HMAC-SHA256 using standard <code>t=&lt;timestamp&gt;,v1=&lt;signature&gt;</code> headers to safeguard recipient integrity.
          </p>

          <form onSubmit={handleTestWebhook}>
            <div className="form-group">
              <label>Target Webhook Receiver URL</label>
              <input
                type="url"
                required
                className="form-input"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Secret Signing Key</label>
              <input
                type="text"
                required
                className="form-input"
                value={webhookSecret}
                onChange={(e) => setWebhookSecret(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Event Type</label>
              <select
                className="form-select"
                value={webhookEvent}
                onChange={(e) => setWebhookEvent(e.target.value)}
              >
                <option value="task.created">task.created</option>
                <option value="task.completed">task.completed</option>
                <option value="workflow.execution.completed">workflow.execution.completed</option>
                <option value="approval.requested">approval.requested</option>
              </select>
            </div>

            <button type="submit" className="btn-primary" disabled={simulating}>
              <Send size={15} />
              {simulating ? 'Signing & Dispatching...' : 'Dispatch Test Webhook'}
            </button>
          </form>

          {webhookResult && (
            <div className="hmac-result-box">
              <div style={{ color: '#4ade80', marginBottom: 8, fontWeight: 600 }}>
                ✓ Webhook Dispatched (Status: {webhookResult.status_code} in {webhookResult.duration_ms}ms)
              </div>
              <div><strong>Signature Header:</strong> {webhookResult.signature_header}</div>
              <div><strong>Event ID:</strong> {webhookResult.event_id}</div>
              <div><strong>Response Body:</strong> {webhookResult.response_body}</div>
            </div>
          )}
        </div>
      )}

      {/* TAB: PLATFORM ANALYTICS */}
      {activeTab === 'analytics' && (
        <div>
          <div className="automation-card">
            <h3>API Platform Top Endpoints</h3>
            <table className="workflows-table" style={{ marginTop: 12 }}>
              <thead>
                <tr>
                  <th>Endpoint</th>
                  <th>Calls (24h)</th>
                  <th>Avg Latency</th>
                </tr>
              </thead>
              <tbody>
                {(analytics?.top_endpoints || []).map((ep, i) => (
                  <tr key={i}>
                    <td><code>{ep.endpoint}</code></td>
                    <td>{ep.calls}</td>
                    <td>{ep.avg_ms} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Consent & Install Modal */}
      {selectedListing && (
        <div className="modal-overlay" onClick={() => setSelectedListing(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Install {selectedListing.title}</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setSelectedListing(null)}>
                ✕
              </button>
            </div>
            <div>
              <p style={{ fontSize: '0.9rem', color: '#475569', marginBottom: 16 }}>
                {selectedListing.description}
              </p>

              <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 8, padding: 16, marginBottom: 16 }}>
                <h4 style={{ margin: '0 0 10px', fontSize: '0.92rem', color: '#0f172a' }}>
                  Requested Scopes & Permissions:
                </h4>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: '0.85rem', color: '#334155' }}>
                  {(selectedListing.permissions_list || ['tasks:read']).map((scope, idx) => (
                    <li key={idx} style={{ marginBottom: 4 }}>
                      <code>{scope}</code>
                    </li>
                  ))}
                </ul>
              </div>

              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.88rem', cursor: 'pointer', marginBottom: 20 }}>
                <input
                  type="checkbox"
                  checked={consentGranted}
                  onChange={(e) => setConsentGranted(e.target.checked)}
                />
                I grant this application the requested workspace permissions.
              </label>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button className="btn-secondary" onClick={() => setSelectedListing(null)}>
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={handleInstallApp}
                  disabled={!consentGranted || installing}
                >
                  <ShieldCheck size={16} />
                  {installing ? 'Installing...' : 'Confirm & Install'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
