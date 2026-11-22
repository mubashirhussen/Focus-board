import { apiClient } from './api';

export const integrationApi = {
  getConnected: () => apiClient.get('/integrations'),
  getAvailable: () => apiClient.get('/integrations/available'),
  getGoogleConnectUrl: () => apiClient.get('/integrations/google/connect'),
  handleGoogleCallback: (code, state) => apiClient.get(`/integrations/google/callback?code=${code}&state=${state}`),
  disconnect: (id) => apiClient.delete(`/integrations/${id}`),
};
