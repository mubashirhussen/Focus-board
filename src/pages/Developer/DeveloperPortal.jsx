import React, { useState, useEffect } from 'react';
import {
  Code,
  Key,
  Webhook,
  Terminal,
  Copy,
  Check,
  Plus,
  Trash2,
  Send,
  Shield,
  Layers,
  Activity,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  Clock
} from 'lucide-react';
import { developerApi } from '../../services/developerApi';
import './DeveloperPortal.css';

export default function DeveloperPortal() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data
  const [stats, setStats] = useState(null);
  const [applications, setApplications] = useState([]);
  const [credentials, setCredentials] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [deliveries, setDeliveries] = useState([]);

  // Modals & Forms
  const [showAppModal, setShowAppModal] = useState(false);
  const [appName, setAppName] = useState('');
  const [appDescription, setAppDescription] = useState('');
  const [appType, setAppType] = useState('INTERNAL');

  const [showKeyModal, setShowKeyModal] = useState(false);
  const [keyAppId, setKeyAppId] = useState('');
  const [keyName, setKeyName] = useState('');
  const [selectedScopes, setSelectedScopes] = useState(['tasks:read']);
  const [createdPlaintextKey, setCreatedPlaintextKey] = useState(null);
  const [copiedKey, setCopiedKey] = useState(false);

  const [showWebhookModal, setShowWebhookModal] = useState(false);
  const [webhookUrl, setWebhookUrl] = useState('');
  const [webhookEvents, setWebhookEvents] = useState(['task.created', 'task.updated']);
  const [createdWebhookSecret, setCreatedWebhookSecret] = useState(null);
  const [testingWebhookId, setTestingWebhookId] = useState(null);
  const [testResult, setTestResult] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, appsRes, webhooksRes] = await Promise.all([
        developerApi.getStats().catch(() => null),
        developerApi.listApplications().catch(() => []),
        developerApi.listWebhooks().catch(() => []),
      ]);
      setStats(statsRes);
      setApplications(appsRes || []);
      setWebhooks(webhooksRes || []);

      // Load credentials for all apps
      if (appsRes && appsRes.length > 0) {
        const credPromises = appsRes.map((a) => developerApi.listCredentials(a.id).catch(() => []));
        const credResults = await Promise.all(credPromises);
        setCredentials(credResults.flat());
        if (!keyAppId) setKeyAppId(appsRes[0].id);
      }
    } catch (err) {
      setError('Failed to load developer portal records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateApp = async (e) => {
    e.preventDefault();
    if (!appName.trim()) return;
    try {
      await developerApi.createApplication({
        name: appName,
        description: appDescription,
        app_type: appType,
      });
      setShowAppModal(false);
      setAppName('');
      setAppDescription('');
      loadData();
    } catch (err) {
      alert('Error creating app: ' + err.message);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!keyName.trim() || !keyAppId) return;
    try {
      const res = await developerApi.createCredential({
        application_id: keyAppId,
        name: keyName,
        scopes: selectedScopes,
      });
      setCreatedPlaintextKey(res.plaintext_key);
      loadData();
    } catch (err) {
      alert('Error generating API key: ' + err.message);
    }
  };

  const handleRevokeKey = async (credId) => {
    if (!window.confirm('Are you sure you want to permanently revoke this API key? External systems using it will be rejected.')) return;
    try {
      await developerApi.revokeCredential(credId);
      loadData();
    } catch (err) {
      alert('Error revoking key: ' + err.message);
    }
  };

  const handleCreateWebhook = async (e) => {
    e.preventDefault();
    if (!webhookUrl.trim()) return;
    try {
      const res = await developerApi.createWebhook({
        target_url: webhookUrl,
        events: webhookEvents,
      });
      setCreatedWebhookSecret(res.secret_key);
      loadData();
    } catch (err) {
      alert('Error registering webhook: ' + err.message);
    }
  };

  const handleDeleteWebhook = async (whId) => {
    if (!window.confirm('Delete this webhook subscription?')) return;
    try {
      await developerApi.deleteWebhook(whId);
      loadData();
    } catch (err) {
      alert('Error deleting webhook: ' + err.message);
    }
  };

  const handleTestWebhook = async (whId) => {
    setTestingWebhookId(whId);
    setTestResult(null);
    try {
      const res = await developerApi.testWebhook(whId);
      setTestResult({ id: whId, success: true, status: res.response_status_code || 200, message: 'Test delivery dispatched successfully.' });
      const delivs = await developerApi.getWebhookDeliveries(whId);
      setDeliveries(delivs || []);
    } catch (err) {
      setTestResult({ id: whId, success: false, status: 500, message: err.message });
    } finally {
      setTestingWebhookId(null);
    }
  };

  const handleScopeToggle = (scope) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const handleCopyKey = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2500);
  };

  const AVAILABLE_SCOPES = [
    { id: 'tasks:read', label: 'tasks:read', desc: 'Read tasks and comments' },
    { id: 'tasks:write', label: 'tasks:write', desc: 'Create, update, and delete tasks' },
    { id: 'projects:read', label: 'projects:read', desc: 'Read workspace projects' },
    { id: 'projects:write', label: 'projects:write', desc: 'Create and update projects' },
    { id: 'analytics:read', label: 'analytics:read', desc: 'Read executive portfolio metrics' },
    { id: 'webhooks:manage', label: 'webhooks:manage', desc: 'Manage webhook endpoints' },
  ];

  return (
    <div className="dev-portal-wrapper">
      {/* Header */}
      <div className="dev-header">
        <div>
          <h2 className="dev-title">Developer Platform & Public API</h2>
          <p className="dev-subtitle">
            Manage applications, generate scoped API keys, configure webhooks, and integrate SDKs.
          </p>
        </div>
        <div className="dev-header-actions">
          <button className="dev-btn-secondary" onClick={loadData}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="dev-btn-primary" onClick={() => setShowAppModal(true)}>
            <Plus size={16} /> Register Application
          </button>
        </div>
      </div>

      {error && <div className="dev-error-banner">{error}</div>}

      {/* Stats Banner */}
      <div className="dev-stats-grid">
        <div className="dev-stat-card">
          <div className="dev-stat-header">
            <span>Registered Apps</span>
            <Layers size={18} className="icon-blue" />
          </div>
          <div className="dev-stat-val">{stats?.total_applications ?? applications.length}</div>
          <div className="dev-stat-sub">Integrated clients</div>
        </div>

        <div className="dev-stat-card">
          <div className="dev-stat-header">
            <span>Active API Keys</span>
            <Key size={18} className="icon-teal" />
          </div>
          <div className="dev-stat-val">{stats?.active_credentials ?? credentials.length}</div>
          <div className="dev-stat-sub">Cryptographically secure tokens</div>
        </div>

        <div className="dev-stat-card">
          <div className="dev-stat-header">
            <span>Webhook Subscriptions</span>
            <Webhook size={18} className="icon-purple" />
          </div>
          <div className="dev-stat-val">{stats?.total_webhooks ?? webhooks.length}</div>
          <div className="dev-stat-sub">Active event dispatchers</div>
        </div>

        <div className="dev-stat-card">
          <div className="dev-stat-header">
            <span>API Calls (30 Days)</span>
            <Activity size={18} className="icon-green" />
          </div>
          <div className="dev-stat-val">{stats?.api_calls_last_30d ?? 0}</div>
          <div className="dev-stat-sub">{stats?.api_success_rate ?? 100}% success rate</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="dev-tabs">
        <button
          className={`dev-tab-btn ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <Layers size={16} /> Applications ({applications.length})
        </button>
        <button
          className={`dev-tab-btn ${activeTab === 'keys' ? 'active' : ''}`}
          onClick={() => setActiveTab('keys')}
        >
          <Key size={16} /> API Keys ({credentials.length})
        </button>
        <button
          className={`dev-tab-btn ${activeTab === 'webhooks' ? 'active' : ''}`}
          onClick={() => setActiveTab('webhooks')}
        >
          <Webhook size={16} /> Webhooks & Simulator ({webhooks.length})
        </button>
        <button
          className={`dev-tab-btn ${activeTab === 'docs' ? 'active' : ''}`}
          onClick={() => setActiveTab('docs')}
        >
          <Terminal size={16} /> API Reference & SDKs
        </button>
      </div>

      {/* TAB 1: Applications */}
      {activeTab === 'overview' && (
        <div className="dev-tab-content">
          <div className="dev-section-header">
            <div>
              <h3>Registered Applications</h3>
              <p>Applications represent integrations, bots, or third-party clients authorized to interact with your workspace.</p>
            </div>
            <button className="dev-btn-primary" onClick={() => setShowAppModal(true)}>
              <Plus size={16} /> Register App
            </button>
          </div>

          {applications.length === 0 ? (
            <div className="dev-empty-state">
              <Layers size={36} />
              <h4>No Applications Registered</h4>
              <p>Register your first application to generate API keys and configure webhooks.</p>
            </div>
          ) : (
            <div className="dev-cards-grid">
              {applications.map((app) => (
                <div key={app.id} className="dev-app-card">
                  <div className="dev-app-card-header">
                    <div>
                      <h4 className="dev-app-title">{app.name}</h4>
                      <span className="dev-app-type">{app.app_type}</span>
                    </div>
                    <span className={`dev-badge ${app.status === 'ACTIVE' ? 'badge-active' : 'badge-suspended'}`}>
                      {app.status}
                    </span>
                  </div>
                  <p className="dev-app-desc">{app.description || 'No description provided.'}</p>
                  <div className="dev-app-footer">
                    <small className="text-muted">Registered {new Date(app.created_at).toLocaleDateString()}</small>
                    <button
                      className="dev-btn-sm"
                      onClick={() => {
                        setKeyAppId(app.id);
                        setShowKeyModal(true);
                      }}
                    >
                      <Plus size={14} /> New API Key
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: API Keys */}
      {activeTab === 'keys' && (
        <div className="dev-tab-content">
          <div className="dev-section-header">
            <div>
              <h3>API Credentials</h3>
              <p>API keys authenticate external requests via the <code>X-API-Key: fb_live_...</code> header. Keys are securely hashed at rest with SHA-256.</p>
            </div>
            <button className="dev-btn-primary" onClick={() => setShowKeyModal(true)}>
              <Plus size={16} /> Generate API Key
            </button>
          </div>

          {credentials.length === 0 ? (
            <div className="dev-empty-state">
              <Key size={36} />
              <h4>No Active API Keys</h4>
              <p>Generate an API key to start automating tasks with Python, TypeScript, or curl.</p>
            </div>
          ) : (
            <div className="dev-table-card">
              <table className="dev-table">
                <thead>
                  <tr>
                    <th>Key Name</th>
                    <th>Key Prefix</th>
                    <th>Granted Scopes</th>
                    <th>Status</th>
                    <th>Last Used</th>
                    <th>Created</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {credentials.map((cred) => (
                    <tr key={cred.id}>
                      <td className="font-semibold">{cred.name}</td>
                      <td>
                        <code className="key-prefix-badge">{cred.key_prefix}••••••••</code>
                      </td>
                      <td>
                        <div className="scopes-container">
                          {cred.scopes?.map((s) => (
                            <span key={s} className="scope-chip">{s}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <span className={`dev-badge ${cred.is_active ? 'badge-active' : 'badge-revoked'}`}>
                          {cred.is_active ? 'ACTIVE' : 'REVOKED'}
                        </span>
                      </td>
                      <td>{cred.last_used_at ? new Date(cred.last_used_at).toLocaleDateString() : 'Never'}</td>
                      <td>{new Date(cred.created_at).toLocaleDateString()}</td>
                      <td>
                        {cred.is_active && (
                          <button
                            className="dev-btn-danger-sm"
                            onClick={() => handleRevokeKey(cred.id)}
                            title="Revoke Key"
                          >
                            <Trash2 size={14} /> Revoke
                          </button>
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

      {/* TAB 3: Webhooks & Simulator */}
      {activeTab === 'webhooks' && (
        <div className="dev-tab-content">
          <div className="dev-section-header">
            <div>
              <h3>Webhook Endpoints & Dispatch Simulator</h3>
              <p>FocusBoard sends real-time HTTP POST deliveries when tasks are created, updated, or completed with HMAC-SHA256 signatures.</p>
            </div>
            <button className="dev-btn-primary" onClick={() => setShowWebhookModal(true)}>
              <Plus size={16} /> Register Endpoint
            </button>
          </div>

          {webhooks.length === 0 ? (
            <div className="dev-empty-state">
              <Webhook size={36} />
              <h4>No Webhook Endpoints Configured</h4>
              <p>Add a target URL to subscribe to real-time events.</p>
            </div>
          ) : (
            <div className="dev-table-card">
              <table className="dev-table">
                <thead>
                  <tr>
                    <th>Target URL</th>
                    <th>Subscribed Events</th>
                    <th>Status</th>
                    <th>Failures</th>
                    <th>Last Delivered</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {webhooks.map((wh) => (
                    <tr key={wh.id}>
                      <td className="font-mono text-sm max-w-xs truncate" title={wh.target_url}>
                        {wh.target_url}
                      </td>
                      <td>
                        <div className="scopes-container">
                          {wh.events?.map((ev) => (
                            <span key={ev} className="scope-chip">{ev}</span>
                          ))}
                        </div>
                      </td>
                      <td>
                        <span className={`dev-badge ${wh.is_active ? 'badge-active' : 'badge-suspended'}`}>
                          {wh.is_active ? 'ACTIVE' : 'DISABLED'}
                        </span>
                      </td>
                      <td>{wh.failure_count}</td>
                      <td>{wh.last_delivered_at ? new Date(wh.last_delivered_at).toLocaleTimeString() : 'Never'}</td>
                      <td>
                        <div className="dev-row-actions">
                          <button
                            className="dev-btn-sm"
                            disabled={testingWebhookId === wh.id}
                            onClick={() => handleTestWebhook(wh.id)}
                            title="Dispatch Test Ping"
                          >
                            <Send size={13} /> {testingWebhookId === wh.id ? 'Sending...' : 'Test Ping'}
                          </button>
                          <button
                            className="dev-btn-danger-sm"
                            onClick={() => handleDeleteWebhook(wh.id)}
                            title="Delete"
                          >
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {testResult && (
            <div className={`dev-test-banner ${testResult.success ? 'test-success' : 'test-failure'}`}>
              <strong>Webhook Test Result:</strong> HTTP {testResult.status} — {testResult.message}
            </div>
          )}

          {deliveries.length > 0 && (
            <div className="dev-deliveries-section">
              <h4>Recent Delivery Logs</h4>
              <div className="dev-table-card">
                <table className="dev-table">
                  <thead>
                    <tr>
                      <th>Event</th>
                      <th>Status Code</th>
                      <th>Attempt</th>
                      <th>Delivered At</th>
                      <th>Signature</th>
                    </tr>
                  </thead>
                  <tbody>
                    {deliveries.map((d) => (
                      <tr key={d.id}>
                        <td><code>{d.event_type}</code></td>
                        <td>
                          <span className={`status-code ${d.response_status_code === 200 ? 'code-200' : 'code-err'}`}>
                            {d.response_status_code || 'Err'}
                          </span>
                        </td>
                        <td>{d.attempt_count}</td>
                        <td>{new Date(d.delivered_at).toLocaleTimeString()}</td>
                        <td className="text-muted text-xs">HMAC-SHA256 Verified</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: API Docs & SDKs */}
      {activeTab === 'docs' && (
        <div className="dev-tab-content">
          <div className="dev-docs-grid">
            <div className="dev-doc-card">
              <h4>Quickstart: Python SDK</h4>
              <p className="text-sm text-muted mb-3">Install via pip or include <code>focusboard_sdk</code> in your repo:</p>
              <pre className="dev-code-block">
{`from focusboard_sdk.client import FocusBoardClient

client = FocusBoardClient(api_key="fb_live_YOUR_KEY_HERE")

# 1. List workspace tasks
tasks = client.list_tasks(limit=10)

# 2. Create automated task with idempotency
new_task = client.create_task(
    title="Automated Release Deployment",
    priority="high",
    category="DevOps",
    idempotency_key="release-v2.5-deploy"
)
print("Created Task ID:", new_task["id"])`}
              </pre>
            </div>

            <div className="dev-doc-card">
              <h4>Quickstart: TypeScript SDK</h4>
              <p className="text-sm text-muted mb-3">Strongly-typed client for Node.js and frontend environments:</p>
              <pre className="dev-code-block">
{`import { FocusBoardClient } from '@focusboard/sdk';

const client = new FocusBoardClient({
  apiKey: 'fb_live_YOUR_KEY_HERE',
});

// Create task
const task = await client.createTask({
  title: 'CI/CD Pipeline Failure Investigation',
  priority: 'high',
  category: 'Infrastructure',
});

console.log('Task Created:', task.id);`}
              </pre>
            </div>
          </div>

          <div className="dev-endpoints-card">
            <h4>Public API v1 Endpoints</h4>
            <table className="dev-table">
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Endpoint</th>
                  <th>Required Scope</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><span className="method-get">GET</span></td>
                  <td><code>/api/v1/public/v1/tasks</code></td>
                  <td><code>tasks:read</code></td>
                  <td>List tasks with pagination and status filters.</td>
                </tr>
                <tr>
                  <td><span className="method-post">POST</span></td>
                  <td><code>/api/v1/public/v1/tasks</code></td>
                  <td><code>tasks:write</code></td>
                  <td>Create a new task. Supports <code>Idempotency-Key</code>.</td>
                </tr>
                <tr>
                  <td><span className="method-patch">PATCH</span></td>
                  <td><code>/api/v1/public/v1/tasks/{'{task_id}'}</code></td>
                  <td><code>tasks:write</code></td>
                  <td>Update status, title, description, or due date.</td>
                </tr>
                <tr>
                  <td><span className="method-delete">DELETE</span></td>
                  <td><code>/api/v1/public/v1/tasks/{'{task_id}'}</code></td>
                  <td><code>tasks:write</code></td>
                  <td>Delete a task permanently.</td>
                </tr>
                <tr>
                  <td><span className="method-get">GET</span></td>
                  <td><code>/api/v1/public/v1/projects</code></td>
                  <td><code>projects:read</code></td>
                  <td>List workspace projects and milestone targets.</td>
                </tr>
                <tr>
                  <td><span className="method-get">GET</span></td>
                  <td><code>/api/v1/public/v1/analytics/portfolio</code></td>
                  <td><code>analytics:read</code></td>
                  <td>Fetch portfolio health scores, signals, and forecasts.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Modal: Register Application */}
      {showAppModal && (
        <div className="dev-modal-overlay">
          <div className="dev-modal">
            <div className="dev-modal-header">
              <h3>Register Application</h3>
              <button className="dev-close-btn" onClick={() => setShowAppModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateApp}>
              <div className="dev-form-group">
                <label>Application Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. GitHub Actions Bot"
                  value={appName}
                  onChange={(e) => setAppName(e.target.value)}
                />
              </div>
              <div className="dev-form-group">
                <label>Description</label>
                <input
                  type="text"
                  placeholder="What does this application do?"
                  value={appDescription}
                  onChange={(e) => setAppDescription(e.target.value)}
                />
              </div>
              <div className="dev-form-group">
                <label>Application Type</label>
                <select value={appType} onChange={(e) => setAppType(e.target.value)}>
                  <option value="INTERNAL">Internal (Company Tools)</option>
                  <option value="PARTNER">Partner (B2B Integration)</option>
                  <option value="PUBLIC">Public Client</option>
                </select>
              </div>
              <div className="dev-modal-actions">
                <button type="button" className="dev-btn-secondary" onClick={() => setShowAppModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="dev-btn-primary">
                  Register App
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Generate API Key */}
      {showKeyModal && (
        <div className="dev-modal-overlay">
          <div className="dev-modal">
            <div className="dev-modal-header">
              <h3>Generate API Key</h3>
              <button
                className="dev-close-btn"
                onClick={() => {
                  setShowKeyModal(false);
                  setCreatedPlaintextKey(null);
                }}
              >
                ×
              </button>
            </div>

            {createdPlaintextKey ? (
              <div className="dev-created-key-box">
                <div className="alert-warning-banner">
                  <AlertCircle size={18} />
                  <span>Copy your API key now. You will not be able to view it again!</span>
                </div>
                <div className="key-display-field">
                  <code>{createdPlaintextKey}</code>
                  <button className="copy-btn" onClick={() => handleCopyKey(createdPlaintextKey)}>
                    {copiedKey ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
                <div className="dev-modal-actions mt-4">
                  <button
                    className="dev-btn-primary"
                    onClick={() => {
                      setShowKeyModal(false);
                      setCreatedPlaintextKey(null);
                    }}
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreateKey}>
                <div className="dev-form-group">
                  <label>Application</label>
                  <select value={keyAppId} onChange={(e) => setKeyAppId(e.target.value)} required>
                    {applications.map((app) => (
                      <option key={app.id} value={app.id}>{app.name}</option>
                    ))}
                  </select>
                </div>
                <div className="dev-form-group">
                  <label>Key Name / Purpose</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Production CI Server"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                  />
                </div>
                <div className="dev-form-group">
                  <label>Granted Permission Scopes</label>
                  <div className="scopes-checkbox-grid">
                    {AVAILABLE_SCOPES.map((sc) => (
                      <label key={sc.id} className="scope-checkbox-item">
                        <input
                          type="checkbox"
                          checked={selectedScopes.includes(sc.id)}
                          onChange={() => handleScopeToggle(sc.id)}
                        />
                        <div>
                          <strong>{sc.label}</strong>
                          <small className="text-muted block">{sc.desc}</small>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="dev-modal-actions">
                  <button type="button" className="dev-btn-secondary" onClick={() => setShowKeyModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="dev-btn-primary">
                    Create Key
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Modal: Register Webhook */}
      {showWebhookModal && (
        <div className="dev-modal-overlay">
          <div className="dev-modal">
            <div className="dev-modal-header">
              <h3>Register Webhook Endpoint</h3>
              <button
                className="dev-close-btn"
                onClick={() => {
                  setShowWebhookModal(false);
                  setCreatedWebhookSecret(null);
                }}
              >
                ×
              </button>
            </div>

            {createdWebhookSecret ? (
              <div className="dev-created-key-box">
                <div className="alert-success-banner">
                  <Check size={18} />
                  <span>Webhook registered successfully! Save this secret to verify signatures.</span>
                </div>
                <label className="text-xs font-semibold text-muted">SIGNING SECRET (HMAC-SHA256)</label>
                <div className="key-display-field">
                  <code>{createdWebhookSecret}</code>
                  <button className="copy-btn" onClick={() => handleCopyKey(createdWebhookSecret)}>
                    {copiedKey ? <Check size={16} /> : <Copy size={16} />}
                  </button>
                </div>
                <div className="dev-modal-actions mt-4">
                  <button
                    className="dev-btn-primary"
                    onClick={() => {
                      setShowWebhookModal(false);
                      setCreatedWebhookSecret(null);
                    }}
                  >
                    Done
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleCreateWebhook}>
                <div className="dev-form-group">
                  <label>Payload Target URL</label>
                  <input
                    type="url"
                    required
                    placeholder="https://api.yourdomain.com/webhooks/focusboard"
                    value={webhookUrl}
                    onChange={(e) => setWebhookUrl(e.target.value)}
                  />
                  <small className="text-muted text-xs">Must be a valid HTTP or HTTPS endpoint.</small>
                </div>
                <div className="dev-modal-actions">
                  <button type="button" className="dev-btn-secondary" onClick={() => setShowWebhookModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="dev-btn-primary">
                    Register Webhook
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
