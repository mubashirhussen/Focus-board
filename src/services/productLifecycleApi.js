import { apiClient } from './api.js';

export const productLifecycleApi = {
  // Overview
  getOverview: (params = {}) => apiClient.get('/product-lifecycle/overview', { params }),

  // Discoveries
  listDiscoveries: (params = {}) => apiClient.get('/product-lifecycle/discoveries', { params }),
  getDiscovery: (id) => apiClient.get(`/product-lifecycle/discoveries/${id}`),
  createDiscovery: (payload) => apiClient.post('/product-lifecycle/discoveries', payload),
  updateDiscovery: (id, payload) => apiClient.patch(`/product-lifecycle/discoveries/${id}`, payload),
  deleteDiscovery: (id) => apiClient.delete(`/product-lifecycle/discoveries/${id}`),

  // Ideas
  listIdeas: (params = {}) => apiClient.get('/product-lifecycle/ideas', { params }),
  createIdea: (payload) => apiClient.post('/product-lifecycle/ideas', payload),
  updateIdea: (id, payload) => apiClient.patch(`/product-lifecycle/ideas/${id}`, payload),
  deleteIdea: (id) => apiClient.delete(`/product-lifecycle/ideas/${id}`),

  // Feature Requests & Demand Hub
  listFeatureRequests: (params = {}) => apiClient.get('/product-lifecycle/feature-requests', { params }),
  createFeatureRequest: (payload) => apiClient.post('/product-lifecycle/feature-requests', payload),
  updateFeatureRequest: (id, payload) => apiClient.patch(`/product-lifecycle/feature-requests/${id}`, payload),
  mergeFeatureRequests: (sourceId, targetId) =>
    apiClient.post(`/product-lifecycle/feature-requests/${sourceId}/merge?target_id=${targetId}`),

  // Opportunities
  listOpportunities: (params = {}) => apiClient.get('/product-lifecycle/opportunities', { params }),
  createOpportunity: (payload) => apiClient.post('/product-lifecycle/opportunities', payload),

  // Prioritization Engine
  calculatePrioritization: (reach, impact, confidence, effort, ease = 3.0) =>
    apiClient.post(`/product-lifecycle/prioritization/calculate?reach=${reach}&impact=${impact}&confidence=${confidence}&effort=${effort}&ease=${ease}`),
  listPrioritizationItems: (params = {}) => apiClient.get('/product-lifecycle/prioritization/items', { params }),
  createPrioritizationItem: (payload) => apiClient.post('/product-lifecycle/prioritization/items', payload),

  // Initiatives & Roadmaps
  listInitiatives: (params = {}) => apiClient.get('/product-lifecycle/initiatives', { params }),
  createInitiative: (payload) => apiClient.post('/product-lifecycle/initiatives', payload),
  listRoadmapItems: (params = {}) => apiClient.get('/product-lifecycle/roadmap', { params }),
  createRoadmapItem: (payload) => apiClient.post('/product-lifecycle/roadmap', payload),

  // Experiments & A/B Testing
  listExperiments: (params = {}) => apiClient.get('/product-lifecycle/experiments', { params }),
  createExperiment: (payload) => apiClient.post('/product-lifecycle/experiments', payload),
  updateExperiment: (id, payload) => apiClient.patch(`/product-lifecycle/experiments/${id}`, payload),
  assignExperimentVariant: (expId) => apiClient.post(`/product-lifecycle/experiments/${expId}/assign`),
  trackExperimentEvent: (expId, eventName, metricValue = 1.0) =>
    apiClient.post(`/product-lifecycle/experiments/${expId}/events?event_name=${eventName}&metric_value=${metricValue}`),

  // Releases
  listReleases: (params = {}) => apiClient.get('/product-lifecycle/releases', { params }),
  createRelease: (payload) => apiClient.post('/product-lifecycle/releases', payload),

  // Decisions & Risks
  listDecisions: (params = {}) => apiClient.get('/product-lifecycle/decisions', { params }),
  createDecision: (payload) => apiClient.post('/product-lifecycle/decisions', payload),
  listRisks: (params = {}) => apiClient.get('/product-lifecycle/risks', { params }),
  createRisk: (payload) => apiClient.post('/product-lifecycle/risks', payload),

  // AI Product Assistant
  askAssistant: (query, contextType = 'PRODUCT_OVERVIEW') =>
    apiClient.post('/product-lifecycle/ai/query', { query, context_type: contextType }),

  // Explicit Demo Seed (Protected)
  seedDemoData: (params = {}) => apiClient.post('/product-lifecycle/seed-demo', null, { params }),
};

export default productLifecycleApi;
