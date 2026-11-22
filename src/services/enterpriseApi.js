import { apiClient } from './api.js';

export const enterpriseApi = {
  getPolicies: () => apiClient.get('/enterprise/policies'),
  updatePolicy: (policyType, isEnabled, configJson = null) =>
    apiClient.put(`/enterprise/policies/${policyType}`, {
      policy_type: policyType,
      is_enabled: isEnabled,
      config_json: configJson,
    }),
  getRoles: () => apiClient.get('/enterprise/roles'),
  createRole: (roleData) => apiClient.post('/enterprise/roles', roleData),
  getDomains: () => apiClient.get('/enterprise/domains'),
  addDomain: (domainName) => apiClient.post('/enterprise/domains', { domain_name: domainName }),
  verifyDomain: (domainId) => apiClient.post(`/enterprise/domains/${domainId}/verify`, {}),
  setupMFA: () => apiClient.post('/enterprise/mfa/setup', {}),
  verifyMFA: (code) => apiClient.post('/enterprise/mfa/verify', { code }),
  disableMFA: (code) => apiClient.post('/enterprise/mfa/disable', { code }),
  exportAuditLogs: async () => {
    const token = localStorage.getItem('focusboard_token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    const response = await fetch(`${baseUrl}/enterprise/audit/export`, {
      method: 'GET',
      headers,
    });
    if (!response.ok) {
      throw new Error(`Failed to export audit logs (${response.status})`);
    }
    return await response.blob();
  },
};
