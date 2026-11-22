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
} from 'lucide-react';
import { productLifecycleApi } from '../../services/productLifecycleApi';
import './ProductLifecycleWorkspace.css';

export default function ProductLifecycleWorkspace() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [overview, setOverview] = useState(null);
  const [discoveries, setDiscoveries] = useState([]);
  const [ideas, setIdeas] = useState([]);
  const [featureRequests, setFeatureRequests] = useState([]);
  const [initiatives, setInitiatives] = useState([]);
  const [roadmapItems, setRoadmapItems] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [releases, setReleases] = useState([]);

  // Prioritization Calculator state
  const [prioInputs, setPrioInputs] = useState({ reach: 150, impact: 3.0, confidence: 0.8, effort: 2.0, ease: 3.0 });
  const [prioScores, setPrioScores] = useState({ rice_score: 180, ice_score: 7.2, weighted_score: 65 });

  // AI Assistant state
  const [aiQuery, setAiQuery] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResponse, setAiResponse] = useState(null);

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
      console.error(err);
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
          <button className="plm-btn-outline" onClick={loadData} disabled={loading}>
            <RefreshCw className={`plm-btn-icon ${loading ? 'spin' : ''}`} />
            Sync Lifecycle
          </button>
        </div>
      </div>

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

      {error && <div className="plm-banner-error">{error}</div>}

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
          <div className="discoveries-grid">
            {discoveries.map((disc) => (
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
        </div>
      )}

      {/* TAB 3: FEATURE REQUESTS & DEMAND HUB */}
      {activeTab === 'requests' && (
        <div className="plm-tab-content">
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
                {featureRequests.map((freq) => (
                  <tr key={freq.id}>
                    <td>
                      <strong>{freq.title}</strong>
                      <p className="row-desc">{freq.description}</p>
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
        </div>
      )}

      {/* TAB 4: PRIORITIZATION ENGINE */}
      {activeTab === 'prioritization' && (
        <div className="plm-tab-content">
          <div className="prioritization-container">
            <div className="calculator-box">
              <h3>Interactive RICE & ICE Scoring Calculator</h3>
              <div className="calc-inputs-grid">
                <div className="calc-group">
                  <label>Reach (Users/month)</label>
                  <input
                    type="number"
                    value={prioInputs.reach}
                    onChange={(e) => setPrioInputs({ ...prioInputs, reach: Number(e.target.value) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Impact (0.5 to 5.0)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={prioInputs.impact}
                    onChange={(e) => setPrioInputs({ ...prioInputs, impact: Number(e.target.value) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Confidence (0.1 to 1.0)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={prioInputs.confidence}
                    onChange={(e) => setPrioInputs({ ...prioInputs, confidence: Number(e.target.value) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Effort (Person-months)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={prioInputs.effort}
                    onChange={(e) => setPrioInputs({ ...prioInputs, effort: Number(e.target.value) })}
                  />
                </div>
                <div className="calc-group">
                  <label>Ease (1 to 5)</label>
                  <input
                    type="number"
                    value={prioInputs.ease}
                    onChange={(e) => setPrioInputs({ ...prioInputs, ease: Number(e.target.value) })}
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
        </div>
      )}

      {/* TAB 6: A/B TESTING */}
      {activeTab === 'experiments' && (
        <div className="plm-tab-content">
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
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 7: RELEASES */}
      {activeTab === 'releases' && (
        <div className="plm-tab-content">
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
                <p>Natural language answers backed strictly by customer feature requests, demand signals, and live roadmap deliverables.</p>
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
                  <span className="badge-grounded">Verified Product Telemetry</span>
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
    </div>
  );
}
