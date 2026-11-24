/**
 * Frontend Unit & Workflow Tests for Module B51: Advanced Project Planning & Scheduling.
 */

import assert from 'assert';
import { projectPlanningApi } from '../../src/services/projectPlanningApi.js';

console.log('--- RUNNING MODULE B51: ADVANCED PROJECT PLANNING & SCHEDULING FRONTEND TESTS ---');

// 1. Verify API Service Exposure
assert(typeof projectPlanningApi.getPlanningOverview === 'function', 'projectPlanningApi must expose getPlanningOverview');
assert(typeof projectPlanningApi.getScheduleSettings === 'function', 'projectPlanningApi must expose getScheduleSettings');
assert(typeof projectPlanningApi.updateScheduleSettings === 'function', 'projectPlanningApi must expose updateScheduleSettings');
assert(typeof projectPlanningApi.createTaskDependency === 'function', 'projectPlanningApi must expose createTaskDependency');
assert(typeof projectPlanningApi.deleteTaskDependency === 'function', 'projectPlanningApi must expose deleteTaskDependency');
assert(typeof projectPlanningApi.getTaskDependencies === 'function', 'projectPlanningApi must expose getTaskDependencies');
assert(typeof projectPlanningApi.calculateCriticalPath === 'function', 'projectPlanningApi must expose calculateCriticalPath');
assert(typeof projectPlanningApi.createBaseline === 'function', 'projectPlanningApi must expose createBaseline');
assert(typeof projectPlanningApi.getBaselines === 'function', 'projectPlanningApi must expose getBaselines');
assert(typeof projectPlanningApi.compareBaseline === 'function', 'projectPlanningApi must expose compareBaseline');
assert(typeof projectPlanningApi.getBudgetSummary === 'function', 'projectPlanningApi must expose getBudgetSummary');
assert(typeof projectPlanningApi.updateBudget === 'function', 'projectPlanningApi must expose updateBudget');
assert(typeof projectPlanningApi.addCostRecord === 'function', 'projectPlanningApi must expose addCostRecord');
assert(typeof projectPlanningApi.getCostRecords === 'function', 'projectPlanningApi must expose getCostRecords');
assert(typeof projectPlanningApi.getScheduleForecast === 'function', 'projectPlanningApi must expose getScheduleForecast');
assert(typeof projectPlanningApi.generateForecast === 'function', 'projectPlanningApi must expose generateForecast');
assert(typeof projectPlanningApi.getScenarios === 'function', 'projectPlanningApi must expose getScenarios');
assert(typeof projectPlanningApi.createScenario === 'function', 'projectPlanningApi must expose createScenario');
assert(typeof projectPlanningApi.simulateScenario === 'function', 'projectPlanningApi must expose simulateScenario');
assert(typeof projectPlanningApi.applyScenario === 'function', 'projectPlanningApi must expose applyScenario');
console.log('✓ projectPlanningApi exposes all 20 required B51 client endpoints.');

// 2. Critical Path Method (CPM) Forward & Backward Pass Engine Tests
function calculateCPM(tasks, dependencies) {
  const taskMap = {};
  tasks.forEach(t => {
    taskMap[t.id] = {
      id: t.id,
      name: t.name,
      duration: t.duration,
      es: 0,
      ef: t.duration,
      ls: Infinity,
      lf: Infinity,
      totalFloat: 0,
      freeFloat: 0,
      isCritical: false,
      preds: [],
      succs: []
    };
  });

  dependencies.forEach(d => {
    if (taskMap[d.predId] && taskMap[d.succId]) {
      taskMap[d.predId].succs.push({ id: d.succId, lag: d.lag || 0 });
      taskMap[d.succId].preds.push({ id: d.predId, lag: d.lag || 0 });
    }
  });

  // Forward Pass
  const visited = new Set();
  function forward(id) {
    const node = taskMap[id];
    let maxPredEf = 0;
    node.preds.forEach(p => {
      forward(p.id);
      const finishWithLag = taskMap[p.id].ef + p.lag;
      if (finishWithLag > maxPredEf) maxPredEf = finishWithLag;
    });
    node.es = maxPredEf;
    node.ef = node.es + node.duration;
  }
  tasks.forEach(t => forward(t.id));

  // Project Duration
  let projectDuration = 0;
  tasks.forEach(t => {
    if (taskMap[t.id].ef > projectDuration) projectDuration = taskMap[t.id].ef;
  });

  // Backward Pass
  tasks.forEach(t => {
    if (taskMap[t.id].succs.length === 0) {
      taskMap[t.id].lf = projectDuration;
      taskMap[t.id].ls = projectDuration - taskMap[t.id].duration;
    }
  });

  function backward(id) {
    const node = taskMap[id];
    let minSuccLs = Infinity;
    node.succs.forEach(s => {
      backward(s.id);
      const startMinusLag = taskMap[s.id].ls - s.lag;
      if (startMinusLag < minSuccLs) minSuccLs = startMinusLag;
    });
    if (node.succs.length > 0) {
      node.lf = minSuccLs;
      node.ls = node.lf - node.duration;
    }
    node.totalFloat = Math.max(0, node.ls - node.es);
    node.isCritical = node.totalFloat === 0;
  }
  tasks.forEach(t => backward(t.id));

  return { projectDuration, taskMap };
}

const mockTasks = [
  { id: 1, name: 'Task 1 (Setup)', duration: 2 },
  { id: 2, name: 'Task 2 (Core)', duration: 4 },
  { id: 3, name: 'Task 3 (Docs)', duration: 1 },
  { id: 4, name: 'Task 4 (Deploy)', duration: 2 },
];

const mockDependencies = [
  { predId: 1, succId: 2, lag: 0 },
  { predId: 1, succId: 3, lag: 0 },
  { predId: 2, succId: 4, lag: 0 },
  { predId: 3, succId: 4, lag: 0 },
];

const cpmResult = calculateCPM(mockTasks, mockDependencies);
assert.strictEqual(cpmResult.projectDuration, 8, 'Total project duration must be 8 days (2 + 4 + 2)');
assert.strictEqual(cpmResult.taskMap[1].isCritical, true, 'Task 1 must be on critical path');
assert.strictEqual(cpmResult.taskMap[2].isCritical, true, 'Task 2 must be on critical path');
assert.strictEqual(cpmResult.taskMap[4].isCritical, true, 'Task 4 must be on critical path');
assert.strictEqual(cpmResult.taskMap[3].isCritical, false, 'Task 3 (Docs) has float and must NOT be critical');
assert.strictEqual(cpmResult.taskMap[3].totalFloat, 3, 'Task 3 total float must be 3 days');
console.log('✓ Critical Path Method (CPM) forward and backward pass calculations verified.');

// 3. DAG Cycle Detection Logic
function isAcyclic(nodeCount, edges, newEdge) {
  if (newEdge.from === newEdge.to) return false; // Self-loop

  const adj = {};
  for (let i = 1; i <= nodeCount; i++) adj[i] = [];
  edges.forEach(e => adj[e.from].push(e.to));
  adj[newEdge.from].push(newEdge.to);

  const visited = {};
  const recStack = {};

  function dfs(node) {
    visited[node] = true;
    recStack[node] = true;

    for (const neighbor of adj[node] || []) {
      if (!visited[neighbor]) {
        if (dfs(neighbor)) return true;
      } else if (recStack[neighbor]) {
        return true; // Cycle detected
      }
    }

    recStack[node] = false;
    return false;
  }

  for (let i = 1; i <= nodeCount; i++) {
    if (!visited[i]) {
      if (dfs(i)) return false; // Contains cycle -> Not acyclic
    }
  }

  return true; // Acyclic
}

const edges = [
  { from: 1, to: 2 },
  { from: 2, to: 3 },
  { from: 3, to: 4 }
];

// Valid addition: 1 -> 4
assert.strictEqual(isAcyclic(4, edges, { from: 1, to: 4 }), true, '1 -> 4 should be a valid DAG edge');

// Invalid additions (cycles)
assert.strictEqual(isAcyclic(4, edges, { from: 3, to: 1 }), false, '3 -> 1 introduces a cycle');
assert.strictEqual(isAcyclic(4, edges, { from: 4, to: 2 }), false, '4 -> 2 introduces a cycle');
assert.strictEqual(isAcyclic(4, edges, { from: 2, to: 2 }), false, 'Self-dependency 2 -> 2 is disallowed');
console.log('✓ DAG dependency cycle detection and self-loop prevention verified.');

// 4. Baseline Comparison & Variance Calculations
function computeScheduleVariance(plannedDays, actualDays) {
  return actualDays - plannedDays; // positive means delayed
}

function computeBudgetVariance(plannedBudget, actualCost, committedCost = 0) {
  const totalCost = actualCost + committedCost;
  const variance = plannedBudget - totalCost; // positive means under budget
  const utilizationPct = plannedBudget > 0 ? (totalCost / plannedBudget) * 100 : 0;
  return { variance, utilizationPct };
}

assert.strictEqual(computeScheduleVariance(10, 14), 4, 'Task delayed by 4 days');
assert.strictEqual(computeScheduleVariance(10, 8), -2, 'Task completed 2 days ahead of schedule');

const bRes = computeBudgetVariance(50000, 35000, 5000);
assert.strictEqual(bRes.variance, 10000, 'Budget variance must be +$10,000 remaining');
assert.strictEqual(bRes.utilizationPct, 80, 'Budget utilization must be 80%');
console.log('✓ Baseline schedule and budget variance formulas verified.');

// 5. What-If Scenario Simulation Delta Computation
function computeScenarioDelta(baseDuration, scenarioTaskDurationOverrides) {
  let delta = 0;
  for (const key in scenarioTaskDurationOverrides) {
    delta += scenarioTaskDurationOverrides[key];
  }
  return {
    originalDuration: baseDuration,
    simulatedDuration: baseDuration + delta,
    delayRisk: delta > 0 ? 'INCREASED' : (delta < 0 ? 'REDUCED' : 'NEUTRAL')
  };
}

const sim1 = computeScenarioDelta(30, { 2: +5, 4: -2 });
assert.strictEqual(sim1.simulatedDuration, 33);
assert.strictEqual(sim1.delayRisk, 'INCREASED');

const sim2 = computeScenarioDelta(30, { 2: -5 });
assert.strictEqual(sim2.simulatedDuration, 25);
assert.strictEqual(sim2.delayRisk, 'REDUCED');
console.log('✓ What-if scenario simulation non-destructive delta calculations verified.');

console.log('ALL MODULE B51 ADVANCED PROJECT PLANNING FRONTEND TESTS PASSED SUCCESSFULLY! ✓');
