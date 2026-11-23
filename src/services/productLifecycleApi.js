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
  getIdea: (id) => apiClient.get(`/product-lifecycle/ideas/${id}`),
  createIdea: (payload) => apiClient.post('/product-lifecycle/ideas', payload),
  updateIdea: (id, payload) => apiClient.patch(`/product-lifecycle/ideas/${id}`, payload),
  deleteIdea: (id) => apiClient.delete(`/product-lifecycle/ideas/${id}`),
  convertIdea: (id, payload) => apiClient.post(`/product-lifecycle/ideas/${id}/convert`, payload),

  // Feature Requests & Demand Hub
  listFeatureRequests: (params = {}) => apiClient.get('/product-lifecycle/feature-requests', { params }),
  getFeatureRequest: (id) => apiClient.get(`/product-lifecycle/feature-requests/${id}`),
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
  updateInitiative: (id, payload) => apiClient.patch(`/product-lifecycle/initiatives/${id}`, payload),
  deleteInitiative: (id) => apiClient.delete(`/product-lifecycle/initiatives/${id}`),

  listRoadmapItems: (params = {}) => apiClient.get('/product-lifecycle/roadmap', { params }),
  createRoadmapItem: (payload) => apiClient.post('/product-lifecycle/roadmap', payload),
  updateRoadmapItem: (id, payload) => apiClient.patch(`/product-lifecycle/roadmap/${id}`, payload),
  deleteRoadmapItem: (id) => apiClient.delete(`/product-lifecycle/roadmap/${id}`),
  reorderRoadmapItems: (payload) => apiClient.post('/product-lifecycle/roadmap/reorder', payload),

  // Roadmap Dependencies
  listRoadmapDependencies: (params = {}) => apiClient.get('/product-lifecycle/roadmap/dependencies', { params }),
  createRoadmapDependency: (payload) => apiClient.post('/product-lifecycle/roadmap/dependencies', payload),
  deleteRoadmapDependency: (id) => apiClient.delete(`/product-lifecycle/roadmap/dependencies/${id}`),

  // Experiments & A/B Testing
  listExperiments: (params = {}) => apiClient.get('/product-lifecycle/experiments', { params }),
  getExperiment: (id) => apiClient.get(`/product-lifecycle/experiments/${id}`),
  createExperiment: (payload) => apiClient.post('/product-lifecycle/experiments', payload),
  updateExperiment: (id, payload) => apiClient.patch(`/product-lifecycle/experiments/${id}`, payload),
  assignExperimentVariant: (expId) => apiClient.post(`/product-lifecycle/experiments/${expId}/assign`),
  trackExperimentEvent: (expId, eventName, metricValue = 1.0) =>
    apiClient.post(`/product-lifecycle/experiments/${expId}/events?event_name=${eventName}&metric_value=${metricValue}`),
  getExperimentAnalysis: (id) => apiClient.get(`/product-lifecycle/experiments/${id}/analysis`),

  // Releases
  listReleases: (params = {}) => apiClient.get('/product-lifecycle/releases', { params }),
  createRelease: (payload) => apiClient.post('/product-lifecycle/releases', payload),
  updateRelease: (id, payload) => apiClient.patch(`/product-lifecycle/releases/${id}`, payload),
  deleteRelease: (id) => apiClient.delete(`/product-lifecycle/releases/${id}`),
  getReleaseReadiness: (id) => apiClient.get(`/product-lifecycle/releases/${id}/readiness`),

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
