import { api } from './api.js';

export const aiApi = {
  // Existing / Assistant Core Methods
  getPriorities: async () => {
    return api.get('/ai/priorities');
  },

  generateDailyPlan: async (params = {}) => {
    return api.post('/ai/daily-plan', {
      planning_date: params.planningDate,
      available_hours: params.availableHours || 6.0,
      preferred_category: params.preferredCategory,
    });
  },

  breakdownTask: async (params) => {
    return api.post('/ai/task-breakdown', {
      task_id: params.taskId,
      task_title: params.taskTitle,
      task_description: params.taskDescription || '',
      category: params.category || 'Design',
      target_deadline: params.targetDeadline,
    });
  },

  getWorkloadAnalysis: async () => {
    return api.get('/ai/workload-analysis');
  },

  chat: async (message, history = [], options = {}) => {
    return api.post('/ai/chat', {
      message,
      history,
      conversation_id: options.conversationId,
      workspace_id: options.workspaceId,
      project_id: options.projectId,
      provider: options.provider,
      model: options.model,
    });
  },

  approveAction: async (actionType, taskId, payload = {}) => {
    return api.post('/ai/approve-action', {
      action_type: actionType,
      task_id: taskId,
      payload,
    });
  },

  // Conversation Management Methods (Phase B13)
  createConversation: async (data = {}) => {
    return api.post('/ai/conversations', data);
  },

  getConversations: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/conversations${q ? `?${q}` : ''}`);
  },

  getConversation: async (conversationId) => {
    return api.get(`/ai/conversations/${conversationId}`);
  },

  updateConversation: async (conversationId, data) => {
    return api.patch(`/ai/conversations/${conversationId}`, data);
  },

  deleteConversation: async (conversationId) => {
    return api.delete(`/ai/conversations/${conversationId}`);
  },

  getMessages: async (conversationId, params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/conversations/${conversationId}/messages${q ? `?${q}` : ''}`);
  },

  // Task Intelligence Methods (Phase B13)
  generateTaskDescription: async (data) => {
    return api.post('/ai/tasks/generate-description', data);
  },

  decomposeTask: async (data) => {
    return api.post('/ai/tasks/decompose', data);
  },

  planTask: async (data) => {
    return api.post('/ai/tasks/plan', data);
  },

  createTaskAssist: async (data) => {
    return api.post('/ai/tasks/create-assist', data);
  },

  // Project Intelligence Methods (Phase B13)
  getProjectSummary: async (projectId) => {
    return api.get(`/ai/projects/${projectId}/summary`);
  },

  planProject: async (data) => {
    return api.post('/ai/projects/plan', data);
  },

  getProjectRiskAnalysis: async (projectId) => {
    return api.get(`/ai/projects/${projectId}/risk-analysis`);
  },

  // Analytics & Usage Methods (Phase B13)
  interpretAnalytics: async (data = {}) => {
    return api.post('/ai/analytics/interpret', data);
  },

  getUsage: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/usage${q ? `?${q}` : ''}`);
  },

  // Strategic Work Intelligence & High-Value Features (Review Expansion)
  getNextBestTask: async () => {
    return api.get('/ai/next-best-task');
  },

  logFocusSession: async (data) => {
    return api.post('/ai/focus-sessions', data);
  },

  getFocusStats: async () => {
    return api.get('/ai/focus-stats');
  },

  getPredictiveRisks: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/predictive-risks${q ? `?${q}` : ''}`);
  },

  getTeamCapacity: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/team-capacity${q ? `?${q}` : ''}`);
  },

  analyzeMeeting: async (data) => {
    return api.post('/ai/meetings/analyze', data);
  },

  convertMeetingActionItem: async (data) => {
    return api.post('/ai/meetings/convert-action-item', data);
  },

  createDecision: async (data) => {
    return api.post('/ai/decisions', data);
  },

  getDecisions: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return api.get(`/ai/decisions${q ? `?${q}` : ''}`);
  },
};
