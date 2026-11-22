import React, { useState, useEffect } from 'react';
import {
  Bot,
  Play,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  ShieldAlert,
  ChevronRight,
  Sparkles,
  Sliders,
  RotateCcw,
  Check,
  X,
  Layers,
  FileCode,
} from 'lucide-react';
import { agentApi } from '../../services/agentApi';
import { useI18n } from '../../i18n/I18nContext';
import './AIAgentWorkspace.css';

export default function AIAgentWorkspace() {
  const { t, formatCurrency } = useI18n();
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState('agent-task-planner');
  const [prompt, setPrompt] = useState('');
  const [execution, setExecution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executionsHistory, setExecutionsHistory] = useState([]);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState({
    planning_style: 'balanced',
    preferred_work_hours: 6,
    prioritization_approach: 'deadline_first',
  });
  const [selectedStepOutput, setSelectedStepOutput] = useState(null);

  useEffect(() => {
    loadAgents();
    loadHistory();
    loadPreferences();
  }, []);

  const loadAgents = async () => {
    try {
      const data = await agentApi.getAgents();
      setAgents(data || []);
      if (data && data.length > 0 && !selectedAgentId) {
        setSelectedAgentId(data[0].id);
      }
    } catch (err) {
      console.error('Error loading agents:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await agentApi.getExecutions(10);
      setExecutionsHistory(data || []);
      if (data && data.length > 0 && !execution) {
        setExecution(data[0]);
      }
    } catch (err) {
      console.error('Error loading execution history:', err);
    }
  };

  const loadPreferences = async () => {
    try {
      const data = await agentApi.getPreferences();
      if (data) setPreferences(data);
    } catch (err) {
      console.error('Error loading preferences:', err);
    }
  };

  const handleLaunchExecution = async (e) => {
    if (e) e.preventDefault();
    if (!prompt.trim() || !selectedAgentId) return;

    setLoading(true);
    try {
      const created = await agentApi.createExecution({
        agent_id: selectedAgentId,
        prompt: prompt.trim(),
        auto_execute_safe: true,
      });
      setExecution(created);
      setExecutionsHistory((prev) => [created, ...prev]);
    } catch (err) {
      console.error('Error creating execution:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId) => {
    if (!execution) return;
    try {
      const updated = await agentApi.approveAction(execution.id, approvalId);
      setExecution(updated);
      setExecutionsHistory((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (err) {
      console.error('Error approving action:', err);
    }
  };

  const handleReject = async (approvalId) => {
    if (!execution) return;
    try {
      const updated = await agentApi.rejectAction(execution.id, approvalId);
      setExecution(updated);
      setExecutionsHistory((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (err) {
      console.error('Error rejecting action:', err);
    }
  };

  const handleCancel = async () => {
    if (!execution) return;
    try {
      const updated = await agentApi.cancelExecution(execution.id);
      setExecution(updated);
      setExecutionsHistory((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (err) {
      console.error('Error cancelling execution:', err);
    }
  };

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    try {
      const updated = await agentApi.updatePreferences(preferences);
      setPreferences(updated);
      setShowPreferences(false);
    } catch (err) {
      console.error('Error updating preferences:', err);
    }
  };

  const selectedAgent = agents.find((a) => a.id === selectedAgentId) || agents[0];

  const quickPrompts = [
    { label: 'Organize backlog & plan tomorrow', agent: 'agent-task-planner', text: 'Organize my overdue tasks and prepare an optimal plan for tomorrow.' },
    { label: 'Deconstruct launch project', agent: 'agent-task-breakdown', text: 'Deconstruct our Q3 product launch milestone into clear subtasks.' },
    { label: 'Plan new portfolio project', agent: 'agent-project-planner', text: 'Create a project for launching my portfolio and organize the initial work.' },
    { label: 'Analyze weekly velocity', agent: 'agent-productivity-insights', text: 'Analyze my task completion velocity and identify workflow bottlenecks.' },
  ];

  return (
    <div className="agent-workspace-container">
      {/* Top Header */}
      <div className="agent-workspace-header">
        <div>
          <h1>{t('agents.title')}</h1>
          <p className="agent-workspace-sub">{t('agents.subtitle')}</p>
        </div>
        <button
          className="btn-preferences"
          onClick={() => setShowPreferences(!showPreferences)}
          title="Configure persistent agent memory and planning preferences"
        >
          <Sliders size={15} />
          <span>{t('agents.preferences')}</span>
        </button>
      </div>

      {/* Memory Preferences Card (Collapsible) */}
      {showPreferences && (
        <form onSubmit={handleSavePreferences} className="agent-preferences-card">
          <div className="preferences-header">
            <h3>Agent Memory & Persona Controls</h3>
            <button type="button" className="btn-close-sm" onClick={() => setShowPreferences(false)}>
              <X size={16} />
            </button>
          </div>
          <div className="preferences-grid">
            <div className="pref-field">
              <label>Planning Style</label>
              <select
                value={preferences.planning_style}
                onChange={(e) => setPreferences({ ...preferences, planning_style: e.target.value })}
              >
                <option value="balanced">Balanced (Realistic buffers)</option>
                <option value="deep_work">Deep Work (90-min focus blocks)</option>
                <option value="aggressive">Aggressive (Sprint pace)</option>
                <option value="relaxed">Relaxed (Low urgency)</option>
              </select>
            </div>
            <div className="pref-field">
              <label>Target Daily Work Hours</label>
              <input
                type="number"
                min={2}
                max={12}
                value={preferences.preferred_work_hours}
                onChange={(e) => setPreferences({ ...preferences, preferred_work_hours: Number(e.target.value) })}
              />
            </div>
            <div className="pref-field">
              <label>Prioritization Approach</label>
              <select
                value={preferences.prioritization_approach}
                onChange={(e) => setPreferences({ ...preferences, prioritization_approach: e.target.value })}
              >
                <option value="deadline_first">Deadline Urgency First</option>
                <option value="impact_first">High Impact / Priority First</option>
                <option value="quick_wins">Quick Wins First</option>
              </select>
            </div>
          </div>
          <div className="preferences-actions">
            <button type="submit" className="btn-save-pref">
              Save Memory Preferences
            </button>
          </div>
        </form>
      )}

      {/* Main Workspace Layout */}
      <div className="agent-layout-grid">
        {/* Left: Agent Selection & Prompt Input */}
        <div className="agent-input-panel">
          <div className="panel-section-title">
            <Bot size={16} />
            <span>Select Autonomous Agent</span>
          </div>

          <div className="agent-cards-selector">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`agent-card-item ${selectedAgentId === agent.id ? 'active' : ''}`}
                onClick={() => setSelectedAgentId(agent.id)}
              >
                <div className="agent-card-top">
                  <strong>{agent.name}</strong>
                  <span className="agent-type-badge">{agent.agent_type.replace('_', ' ')}</span>
                </div>
                <p className="agent-card-desc">{agent.description}</p>
                <div className="agent-tools-row">
                  {agent.tools.slice(0, 3).map((tool) => (
                    <span key={tool} className="tool-pill">
                      {tool}
                    </span>
                  ))}
                  {agent.tools.length > 3 && (
                    <span className="tool-pill more">+{agent.tools.length - 3}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Prompt Form */}
          <form onSubmit={handleLaunchExecution} className="agent-prompt-form">
            <label htmlFor="agent-prompt-input">Agent Instructions / Goal</label>
            <textarea
              id="agent-prompt-input"
              rows={3}
              placeholder={t('agents.prompt_placeholder')}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
            />

            <div className="quick-prompts-bar">
              <span className="quick-label">Suggested goals:</span>
              <div className="quick-chips">
                {quickPrompts.map((qp, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="chip-btn"
                    onClick={() => {
                      setSelectedAgentId(qp.agent);
                      setPrompt(qp.text);
                    }}
                  >
                    {qp.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className="btn-launch-agent"
              disabled={loading || !prompt.trim()}
            >
              <Play size={15} />
              <span>{loading ? t('agents.executing') : t('agents.launch')}</span>
            </button>
          </form>
        </div>

        {/* Right: Execution Plan & Live Status */}
        <div className="agent-execution-panel">
          {execution ? (
            <div className="execution-view">
              <div className="execution-view-header">
                <div>
                  <div className="execution-title-row">
                    <h2>{execution.agent_name}</h2>
                    <span className={`exec-status-badge ${execution.status.toLowerCase()}`}>
                      {execution.status}
                    </span>
                  </div>
                  <p className="execution-prompt">"{execution.prompt}"</p>
                </div>
                <div className="execution-telemetry">
                  <span>Tokens: {execution.tokens_used}</span>
                  <span>Est: ${ (execution.cost_estimate_cents / 100).toFixed(2) }</span>
                  {execution.status === 'RUNNING' && (
                    <button className="btn-cancel-exec" onClick={handleCancel}>
                      Cancel Run
                    </button>
                  )}
                </div>
              </div>

              {/* HUMAN APPROVAL GATE BANNER */}
              {execution.pending_approvals && execution.pending_approvals.length > 0 && (
                <div className="approval-gate-banner">
                  <div className="approval-banner-top">
                    <ShieldAlert size={20} className="approval-icon" />
                    <div>
                      <h4>{t('agents.approval_required')}</h4>
                      <p>{t('agents.approval_notice')}</p>
                    </div>
                  </div>

                  {execution.pending_approvals.map((appr) => (
                    <div key={appr.id} className="approval-item-card">
                      <div className="approval-details">
                        <span className="action-type-badge">{appr.action_type}</span>
                        <div className="approval-reason">{appr.reason}</div>
                        <div className="approval-target">
                          <strong>Target Resource:</strong> {appr.target_resource}
                        </div>
                      </div>
                      <div className="approval-action-btns">
                        <button
                          className="btn-approve"
                          onClick={() => handleApprove(appr.id)}
                        >
                          <Check size={14} />
                          <span>{t('common.approve')}</span>
                        </button>
                        <button
                          className="btn-reject"
                          onClick={() => handleReject(appr.id)}
                        >
                          <X size={14} />
                          <span>{t('common.reject')}</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Structured Steps List */}
              <div className="execution-steps-section">
                <h3>{t('agents.plan')} ({execution.steps?.length || 0} Steps)</h3>
                <div className="steps-timeline">
                  {execution.steps?.map((step) => {
                    const isCompleted = step.status === 'COMPLETED';
                    const isRunning = step.status === 'RUNNING';
                    const isAwaiting = step.status === 'AWAITING_APPROVAL';
                    const isSkipped = step.status === 'SKIPPED';
                    const isFailed = step.status === 'FAILED';

                    return (
                      <div
                        key={step.id}
                        className={`step-timeline-item ${step.status.toLowerCase()}`}
                      >
                        <div className="step-status-icon">
                          {isCompleted && <CheckCircle2 size={18} className="icon-success" />}
                          {isRunning && <Clock size={18} className="icon-running" />}
                          {isAwaiting && <AlertTriangle size={18} className="icon-warning" />}
                          {isSkipped && <RotateCcw size={18} className="icon-skipped" />}
                          {isFailed && <XCircle size={18} className="icon-failed" />}
                          {step.status === 'PENDING' && <div className="icon-pending" />}
                        </div>
                        <div className="step-content">
                          <div className="step-header-line">
                            <span className="step-index">Step {step.step_index + 1}</span>
                            <span className="step-tool-name">{step.tool_name}</span>
                            <span className={`step-badge ${step.status.toLowerCase()}`}>
                              {step.status}
                            </span>
                          </div>
                          <div className="step-desc">{step.description}</div>

                          {step.result && (
                            <button
                              type="button"
                              className="btn-view-output"
                              onClick={() =>
                                setSelectedStepOutput(
                                  selectedStepOutput === step.id ? null : step.id
                                )
                              }
                            >
                              <FileCode size={13} />
                              <span>{selectedStepOutput === step.id ? 'Hide Output' : 'View Tool Output'}</span>
                            </button>
                          )}

                          {selectedStepOutput === step.id && step.result && (
                            <pre className="step-output-json">
                              {JSON.stringify(step.result, null, 2)}
                            </pre>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="no-execution-placeholder">
              <Sparkles size={36} className="placeholder-icon" />
              <h3>Autonomous Agent Orchestration</h3>
              <p>
                Select an agent, describe your objective, and launch an execution.
                The agent will construct an actionable plan, call verified platform tools,
                and halt for your explicit approval before any sensitive changes.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
