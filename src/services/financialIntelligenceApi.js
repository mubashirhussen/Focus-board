import { apiClient } from './api.js';

export const financialIntelligenceApi = {
  getOverview: (tenantId = 'default', workspaceId) => {
    const q = workspaceId ? `?tenant_id=${tenantId}&workspace_id=${workspaceId}` : `?tenant_id=${tenantId}`;
    return apiClient.get(`/finance/overview${q}`);
  },

  listTransactions: (limit = 50, workspaceId) => {
    const q = workspaceId ? `?limit=${limit}&workspace_id=${workspaceId}` : `?limit=${limit}`;
    return apiClient.get(`/finance/transactions${q}`);
  },

  recordTransaction: (data) => apiClient.post('/finance/transactions', data),

  listCosts: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/costs${q}`);
  },

  recordCost: (data) => apiClient.post('/finance/costs', data),

  listBudgets: (tenantId = 'default', workspaceId) => {
    const q = workspaceId ? `?tenant_id=${tenantId}&workspace_id=${workspaceId}` : `?tenant_id=${tenantId}`;
    return apiClient.get(`/finance/budgets${q}`);
  },

  createBudget: (data) => apiClient.post('/finance/budgets', data),

  updateBudget: (budgetId, data) => apiClient.put(`/finance/budgets/${budgetId}`, data),

  listForecasts: (tenantId = 'default', workspaceId) => {
    const q = workspaceId ? `?tenant_id=${tenantId}&workspace_id=${workspaceId}` : `?tenant_id=${tenantId}`;
    return apiClient.get(`/finance/forecasts${q}`);
  },

  createForecast: (data) => apiClient.post('/finance/forecasts', data),

  exportReport: (reportType = 'EXECUTIVE_SUMMARY', format = 'CSV', workspaceId) =>
    apiClient.post('/finance/reports/export', { report_type: reportType, format, workspace_id: workspaceId }),

  // Data Sources
  listDataSources: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/data-sources${q}`);
  },

  createDataSource: (data) => apiClient.post('/finance/data-sources', data),

  testDataSourceConnection: (dataSourceId) => apiClient.post(`/finance/data-sources/${dataSourceId}/test-connection`),

  syncDataSource: (dataSourceId) => apiClient.post(`/finance/data-sources/${dataSourceId}/sync`),

  deleteDataSource: (dataSourceId) => apiClient.delete(`/finance/data-sources/${dataSourceId}`),

  // CSV Imports
  previewImport: (data) => apiClient.post('/finance/imports/preview', data),

  commitImport: (data) => apiClient.post('/finance/imports/commit', data),

  listImports: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/imports${q}`);
  },

  // Insights & Anomalies
  listInsights: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/insights${q}`);
  },

  generateInsights: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/finance/insights/generate${q}`);
  },

  updateInsight: (insightId, data) => apiClient.patch(`/finance/insights/${insightId}`, data),

  // Recommendations
  listRecommendations: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/recommendations${q}`);
  },

  actOnRecommendation: (recommendationId, data) => apiClient.post(`/finance/recommendations/${recommendationId}/action`, data),

  // Scenarios
  listScenarios: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/scenarios${q}`);
  },

  createScenario: (data) => apiClient.post('/finance/scenarios', data),

  compareScenarios: (workspaceId) => {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/finance/scenarios/compare${q}`);
  },

  // AI Analysis
  aiAnalyze: (data) => apiClient.post('/finance/ai/analyze', data),
};
