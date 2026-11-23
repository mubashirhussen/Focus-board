/**
 * FocusBoard Initial Sample Tasks
 * Mandatory Requirement: At least 6 sample tasks with unique IDs, meaningful titles,
 * descriptions, categories, statuses ('Todo', 'In Progress', 'Completed'),
 * priorities ('Low', 'Medium', 'High'), and due dates.
 */

export const sampleTasks = [
  {
    id: 'task-1',
    title: 'Design landing page',
    description: 'Website redesign • Q4 sprint',
    category: 'Design',
    status: 'In Progress',
    priority: 'High',
    dueDate: '2026-11-22',
    createdAt: '2026-11-15T09:00:00.000Z',
    updatedAt: '2026-11-15T09:00:00.000Z',
  },
  {
    id: 'task-2',
    title: 'Fix mobile navigation',
    description: 'Responsive fixes • Sprint 3',
    category: 'Development',
    status: 'In Progress',
    priority: 'Medium',
    dueDate: '2026-11-23',
    createdAt: '2026-11-16T10:30:00.000Z',
    updatedAt: '2026-11-16T10:30:00.000Z',
  },
  {
    id: 'task-3',
    title: 'Review onboarding copy',
    description: 'User experience • App launch',
    category: 'Content',
    status: 'Completed',
    priority: 'Low',
    dueDate: '2026-11-18',
    createdAt: '2026-11-14T14:15:00.000Z',
    updatedAt: '2026-11-14T14:15:00.000Z',
  },
  {
    id: 'task-4',
    title: 'Set up CI/CD pipeline',
    description: 'Automated test suite and preview deployments',
    category: 'Development',
    status: 'Completed',
    priority: 'High',
    dueDate: '2026-11-19',
    createdAt: '2026-11-12T11:00:00.000Z',
    updatedAt: '2026-11-12T11:00:00.000Z',
  },
  {
    id: 'task-5',
    title: 'User research interview synthesis',
    description: 'Analyze user feedback from 10 stakeholder sessions',
    category: 'Research',
    status: 'Todo',
    priority: 'Medium',
    dueDate: '2026-11-25',
    createdAt: '2026-11-17T08:45:00.000Z',
    updatedAt: '2026-11-17T08:45:00.000Z',
  },
  {
    id: 'task-6',
    title: 'Quarterly roadmap presentation',
    description: 'Finalize OKR slide deck for leadership team',
    category: 'Planning',
    status: 'Todo',
    priority: 'High',
    dueDate: '2026-11-26',
    createdAt: '2026-11-18T13:20:00.000Z',
    updatedAt: '2026-11-18T13:20:00.000Z',
  },
  {
    id: 'task-7',
    title: 'Audit accessibility contrast',
    description: 'Verify WCAG 2.1 AA compliance across all components',
    category: 'Testing',
    status: 'Todo',
    priority: 'Low',
    dueDate: '2026-11-28',
    createdAt: '2026-11-19T16:00:00.000Z',
    updatedAt: '2026-11-19T16:00:00.000Z',
  },
];

// Alias initialTasks for backwards compatibility with existing imports
export const initialTasks = sampleTasks;
export default sampleTasks;
