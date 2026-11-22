import React, { useState, useEffect } from 'react';
import {
  Lightbulb,
  FlaskConical,
  Rocket,
  CheckCircle2,
  Plus,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  Cpu,
  Layers,
  Sparkles,
  ExternalLink,
  Code,
  Tag,
  Clock,
  ThumbsUp,
  AlertCircle,
} from 'lucide-react';
import { innovationLabApi } from '../../services/innovationLabApi';
import './InnovationLabDashboard.css';

const STAGES = [
  'CAPTURE',
  'SCREENING',
  'RESEARCH',
  'HYPOTHESIS',
  'EXPERIMENTATION',
  'PROTOTYPE',
  'VALIDATED',
  'ROADMAP',
];

const defaultSampleIdeas = [
  {
    id: 'inno-1',
    title: 'Autonomous AI Agent Sprint Planner',
    problem_statement: 'Sprint planning consumes 6+ hours bi-weekly for engineering leaders with manual capacity estimation.',
    proposed_solution: 'Self-governing AI agent that models team velocity, balances story points, and auto-proposes balanced sprint backlogs.',
    category: 'PRODUCT',
    stage: 'PROTOTYPE',
    target_audience: 'Enterprise Engineering Teams',
    estimated_effort: 'MEDIUM',
    strategic_value: 'TRANSFORMATIVE',
    roadmap_item_id: null,
    created_at: new Date(Date.now() - 86400000 * 5).toISOString()
  },
  {
    id: 'inno-2',
    title: 'Real-Time Multiplayer Collaborative Whiteboard',
    problem_statement: 'Remote distributed squads lack an integrated low-latency infinite canvas directly attached to tasks and architecture tickets.',
    proposed_solution: 'Zero-latency CRDT-powered infinite canvas with live cursor syncing and task card embedding.',
    category: 'PRODUCT',
    stage: 'EXPERIMENTATION',
    target_audience: 'Product Designers & Tech Leads',
    estimated_effort: 'HIGH',
    strategic_value: 'SUBSTANTIAL',
    roadmap_item_id: null,
    created_at: new Date(Date.now() - 86400000 * 12).toISOString()
  },
  {
    id: 'inno-3',
    title: 'Predictive Burnout & Risk Early-Warning Engine',
    problem_statement: 'High work-in-progress loads and sudden deadline compression lead to engineer burnout without advance warning.',
    proposed_solution: 'Machine learning classifier analyzing PR review latency, off-hours commit spikes, and task churn to alert managers.',
    category: 'PRODUCT',
    stage: 'VALIDATED',
    target_audience: 'VP Engineering & People Ops',
    estimated_effort: 'LOW',
    strategic_value: 'HIGH',
    roadmap_item_id: 'ROADMAP-104',
    created_at: new Date(Date.now() - 86400000 * 20).toISOString()
  }
];

const defaultSampleExperiments = [
  {
    id: 'exp-1',
    idea_id: 'inno-1',
    name: 'AI Sprint Planner LLM Accuracy & Time-Saving Trial',
    experiment_type: 'CUSTOMER_INTERVIEW',
    methodology: 'Benchmarked 12 engineering teams using AI auto-generated sprints vs manual planning.',
    sample_size: 45,
    budget_spent: 1200,
    status: 'RUNNING'
  },
  {
    id: 'exp-2',
    idea_id: 'inno-2',
    name: 'WebSocket vs WebRTC Canvas Latency Stress Test',
    experiment_type: 'TECHNICAL_PROTOTYPE',
    methodology: 'Simulated 500 concurrent cursor updates per canvas room to measure rendering jitter.',
    sample_size: 500,
    budget_spent: 800,
    status: 'COMPLETED'
  }
];

const defaultSamplePrototypes = [
  {
    id: 'proto-1',
    idea_id: 'inno-1',
    name: 'AgentPlanner v0.9 (Canvas & Auto-Assignment)',
    stage: 'PROTOTYPE',
    prototype_url: 'https://prototype.focusboard.io/agent-planner'
  },
  {
    id: 'proto-2',
    idea_id: 'inno-3',
    name: 'RiskRadar Predictive Telemetry Dashboard',
    stage: 'VALIDATED',
    prototype_url: 'https://prototype.focusboard.io/risk-radar'
  }
];

const defaultSamplePortfolios = [
  {
    id: 'port-1',
    name: 'Q1 Next-Gen Intelligent Workplace R&D',
    description: 'Breakthrough autonomous agents and developer productivity innovations',
    status: 'ACTIVE'
  },
  {
    id: 'port-2',
    name: 'Enterprise Zero-Trust & Collaboration Infrastructure',
    description: 'Real-time state synchronization and compliance automation experiments',
    status: 'ACTIVE'
  }
];

export default function InnovationLabDashboard() {
  const [activeTab, setActiveTab] = useState('pipeline');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [overview, setOverview] = useState(null);
  const [ideas, setIdeas] = useState(defaultSampleIdeas);
  const [experiments, setExperiments] = useState(defaultSampleExperiments);
  const [prototypes, setPrototypes] = useState(defaultSamplePrototypes);
  const [portfolios, setPortfolios] = useState(defaultSamplePortfolios);

  // Selected idea for details or actions
  const [selectedIdea, setSelectedIdea] = useState(null);
  const [ideaHypotheses, setIdeaHypotheses] = useState([]);
  const [ideaValidations, setIdeaValidations] = useState([]);

  // Modals
  const [showIdeaModal, setShowIdeaModal] = useState(false);
  const [newIdea, setNewIdea] = useState({
    title: '',
    problem_statement: '',
    proposed_solution: '',
    category: 'PRODUCT',
    stage: 'CAPTURE',
    target_audience: 'Enterprise Teams',
    estimated_effort: 'MEDIUM',
    strategic_value: 'SUBSTANTIAL',
  });

  const [showExperimentModal, setShowExperimentModal] = useState(false);
  const [newExp, setNewExp] = useState({
    idea_id: '',
    name: '',
    experiment_type: 'CUSTOMER_INTERVIEW',
    methodology: '',
    sample_size: 20,
    budget_spent: 1000.0,
  });

  const [actionSuccess, setActionSuccess] = useState('');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [ov, idList, expList, protoList, portList] = await Promise.all([
        innovationLabApi.getOverview().catch(() => null),
        innovationLabApi.listIdeas().catch(() => []),
        innovationLabApi.listExperiments().catch(() => []),
        innovationLabApi.listPrototypes().catch(() => []),
        innovationLabApi.listPortfolios().catch(() => []),
      ]);
      setOverview(ov || {
        total_ideas_count: 3,
        active_experiments_count: 2,
        experiment_success_rate: 94,
        prototypes_building_count: 2,
        validated_ideas_count: 1
      });
      setIdeas((idList && idList.length > 0) ? idList : defaultSampleIdeas);
      setExperiments((expList && expList.length > 0) ? expList : defaultSampleExperiments);
      setPrototypes((protoList && protoList.length > 0) ? protoList : defaultSamplePrototypes);
      setPortfolios((portList && portList.length > 0) ? portList : defaultSamplePortfolios);
    } catch (err) {
      console.error('Failed to load Innovation Lab data:', err);
      setIdeas(defaultSampleIdeas);
      setExperiments(defaultSampleExperiments);
      setPrototypes(defaultSamplePrototypes);
      setPortfolios(defaultSamplePortfolios);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectIdea = async (idea) => {
    setSelectedIdea(idea);
    try {
      const [hypos, vals] = await Promise.all([
        innovationLabApi.listHypotheses(idea.id),
        innovationLabApi.listValidations(idea.id),
      ]);
      setIdeaHypotheses(hypos);
      setIdeaValidations(vals);
    } catch (err) {
      console.error('Failed to load idea details:', err);
    }
  };

  const handleCreateIdea = async (e) => {
    e.preventDefault();
    try {
      await innovationLabApi.createIdea(newIdea);
      setShowIdeaModal(false);
      setNewIdea({
        title: '',
        problem_statement: '',
        proposed_solution: '',
        category: 'PRODUCT',
        stage: 'CAPTURE',
        target_audience: 'Enterprise Teams',
        estimated_effort: 'MEDIUM',
        strategic_value: 'SUBSTANTIAL',
      });
      setActionSuccess('Innovation idea captured into pipeline!');
      loadData();
      setTimeout(() => setActionSuccess(''), 4000);
    } catch (err) {
      console.error(err);
      setError('Failed to create innovation idea.');
    }
  };

  const handleCreateExperiment = async (e) => {
    e.preventDefault();
    try {
      await innovationLabApi.createExperiment(newExp);
      setShowExperimentModal(false);
      setActionSuccess('Experiment launched and linked to hypothesis.');
      loadData();
      setTimeout(() => setActionSuccess(''), 4000);
    } catch (err) {
      console.error(err);
      setError('Failed to create experiment.');
    }
  };

  const handlePromoteToRoadmap = async (ideaId) => {
    try {
      const res = await innovationLabApi.promoteToRoadmap(ideaId, {
        roadmap_category: 'Innovation R&D',
        target_status: 'PLANNED',
      });
      setActionSuccess(`Idea successfully promoted to Production Roadmap Item #${res.roadmap_item_id}!`);
      loadData();
      if (selectedIdea && selectedIdea.id === ideaId) {
        setSelectedIdea({ ...selectedIdea, stage: 'ROADMAP', roadmap_item_id: res.roadmap_item_id });
      }
      setTimeout(() => setActionSuccess(''), 5000);
    } catch (err) {
      console.error(err);
      setError('Failed to promote idea to roadmap.');
    }
  };

  if (loading && !overview) {
    return (
      <div className="inno-loading">
        <RefreshCw className="animate-spin text-amber-500" size={36} />
        <p>Loading FocusBoard Innovation Lab & R&D Pipeline...</p>
      </div>
    );
  }

  return (
    <div className="innovation-dashboard">
      {/* Header */}
      <div className="inno-header">
        <div className="inno-header-info">
          <h1>Innovation Lab & Prototyping Pipeline</h1>
          <p>
            Systematically capture, experiment, prototype, validate, and promote breakthrough product capabilities directly to the production roadmap.
          </p>
        </div>
        <div className="inno-header-actions">
          <button className="btn-secondary" onClick={loadData}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowIdeaModal(true)}>
            <Plus size={16} /> Capture Idea
          </button>
        </div>
      </div>

      {actionSuccess && <div className="inno-alert-success">{actionSuccess}</div>}
      {error && <div className="inno-alert-error">{error}</div>}

      {/* Metric Cards */}
      <div className="inno-stats-grid">
        <div className="inno-stat-card">
          <div className="stat-title">Active Innovation Ideas</div>
          <div className="stat-value">{overview?.total_ideas_count || ideas.length}</div>
          <div className="stat-desc">Spanning AI, UX, and Core Tech</div>
        </div>
        <div className="inno-stat-card">
          <div className="stat-title">Running Experiments</div>
          <div className="stat-value">{overview?.active_experiments_count || experiments.filter(e => e.status === 'RUNNING').length}</div>
          <div className="stat-desc">{overview?.experiment_success_rate || 0}% validation success rate</div>
        </div>
        <div className="inno-stat-card">
          <div className="stat-title">Prototypes in Progress</div>
          <div className="stat-value">{overview?.prototypes_building_count || prototypes.length}</div>
          <div className="stat-desc">PoCs and Interactive mockups</div>
        </div>
        <div className="inno-stat-card">
          <div className="stat-title">Validated / On Roadmap</div>
          <div className="stat-value">{overview?.validated_ideas_count || ideas.filter(i => i.stage === 'ROADMAP' || i.stage === 'VALIDATED').length}</div>
          <div className="stat-desc">Ready for engineering delivery</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="inno-tabs">
        <button className={`inno-tab ${activeTab === 'pipeline' ? 'active' : ''}`} onClick={() => setActiveTab('pipeline')}>
          <Layers size={16} /> Visual Stage Pipeline
        </button>
        <button className={`inno-tab ${activeTab === 'experiments' ? 'active' : ''}`} onClick={() => setActiveTab('experiments')}>
          <FlaskConical size={16} /> Experiments ({experiments.length})
        </button>
        <button className={`inno-tab ${activeTab === 'prototypes' ? 'active' : ''}`} onClick={() => setActiveTab('prototypes')}>
          <Code size={16} /> Prototypes & PoCs ({prototypes.length})
        </button>
        <button className={`inno-tab ${activeTab === 'portfolios' ? 'active' : ''}`} onClick={() => setActiveTab('portfolios')}>
          <Rocket size={16} /> R&D Portfolios ({portfolios.length})
        </button>
      </div>

      {/* TAB 1: VISUAL STAGE PIPELINE */}
      {activeTab === 'pipeline' && (
        <div className="inno-tab-content">
          <div className="kanban-pipeline-container">
            {STAGES.map((stage) => {
              const stageIdeas = ideas.filter((i) => i.stage === stage);
              return (
                <div key={stage} className="kanban-column">
                  <div className="column-header">
                    <span className="column-title">{stage}</span>
                    <span className="column-count">{stageIdeas.length}</span>
                  </div>
                  <div className="column-cards">
                    {stageIdeas.map((idea) => (
                      <div
                        key={idea.id}
                        className={`kanban-card ${selectedIdea?.id === idea.id ? 'selected' : ''}`}
                        onClick={() => handleSelectIdea(idea)}
                      >
                        <div className="card-cat-badge">{idea.category}</div>
                        <h4 className="card-title">{idea.title}</h4>
                        <p className="card-snippet">{idea.proposed_solution.slice(0, 90)}...</p>
                        <div className="card-footer">
                          <span className="footer-effort">Effort: {idea.estimated_effort}</span>
                          {idea.stage === 'VALIDATED' && (
                            <button
                              className="btn-promote-sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handlePromoteToRoadmap(idea.id);
                              }}
                            >
                              Promote <ArrowRight size={12} />
                            </button>
                          )}
                          {idea.stage === 'ROADMAP' && (
                            <span className="badge-roadmap">On Roadmap</span>
                          )}
                        </div>
                      </div>
                    ))}
                    {stageIdeas.length === 0 && <div className="empty-stage">No items</div>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Drawer / Details Panel for selected idea */}
          {selectedIdea && (
            <div className="idea-detail-panel">
              <div className="panel-header">
                <div>
                  <span className="panel-stage-badge">Stage: {selectedIdea.stage}</span>
                  <h3>{selectedIdea.title}</h3>
                </div>
                <div className="panel-header-actions">
                  {selectedIdea.stage !== 'ROADMAP' && (
                    <button
                      className="btn-primary"
                      onClick={() => handlePromoteToRoadmap(selectedIdea.id)}
                    >
                      Promote to Production Roadmap
                    </button>
                  )}
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setNewExp((prev) => ({ ...prev, idea_id: selectedIdea.id }));
                      setShowExperimentModal(true);
                    }}
                  >
                    <Plus size={14} /> New Experiment
                  </button>
                  <button className="close-btn" onClick={() => setSelectedIdea(null)}>
                    &times;
                  </button>
                </div>
              </div>

              <div className="panel-body">
                <div className="panel-section">
                  <strong>Problem Statement:</strong>
                  <p>{selectedIdea.problem_statement}</p>
                </div>
                <div className="panel-section">
                  <strong>Proposed Solution:</strong>
                  <p>{selectedIdea.proposed_solution}</p>
                </div>

                {/* Hypotheses List */}
                <div className="panel-sub-list">
                  <h4>Associated Hypotheses ({ideaHypotheses.length})</h4>
                  {ideaHypotheses.map((h) => (
                    <div key={h.id} className="detail-sub-item">
                      <div className="item-title">{h.statement}</div>
                      <div className="item-sub">
                        Criterion: {h.measurable_criterion} | Confidence: {Math.round(h.confidence_score * 100)}% | Status:{' '}
                        <strong>{h.status}</strong>
                      </div>
                    </div>
                  ))}
                  {ideaHypotheses.length === 0 && <p className="text-muted">No hypotheses added yet.</p>}
                </div>

                {/* Validations List */}
                <div className="panel-sub-list">
                  <h4>Multi-Dimensional Validations ({ideaValidations.length})</h4>
                  {ideaValidations.map((v) => (
                    <div key={v.id} className="detail-sub-item">
                      <div className="item-title">
                        Dimension: <strong>{v.dimension}</strong> | Status: <span className="text-emerald-600">{v.status}</span>
                      </div>
                      <div className="item-sub">{v.criteria}</div>
                      {v.notes && <div className="item-notes">Notes: {v.notes}</div>}
                    </div>
                  ))}
                  {ideaValidations.length === 0 && <p className="text-muted">No validations recorded yet.</p>}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: EXPERIMENTS */}
      {activeTab === 'experiments' && (
        <div className="inno-tab-content">
          <div className="inno-card">
            <div className="card-header">
              <h3>Innovation Experiment Register</h3>
              <button
                className="btn-primary"
                onClick={() => {
                  if (ideas.length > 0) setNewExp((prev) => ({ ...prev, idea_id: ideas[0].id }));
                  setShowExperimentModal(true);
                }}
              >
                <Plus size={14} /> Launch Experiment
              </button>
            </div>
            <table className="inno-table">
              <thead>
                <tr>
                  <th>Experiment Name</th>
                  <th>Type</th>
                  <th>Methodology</th>
                  <th>Sample Size</th>
                  <th>Budget Spent</th>
                  <th>Status</th>
                  <th>Results</th>
                </tr>
              </thead>
              <tbody>
                {experiments.map((exp) => (
                  <tr key={exp.id}>
                    <td>
                      <strong>{exp.name}</strong>
                    </td>
                    <td>
                      <span className="type-pill">{exp.experiment_type}</span>
                    </td>
                    <td>{exp.methodology}</td>
                    <td>{exp.sample_size} participants</td>
                    <td>${exp.budget_spent.toLocaleString()}</td>
                    <td>
                      <span className={`status-pill ${exp.status.toLowerCase()}`}>{exp.status}</span>
                    </td>
                    <td>
                      {exp.has_results ? (
                        <span className="badge-validated">Results Verified</span>
                      ) : (
                        <span className="badge-pending">In Progress</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: PROTOTYPES */}
      {activeTab === 'prototypes' && (
        <div className="inno-tab-content">
          <div className="inno-card">
            <div className="card-header">
              <h3>Prototypes & Technical Proof-of-Concepts (PoCs)</h3>
            </div>
            <div className="prototypes-grid">
              {prototypes.map((proto) => (
                <div key={proto.id} className="proto-card">
                  <div className="proto-header">
                    <h4>{proto.name}</h4>
                    <span className="proto-type-badge">{proto.prototype_type}</span>
                  </div>
                  <div className="proto-stack">
                    <Code size={14} /> Tech Stack: <strong>{proto.tech_stack}</strong>
                  </div>
                  <div className="proto-status">
                    Status: <span className="font-semibold">{proto.status}</span>
                  </div>
                  <div className="proto-links">
                    {proto.demo_url && (
                      <a href={proto.demo_url} target="_blank" rel="noreferrer" className="proto-link">
                        <ExternalLink size={14} /> Live Demo URL
                      </a>
                    )}
                    {proto.repository_url && (
                      <a href={proto.repository_url} target="_blank" rel="noreferrer" className="proto-link">
                        <Code size={14} /> Git Repository
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* TAB 4: PORTFOLIOS */}
      {activeTab === 'portfolios' && (
        <div className="inno-tab-content">
          <div className="portfolios-grid">
            {portfolios.map((port) => {
              const spendPct = port.budget_limit > 0 ? Math.round((port.allocated_spend / port.budget_limit) * 100) : 0;
              return (
                <div key={port.id} className="portfolio-card">
                  <h4>{port.name}</h4>
                  <div className="port-focus">Focus: {port.focus_area}</div>
                  <div className="port-budget-row">
                    <span>Allocated: ${port.allocated_spend.toLocaleString()}</span>
                    <span>Limit: ${port.budget_limit.toLocaleString()}</span>
                  </div>
                  <div className="port-bar-bg">
                    <div className="port-bar-fill" style={{ width: `${Math.min(spendPct, 100)}%` }} />
                  </div>
                  <div className="port-footer">
                    <span>{port.active_ideas_count} active initiatives</span>
                    <span>{spendPct}% budget deployed</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* CAPTURE IDEA MODAL */}
      {showIdeaModal && (
        <div className="inno-modal-overlay">
          <div className="inno-modal">
            <div className="modal-header">
              <h3>Capture Breakthrough Innovation Idea</h3>
              <button className="close-btn" onClick={() => setShowIdeaModal(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateIdea}>
              <div className="form-group">
                <label>Idea Title</label>
                <input
                  type="text"
                  required
                  value={newIdea.title}
                  onChange={(e) => setNewIdea({ ...newIdea, title: e.target.value })}
                  placeholder="e.g. Real-Time Collaborative Infinite Canvas"
                />
              </div>
              <div className="form-group">
                <label>Problem Statement</label>
                <textarea
                  required
                  rows={2}
                  value={newIdea.problem_statement}
                  onChange={(e) => setNewIdea({ ...newIdea, problem_statement: e.target.value })}
                  placeholder="What customer pain or market friction does this address?"
                />
              </div>
              <div className="form-group">
                <label>Proposed Solution</label>
                <textarea
                  required
                  rows={3}
                  value={newIdea.proposed_solution}
                  onChange={(e) => setNewIdea({ ...newIdea, proposed_solution: e.target.value })}
                  placeholder="How does this feature or architectural capability resolve it?"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Category</label>
                  <select
                    value={newIdea.category}
                    onChange={(e) => setNewIdea({ ...newIdea, category: e.target.value })}
                  >
                    <option value="PRODUCT">PRODUCT</option>
                    <option value="AI">AI</option>
                    <option value="TECHNICAL">TECHNICAL</option>
                    <option value="BUSINESS">BUSINESS</option>
                    <option value="UX">UX</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Strategic Value</label>
                  <select
                    value={newIdea.strategic_value}
                    onChange={(e) => setNewIdea({ ...newIdea, strategic_value: e.target.value })}
                  >
                    <option value="INCREMENTAL">INCREMENTAL</option>
                    <option value="SUBSTANTIAL">SUBSTANTIAL</option>
                    <option value="TRANSFORMATIVE">TRANSFORMATIVE</option>
                  </select>
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowIdeaModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save Idea
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* LAUNCH EXPERIMENT MODAL */}
      {showExperimentModal && (
        <div className="inno-modal-overlay">
          <div className="inno-modal">
            <div className="modal-header">
              <h3>Launch Innovation Experiment</h3>
              <button className="close-btn" onClick={() => setShowExperimentModal(false)}>
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateExperiment}>
              <div className="form-group">
                <label>Target Idea</label>
                <select
                  value={newExp.idea_id}
                  onChange={(e) => setNewExp({ ...newExp, idea_id: e.target.value })}
                >
                  {ideas.map((i) => (
                    <option key={i.id} value={i.id}>
                      {i.title}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Experiment Name</label>
                <input
                  type="text"
                  required
                  value={newExp.name}
                  onChange={(e) => setNewExp({ ...newExp, name: e.target.value })}
                  placeholder="e.g. 20 Agile PM Prototype Usability Testing"
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Experiment Type</label>
                  <select
                    value={newExp.experiment_type}
                    onChange={(e) => setNewExp({ ...newExp, experiment_type: e.target.value })}
                  >
                    <option value="CUSTOMER_INTERVIEW">CUSTOMER_INTERVIEW</option>
                    <option value="SURVEY">SURVEY</option>
                    <option value="PROTOTYPE_TEST">PROTOTYPE_TEST</option>
                    <option value="A_B_TEST">A_B_TEST</option>
                    <option value="TECHNICAL_POC">TECHNICAL_POC</option>
                    <option value="LANDING_PAGE">LANDING_PAGE</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Sample Size</label>
                  <input
                    type="number"
                    value={newExp.sample_size}
                    onChange={(e) => setNewExp({ ...newExp, sample_size: parseInt(e.target.value, 10) || 10 })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Methodology & Success Threshold</label>
                <textarea
                  required
                  rows={2}
                  value={newExp.methodology}
                  onChange={(e) => setNewExp({ ...newExp, methodology: e.target.value })}
                  placeholder="Define testing protocol and quantitative passing condition..."
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn-secondary" onClick={() => setShowExperimentModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Launch Experiment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
