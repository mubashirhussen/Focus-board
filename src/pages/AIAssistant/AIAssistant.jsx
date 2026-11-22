import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Bot,
  Calendar,
  Clock,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  Send,
  Check,
  X,
  ListTodo,
  Layers,
  Zap,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { useAuth } from '../../context/AuthContext';
import { aiApi } from '../../services/aiApi';
import './AIAssistant.css';

export function AIAssistant() {
  const { tasks, addTask, updateTask } = useTasks();
  const { isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState('chat'); // 'chat' | 'planner' | 'priorities' | 'breakdown'

  // Chat State
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I am your FocusBoard AI Productivity Assistant. I can help you plan your work day, prioritize urgent assignments, break down complex projects into subtasks, or answer questions about your workload.',
      taskReferences: [],
      proposedActions: [],
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [actionFeedback, setActionFeedback] = useState({});

  // Daily Planner State
  const [availableHours, setAvailableHours] = useState(6);
  const [planningDate, setPlanningDate] = useState(() => new Date().toISOString().split('T')[0]);
  const [dailyPlan, setDailyPlan] = useState(null);
  const [isPlanLoading, setIsPlanLoading] = useState(false);

  // Smart Prioritizer State
  const [priorities, setPriorities] = useState([]);
  const [isPrioritiesLoading, setIsPrioritiesLoading] = useState(false);

  // Task Breakdown State
  const [selectedTaskForBreakdown, setSelectedTaskForBreakdown] = useState(tasks[0]?.title || '');
  const [breakdownResult, setBreakdownResult] = useState(null);
  const [isBreakdownLoading, setIsBreakdownLoading] = useState(false);

  // Load priorities when tab clicked
  useEffect(() => {
    if (activeTab === 'priorities') {
      loadPriorities();
    }
  }, [activeTab, tasks]);

  const loadPriorities = async () => {
    setIsPrioritiesLoading(true);
    try {
      if (isAuthenticated) {
        const data = await aiApi.getPriorities();
        setPriorities(data || []);
      } else {
        // Local calculation fallback
        generateLocalPriorities();
      }
    } catch {
      generateLocalPriorities();
    } finally {
      setIsPrioritiesLoading(false);
    }
  };

  const generateLocalPriorities = () => {
    const todayStr = new Date().toISOString().split('T')[0];
    const scored = tasks
      .filter((t) => (t.status || '').toLowerCase() !== 'completed')
      .map((t) => {
        let score = (t.priority || '').toLowerCase() === 'high' ? 50 : (t.priority || '').toLowerCase() === 'medium' ? 30 : 10;
        let urgency = 'Normal';
        let reason = `Base priority: ${t.priority || 'Medium'}.`;

        if (t.dueDate) {
          if (t.dueDate < todayStr) {
            score += 40;
            urgency = 'Critical';
            reason += ` Overdue since ${t.dueDate}.`;
          } else if (t.dueDate === todayStr) {
            score += 30;
            urgency = 'High';
            reason += ' Due today.';
          }
        }
        if ((t.status || '').toLowerCase() === 'in progress') {
          score += 10;
          reason += ' Active work in progress.';
        }

        const suggestedP = score >= 70 ? 'High' : score <= 25 ? 'Low' : t.priority || 'Medium';

        return {
          task_id: t.id,
          title: t.title,
          current_priority: t.priority || 'Medium',
          suggested_priority: suggestedP,
          priority_score: Math.min(100, score),
          urgency,
          due_date: t.dueDate,
          reason,
          suggested_action: score >= 70 ? 'Schedule immediate focus block.' : 'Work during planned routine.',
        };
      })
      .sort((a, b) => b.priority_score - a.priority_score);

    setPriorities(scored);
  };

  // Chat Submission
  const handleSendMessage = async (customText = null) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim() || isChatLoading) return;

    const userMsg = { role: 'user', content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    if (!customText) setInputMessage('');
    setIsChatLoading(true);

    try {
      if (isAuthenticated) {
        const historyForApi = messages.map((m) => ({ role: m.role, content: m.content }));
        const response = await aiApi.chat(textToSend, historyForApi);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.reply,
            taskReferences: response.task_references || [],
            proposedActions: response.proposed_actions || [],
          },
        ]);
      } else {
        // Local offline chat reply
        generateLocalChatReply(textToSend);
      }
    } catch {
      generateLocalChatReply(textToSend);
    } finally {
      setIsChatLoading(false);
    }
  };

  const generateLocalChatReply = (text) => {
    const lower = text.toLowerCase();
    const incomplete = tasks.filter((t) => (t.status || '').toLowerCase() !== 'completed');
    const todayStr = new Date().toISOString().split('T')[0];

    let reply = '';
    const proposed = [];

    if (lower.includes('today') || lower.includes('work on') || lower.includes('plan')) {
      reply = `Based on your ${incomplete.length} active tasks, here are your top recommendations:\n` +
        incomplete.slice(0, 3).map((t, idx) => `${idx + 1}. **${t.title}** (${t.priority} priority, Due: ${t.dueDate || 'No deadline'})`).join('\n');
    } else if (lower.includes('overdue')) {
      const overdue = incomplete.filter((t) => t.dueDate && t.dueDate < todayStr);
      if (overdue.length === 0) {
        reply = 'You have zero overdue assignments. All task deadlines are on schedule!';
      } else {
        reply = `You have **${overdue.length} overdue task(s)**:\n` +
          overdue.map((t) => `• **${t.title}** (Was due ${t.dueDate})`).join('\n');
      }
    } else {
      reply = `You have **${incomplete.length} active assignments** currently in your FocusBoard queue. ` +
        `Feel free to use the Daily Planner or Smart Prioritizer tabs above for deep workload optimization.`;
    }

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: reply,
        taskReferences: [],
        proposedActions: proposed,
      },
    ]);
  };

  // Proposal Approval
  const handleApproveAction = async (proposal) => {
    const pId = proposal.proposal_id;
    setActionFeedback((prev) => ({ ...prev, [pId]: 'approving' }));

    try {
      if (isAuthenticated) {
        await aiApi.approveAction(proposal.action_type, proposal.task_id, proposal.payload);
      }

      // Execute locally
      if (proposal.action_type === 'update_priority' && proposal.task_id) {
        updateTask(proposal.task_id, { priority: proposal.payload.priority });
      } else if (proposal.action_type === 'reschedule' && proposal.task_id) {
        updateTask(proposal.task_id, { dueDate: proposal.payload.due_date });
      } else if (proposal.action_type === 'create_subtask') {
        addTask({
          title: proposal.payload.title,
          category: proposal.payload.category || 'Design',
          priority: proposal.payload.priority || 'Medium',
          dueDate: proposal.payload.due_date,
        });
      }

      setActionFeedback((prev) => ({ ...prev, [pId]: 'approved' }));
    } catch (err) {
      alert(`Approval error: ${err.message}`);
      setActionFeedback((prev) => ({ ...prev, [pId]: 'failed' }));
    }
  };

  // Daily Plan Generation
  const handleGeneratePlan = async () => {
    setIsPlanLoading(true);
    try {
      if (isAuthenticated) {
        const plan = await aiApi.generateDailyPlan({ planningDate, availableHours });
        setDailyPlan(plan);
      } else {
        // Local plan generation
        const incomplete = tasks.filter((t) => (t.status || '').toLowerCase() !== 'completed');
        const items = incomplete.slice(0, 4).map((t, idx) => ({
          task_id: t.id,
          title: t.title,
          category: t.category,
          priority: t.priority,
          estimated_minutes: 60,
          time_block: `${9 + idx}:00 - ${10 + idx}:00`,
          selection_reason: `Priority: ${t.priority}. Bounded for today's ${availableHours}-hour capacity.`,
        }));

        setDailyPlan({
          planning_date: planningDate,
          available_hours: availableHours,
          allocated_hours: items.length * 1.0,
          recommended_tasks: items,
          deferred_tasks_count: Math.max(0, incomplete.length - items.length),
          planning_assumptions: `Built conservatively for ${availableHours} hours with 15-minute intervals.`,
          break_suggestions: [
            'Take a 15-minute screen-free rest between focus sprints.',
            'Include a 45-minute lunch break.',
          ],
        });
      }
    } catch {
      // Fallback
    } finally {
      setIsPlanLoading(false);
    }
  };

  // Task Breakdown Generation
  const handleBreakdownTask = async () => {
    if (!selectedTaskForBreakdown) return;
    setIsBreakdownLoading(true);
    try {
      if (isAuthenticated) {
        const result = await aiApi.breakdownTask({ taskTitle: selectedTaskForBreakdown });
        setBreakdownResult(result);
      } else {
        setBreakdownResult({
          task_title: selectedTaskForBreakdown,
          summary: `Deconstructed '${selectedTaskForBreakdown}' into 3 practical subtasks.`,
          possible_blockers: ['Changing specification requirements', 'External dependency bottlenecks'],
          proposed_subtasks: [
            {
              title: `[1/3] Clarify scope & design requirements for ${selectedTaskForBreakdown}`,
              estimated_minutes: 30,
              order: 1,
              preparation: 'Audit existing requirements and Figma specs.',
              completion_criteria: 'Scope checklist approved.',
            },
            {
              title: `[2/3] Core implementation sprint for ${selectedTaskForBreakdown}`,
              estimated_minutes: 90,
              order: 2,
              preparation: 'Establish focus block with zero notifications.',
              completion_criteria: 'Draft implementation ready.',
            },
            {
              title: `[3/3] Quality verification & final testing for ${selectedTaskForBreakdown}`,
              estimated_minutes: 45,
              order: 3,
              preparation: 'Run deterministic test suite.',
              completion_criteria: 'All acceptance criteria validated.',
            },
          ],
        });
      }
    } catch {
      // Fallback
    } finally {
      setIsBreakdownLoading(false);
    }
  };

  const handleAddSubtasksToBoard = () => {
    if (!breakdownResult) return;
    breakdownResult.proposed_subtasks.forEach((st) => {
      addTask({
        title: st.title,
        category: 'Design',
        priority: 'Medium',
      });
    });
    alert(`Successfully created ${breakdownResult.proposed_subtasks.length} subtasks on your board!`);
  };

  return (
    <div className="ai-assistant-page">
      {/* Top Header */}
      <div className="ai-header">
        <div className="ai-header-titles">
          <div className="ai-sparkle-badge">
            <Sparkles size={14} />
            <span>AI Productivity Intelligence</span>
          </div>
          <h1 className="ai-title">Task Planning & Productivity Assistant</h1>
          <p className="ai-subtitle">
            Intelligent daily workload planning, transparent priority scoring, and proposal-based workflow execution.
          </p>
        </div>

        {/* Sub-Navigation Tabs */}
        <div className="ai-nav-tabs" role="tablist">
          <button
            type="button"
            className={`ai-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <Bot size={15} />
            <span>Productivity Chat</span>
          </button>
          <button
            type="button"
            className={`ai-tab-btn ${activeTab === 'planner' ? 'active' : ''}`}
            onClick={() => setActiveTab('planner')}
          >
            <Calendar size={15} />
            <span>Daily Planner</span>
          </button>
          <button
            type="button"
            className={`ai-tab-btn ${activeTab === 'priorities' ? 'active' : ''}`}
            onClick={() => setActiveTab('priorities')}
          >
            <Zap size={15} />
            <span>Smart Prioritizer</span>
          </button>
          <button
            type="button"
            className={`ai-tab-btn ${activeTab === 'breakdown' ? 'active' : ''}`}
            onClick={() => setActiveTab('breakdown')}
          >
            <Layers size={15} />
            <span>Task Breakdown</span>
          </button>
        </div>
      </div>

      {/* --- TAB 1: PRODUCTIVITY CHAT --- */}
      {activeTab === 'chat' && (
        <div className="ai-chat-container">
          {/* Quick Prompts Bar */}
          <div className="quick-prompts-bar">
            <span className="quick-prompts-label">SUGGESTED:</span>
            <button
              type="button"
              className="prompt-pill"
              onClick={() => handleSendMessage('What should I work on today?')}
            >
              Plan my day
            </button>
            <button
              type="button"
              className="prompt-pill"
              onClick={() => handleSendMessage('Which tasks are overdue or critical?')}
            >
              Check overdue tasks
            </button>
            <button
              type="button"
              className="prompt-pill"
              onClick={() => handleSendMessage('Analyze my current workload bottlenecks')}
            >
              Analyze workload
            </button>
            <button
              type="button"
              className="prompt-pill"
              onClick={() => handleSendMessage('Break down my design assignment into steps')}
            >
              Break down assignment
            </button>
          </div>

          {/* Conversation Area */}
          <div className="chat-messages-scroll">
            {messages.map((m, idx) => (
              <div key={idx} className={`chat-message ${m.role}`}>
                <div className="message-avatar">
                  {m.role === 'assistant' ? <Bot size={18} /> : <span>You</span>}
                </div>
                <div className="message-body">
                  <div className="message-text" style={{ whiteSpace: 'pre-line' }}>
                    {m.content}
                  </div>

                  {/* Render Action Proposals if present */}
                  {m.proposedActions && m.proposedActions.length > 0 && (
                    <div className="proposals-container">
                      <span className="proposals-header">AI RECOMMENDED ACTIONS (REQUIRES YOUR APPROVAL):</span>
                      {m.proposedActions.map((prop) => {
                        const status = actionFeedback[prop.proposal_id];
                        return (
                          <div key={prop.proposal_id} className="proposal-card">
                            <div className="proposal-info">
                              <span className="proposal-type">{prop.action_type.replace('_', ' ').toUpperCase()}</span>
                              <p className="proposal-desc">{prop.description}</p>
                            </div>
                            <div className="proposal-actions">
                              {status === 'approved' ? (
                                <span className="approved-badge">
                                  <Check size={14} /> Approved
                                </span>
                              ) : (
                                <button
                                  type="button"
                                  className="approve-action-btn"
                                  disabled={status === 'approving'}
                                  onClick={() => handleApproveAction(prop)}
                                >
                                  {status === 'approving' ? 'Applying...' : 'Approve & Execute'}
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="chat-message assistant loading">
                <div className="message-avatar"><Bot size={18} /></div>
                <div className="message-body">
                  <span className="typing-dots">Evaluating tasks...</span>
                </div>
              </div>
            )}
          </div>

          {/* Input Box */}
          <div className="chat-input-bar">
            <input
              type="text"
              className="chat-text-input"
              placeholder="Ask about your tasks, priorities, daily scheduling, or subtasks..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            />
            <button
              type="button"
              className="chat-send-btn"
              disabled={!inputMessage.trim() || isChatLoading}
              onClick={() => handleSendMessage()}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}

      {/* --- TAB 2: DAILY PLANNER --- */}
      {activeTab === 'planner' && (
        <div className="ai-planner-layout">
          {/* Controls Card */}
          <div className="planner-controls-card">
            <h3 className="section-title">Schedule Parameters</h3>
            <div className="control-group">
              <label>Planning Target Date</label>
              <input
                type="date"
                className="planner-input"
                value={planningDate}
                onChange={(e) => setPlanningDate(e.target.value)}
              />
            </div>
            <div className="control-group">
              <label>Available Focus Time: <strong>{availableHours} hours</strong></label>
              <input
                type="range"
                min="2"
                max="10"
                step="0.5"
                value={availableHours}
                onChange={(e) => setAvailableHours(parseFloat(e.target.value))}
                className="planner-slider"
              />
            </div>
            <button
              type="button"
              className="generate-plan-btn"
              disabled={isPlanLoading}
              onClick={handleGeneratePlan}
            >
              <Sparkles size={16} />
              <span>{isPlanLoading ? 'Generating Schedule...' : 'Generate Daily Schedule'}</span>
            </button>
          </div>

          {/* Plan Results Area */}
          <div className="planner-results-card">
            {!dailyPlan ? (
              <div className="empty-plan-placeholder">
                <Calendar size={36} className="empty-icon" />
                <h4>No Daily Schedule Generated Yet</h4>
                <p>Select your available focus hours and generate a realistic, bounded daily plan.</p>
              </div>
            ) : (
              <div className="daily-plan-view">
                <div className="plan-summary-header">
                  <div>
                    <h3>Daily Plan for {dailyPlan.planning_date}</h3>
                    <span className="plan-stats">
                      Allocated: <strong>{dailyPlan.allocated_hours}h</strong> of {dailyPlan.available_hours}h capacity
                    </span>
                  </div>
                  <span className="deferred-pill">{dailyPlan.deferred_tasks_count} tasks deferred</span>
                </div>

                <div className="time-blocks-list">
                  {dailyPlan.recommended_tasks.map((item, idx) => (
                    <div key={idx} className="time-block-row">
                      <div className="time-badge">{item.time_block}</div>
                      <div className="block-details">
                        <h4 className="block-title">{item.title}</h4>
                        <span className="block-reason">{item.selection_reason}</span>
                      </div>
                      <span className={`block-priority ${item.priority.toLowerCase()}`}>{item.priority}</span>
                    </div>
                  ))}
                </div>

                <div className="plan-footer-notes">
                  <h5>Assumptions & Rest Intervals</h5>
                  <p>{dailyPlan.planning_assumptions}</p>
                  <ul>
                    {dailyPlan.break_suggestions.map((b, i) => (
                      <li key={i}>{b}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* --- TAB 3: SMART PRIORITIZER --- */}
      {activeTab === 'priorities' && (
        <div className="ai-priorities-view">
          <div className="priorities-header">
            <h3>Deterministic Priority Scoring</h3>
            <p>
              Scores are calculated transparently (0–100) using Base Priority + Overdue/Due-Date Urgency + Active Momentum.
            </p>
          </div>

          {isPrioritiesLoading ? (
            <div className="loading-state">Evaluating task scores...</div>
          ) : priorities.length === 0 ? (
            <div className="empty-state">No incomplete tasks to score!</div>
          ) : (
            <div className="priorities-table-card">
              <table className="priorities-table">
                <thead>
                  <tr>
                    <th>Task Assignment</th>
                    <th>Score</th>
                    <th>Urgency</th>
                    <th>Current</th>
                    <th>Suggested</th>
                    <th>Rationale & Suggested Action</th>
                  </tr>
                </thead>
                <tbody>
                  {priorities.map((item) => (
                    <tr key={item.task_id}>
                      <td className="task-title-cell">
                        <strong>{item.title}</strong>
                        {item.due_date && <span className="due-tag">Due: {item.due_date}</span>}
                      </td>
                      <td>
                        <span className="score-badge">{item.priority_score}/100</span>
                      </td>
                      <td>
                        <span className={`urgency-pill ${item.urgency.toLowerCase()}`}>{item.urgency}</span>
                      </td>
                      <td>{item.current_priority}</td>
                      <td>
                        <strong className={item.suggested_priority === 'High' ? 'text-urgent' : ''}>
                          {item.suggested_priority}
                        </strong>
                      </td>
                      <td className="rationale-cell">
                        <p>{item.reason}</p>
                        <span className="action-hint">Action: {item.suggested_action}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* --- TAB 4: TASK BREAKDOWN --- */}
      {activeTab === 'breakdown' && (
        <div className="ai-breakdown-view">
          <div className="breakdown-input-card">
            <h3>AI Task Breakdown Generator</h3>
            <p>Select any complex assignment to decompose it into 3 clear, practical subtasks.</p>
            <div className="breakdown-form">
              <input
                type="text"
                className="breakdown-input"
                placeholder="Type or select a task name to break down..."
                value={selectedTaskForBreakdown}
                onChange={(e) => setSelectedTaskForBreakdown(e.target.value)}
              />
              <button
                type="button"
                className="breakdown-submit-btn"
                disabled={!selectedTaskForBreakdown.trim() || isBreakdownLoading}
                onClick={handleBreakdownTask}
              >
                <Layers size={16} />
                <span>{isBreakdownLoading ? 'Deconstructing...' : 'Deconstruct Task'}</span>
              </button>
            </div>
          </div>

          {breakdownResult && (
            <div className="breakdown-results-card">
              <div className="breakdown-results-header">
                <div>
                  <h4>Subtask Plan for: {breakdownResult.task_title}</h4>
                  <p>{breakdownResult.summary}</p>
                </div>
                <button
                  type="button"
                  className="add-subtasks-btn"
                  onClick={handleAddSubtasksToBoard}
                >
                  <ListTodo size={16} />
                  <span>Add Subtasks to Board</span>
                </button>
              </div>

              <div className="subtasks-grid">
                {breakdownResult.proposed_subtasks.map((st, i) => (
                  <div key={i} className="subtask-card">
                    <div className="subtask-header">
                      <span className="step-tag">Step {st.order}</span>
                      <span className="duration-tag">{st.estimated_minutes} min</span>
                    </div>
                    <h5 className="subtask-title">{st.title}</h5>
                    <div className="subtask-meta">
                      <p><strong>Prep:</strong> {st.preparation}</p>
                      <p><strong>Done when:</strong> {st.completion_criteria}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
