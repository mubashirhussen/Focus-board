import { api } from './api';

export const taskApi = {
  getTasks: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status && filters.status !== 'All') params.append('status', filters.status);
    if (filters.priority && filters.priority !== 'All') params.append('priority', filters.priority);
    if (filters.category && filters.category !== 'All') params.append('category', filters.category);
    if (filters.search) params.append('search', filters.search);

    const query = params.toString() ? `?${params.toString()}` : '';
    return api.get(`/tasks${query}`);
  },

  createTask: async (taskData) => {
    return api.post('/tasks', {
      id: taskData.id,
      title: taskData.title,
      description: taskData.description || '',
      category: taskData.category || 'Design',
      status: taskData.status || 'Todo',
      priority: taskData.priority || 'Medium',
      due_date: taskData.dueDate || '',
    });
  },

  updateTask: async (taskId, taskData) => {
    return api.put(`/tasks/${taskId}`, {
      title: taskData.title,
      description: taskData.description,
      category: taskData.category,
      status: taskData.status,
      priority: taskData.priority,
      due_date: taskData.dueDate,
    });
  },

  deleteTask: async (taskId) => {
    return api.delete(`/tasks/${taskId}`);
  },
};
