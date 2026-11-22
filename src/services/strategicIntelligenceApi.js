import { apiClient } from './api.js';

export const strategicIntelligenceApi = {
  getOverview: () => apiClient.get('/strategy/overview'),

  listPlans: () => apiClient.get('/strategy/plans'),
  createPlan: (data) => apiClient.post('/strategy/plans', data),

  listGoals: (planId = null) => {
    const url = planId ? `/strategy/goals?plan_id=${planId}` : '/strategy/goals';
    return apiClient.get(url);
  },
  createGoal: (data) => apiClient.post('/strategy/goals', data),

  listInitiatives: (goalId = null) => {
    const url = goalId ? `/strategy/initiatives?goal_id=${goalId}` : '/strategy/initiatives';
    return apiClient.get(url);
  },
  createInitiative: (data) => apiClient.post('/strategy/initiatives', data),

  listMarketIntelligence: () => apiClient.get('/strategy/market-intel'),
  createMarketIntelligence: (data) => apiClient.post('/strategy/market-intel', data),

  listSignals: () => apiClient.get('/strategy/signals'),
  createSignal: (data) => apiClient.post('/strategy/signals', data),

  listCompetitors: () => apiClient.get('/strategy/competitors'),
  createCompetitor: (data) => apiClient.post('/strategy/competitors', data),

  listSwot: () => apiClient.get('/strategy/swot'),
  createSwot: (data) => apiClient.post('/strategy/swot', data),

  listMarketSizing: () => apiClient.get('/strategy/market-sizing'),
  createMarketSizing: (data) => apiClient.post('/strategy/market-sizing', data),

  listOpportunities: () => apiClient.get('/strategy/opportunities'),
  createOpportunity: (data) => apiClient.post('/strategy/opportunities', data),

  listDecisions: () => apiClient.get('/strategy/decisions'),
  createDecision: (data) => apiClient.post('/strategy/decisions', data),
};
