import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Shield,
  Key,
  Globe,
  Users,
  Download,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Plus,
  Copy,
  Check,
  RefreshCw,
  FileSpreadsheet,
} from 'lucide-react';
import { enterpriseApi } from '../../services/enterpriseApi';
import { useAuth } from '../../context/AuthContext';
import './Enterprise.css';

const AVAILABLE_PERMISSIONS = [
  { id: 'organization.read', label: 'View Organization details' },
  { id: 'organization.update', label: 'Update Organization settings' },
  { id: 'organization.policies', label: 'Manage Organization policies' },
  { id: 'workspace.create', label: 'Create new Workspaces' },
  { id: 'workspace.read', label: 'View Workspaces & members' },
  { id: 'workspace.update', label: 'Update Workspace configurations' },
  { id: 'workspace.delete', label: 'Delete Workspaces' },
  { id: 'project.create', label: 'Create Projects' },
  { id: 'project.read', label: 'View Projects' },
  { id: 'project.update', label: 'Edit Projects' },
  { id: 'project.delete', label: 'Delete Projects' },
  { id: 'task.create', label: 'Create Tasks' },
  { id: 'task.read', label: 'View Tasks' },
  { id: 'task.update', label: 'Update Tasks' },
  { id: 'task.delete', label: 'Delete Tasks' },
  { id: 'billing.read', label: 'View Billing & Invoices' },
  { id: 'billing.manage', label: 'Manage Plans & Subscriptions' },
  { id: 'integration.manage', label: 'Manage Webhooks & Integrations' },
  { id: 'audit.read', label: 'View Audit Logs' },
  { id: 'audit.export', label: 'Export Audit Logs (CSV)' },
];

export function Enterprise() {
  const { isAuthenticated, user, openAuthModal } = useAuth();
  const isUserLoggedIn = Boolean(isAuthenticated && user && !user.isGuest);

  const [activeTab, setActiveTab] = useState('governance'); // 'governance' | 'roles' | 'domains' | 'mfa' | 'audit'
  const [policies, setPolicies] = useState({});
  const [policyLoading, setPolicyLoading] = useState({});
  const [policyError, setPolicyError] = useState(null);
  const [roles, setRoles] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionNotice, setActionNotice] = useState(null);

  // Custom Role Creator Form
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleDesc, setNewRoleDesc] = useState('');
  const [selectedPermissions, setSelectedPermissions] = useState([]);

  // Domain Form
  const [newDomainName, setNewDomainName] = useState('');

  // MFA Flow
  const [mfaData, setMfaData] = useState(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaEnabled, setMfaEnabled] = useState(false);
  const [copiedToken, setCopiedToken] = useState(null);
  const [isExportingAudit, setIsExportingAudit] = useState(false);

  useEffect(() => {
    loadEnterpriseData();
  }, [isAuthenticated]);

  const loadEnterpriseData = async () => {
    setLoading(true);
    setPolicyError(null);
    try {
      if (isAuthenticated) {
        const [polRes, rolesRes, domRes] = await Promise.allSettled([
          enterpriseApi.getPolicies(),
          enterpriseApi.getRoles(),
          enterpriseApi.getDomains(),
        ]);

        if (polRes.status === 'fulfilled' && polRes.value) {
          const map = {};
          if (Array.isArray(polRes.value)) {
            polRes.value.forEach((p) => {
              const pType = p.policy_type || p.key;
              map[pType] = {
                policy_type: pType,
                is_enabled: Boolean(p.is_enabled ?? p.enabled),
                ...p,
              };
            });
          } else if (typeof polRes.value === 'object') {
            Object.entries(polRes.value).forEach(([k, v]) => {
              const isEn = typeof v === 'boolean' ? v : Boolean(v?.is_enabled ?? v?.enabled);
              map[k] = {
                policy_type: k,
                is_enabled: isEn,
                ...(typeof v === 'object' ? v : {}),
              };
            });
          }
          // Ensure aliases match
          if (map['mfa_required'] && !map['mfa_enforced']) {
            map['mfa_enforced'] = { ...map['mfa_required'], policy_type: 'mfa_enforced' };
          }
          if (map['mfa_enforced'] && !map['mfa_required']) {
            map['mfa_required'] = { ...map['mfa_enforced'], policy_type: 'mfa_required' };
          }
          setPolicies(map);
          try {
            localStorage.setItem('focusboard_enterprise_policies', JSON.stringify(map));
          } catch {}
        }
        if (rolesRes.status === 'fulfilled') setRoles(rolesRes.value || []);
        if (domRes.status === 'fulfilled') setDomains(domRes.value || []);
      } else {
        // Load cached or default policies for guest / offline mode
        let cached = null;
        try {
          cached = JSON.parse(localStorage.getItem('focusboard_enterprise_policies') || 'null');
        } catch {}

        setPolicies(cached || {
          mfa_enforced: { policy_type: 'mfa_enforced', is_enabled: true },
          mfa_required: { policy_type: 'mfa_required', is_enabled: true },
          domain_restriction: { policy_type: 'domain_restriction', is_enabled: false },
          ai_governance: { policy_type: 'ai_governance', is_enabled: true },
        });
        setRoles([
          { id: 'r-1', name: 'ComplianceOfficer', description: 'Audits access and exports compliance trails', permissions: ['audit.read', 'audit.export', 'organization.read'] },
          { id: 'r-2', name: 'ProjectManager', description: 'Manages workspaces, projects, and task assignments', permissions: ['project.create', 'project.read', 'project.update', 'task.create', 'task.update'] },
        ]);
        setDomains([
          { id: 'd-1', domain_name: 'acme-corp.com', is_verified: true, verification_token: 'fb-token-verified-example' },
        ]);
      }
    } catch (err) {
      console.warn('Failed to load enterprise data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePolicy = async (policyType) => {
    if (policyLoading[policyType]) return;

    const current = Boolean(policies[policyType]?.is_enabled);
    const nextVal = !current;

    // Optimistic UI update
    const updatedMap = {
      ...policies,
      [policyType]: { ...policies[policyType], policy_type: policyType, is_enabled: nextVal },
    };
    if (policyType === 'mfa_enforced') {
      updatedMap['mfa_required'] = { ...updatedMap['mfa_required'], is_enabled: nextVal };
    }
    setPolicies(updatedMap);
    setPolicyError(null);
    setPolicyLoading((prev) => ({ ...prev, [policyType]: true }));

    try {
      if (isAuthenticated) {
        await enterpriseApi.updatePolicy(policyType, nextVal);
      }
      try {
        localStorage.setItem('focusboard_enterprise_policies', JSON.stringify(updatedMap));
      } catch {}
    } catch (err) {
      // Revert optimistic update
      const revertedMap = {
        ...policies,
        [policyType]: { ...policies[policyType], is_enabled: current },
      };
      if (policyType === 'mfa_enforced') {
        revertedMap['mfa_required'] = { ...revertedMap['mfa_required'], is_enabled: current };
      }
      setPolicies(revertedMap);
      setPolicyError({
        policyType,
        message: err.message || 'Network error updating policy. Please check backend connection.',
      });
    } finally {
      setPolicyLoading((prev) => ({ ...prev, [policyType]: false }));
    }
  };

  const handleCreateRole = async (e) => {
    e.preventDefault();
    if (!newRoleName.trim() || selectedPermissions.length === 0) {
      alert('Please provide a role name and select at least one permission.');
      return;
    }

    try {
      if (isAuthenticated) {
        const created = await enterpriseApi.createRole({
          name: newRoleName.trim(),
          description: newRoleDesc.trim(),
          permissions: selectedPermissions,
        });
        setRoles((prev) => [...prev, created]);
      } else {
        setRoles((prev) => [
          ...prev,
          {
            id: `role-local-${Date.now()}`,
            name: newRoleName.trim(),
            description: newRoleDesc.trim(),
            permissions: selectedPermissions,
          },
        ]);
      }
      setNewRoleName('');
      setNewRoleDesc('');
      setSelectedPermissions([]);
      setActionNotice('Custom RBAC role created successfully.');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      alert('Failed to create role: ' + err.message);
    }
  };

  const togglePermission = (permId) => {
    setSelectedPermissions((prev) =>
      prev.includes(permId) ? prev.filter((p) => p !== permId) : [...prev, permId]
    );
  };

  const handleAddDomain = async (e) => {
    e.preventDefault();
    if (!newDomainName.trim()) return;

    try {
      if (isAuthenticated) {
        const created = await enterpriseApi.addDomain(newDomainName.trim());
        setDomains((prev) => [...prev, created]);
      } else {
        setDomains((prev) => [
          ...prev,
          {
            id: `dom-${Date.now()}`,
            domain_name: newDomainName.trim(),
            is_verified: false,
            verification_token: `fb-token-demo-${Math.random().toString(36).substring(2, 10)}`,
          },
        ]);
      }
      setNewDomainName('');
      setActionNotice('Domain registered. Please verify DNS token.');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      alert('Failed to add domain: ' + err.message);
    }
  };

  const handleVerifyDomain = async (id) => {
    try {
      if (isAuthenticated && !String(id).startsWith('dom-')) {
        const verified = await enterpriseApi.verifyDomain(id);
        setDomains((prev) => prev.map((d) => (d.id === id ? verified : d)));
      } else {
        setDomains((prev) =>
          prev.map((d) => (d.id === id ? { ...d, is_verified: true } : d))
        );
      }
      setActionNotice('Domain verified successfully!');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      alert('Domain verification failed: ' + err.message);
    }
  };

  const handleStartMFASetup = async () => {
    try {
      if (isAuthenticated) {
        const data = await enterpriseApi.setupMFA();
        setMfaData(data);
      } else {
        setMfaData({
          secret_key: 'JBSWY3DPEHPK3PXP',
          otpauth_url: 'otpauth://totp/FocusBoard:demo_user?secret=JBSWY3DPEHPK3PXP&issuer=FocusBoard',
          recovery_codes: ['a1b2-c3d4', 'e5f6-g7h8', 'i9j0-k1l2', 'm3n4-o5p6'],
        });
      }
    } catch (err) {
      alert('Failed to initiate MFA setup: ' + err.message);
    }
  };

  const handleVerifyMFACode = async (e) => {
    e.preventDefault();
    if (!mfaCode.trim()) return;

    try {
      if (isAuthenticated) {
        await enterpriseApi.verifyMFA(mfaCode.trim());
      }
      setMfaEnabled(true);
      setMfaData(null);
      setMfaCode('');
      setActionNotice('Two-Factor Authentication is now enabled for your account!');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      alert('Invalid code or verification error: ' + err.message);
    }
  };

  const handleExportAuditLogs = async () => {
    setIsExportingAudit(true);
    try {
      if (isAuthenticated) {
        const blob = await enterpriseApi.exportAuditLogs();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `focusboard_compliance_audit_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        // Fallback demo CSV
        const dummyCSV = 'id,created_at,user_id,action,resource_type,ip_address\n1,2026-11-22T08:00:00Z,u-1,auth.login,auth,127.0.0.1\n2,2026-11-22T08:05:00Z,u-1,policy.update,enterprise,127.0.0.1';
        const blob = new Blob([dummyCSV], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'focusboard_compliance_audit_demo.csv';
        a.click();
        URL.revokeObjectURL(url);
      }
      setActionNotice('Audit log CSV exported. This export action was recorded in the audit trail.');
      setTimeout(() => setActionNotice(null), 4000);
    } catch (err) {
      alert('Failed to export audit logs: ' + err.message);
    } finally {
      setIsExportingAudit(false);
    }
  };

  const handleCopy = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopiedToken(key);
    setTimeout(() => setCopiedToken(null), 2000);
  };

  return (
    <div className="enterprise-page">
      {/* Hero Header */}
      <div className="enterprise-header">
        <h1 className="enterprise-title">Security Policies, Custom RBAC & Compliance</h1>
        <p className="enterprise-subtitle">
          Manage organizational security guardrails, fine-grained access control, verified corporate domains, and immutable compliance audit logs.
        </p>
      </div>

      {actionNotice && <div className="enterprise-alert">{actionNotice}</div>}

      {/* Nav Tabs */}
      <div className="enterprise-nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'governance' ? 'active' : ''}`}
          onClick={() => setActiveTab('governance')}
        >
          <Shield size={16} />
          <span>Security Policies</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'roles' ? 'active' : ''}`}
          onClick={() => setActiveTab('roles')}
        >
          <Users size={16} />
          <span>Custom RBAC Roles ({roles.length})</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'domains' ? 'active' : ''}`}
          onClick={() => setActiveTab('domains')}
        >
          <Globe size={16} />
          <span>Verified Domains ({domains.length})</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'mfa' ? 'active' : ''}`}
          onClick={() => setActiveTab('mfa')}
        >
          <Lock size={16} />
          <span>Two-Factor Authentication</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <FileSpreadsheet size={16} />
          <span>Compliance Audit Trail</span>
        </button>
      </div>

      {/* Notification Banners */}
      {actionNotice && (
        <div className="enterprise-notice success" role="status">
          <CheckCircle2 size={16} />
          <span>{actionNotice}</span>
        </div>
      )}

      {policyError && (
        <div className="enterprise-notice error" role="alert">
          <AlertTriangle size={16} />
          <div className="notice-content">
            <strong>Update Error:</strong> {policyError.message}
          </div>
          <button
            type="button"
            className="notice-retry-btn"
            onClick={() => handleTogglePolicy(policyError.policyType)}
          >
            Retry
          </button>
          <button
            type="button"
            className="notice-dismiss-btn"
            onClick={() => setPolicyError(null)}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Tab: Governance Policies */}
      {activeTab === 'governance' && (
        <div className="tab-pane">
          {!isUserLoggedIn ? (
            <div className="enterprise-auth-gate" role="region" aria-label="Authentication Required">
              <div className="auth-gate-card">
                <div className="auth-gate-icon">
                  <Lock size={32} />
                </div>
                <h3 className="auth-gate-title">Enterprise Security Policies</h3>
                <p className="auth-gate-desc">
                  Security guardrails, corporate domain restrictions, and AI privacy controls are restricted to authenticated enterprise administrators.
                </p>
                <button
                  type="button"
                  className="auth-gate-btn"
                  onClick={openAuthModal}
                >
                  Sign In to Access Security Policies
                </button>
              </div>
            </div>
          ) : (
            <div className="policies-grid">
            {/* Policy 1: MFA */}
            <div className="policy-card">
              <div className="policy-card-header">
                <div className="policy-icon mfa">
                  <Lock size={20} />
                </div>
                <div className="policy-info">
                  <h4 className="policy-name">Enforce Multi-Factor Authentication</h4>
                  <p className="policy-desc">
                    Requires all workspace members to authenticate using an RFC 6238 TOTP authenticator before accessing data.
                  </p>
                </div>
              </div>
              <div className="policy-toggle-wrapper">
                <button
                  className={`toggle-switch ${policies['mfa_enforced']?.is_enabled ? 'enabled' : ''} ${policyLoading['mfa_enforced'] ? 'loading' : ''}`}
                  onClick={() => handleTogglePolicy('mfa_enforced')}
                  disabled={policyLoading['mfa_enforced']}
                  aria-label="Toggle Multi-Factor Authentication"
                >
                  <span className="toggle-slider" />
                </button>
                <span className="toggle-state">
                  {policyLoading['mfa_enforced'] ? (
                    <RefreshCw size={13} className="spin-icon" />
                  ) : policies['mfa_enforced']?.is_enabled ? (
                    'Enforced'
                  ) : (
                    'Optional'
                  )}
                </span>
              </div>
            </div>

            {/* Policy 2: Domain Restriction */}
            <div className="policy-card">
              <div className="policy-card-header">
                <div className="policy-icon domain">
                  <Globe size={20} />
                </div>
                <div className="policy-info">
                  <h4 className="policy-name">Corporate Domain Restriction</h4>
                  <p className="policy-desc">
                    Restricts invitations and member registrations to approved, verified corporate email domains only.
                  </p>
                </div>
              </div>
              <div className="policy-toggle-wrapper">
                <button
                  className={`toggle-switch ${policies['domain_restriction']?.is_enabled ? 'enabled' : ''} ${policyLoading['domain_restriction'] ? 'loading' : ''}`}
                  onClick={() => handleTogglePolicy('domain_restriction')}
                  disabled={policyLoading['domain_restriction']}
                  aria-label="Toggle Corporate Domain Restriction"
                >
                  <span className="toggle-slider" />
                </button>
                <span className="toggle-state">
                  {policyLoading['domain_restriction'] ? (
                    <RefreshCw size={13} className="spin-icon" />
                  ) : policies['domain_restriction']?.is_enabled ? (
                    'Restricted'
                  ) : (
                    'Open'
                  )}
                </span>
              </div>
            </div>

            {/* Policy 3: AI Governance */}
            <div className="policy-card">
              <div className="policy-card-header">
                <div className="policy-icon ai">
                  <ShieldCheck size={20} />
                </div>
                <div className="policy-info">
                  <h4 className="policy-name">AI Data Privacy & Zero-Retention</h4>
                  <p className="policy-desc">
                    Ensures prompt payloads and behavioral task telemetry are never retained for model training by third parties.
                  </p>
                </div>
              </div>
              <div className="policy-toggle-wrapper">
                <button
                  className={`toggle-switch ${policies['ai_governance']?.is_enabled ? 'enabled' : ''} ${policyLoading['ai_governance'] ? 'loading' : ''}`}
                  onClick={() => handleTogglePolicy('ai_governance')}
                  disabled={policyLoading['ai_governance']}
                  aria-label="Toggle AI Data Privacy & Zero Retention"
                >
                  <span className="toggle-slider" />
                </button>
                <span className="toggle-state">
                  {policyLoading['ai_governance'] ? (
                    <RefreshCw size={13} className="spin-icon" />
                  ) : policies['ai_governance']?.is_enabled ? (
                    'Protected'
                  ) : (
                    'Standard'
                  )}
                </span>
              </div>
            </div>
          </div>
        )}
        </div>
      )}

      {/* Tab: Custom RBAC Roles */}
      {activeTab === 'roles' && (
        <div className="tab-pane">
          <div className="roles-layout">
            {/* Roles List */}
            <div className="roles-list-section">
              <h3 className="section-title">Configured Custom Roles</h3>
              <div className="roles-cards">
                {roles.length === 0 ? (
                  <div className="empty-state">No custom roles defined yet.</div>
                ) : (
                  roles.map((r) => (
                    <div key={r.id} className="role-card">
                      <div className="role-card-header">
                        <span className="role-name">{r.name}</span>
                        <span className="role-badge">{r.permissions?.length || 0} permissions</span>
                      </div>
                      <p className="role-desc">{r.description || 'No description provided.'}</p>
                      <div className="permissions-chips">
                        {r.permissions?.map((p) => (
                          <span key={p} className="perm-chip">
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Role Creator Form */}
            <div className="role-form-section">
              <form className="role-create-form" onSubmit={handleCreateRole}>
                <h3 className="section-title">
                  <Plus size={18} /> Create Custom Role
                </h3>
                <div className="form-group">
                  <label>Role Identifier Name</label>
                  <input
                    type="text"
                    placeholder="e.g. SecurityAuditor"
                    value={newRoleName}
                    onChange={(e) => setNewRoleName(e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <input
                    type="text"
                    placeholder="Brief description of the role's purpose..."
                    value={newRoleDesc}
                    onChange={(e) => setNewRoleDesc(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Granted Permissions ({selectedPermissions.length} selected)</label>
                  <div className="perm-grid">
                    {AVAILABLE_PERMISSIONS.map((p) => (
                      <label key={p.id} className="perm-checkbox-item">
                        <input
                          type="checkbox"
                          checked={selectedPermissions.includes(p.id)}
                          onChange={() => togglePermission(p.id)}
                        />
                        <span>{p.label} (<code>{p.id}</code>)</span>
                      </label>
                    ))}
                  </div>
                </div>

                <button type="submit" className="primary-btn">
                  Save Custom Role
                </button>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Verified Domains */}
      {activeTab === 'domains' && (
        <div className="tab-pane">
          <div className="domains-container">
            <form className="domain-add-form" onSubmit={handleAddDomain}>
              <div className="domain-input-group">
                <Globe size={18} color="#64748b" />
                <input
                  type="text"
                  placeholder="e.g. acme-enterprise.com"
                  value={newDomainName}
                  onChange={(e) => setNewDomainName(e.target.value)}
                />
                <button type="submit" className="primary-btn">
                  Add Domain
                </button>
              </div>
            </form>

            <div className="domains-list">
              {domains.length === 0 ? (
                <div className="empty-state">No enterprise domains added.</div>
              ) : (
                domains.map((d) => (
                  <div key={d.id} className="domain-row">
                    <div className="domain-info">
                      <span className="domain-name">{d.domain_name}</span>
                      <div className="token-row">
                        <span className="token-label">DNS TXT Record:</span>
                        <code className="token-code">{d.verification_token}</code>
                        <button
                          className="copy-btn"
                          onClick={() => handleCopy(d.verification_token, d.id)}
                          title="Copy verification token"
                        >
                          {copiedToken === d.id ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                        </button>
                      </div>
                    </div>
                    <div className="domain-action">
                      {d.is_verified ? (
                        <span className="verified-badge">
                          <CheckCircle2 size={16} /> Verified Domain
                        </span>
                      ) : (
                        <button
                          className="verify-btn"
                          onClick={() => handleVerifyDomain(d.id)}
                        >
                          <RefreshCw size={14} /> Verify DNS Record
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Two-Factor Authentication (TOTP) */}
      {activeTab === 'mfa' && (
        <div className="tab-pane">
          <div className="mfa-container">
            <h3 className="section-title">
              <Key size={18} /> Enterprise Multi-Factor Authentication
            </h3>
            <p className="section-subtitle">
              Secure your account using standard RFC 6238 time-based one-time passwords (TOTP), compatible with Google Authenticator, 1Password, or Authy.
            </p>

            {mfaEnabled ? (
              <div className="mfa-enabled-card">
                <CheckCircle2 size={36} color="#10b981" />
                <div className="mfa-enabled-info">
                  <h4>Two-Factor Authentication is Active</h4>
                  <p>Your account is protected with hardware/software TOTP tokens.</p>
                </div>
              </div>
            ) : mfaData ? (
              <div className="mfa-setup-card">
                <h4>Step 1: Save Your Secret Key</h4>
                <div className="secret-display">
                  <code>{mfaData.secret_key}</code>
                  <button
                    className="copy-btn"
                    onClick={() => handleCopy(mfaData.secret_key, 'mfa_secret')}
                  >
                    {copiedToken === 'mfa_secret' ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                  </button>
                </div>

                <h4>Step 2: Emergency Recovery Codes</h4>
                <p className="recovery-note">Save these single-use codes in a secure vault:</p>
                <div className="recovery-grid">
                  {mfaData.recovery_codes?.map((code, idx) => (
                    <code key={idx} className="recovery-code">
                      {code}
                    </code>
                  ))}
                </div>

                <h4>Step 3: Enter 6-digit Authenticator Code</h4>
                <form className="mfa-verify-form" onSubmit={handleVerifyMFACode}>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={mfaCode}
                    onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
                  />
                  <button type="submit" className="primary-btn">
                    Confirm & Enable MFA
                  </button>
                </form>
              </div>
            ) : (
              <div className="mfa-prompt-card">
                <p>Enhance your security posture by activating TOTP authentication.</p>
                <button className="primary-btn" onClick={handleStartMFASetup}>
                  Begin MFA Configuration
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Compliance Audit Trail */}
      {activeTab === 'audit' && (
        <div className="tab-pane">
          <div className="audit-export-card">
            <div className="audit-card-info">
              <h3 className="section-title">
                <FileSpreadsheet size={18} /> Compliance Audit Log Export
              </h3>
              <p className="section-subtitle">
                Download a tamper-evident, RFC-sanitized CSV export of all user authentication events, policy alterations, and role modifications.
              </p>
              <div className="audit-notice">
                <AlertTriangle size={16} />
                <span>Notice: All export requests are logged immutably for compliance forensics.</span>
              </div>
            </div>

            <button
              className="export-audit-btn"
              onClick={handleExportAuditLogs}
              disabled={isExportingAudit}
            >
              <Download size={16} />
              <span>{isExportingAudit ? 'Generating CSV...' : 'Export Audit Log (CSV)'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
