import { apiClient } from './api.js';

export const predictiveIntelligenceApi = {
  // Aggregated overview
  getOverview: () => apiClient.get('/intelligence/overview'),

  // Projects health
  getProjectsHealth: () => apiClient.get('/intelligence/projects'),
  getProjectHealth: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/health`),
  getProjectForecast: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/forecast`),
  getProjectRisks: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/risks`),

  // Task risk
  getTaskRisk: (taskId) => apiClient.get(`/intelligence/tasks/${taskId}/risk`),

  // Team workload
  getWorkload: () => apiClient.get('/intelligence/workload'),

  // AI Recommendations
  getRecommendations: (status = null) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient.get(`/intelligence/project-recommendations${query}`);
  },
  acceptRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/accept`, {}),
  rejectRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/reject`, {}),
  completeRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/complete`, {}),

  // Prediction history & accuracy
  getHistory: () => apiClient.get('/intelligence/history'),

  // Settings
  getSettings: () => apiClient.get('/intelligence/settings'),
  updateSettings: (data) => apiClient.put('/intelligence/settings', data),

  // Recalculate
  recalculateProject: (projectId) => apiClient.post(`/intelligence/recalculate/${projectId}`, {}),
};
