import React, { useState, useEffect } from 'react';
import { CheckCircle2, Circle, ChevronDown, ChevronUp, Sparkles, X } from 'lucide-react';
import { growthApi } from '../../services/growthApi';
import './OnboardingChecklist.css';

export default function OnboardingChecklist({ onNavigate }) {
  const [progress, setProgress] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    loadProgress();
  }, []);

  const loadProgress = async () => {
    try {
      const data = await growthApi.getOnboarding();
      if (data) {
        setProgress(data);
        if (data.is_completed || data.dismissed) {
          setVisible(false);
        }
      }
    } catch (err) {
      console.warn('Could not load onboarding progress:', err);
    }
  };

  const handleCompleteStep = async (stepId) => {
    try {
      const updated = await growthApi.updateOnboarding({ step_id: stepId });
      setProgress(updated);
      growthApi.trackEvent('onboarding_step_completed', { step_id: stepId });
    } catch (err) {
      console.error('Error updating step:', err);
    }
  };

  const handleDismiss = async () => {
    try {
      await growthApi.updateOnboarding({ step_id: 'dismissed', dismissed: true });
      growthApi.trackEvent('onboarding_dismissed', { from: 'checklist' });
      setVisible(false);
    } catch (err) {
      setVisible(false);
    }
  };

  if (!visible || !progress) return null;

  const checklistItems = [
    { id: 'workspace', label: 'Create your primary workspace', tab: 'workspaces' },
    { id: 'project', label: 'Organize tasks into a project board', tab: 'dashboard' },
    { id: 'first_task', label: 'Add your first high-priority task', tab: 'dashboard' },
    { id: 'analytics', label: 'Explore productivity analytics & insights', tab: 'analytics' },
  ];

  const completedCount = checklistItems.filter((i) =>
    progress.completed_steps?.includes(i.id)
  ).length;
  const pct = Math.round((completedCount / checklistItems.length) * 100);

  return (
    <div className={`onboarding-checklist-card ${collapsed ? 'collapsed' : ''}`}>
      <div className="checklist-header">
        <div className="checklist-header-title">
          <Sparkles size={16} className="checklist-sparkle-icon" />
          <span>Getting Started Checklist</span>
          <span className="checklist-pct-badge">{pct}%</span>
        </div>
        <div className="checklist-header-actions">
          <button
            className="checklist-toggle-btn"
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand checklist' : 'Collapse checklist'}
          >
            {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
          </button>
          <button
            className="checklist-dismiss-btn"
            onClick={handleDismiss}
            aria-label="Dismiss checklist"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="checklist-progress-bar">
        <div className="checklist-progress-fill" style={{ width: `${pct}%` }} />
      </div>

      {!collapsed && (
        <div className="checklist-body">
          <p className="checklist-prompt">Complete these key steps to get the most out of FocusBoard:</p>
          <ul className="checklist-list">
            {checklistItems.map((item) => {
              const isDone = progress.completed_steps?.includes(item.id);
              return (
                <li
                  key={item.id}
                  className={`checklist-item ${isDone ? 'completed' : ''}`}
                  onClick={() => {
                    if (!isDone) handleCompleteStep(item.id);
                    if (onNavigate && item.tab) onNavigate(item.tab);
                  }}
                >
                  <button className="checklist-item-check" aria-label={`Mark ${item.label} complete`}>
                    {isDone ? (
                      <CheckCircle2 size={18} className="check-done" />
                    ) : (
                      <Circle size={18} className="check-pending" />
                    )}
                  </button>
                  <span className="checklist-item-text">{item.label}</span>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
