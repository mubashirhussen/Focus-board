import { apiClient } from './api.js';

export const timeTrackingApi = {
  // --- Active Timer Operations ---
  getActiveTimer: () => apiClient.get('/time-tracking/timer/active'),

  startTimer: (data) => apiClient.post('/time-tracking/timer/start', data),

  pauseTimer: () => apiClient.post('/time-tracking/timer/pause', {}),

  resumeTimer: () => apiClient.post('/time-tracking/timer/resume', {}),

  stopTimer: () => apiClient.post('/time-tracking/timer/stop', {}),

  cancelTimer: () => apiClient.post('/time-tracking/timer/cancel', {}),

  // --- Time Entries CRUD ---
  getEntries: (params = {}) => apiClient.get('/time-tracking/entries', { params }),

  createEntry: (data) => apiClient.post('/time-tracking/entries', data),

  updateEntry: (id, data) => apiClient.put(`/time-tracking/entries/${id}`, data),

  deleteEntry: (id) => apiClient.delete(`/time-tracking/entries/${id}`),

  // --- Timesheet Management & Approvals ---
  getTimesheets: (params = {}) => apiClient.get('/time-tracking/timesheets', { params }),

  getOrCreateTimesheet: (data) => apiClient.post('/time-tracking/timesheets', data),

  getTimesheetDetail: (id) => apiClient.get(`/time-tracking/timesheets/${id}`),

  submitTimesheet: (id) => apiClient.post(`/time-tracking/timesheets/${id}/submit`, {}),

  withdrawTimesheet: (id) => apiClient.post(`/time-tracking/timesheets/${id}/withdraw`, {}),

  approveTimesheet: (id, comments = '') =>
    apiClient.post(`/time-tracking/timesheets/${id}/approve`, { review_comments: comments }),

  rejectTimesheet: (id, comments = '') =>
    apiClient.post(`/time-tracking/timesheets/${id}/reject`, { review_comments: comments }),

  reopenTimesheet: (id, comments = '') =>
    apiClient.post(`/time-tracking/timesheets/${id}/reopen`, { review_comments: comments }),

  // --- Analytics & Reports ---
  getSummary: () => apiClient.get('/time-tracking/summary'),

  getProjectReports: (params = {}) => apiClient.get('/time-tracking/reports/project', { params }),

  getUserReports: (params = {}) => apiClient.get('/time-tracking/reports/user', { params }),

  getBillableReport: (params = {}) => apiClient.get('/time-tracking/reports/billable', { params }),

  // --- Settings ---
  getSettings: () => apiClient.get('/time-tracking/settings'),

  updateSettings: (data) => apiClient.put('/time-tracking/settings', data),
};
