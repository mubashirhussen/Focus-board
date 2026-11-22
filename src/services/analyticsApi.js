import { api, API_BASE_URL } from './api.js';

export const analyticsApi = {
  getSummary: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/summary${q ? `?${q}` : ''}`);
  },

  getTrends: async (days = 7, params = {}) => {
    const q = new URLSearchParams({ days, ...params }).toString();
    return api.get(`/analytics/completion-trends?${q}`);
  },

  getTrendComparison: async (days = 7, params = {}) => {
    const q = new URLSearchParams({ days, ...params }).toString();
    return api.get(`/analytics/trends/compare?${q}`);
  },

  getDistribution: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/distribution${q ? `?${q}` : ''}`);
  },

  getInsights: async () => {
    return api.get('/analytics/insights');
  },

  getPersonalAnalytics: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/personal${q ? `?${q}` : ''}`);
  },

  getProjectAnalytics: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/projects${q ? `?${q}` : ''}`);
  },

  getSingleProjectAnalytics: async (projectId) => {
    return api.get(`/analytics/projects/${projectId}`);
  },

  getTeamAnalytics: async (teamId) => {
    return api.get(`/analytics/teams/${teamId}`);
  },

  getWorkspaceAnalytics: async (workspaceId) => {
    return api.get(`/analytics/workspaces/${workspaceId}`);
  },

  getOrganizationAnalytics: async (orgId) => {
    const q = orgId ? `?organization_id=${orgId}` : '';
    return api.get(`/analytics/organization${q}`);
  },

  getDeadlines: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/deadlines${q ? `?${q}` : ''}`);
  },

  getActivity: async (days = 14) => {
    return api.get(`/analytics/activity?days=${days}`);
  },

  getKPIs: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/analytics/kpis${q ? `?${q}` : ''}`);
  },

  downloadCsv: async (reportType = 'tasks') => {
    const token = localStorage.getItem('focusboard_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/analytics/export?report_type=${reportType}`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Failed to export CSV: ${response.statusText}`);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `focusboard_${reportType}_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
