import { apiClient } from './api.js';

export const goalApi = {
  // --- Analytics & Overview ---
  getOverviewAnalytics: () => apiClient.get('/goals/analytics/overview'),
  getGoalsOverviewMetrics: () => apiClient.get('/goals/analytics/overview'),

  // --- Goals CRUD & Lifecycle ---
  getGoals: (params = {}) => apiClient.get('/goals', { params }),

  createGoal: (data) => apiClient.post('/goals', data),

  getGoalDetail: (id) => apiClient.get(`/goals/${id}`),

  updateGoal: (id, data) => apiClient.put(`/goals/${id}`, data),

  deleteGoal: (id) => apiClient.delete(`/goals/${id}`),

  transitionStatus: (id, status, reason = '') =>
    apiClient.post(`/goals/${id}/status`, { status, reason }),

  activateGoal: (id) => apiClient.post(`/goals/${id}/activate`, {}),

  completeGoal: (id) => apiClient.post(`/goals/${id}/complete`, {}),

  cancelGoal: (id) => apiClient.post(`/goals/${id}/cancel`, {}),

  archiveGoal: (id) => apiClient.post(`/goals/${id}/archive`, {}),

  // --- Key Results ---
  createKeyResult: (goalId, data) => apiClient.post(`/goals/${goalId}/key-results`, data),

  updateKeyResultProgress: (krId, currentValue, comment = '') =>
    apiClient.post(`/goals/key-results/${krId}/progress`, { current_value: currentValue, comment }),

  getKeyResultHistory: (krId) => apiClient.get(`/goals/key-results/${krId}/history`),

  deleteKeyResult: (krId) => apiClient.delete(`/goals/key-results/${krId}`),

  // --- Milestones ---
  getMilestones: (params = {}) => apiClient.get('/goals/milestones/list', { params }),

  createMilestone: (goalId, data) => apiClient.post(`/goals/${goalId}/milestones`, data),

  completeMilestone: (milestoneId) => apiClient.post(`/goals/milestones/${milestoneId}/complete`, {}),

  reopenMilestone: (milestoneId) => apiClient.post(`/goals/milestones/${milestoneId}/reopen`, {}),

  addMilestoneDependency: (milestoneId, dependsOnId) =>
    apiClient.post(`/goals/milestones/${milestoneId}/dependencies`, {
      depends_on_milestone_id: dependsOnId,
    }),

  deleteMilestone: (milestoneId) => apiClient.delete(`/goals/milestones/${milestoneId}`),

  // --- Check-Ins & Reviews ---
  submitCheckIn: (goalId, data) => apiClient.post(`/goals/${goalId}/check-ins`, data),

  reviewCheckIn: (checkInId, feedback) =>
    apiClient.post(`/goals/check-ins/${checkInId}/review`, { feedback }),

  // --- Linking Projects & Tasks ---
  linkProject: (goalId, projectId) =>
    apiClient.post(`/goals/${goalId}/projects`, { project_id: projectId }),

  unlinkProject: (goalId, projectId) =>
    apiClient.delete(`/goals/${goalId}/projects/${projectId}`),

  linkTask: (krId, taskId, weight = 1.0) =>
    apiClient.post(`/goals/key-results/${krId}/tasks`, { task_id: taskId, weight }),
  linkTaskToKeyResult: (krId, taskId, weight = 1.0) =>
    apiClient.post(`/goals/key-results/${krId}/tasks`, { task_id: taskId, weight }),

  unlinkTask: (krId, taskId) =>
    apiClient.delete(`/goals/key-results/${krId}/tasks/${taskId}`),
  unlinkTaskFromKeyResult: (krId, taskId) =>
    apiClient.delete(`/goals/key-results/${krId}/tasks/${taskId}`),

  // --- Comments ---
  getGoalComments: (goalId) => apiClient.get(`/goals/${goalId}/comments`),
  addComment: (goalId, content) =>
    apiClient.post(`/goals/${goalId}/comments`, { content }),
  addGoalComment: (goalId, content) =>
    apiClient.post(`/goals/${goalId}/comments`, { content }),
};
