import { apiClient } from './api.js';

export const clientPortalApi = {
  // Client Dashboard & Projects
  getDashboard: () =>
    apiClient.get('/client-portal/dashboard'),

  getProjectOverview: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}`),

  getProjectVisibility: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}/visibility`),

  updateProjectVisibility: (projectId, data) =>
    apiClient.put(`/client-portal/projects/${projectId}/visibility`, data),

  shareProject: (projectId, data) =>
    apiClient.post(`/client-portal/projects/${projectId}/share`, data),

  unshareProject: (projectId, guestUserId) =>
    apiClient.delete(`/client-portal/projects/${projectId}/guests/${guestUserId}`),

  // Invitations
  getInvitations: () =>
    apiClient.get('/client-portal/invitations'),

  createInvitation: (data) =>
    apiClient.post('/client-portal/invitations', data),

  resendInvitation: (invitationId) =>
    apiClient.post(`/client-portal/invitations/${invitationId}/resend`, {}),

  revokeInvitation: (invitationId) =>
    apiClient.post(`/client-portal/invitations/${invitationId}/revoke`, {}),

  acceptInvitation: (token) =>
    apiClient.post('/client-portal/invitations/accept', { token }),

  // Guest Management
  getGuests: (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.status) query.append('status', params.status);
    const qs = query.toString();
    return apiClient.get(`/client-portal/guests${qs ? `?${qs}` : ''}`);
  },

  suspendGuest: (guestUserId) =>
    apiClient.post(`/client-portal/guests/${guestUserId}/suspend`, {}),

  reactivateGuest: (guestUserId) =>
    apiClient.post(`/client-portal/guests/${guestUserId}/reactivate`, {}),

  revokeGuest: (guestUserId) =>
    apiClient.delete(`/client-portal/guests/${guestUserId}`),

  // Deliverables & Approvals
  getDeliverables: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}/deliverables`),

  createDeliverable: (projectId, data) =>
    apiClient.post(`/client-portal/projects/${projectId}/deliverables`, data),

  reviewDeliverable: (deliverableId, data) =>
    apiClient.post(`/client-portal/deliverables/${deliverableId}/review`, data),

  // Feedback & Comments
  getFeedback: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}/feedback`),

  submitFeedback: (projectId, data) =>
    apiClient.post(`/client-portal/projects/${projectId}/feedback`, data),

  getComments: (projectId, params = {}) => {
    const query = new URLSearchParams();
    if (params.task_id) query.append('task_id', params.task_id);
    if (params.deliverable_id) query.append('deliverable_id', params.deliverable_id);
    if (params.feedback_id) query.append('feedback_id', params.feedback_id);
    const qs = query.toString();
    return apiClient.get(`/client-portal/projects/${projectId}/comments${qs ? `?${qs}` : ''}`);
  },

  postComment: (projectId, data) =>
    apiClient.post(`/client-portal/projects/${projectId}/comments`, data),

  // Documents & Reports
  getDocuments: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}/documents`),

  getReports: (projectId) =>
    apiClient.get(`/client-portal/projects/${projectId}/reports`),

  createReport: (projectId, data) =>
    apiClient.post(`/client-portal/projects/${projectId}/reports`, data),

  // Settings & Audit Logs
  getSettings: () =>
    apiClient.get('/client-portal/settings'),

  updateSettings: (data) =>
    apiClient.put('/client-portal/settings', data),

  getAuditLogs: (params = {}) => {
    const query = new URLSearchParams();
    if (params.project_id) query.append('project_id', params.project_id);
    if (params.guest_user_id) query.append('guest_user_id', params.guest_user_id);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return apiClient.get(`/client-portal/audit-logs${qs ? `?${qs}` : ''}`);
  },
};
