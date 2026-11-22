import { apiClient } from './api.js';

export const automationApi = {
  getOverview: (workspaceId = null) => {
    const url = workspaceId ? `/automation/overview?workspace_id=${workspaceId}` : '/automation/overview';
    return apiClient.get(url);
  },

  listWorkflows: (params = {}) => {
    const query = new URLSearchParams();
    if (params.workspaceId) query.append('workspace_id', params.workspaceId);
    if (params.status) query.append('status', params.status);
    if (params.isTemplate !== undefined) query.append('is_template', params.isTemplate);
    const qs = query.toString();
    return apiClient.get(`/automation/workflows${qs ? `?${qs}` : ''}`);
  },

  getWorkflow: (workflowId) => apiClient.get(`/automation/workflows/${workflowId}`),
  createWorkflow: (data) => apiClient.post('/automation/workflows', data),
  updateWorkflow: (workflowId, data) => apiClient.patch(`/automation/workflows/${workflowId}`, data),
  deleteWorkflow: (workflowId) => apiClient.delete(`/automation/workflows/${workflowId}`),
  getWorkflowVersions: (workflowId) => apiClient.get(`/automation/workflows/${workflowId}/versions`),

  triggerWorkflow: (workflowId, data = {}) =>
    apiClient.post(`/automation/workflows/${workflowId}/trigger`, {
      trigger_event: data.trigger_event || 'MANUAL',
      payload: data.payload || {},
      dry_run: data.dry_run || false,
    }),

  listExecutions: (params = {}) => {
    const query = new URLSearchParams();
    if (params.workflowId) query.append('workflow_id', params.workflowId);
    if (params.status) query.append('status', params.status);
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    const qs = query.toString();
    return apiClient.get(`/automation/executions${qs ? `?${qs}` : ''}`);
  },

  getExecution: (executionId) => apiClient.get(`/automation/executions/${executionId}`),
  getExecutionLogs: (executionId) => apiClient.get(`/automation/executions/${executionId}/logs`),

  listApprovals: (params = {}) => {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.executionId) query.append('execution_id', params.executionId);
    const qs = query.toString();
    return apiClient.get(`/automation/approvals${qs ? `?${qs}` : ''}`);
  },

  submitApprovalDecision: (approvalId, decision, comments = null) =>
    apiClient.post(`/automation/approvals/${approvalId}/decision`, { decision, comments }),

  generateWorkflowFromPrompt: (prompt, category = 'TASK') =>
    apiClient.post('/automation/assistant/generate', { prompt, category }),
};
