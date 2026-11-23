/**
 * Derives aggregate dashboard statistics from the task array.
 * Single source of truth — mathematically sound and prevents division by zero.
 * Supports flexible status formats ('To do', 'Todo', 'In progress', 'In Progress', 'Completed').
 */
export function calculateStats(tasks = []) {
  const safeTasks = Array.isArray(tasks) ? tasks : [];
  const total = safeTasks.length;
  let todo = 0;
  let inProgress = 0;
  let completed = 0;

  for (const task of safeTasks) {
    const s = String(task.status || '').toLowerCase().replace(/[\s_-]+/g, '');
    if (s === 'completed' || s === 'done') {
      completed++;
    } else if (s === 'inprogress' || s === 'progress') {
      inProgress++;
    } else {
      todo++;
    }
  }

  // Mathematically correct completion percentage, safe against division by zero
  const completionRate = total > 0 ? Math.round((completed / total) * 100) : 0;

  return {
    total,
    todo,
    inProgress,
    completed,
    completionRate,
  };
}

/**
 * Filters tasks using composite criteria:
 * - Search query (title and description match, case-insensitive, trimmed)
 * - Status filter ('All', 'To do', 'Todo', 'In progress', 'In Progress', 'Completed')
 * - Priority filter ('All', 'Low', 'Medium', 'High')
 *
 * All filters compose conjunctively (AND).
 */
export function filterTasks(
  tasks = [],
  { searchQuery = '', statusFilter = 'All', priorityFilter = 'All' } = {}
) {
  const safeTasks = Array.isArray(tasks) ? tasks : [];
  const query = (searchQuery || '').trim().toLowerCase();

  return safeTasks.filter((task) => {
    // 1. Status Filter Check
    if (statusFilter && statusFilter !== 'All') {
      const normFilter = String(statusFilter).toLowerCase().replace(/[\s_-]+/g, '');
      const normStatus = String(task.status || '').toLowerCase().replace(/[\s_-]+/g, '');
      if (normFilter !== normStatus) {
        return false;
      }
    }

    // 2. Priority Filter Check
    if (priorityFilter && priorityFilter !== 'All') {
      const normPriorityFilter = String(priorityFilter).toLowerCase();
      const normTaskPriority = String(task.priority || '').toLowerCase();
      if (normPriorityFilter !== normTaskPriority) {
        return false;
      }
    }

    // 3. Search Query Check (Case-insensitive title, description & category match)
    if (query) {
      const titleMatch = (task.title || '').toLowerCase().includes(query);
      const descMatch = (task.description || '').toLowerCase().includes(query);
      const catMatch = (task.category || '').toLowerCase().includes(query);
      if (!titleMatch && !descMatch && !catMatch) {
        return false;
      }
    }

    return true;
  });
}
