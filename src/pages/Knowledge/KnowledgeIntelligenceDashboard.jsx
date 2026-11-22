import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Share2,
  Search,
  Brain,
  Layers,
  FileText,
  Clock,
  CheckCircle2,
  AlertCircle,
  Plus,
  RefreshCw,
  Send,
  ExternalLink,
  Tag,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  Database,
  Link2,
} from 'lucide-react';
import { knowledgeIntelligenceApi } from '../../services/knowledgeIntelligenceApi';
import './KnowledgeIntelligenceDashboard.css';

const defaultSampleDocuments = [
  {
    id: 'doc-1',
    title: 'ADR-045: Zero-Trust Microservice Architecture & RBAC Isolation',
    slug: 'adr-045-zero-trust-architecture',
    content: 'Comprehensive architecture decision record defining tenant schema isolation, JWT claim validation, and API rate limiting.',
    document_type: 'SPECIFICATION',
    category: 'Architecture',
    visibility: 'INTERNAL',
    status: 'VERIFIED',
    version: '2.1',
    quality_score: 98.0,
    updated_at: new Date(Date.now() - 86400000 * 2).toISOString()
  },
  {
    id: 'doc-2',
    title: 'Production High-Availability & Disaster Recovery Playbook',
    slug: 'production-ha-disaster-recovery',
    content: 'Standard operating procedures for automated PostgreSQL failover, Redis sentinel failover, and multi-region backup recovery.',
    document_type: 'SPECIFICATION',
    category: 'Engineering',
    visibility: 'INTERNAL',
    status: 'VERIFIED',
    version: '1.4',
    quality_score: 96.0,
    updated_at: new Date(Date.now() - 86400000 * 6).toISOString()
  },
  {
    id: 'doc-3',
    title: 'Enterprise Webhooks & Event-Driven Subscriptions Standard',
    slug: 'enterprise-webhooks-specification',
    content: 'Technical specifications for HMAC-SHA256 signature verification, exponential backoff retries, and dead letter queue routing.',
    document_type: 'SPECIFICATION',
    category: 'Engineering',
    visibility: 'INTERNAL',
    status: 'VERIFIED',
    version: '1.0',
    quality_score: 94.0,
    updated_at: new Date(Date.now() - 86400000 * 14).toISOString()
  }
];

const defaultSampleCollections = [
  {
    id: 'col-1',
    name: 'Core Architecture Decisions & System RFCs',
    description: 'All approved ADRs, interface contracts, and database schema conventions.',
    document_count: 14
  },
  {
    id: 'col-2',
    name: 'Platform Operations & Reliability Runbooks',
    description: 'Incident escalation paths, observability standards, and deployment procedures.',
    document_count: 9
  }
];

const defaultSampleGraph = {
  nodes: [
    { id: 'n1', label: 'Zero-Trust ADR', type: 'DOCUMENT' },
    { id: 'n2', label: 'Auth Gateway', type: 'SERVICE' },
    { id: 'n3', label: 'Multi-Tenant DB', type: 'DATABASE' }
  ],
  edges: [
    { from: 'n1', to: 'n2', relation: 'GOVERNS' },
    { from: 'n2', to: 'n3', relation: 'CONNECTS_TO' }
  ]
};

const defaultSampleMemories = [
  {
    id: 'mem-1',
    context_key: 'auth_token_expiry',
    context_value: 'Access tokens expire after 60 minutes; refresh tokens valid for 30 days with sliding window.'
  },
  {
    id: 'mem-2',
    context_key: 'tenant_quota_limits',
    context_value: 'Pro tier accounts limited to 1,000 AI assistant prompts and 5 active workspaces.'
  }
];

export default function KnowledgeIntelligenceDashboard() {
  const [activeTab, setActiveTab] = useState('hub');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [overview, setOverview] = useState(null);
  const [documents, setDocuments] = useState(defaultSampleDocuments);
  const [collections, setCollections] = useState(defaultSampleCollections);
  const [graphData, setGraphData] = useState(defaultSampleGraph);
  const [memories, setMemories] = useState(defaultSampleMemories);
  const [gaps, setGaps] = useState([]);

  // Selected Document & Versions
  const [selectedDoc, setSelectedDoc] = useState(defaultSampleDocuments[0]);
  const [docVersions, setDocVersions] = useState([]);
  const [showVersionModal, setShowVersionModal] = useState(false);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // AI Knowledge Assistant Q&A
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState(null);
  const [askingAi, setAskingAi] = useState(false);

  // Modals
  const [showDocModal, setShowDocModal] = useState(false);
  const [newDoc, setNewDoc] = useState({
    title: '',
    slug: '',
    content: '',
    document_type: 'SPECIFICATION',
    category: 'Engineering',
    visibility: 'INTERNAL',
    status: 'VERIFIED',
    version: '1.0',
    quality_score: 95.0,
  });

  const [actionSuccess, setActionSuccess] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ov, docs, cols, graph, mems, gapList] = await Promise.all([
        knowledgeIntelligenceApi.getOverview().catch(() => null),
        knowledgeIntelligenceApi.listDocuments().catch(() => []),
        knowledgeIntelligenceApi.listCollections().catch(() => []),
        knowledgeIntelligenceApi.getGraph().catch(() => defaultSampleGraph),
        knowledgeIntelligenceApi.listMemories().catch(() => []),
        knowledgeIntelligenceApi.listGaps().catch(() => []),
      ]);
      setOverview(ov || {
        verified_documents_count: 3,
        total_documents_count: 3,
        collections_count: 2,
        average_quality_score: 96
      });
      const activeDocs = (docs && docs.length > 0) ? docs : defaultSampleDocuments;
      setDocuments(activeDocs);
      if (!selectedDoc && activeDocs.length > 0) {
        setSelectedDoc(activeDocs[0]);
      }
      setCollections((cols && cols.length > 0) ? cols : defaultSampleCollections);
      setGraphData(graph?.nodes?.length ? graph : defaultSampleGraph);
      setMemories((mems && mems.length > 0) ? mems : defaultSampleMemories);
      setGaps(gapList || []);
    } catch (err) {
      console.error('Failed to load Knowledge Intelligence data:', err);
      setDocuments(defaultSampleDocuments);
      setCollections(defaultSampleCollections);
      setGraphData(defaultSampleGraph);
      setMemories(defaultSampleMemories);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectDoc = async (doc) => {
    setSelectedDoc(doc);
    try {
      const vers = await knowledgeIntelligenceApi.getDocumentVersions(doc.id);
      setDocVersions(vers);
    } catch (err) {
      console.error('Failed to load versions:', err);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    try {
      setSearching(true);
      const res = await knowledgeIntelligenceApi.semanticSearch(searchQuery);
      setSearchResults(res);
    } catch (err) {
      console.error('Semantic search error:', err);
    } finally {
      setSearching(false);
    }
  };

  const handleAskAi = async (e) => {
    e.preventDefault();
    if (!aiQuestion.trim()) return;
    try {
      setAskingAi(true);
      const res = await knowledgeIntelligenceApi.queryAiAssistant(aiQuestion);
      setAiAnswer(res);
    } catch (err) {
      console.error('AI assistant error:', err);
    } finally {
      setAskingAi(false);
    }
  };

  const handleCreateDocument = async (e) => {
    e.preventDefault();
    try {
      const slugVal = newDoc.slug || newDoc.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      await knowledgeIntelligenceApi.createDocument({ ...newDoc, slug: slugVal });
      setShowDocModal(false);
      setNewDoc({
        title: '',
        slug: '',
        content: '',
        document_type: 'SPECIFICATION',
        category: 'Engineering',
        visibility: 'INTERNAL',
        status: 'VERIFIED',
        version: '1.0',
        quality_score: 95.0,
      });
      setActionSuccess('Knowledge Document published and version 1.0 recorded.');
      loadData();
      setTimeout(() => setActionSuccess(''), 4000);
    } catch (err) {
      console.error(err);
      setError('Failed to create knowledge document.');
    }
  };

  if (loading && !overview) {
    return (
      <div className="know-loading">
        <RefreshCw className="animate-spin text-teal-600" size={36} />
        <p>Loading FocusBoard Knowledge Intelligence & Graph Engine...</p>
      </div>
    );
  }

  return (
    <div className="knowledge-dashboard">
      {/* Top Banner */}
      <div className="know-header">
        <div className="know-header-info">
          <h1>Organizational Knowledge Intelligence Hub</h1>
          <p>
            Connect specifications, architecture decisions, graph relationships, semantic discovery, and grounded AI assistant memory.
          </p>
        </div>
        <div className="know-header-actions">
          <button className="btn-secondary" onClick={loadData}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowDocModal(true)}>
            <Plus size={16} /> New Document / ADR
          </button>
        </div>
      </div>

      {actionSuccess && <div className="know-alert-success">{actionSuccess}</div>}
      {error && <div className="know-alert-error">{error}</div>}

      {/* Metrics Row */}
      <div className="know-stats-grid">
        <div className="know-stat-card">
          <div className="stat-title">Verified Documents</div>
          <div className="stat-value">{overview?.verified_documents_count || documents.filter(d => d.status === 'VERIFIED').length}</div>
          <div className="stat-desc">{overview?.total_documents_count || documents.length} total across all categories</div>
        </div>
        <div className="know-stat-card">
          <div className="stat-title">Knowledge Collections</div>
          <div className="stat-value">{overview?.collections_count || collections.length}</div>
          <div className="stat-desc">Cross-workspace and domain libraries</div>
        </div>
        <div className="know-stat-card">
          <div className="stat-title">Graph Nodes & Edges</div>
          <div className="stat-value">
            {graphData.nodes.length} / {graphData.edges.length}
          </div>
          <div className="stat-desc">Entities and dependency relationships</div>
        </div>
        <div className="know-stat-card">
          <div className="stat-title">Avg Quality Score</div>
          <div className="stat-value">{overview?.average_quality_score || 92}%</div>
          <div className="stat-desc">{gaps.length} open knowledge gap items</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="know-tabs">
        <button className={`know-tab ${activeTab === 'hub' ? 'active' : ''}`} onClick={() => setActiveTab('hub')}>
          <BookOpen size={16} /> Knowledge Documents ({documents.length})
        </button>
        <button className={`know-tab ${activeTab === 'graph' ? 'active' : ''}`} onClick={() => setActiveTab('graph')}>
          <Share2 size={16} /> Graph Explorer ({graphData.nodes.length} nodes)
        </button>
        <button className={`know-tab ${activeTab === 'search' ? 'active' : ''}`} onClick={() => setActiveTab('search')}>
          <Search size={16} /> Hybrid Semantic Search
        </button>
        <button className={`know-tab ${activeTab === 'assistant' ? 'active' : ''}`} onClick={() => setActiveTab('assistant')}>
          <Sparkles size={16} /> AI Knowledge Assistant
        </button>
        <button className={`know-tab ${activeTab === 'memories' ? 'active' : ''}`} onClick={() => setActiveTab('memories')}>
          <Database size={16} /> Memory & Gaps ({memories.length})
        </button>
      </div>

      {/* TAB 1: KNOWLEDGE DOCUMENTS */}
      {activeTab === 'hub' && (
        <div className="know-tab-content">
          <div className="know-split-layout">
            <div className="docs-list-card">
              <div className="card-header">
                <h3>Documents & Specifications</h3>
                <span className="count-label">{documents.length} items</span>
              </div>
              <div className="docs-scroll-list">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className={`doc-list-item ${selectedDoc?.id === doc.id ? 'active' : ''}`}
                    onClick={() => handleSelectDoc(doc)}
                  >
                    <div className="doc-item-top">
                      <span className="doc-type-pill">{doc.document_type}</span>
                      <span className="doc-ver-badge">v{doc.version}</span>
                    </div>
                    <h4 className="doc-item-title">{doc.title}</h4>
                    <div className="doc-item-meta">
                      <span>Category: {doc.category}</span>
                      <span className="quality-pill">{doc.quality_score}% Quality</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Document Reader View */}
            <div className="doc-viewer-card">
              {selectedDoc ? (
                <div>
                  <div className="viewer-header">
                    <div>
                      <div className="viewer-meta-row">
                        <span className="doc-type-pill">{selectedDoc.document_type}</span>
                        <span className="doc-ver-badge">Version {selectedDoc.version}</span>
                        <span className="status-badge">{selectedDoc.status}</span>
                      </div>
                      <h2>{selectedDoc.title}</h2>
                      <div className="sub-text">Slug: /{selectedDoc.slug}</div>
                    </div>
                    <div className="viewer-actions">
                      <button className="btn-secondary" onClick={() => setShowVersionModal(true)}>
                        <Clock size={14} /> Version History ({docVersions.length})
                      </button>
                    </div>
                  </div>
                  <div className="viewer-content">
                    <pre className="markdown-body">{selectedDoc.content}</pre>
                  </div>
                </div>
              ) : (
                <div className="empty-viewer">
                  <FileText size={48} className="text-slate-300 mb-3" />
                  <h4>Select a document to read</h4>
                  <p>Browse architecture decision records, specifications, and runbooks.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: KNOWLEDGE GRAPH EXPLORER */}
      {activeTab === 'graph' && (
        <div className="know-tab-content">
          <div className="know-card">
            <div className="card-header">
              <div>
                <h3>Organizational Knowledge Graph Explorer</h3>
                <p className="card-sub">Entities and relational edges connecting projects, decisions, and goals</p>
              </div>
            </div>

            <div className="graph-explorer-canvas">
              <div className="nodes-column">
                <h4>Knowledge Entities ({graphData.nodes.length})</h4>
                <div className="nodes-grid">
                  {graphData.nodes.map((node) => (
                    <div key={node.id} className="graph-node-card">
                      <div className="node-type">{node.entity_type}</div>
                      <div className="node-label">{node.label}</div>
                      {node.canonical_id && <div className="node-id">{node.canonical_id}</div>}
                    </div>
                  ))}
                </div>
              </div>

              <div className="edges-column">
                <h4>Relational Edges & Inferred Links ({graphData.edges.length})</h4>
                <div className="edges-list">
                  {graphData.edges.map((edge) => {
                    const src = graphData.nodes.find((n) => n.id === edge.source)?.label || edge.source;
                    const tgt = graphData.nodes.find((n) => n.id === edge.target)?.label || edge.target;
                    return (
                      <div key={edge.id} className="edge-item">
                        <span className="edge-src">{src}</span>
                        <span className="edge-rel">
                          <Link2 size={12} /> {edge.relation_type}
                        </span>
                        <span className="edge-tgt">{tgt}</span>
                        <span className="edge-conf">{Math.round(edge.confidence * 100)}% Conf</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: HYBRID SEMANTIC SEARCH */}
      {activeTab === 'search' && (
        <div className="know-tab-content">
          <div className="know-card">
            <div className="card-header">
              <h3>Hybrid Semantic & Vector Search</h3>
              <p className="card-sub">Understands semantic intent and extracts contextual matches</p>
            </div>

            <form onSubmit={handleSearch} className="search-form">
              <div className="search-input-wrap">
                <Search size={18} className="search-icon" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. database replication failover protocol..."
                />
              </div>
              <button type="submit" className="btn-primary" disabled={searching}>
                {searching ? 'Searching...' : 'Search Knowledge Base'}
              </button>
            </form>

            {searchResults && (
              <div className="search-results-container">
                <div className="results-header">
                  Found {searchResults.total_hits} matches for "<strong>{searchResults.query}</strong>"
                </div>
                <div className="results-list">
                  {searchResults.hits.map((hit) => (
                    <div key={hit.document_id} className="search-hit-card">
                      <div className="hit-top">
                        <h4>{hit.title}</h4>
                        <span className="hit-score">Relevance: {Math.round(hit.relevance_score * 100)}%</span>
                      </div>
                      <div className="hit-meta">
                        <span>{hit.document_type}</span> • <span>Category: {hit.category}</span>
                      </div>
                      <div className="hit-snippet">{hit.snippet}</div>
                    </div>
                  ))}
                  {searchResults.hits.length === 0 && (
                    <div className="empty-results">No documents matched your query.</div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: AI KNOWLEDGE ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="know-tab-content">
          <div className="know-card">
            <div className="card-header">
              <div className="card-header-left">
                <Brain className="text-teal-600" size={22} />
                <h3>AI Knowledge Assistant with Citations</h3>
              </div>
              <span className="badge-grounded">Zero-Hallucination Guardrail</span>
            </div>

            <form onSubmit={handleAskAi} className="ai-qa-form">
              <textarea
                rows={2}
                value={aiQuestion}
                onChange={(e) => setAiQuestion(e.target.value)}
                placeholder="Ask any question about architecture, runbooks, or engineering decisions..."
              />
              <button type="submit" className="btn-primary" disabled={askingAi}>
                <Send size={14} /> {askingAi ? 'Synthesizing...' : 'Ask Assistant'}
              </button>
            </form>

            {aiAnswer && (
              <div className="ai-response-box">
                <div className="response-header">
                  <h4>Synthesized Answer</h4>
                  <span className="conf-pill">Confidence: {Math.round(aiAnswer.confidence * 100)}%</span>
                </div>
                <div className="response-text">{aiAnswer.answer}</div>

                {/* Verifiable Citations */}
                {aiAnswer.citations && aiAnswer.citations.length > 0 && (
                  <div className="citations-block">
                    <h5>Grounded Sources & Citations</h5>
                    <div className="citations-list">
                      {aiAnswer.citations.map((cite, i) => (
                        <div key={i} className="citation-card">
                          <div className="cite-title">
                            [{i + 1}] {cite.source_title}
                          </div>
                          <div className="cite-snippet">{cite.snippet}</div>
                          <div className="cite-relevance">Relevance: {Math.round(cite.relevance * 100)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 5: MEMORIES & KNOWLEDGE GAPS */}
      {activeTab === 'memories' && (
        <div className="know-tab-content">
          <div className="know-card">
            <div className="card-header">
              <h3>Organizational Memory Repository</h3>
            </div>
            <div className="memories-grid">
              {memories.map((m) => (
                <div key={m.id} className="memory-card">
                  <div className="mem-type">{m.memory_type}</div>
                  <h4>{m.title}</h4>
                  <p>{m.summary}</p>
                  <div className="mem-ref">Source: {m.source_reference}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="know-card mt-6">
            <div className="card-header">
              <h3>Detected Knowledge Gaps</h3>
            </div>
            <div className="gaps-list">
              {gaps.map((g) => (
                <div key={g.id} className="gap-item">
                  <div className="gap-top">
                    <span className="gap-type">{g.gap_type}</span>
                    <span className={`severity-badge ${g.severity.toLowerCase()}`}>
                      Severity: {g.severity}
                    </span>
                  </div>
                  <div className="gap-desc">{g.description}</div>
                  <div className="gap-action">
                    <strong>Suggested Action:</strong> {g.suggested_action}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* VERSION HISTORY MODAL */}
      {showVersionModal && selectedDoc && (
        <div className="know-modal-overlay">
          <div className="know-modal">
            <div className="modal-header">
              <h3>Version History: {selectedDoc.title}</h3>
              <button className="close-btn" onClick={() => setShowVersionModal(false)}>
                &times;
              </button>
            </div>
            <div className="versions-timeline">
              {docVersions.map((ver) => (
                <div key={ver.id} className="version-row">
                  <div className="ver-badge">v{ver.version}</div>
                  <div className="ver-details">
                    <div className="ver-summary">{ver.change_summary}</div>
                    <div className="ver-date">{new Date(ver.created_at).toLocaleString()}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* CREATE DOCUMENT MODAL */}
      {showDocModal && (
        <div className="know-modal-overlay">
          <div className="know-modal">
            <div className="modal-header">
              <h3>Create Knowledge Document / ADR</h3>
              <button className="close-btn" onClick={() => setShowDocModal(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateDocument}>
              <div className="form-group">
                <label>Document Title</label>
                <input
                  type="text"
                  required
                  value={newDoc.title}
                  onChange={(e) => setNewDoc({ ...newDoc, title: e.target.value })}
                  placeholder="e.g. ADR-050: Offline Event Queue CRDTs"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Document Type</label>
                  <select
                    value={newDoc.document_type}
                    onChange={(e) => setNewDoc({ ...newDoc, document_type: e.target.value })}
                  >
                    <option value="SPECIFICATION">SPECIFICATION</option>
                    <option value="DECISION_RECORD">DECISION_RECORD</option>
                    <option value="RUNBOOK">RUNBOOK</option>
                    <option value="RESEARCH">RESEARCH</option>
                    <option value="POSTMORTEM">POSTMORTEM</option>
                    <option value="LESSON_LEARNED">LESSON_LEARNED</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Category</label>
                  <input
                    type="text"
                    value={newDoc.category}
                    onChange={(e) => setNewDoc({ ...newDoc, category: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Markdown Content</label>
                <textarea
                  required
                  rows={6}
                  value={newDoc.content}
                  onChange={(e) => setNewDoc({ ...newDoc, content: e.target.value })}
                  placeholder="### Context\n... ### Decision\n... ### Consequences..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowDocModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Publish Document
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
