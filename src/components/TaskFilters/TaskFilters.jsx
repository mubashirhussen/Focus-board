import React from 'react';
import { Search, X, Filter } from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import './TaskFilters.css';

export function TaskFilters() {
  const {
    tasks,
    stats,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
  } = useTasks();

  const statusTabs = [
    { id: 'All', label: 'All tasks', count: stats.total },
    { id: 'Todo', label: 'To do', count: stats.todo },
    { id: 'In Progress', label: 'In progress', count: stats.inProgress },
    { id: 'Completed', label: 'Completed', count: stats.completed },
  ];

  const priorities = [
    { value: 'All', label: 'Priority: All' },
    { value: 'High', label: 'High Priority' },
    { value: 'Medium', label: 'Medium Priority' },
    { value: 'Low', label: 'Low Priority' },
  ];

  const hasActiveFilters = searchQuery !== '' || statusFilter !== 'All' || priorityFilter !== 'All';

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('All');
    setPriorityFilter('All');
  };

  return (
    <div className="task-filters-bar" role="search" aria-label="Task search and filters">
      {/* Status Filter Tabs (Desktop & Mobile Scrollable) */}
      <div className="status-tabs" role="tablist" aria-label="Filter tasks by status">
        {statusTabs.map((tab) => {
          const isActive = statusFilter === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              className={`status-tab-btn ${isActive ? 'active' : ''}`}
              onClick={() => setStatusFilter(tab.id)}
              role="tab"
              aria-selected={isActive}
            >
              <span>{tab.label}</span>
              <span className="status-tab-count">({tab.count})</span>
            </button>
          );
        })}
      </div>

      {/* Search and Priority Controls */}
      <div className="filter-controls-group">
        {/* Search Input */}
        <div className="search-input-wrapper">
          <Search className="search-icon" size={16} aria-hidden="true" />
          <input
            type="text"
            className="search-field"
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search tasks by title, description or category"
          />
          {searchQuery && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => setSearchQuery('')}
              aria-label="Clear search query"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {/* Priority Dropdown Filter */}
        <div className="priority-select-wrapper">
          <label htmlFor="priority-filter-select" className="sr-only">
            Filter by priority
          </label>
          <select
            id="priority-filter-select"
            className="priority-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            {priorities.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        {/* Quick Clear Filter indicator button */}
        {hasActiveFilters && (
          <button
            type="button"
            className="reset-filters-btn"
            onClick={handleClearFilters}
            title="Reset all search and filters"
          >
            <X size={12} />
            <span>Reset</span>
          </button>
        )}
      </div>
    </div>
  );
}
