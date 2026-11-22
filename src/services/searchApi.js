import { apiClient } from './api.js';

export const searchApi = {
  search: (params = {}) => {
    const query = new URLSearchParams();
    if (params.q) query.append('q', params.q);
    if (params.type) query.append('type', params.type);
    if (params.status && params.status !== 'All') query.append('status', params.status);
    if (params.priority && params.priority !== 'All') query.append('priority', params.priority);
    if (params.category && params.category !== 'All') query.append('category', params.category);
    if (params.workspace_id) query.append('workspace_id', params.workspace_id);
    if (params.project_id) query.append('project_id', params.project_id);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.sort_order) query.append('sort_order', params.sort_order);
    const queryString = query.toString();
    return apiClient.get(`/search${queryString ? `?${queryString}` : ''}`);
  },

  getSuggestions: (q, limit = 5) => {
    return apiClient.get(`/search/suggestions?q=${encodeURIComponent(q)}&limit=${limit}`);
  },

  searchTasks: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/tasks${query ? `?${query}` : ''}`);
  },

  searchProjects: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/projects${query ? `?${query}` : ''}`);
  },

  searchTeams: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/teams${query ? `?${query}` : ''}`);
  },

  searchWorkspaces: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/workspaces${query ? `?${query}` : ''}`);
  },

  searchBoards: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/boards${query ? `?${query}` : ''}`);
  },

  searchMembers: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/members${query ? `?${query}` : ''}`);
  },

  searchComments: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return apiClient.get(`/search/comments${query ? `?${query}` : ''}`);
  },

  advancedFilter: (payload) => {
    return apiClient.post('/search/filter', payload);
  },

  getHistory: (limit = 20) => {
    return apiClient.get(`/search/history?limit=${limit}`);
  },

  deleteHistoryItem: (id) => {
    return apiClient.delete(`/search/history/${id}`);
  },

  clearHistory: () => {
    return apiClient.delete('/search/history');
  },

  getSavedSearches: (entityType) => {
    const q = entityType ? `?entity_type=${entityType}` : '';
    return apiClient.get(`/search/saved${q}`);
  },

  createSavedSearch: (payload) => {
    return apiClient.post('/search/saved', payload);
  },

  getSavedSearch: (id) => {
    return apiClient.get(`/search/saved/${id}`);
  },

  updateSavedSearch: (id, payload) => {
    return apiClient.put(`/search/saved/${id}`, payload);
  },

  deleteSavedSearch: (id) => {
    return apiClient.delete(`/search/saved/${id}`);
  },
};
