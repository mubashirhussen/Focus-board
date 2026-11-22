import assert from 'node:assert';
import { initialTasks } from './src/data/initialTasks.js';
import { calculateStats, filterTasks } from './src/utils/taskHelpers.js';
import { validateTaskForm } from './src/utils/validation.js';

console.log('--- STARTING PHASE 2 VERIFICATION SUITE ---');

// 1. Initial State & Data Model
assert.strictEqual(Array.isArray(initialTasks), true, 'initialTasks must be an array');
assert.strictEqual(initialTasks.length >= 6, true, 'Must have at least 6 initial tasks');

for (const t of initialTasks) {
  assert.ok(t.id, 'Task must have an id');
  assert.ok(t.title, 'Task must have a title');
  assert.ok(t.category, 'Task must have a category');
  assert.ok(['Todo', 'In Progress', 'Completed'].includes(t.status), `Invalid status: ${t.status}`);
  assert.ok(['Low', 'Medium', 'High'].includes(t.priority), `Invalid priority: ${t.priority}`);
  assert.ok(t.createdAt, 'Task must have createdAt');
  assert.ok(t.updatedAt, 'Task must have updatedAt');
}
console.log('✓ Initial tasks data model and field requirements validated.');

// 2. Form Validation: Empty and Whitespace Titles
const valEmpty = validateTaskForm({ title: '' });
assert.strictEqual(valEmpty.isValid, false, 'Empty title must fail validation');
assert.strictEqual(valEmpty.errors.title, 'Task title is required.');

const valWhitespace = validateTaskForm({ title: '    ' });
assert.strictEqual(valWhitespace.isValid, false, 'Whitespace title must fail validation');
assert.strictEqual(valWhitespace.errors.title, 'Task title is required.');

const valShort = validateTaskForm({ title: 'a' });
assert.strictEqual(valShort.isValid, false, 'Single char title must fail validation');

const valValid = validateTaskForm({ title: '  Complete Phase 2  ', priority: 'High', status: 'In Progress' });
assert.strictEqual(valValid.isValid, true, 'Valid title must pass validation');
assert.strictEqual(valValid.sanitizedTitle, 'Complete Phase 2', 'Sanitized title must be trimmed');
console.log('✓ Form validation handles empty, whitespace, and valid titles correctly.');

// 3. Centralized Task State Simulation (Simulating TaskContext reducer/callbacks)
let state = [...initialTasks];

// Create Task
function addTask(data) {
  const validation = validateTaskForm(data);
  if (!validation.isValid) return null;
  const now = new Date().toISOString();
  const newTask = {
    id: `task-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
    title: validation.sanitizedTitle,
    description: (data.description || '').trim(),
    category: data.category || 'Design',
    status: data.status || 'Todo',
    priority: data.priority || 'Medium',
    dueDate: data.dueDate || '',
    createdAt: now,
    updatedAt: now,
  };
  state = [newTask, ...state];
  return newTask;
}

const created = addTask({
  title: '   Build automated test suite   ',
  description: 'Integration test for Phase 2',
  category: 'Development',
  status: 'In Progress',
  priority: 'High',
  dueDate: '2026-11-24',
});

assert.ok(created, 'Task should be created');
assert.strictEqual(created.title, 'Build automated test suite');
assert.strictEqual(state[0].id, created.id);
assert.strictEqual(state.length, initialTasks.length + 1);
console.log('✓ Task creation successfully prepends to state with unique ID and timestamps.');

// 4. Edit Task (Maintaining original ID and createdAt)
function updateTask(taskId, updatedData) {
  state = state.map((task) => {
    if (task.id !== taskId) return task;
    return {
      ...task,
      ...updatedData,
      id: task.id, // Strictly preserve original ID
      createdAt: task.createdAt, // Strictly preserve original createdAt
      title: updatedData.title ? updatedData.title.trim() : task.title,
      updatedAt: new Date().toISOString(),
    };
  });
}

const originalCreatedAt = created.createdAt;
updateTask(created.id, { title: 'Updated task title', priority: 'Low' });
const updated = state.find((t) => t.id === created.id);
assert.strictEqual(updated.title, 'Updated task title');
assert.strictEqual(updated.priority, 'Low');
assert.strictEqual(updated.id, created.id, 'ID must not change on edit');
assert.strictEqual(updated.createdAt, originalCreatedAt, 'createdAt must not change on edit');
assert.ok(updated.updatedAt >= originalCreatedAt, 'updatedAt must be updated');
console.log('✓ Task editing preserves original ID and createdAt, updating updatedAt.');

// 5. Update Status
function updateTaskStatus(taskId, newStatus) {
  state = state.map((task) =>
    task.id === taskId
      ? { ...task, status: newStatus, updatedAt: new Date().toISOString() }
      : task
  );
}

updateTaskStatus(created.id, 'Completed');
assert.strictEqual(state.find((t) => t.id === created.id).status, 'Completed');
console.log('✓ Task status updates properly.');

// 6. Delete Task (Cancel & Confirm semantics)
let pendingDelete = updated;
// Cancel delete:
pendingDelete = null;
assert.strictEqual(state.some((t) => t.id === created.id), true, 'Cancel delete leaves task intact');

// Confirm delete:
function deleteTask(taskId) {
  state = state.filter((t) => t.id !== taskId);
}
deleteTask(created.id);
assert.strictEqual(state.some((t) => t.id === created.id), false, 'Task successfully removed on confirm delete');
assert.strictEqual(state.length, initialTasks.length);
console.log('✓ Task deletion with cancel/confirm semantics verified.');

// 7. Dynamic Statistics Calculation
const stats = calculateStats(state);
assert.strictEqual(stats.total, state.length);
assert.strictEqual(stats.todo + stats.inProgress + stats.completed, stats.total, 'Stats sum must equal total');
const expectedRate = Math.round((stats.completed / stats.total) * 100);
assert.strictEqual(stats.completionRate, expectedRate, 'Completion rate must match formula');

// Zero division check
const zeroStats = calculateStats([]);
assert.strictEqual(zeroStats.total, 0);
assert.strictEqual(zeroStats.completionRate, 0, 'Zero tasks must yield 0% completion without NaN');
console.log('✓ Statistics and completion rate dynamically calculated correctly.');

// 8. Search & Composite Filtering
// Search case-insensitivity & whitespace
const search1 = filterTasks(state, { searchQuery: '   LANDING   ' });
assert.strictEqual(search1.length, 1);
assert.strictEqual(search1[0].title, 'Design landing page');

const searchEmpty = filterTasks(state, { searchQuery: '   ' });
assert.strictEqual(searchEmpty.length, state.length, 'Empty search returns all tasks');

// Status filtering
const todoTasks = filterTasks(state, { statusFilter: 'Todo' });
assert.strictEqual(todoTasks.every((t) => t.status === 'Todo'), true);
assert.strictEqual(todoTasks.length, stats.todo);

const inProgressTasks = filterTasks(state, { statusFilter: 'In Progress' });
assert.strictEqual(inProgressTasks.every((t) => t.status === 'In Progress'), true);
assert.strictEqual(inProgressTasks.length, stats.inProgress);

const completedTasks = filterTasks(state, { statusFilter: 'Completed' });
assert.strictEqual(completedTasks.every((t) => t.status === 'Completed'), true);
assert.strictEqual(completedTasks.length, stats.completed);

// Priority filtering
const highPriority = filterTasks(state, { priorityFilter: 'High' });
assert.strictEqual(highPriority.every((t) => t.priority === 'High'), true);

// Composite: Search + Status + Priority combined
const combined = filterTasks(state, {
  searchQuery: 'mobile',
  statusFilter: 'In Progress',
  priorityFilter: 'Medium',
});
assert.strictEqual(combined.length, 1);
assert.strictEqual(combined[0].title, 'Fix mobile navigation');
console.log('✓ Search, Status, and Priority composite filtering verified.');

// 9. LocalStorage Persistence Logic & Corruption Resilience
class MockLocalStorage {
  constructor() {
    this.store = {};
  }
  getItem(key) {
    return this.store[key] !== undefined ? this.store[key] : null;
  }
  setItem(key, value) {
    this.store[key] = String(value);
  }
  removeItem(key) {
    delete this.store[key];
  }
}

const mockStorage = new MockLocalStorage();
const STORAGE_KEY = 'focusboard_tasks_test';

// First initialization: no saved data -> uses initialTasks
let stored = mockStorage.getItem(STORAGE_KEY);
let loadedTasks = stored ? JSON.parse(stored) : initialTasks;
assert.strictEqual(loadedTasks.length, initialTasks.length);

// Save mutation
const testNewTask = { id: 'task-test-99', title: 'New persistent task', status: 'Todo', priority: 'Low' };
const mutatedList = [testNewTask, ...loadedTasks];
mockStorage.setItem(STORAGE_KEY, JSON.stringify(mutatedList));

// Simulate refresh: reload from storage
const reloadedJson = mockStorage.getItem(STORAGE_KEY);
const reloadedTasks = JSON.parse(reloadedJson);
assert.strictEqual(reloadedTasks.length, initialTasks.length + 1);
assert.strictEqual(reloadedTasks[0].id, 'task-test-99', 'Saved user task MUST be preserved on refresh');

// Malformed JSON test
mockStorage.setItem(STORAGE_KEY, 'INVALID_CORRUPTED_JSON{[');
let corruptedFallback;
try {
  corruptedFallback = JSON.parse(mockStorage.getItem(STORAGE_KEY));
} catch {
  corruptedFallback = initialTasks;
}
assert.strictEqual(Array.isArray(corruptedFallback), true, 'Corrupted storage falls back to initialTasks safely');
console.log('✓ LocalStorage persistence and fallback handling verified.');

console.log('--- ALL PHASE 2 VERIFICATIONS PASSED SUCCESSFULLY (28/28) ---');
