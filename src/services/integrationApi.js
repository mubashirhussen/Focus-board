import { apiClient } from './api.js';

export const integrationApi = {
  getConnected: () => apiClient.get('/integrations'),
  getAvailable: (params) => {
    const query = new URLSearchParams(params || {}).toString();
    return apiClient.get(`/integrations/available${query ? `?${query}` : ''}`);
  },
  getProviderDetails: (providerId) => apiClient.get(`/integrations/providers/${providerId}`),
  getGoogleConnectUrl: () => apiClient.get('/integrations/google/connect'),
  handleGoogleCallback: (code, state) => apiClient.get(`/integrations/google/callback?code=${code}&state=${state}`),
  getConnectUrl: (provider, redirectUri) => {
    const q = redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : '';
    return apiClient.get(`/integrations/${provider}/connect${q}`);
  },
  handleCallback: (provider, code, state) => apiClient.get(`/integrations/${provider}/callback?code=${code}&state=${state}`),
  connectApiKey: (payload) => apiClient.post('/integrations/api-key/connect', payload),
  testConnection: (id) => apiClient.post(`/integrations/${id}/test`),
  getHealth: (id) => apiClient.get(`/integrations/${id}/health`),
  reconnect: (id) => apiClient.post(`/integrations/${id}/reconnect`),
  syncNow: (id, payload) => apiClient.post(`/integrations/${id}/sync`, payload || {}),
  getSyncHistory: (id) => apiClient.get(`/integrations/${id}/sync-history`),
  getSyncLogs: (id) => apiClient.get(`/integrations/${id}/sync-logs`),
  getMappings: (id) => apiClient.get(`/integrations/${id}/mappings`),
  disconnect: (id) => apiClient.delete(`/integrations/${id}`),
};
export default integrationApi;
