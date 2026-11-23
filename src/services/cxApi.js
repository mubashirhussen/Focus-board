import { apiClient } from './api.js';

export const cxApi = {
  // Feedback
  submitFeedback: (data) => apiClient.post('/cx/feedback', data),
  listFeedback: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiClient.get(qs ? `/cx/feedback?${qs}` : '/cx/feedback');
  },
  getFeedback: (id) => apiClient.get(`/cx/feedback/${id}`),
  updateFeedback: (id, data) => apiClient.patch(`/cx/feedback/${id}`, data),
  deleteFeedback: (id) => apiClient.delete(`/cx/feedback/${id}`),

  // Categories
  getCategories: (organizationId = null) => {
    const url = organizationId ? `/cx/categories?organization_id=${organizationId}` : '/cx/categories';
    return apiClient.get(url);
  },
  createCategory: (data) => apiClient.post('/cx/categories', data),

  // Metrics & Dashboard
  getMetrics: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiClient.get(qs ? `/cx/metrics?${qs}` : '/cx/metrics');
  },
  getDashboard: (workspaceId = null, days = 30) => {
    const params = new URLSearchParams();
    if (workspaceId) params.append('workspace_id', workspaceId);
    if (days) params.append('days', days);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/cx/dashboard${qs}`);
  },

  // Insights & Recommendations
  listInsights: (workspaceId = null) => {
    const url = workspaceId ? `/cx/insights?workspace_id=${workspaceId}` : '/cx/insights';
    return apiClient.get(url);
  },
  detectInsights: (workspaceId = null) => {
    const url = workspaceId ? `/cx/insights/detect?workspace_id=${workspaceId}` : '/cx/insights/detect';
    return apiClient.post(url);
  },
  listRecommendations: (workspaceId = null) => {
    const url = workspaceId ? `/cx/recommendations?workspace_id=${workspaceId}` : '/cx/recommendations';
    return apiClient.get(url);
  },
  convertRecommendation: (recommendationId, data = {}) =>
    apiClient.post(`/cx/recommendations/${recommendationId}/convert`, data),

  // Surveys
  createSurvey: (data) => apiClient.post('/cx/surveys', data),
  listSurveys: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiClient.get(qs ? `/cx/surveys?${qs}` : '/cx/surveys');
  },
  getSurvey: (surveyId) => apiClient.get(`/cx/surveys/${surveyId}`),
  submitSurveyResponse: (surveyId, data) => apiClient.post(`/cx/surveys/${surveyId}/responses`, data),

  // Customer Journey
  trackJourneyEvent: (data) => apiClient.post('/cx/journey/events', data),
  listJourneyEvents: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiClient.get(qs ? `/cx/journey/events?${qs}` : '/cx/journey/events');
  },
};
