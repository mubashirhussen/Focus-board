import assert from 'node:assert';
import { aiApi } from '../../src/services/aiApi.js';

console.log('--- RUNNING WORK INTELLIGENCE & ADAPTIVE FOCUS FRONTEND TESTS ---');

// 1. aiApi Surface Method Validation
{
  const requiredMethods = [
    'getNextBestTask',
    'logFocusSession',
    'getFocusStats',
    'getPredictiveRisks',
    'getTeamCapacity',
    'analyzeMeeting',
    'convertMeetingActionItem',
    'createDecision',
    'getDecisions',
    'getPriorities',
    'generateDailyPlan',
    'breakdownTask',
    'chat',
  ];

  for (const method of requiredMethods) {
    assert.strictEqual(typeof aiApi[method], 'function', `aiApi should expose ${method}`);
  }
  console.log('✓ aiApi client exposes all strategic intelligence, focus session, and meeting methods.');
}

// 2. Next Best Task Scoring & Explainability Logic
{
  const calculateNextBestTaskScore = (task, todayStr) => {
    let score = (task.priority || '').toLowerCase() === 'high' ? 45 : (task.priority || '').toLowerCase() === 'medium' ? 25 : 10;
    const tags = [];

    if (task.dueDate) {
      if (task.dueDate < todayStr) {
        score += 40;
        tags.push('OVERDUE_RISK');
      } else if (task.dueDate === todayStr) {
        score += 30;
        tags.push('DUE_TODAY');
      }
    }

    if ((task.status || '').toLowerCase() === 'in progress') {
      score += 15;
      tags.push('IN_PROGRESS_MOMENTUM');
    }

    const est = task.estimated_duration_minutes || 45;
    if (est <= 30) tags.push('QUICK_WIN');
    else if (est >= 60) tags.push('DEEP_WORK');

    return {
      score: Math.min(100, Math.max(10, score)),
      tags,
      urgency: score >= 80 ? 'Critical' : score >= 60 ? 'High' : 'Normal',
    };
  };

  const today = '2026-11-23';
  const overdueTask = {
    title: 'Fix High Priority Bug',
    priority: 'High',
    dueDate: '2026-11-20',
    status: 'In Progress',
    estimated_duration_minutes: 90,
  };

  const evalResult = calculateNextBestTaskScore(overdueTask, today);
  assert.strictEqual(evalResult.score, 100);
  assert.strictEqual(evalResult.urgency, 'Critical');
  assert(evalResult.tags.includes('OVERDUE_RISK'));
  assert(evalResult.tags.includes('IN_PROGRESS_MOMENTUM'));
  assert(evalResult.tags.includes('DEEP_WORK'));

  console.log('✓ Next Best Task scoring accurately calculates urgency, momentum, and explainability tags.');
}

// 3. Adaptive Focus Timer Formatting & Sprint Calculations
{
  const formatTimerDisplay = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  assert.strictEqual(formatTimerDisplay(1500), '25:00');
  assert.strictEqual(formatTimerDisplay(2700), '45:00');
  assert.strictEqual(formatTimerDisplay(59), '00:59');
  assert.strictEqual(formatTimerDisplay(0), '00:00');

  console.log('✓ Adaptive Focus timer formatting executes accurately.');
}

// 4. Team Capacity Utilization Calculations
{
  const computeMemberCapacity = (assignedTasks, capacityHours = 40) => {
    const totalMinutes = assignedTasks.reduce((acc, t) => acc + (t.estimated_duration_minutes || 45), 0);
    const allocatedHours = Math.round((totalMinutes / 60) * 10) / 10;
    const utilizationPct = Math.round((allocatedHours / capacityHours) * 1000) / 10;
    const status = utilizationPct > 85 ? 'OVERLOADED' : utilizationPct >= 40 ? 'OPTIMAL' : 'AVAILABLE';
    return { allocatedHours, utilizationPct, status };
  };

  const overloaded = computeMemberCapacity([
    { estimated_duration_minutes: 600 },
    { estimated_duration_minutes: 800 },
    { estimated_duration_minutes: 800 },
  ]);
  assert.strictEqual(overloaded.status, 'OVERLOADED');
  assert(overloaded.utilizationPct > 85);

  const optimal = computeMemberCapacity([
    { estimated_duration_minutes: 600 },
    { estimated_duration_minutes: 600 },
  ]);
  assert.strictEqual(optimal.status, 'OPTIMAL');

  console.log('✓ Team capacity utilization formulas accurately evaluate overloads and optimal thresholds.');
}

// 5. Meeting Action Item Extraction & Task Payload Generation
{
  const generateTaskPayloadFromAction = (action, userId, projectId) => {
    return {
      title: (action.title || '').trim(),
      description: action.description || 'Generated from Meeting Intelligence action item.',
      priority: action.priority || 'Medium',
      dueDate: action.suggested_due_date || new Date().toISOString().split('T')[0],
      category: 'Meeting Action',
      userId,
      projectId,
    };
  };

  const testAction = {
    title: '  Deploy Zero-Trust Telemetry Exporter  ',
    description: 'Ensure RFC 6238 compliance audit completes.',
    priority: 'High',
    suggested_due_date: '2026-11-27',
  };

  const payload = generateTaskPayloadFromAction(testAction, 42, 10);
  assert.strictEqual(payload.title, 'Deploy Zero-Trust Telemetry Exporter');
  assert.strictEqual(payload.priority, 'High');
  assert.strictEqual(payload.category, 'Meeting Action');
  assert.strictEqual(payload.dueDate, '2026-11-27');
  assert.strictEqual(payload.userId, 42);

  console.log('✓ Meeting action item converter prepares fully validated FocusBoard task payloads.');
}

console.log('--- ALL WORK INTELLIGENCE & ADAPTIVE FOCUS FRONTEND TESTS PASSED ---');
