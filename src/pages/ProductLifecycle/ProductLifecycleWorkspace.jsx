import React, { useState, useEffect } from 'react';
import {
  Compass,
  Lightbulb,
  MessageSquare,
  TrendingUp,
  Sliders,
  Map,
  FlaskConical,
  Rocket,
  Sparkles,
  RefreshCw,
  Plus,
  ArrowRight,
  GitMerge,
  CheckCircle2,
  Clock,
  DollarSign,
  Users,
  Search,
  Layers,
  Play,
  X,
  AlertCircle,
  Database,
} from 'lucide-react';
import { productLifecycleApi } from '../../services/productLifecycleApi';
import './ProductLifecycleWorkspace.css';

export default function ProductLifecycleWorkspace() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState('');

  // Data states
  const [overview, setOverview] = useState(null);
  const [discoveries, setDiscoveries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [featureRequests, setFeatureRequests] = useState([]);
  const [initiatives, setInitiatives] = useState([]);
  const [roadmapItems, setRoadmapItems] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [releases, setReleases] = useState([]);

  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Prioritization Calculator state
  const [prioInputs, setPrioInputs] = useState({ reach: 150, impact: 3.0, confidence: 0.8, effort: 2.0, ease: 3.0 });
  const [prioScores, setPrioScores] = useState({ rice_score: 180, ice_score: 7.2, weighted_score: 65 });

  // AI Assistant state
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);

  // Modals
  const [showDiscoveryModal, setShowDiscoveryModal] = useState(false);
  const [newDiscovery, setNewDiscovery] = useState({
    title: '',
    problem_statement: '',
    hypothesis: '',
    target_users: 'Product Managers, Engineering Leads',
    customer_segment: 'ENTERPRISE',
    business_impact: 'Increases platform retention and seat growth.',
    customer_impact: 'Reduces context-switching across external tooling.',
    status: 'VALIDATED',
  });

  const [showFeatureModal, setShowFeatureModal] = useState(false);
  const [newFeature, setNewFeature] = useState({
    title: '',
    description: '',
    customer_name: 'Acme Global',
    customer_segment: 'ENTERPRISE',
    source: 'CUSTOMER_FEEDBACK',
    request_count: 5,
    priority: 'HIGH',
    status: 'NEW',
    revenue_impact: 25000.0,
  });

  const [showMergeModal, setShowMergeModal] = useState(false);
  const [mergeSourceId, setMergeSourceId] = useState('');
  const [mergeTargetId, setMergeTargetId] = useState('');

  const [showRoadmapModal, setShowRoadmapModal] = useState(false);
  const [newRoadmapItem, setNewRoadmapItem] = useState({
    title: '',
    description: '',
    product_area: 'CORE_PLATFORM',
    quarter: 'Q2-2027',
    status: 'PLANNED',
    priority: 'HIGH',
    progress_pct: 20.0,
  });

  const [showExperimentModal, setShowExperimentModal] = useState(false);
  const [newExp, setNewExp] = useState({
    name: '',
    description: '',
    hypothesis: '',
    experiment_type: 'AB_TEST',
    primary_metric: 'conversion_rate',
    status: 'DRAFT',
    audience_segment: 'ALL_USERS',
    variants: [
      { variant_name: 'Control (Standard Flow)', variant_key: 'control_a', allocation_pct: 50.0 },
      { variant_name: 'Treatment (Optimized Flow)', variant_key: 'treatment_b', allocation_pct: 50.0 },
    ],
  });

  const showNotification = (msg) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(''), 4500);
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, discRes, ideaRes, freqRes, initRes, rmapRes, expRes, relRes] = await Promise.all([
        productLifecycleApi.getOverview().catch(() => null),
        productLifecycleApi.listDiscoveries().catch(() => null),
        productLifecycleApi.listIdeas().catch(() => null),
        productLifecycleApi.listFeatureRequests().catch(() => null),
        productLifecycleApi.listInitiatives().catch(() => null),
        productLifecycleApi.listRoadmapItems().catch(() => null),
        productLifecycleApi.listExperiments().catch(() => null),
        productLifecycleApi.listReleases().catch(() => null),
      ]);

      if (ovRes?.data) setOverview(ovRes.data);
      if (discRes?.data) setDiscoveries(discRes.data);
      if (ideaRes?.data) setIdeas(ideaRes.data);
      if (freqRes?.data) setFeatureRequests(freqRes.data);
      if (initRes?.data) setInitiatives(initRes.data);
      if (rmapRes?.data) setRoadmapItems(rmapRes.data);
      if (expRes?.data) setExperiments(expRes.data);
      if (relRes?.data) setReleases(relRes.data);
    } catch (err) {
      setError(err?.message || 'Failed to load product lifecycle intelligence');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSeedDemoData = async () => {
    setActionLoading(true);
    try {
      await productLifecycleApi.seedDemoData();
      showNotification('Initial demo product lifecycle records successfully loaded!');
      await loadData();
    } catch (err) {
      alert('Seeding failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateDiscovery = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await productLifecycleApi.createDiscovery(newDiscovery);
      setShowDiscoveryModal(false);
      setNewDiscovery({
        title: '',
        problem_statement: '',
        hypothesis: '',
        target_users: 'Product Managers, Engineering Leads',
        customer_segment: 'ENTERPRISE',
        business_impact: 'Increases platform retention and seat growth.',
        customer_impact: 'Reduces context-switching across external tooling.',
        status: 'VALIDATED',
      });
      showNotification('Product discovery recorded successfully!');
      loadData();
    } catch (err) {
      alert('Failed to create discovery: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateFeatureRequest = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await productLifecycleApi.createFeatureRequest(newFeature);
      setShowFeatureModal(false);
      setNewFeature({
        title: '',
        description: '',
        customer_name: 'Acme Global',
        customer_segment: 'ENTERPRISE',
        source: 'CUSTOMER_FEEDBACK',
        request_count: 5,
        priority: 'HIGH',
        status: 'NEW',
        revenue_impact: 25000.0,
      });
      showNotification('Customer feature request submitted to Demand Hub!');
      loadData();
    } catch (err) {
      alert('Failed to submit feature request: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleMergeFeatureRequests = async (e) => {
    e.preventDefault();
    if (!mergeSourceId || !mergeTargetId) return;
    setActionLoading(true);
    try {
      await productLifecycleApi.mergeFeatureRequests(mergeSourceId, mergeTargetId);
      setShowMergeModal(false);
      setMergeSourceId('');
      setMergeTargetId('');
      showNotification('Feature request merged successfully; demand aggregated.');
      loadData();
    } catch (err) {
      alert('Merge failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateRoadmapItem = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await productLifecycleApi.createRoadmapItem(newRoadmapItem);
      setShowRoadmapModal(false);
      setNewRoadmapItem({
        title: '',
        description: '',
        product_area: 'CORE_PLATFORM',
        quarter: 'Q2-2027',
        status: 'PLANNED',
        priority: 'HIGH',
        progress_pct: 20.0,
      });
      showNotification('Roadmap item scheduled successfully!');
      loadData();
    } catch (err) {
      alert('Failed to create roadmap item: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateExperiment = async (e) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await productLifecycleApi.createExperiment(newExp);
      setShowExperimentModal(false);
      showNotification('A/B experiment configured in DRAFT status!');
      loadData();
    } catch (err) {
      alert('Failed to create experiment: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulateAssignmentAndConversion = async (expId) => {
    setActionLoading(true);
    try {
      const variantRes = await productLifecycleApi.assignExperimentVariant(expId);
      const variantName = variantRes.data?.variant_name || 'Variant';
      await productLifecycleApi.trackExperimentEvent(expId, 'conversion_action', 1.0);
      showNotification(`Simulated impression & conversion recorded for ${variantName}!`);
      loadData();
    } catch (err) {
      alert('Simulation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading(false);
    }
  };

  const handleCalculatePrio = async () => {
    try {
      const res = await productLifecycleApi.calculatePrioritization(
        prioInputs.reach,
        prioInputs.impact,
        prioInputs.confidence,
        prioInputs.effort,
        prioInputs.ease
      );
      setPrioScores(res.data);
    } catch (err) {
      alert('Prioritization calculation failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAskAssistant = async (e) => {
    e?.preventDefault();
    if (!aiQuery.trim()) return;
    setAiLoading(true);
    setAiResponse(null);
    try {
      const res = await productLifecycleApi.askAssistant(aiQuery);
      setAiResponse(res.data);
    } catch (err) {
      alert('AI Assistant failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAiLoading(false);
    }
  };

  const filteredDiscoveries = discoveries.filter(d =>
    (!searchQuery || d.title.toLowerCase().includes(searchQuery.toLowerCase()) || d.problem_statement.toLowerCase().includes(searchQuery.toLowerCase())) &&
    (!statusFilter || d.status === statusFilter)
  );

  const filteredRequests = featureRequests.filter(r =>
    (!searchQuery || r.title.toLowerCase().includes(searchQuery.toLowerCase()) || r.customer_name.toLowerCase().includes(searchQuery.toLowerCase())) &&
    (!statusFilter || r.status === statusFilter)
  );

  return (
    <div className="plm-container">
      {/* Header */}
      <div className="plm-header">
        <div className="plm-title-area">
          <div className="plm-icon-badge">
            <Compass className="plm-icon" />
          </div>
          <div>
            <h1>Product Lifecycle Intelligence</h1>
            <p className="plm-subtitle">
              Problem discovery, customer demand analytics, RICE prioritization, roadmap sequencing & A/B testing.
            </p>
          </div>
        </div>
        <div className="plm-header-actions">
          <button className="plm-btn-outline" onClick={handleSeedDemoData} disabled={actionLoading}>
            <Database size={15} /> Demo Data
          </button>
          <button className="plm-btn-outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`plm-btn-icon ${loading ? 'spin' : ''}`} size={15} /> Sync
          </button>
        </div>
      </div>

      {successMsg && <div className="plm-banner-success"><CheckCircle2 size={16} /> {successMsg}</div>}
      {error && <div className="plm-banner-error"><AlertCircle size={16} /> {error}</div>}

      {/* Tabs */}
      <div className="plm-tabs">
        <button
          className={`plm-tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <TrendingUp className="tab-icon" /> Overview
        </button>
        <button
          className={`plm-tab ${activeTab === 'discoveries' ? 'active' : ''}`}
          onClick={() => setActiveTab('discoveries')}
        >
          <Lightbulb className="tab-icon" /> Discoveries & Ideas ({discoveries.length})
        </button>
        <button
          className={`plm-tab ${activeTab === 'requests' ? 'active' : ''}`}
          onClick={() => setActiveTab('requests')}
        >
          <MessageSquare className="tab-icon" /> Demand Hub ({featureRequests.length})
        </button>
        <button
          className={`plm-tab ${activeTab === 'prioritization' ? 'active' : ''}`}
          onClick={() => setActiveTab('prioritization')}
        >
          <Sliders className="tab-icon" /> Prioritization Engine
        </button>
        <button
          className={`plm-tab ${activeTab === 'roadmap' ? 'active' : ''}`}
          onClick={() => setActiveTab('roadmap')}
        >
          <Map className="tab-icon" /> Roadmap & Initiatives ({roadmapItems.length})
        </button>
        <button
          className={`plm-tab ${activeTab === 'experiments' ? 'active' : ''}`}
          onClick={() => setActiveTab('experiments')}
        >
          <FlaskConical className="tab-icon" /> A/B Testing ({experiments.length})
        </button>
        <button
          className={`plm-tab ${activeTab === 'releases' ? 'active' : ''}`}
          onClick={() => setActiveTab('releases')}
        >
          <Rocket className="tab-icon" /> Releases ({releases.length})
        </button>
        <button
          className={`plm-tab ${activeTab === 'assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('assistant')}
        >
          <Sparkles className="tab-icon" /> AI Product Assistant
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="plm-tab-content">
          <div className="plm-kpi-grid">
            <div className="plm-kpi-card">
              <span className="kpi-label">Customer Demand Count</span>
              <div className="kpi-value">{overview?.total_customer_demand_count ?? 0} reqs</div>
              <span className="kpi-subtext">Across {overview?.total_feature_requests ?? 0} prioritized features</span>
            </div>
            <div className="plm-kpi-card">
              <span className="kpi-label">Pipeline Revenue Impact</span>
              <div className="kpi-value highlight-value">
                ${(overview?.total_pipeline_revenue_impact ?? 0).toLocaleString()}
              </div>
              <span className="kpi-subtext">Associated with customer requested deals</span>
            </div>
            <div className="plm-kpi-card">
              <span className="kpi-label">Validated Discoveries</span>
              <div className="kpi-value">{overview?.total_discoveries ?? 0}</div>
              <span className="kpi-subtext">{overview?.total_ideas ?? 0} backlog concepts</span>
            </div>
            <div className="plm-kpi-card">
              <span className="kpi-label">Active A/B Experiments</span>
              <div className="kpi-value">{overview?.active_experiments_count ?? 0}</div>
              <span className="kpi-subtext">Deterministic variant tracking live</span>
            </div>
          </div>

          <div className="plm-section-card">
            <h3>Product Discovery to Release Pipeline</h3>
            <div className="funnel-steps-grid">
              <div className="funnel-step">
                <span className="funnel-badge">Step 1</span>
                <h4>Discovery</h4>
                <p>{overview?.total_discoveries ?? 0} Customer Problems</p>
              </div>
              <div className="funnel-step">
                <span className="funnel-badge">Step 2</span>
                <h4>Feature Requests</h4>
                <p>{overview?.total_feature_requests ?? 0} Demands Endorsed</p>
              </div>
              <div className="funnel-step">
                <span className="funnel-badge">Step 3</span>
                <h4>Initiatives</h4>
                <p>{overview?.total_initiatives ?? 0} Strategic Themes</p>
              </div>
              <div className="funnel-step">
                <span className="funnel-badge">Step 4</span>
                <h4>Roadmap</h4>
                <p>{overview?.total_roadmap_items ?? 0} Deliverables</p>
              </div>
              <div className="funnel-step">
                <span className="funnel-badge">Step 5</span>
                <h4>Release</h4>
                <p>{overview?.total_releases ?? 0} Shipped Versions</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: DISCOVERIES & IDEAS */}
      {activeTab === 'discoveries' && (
        <div className="plm-tab-content">
          <div className="plm-toolbar-row">
            <div className="plm-search-input-wrap">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search problem statements or target users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="plm-btn-primary" onClick={() => setShowDiscoveryModal(true)}>
              <Plus size={15} /> Log Discovery
            </button>
          </div>

          {filteredDiscoveries.length === 0 ? (
            <div className="plm-empty-card">
              <Lightbulb size={36} color="#6366f1" />
              <h4>No Product Discoveries Logged</h4>
              <p>Capture customer problem statements, hypotheses, and target segments.</p>
              <button className="plm-btn-primary" onClick={() => setShowDiscoveryModal(true)}>
                <Plus size={14} /> Add First Discovery
              </button>
            </div>
          ) : (
            <div className="discoveries-grid">
              {filteredDiscoveries.map((disc) => (
                <div key={disc.id} className="discovery-card">
                  <div className="discovery-header">
                    <span className={`badge-status ${disc.status.toLowerCase()}`}>{disc.status}</span>
                    <span className="segment-badge">{disc.customer_segment}</span>
                  </div>
                  <h4>{disc.title}</h4>
                  <p className="problem-text"><strong>Problem:</strong> {disc.problem_statement}</p>
                  <p className="hypothesis-text"><strong>Hypothesis:</strong> {disc.hypothesis}</p>
                  <div className="discovery-meta">
                    <span>Target Users: {disc.target_users}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: FEATURE REQUESTS & DEMAND HUB */}
      {activeTab === 'requests' && (
        <div className="plm-tab-content">
          <div className="plm-toolbar-row">
            <div className="plm-search-input-wrap">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search requests or customer accounts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              {featureRequests.length >= 2 && (
                <button className="plm-btn-outline" onClick={() => setShowMergeModal(true)}>
                  <GitMerge size={15} /> Merge Requests
                </button>
              )}
              <button className="plm-btn-primary" onClick={() => setShowFeatureModal(true)}>
                <Plus size={15} /> Capture Request
              </button>
            </div>
          </div>

          {filteredRequests.length === 0 ? (
            <div className="plm-empty-card">
              <MessageSquare size={36} color="#6366f1" />
              <h4>No Customer Feature Requests</h4>
              <p>Capture incoming customer demand, segment attribution, and pipeline value.</p>
              <button className="plm-btn-primary" onClick={() => setShowFeatureModal(true)}>
                <Plus size={14} /> Capture First Request
              </button>
            </div>
          ) : (
            <div className="plm-table-wrapper">
              <table className="plm-table">
                <thead>
                  <tr>
                    <th>Feature Request</th>
                    <th>Customer Endorsements</th>
                    <th>Customer Segment</th>
                    <th>Pipeline Value</th>
                    <th>Priority</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRequests.map((freq) => (
                    <tr key={freq.id}>
                      <td>
                        <strong>{freq.title}</strong>
                        <p className="row-desc">{freq.description}</p>
                        {freq.merged_into_id && (
                          <span className="merged-tag">Merged into {freq.merged_into_id}</span>
                        )}
                      </td>
                      <td>
                        <span className="demand-count-chip">{freq.request_count} customers</span>
                      </td>
                      <td>{freq.customer_segment}</td>
                      <td className="revenue-cell">
                        ${freq.revenue_impact > 0 ? freq.revenue_impact.toLocaleString() : '—'}
                      </td>
                      <td>
                        <span className={`badge-priority ${freq.priority.toLowerCase()}`}>{freq.priority}</span>
                      </td>
                      <td>
                        <span className={`badge-status ${freq.status.toLowerCase()}`}>{freq.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* TAB 4: PRIORITIZATION ENGINE */}
      {activeTab === 'prioritization' && (
        <div className="plm-tab-content">
          <div className="prioritization-container">
            <div className="calculator-box">
              <h3>Interactive RICE & ICE Scoring Calculator</h3>
              <p className="calc-desc">Calculate deterministic priority scores with non-zero effort bounds and explainable formulas.</p>
              <div className="calc-inputs-grid">
                <div className="calc-group">
                  <label>Reach (Users/month)</label>
                  <input
                    type="number"
                    min="1"
                    value={prioInputs.reach}
                    onChange={(e) => setPrioInputs({ ...prioInputs, reach: Math.max(1, Number(e.target.value)) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Impact (0.1 to 10.0)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.1"
                    max="10"
                    value={prioInputs.impact}
                    onChange={(e) => setPrioInputs({ ...prioInputs, impact: Math.max(0.1, Number(e.target.value)) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Confidence (0.01 to 1.0)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.01"
                    max="1"
                    value={prioInputs.confidence}
                    onChange={(e) => setPrioInputs({ ...prioInputs, confidence: Math.max(0.01, Number(e.target.value)) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Effort (Person-months &gt; 0)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.1"
                    value={prioInputs.effort}
                    onChange={(e) => setPrioInputs({ ...prioInputs, effort: Math.max(0.1, Number(e.target.value)) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Ease (0.1 to 10.0)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0.1"
                    max="10"
                    value={prioInputs.ease}
                    onChange={(e) => setPrioInputs({ ...prioInputs, ease: Math.max(0.1, Number(e.target.value)) })}
                  />
                </div>
              </div>

              <button className="plm-btn-primary" onClick={handleCalculatePrio}>
                Recalculate Scores
              </button>

              <div className="scores-result-bar">
                <div className="score-pill">
                  <span>RICE Score:</span>
                  <strong>{prioScores.rice_score}</strong>
                </div>
                <div className="score-pill">
                  <span>ICE Score:</span>
                  <strong>{prioScores.ice_score}</strong>
                </div>
                <div className="score-pill">
                  <span>Weighted Rank:</span>
                  <strong>{prioScores.weighted_score}/100</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: ROADMAP & INITIATIVES */}
      {activeTab === 'roadmap' && (
        <div className="plm-tab-content">
          <div className="plm-toolbar-row">
            <div className="plm-search-input-wrap">
              <Search size={16} />
              <input
                type="text"
                placeholder="Search roadmap deliverables..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <button className="plm-btn-primary" onClick={() => setShowRoadmapModal(true)}>
              <Plus size={15} /> Schedule Deliverable
            </button>
          </div>

          {roadmapItems.length === 0 ? (
            <div className="plm-empty-card">
              <Map size={36} color="#6366f1" />
              <h4>No Roadmap Items Scheduled</h4>
              <p>Add quarter-aligned deliverables and track progress toward release goals.</p>
              <button className="plm-btn-primary" onClick={() => setShowRoadmapModal(true)}>
                <Plus size={14} /> Add Roadmap Item
              </button>
            </div>
          ) : (
            <div className="roadmap-items-grid">
              {roadmapItems.map((item) => (
                <div key={item.id} className="roadmap-card">
                  <div className="roadmap-header">
                    <span className="quarter-badge">{item.quarter}</span>
                    <span className={`badge-status ${item.status.toLowerCase()}`}>{item.status}</span>
                  </div>
                  <h4>{item.title}</h4>
                  <p className="roadmap-desc">{item.description}</p>
                  <div className="progress-section">
                    <div className="progress-label">
                      <span>Progress</span>
                      <span>{item.progress_pct}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div className="progress-bar-fill" style={{ width: `${item.progress_pct}%` }}></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 6: A/B TESTING */}
      {activeTab === 'experiments' && (
        <div className="plm-tab-content">
          <div className="plm-toolbar-row">
            <div>
              <h3>Product A/B Testing & Telemetry</h3>
              <p className="plm-subtitle">Deterministic cohort assignment and real-time conversion telemetry.</p>
            </div>
            <button className="plm-btn-primary" onClick={() => setShowExperimentModal(true)}>
              <Plus size={15} /> New Experiment
            </button>
          </div>

          {experiments.length === 0 ? (
            <div className="plm-empty-card">
              <FlaskConical size={36} color="#6366f1" />
              <h4>No A/B Experiments Configured</h4>
              <p>Create treatment variants, configure 100% split allocation, and track conversion.</p>
              <button className="plm-btn-primary" onClick={() => setShowExperimentModal(true)}>
                <Plus size={14} /> Configure Experiment
              </button>
            </div>
          ) : (
            <div className="experiments-grid">
              {experiments.map((exp) => (
                <div key={exp.id} className="experiment-card">
                  <div className="exp-header">
                    <span className={`badge-status ${exp.status.toLowerCase()}`}>{exp.status}</span>
                    <span className="sample-chip">Sample: {exp.total_sample_size} users</span>
                  </div>
                  <h4>{exp.name}</h4>
                  <p className="exp-hypothesis"><strong>Hypothesis:</strong> {exp.hypothesis}</p>
                  <div className="variants-list">
                    {exp.variants?.map((v) => (
                      <div key={v.id} className="variant-item">
                        <div className="variant-title">
                          <span>{v.variant_name}</span>
                          <strong>{v.conversion_rate}% Conv</strong>
                        </div>
                        <div className="variant-meta">
                          <span>{v.allocation_pct}% Allocation</span>
                          <span>{v.conversion_count}/{v.impression_count} conversions</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {exp.status === 'RUNNING' && (
                    <div style={{ marginTop: 14 }}>
                      <button
                        className="plm-btn-outline"
                        style={{ width: '100%', justifyContent: 'center' }}
                        onClick={() => handleSimulateAssignmentAndConversion(exp.id)}
                        disabled={actionLoading}
                      >
                        <Play size={13} /> Simulate User Assignment & Conversion
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 7: RELEASES */}
      {activeTab === 'releases' && (
        <div className="plm-tab-content">
          <div className="plm-toolbar-row">
            <div>
              <h3>Shipped Versions & Release Notes</h3>
              <p className="plm-subtitle">Document release milestones, rollout percentages, and changelogs.</p>
            </div>
          </div>

          {releases.length === 0 ? (
            <div className="plm-empty-card">
              <Rocket size={36} color="#6366f1" />
              <h4>No Release Records Found</h4>
              <p>Releases document version rollouts and customer changelogs.</p>
            </div>
          ) : (
            <div className="releases-list">
              {releases.map((rel) => (
                <div key={rel.id} className="release-card">
                  <div className="release-header">
                    <span className="version-tag">{rel.release_version}</span>
                    <span className={`badge-status ${rel.status.toLowerCase()}`}>{rel.status}</span>
                  </div>
                  <h4>{rel.title}</h4>
                  <p className="release-desc">{rel.description}</p>
                  <div className="release-notes-box">
                    <strong>Changelog:</strong>
                    <p>{rel.release_notes}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 8: AI PRODUCT ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="plm-tab-content">
          <div className="ai-assistant-card">
            <div className="ai-header">
              <Sparkles className="ai-icon" />
              <div>
                <h3>Grounded AI Product Assistant</h3>
                <p>Natural language answers backed strictly by tenant customer feature requests, demand signals, and live roadmap deliverables.</p>
              </div>
            </div>

            <form onSubmit={handleAskAssistant} className="ai-query-form">
              <input
                type="text"
                placeholder="Ask about highest demand feature requests, roadmap bottlenecks, or experiment conversion..."
                value={aiQuery}
                onChange={(e) => setAiQuery(e.target.value)}
                className="ai-input"
              />
              <button type="submit" className="plm-btn-primary" disabled={aiLoading || !aiQuery.trim()}>
                {aiLoading ? 'Analyzing...' : 'Ask Assistant'}
              </button>
            </form>

            {aiResponse && (
              <div className="ai-response-box">
                <div className="response-header">
                  <span className="badge-grounded">Verified Grounded Telemetry</span>
                  <span className="demand-chip">Total Demand: {aiResponse.total_feature_requests} Requests</span>
                </div>
                <p className="ai-answer-text">{aiResponse.answer}</p>
                {aiResponse.recommended_roadmap_actions?.length > 0 && (
                  <div className="recommendations-box">
                    <strong>Recommended Strategic Actions:</strong>
                    <ul>
                      {aiResponse.recommended_roadmap_actions.map((act, idx) => (
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

      {/* MODAL 1: ADD DISCOVERY */}
      {showDiscoveryModal && (
        <div className="modal-backdrop">
          <div className="plm-modal">
            <div className="modal-header">
              <h3>Log Product Discovery</h3>
              <button className="btn-close" onClick={() => setShowDiscoveryModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateDiscovery}>
              <div className="form-group">
                <label>Problem Statement Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Real-Time Collaborative Canvas"
                  value={newDiscovery.title}
                  onChange={(e) => setNewDiscovery({ ...newDiscovery, title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Problem Statement</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Describe the friction or pain point customers experience..."
                  value={newDiscovery.problem_statement}
                  onChange={(e) => setNewDiscovery({ ...newDiscovery, problem_statement: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Hypothesis</label>
                <textarea
                  rows={2}
                  required
                  placeholder="We believe that building X will result in Y metric improvement..."
                  value={newDiscovery.hypothesis}
                  onChange={(e) => setNewDiscovery({ ...newDiscovery, hypothesis: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Target Users</label>
                  <input
                    type="text"
                    value={newDiscovery.target_users}
                    onChange={(e) => setNewDiscovery({ ...newDiscovery, target_users: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Customer Segment</label>
                  <select
                    value={newDiscovery.customer_segment}
                    onChange={(e) => setNewDiscovery({ ...newDiscovery, customer_segment: e.target.value })}
                  >
                    <option value="ENTERPRISE">Enterprise</option>
                    <option value="MID_MARKET">Mid-Market</option>
                    <option value="SMB">SMB</option>
                    <option value="STARTUP">Startup</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="plm-btn-outline" onClick={() => setShowDiscoveryModal(false)}>Cancel</button>
                <button type="submit" className="plm-btn-primary" disabled={actionLoading}>Save Discovery</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: ADD FEATURE REQUEST */}
      {showFeatureModal && (
        <div className="modal-backdrop">
          <div className="plm-modal">
            <div className="modal-header">
              <h3>Capture Customer Feature Request</h3>
              <button className="btn-close" onClick={() => setShowFeatureModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateFeatureRequest}>
              <div className="form-group">
                <label>Feature Request Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Bidirectional Jira Ticket Synchronization"
                  value={newFeature.title}
                  onChange={(e) => setNewFeature({ ...newFeature, title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Description & Scope</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Detail the requested capability..."
                  value={newFeature.description}
                  onChange={(e) => setNewFeature({ ...newFeature, description: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Customer Name / Account</label>
                  <input
                    type="text"
                    required
                    value={newFeature.customer_name}
                    onChange={(e) => setNewFeature({ ...newFeature, customer_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Customer Endorsements Count</label>
                  <input
                    type="number"
                    min="1"
                    value={newFeature.request_count}
                    onChange={(e) => setNewFeature({ ...newFeature, request_count: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Priority</label>
                  <select
                    value={newFeature.priority}
                    onChange={(e) => setNewFeature({ ...newFeature, priority: e.target.value })}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="CRITICAL">Critical</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Pipeline Revenue Impact ($)</label>
                  <input
                    type="number"
                    min="0"
                    step="1000"
                    value={newFeature.revenue_impact}
                    onChange={(e) => setNewFeature({ ...newFeature, revenue_impact: Number(e.target.value) })}
                  />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="plm-btn-outline" onClick={() => setShowFeatureModal(false)}>Cancel</button>
                <button type="submit" className="plm-btn-primary" disabled={actionLoading}>Submit Request</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: MERGE FEATURE REQUESTS */}
      {showMergeModal && (
        <div className="modal-backdrop">
          <div className="plm-modal">
            <div className="modal-header">
              <h3>Merge Duplicate Feature Requests</h3>
              <button className="btn-close" onClick={() => setShowMergeModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleMergeFeatureRequests}>
              <p className="calc-desc">
                Merging transfers customer endorsement count and pipeline revenue impact into the primary target request, marking the duplicate as merged.
              </p>
              <div className="form-group">
                <label>Duplicate Source Request (to be merged)</label>
                <select
                  required
                  value={mergeSourceId}
                  onChange={(e) => setMergeSourceId(e.target.value)}
                >
                  <option value="">Select source request...</option>
                  {featureRequests.filter(r => !r.merged_into_id).map(r => (
                    <option key={r.id} value={r.id}>{r.title} ({r.request_count} reqs)</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Primary Target Request (to keep active)</label>
                <select
                  required
                  value={mergeTargetId}
                  onChange={(e) => setMergeTargetId(e.target.value)}
                >
                  <option value="">Select primary target request...</option>
                  {featureRequests.filter(r => r.id !== mergeSourceId && !r.merged_into_id).map(r => (
                    <option key={r.id} value={r.id}>{r.title} ({r.request_count} reqs)</option>
                  ))}
                </select>
              </div>
              <div className="modal-actions">
                <button type="button" className="plm-btn-outline" onClick={() => setShowMergeModal(false)}>Cancel</button>
                <button type="submit" className="plm-btn-primary" disabled={actionLoading || !mergeSourceId || !mergeTargetId}>
                  Confirm Merge
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: ADD ROADMAP ITEM */}
      {showRoadmapModal && (
        <div className="modal-backdrop">
          <div className="plm-modal">
            <div className="modal-header">
              <h3>Schedule Roadmap Deliverable</h3>
              <button className="btn-close" onClick={() => setShowRoadmapModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateRoadmapItem}>
              <div className="form-group">
                <label>Deliverable Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Audit Log Evidence Export Engine"
                  value={newRoadmapItem.title}
                  onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, title: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Deliverable technical scope..."
                  value={newRoadmapItem.description}
                  onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, description: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Target Quarter</label>
                  <input
                    type="text"
                    required
                    value={newRoadmapItem.quarter}
                    onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, quarter: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Product Area</label>
                  <select
                    value={newRoadmapItem.product_area}
                    onChange={(e) => setNewRoadmapItem({ ...newRoadmapItem, product_area: e.target.value })}
                  >
                    <option value="CORE_PLATFORM">Core Platform</option>
                    <option value="SECURITY">Security & SOC</option>
                    <option value="INTEGRATIONS">Integrations</option>
                    <option value="AI_ANALYTICS">AI Analytics</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="plm-btn-outline" onClick={() => setShowRoadmapModal(false)}>Cancel</button>
                <button type="submit" className="plm-btn-primary" disabled={actionLoading}>Schedule Item</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 5: ADD EXPERIMENT */}
      {showExperimentModal && (
        <div className="modal-backdrop">
          <div className="plm-modal">
            <div className="modal-header">
              <h3>Configure A/B Experiment</h3>
              <button className="btn-close" onClick={() => setShowExperimentModal(false)}><X size={18} /></button>
            </div>
            <form onSubmit={handleCreateExperiment}>
              <div className="form-group">
                <label>Experiment Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Quickstart Checklist vs Guided Modal"
                  value={newExp.name}
                  onChange={(e) => setNewExp({ ...newExp, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Hypothesis</label>
                <textarea
                  rows={2}
                  required
                  placeholder="Describe expected conversion outcome..."
                  value={newExp.hypothesis}
                  onChange={(e) => setNewExp({ ...newExp, hypothesis: e.target.value })}
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Primary Metric</label>
                  <input
                    type="text"
                    required
                    value={newExp.primary_metric}
                    onChange={(e) => setNewExp({ ...newExp, primary_metric: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Initial Status</label>
                  <select
                    value={newExp.status}
                    onChange={(e) => setNewExp({ ...newExp, status: e.target.value })}
                  >
                    <option value="DRAFT">DRAFT (Recommended for Review)</option>
                    <option value="RUNNING">RUNNING (Live Cohort Assignment)</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="plm-btn-outline" onClick={() => setShowExperimentModal(false)}>Cancel</button>
                <button type="submit" className="plm-btn-primary" disabled={actionLoading}>Create Experiment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
