import { apiClient } from './api.js';

export const enterpriseAnalyticsApi = {
  getExecutiveSummary: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/enterprise-analytics/executive-summary${query}`);
  },

  getPortfolioHealth: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/enterprise-analytics/portfolio-health${query}`);
  },

  getProjectHealth: (projectId) => {
    return apiClient.get(`/enterprise-analytics/projects/${projectId}/health`);
  },

  getProjectMilestones: (projectId) => {
    return apiClient.get(`/enterprise-analytics/projects/${projectId}/milestones`);
  },

  createProjectMilestone: (projectId, data) => {
    return apiClient.post(`/enterprise-analytics/projects/${projectId}/milestones`, data);
  },

  updateProjectMilestone: (milestoneId, data) => {
    return apiClient.patch(`/enterprise-analytics/milestones/${milestoneId}`, data);
  },

  deleteProjectMilestone: (milestoneId) => {
    return apiClient.delete(`/enterprise-analytics/milestones/${milestoneId}`);
  },

  getProjectRisks: (projectId) => {
    return apiClient.get(`/enterprise-analytics/projects/${projectId}/risks`);
  },

  createProjectRisk: (projectId, data) => {
    return apiClient.post(`/enterprise-analytics/projects/${projectId}/risks`, data);
  },

  updateProjectRisk: (riskId, data) => {
    return apiClient.patch(`/enterprise-analytics/risks/${riskId}`, data);
  },

  getTeamWorkload: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/enterprise-analytics/team-workload${query}`);
  },

  setResourceCapacity: (data, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/enterprise-analytics/resource-capacity${query}`, data);
  },

  createReport: (data, workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.post(`/enterprise-analytics/reports${query}`, data);
  },

  listReports: (workspaceId) => {
    const query = workspaceId ? `?workspace_id=${workspaceId}` : '';
    return apiClient.get(`/enterprise-analytics/reports${query}`);
  },

  downloadReportUrl: (reportId) => {
    return `${apiClient.baseUrl}/enterprise-analytics/reports/${reportId}/download`;
  },
};
