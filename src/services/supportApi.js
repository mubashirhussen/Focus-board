import { apiClient } from './api.js';

export const supportApi = {
  // Support Tickets
  createTicket: (data) => apiClient.post('/support/tickets', data),
  getTickets: (status = null, category = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/support/tickets${qs}`);
  },
  getTicketMessages: (ticketId) => apiClient.get(`/support/tickets/${ticketId}/messages`),
  createTicketMessage: (ticketId, message, isInternalNote = false) =>
    apiClient.post(`/support/tickets/${ticketId}/messages`, {
      message,
      is_internal_note: isInternalNote,
    }),
  updateTicket: (ticketId, data) => apiClient.patch(`/support/tickets/${ticketId}`, data),

  // Knowledge Base
  getKBCategories: () => apiClient.get('/support/knowledge-base/categories'),
  getKBArticles: (categoryId = null, query = null) => {
    const params = new URLSearchParams();
    if (categoryId) params.append('category_id', categoryId);
    if (query) params.append('q', query);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/support/knowledge-base/articles${qs}`);
  },
  voteKBArticle: (articleId, helpful = true) =>
    apiClient.post(`/support/knowledge-base/articles/${articleId}/vote`, { helpful }),

  // Roadmap & Upvoting
  getRoadmap: (status = null, category = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (category) params.append('category', category);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get(`/support/roadmap${qs}`);
  },
  voteRoadmap: (itemId) => apiClient.post(`/support/roadmap/${itemId}/vote`, {}),
  createRoadmapItem: (data) => apiClient.post('/support/roadmap', data),

  // Customer Health Score
  getCustomerHealth: () => apiClient.get('/support/customer-health'),
};
