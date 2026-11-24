import { apiClient } from './api.js';

export const intelligenceApi = {
  getMetrics: () => apiClient.get('/intelligence/metrics'),
  getPatterns: () => apiClient.get('/intelligence/patterns'),
  getInsights: () => apiClient.get('/intelligence/insights'),
  getRecommendations: () => apiClient.get('/intelligence/recommendations'),
  submitFeedback: (insightId, feedbackType, notes = null) =>
    apiClient.post('/intelligence/feedback', {
      insight_id: insightId,
      feedback_type: feedbackType,
      notes,
    }),
  dismissInsight: (insightId) =>
    apiClient.post(`/intelligence/insights/${insightId}/dismiss`, {}),
  queryCoach: (message) =>
    apiClient.post('/intelligence/coach', { message }),
  getPreferences: () => apiClient.get('/intelligence/preferences'),
  updatePreferences: (data) =>
    apiClient.put('/intelligence/preferences', data),

  // Module B47: Predictive Project Intelligence extensions
  getOverview: () => apiClient.get('/intelligence/overview'),
  getProjectsHealth: () => apiClient.get('/intelligence/projects'),
  getProjectHealth: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/health`),
  getProjectForecast: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/forecast`),
  getProjectRisks: (projectId) => apiClient.get(`/intelligence/projects/${projectId}/risks`),
  getTaskRisk: (taskId) => apiClient.get(`/intelligence/tasks/${taskId}/risk`),
  getWorkload: () => apiClient.get('/intelligence/workload'),
  getProjectRecommendations: (status = null) => {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiClient.get(`/intelligence/project-recommendations${query}`);
  },
  acceptRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/accept`, {}),
  rejectRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/reject`, {}),
  completeRecommendation: (id) => apiClient.post(`/intelligence/recommendations/${id}/complete`, {}),
  getHistory: () => apiClient.get('/intelligence/history'),
  getSettings: () => apiClient.get('/intelligence/settings'),
  updateSettings: (data) => apiClient.put('/intelligence/settings', data),
  recalculateProject: (projectId) => apiClient.post(`/intelligence/recalculate/${projectId}`, {}),
};
