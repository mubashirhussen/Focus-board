import React, { useState, useEffect } from 'react';
import { useTasks } from '../../hooks/useTasks';
import { validateTaskForm } from '../../utils/validation';
import { APP_CONFIG } from '../../app/appConfig';
import { predictiveIntelligenceApi } from '../../services/predictiveIntelligenceApi';
import { AlertTriangle, ShieldCheck } from 'lucide-react';
import './TaskForm.css';

export function TaskForm() {
  const { editingTask, addTask, updateTask, closeTaskModal } = useTasks();

  const isEditMode = Boolean(editingTask);

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'Design',
    status: 'Todo',
    priority: 'Medium',
    dueDate: '',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [taskRisk, setTaskRisk] = useState(null);

  // Populate form in edit mode
  useEffect(() => {
    if (editingTask) {
      setFormData({
        title: editingTask.title || '',
        description: editingTask.description || '',
        category: editingTask.category || 'Design',
        status: editingTask.status || 'Todo',
        priority: editingTask.priority || 'Medium',
        dueDate: editingTask.dueDate || '',
      });
      // Fetch task risk telemetry
      if (editingTask.id) {
        predictiveIntelligenceApi.getTaskRisk(editingTask.id)
          .then(setTaskRisk)
          .catch(() => setTaskRisk(null));
      }
    } else {
      setTaskRisk(null);
      setFormData({
        title: '',
        description: '',
        category: 'Design',
        status: 'Todo',
        priority: 'Medium',
        dueDate: '',
      });
    }
    setErrors({});
  }, [editingTask]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Clear error for field on change
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: null,
      }));
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (isSubmitting) return;

    const validation = validateTaskForm(formData);
    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }

    setIsSubmitting(true);

    try {
      if (isEditMode) {
        updateTask(editingTask.id, formData);
      } else {
        addTask(formData);
      }
      closeTaskModal();
    } catch (err) {
      console.error('Failed to save task:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form className="task-form" onSubmit={handleSubmit} noValidate>
      {/* Title Field (Mandatory) */}
      <div className="form-group floating-form-group">
        <div className={`floating-input-wrap ${formData.title ? 'has-value' : ''}`}>
          <input
            id="task-title-input"
            name="title"
            type="text"
            className={`form-input floating-input ${errors.title ? 'is-invalid' : ''}`}
            placeholder=" "
            value={formData.title}
            onChange={handleChange}
            autoFocus
            required
            aria-required="true"
            aria-invalid={Boolean(errors.title)}
            aria-describedby={errors.title ? 'task-title-error' : undefined}
          />
          <label htmlFor="task-title-input" className="floating-placeholder-label">
            Task title (e.g., Update brand guidelines) <span className="required-asterisk">*</span>
          </label>
        </div>
        {errors.title && (
          <p id="task-title-error" className="form-error-msg" role="alert">
            {errors.title}
          </p>
        )}
      </div>

      {/* Description Field */}
      <div className="form-group floating-form-group">
        <div className={`floating-input-wrap ${formData.description ? 'has-value' : ''}`}>
          <textarea
            id="task-desc-input"
            name="description"
            rows={3}
            className={`form-textarea floating-input ${errors.description ? 'is-invalid' : ''}`}
            placeholder=" "
            value={formData.description}
            onChange={handleChange}
            aria-describedby={errors.description ? 'task-desc-error' : undefined}
          />
          <label htmlFor="task-desc-input" className="floating-placeholder-label">
            Add more details about this task...
          </label>
        </div>
        {errors.description && (
          <p id="task-desc-error" className="form-error-msg" role="alert">
            {errors.description}
          </p>
        )}
      </div>

      {/* Status & Priority 2-column row */}
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="task-status-select" className="form-label">
            Status
          </label>
          <select
            id="task-status-select"
            name="status"
            className="form-select"
            value={formData.status}
            onChange={handleChange}
          >
            {APP_CONFIG.statuses.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="task-priority-select" className="form-label">
            Priority
          </label>
          <select
            id="task-priority-select"
            name="priority"
            className="form-select"
            value={formData.priority}
            onChange={handleChange}
          >
            {APP_CONFIG.priorities.map((priority) => (
              <option key={priority} value={priority}>
                {priority}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Category & Due Date 2-column row */}
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="task-category-select" className="form-label">
            Category
          </label>
          <select
            id="task-category-select"
            name="category"
            className="form-select"
            value={formData.category}
            onChange={handleChange}
          >
            {APP_CONFIG.categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="task-due-date-input" className="form-label">
            Due date
          </label>
          <input
            id="task-due-date-input"
            name="dueDate"
            type="date"
            className="form-input"
            value={formData.dueDate}
            onChange={handleChange}
          />
        </div>
      </div>

      {/* Predictive Task Risk Telemetry (Module B47) */}
      {taskRisk && (
        <div className={`task-risk-summary-box risk-${taskRisk.risk_level?.toLowerCase()}`}>
          <div className="risk-header-line">
            <span className="risk-title">
              <AlertTriangle size={13} /> Predictive Risk: <strong>{taskRisk.risk_level}</strong> ({taskRisk.risk_score}/100)
            </span>
            <span className="risk-conf">Confidence: {Math.round((taskRisk.confidence || 0.85) * 100)}%</span>
          </div>
          {taskRisk.suggested_action && (
            <p className="risk-action-text">{taskRisk.suggested_action}</p>
          )}
        </div>
      )}

      {/* Form Action Buttons */}
      <div className="form-actions">
        <button
          type="button"
          className="form-btn form-btn--cancel"
          onClick={closeTaskModal}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="form-btn form-btn--primary"
          disabled={isSubmitting}
        >
          {isEditMode ? 'Save changes' : 'Create task'}
        </button>
      </div>
    </form>
  );
}
