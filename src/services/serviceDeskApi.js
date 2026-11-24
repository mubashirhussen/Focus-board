import { apiClient } from './api.js';

export const serviceDeskApi = {
  // Tickets
  getTickets: (params = {}) => {
    const query = new URLSearchParams();
    if (params.view) query.append('view', params.view);
    if (params.status) query.append('status', params.status);
    if (params.priority) query.append('priority', params.priority);
    if (params.category_id) query.append('category_id', params.category_id);
    if (params.team_id) query.append('team_id', params.team_id);
    if (params.agent_id) query.append('agent_id', params.agent_id);
    if (params.search) query.append('search', params.search);
    if (params.skip !== undefined) query.append('skip', params.skip);
    if (params.limit !== undefined) query.append('limit', params.limit);
    const qs = query.toString();
    return apiClient.get(`/service-desk/tickets${qs ? `?${qs}` : ''}`);
  },

  getTicketDetail: (ticketId) =>
    apiClient.get(`/service-desk/tickets/${ticketId}`),

  createTicket: (data) =>
    apiClient.post('/service-desk/tickets', data),

  assignTicket: (ticketId, data) =>
    apiClient.post(`/service-desk/tickets/${ticketId}/assign`, data),

  updateTicketStatus: (ticketId, data) =>
    apiClient.post(`/service-desk/tickets/${ticketId}/status`, data),

  escalateTicket: (ticketId, data) =>
    apiClient.post(`/service-desk/tickets/${ticketId}/escalate`, data),

  // Conversations & Notes
  getTicketComments: (ticketId) =>
    apiClient.get(`/service-desk/tickets/${ticketId}/comments`),

  addTicketComment: (ticketId, data) =>
    apiClient.post(`/service-desk/tickets/${ticketId}/comments`, data),

  // Categories & SLA Policies
  getCategories: () =>
    apiClient.get('/service-desk/categories'),

  createCategory: (data) =>
    apiClient.post('/service-desk/categories', data),

  getSLAPolicies: () =>
    apiClient.get('/service-desk/sla-policies'),

  createSLAPolicy: (data) =>
    apiClient.post('/service-desk/sla-policies', data),

  // Escalation Rules & Monitoring
  getEscalationRules: () =>
    apiClient.get('/service-desk/escalation-rules'),

  createEscalationRule: (data) =>
    apiClient.post('/service-desk/escalation-rules', data),

  recalculateSLAs: () =>
    apiClient.post('/service-desk/sla/recalculate', {}),

  // Dashboard & Reporting
  getDashboard: () =>
    apiClient.get('/service-desk/dashboard'),

  getPerformanceReports: () =>
    apiClient.get('/service-desk/reports/performance'),
};
