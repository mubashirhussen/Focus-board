import { apiClient } from './api.js';

export const dataIntelligenceApi = {
  getOverview: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/overview?workspace_id=${workspaceId}` : '/data-intelligence/overview';
    return apiClient.get(url);
  },

  // Data Sources
  listSources: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/sources?workspace_id=${workspaceId}` : '/data-intelligence/sources';
    return apiClient.get(url);
  },
  createSource: (data) => apiClient.post('/data-intelligence/sources', data),
  testSource: (sourceId) => apiClient.post(`/data-intelligence/sources/${sourceId}/test`),

  // Datasets
  listDatasets: (workspaceId = null, category = null) => {
    const params = new URLSearchParams();
    if (workspaceId) params.append('workspace_id', workspaceId);
    if (category) params.append('category', category);
    const qs = params.toString();
    return apiClient.get(qs ? `/data-intelligence/datasets?${qs}` : '/data-intelligence/datasets');
  },
  createDataset: (data) => apiClient.post('/data-intelligence/datasets', data),
  importDataset: (data) => apiClient.post('/data-intelligence/datasets/import', data),
  profileDataset: (slug) => apiClient.get(`/data-intelligence/datasets/${slug}/profile`),

  // Pipelines
  listPipelines: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/pipelines?workspace_id=${workspaceId}` : '/data-intelligence/pipelines';
    return apiClient.get(url);
  },
  createPipeline: (data) => apiClient.post('/data-intelligence/pipelines', data),
  runPipeline: (pipelineId) => apiClient.post(`/data-intelligence/pipelines/${pipelineId}/run`),

  // Dashboards
  listDashboards: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/dashboards?workspace_id=${workspaceId}` : '/data-intelligence/dashboards';
    return apiClient.get(url);
  },
  getDashboard: (dashboardId) => apiClient.get(`/data-intelligence/dashboards/${dashboardId}`),
  createDashboard: (data) => apiClient.post('/data-intelligence/dashboards', data),
  deleteDashboard: (dashboardId) => apiClient.delete(`/data-intelligence/dashboards/${dashboardId}`),

  // Reports
  listReports: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/reports?workspace_id=${workspaceId}` : '/data-intelligence/reports';
    return apiClient.get(url);
  },
  createReport: (data) => apiClient.post('/data-intelligence/reports', data),
  executeReport: (reportId) => apiClient.post(`/data-intelligence/reports/${reportId}/run`),
  exportReport: (reportId, format = 'CSV') => apiClient.get(`/data-intelligence/reports/${reportId}/export?format=${format}`),

  // Quality Rules & Audit
  listQualityRules: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/quality/rules?workspace_id=${workspaceId}` : '/data-intelligence/quality/rules';
    return apiClient.get(url);
  },

  // Lineage & Insights
  getLineage: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/lineage?workspace_id=${workspaceId}` : '/data-intelligence/lineage';
    return apiClient.get(url);
  },
  listInsights: (workspaceId = null) => {
    const url = workspaceId ? `/data-intelligence/insights?workspace_id=${workspaceId}` : '/data-intelligence/insights';
    return apiClient.get(url);
  },
  createInsight: (data) => apiClient.post('/data-intelligence/insights', data),

  // AI Assistant
  queryAiAssistant: (prompt, workspaceId = null) =>
    apiClient.post('/data-intelligence/assistant/query', { prompt, workspace_id: workspaceId }),
};
