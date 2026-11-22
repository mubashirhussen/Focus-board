import { apiClient } from './api';

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
};
