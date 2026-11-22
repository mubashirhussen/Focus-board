import assert from 'node:assert';
import { observabilityApi } from '../../src/services/observabilityApi.js';
import { dataIntelligenceApi } from '../../src/services/dataIntelligenceApi.js';
import { translations } from '../../src/i18n/translations.js';

console.log('--- RUNNING PHASES 41 & 42 FRONTEND UNIT TESTS ---');

// 1. Observability & Operations API Client Interface Tests
{
  assert.strictEqual(typeof observabilityApi.getOverview, 'function');
  assert.strictEqual(typeof observabilityApi.listServices, 'function');
  assert.strictEqual(typeof observabilityApi.listAlerts, 'function');
  assert.strictEqual(typeof observabilityApi.createAlert, 'function');
  assert.strictEqual(typeof observabilityApi.acknowledgeAlert, 'function');
  assert.strictEqual(typeof observabilityApi.resolveAlert, 'function');
  assert.strictEqual(typeof observabilityApi.listIncidents, 'function');
  assert.strictEqual(typeof observabilityApi.getIncident, 'function');
  assert.strictEqual(typeof observabilityApi.createIncident, 'function');
  assert.strictEqual(typeof observabilityApi.updateIncident, 'function');
  assert.strictEqual(typeof observabilityApi.addActionItem, 'function');
  assert.strictEqual(typeof observabilityApi.createPostMortem, 'function');
  assert.strictEqual(typeof observabilityApi.runSupportDiagnostics, 'function');
  assert.strictEqual(typeof observabilityApi.listMaintenance, 'function');
  assert.strictEqual(typeof observabilityApi.createMaintenance, 'function');
  console.log('✓ Observability & Platform Operations API client exposes all required endpoints.');
}

// 2. Data Intelligence & BI API Client Interface Tests
{
  assert.strictEqual(typeof dataIntelligenceApi.getOverview, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.listDatasets, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.listPipelines, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.runPipeline, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.listDashboards, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.getDashboard, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.createDashboard, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.deleteDashboard, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.listReports, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.createReport, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.executeReport, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.listQualityRules, 'function');
  assert.strictEqual(typeof dataIntelligenceApi.queryAiAssistant, 'function');
  console.log('✓ Data Intelligence & BI API client exposes all required endpoints.');
}

// 3. Operational Severity & Incident Transition Logic
{
  const validTransitions = {
    DETECTED: ['INVESTIGATING', 'CLOSED'],
    INVESTIGATING: ['IDENTIFIED', 'MITIGATING'],
    IDENTIFIED: ['MITIGATING'],
    MITIGATING: ['RESOLVED'],
    RESOLVED: ['CLOSED', 'INVESTIGATING'],
    CLOSED: [],
  };

  function canTransitionIncident(current, target) {
    return (validTransitions[current] || []).includes(target);
  }

  assert.strictEqual(canTransitionIncident('DETECTED', 'INVESTIGATING'), true);
  assert.strictEqual(canTransitionIncident('INVESTIGATING', 'MITIGATING'), true);
  assert.strictEqual(canTransitionIncident('MITIGATING', 'RESOLVED'), true);
  assert.strictEqual(canTransitionIncident('CLOSED', 'DETECTED'), false);
  console.log('✓ Incident state transition workflow validation verified.');
}

// 4. Data Quality Score Calculation
{
  function computeQualityScore(rules) {
    if (!rules || rules.length === 0) return 100.0;
    const passed = rules.filter(r => r.status === 'PASS').length;
    return Math.round((passed / rules.length) * 1000) / 10;
  }

  const sampleRules = [
    { rule_name: 'r1', status: 'PASS' },
    { rule_name: 'r2', status: 'PASS' },
    { rule_name: 'r3', status: 'PASS' },
    { rule_name: 'r4', status: 'FAIL' },
  ];
  assert.strictEqual(computeQualityScore(sampleRules), 75.0);
  assert.strictEqual(computeQualityScore([]), 100.0);
  console.log('✓ Data quality scoring computation validated.');
}

// 5. Navigation & Translations Registration
{
  assert.strictEqual(translations.en['nav.operations'], 'Platform Ops');
  assert.strictEqual(translations.en['nav.data_intelligence'], 'Data Intelligence');
  console.log('✓ Navigation translations registered for Platform Operations and Data Intelligence.');
}

console.log('--- ALL PHASES 41 & 42 FRONTEND TESTS PASSED ---');
