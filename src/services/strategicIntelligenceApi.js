import { apiClient } from './api.js';

export const strategicIntelligenceApi = {
  getOverview: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/overview?workspace_id=${workspaceId}` : '/strategy/overview';
    return apiClient.get(url);
  },

  listPlans: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/plans?workspace_id=${workspaceId}` : '/strategy/plans';
    return apiClient.get(url);
  },
  createPlan: (data) => apiClient.post('/strategy/plans', data),
  updatePlan: (id, data) => apiClient.patch(`/strategy/plans/${id}`, data),

  listGoals: (planId = null, workspaceId = null) => {
    const params = new URLSearchParams();
    if (planId) params.append('plan_id', planId);
    if (workspaceId) params.append('workspace_id', workspaceId);
    const qs = params.toString();
    return apiClient.get(qs ? `/strategy/goals?${qs}` : '/strategy/goals');
  },
  createGoal: (data) => apiClient.post('/strategy/goals', data),
  updateGoal: (id, data) => apiClient.patch(`/strategy/goals/${id}`, data),

  listInitiatives: (goalId = null, workspaceId = null) => {
    const params = new URLSearchParams();
    if (goalId) params.append('goal_id', goalId);
    if (workspaceId) params.append('workspace_id', workspaceId);
    const qs = params.toString();
    return apiClient.get(qs ? `/strategy/initiatives?${qs}` : '/strategy/initiatives');
  },
  createInitiative: (data) => apiClient.post('/strategy/initiatives', data),
  updateInitiative: (id, data) => apiClient.patch(`/strategy/initiatives/${id}`, data),

  listMarketIntelligence: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/market-intel?workspace_id=${workspaceId}` : '/strategy/market-intel';
    return apiClient.get(url);
  },
  createMarketIntelligence: (data) => apiClient.post('/strategy/market-intel', data),

  listSignals: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/signals?workspace_id=${workspaceId}` : '/strategy/signals';
    return apiClient.get(url);
  },
  createSignal: (data) => apiClient.post('/strategy/signals', data),

  listCompetitors: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/competitors?workspace_id=${workspaceId}` : '/strategy/competitors';
    return apiClient.get(url);
  },
  createCompetitor: (data) => apiClient.post('/strategy/competitors', data),
  updateCompetitor: (id, data) => apiClient.patch(`/strategy/competitors/${id}`, data),

  listSwot: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/swot?workspace_id=${workspaceId}` : '/strategy/swot';
    return apiClient.get(url);
  },
  createSwot: (data) => apiClient.post('/strategy/swot', data),

  listMarketSizing: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/market-sizing?workspace_id=${workspaceId}` : '/strategy/market-sizing';
    return apiClient.get(url);
  },
  createMarketSizing: (data) => apiClient.post('/strategy/market-sizing', data),

  listOpportunities: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/opportunities?workspace_id=${workspaceId}` : '/strategy/opportunities';
    return apiClient.get(url);
  },
  createOpportunity: (data) => apiClient.post('/strategy/opportunities', data),
  updateOpportunity: (id, data) => apiClient.patch(`/strategy/opportunities/${id}`, data),

  listScenarios: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/scenarios?workspace_id=${workspaceId}` : '/strategy/scenarios';
    return apiClient.get(url);
  },
  createScenario: (data) => apiClient.post('/strategy/scenarios', data),
  compareScenarios: (scenarioIds = null, workspaceId = null) => {
    const url = workspaceId ? `/strategy/scenarios/compare?workspace_id=${workspaceId}` : '/strategy/scenarios/compare';
    return apiClient.post(url, scenarioIds);
  },

  listDecisions: (workspaceId = null) => {
    const url = workspaceId ? `/strategy/decisions?workspace_id=${workspaceId}` : '/strategy/decisions';
    return apiClient.get(url);
  },
  createDecision: (data) => apiClient.post('/strategy/decisions', data),

  listKPIs: (category = null, status = null, workspaceId = null) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (status) params.append('status', status);
    if (workspaceId) params.append('workspace_id', workspaceId);
    const qs = params.toString();
    return apiClient.get(qs ? `/strategy/kpis?${qs}` : '/strategy/kpis');
  },
  createKPI: (data) => apiClient.post('/strategy/kpis', data),
  updateKPI: (id, data) => apiClient.patch(`/strategy/kpis/${id}`, data),
  recordKPIValue: (id, data) => apiClient.post(`/strategy/kpis/${id}/values`, data),

  aiAnalyze: (req = {}) => apiClient.post('/strategy/ai/analyze', req),
};
