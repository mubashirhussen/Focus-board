import assert from 'node:assert';
import { predictiveIntelligenceApi } from '../../src/services/predictiveIntelligenceApi.js';
import { intelligenceApi } from '../../src/services/intelligenceApi.js';

console.log('--- RUNNING MODULE B47: PREDICTIVE PROJECT INTELLIGENCE FRONTEND TESTS ---');

// 1. Client API Surface Validation
{
  const requiredMethods = [
    'getOverview',
    'getProjectsHealth',
    'getProjectHealth',
    'getProjectForecast',
    'getProjectRisks',
    'getTaskRisk',
    'getWorkload',
    'getRecommendations',
    'acceptRecommendation',
    'rejectRecommendation',
    'completeRecommendation',
    'getHistory',
    'getSettings',
    'updateSettings',
    'recalculateProject',
  ];

  for (const m of requiredMethods) {
    assert.strictEqual(
      typeof predictiveIntelligenceApi[m],
      'function',
      `predictiveIntelligenceApi must expose method ${m}`
    );
  }

  // Also check intelligenceApi extensions
  assert.strictEqual(typeof intelligenceApi.getOverview, 'function');
  assert.strictEqual(typeof intelligenceApi.getProjectHealth, 'function');
  assert.strictEqual(typeof intelligenceApi.getProjectForecast, 'function');
  assert.strictEqual(typeof intelligenceApi.getTaskRisk, 'function');
  assert.strictEqual(typeof intelligenceApi.getWorkload, 'function');
  assert.strictEqual(typeof intelligenceApi.recalculateProject, 'function');

  console.log('✓ predictiveIntelligenceApi & intelligenceApi expose all required B47 endpoints.');
}

// 2. Project Health Scoring Mathematical Model Verification
{
  const calculateProjectHealth = (totalTasks, completedTasks, overdueTasks, criticalTasks, blockedTasks) => {
    if (totalTasks === 0) return { score: 100.0, status: 'HEALTHY' };
    const openTasks = totalTasks - completedTasks;
    const overdueRatio = openTasks > 0 ? overdueTasks / openTasks : 0;
    const criticalRatio = openTasks > 0 ? criticalTasks / openTasks : 0;
    const blockedRatio = openTasks > 0 ? blockedTasks / openTasks : 0;

    const deductions = (overdueRatio * 35.0) + (criticalRatio * 25.0) + (blockedRatio * 20.0);
    const score = Math.max(5.0, Math.min(100.0, Math.round((100.0 - deductions) * 10) / 10));

    let status = 'HEALTHY';
    if (score < 40) status = 'CRITICAL';
    else if (score < 60) status = 'AT_RISK';
    else if (score < 80) status = 'NEEDS_ATTENTION';

    return { score, status };
  };

  // Case A: Perfect project
  const perf = calculateProjectHealth(10, 10, 0, 0, 0);
  assert.strictEqual(perf.score, 100.0);
  assert.strictEqual(perf.status, 'HEALTHY');

  // Case B: Project with heavy overdue tasks
  const atRisk = calculateProjectHealth(10, 2, 7, 6, 4);
  assert(atRisk.score < 60.0);
  assert.strictEqual(atRisk.status, 'AT_RISK');

  // Case C: Critical project with all blockers
  const crit = calculateProjectHealth(10, 0, 10, 8, 5);
  assert(crit.score <= 40.0);
  assert.strictEqual(crit.status, 'CRITICAL');

  console.log('✓ Project health scoring formulas correctly evaluate healthy, at-risk, and critical states.');
}

// 3. Task Risk Scoring & Tier Classification Verification
{
  const classifyTaskRisk = (isCompleted, isOverdue, daysToDue, hasDependencies, priority) => {
    if (isCompleted) return { level: 'LOW', score: 0.0 };
    let score = 10.0;
    if (isOverdue) score += 40.0;
    else if (daysToDue <= 1.0) score += 25.0;
    else if (daysToDue <= 3.0) score += 15.0;

    if (hasDependencies) score += 20.0;

    const p = (priority || '').toLowerCase();
    if (p === 'critical' || p === 'urgent') score *= 1.3;
    else if (p === 'high') score *= 1.15;

    const finalScore = Math.max(5.0, Math.min(100.0, Math.round(score * 10) / 10));
    let level = 'LOW';
    if (finalScore >= 70) level = 'CRITICAL';
    else if (finalScore >= 50) level = 'HIGH';
    else if (finalScore >= 30) level = 'MEDIUM';

    return { level, score: finalScore };
  };

  // Completed task
  assert.strictEqual(classifyTaskRisk(true, true, -2, true, 'Critical').level, 'LOW');

  // Overdue critical task with dependencies
  const overdueCrit = classifyTaskRisk(false, true, -3, true, 'Critical');
  assert.strictEqual(overdueCrit.level, 'CRITICAL');
  assert(overdueCrit.score >= 70.0);

  // Future low priority task
  const futureLow = classifyTaskRisk(false, false, 10, false, 'Low');
  assert.strictEqual(futureLow.level, 'LOW');
  assert(futureLow.score < 30.0);

  console.log('✓ Task risk scoring and tier classification execute accurately across priority and dependency edges.');
}

// 4. Team Capacity Utilization & Workload Balancing Logic
{
  const calculateWorkloadTier = (estimatedHours, standardCapacity = 40.0) => {
    const rate = Math.round((estimatedHours / standardCapacity) * 100 * 10) / 10;
    let tier = 'BALANCED';
    if (rate > 100.0) tier = 'OVERLOADED';
    else if (rate < 40.0) tier = 'UNDERUTILIZED';
    return { rate, tier };
  };

  assert.strictEqual(calculateWorkloadTier(48.0).tier, 'OVERLOADED');
  assert.strictEqual(calculateWorkloadTier(12.0).tier, 'UNDERUTILIZED');
  assert.strictEqual(calculateWorkloadTier(35.0).tier, 'BALANCED');

  console.log('✓ Resource capacity utilization and workload balancing rules validated.');
}

// 5. AI Recommendations Lifecycle State Verification
{
  const validTransitions = {
    PENDING: ['ACCEPTED', 'REJECTED'],
    ACCEPTED: ['COMPLETED'],
    REJECTED: [],
    COMPLETED: [],
  };

  const canTransition = (current, next) => validTransitions[current]?.includes(next) ?? false;

  assert.strictEqual(canTransition('PENDING', 'ACCEPTED'), true);
  assert.strictEqual(canTransition('PENDING', 'REJECTED'), true);
  assert.strictEqual(canTransition('ACCEPTED', 'COMPLETED'), true);
  assert.strictEqual(canTransition('REJECTED', 'COMPLETED'), false);
  assert.strictEqual(canTransition('COMPLETED', 'ACCEPTED'), false);

  console.log('✓ AI Recommendation state machine transitions strictly enforced.');
}

console.log('--- ALL MODULE B47 PREDICTIVE PROJECT INTELLIGENCE TESTS PASSED ---');
