import { apiClient } from './api.js';

export const regionalApi = {
  getSettings: () => apiClient.get('/regional/settings'),
  updateSettings: (data) => apiClient.put('/regional/settings', data),
  getLocales: () => apiClient.get('/regional/locales'),
};
