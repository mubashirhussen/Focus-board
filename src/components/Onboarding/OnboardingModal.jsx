import React, { useState } from 'react';
import { Target, Users, CheckCircle, ArrowRight, X, Sparkles } from 'lucide-react';
import { growthApi } from '../../services/growthApi';
import './OnboardingModal.css';

export default function OnboardingModal({ isOpen, onClose, onComplete }) {
  const [step, setStep] = useState(1);
  const [selectedGoal, setSelectedGoal] = useState('personal_productivity');
  const [workspaceType, setWorkspaceType] = useState('personal');
  const [firstTaskTitle, setFirstTaskTitle] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleNextStep = async () => {
    if (step === 1) {
      growthApi.trackEvent('onboarding_started', { goal: selectedGoal });
      growthApi.updateOnboarding({ step_id: 'workspace', primary_goal: selectedGoal });
      setStep(2);
    } else if (step === 2) {
      growthApi.trackEvent('onboarding_step_completed', { step: 2, workspaceType });
      growthApi.updateOnboarding({ step_id: 'project' });
      setStep(3);
    } else if (step === 3) {
      setSubmitting(true);
      try {
        await growthApi.updateOnboarding({ step_id: 'first_task' });
        await growthApi.updateOnboarding({ step_id: 'analytics' });
        growthApi.trackEvent('onboarding_completed', {
          goal: selectedGoal,
          workspaceType,
          hasTask: Boolean(firstTaskTitle),
        });
        if (onComplete) onComplete({ goal: selectedGoal, firstTaskTitle });
        onClose();
      } catch (err) {
        console.error('Error completing onboarding:', err);
      } finally {
        setSubmitting(false);
      }
    }
  };

  const handleSkip = () => {
    growthApi.trackEvent('onboarding_dismissed', { step });
    growthApi.updateOnboarding({ step_id: 'dismissed', dismissed: true });
    onClose();
  };

  return (
    <div className="onboarding-overlay" role="dialog" aria-modal="true" aria-labelledby="onboarding-title">
      <div className="onboarding-card">
        <button className="onboarding-close-btn" onClick={handleSkip} aria-label="Skip onboarding">
          <X size={18} />
        </button>

        <div className="onboarding-progress-bar">
          <div className="onboarding-progress-fill" style={{ width: `${(step / 3) * 100}%` }} />
        </div>

        <div className="onboarding-header">
          <div className="onboarding-badge">
            <Sparkles size={14} />
            <span>Welcome to FocusBoard</span>
          </div>
          <span className="onboarding-step-indicator">Step {step} of 3</span>
        </div>

        {step === 1 && (
          <div className="onboarding-step">
            <h2 id="onboarding-title">What is your primary goal with FocusBoard?</h2>
            <p className="onboarding-subtext">We'll tailor your workspace view and insights to fit your workflow.</p>
            <div className="onboarding-options">
              <label
                className={`onboarding-option-card ${selectedGoal === 'personal_productivity' ? 'active' : ''}`}
                onClick={() => setSelectedGoal('personal_productivity')}
              >
                <div className="option-icon">
                  <Target size={20} />
                </div>
                <div className="option-text">
                  <strong>Personal Task Mastery</strong>
                  <span>Track individual deadlines, organize priorities, and boost daily deep work.</span>
                </div>
              </label>

              <label
                className={`onboarding-option-card ${selectedGoal === 'team_productivity' ? 'active' : ''}`}
                onClick={() => setSelectedGoal('team_productivity')}
              >
                <div className="option-icon">
                  <Users size={20} />
                </div>
                <div className="option-text">
                  <strong>Team Collaboration & Velocity</strong>
                  <span>Collaborate in shared workspaces, assign tasks, and track team sprints.</span>
                </div>
              </label>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="onboarding-step">
            <h2 id="onboarding-title">Choose your workspace setup</h2>
            <p className="onboarding-subtext">You can always create more workspaces or invite teammates later.</p>
            <div className="onboarding-options">
              <label
                className={`onboarding-option-card ${workspaceType === 'personal' ? 'active' : ''}`}
                onClick={() => setWorkspaceType('personal')}
              >
                <div className="option-icon">
                  <CheckCircle size={20} />
                </div>
                <div className="option-text">
                  <strong>Personal Productivity Space</strong>
                  <span>Private by default. Perfect for personal goals and daily scheduling.</span>
                </div>
              </label>

              <label
                className={`onboarding-option-card ${workspaceType === 'team' ? 'active' : ''}`}
                onClick={() => setWorkspaceType('team')}
              >
                <div className="option-icon">
                  <Users size={20} />
                </div>
                <div className="option-text">
                  <strong>Team Project Workspace</strong>
                  <span>Pre-configured with member roles, project kanbans, and activity feeds.</span>
                </div>
              </label>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="onboarding-step">
            <h2 id="onboarding-title">Create your first focus item</h2>
            <p className="onboarding-subtext">Add a priority task you want to knock out today.</p>
            <div className="onboarding-input-group">
              <label htmlFor="first-task-input">Task Title</label>
              <input
                id="first-task-input"
                type="text"
                placeholder="e.g. Review Q3 product launch roadmap"
                value={firstTaskTitle}
                onChange={(e) => setFirstTaskTitle(e.target.value)}
                autoFocus
              />
            </div>
          </div>
        )}

        <div className="onboarding-footer">
          <button className="onboarding-btn-skip" onClick={handleSkip}>
            Skip for now
          </button>
          <button className="onboarding-btn-primary" onClick={handleNextStep} disabled={submitting}>
            {step === 3 ? (submitting ? 'Finishing...' : 'Get Started') : 'Continue'}
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
