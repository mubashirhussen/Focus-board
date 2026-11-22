import React, { createContext, useMemo, useState, useEffect, useCallback } from 'react';
import { initialTasks } from '../data/initialTasks';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { calculateStats, filterTasks } from '../utils/taskHelpers';
import { APP_CONFIG } from '../app/appConfig';
import { taskApi } from '../services/taskApi';
import { useAuth } from './AuthContext';

export const TaskContext = createContext(null);

export function TaskProvider({ children }) {
  const { isAuthenticated, token } = useAuth();

  // 1. Local Persistent Task State (For offline / guest mode)
  const [localTasks, setLocalTasks] = useLocalStorage(APP_CONFIG.storageKey, initialTasks);
  
  // Remote tasks state for authenticated users
  const [remoteTasks, setRemoteTasks] = useState([]);
  const [isSyncing, setIsSyncing] = useState(false);

  // Active tasks based on authentication mode
  const tasks = isAuthenticated ? remoteTasks : localTasks;

  // Sync tasks from backend when user logs in
  const fetchRemoteTasks = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsSyncing(true);
    try {
      const data = await taskApi.getTasks();
      // Format backend response with camelCase aliases if needed
      const formatted = (data || []).map((t) => ({
        id: t.id,
        title: t.title,
        description: t.description || '',
        category: t.category,
        status: t.status,
        priority: t.priority,
        dueDate: t.due_date || t.dueDate || '',
        createdAt: t.created_at || t.createdAt,
        updatedAt: t.updated_at || t.updatedAt,
        completedAt: t.completed_at || t.completedAt,
      }));
      setRemoteTasks(formatted);
    } catch (err) {
      console.warn('Failed to fetch remote tasks from API, falling back to local cache:', err);
    } finally {
      setIsSyncing(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchRemoteTasks();
    }
  }, [isAuthenticated, fetchRemoteTasks]);

  // 2. Filter & Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [priorityFilter, setPriorityFilter] = useState('All');

  // 3. Modals & Dialog State
  const [isTaskModalOpen, setIsTaskModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [deletingTask, setDeletingTask] = useState(null);

  // 4. Derived Statistics (Dynamically derived from active tasks)
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
  const addTask = useCallback(async (taskData) => {
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

    if (isAuthenticated) {
      // Optimistic update
      setRemoteTasks((prev) => [newTask, ...prev]);
      try {
        const created = await taskApi.createTask(newTask);
        setRemoteTasks((prev) =>
          prev.map((t) => (t.id === newTask.id ? { ...t, id: created.id } : t))
        );
      } catch (err) {
        console.error('API createTask error:', err);
      }
    } else {
      setLocalTasks((prevTasks) => [newTask, ...prevTasks]);
    }

    return newTask;
  }, [isAuthenticated, setLocalTasks]);

  const updateTask = useCallback(async (taskId, updatedData) => {
    if (!taskId) {
      console.warn('updateTask rejected: missing taskId.');
      return;
    }

    const updateUpdater = (prevTasks) =>
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
      });

    if (isAuthenticated) {
      setRemoteTasks(updateUpdater);
      try {
        await taskApi.updateTask(taskId, updatedData);
      } catch (err) {
        console.error('API updateTask error:', err);
      }
    } else {
      setLocalTasks(updateUpdater);
    }
  }, [isAuthenticated, setLocalTasks]);

  const deleteTask = useCallback(async (taskId) => {
    if (!taskId) return;

    if (isAuthenticated) {
      setRemoteTasks((prev) => prev.filter((task) => task.id !== taskId));
      try {
        await taskApi.deleteTask(taskId);
      } catch (err) {
        console.error('API deleteTask error:', err);
      }
    } else {
      setLocalTasks((prevTasks) => prevTasks.filter((task) => task.id !== taskId));
    }
  }, [isAuthenticated, setLocalTasks]);

  const updateTaskStatus = useCallback(async (taskId, newStatus) => {
    if (!taskId) return;
    const validStatuses = ['Todo', 'In Progress', 'Completed'];
    if (!validStatuses.includes(newStatus)) {
      console.warn(`updateTaskStatus rejected: invalid status "${newStatus}".`);
      return;
    }

    await updateTask(taskId, { status: newStatus });
  }, [updateTask]);

  // Reset to initial sample data helper
  const resetToSampleData = useCallback(() => {
    if (isAuthenticated) {
      // In authenticated mode, seed initial tasks to user account
      initialTasks.forEach(async (task) => {
        try {
          await taskApi.createTask(task);
        } catch {
          // ignore duplicate
        }
      });
      fetchRemoteTasks();
    } else {
      setLocalTasks(initialTasks);
    }
  }, [isAuthenticated, fetchRemoteTasks, setLocalTasks]);

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
    isSyncing,
    fetchRemoteTasks,
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
