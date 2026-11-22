import { api } from './api';

export const collaborationApi = {
  getWorkspaces: async () => {
    return api.get('/workspaces');
  },

  createWorkspace: async (data) => {
    return api.post('/workspaces', data);
  },

  getWorkspaceDetails: async (workspaceId) => {
    return api.get(`/workspaces/${workspaceId}`);
  },

  getMembers: async (workspaceId) => {
    return api.get(`/workspaces/${workspaceId}/members`);
  },

  inviteMember: async (workspaceId, email, role = 'MEMBER') => {
    return api.post(`/workspaces/${workspaceId}/invitations`, { email, role });
  },

  acceptInvitation: async (token) => {
    return api.post(`/workspaces/invitations/${token}/accept`, {});
  },

  getProjects: async (workspaceId) => {
    return api.get(`/workspaces/${workspaceId}/projects`);
  },

  createProject: async (workspaceId, data) => {
    return api.post(`/workspaces/${workspaceId}/projects`, data);
  },

  getWorkspaceTasks: async (workspaceId, projectId = null) => {
    const query = projectId ? `?project_id=${projectId}` : '';
    return api.get(`/workspaces/${workspaceId}/tasks${query}`);
  },

  createWorkspaceTask: async (workspaceId, taskData, projectId = null, assigneeId = null) => {
    const params = new URLSearchParams();
    if (projectId) params.append('project_id', projectId);
    if (assigneeId) params.append('assignee_id', assigneeId);
    const query = params.toString() ? `?${params.toString()}` : '';
    return api.post(`/workspaces/${workspaceId}/tasks${query}`, taskData);
  },

  assignTask: async (workspaceId, taskId, data) => {
    return api.request(`/workspaces/${workspaceId}/tasks/${taskId}/assign`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  getComments: async (workspaceId, taskId) => {
    return api.get(`/workspaces/${workspaceId}/tasks/${taskId}/comments`);
  },

  addComment: async (workspaceId, taskId, content) => {
    return api.post(`/workspaces/${workspaceId}/tasks/${taskId}/comments`, { content });
  },

  getActivities: async (workspaceId) => {
    return api.get(`/workspaces/${workspaceId}/activities`);
  },

  getTeamAnalytics: async (workspaceId) => {
    return api.get(`/workspaces/${workspaceId}/analytics`);
  },
};
