import { apiClient } from './api.js';

export const productLifecycleApi = {
  // Overview
  getOverview: () => apiClient.get('/product-lifecycle/overview'),

  // Discoveries
  listDiscoveries: (params = {}) => apiClient.get('/product-lifecycle/discoveries', { params }),
  createDiscovery: (payload) => apiClient.post('/product-lifecycle/discoveries', payload),

  // Ideas
  listIdeas: (params = {}) => apiClient.get('/product-lifecycle/ideas', { params }),
  createIdea: (payload) => apiClient.post('/product-lifecycle/ideas', payload),

  // Feature Requests & Demand Hub
  listFeatureRequests: (params = {}) => apiClient.get('/product-lifecycle/feature-requests', { params }),
  createFeatureRequest: (payload) => apiClient.post('/product-lifecycle/feature-requests', payload),
  mergeFeatureRequests: (sourceId, targetId) =>
    apiClient.post(`/product-lifecycle/feature-requests/${sourceId}/merge?target_id=${targetId}`),

  // Opportunities
  listOpportunities: () => apiClient.get('/product-lifecycle/opportunities'),
  createOpportunity: (payload) => apiClient.post('/product-lifecycle/opportunities', payload),

  // Prioritization Engine
  calculatePrioritization: (reach, impact, confidence, effort, ease = 3.0) =>
    apiClient.post(`/product-lifecycle/prioritization/calculate?reach=${reach}&impact=${impact}&confidence=${confidence}&effort=${effort}&ease=${ease}`),
  listPrioritizationItems: () => apiClient.get('/product-lifecycle/prioritization/items'),
  createPrioritizationItem: (payload) => apiClient.post('/product-lifecycle/prioritization/items', payload),

  // Initiatives & Roadmaps
  listInitiatives: () => apiClient.get('/product-lifecycle/initiatives'),
  createInitiative: (payload) => apiClient.post('/product-lifecycle/initiatives', payload),
  listRoadmapItems: () => apiClient.get('/product-lifecycle/roadmap'),
  createRoadmapItem: (payload) => apiClient.post('/product-lifecycle/roadmap', payload),

  // Experiments & A/B Testing
  listExperiments: () => apiClient.get('/product-lifecycle/experiments'),
  createExperiment: (payload) => apiClient.post('/product-lifecycle/experiments', payload),
  assignExperimentVariant: (expId) => apiClient.post(`/product-lifecycle/experiments/${expId}/assign`),
  trackExperimentEvent: (expId, eventName, metricValue = 1.0) =>
    apiClient.post(`/product-lifecycle/experiments/${expId}/events?event_name=${eventName}&metric_value=${metricValue}`),

  // Releases
  listReleases: () => apiClient.get('/product-lifecycle/releases'),
  createRelease: (payload) => apiClient.post('/product-lifecycle/releases', payload),

  // AI Product Assistant
  askAssistant: (query, contextType = 'PRODUCT_OVERVIEW') =>
    apiClient.post('/product-lifecycle/ai/query', { query, context_type: contextType }),
};

export default productLifecycleApi;
