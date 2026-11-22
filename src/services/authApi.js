import { api } from './api';

export const authApi = {
  login: async (email, password) => {
    return api.post('/auth/login', { email, password });
  },

  register: async (name, email, password, role = 'Member') => {
    return api.post('/auth/register', { name, email, password, role });
  },

  getMe: async () => {
    return api.get('/auth/me');
  },
};
