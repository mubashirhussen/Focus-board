import { api } from './api.js';

export const aiApi = {
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

  chat: async (message, history = []) => {
    return api.post('/ai/chat', {
      message,
      history,
    });
  },

  approveAction: async (actionType, taskId, payload = {}) => {
    return api.post('/ai/approve-action', {
      action_type: actionType,
      task_id: taskId,
      payload,
    });
  },
};
