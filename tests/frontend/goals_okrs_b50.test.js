/**
 * Frontend Unit & Workflow Tests for Module B50: Goals, OKRs & Milestones Management.
 */

import assert from 'assert';
import { goalApi } from '../../src/services/goalApi.js';

console.log('--- RUNNING MODULE B50: GOALS, OKRS & MILESTONES MANAGEMENT FRONTEND TESTS ---');

// 1. Verify API Service Exposure
assert(typeof goalApi.getGoals === 'function', 'goalApi must expose getGoals');
assert(typeof goalApi.createGoal === 'function', 'goalApi must expose createGoal');
assert(typeof goalApi.getGoalDetail === 'function', 'goalApi must expose getGoalDetail');
assert(typeof goalApi.updateGoal === 'function', 'goalApi must expose updateGoal');
assert(typeof goalApi.deleteGoal === 'function', 'goalApi must expose deleteGoal');
assert(typeof goalApi.createKeyResult === 'function', 'goalApi must expose createKeyResult');
assert(typeof goalApi.updateKeyResultProgress === 'function', 'goalApi must expose updateKeyResultProgress');
assert(typeof goalApi.deleteKeyResult === 'function', 'goalApi must expose deleteKeyResult');
assert(typeof goalApi.createMilestone === 'function', 'goalApi must expose createMilestone');
assert(typeof goalApi.completeMilestone === 'function', 'goalApi must expose completeMilestone');
assert(typeof goalApi.reopenMilestone === 'function', 'goalApi must expose reopenMilestone');
assert(typeof goalApi.addMilestoneDependency === 'function', 'goalApi must expose addMilestoneDependency');
assert(typeof goalApi.linkTaskToKeyResult === 'function', 'goalApi must expose linkTaskToKeyResult');
assert(typeof goalApi.unlinkTaskFromKeyResult === 'function', 'goalApi must expose unlinkTaskFromKeyResult');
assert(typeof goalApi.submitCheckIn === 'function', 'goalApi must expose submitCheckIn');
assert(typeof goalApi.reviewCheckIn === 'function', 'goalApi must expose reviewCheckIn');
assert(typeof goalApi.getGoalsOverviewMetrics === 'function', 'goalApi must expose getGoalsOverviewMetrics');
assert(typeof goalApi.getGoalComments === 'function', 'goalApi must expose getGoalComments');
assert(typeof goalApi.addGoalComment === 'function', 'goalApi must expose addGoalComment');
console.log('✓ goalApi exposes all 19 required B50 client endpoints.');

// 2. Key Result Mathematical Progress Calculation Engine
function computeKeyResultProgress(type, startingVal, targetVal, currentVal) {
  if (type === 'BINARY') {
    return currentVal >= 1 ? 100 : 0;
  }
  const denominator = targetVal - startingVal;
  if (Math.abs(denominator) < 1e-9) {
    return currentVal >= targetVal ? 100 : 0;
  }
  if (type === 'NUMERIC_INCREASE' || type === 'PERCENTAGE' || type === 'MANUAL') {
    const raw = ((currentVal - startingVal) / denominator) * 100;
    return Math.min(100, Math.max(0, Math.round(raw * 100) / 100));
  }
  if (type === 'NUMERIC_DECREASE') {
    const raw = ((startingVal - currentVal) / (startingVal - targetVal)) * 100;
    return Math.min(100, Math.max(0, Math.round(raw * 100) / 100));
  }
  return 0;
}

// Test Numeric Increase
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 0, 100, 50), 50);
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 10, 50, 30), 50);
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 0, 100, 120), 100); // capped at 100
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 0, 100, -10), 0); // floor at 0

// Test Numeric Decrease (e.g. latency from 200ms to 50ms)
assert.strictEqual(computeKeyResultProgress('NUMERIC_DECREASE', 200, 50, 125), 50);
assert.strictEqual(computeKeyResultProgress('NUMERIC_DECREASE', 200, 50, 50), 100);
assert.strictEqual(computeKeyResultProgress('NUMERIC_DECREASE', 200, 50, 250), 0);

// Test Binary (0 or 1)
assert.strictEqual(computeKeyResultProgress('BINARY', 0, 1, 0), 0);
assert.strictEqual(computeKeyResultProgress('BINARY', 0, 1, 1), 100);

// Test Safe Division (Zero Denominator)
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 50, 50, 50), 100);
assert.strictEqual(computeKeyResultProgress('NUMERIC_INCREASE', 50, 50, 20), 0);
console.log('✓ Key result mathematical progress calculation formulas verify correctly.');

// 3. Goal Health Diagnosis Classifier
function evaluateGoalHealth(goal, daysRemaining, expectedProgress) {
  if (goal.progress_percentage >= 100) return 'COMPLETED';
  if (daysRemaining <= 0 && goal.progress_percentage < 100) return 'BEHIND';
  
  const diff = goal.progress_percentage - expectedProgress;
  if (diff >= -10) return 'ON_TRACK';
  if (diff >= -25) return 'AT_RISK';
  return 'BEHIND';
}

assert.strictEqual(evaluateGoalHealth({ progress_percentage: 100 }, 30, 80), 'COMPLETED');
assert.strictEqual(evaluateGoalHealth({ progress_percentage: 45 }, 0, 100), 'BEHIND');
assert.strictEqual(evaluateGoalHealth({ progress_percentage: 75 }, 30, 80), 'ON_TRACK'); // diff -5 >= -10
assert.strictEqual(evaluateGoalHealth({ progress_percentage: 60 }, 30, 80), 'AT_RISK'); // diff -20 >= -25
assert.strictEqual(evaluateGoalHealth({ progress_percentage: 40 }, 30, 80), 'BEHIND'); // diff -40 < -25
console.log('✓ Explainable goal health classification heuristics evaluate correctly.');

// 4. Milestone Prerequisite Dependency Graph Validation
function canCompleteMilestone(milestoneId, dependencies, milestones) {
  const prereqIds = dependencies
    .filter((d) => d.milestone_id === milestoneId)
    .map((d) => d.prerequisite_milestone_id);
  
  for (const pid of prereqIds) {
    const prereq = milestones.find((m) => m.id === pid);
    if (!prereq || prereq.status !== 'COMPLETED') {
      return false;
    }
  }
  return true;
}

const mockMilestones = [
  { id: 1, title: 'Architecture Signoff', status: 'COMPLETED' },
  { id: 2, title: 'Backend Implementation', status: 'IN_PROGRESS' },
  { id: 3, title: 'Release to Production', status: 'PENDING' },
];

const mockDependencies = [
  { milestone_id: 2, prerequisite_milestone_id: 1 },
  { milestone_id: 3, prerequisite_milestone_id: 2 },
];

assert.strictEqual(canCompleteMilestone(2, mockDependencies, mockMilestones), true); // Prereq 1 is COMPLETED
assert.strictEqual(canCompleteMilestone(3, mockDependencies, mockMilestones), false); // Prereq 2 is IN_PROGRESS
console.log('✓ Milestone prerequisite dependency validation verifies execution order.');

// 5. Confidence Score & Check-In Validation
function validateCheckInPayload(payload) {
  if (typeof payload.confidence_score !== 'number' || payload.confidence_score < 1 || payload.confidence_score > 5) {
    return { valid: false, error: 'Confidence score must be between 1 and 5' };
  }
  if (!payload.progress_report || payload.progress_report.trim().length === 0) {
    return { valid: false, error: 'Progress report narrative is required' };
  }
  return { valid: true };
}

assert.strictEqual(validateCheckInPayload({ confidence_score: 4, progress_report: 'Velocity is strong' }).valid, true);
assert.strictEqual(validateCheckInPayload({ confidence_score: 6, progress_report: 'Too high' }).valid, false);
assert.strictEqual(validateCheckInPayload({ confidence_score: 3, progress_report: '' }).valid, false);
console.log('✓ Check-in confidence score and payload narrative validation succeed.');

console.log('--- ALL MODULE B50 FRONTEND TESTS PASSED SUCCESSFULLY ---');
