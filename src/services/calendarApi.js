import { apiClient } from './api';

export const calendarApi = {
  getEvents: (start, end) => {
    const params = new URLSearchParams();
    if (start) params.append('start', start);
    if (end) params.append('end', end);
    const qs = params.toString();
    return apiClient.get(`/calendar/events${qs ? `?${qs}` : ''}`);
  },
  scheduleTask: (taskId, start, end, duration = 30) => {
    return apiClient.post('/calendar/schedule-task', {
      task_id: taskId,
      scheduled_start: start,
      scheduled_end: end,
      estimated_duration_minutes: duration,
    });
  },
  getConflicts: () => apiClient.get('/calendar/conflicts'),
  triggerSync: () => apiClient.post('/calendar/sync', {}),
};
