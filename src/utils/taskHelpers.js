/**
 * Derives aggregate dashboard statistics from the task array.
 * Single source of truth — mathematically sound and prevents division by zero.
 */
export function calculateStats(tasks = []) {
  const safeTasks = Array.isArray(tasks) ? tasks : [];
  const total = safeTasks.length;
  let todo = 0;
  let inProgress = 0;
  let completed = 0;

  for (const task of safeTasks) {
    if (task.status === 'Completed') {
      completed++;
    } else if (task.status === 'In Progress') {
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
 * - Status filter ('All', 'Todo', 'In Progress', 'Completed')
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
      if (task.status !== statusFilter) {
        return false;
      }
    }

    // 2. Priority Filter Check
    if (priorityFilter && priorityFilter !== 'All') {
      if (task.priority !== priorityFilter) {
        return false;
      }
    }

    // 3. Search Query Check (Case-insensitive title & description match)
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
