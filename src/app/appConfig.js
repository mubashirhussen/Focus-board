export const APP_CONFIG = {
  appName: 'FocusBoard',
  tagline: 'Your work, in focus.',
  subtitle: 'Plan your day, stay organized, and get things done.',
  storageKey: import.meta.env.VITE_APP_STORAGE_KEY || 'focusboard_tasks_v1',
  user: {
    name: 'John Doe',
    initials: 'JD',
    role: 'Product Designer',
  },
  statuses: ['Todo', 'In Progress', 'Completed'],
  priorities: ['Low', 'Medium', 'High'],
  categories: ['Design', 'Development', 'Content', 'Marketing', 'Research', 'Planning'],
  navItems: [
    { id: 'tasks', label: 'My Tasks', icon: 'CheckSquare' },
    { id: 'calendar', label: 'Calendar', icon: 'Calendar' },
    { id: 'settings', label: 'Settings', icon: 'Settings' },
  ],
};
