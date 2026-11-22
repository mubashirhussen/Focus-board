import { apiClient } from './api';

export const workflowApi = {
  getWorkflows: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/workflows${query}`);
  },
  createWorkflow: (data, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/workflows${query}`, data);
  },
  toggleWorkflow: (id) => apiClient.patch(`/workflows/${id}/toggle`, {}),
  deleteWorkflow: (id) => apiClient.delete(`/workflows/${id}`),
  testWorkflow: (id) => apiClient.post(`/workflows/${id}/test`, {}),
};
