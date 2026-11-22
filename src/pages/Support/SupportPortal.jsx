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

export default function SupportPortal() {
  const [activeTab, setActiveTab] = useState('tickets'); // 'tickets' | 'kb' | 'roadmap' | 'health'

  // Tickets state
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [messages, setMessages] = useState([]);
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
  const [kbCategories, setKbCategories] = useState([]);
  const [kbArticles, setKbArticles] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeArticle, setActiveArticle] = useState(null);

  // Roadmap state
  const [roadmapItems, setRoadmapItems] = useState([]);

  // Health state
  const [healthData, setHealthData] = useState(null);

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
      setTickets(data || []);
      if (data && data.length > 0 && !selectedTicket) {
        selectTicket(data[0]);
      }
    } catch (err) {
      console.error('Error loading tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  const selectTicket = async (ticket) => {
    setSelectedTicket(ticket);
    try {
      const msgs = await supportApi.getTicketMessages(ticket.id);
      setMessages(msgs || []);
    } catch (err) {
      console.error('Error loading ticket messages:', err);
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
      console.error('Error replying to ticket:', err);
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
      console.error('Error creating ticket:', err);
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
      console.error('Error updating status:', err);
    }
  };

  // Knowledge Base
  const loadKnowledgeBase = async () => {
    setLoading(true);
    try {
      const [cats, arts] = await Promise.all([
        supportApi.getKBCategories(),
        supportApi.getKBArticles(selectedCategory, searchQuery),
      ]);
      setKbCategories(cats || []);
      setKbArticles(arts || []);
    } catch (err) {
      console.error('Error loading KB:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchKB = async (query) => {
    setSearchQuery(query);
    try {
      const arts = await supportApi.getKBArticles(selectedCategory, query);
      setKbArticles(arts || []);
    } catch (err) {
      console.error('Error searching articles:', err);
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
      setRoadmapItems(items || []);
    } catch (err) {
      console.error('Error loading roadmap:', err);
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
      console.error('Error voting on roadmap:', err);
    }
  };

  // Health
  const loadCustomerHealth = async () => {
    setLoading(true);
    try {
      const data = await supportApi.getCustomerHealth();
      setHealthData(data);
    } catch (err) {
      console.error('Error loading health score:', err);
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
