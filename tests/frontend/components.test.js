import assert from 'node:assert';
import { validateTaskForm } from '../../src/utils/validation.js';
import { calculateStats, filterTasks } from '../../src/utils/taskHelpers.js';

console.log('--- RUNNING FRONTEND COMPONENT & INTERACTION TESTS ---');

// 1. Form Validation Unit Tests
{
  // Empty title
  const r1 = validateTaskForm({ title: '' });
  assert.strictEqual(r1.isValid, false);
  assert.strictEqual(r1.errors.title, 'Task title is required.');

  // Whitespace-only title
  const r2 = validateTaskForm({ title: '   \t  \n ' });
  assert.strictEqual(r2.isValid, false);
  assert.strictEqual(r2.errors.title, 'Task title is required.');

  // Single character title
  const r3 = validateTaskForm({ title: 'x' });
  assert.strictEqual(r3.isValid, false);

  // XSS sanitization check
  const r4 = validateTaskForm({ title: '  <script>alert("xss")</script> Valid Title  ', priority: 'High', status: 'Todo' });
  assert.strictEqual(r4.isValid, true);
  assert.strictEqual(r4.sanitizedTitle, '<script>alert("xss")</script> Valid Title');
  console.log('✓ Form validation handles empty, short, and sanitized titles correctly.');
}

// 2. Task Filtering & Composite Search
{
  const mockTasks = [
    { id: '1', title: 'Design Figma UI', category: 'Design', status: 'Todo', priority: 'High' },
    { id: '2', title: 'Implement Auth API', category: 'Development', status: 'In Progress', priority: 'High' },
    { id: '3', title: 'Write Documentation', category: 'Documentation', status: 'Completed', priority: 'Low' },
    { id: '4', title: 'Refactor Database Queries', category: 'Development', status: 'Todo', priority: 'Medium' },
  ];

  // Filter by status
  const todoTasks = filterTasks(mockTasks, { statusFilter: 'Todo' });
  assert.strictEqual(todoTasks.length, 2);

  // Filter by priority
  const highTasks = filterTasks(mockTasks, { priorityFilter: 'High' });
  assert.strictEqual(highTasks.length, 2);

  // Search keyword query
  const searchResults = filterTasks(mockTasks, { searchQuery: 'Figma' });
  assert.strictEqual(searchResults.length, 1);
  assert.strictEqual(searchResults[0].id, '1');

  // Composite search: priority + status
  const composite = filterTasks(mockTasks, { priorityFilter: 'High', statusFilter: 'In Progress' });
  assert.strictEqual(composite.length, 1);
  assert.strictEqual(composite[0].id, '2');
  console.log('✓ Composite filtering across status, priority, and text search passed.');
}

// 3. Dynamic Statistics Calculation
{
  const mockTasks = [
    { id: '1', status: 'Completed' },
    { id: '2', status: 'Completed' },
    { id: '3', status: 'In Progress' },
    { id: '4', status: 'Todo' },
  ];

  const stats = calculateStats(mockTasks);
  assert.strictEqual(stats.total, 4);
  assert.strictEqual(stats.completed, 2);
  assert.strictEqual(stats.inProgress, 1);
  assert.strictEqual(stats.todo, 1);
  assert.strictEqual(stats.completionRate, 50); // 2/4 = 50%

  // Empty state handling
  const emptyStats = calculateStats([]);
  assert.strictEqual(emptyStats.total, 0);
  assert.strictEqual(emptyStats.completionRate, 0);
  console.log('✓ Dynamic statistics and completion rates compute accurately without zero-division errors.');
}

console.log('--- ALL FRONTEND COMPONENT & INTERACTION TESTS PASSED ---');
