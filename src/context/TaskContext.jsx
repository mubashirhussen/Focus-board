import React, { createContext, useMemo, useState, useCallback } from 'react';
import { initialTasks } from '../data/initialTasks';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { calculateStats, filterTasks } from '../utils/taskHelpers';
import { APP_CONFIG } from '../app/appConfig';

export const TaskContext = createContext(null);

export function TaskProvider({ children }) {
  // 1. Persistent Task State (Central Single Source of Truth)
  const [tasks, setTasks] = useLocalStorage(APP_CONFIG.storageKey, initialTasks);

  // 2. Filter & Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');

  // 3. Modals & Dialog State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [deletingTask, setDeletingTask] = useState(null);

  // 4. Derived Statistics (Dynamically derived from tasks)
  const stats = useMemo(() => calculateStats(tasks), [tasks]);

  // 5. Derived Filtered Tasks (Single composite filtering mechanism)
  const filteredTasks = useMemo(() => {
    return filterTasks(tasks, {
      searchQuery,
      statusFilter,
      priorityFilter,
    });
  }, [tasks, searchQuery, statusFilter, priorityFilter]);

  // CRUD Operations
  const addTask = useCallback((taskData) => {
    const rawTitle = taskData.title !== undefined && taskData.title !== null ? String(taskData.title) : '';
    const title = rawTitle.trim();
    if (!title) {
      console.warn('addTask rejected: title cannot be empty or whitespace-only.');
      return null;
    }

    const now = new Date().toISOString();
    const newTask = {
      id: `task-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      title,
      description: taskData.description ? String(taskData.description).trim() : '',
      category: taskData.category || 'Design',
      status: taskData.status || 'Todo',
      priority: taskData.priority || 'Medium',
      dueDate: taskData.dueDate || '',
      createdAt: now,
      updatedAt: now,
    };

    setTasks((prevTasks) => [newTask, ...prevTasks]);
    return newTask;
  }, [setTasks]);

  const updateTask = useCallback((taskId, updatedData) => {
    if (!taskId) {
      console.warn('updateTask rejected: missing taskId.');
      return;
    }

    setTasks((prevTasks) =>
      prevTasks.map((task) => {
        if (task.id !== taskId) return task;

        const nextTitle =
          updatedData.title !== undefined
            ? String(updatedData.title).trim()
            : task.title;

        return {
          ...task,
          ...updatedData,
          id: task.id, // Strictly preserve original ID
          createdAt: task.createdAt, // Strictly preserve original creation timestamp
          title: nextTitle || task.title,
          description:
            updatedData.description !== undefined
              ? String(updatedData.description).trim()
              : task.description,
          category: updatedData.category || task.category,
          status: updatedData.status || task.status,
          priority: updatedData.priority || task.priority,
          dueDate: updatedData.dueDate !== undefined ? updatedData.dueDate : task.dueDate,
          updatedAt: new Date().toISOString(),
        };
      })
    );
  }, [setTasks]);

  const deleteTask = useCallback((taskId) => {
    if (!taskId) return;
    setTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
  }, [setTasks]);

  const updateTaskStatus = useCallback((taskId, newStatus) => {
    if (!taskId) return;
    const validStatuses = ['Todo', 'In Progress', 'Completed'];
    if (!validStatuses.includes(newStatus)) {
      console.warn(`updateTaskStatus rejected: invalid status "${newStatus}".`);
      return;
    }

    setTasks((prevTasks) =>
      prevTasks.map((task) =>
        task.id === taskId
          ? {
              ...task,
              status: newStatus,
              updatedAt: new Date().toISOString(),
            }
          : task
      )
    );
  }, [setTasks]);

  // Reset to initial sample data helper
  const resetToSampleData = useCallback(() => {
    setTasks(initialTasks);
  }, [setTasks]);

  // Modal open / close handlers
  const openCreateModal = useCallback(() => {
    setEditingTask(null);
    setIsTaskModalOpen(true);
  }, []);

  const openEditModal = useCallback((task) => {
    if (!task) return;
    setEditingTask(task);
    setIsTaskModalOpen(true);
  }, []);

  const closeTaskModal = useCallback(() => {
    setIsTaskModalOpen(false);
    setEditingTask(null);
  }, []);

  const promptDeleteTask = useCallback((task) => {
    if (!task) return;
    setDeletingTask(task);
  }, []);

  const closeDeleteDialog = useCallback(() => {
    setDeletingTask(null);
  }, []);

  const confirmDeleteTask = useCallback(() => {
    if (deletingTask && deletingTask.id) {
      deleteTask(deletingTask.id);
      setDeletingTask(null);
    }
  }, [deletingTask, deleteTask]);

  const value = {
    tasks,
    stats,
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    priorityFilter,
    setPriorityFilter,
    filteredTasks,
    addTask,
    updateTask,
    deleteTask,
    updateTaskStatus,
    resetToSampleData,
    // Modal & Dialog state
    isTaskModalOpen,
    editingTask,
    openCreateModal,
    openEditModal,
    closeTaskModal,
    deletingTask,
    promptDeleteTask,
    closeDeleteDialog,
    confirmDeleteTask,
  };

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
}
