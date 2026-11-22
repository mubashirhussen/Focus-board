import { apiClient } from './api.js';

export const userPrivacyApi = {
  exportData: () => apiClient.get('/auth/export-data'),
  deleteAccount: () => apiClient.delete('/auth/me'),
  getAuditLogs: (params = {}) => {
    const query = new URLSearchParams();
    if (params.event_type) query.append('event_type', params.event_type);
    if (params.resource_type) query.append('resource_type', params.resource_type);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);
    const queryString = query.toString();
    return apiClient.get(`/audit-logs${queryString ? `?${queryString}` : ''}`);
  },
};
