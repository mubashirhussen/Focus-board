import { apiClient } from './api.js';

export const projectPlanningApi = {
  // Planning Workspace & Settings
  getPlanningOverview: (projectId) =>
    apiClient.get(`/projects/${projectId}/planning`),

  updatePlanningSettings: (projectId, data) =>
    apiClient.put(`/projects/${projectId}/planning`, data),

  // Task Dependencies
  getDependencies: (projectId) =>
    apiClient.get(`/projects/${projectId}/planning/dependencies`),

  createDependency: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/planning/dependencies`, data),

  deleteDependency: (dependencyId) =>
    apiClient.delete(`/planning/dependencies/${dependencyId}`),

  // Critical Path Method (CPM)
  getCriticalPath: (projectId) =>
    apiClient.get(`/projects/${projectId}/critical-path`),

  recalculateCriticalPath: (projectId) =>
    apiClient.post(`/projects/${projectId}/critical-path/recalculate`, {}),

  // Baselines & Comparison
  getBaselines: (projectId) =>
    apiClient.get(`/projects/${projectId}/baselines`),

  createBaseline: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/baselines`, data),

  compareBaseline: (baselineId) =>
    apiClient.get(`/baselines/${baselineId}/comparison`),

  // Project Budget & Cost Records
  getBudget: (projectId) =>
    apiClient.get(`/projects/${projectId}/budget`),

  updateBudget: (projectId, data) =>
    apiClient.put(`/projects/${projectId}/budget`, data),

  recordCost: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/budget/costs`, data),

  // Schedule Forecasting
  getForecast: (projectId) =>
    apiClient.get(`/projects/${projectId}/forecast`),

  recalculateForecast: (projectId) =>
    apiClient.post(`/projects/${projectId}/forecast/recalculate`, {}),

  // What-If Scenarios & Simulations
  getScenarios: (projectId) =>
    apiClient.get(`/projects/${projectId}/scenarios`),

  createScenario: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/scenarios`, data),

  addScenarioChange: (scenarioId, data) =>
    apiClient.post(`/scenarios/${scenarioId}/changes`, data),

  simulateScenario: (scenarioId) =>
    apiClient.post(`/scenarios/${scenarioId}/simulate`, {}),

  applyScenario: (scenarioId) =>
    apiClient.post(`/scenarios/${scenarioId}/apply`, {}),

  // Aliases for convenience
  getScheduleSettings: (projectId) =>
    apiClient.get(`/projects/${projectId}/planning`),
  updateScheduleSettings: (projectId, data) =>
    apiClient.put(`/projects/${projectId}/planning`, data),
  getTaskDependencies: (projectId) =>
    apiClient.get(`/projects/${projectId}/planning/dependencies`),
  createTaskDependency: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/planning/dependencies`, data),
  deleteTaskDependency: (dependencyId) =>
    apiClient.delete(`/planning/dependencies/${dependencyId}`),
  calculateCriticalPath: (projectId) =>
    apiClient.post(`/projects/${projectId}/critical-path/recalculate`, {}),
  getBudgetSummary: (projectId) =>
    apiClient.get(`/projects/${projectId}/budget`),
  getCostRecords: (projectId) =>
    apiClient.get(`/projects/${projectId}/budget`),
  addCostRecord: (projectId, data) =>
    apiClient.post(`/projects/${projectId}/budget/costs`, data),
  getScheduleForecast: (projectId) =>
    apiClient.get(`/projects/${projectId}/forecast`),
  generateForecast: (projectId) =>
    apiClient.post(`/projects/${projectId}/forecast/recalculate`, {}),
};
