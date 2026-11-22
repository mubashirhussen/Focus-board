import { apiClient } from './api.js';

export const financialIntelligenceApi = {
  getOverview: (tenantId = 'default') => apiClient.get(`/finance/overview?tenant_id=${tenantId}`),

  listTransactions: (limit = 50) => apiClient.get(`/finance/transactions?limit=${limit}`),

  recordTransaction: (data) => apiClient.post('/finance/transactions', data),

  listCosts: () => apiClient.get('/finance/costs'),

  recordCost: (data) => apiClient.post('/finance/costs', data),

  listBudgets: (tenantId = 'default') => apiClient.get(`/finance/budgets?tenant_id=${tenantId}`),

  createBudget: (data) => apiClient.post('/finance/budgets', data),

  updateBudget: (budgetId, data) => apiClient.put(`/finance/budgets/${budgetId}`, data),

  listForecasts: (tenantId = 'default') => apiClient.get(`/finance/forecasts?tenant_id=${tenantId}`),

  createForecast: (data) => apiClient.post('/finance/forecasts', data),

  exportReport: (reportType = 'EXECUTIVE_SUMMARY', format = 'CSV') =>
    apiClient.post('/finance/reports/export', { report_type: reportType, format }),
};
