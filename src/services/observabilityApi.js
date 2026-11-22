import { apiClient } from './api.js';

export const observabilityApi = {
  getOverview: () => apiClient.get('/observability/overview'),
  listServices: () => apiClient.get('/observability/services'),

  listAlerts: (status = null) => {
    const url = status ? `/observability/alerts?status=${encodeURIComponent(status)}` : '/observability/alerts';
    return apiClient.get(url);
  },
  createAlert: (data) => apiClient.post('/observability/alerts', data),
  acknowledgeAlert: (alertId) => apiClient.post(`/observability/alerts/${alertId}/acknowledge`),
  resolveAlert: (alertId) => apiClient.post(`/observability/alerts/${alertId}/resolve`),

  listIncidents: (status = null) => {
    const url = status ? `/observability/incidents?status=${encodeURIComponent(status)}` : '/observability/incidents';
    return apiClient.get(url);
  },
  getIncident: (incidentId) => apiClient.get(`/observability/incidents/${incidentId}`),
  createIncident: (data) => apiClient.post('/observability/incidents', data),
  updateIncident: (incidentId, data) => apiClient.patch(`/observability/incidents/${incidentId}`, data),
  addActionItem: (incidentId, data) => apiClient.post(`/observability/incidents/${incidentId}/action-items`, data),
  createPostMortem: (incidentId, data) => apiClient.post(`/observability/incidents/${incidentId}/post-mortem`, data),

  runSupportDiagnostics: (workspaceId, checkType = 'FULL') =>
    apiClient.post('/observability/diagnostics/support', { workspace_id: workspaceId, check_type: checkType }),

  listMaintenance: () => apiClient.get('/observability/maintenance'),
  createMaintenance: (data) => apiClient.post('/observability/maintenance', data),
};
