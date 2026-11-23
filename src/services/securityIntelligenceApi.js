import { apiClient } from './api.js';

export const securityIntelligenceApi = {
  // Posture summary & Zero-Trust Score
  getPosture: (params = {}) => apiClient.get('/security-intelligence/posture', { params }),

  // Security Events & Logging
  listEvents: (params = {}) => apiClient.get('/security-intelligence/events', { params }),
  recordEvent: (payload) => apiClient.post('/security-intelligence/events', payload),

  // Threat Detection Rules
  listDetectionRules: (params = {}) => apiClient.get('/security-intelligence/detection-rules', { params }),
  createDetectionRule: (payload) => apiClient.post('/security-intelligence/detection-rules', payload),
  triggerThreatScan: (params = {}) => apiClient.post('/security-intelligence/threat-detection/run', null, { params }),

  // Security Alerts
  listAlerts: (params = {}) => apiClient.get('/security-intelligence/alerts', { params }),
  updateAlert: (alertId, payload) => apiClient.patch(`/security-intelligence/alerts/${alertId}`, payload),

  // Identity Risk Records
  listIdentityRisks: (params = {}) => apiClient.get('/security-intelligence/identity-risks', { params }),
  createIdentityRisk: (payload) => apiClient.post('/security-intelligence/identity-risks', payload),

  // Access Review Campaigns
  listAccessReviews: (params = {}) => apiClient.get('/security-intelligence/access-reviews', { params }),
  createAccessReview: (payload) => apiClient.post('/security-intelligence/access-reviews', payload),
  recordAccessDecision: (campaignId, recordId, payload) =>
    apiClient.patch(`/security-intelligence/access-reviews/${campaignId}/records/${recordId}`, payload),

  // Vulnerability Management
  listVulnerabilities: (params = {}) => apiClient.get('/security-intelligence/vulnerabilities', { params }),
  createVulnerability: (payload) => apiClient.post('/security-intelligence/vulnerabilities', payload),
  updateVulnerability: (vulnId, payload) => apiClient.patch(`/security-intelligence/vulnerabilities/${vulnId}`, payload),

  // Remediations
  listRemediations: (params = {}) => apiClient.get('/security-intelligence/remediations', { params }),
  createRemediation: (payload) => apiClient.post('/security-intelligence/remediations', payload),
  updateRemediation: (remediationId, payload) => apiClient.patch(`/security-intelligence/remediations/${remediationId}`, payload),

  // Zero Trust Policies & Evaluation
  listZeroTrustPolicies: (params = {}) => apiClient.get('/security-intelligence/zero-trust/policies', { params }),
  createZeroTrustPolicy: (payload) => apiClient.post('/security-intelligence/zero-trust/policies', payload),
  updateZeroTrustPolicy: (policyId, payload) => apiClient.patch(`/security-intelligence/zero-trust/policies/${policyId}`, payload),
  evaluateZeroTrustAccess: (payload) => apiClient.post('/security-intelligence/zero-trust/evaluate', payload),

  // Incident Containment Actions
  revokeSessions: (payload) => apiClient.post('/security-intelligence/actions/revoke-sessions', payload),
  quarantineEntity: (payload) => apiClient.post('/security-intelligence/actions/quarantine-entity', payload),

  // Grounded AI Security Assistant
  askAssistant: (query, contextType = 'SOC_OVERVIEW', workspaceId = null) =>
    apiClient.post('/security-intelligence/ai/query', { query, context_type: contextType, workspace_id: workspaceId }),
};

export default securityIntelligenceApi;
