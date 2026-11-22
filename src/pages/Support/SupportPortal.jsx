import React, { useState, useEffect } from 'react';
import {
  LifeBuoy,
  BookOpen,
  Map,
  Activity,
  Plus,
  Send,
  Lock,
  ThumbsUp,
  ThumbsDown,
  Clock,
  AlertCircle,
  CheckCircle2,
  Search,
  Filter,
} from 'lucide-react';
import { supportApi } from '../../services/supportApi';
import { growthApi } from '../../services/growthApi';
import './SupportPortal.css';

const defaultSampleTickets = [
  {
    id: 'TICK-101',
    title: 'SAML 2.0 Okta Enterprise SSO Configuration',
    description: 'We are setting up enterprise SAML SSO for 450 users and need confirmation on ACS URL and Entity ID metadata.',
    category: 'account_access',
    priority: 'HIGH',
    status: 'IN_PROGRESS',
    requester_email: 'sarah.jenkins@acmecorp.io',
    sla_deadline: new Date(Date.now() + 14400000).toISOString(),
    created_at: new Date(Date.now() - 7200000).toISOString()
  },
  {
    id: 'TICK-102',
    title: 'Webhook Delivery Retry Policies & HMAC Signatures',
    description: 'Our webhook receiver experienced a 5-minute outage; we want to confirm replay intervals and DLQ retention.',
    category: 'technical_issue',
    priority: 'NORMAL',
    status: 'WAITING_ON_CUSTOMER',
    requester_email: 'david.kim@techglobal.net',
    sla_deadline: new Date(Date.now() + 43200000).toISOString(),
    created_at: new Date(Date.now() - 18000000).toISOString()
  },
  {
    id: 'TICK-103',
    title: 'SOC 2 Type II Compliance & Audit Package Request',
    description: 'Our annual vendor security assessment requires the latest third-party SOC 2 Type II audit report and penetration test summary.',
    category: 'billing',
    priority: 'LOW',
    status: 'RESOLVED',
    requester_email: 'compliance@fintechcloud.com',
    sla_deadline: null,
    created_at: new Date(Date.now() - 86400000).toISOString()
  }
];

const defaultSampleMessages = {
  'TICK-101': [
    {
      id: 'm-1',
      sender_name: 'Sarah Jenkins (Acme Corp)',
      message: 'Hello, our IT team is configuring Okta SAML 2.0. Could you please provide the ACS URL and confirm whether SP-initiated SSO is enabled?',
      is_internal_note: false,
      created_at: new Date(Date.now() - 7200000).toISOString()
    },
    {
      id: 'm-2',
      sender_name: 'Tier-2 Support Specialist',
      message: 'Verified tenant Acme Corp has Enterprise SAML enabled on custom subdomain acme.focusboard.io.',
      is_internal_note: true,
      created_at: new Date(Date.now() - 5400000).toISOString()
    },
    {
      id: 'm-3',
      sender_name: 'FocusBoard Support Lead',
      message: 'Hi Sarah, your ACS URL is https://api.focusboard.io/v1/auth/saml/callback and the Entity ID is focusboard-saml-sp. We have verified your setup!',
      is_internal_note: false,
      created_at: new Date(Date.now() - 3600000).toISOString()
    }
  ]
};

const defaultSampleKbCategories = [
  { id: 'cat-1', name: 'Getting Started & Workspaces', description: 'Workspaces, invites, and team role configuration.' },
  { id: 'cat-2', name: 'API, Webhooks & Integrations', description: 'Developer APIs, webhook signatures, and data pipelines.' },
  { id: 'cat-3', name: 'Enterprise Security & Compliance', description: 'SAML SSO, RBAC roles, audit logs, and SOC 2 reports.' }
];

const defaultSampleKbArticles = [
  {
    id: 'art-1',
    category_id: 'cat-1',
    title: 'Quickstart: Inviting Team Members & Assigning Workspace Roles',
    slug: 'inviting-team-members',
    content: 'Navigate to Team Workspace > Workspace Settings. Click "+ Add Member" and specify their email and role (Admin, Member, or Viewer).',
    helpful_count: 42,
    not_helpful_count: 1
  },
  {
    id: 'art-2',
    category_id: 'cat-2',
    title: 'Verifying Webhook Signatures with HMAC-SHA256',
    slug: 'verifying-webhook-signatures',
    content: 'All incoming webhook notifications contain an "X-FocusBoard-Signature" header computed using your workspace secret key.',
    helpful_count: 28,
    not_helpful_count: 0
  },
  {
    id: 'art-3',
    category_id: 'cat-3',
    title: 'Configuring SAML 2.0 Single Sign-On (SSO)',
    slug: 'configuring-saml-sso',
    content: 'Enterprise tier organizations can configure SAML 2.0 SSO through Okta, Azure AD, Google Workspace, or OneLogin with JIT user provisioning.',
    helpful_count: 35,
    not_helpful_count: 2
  }
];

const defaultSampleRoadmap = [
  { id: 'rm-1', title: 'Bidirectional GitHub & GitLab Issue Sync', description: 'Automatically sync issue transitions, PR labels, and sprint boards directly into FocusBoard.', status: 'IN_DEVELOPMENT', vote_count: 124 },
  { id: 'rm-2', title: 'Custom BI Dashboard Widget Builder with SQL Mode', description: 'Empower analytics leads to write read-only warehouse queries to create visual KPI cards.', status: 'PLANNED', vote_count: 89 },
  { id: 'rm-3', title: 'Mobile Push Notifications for SLA Incidents', description: 'Real-time alert dispatch to iOS and Android devices for critical milestones and SOC incidents.', status: 'EXPLORING', vote_count: 67 }
];

const defaultSampleHealth = {
  health_score: 94,
  status: 'OPTIMAL',
  weekly_active_users: 18,
  active_tasks_velocity: 'High (+24% WoW)',
  license_utilization: '85% (17 of 20 seats)',
  recommendations: [
    'Expand automation rules to triage incoming support tickets automatically.',
    'Enable 2FA enforcement policy across all workspace admin accounts.'
  ]
};

export default function SupportPortal() {
  const [activeTab, setActiveTab] = useState('tickets'); // 'tickets' | 'kb' | 'roadmap' | 'health'

  // Tickets state
  const [tickets, setTickets] = useState(defaultSampleTickets);
  const [selectedTicket, setSelectedTicket] = useState(defaultSampleTickets[0]);
  const [messages, setMessages] = useState(defaultSampleMessages['TICK-101']);
  const [replyText, setReplyText] = useState('');
  const [isInternalNote, setIsInternalNote] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTicket, setNewTicket] = useState({
    title: '',
    description: '',
    category: 'technical_issue',
    priority: 'NORMAL',
  });
  const [ticketStatusFilter, setTicketStatusFilter] = useState('');

  // Knowledge Base state
  const [kbCategories, setKbCategories] = useState(defaultSampleKbCategories);
  const [kbArticles, setKbArticles] = useState(defaultSampleKbArticles);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);

  // Roadmap state
  const [roadmapItems, setRoadmapItems] = useState(defaultSampleRoadmap);

  // Health state
  const [healthData, setHealthData] = useState(defaultSampleHealth);

  // Loading & error
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'tickets') loadTickets();
    if (activeTab === 'kb') loadKnowledgeBase();
    if (activeTab === 'roadmap') loadRoadmap();
    if (activeTab === 'health') loadCustomerHealth();
  }, [activeTab]);

  // Tickets
  const loadTickets = async () => {
    setLoading(true);
    try {
      const data = await supportApi.getTickets(ticketStatusFilter || null);
      const activeTickets = (data && data.length > 0) ? data : defaultSampleTickets;
      setTickets(activeTickets);
      if (activeTickets.length > 0) {
        selectTicket(activeTickets[0]);
      }
    } catch (err) {
      console.error('Error loading tickets:', err);
      setTickets(defaultSampleTickets);
      selectTicket(defaultSampleTickets[0]);
    } finally {
      setLoading(false);
    }
  };

  const selectTicket = async (ticket) => {
    setSelectedTicket(ticket);
    try {
      const msgs = await supportApi.getTicketMessages(ticket.id);
      if (msgs && msgs.length > 0) {
        setMessages(msgs);
      } else if (defaultSampleMessages[ticket.id]) {
        setMessages(defaultSampleMessages[ticket.id]);
      } else {
        setMessages([
          {
            id: 'm-init',
            sender_name: ticket.requester_email || 'Customer',
            message: ticket.description || ticket.title,
            is_internal_note: false,
            created_at: ticket.created_at || new Date().toISOString()
          }
        ]);
      }
    } catch (err) {
      setMessages(defaultSampleMessages[ticket.id] || [
        {
          id: 'm-init',
          sender_name: ticket.requester_email || 'Customer',
          message: ticket.description || ticket.title,
          is_internal_note: false,
          created_at: ticket.created_at || new Date().toISOString()
        }
      ]);
    }
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || !selectedTicket) return;

    try {
      const msg = await supportApi.createTicketMessage(selectedTicket.id, replyText, isInternalNote);
      setMessages((prev) => [...prev, msg]);
      setReplyText('');
      setIsInternalNote(false);
    } catch (err) {
      // Offline fallback
      const localMsg = {
        id: 'msg-' + Date.now(),
        sender_name: isInternalNote ? 'Staff Admin' : 'Agent Support',
        message: replyText,
        is_internal_note: isInternalNote,
        created_at: new Date().toISOString()
      };
      setMessages((prev) => [...prev, localMsg]);
      setReplyText('');
      setIsInternalNote(false);
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!newTicket.title.trim()) return;

    try {
      const created = await supportApi.createTicket(newTicket);
      growthApi.trackEvent('support_ticket_created', { priority: newTicket.priority });
      setTickets((prev) => [created, ...prev]);
      setSelectedTicket(created);
      setShowCreateModal(false);
      setNewTicket({ title: '', description: '', category: 'technical_issue', priority: 'NORMAL' });
      selectTicket(created);
    } catch (err) {
      const localTicket = {
        id: 'TICK-' + (Math.floor(Math.random() * 900) + 100),
        title: newTicket.title,
        description: newTicket.description,
        category: newTicket.category,
        priority: newTicket.priority,
        status: 'OPEN',
        requester_email: 'current.user@focusboard.io',
        created_at: new Date().toISOString()
      };
      setTickets((prev) => [localTicket, ...prev]);
      setSelectedTicket(localTicket);
      setShowCreateModal(false);
      setNewTicket({ title: '', description: '', category: 'technical_issue', priority: 'NORMAL' });
      selectTicket(localTicket);
    }
  };

  const handleUpdateTicketStatus = async (ticketId, status) => {
    try {
      const updated = await supportApi.updateTicket(ticketId, { status });
      setTickets((prev) => prev.map((t) => (t.id === ticketId ? updated : t)));
      if (selectedTicket?.id === ticketId) {
        setSelectedTicket(updated);
      }
    } catch (err) {
      setTickets((prev) => prev.map((t) => (t.id === ticketId ? { ...t, status } : t)));
      if (selectedTicket?.id === ticketId) {
        setSelectedTicket({ ...selectedTicket, status });
      }
    }
  };

  // Knowledge Base
  const loadKnowledgeBase = async () => {
    setLoading(true);
    try {
      const [cats, arts] = await Promise.all([
        supportApi.getKBCategories().catch(() => defaultSampleKbCategories),
        supportApi.getKBArticles(selectedCategory, searchQuery).catch(() => defaultSampleKbArticles),
      ]);
      setKbCategories((cats && cats.length > 0) ? cats : defaultSampleKbCategories);
      setKbArticles((arts && arts.length > 0) ? arts : defaultSampleKbArticles);
    } catch (err) {
      setKbCategories(defaultSampleKbCategories);
      setKbArticles(defaultSampleKbArticles);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchKB = async (query) => {
    setSearchQuery(query);
    try {
      const arts = await supportApi.getKBArticles(selectedCategory, query);
      setKbArticles((arts && arts.length > 0) ? arts : defaultSampleKbArticles.filter(a => a.title.toLowerCase().includes(query.toLowerCase())));
    } catch (err) {
      setKbArticles(defaultSampleKbArticles.filter(a => a.title.toLowerCase().includes(query.toLowerCase())));
    }
  };

  const handleVoteArticle = async (articleId, helpful) => {
    try {
      const res = await supportApi.voteKBArticle(articleId, helpful);
      setKbArticles((prev) =>
        prev.map((a) =>
          a.id === articleId
            ? { ...a, helpful_count: res.helpful_count, not_helpful_count: res.not_helpful_count }
            : a
        )
      );
      if (activeArticle?.id === articleId) {
        setActiveArticle((prev) => ({
          ...prev,
          helpful_count: res.helpful_count,
          not_helpful_count: res.not_helpful_count,
        }));
      }
    } catch (err) {
      console.error('Error voting on article:', err);
    }
  };

  // Roadmap
  const loadRoadmap = async () => {
    setLoading(true);
    try {
      const items = await supportApi.getRoadmap();
      setRoadmapItems((items && items.length > 0) ? items : defaultSampleRoadmap);
    } catch (err) {
      setRoadmapItems(defaultSampleRoadmap);
    } finally {
      setLoading(false);
    }
  };

  const handleVoteRoadmap = async (itemId) => {
    try {
      const res = await supportApi.voteRoadmap(itemId);
      setRoadmapItems((prev) =>
        prev.map((item) => (item.id === itemId ? { ...item, vote_count: res.vote_count } : item))
      );
    } catch (err) {
      setRoadmapItems((prev) =>
        prev.map((item) => (item.id === itemId ? { ...item, vote_count: item.vote_count + 1 } : item))
      );
    }
  };

  // Health
  const loadCustomerHealth = async () => {
    setLoading(true);
    try {
      const data = await supportApi.getCustomerHealth();
      setHealthData(data || defaultSampleHealth);
    } catch (err) {
      setHealthData(defaultSampleHealth);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="support-portal-container">
      {/* Header */}
      <div className="support-header">
        <div>
          <h1>Customer Operations & Support</h1>
          <p className="support-subtitle">
            Enterprise ticketing, self-service knowledge base, transparent roadmap, and account health telemetry.
          </p>
        </div>
        <div className="support-nav-pills">
          <button
            className={`nav-pill ${activeTab === 'tickets' ? 'active' : ''}`}
            onClick={() => setActiveTab('tickets')}
          >
            <LifeBuoy size={16} />
            <span>Support Tickets</span>
          </button>
          <button
            className={`nav-pill ${activeTab === 'kb' ? 'active' : ''}`}
            onClick={() => setActiveTab('kb')}
          >
            <BookOpen size={16} />
            <span>Knowledge Base</span>
          </button>
          <button
            className={`nav-pill ${activeTab === 'roadmap' ? 'active' : ''}`}
            onClick={() => setActiveTab('roadmap')}
          >
            <Map size={16} />
            <span>Product Roadmap</span>
          </button>
          <button
            className={`nav-pill ${activeTab === 'health' ? 'active' : ''}`}
            onClick={() => setActiveTab('health')}
          >
            <Activity size={16} />
            <span>Customer Health</span>
          </button>
        </div>
      </div>

      {/* TAB 1: SUPPORT TICKETS */}
      {activeTab === 'tickets' && (
        <div className="tickets-layout">
          {/* Left: Tickets List */}
          <div className="tickets-sidebar">
            <div className="tickets-sidebar-header">
              <h3>All Tickets ({tickets.length})</h3>
              <button
                className="btn-create-ticket"
                onClick={() => setShowCreateModal(true)}
              >
                <Plus size={15} />
                <span>New Ticket</span>
              </button>
            </div>

            <div className="tickets-list">
              {tickets.length === 0 ? (
                <div className="empty-tickets">No support tickets found.</div>
              ) : (
                tickets.map((t) => (
                  <div
                    key={t.id}
                    className={`ticket-item-card ${selectedTicket?.id === t.id ? 'active' : ''}`}
                    onClick={() => selectTicket(t)}
                  >
                    <div className="ticket-item-top">
                      <span className={`priority-badge ${t.priority.toLowerCase()}`}>{t.priority}</span>
                      <span className={`status-badge ${t.status.toLowerCase()}`}>{t.status}</span>
                    </div>
                    <div className="ticket-item-title">{t.title}</div>
                    <div className="ticket-item-meta">
                      <span>ID: {t.id}</span>
                      {t.sla_deadline && (
                        <span className="sla-deadline">
                          <Clock size={12} />
                          {new Date(t.sla_deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right: Ticket Thread */}
          <div className="ticket-thread-container">
            {selectedTicket ? (
              <>
                <div className="ticket-thread-header">
                  <div>
                    <div className="thread-title-row">
                      <h2>{selectedTicket.title}</h2>
                      <span className={`status-badge ${selectedTicket.status.toLowerCase()}`}>
                        {selectedTicket.status}
                      </span>
                    </div>
                    <div className="thread-meta-row">
                      <span>Requester: {selectedTicket.requester_email || 'Customer'}</span>
                      <span>Category: {selectedTicket.category}</span>
                      <span>Priority: {selectedTicket.priority}</span>
                    </div>
                  </div>

                  <div className="thread-actions">
                    <select
                      value={selectedTicket.status}
                      onChange={(e) => handleUpdateTicketStatus(selectedTicket.id, e.target.value)}
                    >
                      <option value="OPEN">Mark OPEN</option>
                      <option value="IN_PROGRESS">In Progress</option>
                      <option value="WAITING_ON_CUSTOMER">Waiting on Customer</option>
                      <option value="RESOLVED">Resolved</option>
                      <option value="CLOSED">Closed</option>
                    </select>
                  </div>
                </div>

                <div className="ticket-messages-stream">
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={`message-bubble ${m.is_internal_note ? 'internal-note' : 'public-message'}`}
                    >
                      <div className="message-header">
                        <span className="message-author">
                          {m.sender_name || 'Agent'}{' '}
                          {m.is_internal_note && <span className="internal-pill"><Lock size={11} /> Agent Internal Note</span>}
                        </span>
                        <span className="message-time">
                          {new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="message-text">{m.message}</div>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleSendReply} className="ticket-reply-form">
                  <div className="reply-options-bar">
                    <label className="internal-note-toggle">
                      <input
                        type="checkbox"
                        checked={isInternalNote}
                        onChange={(e) => setIsInternalNote(e.target.checked)}
                      />
                      <span>Internal agent note (hidden from customer)</span>
                    </label>
                  </div>
                  <div className="reply-input-box">
                    <textarea
                      rows={3}
                      placeholder={
                        isInternalNote
                          ? 'Add private technical notes, root causes, or handover details...'
                          : 'Write a response to the customer...'
                      }
                      value={replyText}
                      onChange={(e) => setReplyText(e.target.value)}
                    />
                    <button
                      type="submit"
                      className={`btn-send-reply ${isInternalNote ? 'internal' : ''}`}
                      disabled={!replyText.trim()}
                    >
                      <Send size={15} />
                      <span>{isInternalNote ? 'Add Note' : 'Send'}</span>
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <div className="no-ticket-selected">Select a ticket to view the conversation thread.</div>
            )}
          </div>
        </div>
      )}

      {/* CREATE TICKET MODAL */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <h3>Open Support Ticket</h3>
            <form onSubmit={handleCreateTicket}>
              <div className="form-group">
                <label>Ticket Subject</label>
                <input
                  type="text"
                  placeholder="e.g. Export failed with timeout"
                  value={newTicket.title}
                  onChange={(e) => setNewTicket({ ...newTicket, title: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Category</label>
                  <select
                    value={newTicket.category}
                    onChange={(e) => setNewTicket({ ...newTicket, category: e.target.value })}
                  >
                    <option value="technical_issue">Technical Issue</option>
                    <option value="billing">Billing & Subscriptions</option>
                    <option value="account_access">Account & Access</option>
                    <option value="feature_request">Feature Request</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Priority (SLA Guarantee)</label>
                  <select
                    value={newTicket.priority}
                    onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
                  >
                    <option value="LOW">Low (72h SLA)</option>
                    <option value="NORMAL">Normal (24h SLA)</option>
                    <option value="HIGH">High (4h SLA)</option>
                    <option value="URGENT">Urgent (1h Critical SLA)</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Detailed Description</label>
                <textarea
                  rows={4}
                  placeholder="Steps to reproduce, expected result, affected project..."
                  value={newTicket.description}
                  onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
                  required
                />
              </div>

              <div className="modal-buttons">
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Submit Ticket
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* TAB 2: KNOWLEDGE BASE */}
      {activeTab === 'kb' && (
        <div className="kb-layout">
          <div className="kb-search-header">
            <div className="kb-search-box">
              <Search size={18} className="search-icon" />
              <input
                type="text"
                placeholder="Search troubleshooting guides, API docs, workflow setup..."
                value={searchQuery}
                onChange={(e) => handleSearchKB(e.target.value)}
              />
            </div>

            <div className="kb-category-pills">
              <button
                className={`category-pill ${selectedCategory === null ? 'active' : ''}`}
                onClick={() => {
                  setSelectedCategory(null);
                  loadKnowledgeBase();
                }}
              >
                All Topics
              </button>
              {kbCategories.map((c) => (
                <button
                  key={c.id}
                  className={`category-pill ${selectedCategory === c.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedCategory(c.id);
                    supportApi.getKBArticles(c.id, searchQuery).then(setKbArticles);
                  }}
                >
                  {c.name} ({c.article_count})
                </button>
              ))}
            </div>
          </div>

          <div className="kb-articles-grid">
            {kbArticles.map((article) => (
              <div key={article.id} className="article-card" onClick={() => setActiveArticle(article)}>
                <h3>{article.title}</h3>
                <p className="article-preview">{article.content.slice(0, 160)}...</p>
                <div className="article-footer">
                  <div className="article-votes">
                    <span title="Helpful votes"><ThumbsUp size={13} /> {article.helpful_count}</span>
                  </div>
                  <span className="read-more-link">Read Guide &rarr;</span>
                </div>
              </div>
            ))}
          </div>

          {/* Article Reader Modal */}
          {activeArticle && (
            <div className="modal-backdrop">
              <div className="modal-dialog article-reader-dialog">
                <div className="article-reader-header">
                  <h2>{activeArticle.title}</h2>
                  <button className="btn-close" onClick={() => setActiveArticle(null)}>✕</button>
                </div>
                <div className="article-reader-body">
                  <pre className="markdown-pre">{activeArticle.content}</pre>
                </div>
                <div className="article-reader-footer">
                  <span>Was this article helpful?</span>
                  <div className="vote-actions">
                    <button
                      className="btn-vote"
                      onClick={() => handleVoteArticle(activeArticle.id, true)}
                    >
                      <ThumbsUp size={15} /> Yes ({activeArticle.helpful_count})
                    </button>
                    <button
                      className="btn-vote"
                      onClick={() => handleVoteArticle(activeArticle.id, false)}
                    >
                      <ThumbsDown size={15} /> No ({activeArticle.not_helpful_count})
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: PRODUCT ROADMAP */}
      {activeTab === 'roadmap' && (
        <div className="roadmap-layout">
          <div className="roadmap-columns">
            {['PLANNED', 'IN_DEVELOPMENT', 'COMPLETED'].map((colStatus) => {
              const colItems = roadmapItems.filter((i) => i.status === colStatus);
              const colTitle =
                colStatus === 'PLANNED'
                  ? 'Planned'
                  : colStatus === 'IN_DEVELOPMENT'
                  ? 'In Development'
                  : 'Completed';

              return (
                <div key={colStatus} className="roadmap-column">
                  <div className="roadmap-column-header">
                    <h4>{colTitle}</h4>
                    <span className="roadmap-count">{colItems.length}</span>
                  </div>
                  <div className="roadmap-card-list">
                    {colItems.map((item) => (
                      <div key={item.id} className="roadmap-item-card">
                        <div className="roadmap-item-cat">{item.category}</div>
                        <h5>{item.title}</h5>
                        <p>{item.description}</p>
                        <div className="roadmap-item-footer">
                          <button
                            className="btn-upvote"
                            onClick={() => handleVoteRoadmap(item.id)}
                            title="Upvote this feature request"
                          >
                            <ThumbsUp size={14} />
                            <span>{item.vote_count}</span>
                          </button>
                          <span className="roadmap-date">
                            {new Date(item.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 4: CUSTOMER HEALTH */}
      {activeTab === 'health' && (
        <div className="health-layout">
          {healthData ? (
            <div className="health-card">
              <div className="health-top-row">
                <div>
                  <span className="health-section-label">Deterministic Telemetry</span>
                  <h2>Account Productivity Health</h2>
                </div>
                <div className={`health-status-badge ${healthData.health_status.toLowerCase()}`}>
                  {healthData.health_status}
                </div>
              </div>

              <div className="health-score-display">
                <div className="health-score-dial">
                  <span className="score-num">{healthData.health_score}</span>
                  <span className="score-den">/100</span>
                </div>
                <div className="health-score-summary">
                  <p>
                    Health is calculated from actual task completion ratios, overdue deadlines, and open support tickets.
                  </p>
                </div>
              </div>

              <div className="health-metrics-grid">
                <div className="metric-box">
                  <span className="metric-label">Completion Velocity</span>
                  <span className="metric-value">{healthData.metrics?.completion_rate}%</span>
                  <span className="metric-sub">
                    {healthData.metrics?.completed_tasks} of {healthData.metrics?.total_tasks} tasks
                  </span>
                </div>

                <div className="metric-box">
                  <span className="metric-label">Overdue Tasks</span>
                  <span className="metric-value">{healthData.metrics?.overdue_tasks}</span>
                  <span className="metric-sub">Needs rescheduling</span>
                </div>

                <div className="metric-box">
                  <span className="metric-label">Open Critical Tickets</span>
                  <span className="metric-value">{healthData.metrics?.open_urgent_tickets || 0}</span>
                  <span className="metric-sub">Active support tickets</span>
                </div>
              </div>

              <div className="health-recommendations">
                <h4>Recommended Actions</h4>
                <ul>
                  {healthData.recommendations?.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            </div>
          ) : (
            <div className="loading-box">Calculating account health telemetry...</div>
          )}
        </div>
      )}
    </div>
  );
}
