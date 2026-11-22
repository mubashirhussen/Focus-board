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
    const queryString = query.toString();
    return apiClient.get(`/search${queryString ? `?${queryString}` : ''}`);
  },
};
