import { apiClient } from './api.js';

export const securityComplianceApi = {
  getOverview: () => apiClient.get('/security/overview'),

  listControls: (framework) => {
    const query = framework ? `?framework=${framework}` : '';
    return apiClient.get(`/security/controls${query}`);
  },

  updateControl: (controlId, data) => apiClient.put(`/security/controls/${controlId}`, data),

  listEvidence: (controlId) => apiClient.get(`/security/controls/${controlId}/evidence`),

  addEvidence: (controlId, data) => apiClient.post(`/security/controls/${controlId}/evidence`, data),

  listPolicies: () => apiClient.get('/security/policies'),

  createPolicy: (data) => apiClient.post('/security/policies', data),

  acknowledgePolicy: (policyId, version) =>
    apiClient.post(`/security/policies/${policyId}/acknowledge`, { version }),

  listRisks: () => apiClient.get('/security/risks'),

  createRisk: (data) => apiClient.post('/security/risks', data),

  updateRisk: (riskId, data) => apiClient.put(`/security/risks/${riskId}`, data),

  listIncidents: () => apiClient.get('/security/incidents'),

  createIncident: (data) => apiClient.post('/security/incidents', data),

  updateIncident: (incidentId, data) => apiClient.put(`/security/incidents/${incidentId}`, data),

  listVendors: () => apiClient.get('/security/vendors'),

  createVendor: (data) => apiClient.post('/security/vendors', data),

  listPrivacyRequests: () => apiClient.get('/security/privacy-requests'),

  createPrivacyRequest: (data) => apiClient.post('/security/privacy-requests', data),

  updatePrivacyRequest: (requestId, data) =>
    apiClient.put(`/security/privacy-requests/${requestId}`, data),

  getTrustCenterOverview: () => apiClient.get('/security/trust/overview'),

  getTrustCenterDocuments: () => apiClient.get('/security/trust/documents'),
};
