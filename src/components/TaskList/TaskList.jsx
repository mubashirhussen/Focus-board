import React from 'react';
import { TaskItem } from '../TaskItem/TaskItem';
import { EmptyState } from '../EmptyState/EmptyState';
import { useTasks } from '../../hooks/useTasks';
import './TaskList.css';

export function TaskList() {
  const {
    tasks,
    filteredTasks,
    searchQuery,
    statusFilter,
    priorityFilter,
    openCreateModal,
    setSearchQuery,
    setStatusFilter,
    setPriorityFilter,
  } = useTasks();

  const handleResetFilters = () => {
    setSearchQuery('');
    setStatusFilter('All');
    setPriorityFilter('All');
  };

  // Determine empty state scenario
  if (tasks.length === 0) {
    return <EmptyState type="no-tasks" onCreateTask={openCreateModal} />;
  }

  if (filteredTasks.length === 0) {
    if (searchQuery.trim()) {
      return (
        <EmptyState
          type="no-search"
          searchQuery={searchQuery}
          onResetFilters={handleResetFilters}
        />
      );
    }
    return (
      <EmptyState
        type="no-filter-match"
        onResetFilters={handleResetFilters}
      />
    );
  }

  return (
    <div className="task-list" role="list" aria-label="Task list">
      {filteredTasks.map((task) => (
        <TaskItem key={task.id} task={task} />
      ))}
    </div>
  );
}
