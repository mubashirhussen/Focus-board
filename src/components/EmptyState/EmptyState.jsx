import React from 'react';
import { ClipboardList, SearchX, FilterX, Plus } from 'lucide-react';
import './EmptyState.css';

export function EmptyState({
  type = 'no-tasks',
  searchQuery = '',
  onCreateTask,
  onResetFilters,
}) {
  if (type === 'no-search') {
    return (
      <div className="empty-state" role="status" aria-live="polite">
        <div className="empty-state-icon" aria-hidden="true">
          <SearchX size={28} />
        </div>
        <h3 className="empty-state-title">No matching tasks</h3>
        <p className="empty-state-message">
          No tasks found matching "{searchQuery}". Try adjusting your search query or check for typos.
        </p>
        {onResetFilters && (
          <button type="button" className="empty-state-btn" onClick={onResetFilters}>
            Clear search
          </button>
        )}
      </div>
    );
  }

  if (type === 'no-filter-match') {
    return (
      <div className="empty-state" role="status" aria-live="polite">
        <div className="empty-state-icon" aria-hidden="true">
          <FilterX size={28} />
        </div>
        <h3 className="empty-state-title">No tasks match selected filters</h3>
        <p className="empty-state-message">
          There are no tasks that match your active status or priority filters.
        </p>
        {onResetFilters && (
          <button type="button" className="empty-state-btn" onClick={onResetFilters}>
            Reset filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="empty-state" role="status" aria-live="polite">
      <div className="empty-state-icon" aria-hidden="true">
        <ClipboardList size={28} />
      </div>
      <h3 className="empty-state-title">No tasks yet</h3>
      <p className="empty-state-message">
        Plan your day, stay organized, and add your first task to get started.
      </p>
      {onCreateTask && (
        <button type="button" className="empty-state-btn empty-state-btn--primary" onClick={onCreateTask}>
          <Plus size={16} />
          <span>Create Task</span>
        </button>
      )}
    </div>
  );
}
