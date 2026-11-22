/**
 * Format ISO or YYYY-MM-DD date string to compact friendly format like "Nov 22"
 */
export function formatDisplayDate(dateString) {
  if (!dateString) return 'No date';
  try {
    const date = new Date(dateString.includes('T') ? dateString : `${dateString}T00:00:00`);
    if (isNaN(date.getTime())) return dateString;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
}

/**
 * Checks if a task is overdue (dueDate in the past and not completed)
 */
export function isOverdue(dateString, status) {
  if (!dateString || status === 'Completed') return false;
  try {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dueDate = new Date(dateString.includes('T') ? dateString : `${dateString}T00:00:00`);
    dueDate.setHours(0, 0, 0, 0);
    return dueDate < today;
  } catch {
    return false;
  }
}

/**
 * Returns today formatted as YYYY-MM-DD for date inputs
 */
export function getTodayInputValue() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
