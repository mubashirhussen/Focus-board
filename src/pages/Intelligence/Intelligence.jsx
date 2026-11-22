import React, { useState, useEffect } from 'react';
import {
  Brain,
  TrendingUp,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ThumbsUp,
  ThumbsDown,
  X,
  MessageSquare,
  Settings,
  Send,
  Zap,
  ArrowRight,
  ShieldAlert,
  Calendar,
} from 'lucide-react';
import { intelligenceApi } from '../../services/intelligenceApi';
import { useAuth } from '../../context/AuthContext';
import { useTasks } from '../../hooks/useTasks';
import './Intelligence.css';

export function Intelligence() {
  const { isAuthenticated } = useAuth();
  const { tasks } = useTasks();

  const [activeTab, setActiveTab] = useState('insights'); // 'insights' | 'recommendations' | 'coach' | 'preferences'
  const [metrics, setMetrics] = useState(null);
  const [patterns, setPatterns] = useState([]);
  const [insights, setInsights] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [preferences, setPreferences] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionNotice, setActionNotice] = useState(null);

  // Coach state
  const [coachInput, setCoachInput] = useState('');
  const [coachConversation, setCoachConversation] = useState([
    {
      role: 'assistant',
      content:
        'Hello! I am your AI Productivity Coach. I analyze your actual task velocity, workload patterns, and deadlines to provide grounded, actionable recommendations. How can I assist your productivity today?',
      groundedMetrics: null,
      proposedActions: ['Analyze my task bottlenecks', 'Show my high-priority recommendations', 'Plan my upcoming focus sessions'],
    },
  ]);
  const [coachLoading, setCoachLoading] = useState(false);

  // Load intelligence data
  useEffect(() => {
    loadIntelligenceData();
  }, [isAuthenticated, tasks]);

  const loadIntelligenceData = async () => {
    setLoading(true);
    try {
      if (isAuthenticated) {
        const [mRes, pRes, iRes, rRes, prefRes] = await Promise.allSettled([
          intelligenceApi.getMetrics(),
          intelligenceApi.getPatterns(),
          intelligenceApi.getInsights(),
          intelligenceApi.getRecommendations(),
          intelligenceApi.getPreferences(),
        ]);

        if (mRes.status === 'fulfilled') setMetrics(mRes.value);
        if (pRes.status === 'fulfilled') setPatterns(pRes.value?.patterns || []);
        if (iRes.status === 'fulfilled') setInsights(iRes.value?.insights || []);
        if (rRes.status === 'fulfilled') setRecommendations(rRes.value?.recommendations || []);
        if (prefRes.status === 'fulfilled') setPreferences(prefRes.value);
      } else {
        // Fallback local calculations for guest / offline mode
        calculateLocalIntelligence();
      }
    } catch (err) {
      console.warn('Failed to fetch remote intelligence, using local fallback:', err);
      calculateLocalIntelligence();
    } finally {
      setLoading(false);
    }
  };

  const calculateLocalIntelligence = () => {
    const total = tasks.length;
    const completed = tasks.filter((t) => (t.status || '').toLowerCase() === 'completed').length;
    const overdue = tasks.filter((t) => {
      if ((t.status || '').toLowerCase() === 'completed') return false;
      if (!t.dueDate) return false;
      return new Date(t.dueDate) < new Date();
    }).length;

    const rate = total > 0 ? Math.round((completed / total) * 100) : 0;

    setMetrics({
      tasks_total: total,
      tasks_completed: completed,
      tasks_overdue: overdue,
      completion_rate: rate,
      avg_completion_hours: 14.5,
      velocity_trend: completed > 2 ? 'positive' : 'stable',
    });

    setPatterns([
      {
        pattern_type: 'workload_distribution',
        title: 'Task Distribution Rhythm',
        description: `You have ${total - completed} pending tasks with ${overdue} currently past due date.`,
        confidence: 0.88,
      },
    ]);

    setInsights([
      {
        id: 'local-1',
        title: overdue > 0 ? 'Address Overdue Backlog' : 'Strong Sprint Momentum',
        description:
          overdue > 0
            ? `You have ${overdue} overdue task(s). Prioritizing or re-scheduling these will clear cognitive drag.`
            : 'You are on track with no overdue tasks! Focus on upcoming high-priority items.',
        category: 'prioritization',
        urgency_score: overdue > 0 ? 0.9 : 0.4,
        evidence_task_ids: tasks.filter((t) => t.dueDate && new Date(t.dueDate) < new Date()).map((t) => t.id),
      },
    ]);

    setRecommendations(
      tasks
        .filter((t) => (t.status || '').toLowerCase() !== 'completed')
        .slice(0, 3)
        .map((t) => ({
          task_id: t.id,
          title: t.title,
          priority: t.priority || 'Medium',
          suggested_focus_time: '09:30 - 11:00 AM',
          deadline_risk: t.dueDate && new Date(t.dueDate) < new Date() ? 'high' : 'medium',
        }))
    );
  };

  const handleDismissInsight = async (id) => {
    try {
      if (isAuthenticated && !id.startsWith('local-')) {
        await intelligenceApi.dismissInsight(id);
      }
      setInsights((prev) => prev.filter((item) => item.id !== id));
      setActionNotice('Insight dismissed.');
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      console.error('Failed to dismiss insight:', err);
    }
  };

  const handleFeedback = async (id, feedbackType) => {
    try {
      if (isAuthenticated && !id.startsWith('local-')) {
        await intelligenceApi.submitFeedback(id, feedbackType, 'User rated insight');
      }
      setActionNotice(`Feedback recorded (${feedbackType === 'helpful' ? 'Helpful 👍' : 'Not helpful 👎'}).`);
      setTimeout(() => setActionNotice(null), 3000);
    } catch (err) {
      console.error('Failed to record feedback:', err);
    }
  };

  const handleSendCoach = async (queryText = null) => {
    const text = queryText || coachInput;
    if (!text.trim()) return;

    const userMsg = { role: 'user', content: text };
    setCoachConversation((prev) => [...prev, userMsg]);
    setCoachInput('');
    setCoachLoading(true);

    try {
      if (isAuthenticated) {
        const response = await intelligenceApi.queryCoach(text);
        const assistantMsg = {
          role: 'assistant',
          content: response.content || response.response,
          groundedMetrics: response.grounded_metrics,
          proposedActions: response.proposed_actions || [],
        };
        setCoachConversation((prev) => [...prev, assistantMsg]);
      } else {
        // Fallback local coach response
        setTimeout(() => {
          setCoachConversation((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: `Based on your ${metrics?.tasks_total || 0} tasks and ${metrics?.completion_rate || 0}% completion rate, your highest priority should be knocking out urgent items early during your peak focus window.`,
              groundedMetrics: metrics,
              proposedActions: ['Re-schedule overdue tasks', 'Schedule 90-minute focus block'],
            },
          ]);
          setCoachLoading(false);
        }, 500);
        return;
      }
    } catch (err) {
      setCoachConversation((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I could not reach the coaching intelligence service. Please check your connectivity.',
          proposedActions: [],
        },
      ]);
    } finally {
      setCoachLoading(false);
    }
  };

  const handleSavePreferences = async (e) => {
    e.preventDefault();
    if (!preferences) return;
    try {
      if (isAuthenticated) {
        await intelligenceApi.updatePreferences(preferences);
        setActionNotice('Productivity preferences updated.');
        setTimeout(() => setActionNotice(null), 3000);
      } else {
        setActionNotice('Preferences saved locally.');
        setTimeout(() => setActionNotice(null), 3000);
      }
    } catch (err) {
      alert('Failed to save preferences: ' + err.message);
    }
  };

  return (
    <div className="intelligence-page">
      {/* Header */}
      <div className="intelligence-header">
        <div className="intelligence-hero">
          <h1 className="intelligence-title">Adaptive Productivity & Behavioral Analytics</h1>
          <p className="intelligence-subtitle">
            Explainable AI insights, velocity pattern tracking, and grounded coaching powered by your actual task data.
          </p>
        </div>
      </div>

      {actionNotice && <div className="intelligence-alert">{actionNotice}</div>}

      {/* Metrics Banner */}
      <div className="intelligence-metrics-grid">
        <div className="metric-box">
          <span className="metric-label">Active Workload</span>
          <div className="metric-value-row">
            <span className="metric-number">{metrics?.tasks_total ?? '—'}</span>
            <span className="metric-sub">Total Tasks</span>
          </div>
        </div>
        <div className="metric-box">
          <span className="metric-label">Completion Velocity</span>
          <div className="metric-value-row">
            <span className="metric-number">{metrics?.tasks_completed ?? '—'}</span>
            <span className="metric-trend positive">
              <CheckCircle2 size={16} /> Completed
            </span>
          </div>
        </div>
        <div className="metric-box">
          <span className="metric-label">Success Rate</span>
          <div className="metric-value-row">
            <span className="metric-number">{metrics?.completion_rate ?? 0}%</span>
            <span className="metric-sub">Efficiency</span>
          </div>
        </div>
        <div className="metric-box">
          <span className="metric-label">Overdue Risk</span>
          <div className="metric-value-row">
            <span className={`metric-number ${(metrics?.tasks_overdue || 0) > 0 ? 'warning-text' : ''}`}>
              {metrics?.tasks_overdue ?? 0}
            </span>
            <span className="metric-sub">Bottlenecks</span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="intelligence-nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'insights' ? 'active' : ''}`}
          onClick={() => setActiveTab('insights')}
        >
          <Sparkles size={16} />
          <span>Actionable Insights & Patterns ({insights.length})</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          <Zap size={16} />
          <span>Adaptive Focus Plan</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'coach' ? 'active' : ''}`}
          onClick={() => setActiveTab('coach')}
        >
          <MessageSquare size={16} />
          <span>Productivity Coach</span>
        </button>
        <button
          className={`tab-btn ${activeTab === 'preferences' ? 'active' : ''}`}
          onClick={() => setActiveTab('preferences')}
        >
          <Settings size={16} />
          <span>Intelligence Settings</span>
        </button>
      </div>

      {/* Tab: Insights & Behavioral Patterns */}
      {activeTab === 'insights' && (
        <div className="tab-pane">
          {patterns.length > 0 && (
            <div className="patterns-card">
              <h3 className="section-title">
                <TrendingUp size={18} /> Detected Behavioral Patterns
              </h3>
              <div className="patterns-list">
                {patterns.map((p, idx) => (
                  <div key={idx} className="pattern-item">
                    <div className="pattern-badge">Pattern: {p.pattern_type.replace('_', ' ').toUpperCase()}</div>
                    <div className="pattern-name">{p.title}</div>
                    <p className="pattern-desc">{p.description}</p>
                    <div className="pattern-confidence">
                      Confidence: {Math.round((p.confidence || 0.85) * 100)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="insights-container">
            <h3 className="section-title">
              <Sparkles size={18} /> Ranked Explainable Insights
            </h3>
            {loading ? (
              <div className="empty-state">Analyzing task history and metrics...</div>
            ) : insights.length === 0 ? (
              <div className="empty-state">
                <CheckCircle2 size={36} color="#10b981" />
                <p>No high-risk bottlenecks detected. Keep maintaining your steady workflow!</p>
              </div>
            ) : (
              <div className="insights-grid">
                {insights.map((insight) => (
                  <div key={insight.id} className="insight-card">
                    <div className="insight-card-header">
                      <div className="insight-badges">
                        <span className="badge category-badge">{insight.category}</span>
                        <span className="badge score-badge">
                          Urgency: {Math.round((insight.urgency_score || 0.5) * 10)}/10
                        </span>
                      </div>
                      <button
                        className="dismiss-btn"
                        onClick={() => handleDismissInsight(insight.id)}
                        title="Dismiss insight"
                      >
                        <X size={15} />
                      </button>
                    </div>

                    <h4 className="insight-title">{insight.title}</h4>
                    <p className="insight-description">{insight.description}</p>

                    {insight.evidence_task_ids?.length > 0 && (
                      <div className="evidence-section">
                        <span className="evidence-label">Supporting Evidence:</span>
                        <div className="evidence-chips">
                          {insight.evidence_task_ids.map((tid) => (
                            <span key={tid} className="evidence-chip">
                              Task #{String(tid).slice(-4)}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="insight-card-footer">
                      <span className="footer-label">Was this insight helpful?</span>
                      <div className="feedback-buttons">
                        <button
                          className="feedback-btn"
                          onClick={() => handleFeedback(insight.id, 'helpful')}
                          title="Helpful"
                        >
                          <ThumbsUp size={14} /> Yes
                        </button>
                        <button
                          className="feedback-btn"
                          onClick={() => handleFeedback(insight.id, 'not_helpful')}
                          title="Not helpful"
                        >
                          <ThumbsDown size={14} /> No
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Adaptive Recommendations */}
      {activeTab === 'recommendations' && (
        <div className="tab-pane">
          <div className="recommendations-container">
            <h3 className="section-title">
              <Zap size={18} /> Suggested Focus Queue
            </h3>
            <p className="section-subtitle">
              Prioritized according to deadline risk, urgency scoring, and your scheduled working hours.
            </p>

            {recommendations.length === 0 ? (
              <div className="empty-state">No pending recommendations. All tasks are clear!</div>
            ) : (
              <div className="recommendations-list">
                {recommendations.map((rec, idx) => (
                  <div key={rec.task_id || idx} className="recommendation-row">
                    <div className="rec-rank">{idx + 1}</div>
                    <div className="rec-details">
                      <h4 className="rec-title">{rec.title}</h4>
                      <div className="rec-meta">
                        <span className="rec-badge priority">Priority: {rec.priority}</span>
                        <span className={`rec-badge risk ${rec.deadline_risk}`}>
                          Risk: {rec.deadline_risk}
                        </span>
                      </div>
                    </div>
                    <div className="rec-timing">
                      <Clock size={16} />
                      <span>{rec.suggested_focus_time || 'Next available slot'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Grounded AI Productivity Coach */}
      {activeTab === 'coach' && (
        <div className="tab-pane">
          <div className="coach-container">
            <div className="coach-messages">
              {coachConversation.map((msg, idx) => (
                <div key={idx} className={`coach-msg-wrapper ${msg.role}`}>
                  <div className="coach-bubble">
                    <div className="coach-role-title">
                      {msg.role === 'assistant' ? (
                        <>
                          <Brain size={14} /> FocusBoard Intelligence Coach
                        </>
                      ) : (
                        'You'
                      )}
                    </div>
                    <p className="coach-text">{msg.content}</p>

                    {/* Proposed Actions */}
                    {msg.proposedActions?.length > 0 && (
                      <div className="coach-proposals">
                        <span className="proposals-title">Suggested Inquiries & Actions:</span>
                        <div className="proposal-pills">
                          {msg.proposedActions.map((action, pIdx) => (
                            <button
                              key={pIdx}
                              className="proposal-pill"
                              onClick={() => handleSendCoach(action)}
                            >
                              <span>{action}</span>
                              <ArrowRight size={12} />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {coachLoading && (
                <div className="coach-msg-wrapper assistant">
                  <div className="coach-bubble loading">
                    Analyzing metrics and formulating coach response...
                  </div>
                </div>
              )}
            </div>

            {/* Coach Input Bar */}
            <div className="coach-input-bar">
              <input
                type="text"
                placeholder="Ask about productivity bottlenecks, focus slots, or velocity..."
                value={coachInput}
                onChange={(e) => setCoachInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSendCoach();
                }}
              />
              <button
                className="coach-send-btn"
                onClick={() => handleSendCoach()}
                disabled={coachLoading || !coachInput.trim()}
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Intelligence Preferences */}
      {activeTab === 'preferences' && (
        <div className="tab-pane">
          <form className="preferences-form" onSubmit={handleSavePreferences}>
            <h3 className="section-title">
              <Settings size={18} /> Productivity & Planning Preferences
            </h3>
            <p className="section-subtitle">
              Configure your working habits so the intelligence engine provides personalized time-blocked suggestions.
            </p>

            <div className="pref-grid">
              <div className="form-group">
                <label>Working Hours (Start)</label>
                <input
                  type="text"
                  value={preferences?.working_hours_start || '09:00'}
                  onChange={(e) =>
                    setPreferences({ ...preferences, working_hours_start: e.target.value })
                  }
                  placeholder="09:00"
                />
              </div>

              <div className="form-group">
                <label>Working Hours (End)</label>
                <input
                  type="text"
                  value={preferences?.working_hours_end || '17:00'}
                  onChange={(e) =>
                    setPreferences({ ...preferences, working_hours_end: e.target.value })
                  }
                  placeholder="17:00"
                />
              </div>

              <div className="form-group">
                <label>Time Zone</label>
                <input
                  type="text"
                  value={preferences?.timezone || 'UTC'}
                  onChange={(e) =>
                    setPreferences({ ...preferences, timezone: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="pref-toggles">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={preferences?.smart_suggestions_enabled ?? true}
                  onChange={(e) =>
                    setPreferences({
                      ...preferences,
                      smart_suggestions_enabled: e.target.checked,
                    })
                  }
                />
                <div>
                  <strong>Enable Smart Insights & Pattern Detection</strong>
                  <p>Continuously detects task accumulation and overdue clusters.</p>
                </div>
              </label>

              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={preferences?.adaptive_planning_enabled ?? true}
                  onChange={(e) =>
                    setPreferences({
                      ...preferences,
                      adaptive_planning_enabled: e.target.checked,
                    })
                  }
                />
                <div>
                  <strong>Enable Adaptive Focus Scheduling</strong>
                  <p>Suggests optimal focus slots according to your working hours.</p>
                </div>
              </label>
            </div>

            <button type="submit" className="save-pref-btn">
              Save Preferences
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
