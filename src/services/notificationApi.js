import { api } from './api';

export const notificationApi = {
  getNotifications: async (unreadOnly = false) => {
    const query = unreadOnly ? '?unread_only=true' : '';
    return api.get(`/notifications${query}`);
  },

  getUnreadCount: async () => {
    return api.get('/notifications/unread-count');
  },

  markAsRead: async (notificationId) => {
    return api.request(`/notifications/${notificationId}/read`, { method: 'PATCH' });
  },

  markAllAsRead: async () => {
    return api.request('/notifications/read-all', { method: 'PATCH' });
  },

  deleteNotification: async (notificationId) => {
    return api.delete(`/notifications/${notificationId}`);
  },

  getPreferences: async () => {
    return api.get('/notifications/preferences');
  },

  updatePreferences: async (preferencesData) => {
    return api.put('/notifications/preferences', preferencesData);
  },

  triggerCheck: async () => {
    return api.post('/notifications/trigger-check', {});
  },
};
