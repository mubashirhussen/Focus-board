import { apiClient } from './api.js';

export const growthApi = {
  getOnboarding: () => apiClient.get('/growth/onboarding'),
  updateOnboarding: (data) => apiClient.post('/growth/onboarding', data),
  trackEvent: (eventName, properties = {}) =>
    apiClient.post('/growth/events', { event_name: eventName, properties }),
  getActivationFunnel: () => apiClient.get('/growth/activation-funnel'),
  submitFeedback: (data) => apiClient.post('/growth/feedback', data),
  getFeedback: (status = null, category = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/growth/feedback${qs}`);
  },
  updateFeedback: (id, data) => apiClient.patch(`/growth/feedback/${id}`, data),
};
