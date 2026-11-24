import React, { useState, useEffect, useMemo } from 'react';
import {
  LifeBuoy,
  Plus,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldAlert,
  Users,
  Send,
  Lock,
  MessageSquare,
  X,
  ArrowUpRight,
  ChevronDown,
  Building2,
  HelpCircle,
  TrendingUp,
  FileText,
  Activity,
} from 'lucide-react';
import { serviceDeskApi } from '../../services/serviceDeskApi';
import { useAuth } from '../../context/AuthContext';
import './ServiceDeskWorkspace.css';

export function ServiceDeskWorkspace() {
  const { user, isAuthenticated } = useAuth();

  // Navigation & View State
  const [activeTab, setActiveTab] = useState('tickets'); // 'tickets', 'dashboard', 'policies', 'performance'
  const [activeQueue, setActiveQueue] = useState('all'); // 'all', 'my', 'assigned', 'queue', 'unassigned', 'overdue', 'at_risk', 'breached', 'resolved'

  // Data State
  const [tickets, setTickets] = useState([]);
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [categories, setCategories] = useState([]);
  const [slaPolicies, setSlaPolicies] = useState([]);
  const [performanceData, setPerformanceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  // Selected Ticket for Drawer
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [ticketComments, setTicketComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [isSubmittingComment, setIsSubmittingComment] = useState(false);

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [showPolicyModal, setShowPolicyModal] = useState(false);

  // Forms
  const [createForm, setCreateForm] = useState({
    subject: '',
    description: '',
    category_name: 'Technical Support',
    priority: 'MEDIUM',
    tags: '',
  });
  const [escalateReason, setEscalateReason] = useState('');
  const [escalatePriority, setEscalatePriority] = useState('CRITICAL');
  const [policyForm, setPolicyForm] = useState({
    name: '',
    description: '',
    first_response_target_minutes: 60,
    resolution_target_minutes: 480,
    business_hours_start: '09:00',
    business_hours_end: '17:00',
    work_days: 'MON,TUE,WED,THU,FRI',
  });

  const isAgentOrAdmin = useMemo(() => {
    return ['Admin', 'Owner', 'Support', 'Manager'].includes(user?.role);
  }, [user]);

  // Load Initial Data
  const loadWorkspaceData = async () => {
    setIsLoading(true);
    try {
      const [ticketsRes, dashRes, catsRes] = await Promise.all([
        serviceDeskApi.getTickets({
          view: activeQueue,
          search: searchQuery || undefined,
          priority: priorityFilter || undefined,
          status: statusFilter || undefined,
          category_id: categoryFilter || undefined,
        }).catch(() => []),
        serviceDeskApi.getDashboard().catch(() => null),
        serviceDeskApi.getCategories().catch(() => []),
      ]);
      setTickets(Array.isArray(ticketsRes) ? ticketsRes : []);
      setDashboardMetrics(dashRes);
      setCategories(Array.isArray(catsRes) ? catsRes : []);

      if (activeTab === 'policies') {
        const polRes = await serviceDeskApi.getSLAPolicies().catch(() => []);
        setSlaPolicies(Array.isArray(polRes) ? polRes : []);
      }
      if (activeTab === 'performance') {
        const perfRes = await serviceDeskApi.getPerformanceReports().catch(() => null);
        setPerformanceData(perfRes);
      }
    } catch (err) {
      console.warn('Failed to load service desk data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadWorkspaceData();
  }, [activeQueue, activeTab, priorityFilter, statusFilter, categoryFilter]);

  // Load Comments when Ticket selected
  useEffect(() => {
    if (selectedTicket) {
      serviceDeskApi.getTicketComments(selectedTicket.id)
        .then((res) => setTicketComments(Array.isArray(res) ? res : []))
        .catch(() => setTicketComments([]));
    }
  }, [selectedTicket]);

  // Handle Create Ticket
  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!createForm.subject.trim() || !createForm.description.trim()) return;

    try {
      const payload = {
        subject: createForm.subject.trim(),
        description: createForm.description.trim(),
        category_name: createForm.category_name,
        priority: createForm.priority,
        tags: createForm.tags ? createForm.tags.split(',').map((t) => t.trim()) : [],
      };
      const created = await serviceDeskApi.createTicket(payload);
      setTickets((prev) => [created, ...prev]);
      setShowCreateModal(false);
      setCreateForm({
        subject: '',
        description: '',
        category_name: 'Technical Support',
        priority: 'MEDIUM',
        tags: '',
      });
      loadWorkspaceData();
    } catch (err) {
      alert('Failed to create ticket: ' + (err.message || 'Unknown error'));
    }
  };

  // Handle Status Transition
  const handleStatusChange = async (ticketId, nextStatus) => {
    let resNotes = undefined;
    if (nextStatus === 'RESOLVED') {
      resNotes = prompt('Please enter resolution notes (mandatory):');
      if (!resNotes || !resNotes.trim()) {
        alert('Resolution notes are required to resolve a ticket.');
        return;
      }
    }

    try {
      const updated = await serviceDeskApi.updateTicketStatus(ticketId, {
        status: nextStatus,
        resolution_notes: resNotes,
      });
      setTickets((prev) => prev.map((t) => (t.id === ticketId ? updated : t)));
      if (selectedTicket?.id === ticketId) setSelectedTicket(updated);
    } catch (err) {
      alert('Failed to update status: ' + (err.message || 'Workflow transition disallowed'));
    }
  };

  // Handle Escalate
  const handleEscalate = async (e) => {
    e.preventDefault();
    if (!selectedTicket || !escalateReason.trim()) return;

    try {
      await serviceDeskApi.escalateTicket(selectedTicket.id, {
        reason: escalateReason.trim(),
        bump_priority: escalatePriority,
      });
      setShowEscalateModal(false);
      setEscalateReason('');
      loadWorkspaceData();
      const refreshed = await serviceDeskApi.getTicketDetail(selectedTicket.id);
      setSelectedTicket(refreshed);
    } catch (err) {
      alert('Failed to escalate: ' + err.message);
    }
  };

  // Handle Add Comment
  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!selectedTicket || !newCommentText.trim()) return;

    setIsSubmittingComment(true);
    try {
      const comment = await serviceDeskApi.addTicketComment(selectedTicket.id, {
        content: newCommentText.trim(),
        is_internal_note: isInternalNote,
      });
      setTicketComments((prev) => [...prev, comment]);
      setNewCommentText('');
      setIsInternalNote(false);
      // Refresh ticket details for updated first response SLA
      const refreshed = await serviceDeskApi.getTicketDetail(selectedTicket.id);
      setSelectedTicket(refreshed);
      setTickets((prev) => prev.map((t) => (t.id === refreshed.id ? refreshed : t)));
    } catch (err) {
      alert('Failed to post comment: ' + err.message);
    } finally {
      setIsSubmittingComment(false);
    }
  };

  // Handle Recalculate SLAs
  const handleRecalculateSLAs = async () => {
    try {
      await serviceDeskApi.recalculateSLAs();
      await loadWorkspaceData();
      alert('SLA countdowns, at-risk classifications, and breach records evaluated.');
    } catch (err) {
      alert('Failed to recalculate SLAs: ' + err.message);
    }
  };

  return (
    <div className="service-desk-page">
      {/* 1. Header Bar */}
      <div className="sd-header-bar">
        <div className="sd-header-left">
          <div className="sd-icon-box">
            <LifeBuoy size={22} />
          </div>
          <div className="sd-title-group">
            <h2>Service Desk & SLA Operations</h2>
            <p>Internal support tickets, multi-tier SLAs, automated escalation, and service intelligence.</p>
          </div>
        </div>

        <div className="sd-header-actions">
          <button
            type="button"
            className="sd-btn secondary"
            onClick={handleRecalculateSLAs}
            title="Recalculate SLA countdowns and breach records"
          >
            <RefreshCw size={15} />
            <span>Recalculate SLAs</span>
          </button>
          <button
            type="button"
            className="sd-btn primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={15} />
            <span>New Support Ticket</span>
          </button>
        </div>
      </div>

      {/* 2. Subtabs Navigation */}
      <div className="sd-tabs-bar">
        <button
          type="button"
          className={`sd-tab-btn ${activeTab === 'tickets' ? 'active' : ''}`}
          onClick={() => setActiveTab('tickets')}
        >
          <FileText size={15} />
          <span>Tickets & Queues</span>
        </button>
        <button
          type="button"
          className={`sd-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          <Activity size={15} />
          <span>Service Analytics</span>
        </button>
        <button
          type="button"
          className={`sd-tab-btn ${activeTab === 'policies' ? 'active' : ''}`}
          onClick={() => setActiveTab('policies')}
        >
          <Clock size={15} />
          <span>SLA Policies</span>
        </button>
        <button
          type="button"
          className={`sd-tab-btn ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => setActiveTab('performance')}
        >
          <Users size={15} />
          <span>Team Performance</span>
        </button>
      </div>

      {/* 3. Operational KPI Cards */}
      {dashboardMetrics && (
        <div className="sd-kpi-grid">
          <div className="sd-kpi-card">
            <div className="sd-kpi-header">
              <span>Open Tickets</span>
              <LifeBuoy size={16} />
            </div>
            <div className="sd-kpi-value">{dashboardMetrics.open_tickets}</div>
            <div className="sd-kpi-sub">{dashboardMetrics.unassigned_tickets} unassigned requests</div>
          </div>

          <div className="sd-kpi-card">
            <div className="sd-kpi-header">
              <span>SLA Compliance</span>
              <CheckCircle2 size={16} style={{ color: '#16a34a' }} />
            </div>
            <div className="sd-kpi-value" style={{ color: dashboardMetrics.sla_compliance_rate >= 90 ? '#16a34a' : '#d97706' }}>
              {dashboardMetrics.sla_compliance_rate}%
            </div>
            <div className="sd-kpi-sub">{dashboardMetrics.breached_tickets} breached deadlines</div>
          </div>

          <div className="sd-kpi-card">
            <div className="sd-kpi-header">
              <span>Avg Response Time</span>
              <Clock size={16} />
            </div>
            <div className="sd-kpi-value">{dashboardMetrics.avg_first_response_minutes}m</div>
            <div className="sd-kpi-sub">First qualifying agent reply</div>
          </div>

          <div className="sd-kpi-card">
            <div className="sd-kpi-header">
              <span>Avg Resolution Time</span>
              <TrendingUp size={16} />
            </div>
            <div className="sd-kpi-value">{dashboardMetrics.avg_resolution_minutes}m</div>
            <div className="sd-kpi-sub">{dashboardMetrics.resolved_tickets} total resolved</div>
          </div>
        </div>
      )}

      {/* 4. Tab 1: Tickets & Queues */}
      {activeTab === 'tickets' && (
        <>
          {/* Queue Pills */}
          <div className="sd-queue-bar">
            {[
              { id: 'all', label: 'All Tickets' },
              { id: 'my', label: 'My Tickets' },
              { id: 'assigned', label: 'Assigned to Me' },
              { id: 'queue', label: 'Team Queue' },
              { id: 'unassigned', label: 'Unassigned' },
              { id: 'overdue', label: 'Overdue' },
              { id: 'at_risk', label: 'SLA at Risk' },
              { id: 'breached', label: 'SLA Breached' },
              { id: 'resolved', label: 'Resolved' },
            ].map((q) => (
              <button
                key={q.id}
                type="button"
                className={`sd-queue-pill ${activeQueue === q.id ? 'active' : ''}`}
                onClick={() => setActiveQueue(q.id)}
              >
                {q.label}
              </button>
            ))}
          </div>

          {/* Search & Filter Controls */}
          <div className="sd-filter-controls">
            <input
              type="text"
              className="sd-search-input"
              placeholder="Search by ticket #, subject, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadWorkspaceData()}
            />
            <select
              className="sd-filter-select"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              <option value="">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="URGENT">Urgent</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
            <select
              className="sd-filter-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="NEW">New</option>
              <option value="OPEN">Open</option>
              <option value="ASSIGNED">Assigned</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="WAITING_FOR_REQUESTER">Waiting for Requester</option>
              <option value="ESCALATED">Escalated</option>
              <option value="RESOLVED">Resolved</option>
              <option value="CLOSED">Closed</option>
            </select>
          </div>

          {/* Ticket Table */}
          <div className="sd-table-wrap">
            {tickets.length === 0 ? (
              <div style={{ padding: '40px 20px', textAlign: 'center', color: '#64748b' }}>
                <p>No tickets found matching the selected queue and filter criteria.</p>
              </div>
            ) : (
              <table className="sd-table">
                <thead>
                  <tr>
                    <th>Ticket #</th>
                    <th>Subject</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Requester</th>
                    <th>Assignee</th>
                    <th>SLA Response</th>
                    <th>SLA Resolution</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map((t) => (
                    <tr key={t.id} onClick={() => setSelectedTicket(t)}>
                      <td className="sd-ticket-num">{t.ticket_number}</td>
                      <td>
                        <strong>{t.subject}</strong>
                      </td>
                      <td>{t.category_name}</td>
                      <td>
                        <span className={`sd-priority-badge ${t.priority}`}>{t.priority}</span>
                      </td>
                      <td>
                        <span className={`sd-status-badge ${t.status}`}>{t.status.replace(/_/g, ' ')}</span>
                      </td>
                      <td>{t.requester_name || `User #${t.requester_id}`}</td>
                      <td>{t.assigned_agent_name || (t.assigned_team_name ? `Team: ${t.assigned_team_name}` : 'Unassigned')}</td>
                      <td>
                        <span className={`sd-sla-indicator ${t.sla_response_status}`}>
                          {t.sla_response_status}
                        </span>
                      </td>
                      <td>
                        <span className={`sd-sla-indicator ${t.sla_resolution_status}`}>
                          {t.sla_resolution_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* 5. Tab 2: Dashboard Analytics */}
      {activeTab === 'dashboard' && dashboardMetrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <div className="sd-kpi-card">
            <h4 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Tickets by Status</h4>
            {Object.entries(dashboardMetrics.by_status).map(([st, cnt]) => (
              <div key={st} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
                <span className={`sd-status-badge ${st}`}>{st.replace(/_/g, ' ')}</span>
                <strong>{cnt}</strong>
              </div>
            ))}
          </div>

          <div className="sd-kpi-card">
            <h4 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Tickets by Priority</h4>
            {Object.entries(dashboardMetrics.by_priority).map(([pri, cnt]) => (
              <div key={pri} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
                <span className={`sd-priority-badge ${pri}`}>{pri}</span>
                <strong>{cnt}</strong>
              </div>
            ))}
          </div>

          <div className="sd-kpi-card">
            <h4 style={{ margin: '0 0 12px 0', fontSize: '15px' }}>Tickets by Category</h4>
            {Object.entries(dashboardMetrics.by_category).map(([cat, cnt]) => (
              <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f1f5f9' }}>
                <span>{cat}</span>
                <strong>{cnt}</strong>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6. Tab 3: SLA Policies */}
      {activeTab === 'policies' && (
        <div className="sd-table-wrap">
          <table className="sd-table">
            <thead>
              <tr>
                <th>Policy Name</th>
                <th>Response Target</th>
                <th>Resolution Target</th>
                <th>Business Hours</th>
                <th>Working Days</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {slaPolicies.map((p) => (
                <tr key={p.id}>
                  <td><strong>{p.name}</strong></td>
                  <td>{p.first_response_target_minutes} mins</td>
                  <td>{p.resolution_target_minutes} mins ({(p.resolution_target_minutes / 60).toFixed(1)}h)</td>
                  <td>{p.business_hours_start} - {p.business_hours_end}</td>
                  <td>{p.work_days}</td>
                  <td>
                    <span className="sd-sla-indicator ON_TRACK">{p.is_active ? 'ACTIVE' : 'DISABLED'}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 7. Tab 4: Team Performance */}
      {activeTab === 'performance' && performanceData && (
        <div className="sd-table-wrap">
          <table className="sd-table">
            <thead>
              <tr>
                <th>Agent ID</th>
                <th>Assigned</th>
                <th>Open Workload</th>
                <th>Resolved</th>
                <th>SLA Breached</th>
              </tr>
            </thead>
            <tbody>
              {performanceData.agents?.map((a) => (
                <tr key={a.agent_id}>
                  <td>Agent #{a.agent_id}</td>
                  <td><strong>{a.assigned}</strong></td>
                  <td>{a.open}</td>
                  <td>{a.resolved}</td>
                  <td style={{ color: a.breached > 0 ? '#dc2626' : '#16a34a' }}>{a.breached}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ================= TICKET DETAIL DRAWER ================= */}
      {selectedTicket && (
        <div className="sd-detail-overlay" onClick={() => setSelectedTicket(null)}>
          <div className="sd-detail-drawer" onClick={(e) => e.stopPropagation()}>
            <div className="sd-drawer-header">
              <div>
                <span className="sd-ticket-num">{selectedTicket.ticket_number}</span>
                <h3 style={{ margin: '4px 0 0 0', fontSize: '18px' }}>{selectedTicket.subject}</h3>
              </div>
              <button
                type="button"
                className="sd-btn secondary"
                onClick={() => setSelectedTicket(null)}
              >
                <X size={16} />
              </button>
            </div>

            <div className="sd-drawer-body">
              {/* Status Action Buttons */}
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {selectedTicket.status !== 'IN_PROGRESS' && selectedTicket.status !== 'RESOLVED' && selectedTicket.status !== 'CLOSED' && (
                  <button
                    type="button"
                    className="sd-btn secondary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'IN_PROGRESS')}
                  >
                    Start Working (In Progress)
                  </button>
                )}
                {selectedTicket.status === 'IN_PROGRESS' && (
                  <button
                    type="button"
                    className="sd-btn secondary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'WAITING_FOR_REQUESTER')}
                  >
                    Wait for Requester (Pause SLA)
                  </button>
                )}
                {selectedTicket.status !== 'RESOLVED' && selectedTicket.status !== 'CLOSED' && (
                  <button
                    type="button"
                    className="sd-btn primary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'RESOLVED')}
                  >
                    Resolve Ticket
                  </button>
                )}
                {selectedTicket.status === 'RESOLVED' && (
                  <button
                    type="button"
                    className="sd-btn primary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'CLOSED')}
                  >
                    Close Ticket
                  </button>
                )}
                {(selectedTicket.status === 'RESOLVED' || selectedTicket.status === 'CLOSED') && (
                  <button
                    type="button"
                    className="sd-btn secondary"
                    onClick={() => handleStatusChange(selectedTicket.id, 'REOPENED')}
                  >
                    Reopen Ticket
                  </button>
                )}
                {selectedTicket.status !== 'ESCALATED' && (
                  <button
                    type="button"
                    className="sd-btn secondary"
                    style={{ borderColor: '#ef4444', color: '#dc2626' }}
                    onClick={() => setShowEscalateModal(true)}
                  >
                    Escalate
                  </button>
                )}
              </div>

              {/* Metadata Grid */}
              <div className="sd-detail-meta-grid">
                <div className="sd-meta-item">
                  <span className="sd-meta-label">Status</span>
                  <span className={`sd-status-badge ${selectedTicket.status}`}>{selectedTicket.status.replace(/_/g, ' ')}</span>
                </div>
                <div className="sd-meta-item">
                  <span className="sd-meta-label">Priority</span>
                  <span className={`sd-priority-badge ${selectedTicket.priority}`}>{selectedTicket.priority}</span>
                </div>
                <div className="sd-meta-item">
                  <span className="sd-meta-label">Requester</span>
                  <span className="sd-meta-val">{selectedTicket.requester_name || `User #${selectedTicket.requester_id}`}</span>
                </div>
                <div className="sd-meta-item">
                  <span className="sd-meta-label">Category</span>
                  <span className="sd-meta-val">{selectedTicket.category_name}</span>
                </div>
                <div className="sd-meta-item">
                  <span className="sd-meta-label">SLA Response Status</span>
                  <span className={`sd-sla-indicator ${selectedTicket.sla_response_status}`}>{selectedTicket.sla_response_status}</span>
                </div>
                <div className="sd-meta-item">
                  <span className="sd-meta-label">SLA Resolution Status</span>
                  <span className={`sd-sla-indicator ${selectedTicket.sla_resolution_status}`}>{selectedTicket.sla_resolution_status}</span>
                </div>
              </div>

              {/* Description */}
              <div>
                <h4 style={{ margin: '0 0 6px 0', fontSize: '14px' }}>Description</h4>
                <p style={{ margin: 0, fontSize: '13.5px', color: '#334155', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>
                  {selectedTicket.description}
                </p>
              </div>

              {/* Conversation Section */}
              <div className="sd-comments-section">
                <h4 style={{ margin: '0', fontSize: '14px' }}>Ticket Conversation</h4>
                {ticketComments.map((c) => (
                  <div key={c.id} className={`sd-comment-card ${c.is_internal_note ? 'internal-note' : ''}`}>
                    <div className="sd-comment-header">
                      <strong>{c.user_name || `User #${c.user_id}`}</strong>
                      {c.is_internal_note && <span className="sd-internal-tag">Private Internal Note</span>}
                      <span>{new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                    <p style={{ margin: 0, fontSize: '13px', color: '#1e293b', whiteSpace: 'pre-wrap' }}>{c.content}</p>
                  </div>
                ))}

                {/* Reply Editor */}
                <form onSubmit={handleAddComment} className="sd-reply-box">
                  <textarea
                    className="sd-reply-textarea"
                    placeholder="Type your response to the requester, or write a private note..."
                    value={newCommentText}
                    onChange={(e) => setNewCommentText(e.target.value)}
                  />
                  <div className="sd-reply-controls">
                    {isAgentOrAdmin && (
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={isInternalNote}
                          onChange={(e) => setIsInternalNote(e.target.checked)}
                        />
                        <Lock size={14} />
                        <span>Confidential internal note (hidden from customer)</span>
                      </label>
                    )}
                    <button
                      type="submit"
                      className="sd-btn primary"
                      disabled={isSubmittingComment || !newCommentText.trim()}
                    >
                      <Send size={14} />
                      <span>{isInternalNote ? 'Save Private Note' : 'Send Public Reply'}</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= CREATE TICKET MODAL ================= */}
      {showCreateModal && (
        <div className="sd-modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="sd-modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="sd-modal-header">
              <h3 style={{ margin: 0 }}>Create Support Ticket</h3>
              <button type="button" className="sd-btn secondary" onClick={() => setShowCreateModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleCreateTicket} className="sd-modal-body">
              <div className="sd-form-group">
                <label className="sd-form-label">Subject</label>
                <input
                  type="text"
                  className="sd-form-input"
                  required
                  placeholder="Short summary of the issue..."
                  value={createForm.subject}
                  onChange={(e) => setCreateForm({ ...createForm, subject: e.target.value })}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
                <div className="sd-form-group">
                  <label className="sd-form-label">Category</label>
                  <select
                    className="sd-form-select"
                    value={createForm.category_name}
                    onChange={(e) => setCreateForm({ ...createForm, category_name: e.target.value })}
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div className="sd-form-group">
                  <label className="sd-form-label">Priority</label>
                  <select
                    className="sd-form-select"
                    value={createForm.priority}
                    onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
              </div>

              <div className="sd-form-group">
                <label className="sd-form-label">Description</label>
                <textarea
                  className="sd-form-textarea"
                  required
                  placeholder="Detailed description of the issue or request..."
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                />
              </div>

              <div className="sd-form-group">
                <label className="sd-form-label">Tags (comma-separated)</label>
                <input
                  type="text"
                  className="sd-form-input"
                  placeholder="e.g. vpn, hardware, macos"
                  value={createForm.tags}
                  onChange={(e) => setCreateForm({ ...createForm, tags: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button type="button" className="sd-btn secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="sd-btn primary">
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================= ESCALATE MODAL ================= */}
      {showEscalateModal && (
        <div className="sd-modal-backdrop" onClick={() => setShowEscalateModal(false)}>
          <div className="sd-modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="sd-modal-header">
              <h3 style={{ margin: 0, color: '#dc2626' }}>Escalate Ticket</h3>
              <button type="button" className="sd-btn secondary" onClick={() => setShowEscalateModal(false)}>
                <X size={16} />
              </button>
            </div>
            <form onSubmit={handleEscalate} className="sd-modal-body">
              <div className="sd-form-group">
                <label className="sd-form-label">Escalation Reason</label>
                <textarea
                  className="sd-form-textarea"
                  required
                  placeholder="Explain why this request is being escalated..."
                  value={escalateReason}
                  onChange={(e) => setEscalateReason(e.target.value)}
                />
              </div>

              <div className="sd-form-group">
                <label className="sd-form-label">Bump Priority To</label>
                <select
                  className="sd-form-select"
                  value={escalatePriority}
                  onChange={(e) => setEscalatePriority(e.target.value)}
                >
                  <option value="HIGH">High</option>
                  <option value="URGENT">Urgent</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="sd-btn secondary" onClick={() => setShowEscalateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="sd-btn primary" style={{ backgroundColor: '#dc2626' }}>
                  Confirm Escalation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ServiceDeskWorkspace;
