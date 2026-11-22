import { apiClient } from './api.js';

export const agentApi = {
  getAgents: () => apiClient.get('/ai-agent/agents'),
  getAgent: (id) => apiClient.get(`/ai-agent/agents/${id}`),
  createExecution: (data) => apiClient.post('/ai-agent/executions', data),
  getExecutions: (limit = 20) => apiClient.get(`/ai-agent/executions?limit=${limit}`),
  getExecution: (id) => apiClient.get(`/ai-agent/executions/${id}`),
  approveAction: (executionId, approvalId) =>
    apiClient.post(`/ai-agent/executions/${executionId}/approve?approval_id=${approvalId}`, {}),
  rejectAction: (executionId, approvalId) =>
    apiClient.post(`/ai-agent/executions/${executionId}/reject?approval_id=${approvalId}`, {}),
  cancelExecution: (executionId) =>
    apiClient.post(`/ai-agent/executions/${executionId}/cancel`, {}),
  getPreferences: () => apiClient.get('/ai-agent/preferences'),
  updatePreferences: (data) => apiClient.put('/ai-agent/preferences', data),
};
