import { apiClient } from './api.js';

export const billingApi = {
  getPlans: () => apiClient.get('/billing/plans'),
  getSubscription: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/billing/subscription${query}`);
  },
  checkout: (planId, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/billing/checkout${query}`, { plan_id: planId });
  },
  changePlan: (planId, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/billing/change-plan${query}`, { plan_id: planId });
  },
  cancelSubscription: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/billing/cancel${query}`, {});
  },
  getUsage: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/billing/usage${query}`);
  },
};
