import { api, API_BASE_URL } from './api.js';

export const analyticsApi = {
  getSummary: async () => {
    return api.get('/analytics/summary');
  },

  getTrends: async (days = 7) => {
    return api.get(`/analytics/completion-trends?days=${days}`);
  },

  getDistribution: async () => {
    return api.get('/analytics/distribution');
  },

  getInsights: async () => {
    return api.get('/analytics/insights');
  },

  downloadCsv: async () => {
    const token = localStorage.getItem('focusboard_token');
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/analytics/export`, {
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
    a.download = `focusboard_tasks_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(downloadUrl);
  },
};
