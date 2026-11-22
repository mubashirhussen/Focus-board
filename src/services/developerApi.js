import { apiClient } from './api.js';

export const developerApi = {
  getStats: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/developer/stats${query}`);
  },

  listApplications: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/developer/applications${query}`);
  },

  createApplication: (data, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/developer/applications${query}`, data);
  },

  updateApplication: (appId, data) => {
    return apiClient.patch(`/developer/applications/${appId}`, data);
  },

  listCredentials: (appId) => {
    return apiClient.get(`/developer/applications/${appId}/credentials`);
  },

  createCredential: (data) => {
    return apiClient.post('/developer/credentials', data);
  },

  revokeCredential: (credId) => {
    return apiClient.delete(`/developer/credentials/${credId}`);
  },

  listWebhooks: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/developer/webhooks${query}`);
  },

  createWebhook: (data, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/developer/webhooks${query}`, data);
  },

  updateWebhook: (webhookId, data) => {
    return apiClient.patch(`/developer/webhooks/${webhookId}`, data);
  },

  deleteWebhook: (webhookId) => {
    return apiClient.delete(`/developer/webhooks/${webhookId}`);
  },

  testWebhook: (webhookId) => {
    return apiClient.post(`/developer/webhooks/${webhookId}/test`, {});
  },

  getWebhookDeliveries: (webhookId) => {
    return apiClient.get(`/developer/webhooks/${webhookId}/deliveries`);
  },
};
