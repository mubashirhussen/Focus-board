/**
 * FocusBoard Account-Specific Sample Testing Tasks.
 * Generates an active, customized set of testing tasks covering all lifecycle stages:
 * - Assigned / Initiated (Todo)
 * - In Progress (Active development/design)
 * - Pending Review (Pending authorization/audit)
 * - Completed (Finished objectives)
 * Ensures every logged-in user can immediately test and evaluate all dashboard cards,
 * statistics, status tabs, priority breakdown, and task interactions.
 */

export function generateUserTestingTasks(user = {}) {
  const userName = user.name || user.display_name || 'Team Member';
  const userInitials = user.initials || userName.slice(0, 2).toUpperCase();
  const userEmail = user.email || 'user@focusboard.io';

  const inDays = (days) => {
    const d = new Date();
    d.setDate(d.getDate() + days);
    return d.toISOString().split('T')[0];
  };

  const agoDays = (days) => {
    const d = new Date();
    d.setDate(d.getDate() - days);
    return d.toISOString().split('T')[0];
  };

  return [
    {
      id: `task-${user.id || 'usr'}-1`,
      title: 'Review assigned workspace backlog',
      description: `Assigned to ${userName} • Initial sprint objectives, priorities, and milestone planning`,
      category: 'Planning',
      status: 'Todo', // Assigned & Initiated
      priority: 'High',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: inDays(2),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-2`,
      title: 'Initiate Slack & Google Workspace webhooks',
      description: 'Configure real-time event notifications for task assignments and team updates',
      category: 'Development',
      status: 'Todo', // Initiated
      priority: 'Medium',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: inDays(4),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-3`,
      title: 'Active sprint feature implementation',
      description: `In progress for ${userName} • Front-end components and responsive mobile design`,
      category: 'Design',
      status: 'In Progress', // In progress
      priority: 'High',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: inDays(1),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-4`,
      title: 'API endpoint regression & token rotation test',
      description: 'Under active testing • Verifying JWT refresh token lifecycle and multi-device sessions',
      category: 'Testing',
      status: 'In Progress', // In progress / active testing
      priority: 'Medium',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: inDays(3),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-5`,
      title: 'Pending security review: Zero-Trust entitlement matrix',
      description: 'Pending authorization approval • SOC-2 compliance checklist verification',
      category: 'Research',
      status: 'Todo', // Pending review / Initiated
      priority: 'High',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: inDays(5),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-6`,
      title: 'Verify single-use Email OTP delivery',
      description: `Completed verification for account ${userEmail} with cryptographic hashing`,
      category: 'Development',
      status: 'Completed', // Completed
      priority: 'High',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: agoDays(1),
      completedAt: agoDays(1),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: `task-${user.id || 'usr'}-7`,
      title: 'Workspace setup & design token integration',
      description: 'Completed onboarding sprint • Initial color palettes and typography calibrated',
      category: 'Content',
      status: 'Completed', // Completed
      priority: 'Low',
      assignee: userName,
      assigneeInitials: userInitials,
      dueDate: agoDays(2),
      completedAt: agoDays(2),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ];
}
