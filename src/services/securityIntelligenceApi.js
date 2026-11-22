import { apiClient } from './api.js';

export const securityIntelligenceApi = {
  // Posture summary & Zero-Trust Score
  getPosture: () => apiClient.get('/security-intelligence/posture'),

  // Security Events & Logging
  listEvents: (params = {}) => apiClient.get('/security-intelligence/events', { params }),
  recordEvent: (payload) => apiClient.post('/security-intelligence/events', payload),

  // Threat Detection Rules
  listDetectionRules: () => apiClient.get('/security-intelligence/detection-rules'),
  createDetectionRule: (payload) => apiClient.post('/security-intelligence/detection-rules', payload),

  // Security Alerts
  listAlerts: (params = {}) => apiClient.get('/security-intelligence/alerts', { params }),
  updateAlert: (alertId, payload) => apiClient.patch(`/security-intelligence/alerts/${alertId}`, payload),

  // Identity Risk Records
  listIdentityRisks: () => apiClient.get('/security-intelligence/identity-risks'),

  // Access Review Campaigns
  listAccessReviews: () => apiClient.get('/security-intelligence/access-reviews'),
  createAccessReview: (payload) => apiClient.post('/security-intelligence/access-reviews', payload),
  recordAccessDecision: (campaignId, recordId, payload) =>
    apiClient.patch(`/security-intelligence/access-reviews/${campaignId}/records/${recordId}`, payload),

  // Vulnerability Management
  listVulnerabilities: (params = {}) => apiClient.get('/security-intelligence/vulnerabilities', { params }),
  createVulnerability: (payload) => apiClient.post('/security-intelligence/vulnerabilities', payload),
  updateVulnerability: (vulnId, payload) => apiClient.patch(`/security-intelligence/vulnerabilities/${vulnId}`, payload),

  // Remediations
  listRemediations: () => apiClient.get('/security-intelligence/remediations'),

  // Grounded AI Security Assistant
  askAssistant: (query, contextType = 'SOC_OVERVIEW') =>
    apiClient.post('/security-intelligence/ai/query', { query, context_type: contextType }),
};

export default securityIntelligenceApi;
