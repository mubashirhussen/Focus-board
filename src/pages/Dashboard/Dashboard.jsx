import React from 'react';
import {
  Plus,
  Layers,
  Clock,
  CheckCircle2,
  CircleDashed,
} from 'lucide-react';
import { useTasks } from '../../hooks/useTasks';
import { APP_CONFIG } from '../../app/appConfig';
import { StatCard } from '../../components/StatCard/StatCard';
import { FocusNotes } from '../../components/FocusNotes/FocusNotes';
import { TaskFilters } from '../../components/TaskFilters/TaskFilters';
import { TaskList } from '../../components/TaskList/TaskList';
import { Modal } from '../../components/Modal/Modal';
import { TaskForm } from '../../components/TaskForm/TaskForm';
import { ConfirmDialog } from '../../components/ConfirmDialog/ConfirmDialog';
import './Dashboard.css';

export function Dashboard() {
  const {
    stats,
    statusFilter,
    setStatusFilter,
    openCreateModal,
    isTaskModalOpen,
    closeTaskModal,
    editingTask,
    deletingTask,
    closeDeleteDialog,
    confirmDeleteTask,
  } = useTasks();

  return (
    <div className="dashboard-page">
      {/* 1. Dashboard Page Title & New Task CTA Header */}
      <section className="dashboard-hero">
        <div className="hero-text-content">
          <h1 className="hero-title">{APP_CONFIG.tagline}</h1>
          <p className="hero-subtitle">{APP_CONFIG.subtitle}</p>
        </div>

        <button
          type="button"
          className="btn-new-task"
          onClick={openCreateModal}
          aria-label="Create a new task"
        >
          <Plus size={18} strokeWidth={2.5} />
          <span>New task</span>
        </button>
      </section>

      {/* 2. Focus Notes Carousel (Figma 15:2, 15:30, 15:58) */}
      <FocusNotes />

      {/* 3. Overview Statistics Cards (Derived dynamically from task state) */}
      <section className="overview-stats-section" aria-label="Task statistics overview">
        <div className="stats-grid">
          <StatCard
            icon={Layers}
            label="Total tasks"
            value={stats.total}
            subtitle="Across all projects"
            variant="total"
            active={statusFilter === 'All'}
            onClick={() => setStatusFilter('All')}
          />

          <StatCard
            icon={CircleDashed}
            label="To do"
            value={stats.todo}
            subtitle="Pending tasks"
            variant="todo"
            active={statusFilter === 'Todo'}
            onClick={() => setStatusFilter('Todo')}
          />

          <StatCard
            icon={Clock}
            label="In progress"
            value={stats.inProgress}
            subtitle="Currently underway"
            variant="in-progress"
            active={statusFilter === 'In Progress'}
            onClick={() => setStatusFilter('In Progress')}
          />

          <StatCard
            icon={CheckCircle2}
            label="Completed"
            value={stats.completed}
            subtitle={`${stats.completionRate}% completion rate`}
            variant="completed"
            active={statusFilter === 'Completed'}
            onClick={() => setStatusFilter('Completed')}
          />
        </div>
      </section>

      {/* 4. My Tasks Section */}
      <section className="my-tasks-section" aria-label="My tasks list and filters">
        <div className="section-header">
          <div>
            <h2 className="section-title">My tasks</h2>
            <p className="section-subtitle">
              Manage, prioritize and stay on top of your work
            </p>
          </div>

          <button
            type="button"
            className="mobile-quick-add-btn"
            onClick={openCreateModal}
            aria-label="Create new task"
          >
            <Plus size={20} />
          </button>
        </div>

        {/* Search & Filter Toolbar */}
        <TaskFilters />

        {/* Task List or Clean Empty State */}
        <TaskList />
      </section>

      {/* 5. Create / Edit Task Modal */}
      <Modal
        isOpen={isTaskModalOpen}
        onClose={closeTaskModal}
        title={editingTask ? 'Edit task' : 'Create new task'}
        subtitle={
          editingTask
            ? 'Update task details to stay on top of your schedule.'
            : 'Set your work details to stay on top of your schedule.'
        }
      >
        <TaskForm />
      </Modal>

      {/* 6. Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deletingTask)}
        title="Delete Task"
        message={`Are you sure you want to delete "${deletingTask?.title}"? This action cannot be undone.`}
        confirmLabel="Delete"
        cancelLabel="Cancel"
        onConfirm={confirmDeleteTask}
        onCancel={closeDeleteDialog}
      />
    </div>
  );
}
