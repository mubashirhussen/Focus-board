import React from 'react';
import { useTasks } from '../hooks/useTasks';
import './TaskFilters/TaskFilters.css';

/**
 * Reusable FilterTabs Component (Step 13 in Implementation Guide)
 * Renders status tabs (All, To do, In progress, Completed) and priority dropdown filter.
 * Can be used with explicit props or automatically connect to useTasks context.
 */
export function FilterTabs({
  activeStatus,
  onStatusChange,
  activePriority,
  onPriorityChange,
  statusCounts = {},
}) {
  let contextValues = null;
  try {
    contextValues = useTasks();
  } catch {
    // Standalone usage outside TaskProvider
  }

  const currentStatus = activeStatus !== undefined ? activeStatus : (contextValues?.statusFilter || 'All');
  const currentPriority = activePriority !== undefined ? activePriority : (contextValues?.priorityFilter || 'All');
  const stats = statusCounts && Object.keys(statusCounts).length > 0 ? statusCounts : (contextValues?.stats || {});

  const handleStatusClick = (statusId) => {
    if (onStatusChange) {
      onStatusChange(statusId);
    } else if (contextValues?.setStatusFilter) {
      contextValues.setStatusFilter(statusId);
    }
  };

  const handlePriorityChange = (e) => {
    if (onPriorityChange) {
      onPriorityChange(e.target.value);
    } else if (contextValues?.setPriorityFilter) {
      contextValues.setPriorityFilter(e.target.value);
    }
  };

  const statusTabs = [
    { id: 'All', label: 'All', count: stats.total },
    { id: 'To do', label: 'To do', count: stats.todo },
    { id: 'In progress', label: 'In progress', count: stats.inProgress },
    { id: 'Completed', label: 'Completed', count: stats.completed },
  ];

  const priorities = [
    { value: 'All', label: 'Priority: All' },
    { value: 'High', label: 'High' },
    { value: 'Medium', label: 'Medium' },
    { value: 'Low', label: 'Low' },
  ];

  return (
    <div className="task-filters-bar" role="region" aria-label="Task status and priority filters">
      {/* Status Filter Tabs */}
      <div className="status-tabs" role="tablist" aria-label="Filter tasks by status">
        {statusTabs.map((tab) => {
          const isNormActive =
            String(currentStatus).toLowerCase().replace(/[\s_-]+/g, '') ===
            String(tab.id).toLowerCase().replace(/[\s_-]+/g, '');

          return (
            <button
              key={tab.id}
              type="button"
              className={`status-tab-btn ${isNormActive ? 'active' : ''}`}
              onClick={() => handleStatusClick(tab.id)}
              role="tab"
              aria-selected={isNormActive}
            >
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span className="status-tab-count">({tab.count})</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Priority Dropdown Filter */}
      <div className="priority-select-wrapper">
        <label htmlFor="priority-filter-select-tabs" className="sr-only">
          Filter by priority
        </label>
        <select
          id="priority-filter-select-tabs"
          className="priority-select"
          value={currentPriority}
          onChange={handlePriorityChange}
          aria-label="Filter tasks by priority"
        >
          {priorities.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default FilterTabs;
