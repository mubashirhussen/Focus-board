import React, { useState, useEffect } from 'react';
import {
  Globe,
  UserCheck,
  Send,
  FileCheck,
  MessageSquare,
  FileText,
  Shield,
  Settings,
  Plus,
  RefreshCw,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Download,
  Eye,
  X,
  Search,
} from 'lucide-react';
import { clientPortalApi } from '../../services/clientPortalApi';
import './ClientPortalWorkspace.css';

export function ClientPortalWorkspace({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('projects');
  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [invitations, setInvitations] = useState([]);
  const [guests, setGuests] = useState([]);
  const [deliverables, setDeliverables] = useState([]);
  const [feedbackList, setFeedbackList] = useState([]);
  const [reports, setReports] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [portalSettings, setPortalSettings] = useState(null);

  // Modals & Drawers
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [showFeedbackModal, setShowFeedbackModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedDeliverable, setSelectedDeliverable] = useState(null);
  const [projectComments, setProjectComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState('');

  // Form states
  const [inviteForm, setInviteForm] = useState({
    guest_email: '',
    guest_name: '',
    company_name: '',
    role: 'CLIENT_APPROVER',
    message: '',
    expiration_days: 7,
  });

  const [reviewForm, setReviewForm] = useState({
    decision: 'APPROVED',
    comments: '',
  });

  const [feedbackForm, setFeedbackForm] = useState({
    title: '',
    content: '',
    category: 'GENERAL',
  });

  const [reportForm, setReportForm] = useState({
    title: '',
    summary: '',
    status_override: 'ON_TRACK',
  });

  const [guestSearch, setGuestSearch] = useState('');
  const [copiedToken, setCopiedToken] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dash, invs, gsts, stgs] = await Promise.all([
        clientPortalApi.getDashboard().catch(() => null),
        clientPortalApi.getInvitations().catch(() => []),
        clientPortalApi.getGuests().catch(() => []),
        clientPortalApi.getSettings().catch(() => null),
      ]);
      setDashboardData(dash);
      setInvitations(invs || []);
      setGuests(gsts || []);
      setPortalSettings(stgs);

      // If we have projects, load deliverables & feedback for first project
      if (dash && dash.projects && dash.projects.length > 0) {
        const firstPid = dash.projects[0].project_id;
        const [delivs, fbs, reps] = await Promise.all([
          clientPortalApi.getDeliverables(firstPid).catch(() => []),
          clientPortalApi.getFeedback(firstPid).catch(() => []),
          clientPortalApi.getReports(firstPid).catch(() => []),
        ]);
        setDeliverables(delivs || []);
        setFeedbackList(fbs || []);
        setReports(reps || []);
      }

      const logs = await clientPortalApi.getAuditLogs().catch(() => []);
      setAuditLogs(logs || []);
    } catch (err) {
      console.error('Error loading client portal data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleOpenProjectDrawer = async (proj) => {
    setSelectedProject(proj);
    try {
      const [comments, delivs, fbs, reps] = await Promise.all([
        clientPortalApi.getComments(proj.project_id).catch(() => []),
        clientPortalApi.getDeliverables(proj.project_id).catch(() => []),
        clientPortalApi.getFeedback(proj.project_id).catch(() => []),
        clientPortalApi.getReports(proj.project_id).catch(() => []),
      ]);
      setProjectComments(comments || []);
      setDeliverables(delivs || []);
      setFeedbackList(fbs || []);
      setReports(reps || []);
    } catch (err) {
      console.error('Failed to load project details:', err);
    }
  };

  const handleSendInvite = async (e) => {
    e.preventDefault();
    try {
      const res = await clientPortalApi.createInvitation(inviteForm);
      if (res && res.raw_token) {
        setCopiedToken(res.raw_token);
      }
      setShowInviteModal(false);
      setInviteForm({
        guest_email: '',
        guest_name: '',
        company_name: '',
        role: 'CLIENT_APPROVER',
        message: '',
        expiration_days: 7,
      });
      loadData();
    } catch (err) {
      alert(`Failed to send invitation: ${err.message || 'Unknown error'}`);
    }
  };

  const handleReviewDeliverable = async (e) => {
    e.preventDefault();
    if (!selectedDeliverable) return;
    try {
      await clientPortalApi.reviewDeliverable(selectedDeliverable.id, reviewForm);
      setShowReviewModal(false);
      setSelectedDeliverable(null);
      setReviewForm({ decision: 'APPROVED', comments: '' });
      if (selectedProject) {
        const delivs = await clientPortalApi.getDeliverables(selectedProject.project_id);
        setDeliverables(delivs || []);
      }
      loadData();
    } catch (err) {
      alert(`Failed to review deliverable: ${err.message || 'Unknown error'}`);
    }
  };

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    if (!selectedProject) return;
    try {
      await clientPortalApi.submitFeedback(selectedProject.project_id, feedbackForm);
      setShowFeedbackModal(false);
      setFeedbackForm({ title: '', content: '', category: 'GENERAL' });
      const fbs = await clientPortalApi.getFeedback(selectedProject.project_id);
      setFeedbackList(fbs || []);
      loadData();
    } catch (err) {
      alert(`Failed to submit feedback: ${err.message || 'Unknown error'}`);
    }
  };

  const handlePostComment = async (e) => {
    e.preventDefault();
    if (!selectedProject || !newCommentText.trim()) return;
    try {
      await clientPortalApi.postComment(selectedProject.project_id, {
        content: newCommentText.trim(),
      });
      setNewCommentText('');
      const comments = await clientPortalApi.getComments(selectedProject.project_id);
      setProjectComments(comments || []);
    } catch (err) {
      alert(`Failed to post comment: ${err.message || 'Unknown error'}`);
    }
  };

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    if (!selectedProject) return;
    try {
      await clientPortalApi.createReport(selectedProject.project_id, reportForm);
      setShowReportModal(false);
      setReportForm({ title: '', summary: '', status_override: 'ON_TRACK' });
      const reps = await clientPortalApi.getReports(selectedProject.project_id);
      setReports(reps || []);
      loadData();
    } catch (err) {
      alert(`Failed to generate report: ${err.message || 'Unknown error'}`);
    }
  };

  const handleSuspendGuest = async (userId) => {
    if (!window.confirm('Suspend this guest account? They will immediately lose access.')) return;
    try {
      await clientPortalApi.suspendGuest(userId);
      loadData();
    } catch (err) {
      alert(`Failed to suspend guest: ${err.message}`);
    }
  };

  const handleReactivateGuest = async (userId) => {
    try {
      await clientPortalApi.reactivateGuest(userId);
      loadData();
    } catch (err) {
      alert(`Failed to reactivate guest: ${err.message}`);
    }
  };

  const handleRevokeGuest = async (userId) => {
    if (!window.confirm('Permanently revoke this guest from the organization?')) return;
    try {
      await clientPortalApi.revokeGuest(userId);
      loadData();
    } catch (err) {
      alert(`Failed to revoke guest: ${err.message}`);
    }
  };

  const handleRevokeInvite = async (invId) => {
    if (!window.confirm('Revoke this pending invitation?')) return;
    try {
      await clientPortalApi.revokeInvitation(invId);
      loadData();
    } catch (err) {
      alert(`Failed to revoke invitation: ${err.message}`);
    }
  };

  const projects = dashboardData?.projects || [];
  const totalSharedProjects = dashboardData?.total_shared_projects || projects.length;
  const pendingApprovalsCount = dashboardData?.pending_approvals || deliverables.filter(d => d.status === 'SUBMITTED').length;

  return (
    <div className="client-portal-container">
      {/* Header */}
      <div className="cp-header">
        <div className="cp-title-section">
          <h1>
            <Globe className="text-primary" size={28} />
            {portalSettings?.custom_portal_title || 'Client & Guest Portal'}
          </h1>
          <p>Secure external stakeholder workspace with controlled project sharing, deliverables review, and audit governance.</p>
        </div>
        <div className="cp-header-actions">
          <button type="button" className="cp-btn secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button type="button" className="cp-btn primary" onClick={() => setShowInviteModal(true)}>
            <Send size={16} />
            Invite Client / Guest
          </button>
        </div>
      </div>

      {/* Token banner if newly created */}
      {copiedToken && (
        <div style={{ background: '#ecfdf5', border: '1px solid #10b981', padding: '12px 16px', borderRadius: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong style={{ color: '#065f46' }}>Guest Invitation Token Created:</strong>
            <span style={{ fontFamily: 'monospace', marginLeft: '8px', color: '#047857' }}>{copiedToken}</span>
          </div>
          <button type="button" className="cp-btn secondary" onClick={() => setCopiedToken(null)}>Dismiss</button>
        </div>
      )}

      {/* KPI Summary Cards */}
      <div className="cp-kpis-grid">
        <div className="cp-kpi-card">
          <div className="cp-kpi-icon-wrapper blue">
            <Globe size={24} />
          </div>
          <div className="cp-kpi-info">
            <h3>Shared Projects</h3>
            <div className="cp-kpi-val">{totalSharedProjects}</div>
          </div>
        </div>

        <div className="cp-kpi-card">
          <div className="cp-kpi-icon-wrapper amber">
            <Clock size={24} />
          </div>
          <div className="cp-kpi-info">
            <h3>Pending Approvals</h3>
            <div className="cp-kpi-val">{pendingApprovalsCount}</div>
          </div>
        </div>

        <div className="cp-kpi-card">
          <div className="cp-kpi-icon-wrapper emerald">
            <UserCheck size={24} />
          </div>
          <div className="cp-kpi-info">
            <h3>Active Guests</h3>
            <div className="cp-kpi-val">{guests.filter(g => g.status === 'ACTIVE').length}</div>
          </div>
        </div>

        <div className="cp-kpi-card">
          <div className="cp-kpi-icon-wrapper purple">
            <MessageSquare size={24} />
          </div>
          <div className="cp-kpi-info">
            <h3>Client Feedback</h3>
            <div className="cp-kpi-val">{feedbackList.length}</div>
          </div>
        </div>
      </div>

      {/* Tabs Navigation */}
      <div className="cp-tabs-nav">
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'projects' ? 'active' : ''}`}
          onClick={() => setActiveTab('projects')}
        >
          <Globe size={18} />
          Shared Projects ({projects.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'invitations' ? 'active' : ''}`}
          onClick={() => setActiveTab('invitations')}
        >
          <Send size={18} />
          Guest Invitations ({invitations.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'guests' ? 'active' : ''}`}
          onClick={() => setActiveTab('guests')}
        >
          <UserCheck size={18} />
          Guest Directory ({guests.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'deliverables' ? 'active' : ''}`}
          onClick={() => setActiveTab('deliverables')}
        >
          <FileCheck size={18} />
          Deliverables & Approvals ({deliverables.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'feedback' ? 'active' : ''}`}
          onClick={() => setActiveTab('feedback')}
        >
          <MessageSquare size={18} />
          Client Feedback ({feedbackList.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'reports' ? 'active' : ''}`}
          onClick={() => setActiveTab('reports')}
        >
          <FileText size={18} />
          Progress Reports ({reports.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          <Shield size={18} />
          Audit Trail ({auditLogs.length})
        </button>
        <button
          type="button"
          className={`cp-tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          <Settings size={18} />
          Portal Governance
        </button>
      </div>

      {/* TAB 1: SHARED PROJECTS */}
      {activeTab === 'projects' && (
        <div>
          {projects.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '60px 20px', background: 'var(--bg-surface, #fff)', borderRadius: '12px', border: '1px solid var(--border-color, #e2e8f0)' }}>
              <Globe size={48} style={{ color: '#94a3b8', margin: '0 auto 12px auto' }} />
              <h3 style={{ margin: '0 0 8px 0', color: '#1e293b' }}>No Shared Projects Yet</h3>
              <p style={{ color: '#64748b', maxWidth: '420px', margin: '0 auto 16px auto' }}>Invite client stakeholders or share projects from the project settings menu to enable external visibility.</p>
              <button type="button" className="cp-btn primary" onClick={() => setShowInviteModal(true)}>
                <Send size={16} />
                Invite First Guest
              </button>
            </div>
          ) : (
            <div className="cp-projects-grid">
              {projects.map((proj) => (
                <div key={proj.project_id} className="cp-project-card">
                  <div className="cp-proj-card-top">
                    <div>
                      <h3>{proj.name}</h3>
                      <span style={{ fontSize: '0.8125rem', color: '#64748b' }}>Role: {proj.role}</span>
                    </div>
                    <span className="cp-badge green">{proj.status}</span>
                  </div>

                  {proj.description && <p className="cp-proj-desc">{proj.description}</p>}

                  {proj.progress_percent !== null && (
                    <div className="cp-proj-progress-wrapper">
                      <div className="cp-proj-progress-header">
                        <span>Approved Progress</span>
                        <span>{proj.progress_percent}%</span>
                      </div>
                      <div className="cp-progress-bar-bg">
                        <div className="cp-progress-bar-fill" style={{ width: `${proj.progress_percent}%` }} />
                      </div>
                    </div>
                  )}

                  <div className="cp-proj-card-footer">
                    <span>{proj.deliverables_count || 0} Deliverables</span>
                    <button type="button" className="cp-btn secondary" onClick={() => handleOpenProjectDrawer(proj)}>
                      <Eye size={14} />
                      Open Portal
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: GUEST INVITATIONS */}
      {activeTab === 'invitations' && (
        <div className="cp-table-wrapper">
          <table className="cp-table">
            <thead>
              <tr>
                <th>Guest Email</th>
                <th>Name</th>
                <th>Company</th>
                <th>Role</th>
                <th>Status</th>
                <th>Expires</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invitations.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                    No invitations found. Use 'Invite Client / Guest' to send an invitation.
                  </td>
                </tr>
              ) : (
                invitations.map((inv) => (
                  <tr key={inv.id}>
                    <td><strong>{inv.guest_email}</strong></td>
                    <td>{inv.guest_name}</td>
                    <td>{inv.company_name || '—'}</td>
                    <td><span className="cp-badge blue">{inv.role}</span></td>
                    <td>
                      <span className={`cp-badge ${inv.status === 'ACCEPTED' ? 'green' : inv.status === 'PENDING' ? 'amber' : 'red'}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td>{new Date(inv.expires_at).toLocaleDateString()}</td>
                    <td>
                      {inv.status === 'PENDING' && (
                        <button type="button" className="cp-btn danger" style={{ padding: '4px 10px', fontSize: '0.75rem' }} onClick={() => handleRevokeInvite(inv.id)}>
                          Revoke
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 3: GUEST DIRECTORY */}
      {activeTab === 'guests' && (
        <div className="cp-table-wrapper">
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color, #e2e8f0)', display: 'flex', gap: '12px' }}>
            <input
              type="text"
              placeholder="Search guests by name, email, or company..."
              className="cp-form-input"
              style={{ maxWidth: '360px' }}
              value={guestSearch}
              onChange={(e) => setGuestSearch(e.target.value)}
            />
          </div>
          <table className="cp-table">
            <thead>
              <tr>
                <th>Guest Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Type</th>
                <th>Status</th>
                <th>Active Projects</th>
                <th>Last Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {guests.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                    No guests registered in this organization.
                  </td>
                </tr>
              ) : (
                guests
                  .filter(g => !guestSearch || g.name.toLowerCase().includes(guestSearch.toLowerCase()) || g.email.toLowerCase().includes(guestSearch.toLowerCase()))
                  .map((g) => (
                    <tr key={g.id}>
                      <td><strong>{g.name}</strong></td>
                      <td>{g.email}</td>
                      <td>{g.company_name || '—'}</td>
                      <td><span className="cp-badge purple">{g.guest_type}</span></td>
                      <td>
                        <span className={`cp-badge ${g.status === 'ACTIVE' ? 'green' : 'red'}`}>
                          {g.status}
                        </span>
                      </td>
                      <td>{g.active_projects_count}</td>
                      <td>{g.last_access_at ? new Date(g.last_access_at).toLocaleDateString() : 'Never'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {g.status === 'ACTIVE' ? (
                            <button type="button" className="cp-btn secondary" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => handleSuspendGuest(g.user_id)}>
                              Suspend
                            </button>
                          ) : (
                            <button type="button" className="cp-btn success" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => handleReactivateGuest(g.user_id)}>
                              Reactivate
                            </button>
                          )}
                          <button type="button" className="cp-btn danger" style={{ padding: '4px 8px', fontSize: '0.75rem' }} onClick={() => handleRevokeGuest(g.user_id)}>
                            Revoke
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 4: DELIVERABLES */}
      {activeTab === 'deliverables' && (
        <div className="cp-table-wrapper">
          <table className="cp-table">
            <thead>
              <tr>
                <th>Deliverable Title</th>
                <th>Version</th>
                <th>Status</th>
                <th>Submitted At</th>
                <th>Reviewer</th>
                <th>Decision & Comments</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {deliverables.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                    No deliverables submitted yet for this project.
                  </td>
                </tr>
              ) : (
                deliverables.map((d) => (
                  <tr key={d.id}>
                    <td>
                      <strong>{d.title}</strong>
                      {d.description && <div style={{ fontSize: '0.8125rem', color: '#64748b' }}>{d.description}</div>}
                    </td>
                    <td>v{d.version_number}</td>
                    <td>
                      <span className={`cp-badge ${d.status === 'APPROVED' ? 'green' : d.status === 'CHANGES_REQUESTED' ? 'red' : 'amber'}`}>
                        {d.status}
                      </span>
                    </td>
                    <td>{new Date(d.submitted_at).toLocaleDateString()}</td>
                    <td>{d.reviewed_by || '—'}</td>
                    <td>{d.review_comments || '—'}</td>
                    <td>
                      <button
                        type="button"
                        className="cp-btn primary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        onClick={() => {
                          setSelectedDeliverable(d);
                          setShowReviewModal(true);
                        }}
                      >
                        Review
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 5: CLIENT FEEDBACK */}
      {activeTab === 'feedback' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="cp-btn primary"
              disabled={!selectedProject && projects.length === 0}
              onClick={() => {
                if (!selectedProject && projects.length > 0) setSelectedProject(projects[0]);
                setShowFeedbackModal(true);
              }}
            >
              <Plus size={16} />
              Submit Client Feedback
            </button>
          </div>
          <div className="cp-table-wrapper">
            <table className="cp-table">
              <thead>
                <tr>
                  <th>Category</th>
                  <th>Title</th>
                  <th>Feedback Summary</th>
                  <th>Status</th>
                  <th>Author</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {feedbackList.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                      No feedback submitted yet.
                    </td>
                  </tr>
                ) : (
                  feedbackList.map((f) => (
                    <tr key={f.id}>
                      <td><span className="cp-badge purple">{f.category}</span></td>
                      <td><strong>{f.title}</strong></td>
                      <td>{f.content}</td>
                      <td>
                        <span className={`cp-badge ${f.status === 'RESOLVED' ? 'green' : f.status === 'NEW' ? 'blue' : 'amber'}`}>
                          {f.status}
                        </span>
                      </td>
                      <td>{f.author}</td>
                      <td>{new Date(f.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 6: PROGRESS REPORTS */}
      {activeTab === 'reports' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="cp-btn primary"
              disabled={!selectedProject && projects.length === 0}
              onClick={() => {
                if (!selectedProject && projects.length > 0) setSelectedProject(projects[0]);
                setShowReportModal(true);
              }}
            >
              <Plus size={16} />
              Generate Client Report
            </button>
          </div>
          <div className="cp-table-wrapper">
            <table className="cp-table">
              <thead>
                <tr>
                  <th>Report Title</th>
                  <th>Summary</th>
                  <th>Status Override</th>
                  <th>Approved Progress</th>
                  <th>Tasks Count</th>
                  <th>Deliverables Count</th>
                  <th>Published Date</th>
                </tr>
              </thead>
              <tbody>
                {reports.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                      No client progress reports generated yet.
                    </td>
                  </tr>
                ) : (
                  reports.map((r) => (
                    <tr key={r.id}>
                      <td><strong>{r.title}</strong></td>
                      <td>{r.summary || '—'}</td>
                      <td><span className="cp-badge green">{r.status_override}</span></td>
                      <td>{r.progress_percent}%</td>
                      <td>{r.tasks_count}</td>
                      <td>{r.deliverables_count}</td>
                      <td>{new Date(r.published_at).toLocaleDateString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 7: AUDIT LOGS */}
      {activeTab === 'audit' && (
        <div className="cp-table-wrapper">
          <table className="cp-table">
            <thead>
              <tr>
                <th>Action</th>
                <th>Guest User</th>
                <th>Resource Type</th>
                <th>Resource ID</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: '#64748b' }}>
                    No audit logs recorded yet.
                  </td>
                </tr>
              ) : (
                auditLogs.map((l) => (
                  <tr key={l.id}>
                    <td><span className="cp-badge blue">{l.action}</span></td>
                    <td><strong>{l.guest_name}</strong></td>
                    <td>{l.resource_type || '—'}</td>
                    <td>{l.resource_id || '—'}</td>
                    <td>{new Date(l.created_at).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB 8: SETTINGS */}
      {activeTab === 'settings' && portalSettings && (
        <div style={{ background: 'var(--bg-surface, #fff)', border: '1px solid var(--border-color, #e2e8f0)', borderRadius: '12px', padding: '24px', maxWidth: '680px' }}>
          <h2 style={{ margin: '0 0 16px 0', fontSize: '1.25rem', color: '#0f172a' }}>Client Portal Governance Settings</h2>
          <div className="cp-form-group">
            <label>Custom Portal Title</label>
            <input
              type="text"
              className="cp-form-input"
              value={portalSettings.custom_portal_title || ''}
              onChange={(e) => setPortalSettings({ ...portalSettings, custom_portal_title: e.target.value })}
            />
          </div>
          <div className="cp-form-group">
            <label>Default Guest Role</label>
            <select
              className="cp-form-select"
              value={portalSettings.default_role || 'CLIENT_VIEWER'}
              onChange={(e) => setPortalSettings({ ...portalSettings, default_role: e.target.value })}
            >
              <option value="CLIENT_VIEWER">Client Viewer (Read Only)</option>
              <option value="CLIENT_COLLABORATOR">Client Collaborator (Comments & Uploads)</option>
              <option value="CLIENT_APPROVER">Client Approver (Deliverables Review & Approvals)</option>
            </select>
          </div>
          <div className="cp-form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              id="allowComments"
              checked={portalSettings.allow_guest_comments ?? true}
              onChange={(e) => setPortalSettings({ ...portalSettings, allow_guest_comments: e.target.checked })}
            />
            <label htmlFor="allowComments" style={{ cursor: 'pointer' }}>Allow Guest Comments & Discussions</label>
          </div>
          <div className="cp-form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '10px' }}>
            <input
              type="checkbox"
              id="requireReason"
              checked={portalSettings.require_approval_reason ?? true}
              onChange={(e) => setPortalSettings({ ...portalSettings, require_approval_reason: e.target.checked })}
            />
            <label htmlFor="requireReason" style={{ cursor: 'pointer' }}>Require Reason Comments on Rejection / Revision</label>
          </div>
          <button
            type="button"
            className="cp-btn primary"
            style={{ marginTop: '16px' }}
            onClick={async () => {
              try {
                await clientPortalApi.updateSettings(portalSettings);
                alert('Portal governance settings updated successfully.');
              } catch (err) {
                alert(`Failed to save settings: ${err.message}`);
              }
            }}
          >
            Save Settings
          </button>
        </div>
      )}

      {/* MODAL: INVITE GUEST */}
      {showInviteModal && (
        <div className="cp-modal-overlay">
          <div className="cp-modal-content">
            <div className="cp-modal-header">
              <h2>Invite External Stakeholder / Client</h2>
              <button type="button" className="cp-btn secondary" onClick={() => setShowInviteModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSendInvite}>
              <div className="cp-form-group">
                <label>Guest Email Address *</label>
                <input
                  type="email"
                  required
                  className="cp-form-input"
                  placeholder="client@acmecorp.com"
                  value={inviteForm.guest_email}
                  onChange={(e) => setInviteForm({ ...inviteForm, guest_email: e.target.value })}
                />
              </div>

              <div className="cp-form-group">
                <label>Guest Full Name *</label>
                <input
                  type="text"
                  required
                  className="cp-form-input"
                  placeholder="Jane Doe"
                  value={inviteForm.guest_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, guest_name: e.target.value })}
                />
              </div>

              <div className="cp-form-group">
                <label>Company / Organization Name</label>
                <input
                  type="text"
                  className="cp-form-input"
                  placeholder="Acme Corporation"
                  value={inviteForm.company_name}
                  onChange={(e) => setInviteForm({ ...inviteForm, company_name: e.target.value })}
                />
              </div>

              <div className="cp-form-group">
                <label>Assigned Guest Role</label>
                <select
                  className="cp-form-select"
                  value={inviteForm.role}
                  onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                >
                  <option value="CLIENT_VIEWER">Client Viewer (Read Only)</option>
                  <option value="CLIENT_COLLABORATOR">Client Collaborator (Comments & Feedback)</option>
                  <option value="CLIENT_APPROVER">Client Approver (Deliverables Review & Approvals)</option>
                </select>
              </div>

              <div className="cp-form-group">
                <label>Personal Invitation Message</label>
                <textarea
                  className="cp-form-textarea"
                  placeholder="Welcome! You have been granted access to review our project deliverables."
                  value={inviteForm.message}
                  onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="cp-btn secondary" onClick={() => setShowInviteModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="cp-btn primary">
                  Generate Invitation Token
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: REVIEW DELIVERABLE */}
      {showReviewModal && selectedDeliverable && (
        <div className="cp-modal-overlay">
          <div className="cp-modal-content">
            <div className="cp-modal-header">
              <h2>Review Deliverable: {selectedDeliverable.title}</h2>
              <button type="button" className="cp-btn secondary" onClick={() => setShowReviewModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleReviewDeliverable}>
              <div className="cp-form-group">
                <label>Review Decision *</label>
                <select
                  className="cp-form-select"
                  value={reviewForm.decision}
                  onChange={(e) => setReviewForm({ ...reviewForm, decision: e.target.value })}
                >
                  <option value="APPROVED">Approve Deliverable</option>
                  <option value="CHANGES_REQUESTED">Request Changes / Revisions</option>
                </select>
              </div>

              <div className="cp-form-group">
                <label>Review Comments {reviewForm.decision === 'CHANGES_REQUESTED' ? '*' : '(Optional)'}</label>
                <textarea
                  required={reviewForm.decision === 'CHANGES_REQUESTED'}
                  className="cp-form-textarea"
                  placeholder={reviewForm.decision === 'CHANGES_REQUESTED' ? 'Specify required adjustments...' : 'Optional approval notes...'}
                  value={reviewForm.comments}
                  onChange={(e) => setReviewForm({ ...reviewForm, comments: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="cp-btn secondary" onClick={() => setShowReviewModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="cp-btn primary">
                  Submit Decision
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: SUBMIT FEEDBACK */}
      {showFeedbackModal && (
        <div className="cp-modal-overlay">
          <div className="cp-modal-content">
            <div className="cp-modal-header">
              <h2>Submit Client Feedback</h2>
              <button type="button" className="cp-btn secondary" onClick={() => setShowFeedbackModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSubmitFeedback}>
              <div className="cp-form-group">
                <label>Feedback Title *</label>
                <input
                  type="text"
                  required
                  className="cp-form-input"
                  placeholder="Summary of your inquiry or feedback"
                  value={feedbackForm.title}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, title: e.target.value })}
                />
              </div>

              <div className="cp-form-group">
                <label>Category</label>
                <select
                  className="cp-form-select"
                  value={feedbackForm.category}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, category: e.target.value })}
                >
                  <option value="GENERAL">General Inquiry</option>
                  <option value="BUG">Issue / Bug</option>
                  <option value="IMPROVEMENT">Improvement Suggestion</option>
                  <option value="QUESTION">Question</option>
                </select>
              </div>

              <div className="cp-form-group">
                <label>Details & Narrative *</label>
                <textarea
                  required
                  className="cp-form-textarea"
                  placeholder="Provide context or details..."
                  value={feedbackForm.content}
                  onChange={(e) => setFeedbackForm({ ...feedbackForm, content: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="cp-btn secondary" onClick={() => setShowFeedbackModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="cp-btn primary">
                  Submit Feedback
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: GENERATE REPORT */}
      {showReportModal && (
        <div className="cp-modal-overlay">
          <div className="cp-modal-content">
            <div className="cp-modal-header">
              <h2>Generate Client Progress Report</h2>
              <button type="button" className="cp-btn secondary" onClick={() => setShowReportModal(false)}>
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleGenerateReport}>
              <div className="cp-form-group">
                <label>Report Title *</label>
                <input
                  type="text"
                  required
                  className="cp-form-input"
                  placeholder="e.g. Bi-Weekly Progress Report"
                  value={reportForm.title}
                  onChange={(e) => setReportForm({ ...reportForm, title: e.target.value })}
                />
              </div>

              <div className="cp-form-group">
                <label>Status</label>
                <select
                  className="cp-form-select"
                  value={reportForm.status_override}
                  onChange={(e) => setReportForm({ ...reportForm, status_override: e.target.value })}
                >
                  <option value="ON_TRACK">On Track</option>
                  <option value="AT_RISK">At Risk</option>
                  <option value="DELAYED">Delayed</option>
                  <option value="COMPLETED">Completed</option>
                </select>
              </div>

              <div className="cp-form-group">
                <label>Executive Summary</label>
                <textarea
                  className="cp-form-textarea"
                  placeholder="Key milestones achieved and next deliverables..."
                  value={reportForm.summary}
                  onChange={(e) => setReportForm({ ...reportForm, summary: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '20px' }}>
                <button type="button" className="cp-btn secondary" onClick={() => setShowReportModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="cp-btn primary">
                  Publish Report
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SLIDE-OVER DRAWER: PROJECT DETAIL */}
      {selectedProject && (
        <div className="cp-drawer-overlay" onClick={() => setSelectedProject(null)}>
          <div className="cp-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="cp-drawer-header">
              <div>
                <h2 style={{ margin: '0 0 4px 0', fontSize: '1.25rem', color: '#0f172a' }}>{selectedProject.name}</h2>
                <span className="cp-badge green">{selectedProject.status}</span>
              </div>
              <button type="button" className="cp-btn secondary" onClick={() => setSelectedProject(null)}>
                <X size={18} />
              </button>
            </div>

            <div className="cp-drawer-body">
              {/* Progress */}
              {selectedProject.progress_percent !== null && (
                <div>
                  <div className="cp-proj-progress-header">
                    <span>Overall Project Progress</span>
                    <span>{selectedProject.progress_percent}%</span>
                  </div>
                  <div className="cp-progress-bar-bg" style={{ marginTop: '6px' }}>
                    <div className="cp-progress-bar-fill" style={{ width: `${selectedProject.progress_percent}%` }} />
                  </div>
                </div>
              )}

              {/* Deliverables section */}
              <div>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#0f172a' }}>Deliverables</h3>
                {deliverables.length === 0 ? (
                  <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No deliverables for this project.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {deliverables.map((d) => (
                      <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f8fafc', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                        <div>
                          <strong>{d.title}</strong>
                          <span style={{ marginLeft: '8px', fontSize: '0.75rem', color: '#64748b' }}>v{d.version_number}</span>
                        </div>
                        <span className={`cp-badge ${d.status === 'APPROVED' ? 'green' : 'amber'}`}>{d.status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Comments Thread */}
              <div>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '1rem', color: '#0f172a' }}>Client-Visible Discussion</h3>
                <div className="cp-comments-timeline">
                  {projectComments.length === 0 ? (
                    <p style={{ color: '#64748b', fontSize: '0.875rem' }}>No messages posted yet. Start the conversation below.</p>
                  ) : (
                    projectComments.map((c) => (
                      <div key={c.id} className="cp-comment-item">
                        <div className="cp-comment-meta">
                          <strong>{c.author_name}</strong>
                          <span>{new Date(c.created_at).toLocaleTimeString()}</span>
                        </div>
                        <p className="cp-comment-text">{c.content}</p>
                      </div>
                    ))
                  )}
                </div>

                <form onSubmit={handlePostComment} style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    required
                    className="cp-form-input"
                    style={{ flex: 1 }}
                    placeholder="Type a message to project stakeholders..."
                    value={newCommentText}
                    onChange={(e) => setNewCommentText(e.target.value)}
                  />
                  <button type="submit" className="cp-btn primary">
                    Send
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ClientPortalWorkspace;
