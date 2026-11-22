import React, { useState, useRef, useEffect } from 'react';
import {
  Calendar,
  MoreVertical,
  Check,
  Clock,
  Circle,
  Edit2,
  Trash2,
  CheckCircle2,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { formatDisplayDate, isOverdue } from '../../utils/dateHelpers';
import './TaskItem.css';

export function TaskItem({ task }) {
  const { updateTaskStatus, openEditModal, promptDeleteTask } = useTasks();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsMenuOpen(false);
      }
    }
    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  const isCompleted = task.status === 'Completed';
  const isInProgress = task.status === 'In Progress';
  const overdue = isOverdue(task.dueDate, task.status);

  // Toggle status cycling: Todo -> In Progress -> Completed -> Todo
  const handleToggleStatus = () => {
    if (task.status === 'Todo') {
      updateTaskStatus(task.id, 'In Progress');
    } else if (task.status === 'In Progress') {
      updateTaskStatus(task.id, 'Completed');
    } else {
      updateTaskStatus(task.id, 'Todo');
    }
  };

  const getPriorityClass = (priority) => {
    switch (priority) {
      case 'High':
        return 'priority-badge--high';
      case 'Medium':
        return 'priority-badge--medium';
      case 'Low':
        return 'priority-badge--low';
      default:
        return '';
    }
  };

  const getCategoryClass = (category) => {
    const cat = (category || '').toLowerCase();
    if (cat.includes('design')) return 'category-badge--design';
    if (cat.includes('dev')) return 'category-badge--dev';
    if (cat.includes('content')) return 'category-badge--content';
    if (cat.includes('market')) return 'category-badge--marketing';
    if (cat.includes('research')) return 'category-badge--research';
    return 'category-badge--default';
  };

  return (
    <div className={`task-row ${isCompleted ? 'is-completed' : ''}`}>
      {/* Left Status Toggle Circle */}
      <button
        type="button"
        className={`task-status-toggle ${isCompleted ? 'checked' : ''} ${
          isInProgress ? 'in-progress' : ''
        }`}
        onClick={handleToggleStatus}
        aria-label={`Current status: ${task.status}. Click to cycle status.`}
        title={`Status: ${task.status} (Click to change)`}
      >
        {isCompleted ? (
          <Check size={13} strokeWidth={3} />
        ) : isInProgress ? (
          <Clock size={12} strokeWidth={2.5} />
        ) : (
          <span className="status-toggle-inner-dot" />
        )}
      </button>

      {/* Task Details */}
      <div className="task-content">
        <h3 className="task-title">{task.title}</h3>
        {task.description && (
          <p className="task-description">{task.description}</p>
        )}
      </div>

      {/* Metadata Badges (Category, Priority, Due Date) */}
      <div className="task-badges">
        {task.category && (
          <span className={`category-badge ${getCategoryClass(task.category)}`}>
            {task.category}
          </span>
        )}

        <span className={`priority-badge ${getPriorityClass(task.priority)}`}>
          {task.priority}
        </span>

        {task.dueDate && (
          <span className={`date-badge ${overdue ? 'is-overdue' : ''}`}>
            <Calendar size={13} aria-hidden="true" />
            <span>{formatDisplayDate(task.dueDate)}</span>
          </span>
        )}
      </div>

      {/* Actions dropdown menu */}
      <div className="task-actions" ref={menuRef}>
        <button
          type="button"
          className="task-menu-btn"
          onClick={() => setIsMenuOpen((prev) => !prev)}
          aria-expanded={isMenuOpen}
          aria-label={`Task actions for ${task.title}`}
        >
          <MoreVertical size={16} />
        </button>

        {isMenuOpen && (
          <div className="task-dropdown-menu" role="menu">
            <button
              type="button"
              className="dropdown-item"
              role="menuitem"
              onClick={() => {
                setIsMenuOpen(false);
                openEditModal(task);
              }}
            >
              <Edit2 size={14} />
              <span>Edit Task</span>
            </button>

            {task.status !== 'Todo' && (
              <button
                type="button"
                className="dropdown-item"
                role="menuitem"
                onClick={() => {
                  setIsMenuOpen(false);
                  updateTaskStatus(task.id, 'Todo');
                }}
              >
                <Circle size={14} />
                <span>Mark To Do</span>
              </button>
            )}

            {task.status !== 'In Progress' && (
              <button
                type="button"
                className="dropdown-item"
                role="menuitem"
                onClick={() => {
                  setIsMenuOpen(false);
                  updateTaskStatus(task.id, 'In Progress');
                }}
              >
                <Clock size={14} />
                <span>Mark In Progress</span>
              </button>
            )}

            {task.status !== 'Completed' && (
              <button
                type="button"
                className="dropdown-item"
                role="menuitem"
                onClick={() => {
                  setIsMenuOpen(false);
                  updateTaskStatus(task.id, 'Completed');
                }}
              >
                <CheckCircle2 size={14} />
                <span>Mark Completed</span>
              </button>
            )}

            <button
              type="button"
              className="dropdown-item dropdown-item--danger"
              role="menuitem"
              onClick={() => {
                setIsMenuOpen(false);
                promptDeleteTask(task);
              }}
            >
              <Trash2 size={14} />
              <span>Delete Task</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
