import React, { useState, useEffect } from 'react';
import {
  Workflow,
  Play,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  Sparkles,
  ShieldCheck,
  Plus,
  RefreshCw,
  Sliders,
  ChevronRight,
  Eye,
  Trash2,
  Pause,
  ArrowRight,
  Zap,
  Activity,
  Layers,
  Copy,
  Check,
} from 'lucide-react';
import { automationApi } from '../../services/automationApi';
import './AutomationDashboard.css';

export default function AutomationDashboard() {
  const [activeTab, setActiveTab] = useState('workflows');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Core Data
  const [overview, setOverview] = useState(null);
  const [workflows, setWorkflows] = useState([]);
  const [executions, setExecutions] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [templates, setTemplates] = useState([]);

  // Modals & Inspectors
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [executionLogs, setExecutionLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [approvalComments, setApprovalComments] = useState('');

  // AI Assistant State
  const [aiPrompt, setAiPrompt] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiGeneratedWorkflow, setAiGeneratedWorkflow] = useState(null);

  // New Workflow Form
  const [newWf, setNewWf] = useState({
    name: '',
    description: '',
    workflow_type: 'EVENT_DRIVEN',
    trigger_type: 'EVENT',
    trigger_event: 'task.created',
    action_type: 'notification.send',
    action_title: 'Automated Alert',
    action_message: 'Rule executed successfully.',
  });

  const sampleAutomationWorkflows = [
    {
      id: 1,
      name: 'High-Priority Bug Auto-Triage & Assign',
      description: 'Automatically detects High priority issues in backlog, calculates urgency score, and routes to engineering lead.',
      workflow_type: 'EVENT_DRIVEN',
      trigger_event: 'task.created',
      status: 'ACTIVE',
      execution_count: 142,
      last_executed_at: new Date(Date.now() - 1800000).toISOString(),
    },
    {
      id: 2,
      name: 'Overdue Milestone Escalation & SLA Webhook',
      description: 'Monitors sprint milestone deadlines and emits signed HMAC webhooks to PagerDuty/Slack upon breach risk.',
      workflow_type: 'SCHEDULED',
      trigger_event: 'task.overdue',
      status: 'ACTIVE',
      execution_count: 68,
      last_executed_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: 3,
      name: 'Sprint Retrospective & Velocity Digest',
      description: 'Aggregates weekly story point throughput and posts a structured Markdown digest to the team feed.',
      workflow_type: 'EVENT_DRIVEN',
      trigger_event: 'project.milestone_completed',
      status: 'ACTIVE',
      execution_count: 24,
      last_executed_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ];

  const sampleOverview = {
    active_workflows_count: 3,
    execution_success_rate: 98.6,
    pending_approvals_count: 1,
    estimated_hours_saved: 54,
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ovRes, wfRes, execRes, appRes] = await Promise.all([
        automationApi.getOverview().catch(() => null),
        automationApi.listWorkflows().catch(() => []),
        automationApi.listExecutions({ limit: 30 }).catch(() => []),
        automationApi.listApprovals({ status: 'PENDING' }).catch(() => []),
      ]);
      setOverview(ovRes || sampleOverview);
      setWorkflows(wfRes && wfRes.length > 0 ? wfRes : sampleAutomationWorkflows);
      setExecutions(execRes || []);
      setApprovals(appRes || []);
      if (ovRes?.templates) {
        setTemplates(ovRes.templates);
      }
    } catch {
      setOverview(sampleOverview);
      setWorkflows(sampleAutomationWorkflows);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Trigger Execution
  const handleTrigger = async (workflowId, dryRun = false) => {
    try {
      await automationApi.triggerWorkflow(workflowId, {
        trigger_event: 'MANUAL',
        payload: { source: 'dashboard_manual_trigger', timestamp: new Date().toISOString() },
        dry_run: dryRun,
      });
      loadData();
      alert(`Workflow execution triggered ${dryRun ? '(Dry Run Simulator)' : 'successfully'}!`);
    } catch (err) {
      alert(`Trigger failed: ${err.message}`);
    }
  };

  // Inspect Execution Logs
  const handleViewExecutionLogs = async (exec) => {
    setSelectedExecution(exec);
    setLogsLoading(true);
    try {
      const logs = await automationApi.getExecutionLogs(exec.id);
      setExecutionLogs(logs || []);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLogsLoading(false);
    }
  };

  // Approval Decision
  const handleApprovalDecision = async (approvalId, decision) => {
    try {
      await automationApi.submitApprovalDecision(approvalId, decision, approvalComments);
      setSelectedApproval(null);
      setApprovalComments('');
      loadData();
      alert(`Execution step ${decision.toLowerCase()}!`);
    } catch (err) {
      alert(`Failed to submit decision: ${err.message}`);
    }
  };

  // Create Workflow
  const handleCreateWorkflow = async (e) => {
    e.preventDefault();
    try {
      const nodes = [
        { id: 'node_1', type: 'trigger', name: 'Trigger Event', config: { event: newWf.trigger_event } },
        { id: 'node_2', type: 'action', name: 'Run Action', config: { action_type: newWf.action_type, title: newWf.action_title, message: newWf.action_message } },
        { id: 'node_3', type: 'end', name: 'Workflow Complete', config: {} },
      ];
      const edges = [
        { source: 'node_1', target: 'node_2' },
        { source: 'node_2', target: 'node_3' },
      ];

      await automationApi.createWorkflow({
        name: newWf.name,
        description: newWf.description,
        workflow_type: newWf.workflow_type,
        status: 'ACTIVE',
        trigger_type: newWf.trigger_type,
        trigger_config_json: JSON.stringify({ event: newWf.trigger_event }),
        nodes_json: JSON.stringify(nodes),
        edges_json: JSON.stringify(edges),
        version: '1.0',
      });

      setShowCreateModal(false);
      setNewWf({
        name: '',
        description: '',
        workflow_type: 'EVENT_DRIVEN',
        trigger_type: 'EVENT',
        trigger_event: 'task.created',
        action_type: 'notification.send',
        action_title: 'Automated Alert',
        action_message: 'Rule executed successfully.',
      });
      loadData();
    } catch (err) {
      alert(`Creation failed: ${err.message}`);
    }
  };

  // AI Workflow Generation
  const handleGenerateAI = async () => {
    if (!aiPrompt.trim()) return;
    setAiLoading(true);
    try {
      const generated = await automationApi.generateWorkflowFromPrompt(aiPrompt);
      setAiGeneratedWorkflow(generated);
    } catch (err) {
      alert(`AI generation failed: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  // Clone AI Generated Workflow
  const handleSaveAiWorkflow = async () => {
    if (!aiGeneratedWorkflow) return;
    try {
      await automationApi.createWorkflow({
        name: aiGeneratedWorkflow.workflow_name,
        description: aiGeneratedWorkflow.description,
        workflow_type: 'EVENT_DRIVEN',
        status: 'ACTIVE',
        trigger_type: aiGeneratedWorkflow.trigger_type,
        trigger_config_json: JSON.stringify(aiGeneratedWorkflow.trigger_config),
        nodes_json: JSON.stringify(aiGeneratedWorkflow.nodes),
        edges_json: JSON.stringify(aiGeneratedWorkflow.edges),
        version: '1.0',
      });
      setAiGeneratedWorkflow(null);
      setAiPrompt('');
      setActiveTab('workflows');
      loadData();
      alert('AI-generated workflow saved and activated!');
    } catch (err) {
      alert(`Failed to save workflow: ${err.message}`);
    }
  };

  // Delete Workflow
  const handleDeleteWorkflow = async (id) => {
    if (!window.confirm('Delete this automation workflow?')) return;
    try {
      await automationApi.deleteWorkflow(id);
      loadData();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="automation-container">
      {/* Header */}
      <div className="automation-header">
        <div className="automation-title-area">
          <h1>
            <Workflow size={28} color="#3b82f6" />
            Automation Intelligence & Workflow Orchestrator
          </h1>
          <p className="automation-subtitle">
            Enterprise event-driven execution, deterministic business rule builder, human-in-the-loop approvals, and AI workflow synthesis.
          </p>
        </div>
        <div className="automation-header-actions">
          <button className="btn-secondary" onClick={loadData} disabled={loading}>
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            Refresh
          </button>
          <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
            <Plus size={16} />
            New Workflow
          </button>
        </div>
      </div>

      {/* Metrics Banner */}
      <div className="automation-metrics-grid">
        <div className="automation-metric-card">
          <div className="metric-icon-wrap">
            <Workflow size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.active_workflows_count ?? 0}</div>
            <div className="metric-lbl">Active Workflows</div>
          </div>
        </div>

        <div className="automation-metric-card">
          <div className="metric-icon-wrap success">
            <CheckCircle2 size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.execution_success_rate ?? 100}%</div>
            <div className="metric-lbl">Success Rate</div>
          </div>
        </div>

        <div className="automation-metric-card">
          <div className="metric-icon-wrap warning">
            <ShieldCheck size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.pending_approvals_count ?? approvals.length}</div>
            <div className="metric-lbl">Pending Approvals</div>
          </div>
        </div>

        <div className="automation-metric-card">
          <div className="metric-icon-wrap purple">
            <Clock size={20} />
          </div>
          <div>
            <div className="metric-val">{overview?.estimated_hours_saved ?? 0}h</div>
            <div className="metric-lbl">Estimated Hours Saved</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="automation-tabs">
        <button
          className={`tab-btn ${activeTab === 'workflows' ? 'active' : ''}`}
          onClick={() => setActiveTab('workflows')}
        >
          <Workflow size={16} />
          Workflows ({workflows.length})
        </button>

        <button
          className={`tab-btn ${activeTab === 'executions' ? 'active' : ''}`}
          onClick={() => setActiveTab('executions')}
        >
          <Activity size={16} />
          Execution Runs ({executions.length})
        </button>

        <button
          className={`tab-btn ${activeTab === 'approvals' ? 'active' : ''}`}
          onClick={() => setActiveTab('approvals')}
        >
          <ShieldCheck size={16} />
          Approvals Inbox
          {approvals.length > 0 && <span className="badge-count">{approvals.length}</span>}
        </button>

        <button
          className={`tab-btn ${activeTab === 'templates' ? 'active' : ''}`}
          onClick={() => setActiveTab('templates')}
        >
          <Layers size={16} />
          Workflow Templates
        </button>

        <button
          className={`tab-btn ${activeTab === 'ai_assistant' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai_assistant')}
        >
          <Sparkles size={16} />
          AI Workflow Generator
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* WORKFLOWS TAB */}
        {activeTab === 'workflows' && (
          <div className="automation-card">
            <table className="workflows-table">
              <thead>
                <tr>
                  <th>Workflow</th>
                  <th>Type & Trigger</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Executions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.map((wf) => (
                  <tr key={wf.id}>
                    <td>
                      <div style={{ fontWeight: 600, color: '#0f172a' }}>{wf.name}</div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{wf.description}</div>
                    </td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{wf.trigger_type}</div>
                      <span style={{ fontSize: '0.78rem', color: '#64748b' }}>{wf.workflow_type}</span>
                    </td>
                    <td>
                      <span style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: 4, fontSize: '0.78rem' }}>
                        v{wf.version}
                      </span>
                    </td>
                    <td>
                      <span className={`status-badge ${wf.status.toLowerCase()}`}>{wf.status}</span>
                    </td>
                    <td>
                      <div>{wf.execution_count} runs</div>
                      {wf.failure_count > 0 && (
                        <span style={{ color: '#dc2626', fontSize: '0.75rem' }}>{wf.failure_count} failed</span>
                      )}
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: 6 }}>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                          title="Trigger Execution"
                          onClick={() => handleTrigger(wf.id, false)}
                        >
                          <Play size={13} color="#16a34a" />
                        </button>
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                          title="Dry-Run Simulation"
                          onClick={() => handleTrigger(wf.id, true)}
                        >
                          <Sliders size={13} color="#3b82f6" />
                        </button>
                        {!wf.is_template && (
                          <button
                            className="btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                            title="Delete"
                            onClick={() => handleDeleteWorkflow(wf.id)}
                          >
                            <Trash2 size={13} color="#dc2626" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* EXECUTIONS TAB */}
        {activeTab === 'executions' && (
          <div className="automation-card">
            <table className="workflows-table">
              <thead>
                <tr>
                  <th>Execution ID</th>
                  <th>Trigger Event</th>
                  <th>Status</th>
                  <th>Duration</th>
                  <th>Timestamp</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {executions.map((ex) => (
                  <tr key={ex.id}>
                    <td>
                      <code style={{ fontSize: '0.82rem', color: '#2563eb' }}>{ex.id}</code>
                    </td>
                    <td>
                      <span style={{ fontWeight: 500 }}>{ex.trigger_event}</span>
                    </td>
                    <td>
                      <span className={`status-badge ${ex.status.toLowerCase()}`}>{ex.status}</span>
                    </td>
                    <td>{ex.duration_ms} ms</td>
                    <td style={{ fontSize: '0.82rem', color: '#64748b' }}>
                      {new Date(ex.started_at).toLocaleString()}
                    </td>
                    <td>
                      <button
                        className="btn-secondary"
                        style={{ padding: '4px 8px', fontSize: '0.8rem' }}
                        onClick={() => handleViewExecutionLogs(ex)}
                      >
                        <Eye size={14} /> View Steps
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* APPROVALS TAB */}
        {activeTab === 'approvals' && (
          <div>
            {approvals.length === 0 ? (
              <div className="automation-card" style={{ textAlign: 'center', padding: 40 }}>
                <CheckCircle2 size={40} color="#16a34a" style={{ margin: '0 auto 12px' }} />
                <h3>No Pending Approvals</h3>
                <p style={{ color: '#64748b' }}>All consequential automation executions are cleared or approved.</p>
              </div>
            ) : (
              approvals.map((appr) => (
                <div key={appr.id} className="approval-item-card">
                  <div className="approval-meta">
                    <h4>{appr.title}</h4>
                    <p>{appr.description}</p>
                    <span className="approval-context-pill">Type: {appr.approval_type}</span>
                    <span className="approval-context-pill" style={{ marginLeft: 8 }}>
                      Execution: {appr.execution_id}
                    </span>
                  </div>
                  <div className="approval-actions">
                    <button
                      className="btn-approve"
                      onClick={() => handleApprovalDecision(appr.id, 'APPROVED')}
                    >
                      <Check size={14} /> Approve & Resume
                    </button>
                    <button
                      className="btn-reject"
                      onClick={() => handleApprovalDecision(appr.id, 'REJECTED')}
                    >
                      <XCircle size={14} /> Reject
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* TEMPLATES TAB */}
        {activeTab === 'templates' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
            {templates.map((tpl) => (
              <div key={tpl.id} className="automation-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span className="status-badge active">{tpl.template_category || 'TEMPLATE'}</span>
                  <span style={{ fontSize: '0.8rem', color: '#64748b' }}>v{tpl.version}</span>
                </div>
                <h3 style={{ fontSize: '1.05rem', marginBottom: 6 }}>{tpl.name}</h3>
                <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: 16 }}>{tpl.description}</p>
                <button
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                  onClick={() => {
                    handleTrigger(tpl.id, false);
                  }}
                >
                  <Play size={14} /> Execute Template
                </button>
              </div>
            ))}
          </div>
        )}

        {/* AI WORKFLOW GENERATOR TAB */}
        {activeTab === 'ai_assistant' && (
          <div>
            <div className="ai-generator-box">
              <h3>
                <Sparkles size={20} color="#2563eb" />
                Natural Language AI Workflow Generator
              </h3>
              <p style={{ fontSize: '0.88rem', color: '#475569' }}>
                Describe your desired business process in plain English (e.g. <em>"When a task becomes overdue, send an alert and create a manager escalation task"</em>). FocusBoard AI synthesizes the deterministic graph nodes, condition branches, and triggers.
              </p>
              <div className="ai-input-row">
                <textarea
                  className="ai-textarea"
                  placeholder="Enter automation prompt..."
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                />
                <button
                  className="btn-primary"
                  onClick={handleGenerateAI}
                  disabled={aiLoading || !aiPrompt.trim()}
                  style={{ height: 'fit-content', alignSelf: 'flex-end' }}
                >
                  <Sparkles size={16} />
                  {aiLoading ? 'Generating...' : 'Synthesize Workflow'}
                </button>
              </div>
            </div>

            {aiGeneratedWorkflow && (
              <div className="automation-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
                  <div>
                    <h3 style={{ margin: 0 }}>{aiGeneratedWorkflow.workflow_name}</h3>
                    <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '0.88rem' }}>
                      {aiGeneratedWorkflow.description}
                    </p>
                  </div>
                  <button className="btn-primary" onClick={handleSaveAiWorkflow}>
                    <Copy size={15} /> Save & Activate Workflow
                  </button>
                </div>

                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 6, marginBottom: 16 }}>
                  <strong>AI Architecture Explanation:</strong> {aiGeneratedWorkflow.explanation}
                </div>

                {/* Visual Node Flow */}
                <h4>Synthesized Workflow Steps:</h4>
                <div className="node-flow-container">
                  {aiGeneratedWorkflow.nodes.map((node, idx) => (
                    <React.Fragment key={node.id}>
                      <div className={`flow-node-box ${node.type}`}>
                        <div className="flow-node-type">{node.type}</div>
                        <div className="flow-node-title">{node.name}</div>
                      </div>
                      {idx < aiGeneratedWorkflow.nodes.length - 1 && (
                        <div className="flow-arrow">
                          <ArrowRight size={18} />
                        </div>
                      )}
                    </React.Fragment>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Create Workflow Modal */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Create Automation Workflow</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setShowCreateModal(false)}>
                ✕
              </button>
            </div>
            <form onSubmit={handleCreateWorkflow}>
              <div className="form-group">
                <label>Workflow Name</label>
                <input
                  type="text"
                  required
                  className="form-input"
                  placeholder="e.g. Critical Task Escalation"
                  value={newWf.name}
                  onChange={(e) => setNewWf({ ...newWf, name: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  placeholder="Describe what this workflow automates..."
                  value={newWf.description}
                  onChange={(e) => setNewWf({ ...newWf, description: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Trigger Event</label>
                <select
                  className="form-select"
                  value={newWf.trigger_event}
                  onChange={(e) => setNewWf({ ...newWf, trigger_event: e.target.value })}
                >
                  <option value="task.created">Task Created</option>
                  <option value="task.completed">Task Completed</option>
                  <option value="task.overdue">Task Overdue</option>
                  <option value="support.ticket.created">Support Ticket Created</option>
                  <option value="experiment.completed">Experiment Completed</option>
                </select>
              </div>

              <div className="form-group">
                <label>Action Type</label>
                <select
                  className="form-select"
                  value={newWf.action_type}
                  onChange={(e) => setNewWf({ ...newWf, action_type: e.target.value })}
                >
                  <option value="notification.send">Send In-App Notification</option>
                  <option value="task.create">Create Follow-up Task</option>
                  <option value="support.create_ticket">Create Support Ticket</option>
                  <option value="knowledge.create_doc">Generate Knowledge Document</option>
                </select>
              </div>

              <div className="form-group">
                <label>Action Title</label>
                <input
                  type="text"
                  className="form-input"
                  value={newWf.action_title}
                  onChange={(e) => setNewWf({ ...newWf, action_title: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Action Message / Description</label>
                <textarea
                  className="form-textarea"
                  rows={2}
                  value={newWf.action_message}
                  onChange={(e) => setNewWf({ ...newWf, action_message: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
                <button type="button" className="btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save & Activate
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Execution Logs Modal */}
      {selectedExecution && (
        <div className="modal-overlay" onClick={() => setSelectedExecution(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Execution Run Inspector ({selectedExecution.id})</h3>
              <button className="btn-secondary" style={{ padding: '4px 8px' }} onClick={() => setSelectedExecution(null)}>
                ✕
              </button>
            </div>
            <div>
              <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                <div><strong>Status:</strong> <span className={`status-badge ${selectedExecution.status.toLowerCase()}`}>{selectedExecution.status}</span></div>
                <div><strong>Duration:</strong> {selectedExecution.duration_ms} ms</div>
                <div><strong>Trigger:</strong> {selectedExecution.trigger_event}</div>
              </div>

              <h4>Step Execution Logs:</h4>
              {logsLoading ? (
                <p>Loading execution steps...</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {executionLogs.map((log) => (
                    <div key={log.id} style={{ border: '1px solid #e2e8f0', borderRadius: 6, padding: 12, background: '#f8fafc' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span style={{ fontWeight: 600 }}>{log.node_name} ({log.node_type})</span>
                        <span className={`status-badge ${log.status.toLowerCase()}`}>{log.status}</span>
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
                        Output: <code>{log.output_data_json}</code>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
