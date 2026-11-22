import { apiClient } from './api.js';

export const innovationLabApi = {
  getOverview: () => apiClient.get('/innovation/overview'),

  listIdeas: (stage = null, category = null) => {
    let url = '/innovation/ideas?limit=50';
    if (stage) url += `&stage=${encodeURIComponent(stage)}`;
    if (category) url += `&category=${encodeURIComponent(category)}`;
    return apiClient.get(url);
  },
  getIdea: (ideaId) => apiClient.get(`/innovation/ideas/${ideaId}`),
  createIdea: (data) => apiClient.post('/innovation/ideas', data),
  updateIdea: (ideaId, data) => apiClient.patch(`/innovation/ideas/${ideaId}`, data),
  deleteIdea: (ideaId) => apiClient.delete(`/innovation/ideas/${ideaId}`),

  promoteToRoadmap: (ideaId, data = { roadmap_category: 'Innovation', target_status: 'PLANNED' }) =>
    apiClient.post(`/innovation/ideas/${ideaId}/promote-to-roadmap`, data),

  listHypotheses: (ideaId = null) => {
    const url = ideaId ? `/innovation/hypotheses?idea_id=${ideaId}` : '/innovation/hypotheses';
    return apiClient.get(url);
  },
  createHypothesis: (data) => apiClient.post('/innovation/hypotheses', data),
  updateHypothesis: (hypoId, data) => apiClient.patch(`/innovation/hypotheses/${hypoId}`, data),

  listExperiments: (ideaId = null, status = null) => {
    let url = '/innovation/experiments?';
    if (ideaId) url += `idea_id=${ideaId}&`;
    if (status) url += `status=${status}&`;
    return apiClient.get(url.replace(/&$/, ''));
  },
  createExperiment: (data) => apiClient.post('/innovation/experiments', data),
  updateExperiment: (expId, data) => apiClient.patch(`/innovation/experiments/${expId}`, data),

  getExperimentResults: (expId) => apiClient.get(`/innovation/experiments/${expId}/results`),
  attachExperimentResult: (expId, data) => apiClient.post(`/innovation/experiments/${expId}/results`, data),

  listPrototypes: (ideaId = null) => {
    const url = ideaId ? `/innovation/prototypes?idea_id=${ideaId}` : '/innovation/prototypes';
    return apiClient.get(url);
  },
  createPrototype: (data) => apiClient.post('/innovation/prototypes', data),
  updatePrototype: (protoId, data) => apiClient.patch(`/innovation/prototypes/${protoId}`, data),

  listValidations: (ideaId = null) => {
    const url = ideaId ? `/innovation/validations?idea_id=${ideaId}` : '/innovation/validations';
    return apiClient.get(url);
  },
  createValidation: (data) => apiClient.post('/innovation/validations', data),

  listPortfolios: () => apiClient.get('/innovation/portfolios'),
  createPortfolio: (data) => apiClient.post('/innovation/portfolios', data),
};
