/**
 * Validates task create and edit form inputs.
 * Ensures data integrity, trims strings, and flags invalid values.
 */
export function validateTaskForm(formData = {}) {
  const errors = {};

  // 1. Title validation (Mandatory, trimmed, non-blank)
  const rawTitle = formData.title !== undefined && formData.title !== null ? String(formData.title) : '';
  const trimmedTitle = rawTitle.trim();

  if (!trimmedTitle) {
    errors.title = 'Task title is required.';
  } else if (trimmedTitle.length < 2) {
    errors.title = 'Task title must be at least 2 characters.';
  } else if (trimmedTitle.length > 120) {
    errors.title = 'Task title cannot exceed 120 characters.';
  }

  // 2. Description validation (Optional, max 500 characters)
  if (formData.description && String(formData.description).length > 500) {
    errors.description = 'Description cannot exceed 500 characters.';
  }

  // 3. Status validation (Must belong to allowed set)
  const validStatuses = ['Todo', 'In Progress', 'Completed'];
  if (formData.status && !validStatuses.includes(formData.status)) {
    errors.status = 'Please select a valid status (Todo, In Progress, Completed).';
  }

  // 4. Priority validation (Must belong to allowed set)
  const validPriorities = ['Low', 'Medium', 'High'];
  if (formData.priority && !validPriorities.includes(formData.priority)) {
    errors.priority = 'Please select a valid priority (Low, Medium, High).';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
    sanitizedTitle: trimmedTitle,
  };
}
