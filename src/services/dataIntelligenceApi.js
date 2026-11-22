import { apiClient } from './api.js';

export const dataIntelligenceApi = {
  getOverview: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/overview?workspace_id=${workspaceId}` : '/data-intelligence/overview';
    return apiClient.get(url);
  },

  listDatasets: () => apiClient.get('/data-intelligence/datasets'),

  listPipelines: () => apiClient.get('/data-intelligence/pipelines'),
  runPipeline: (pipelineId) => apiClient.post(`/data-intelligence/pipelines/${pipelineId}/run`),

  listDashboards: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/dashboards?workspace_id=${workspaceId}` : '/data-intelligence/dashboards';
    return apiClient.get(url);
  },
  getDashboard: (dashboardId) => apiClient.get(`/data-intelligence/dashboards/${dashboardId}`),
  createDashboard: (data) => apiClient.post('/data-intelligence/dashboards', data),
  deleteDashboard: (dashboardId) => apiClient.delete(`/data-intelligence/dashboards/${dashboardId}`),

  listReports: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/reports?workspace_id=${workspaceId}` : '/data-intelligence/reports';
    return apiClient.get(url);
  },
  createReport: (data) => apiClient.post('/data-intelligence/reports', data),
  executeReport: (reportId) => apiClient.post(`/data-intelligence/reports/${reportId}/run`),

  listQualityRules: () => apiClient.get('/data-intelligence/quality/rules'),

  queryAiAssistant: (prompt, workspaceId = null) =>
    apiClient.post('/data-intelligence/assistant/query', { prompt, workspace_id: workspaceId }),
};
