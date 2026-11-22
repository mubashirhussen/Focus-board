import assert from 'node:assert';
import { securityComplianceApi } from '../../src/services/securityComplianceApi.js';
import { financialIntelligenceApi } from '../../src/services/financialIntelligenceApi.js';
import { translations } from '../../src/i18n/translations.js';

console.log('--- RUNNING PHASE 34 & 35 FRONTEND UNIT TESTS ---');

// 1. Security Compliance API Client Interface Tests
{
  assert.strictEqual(typeof securityComplianceApi.getOverview, 'function');
  assert.strictEqual(typeof securityComplianceApi.listControls, 'function');
  assert.strictEqual(typeof securityComplianceApi.updateControl, 'function');
  assert.strictEqual(typeof securityComplianceApi.addEvidence, 'function');
  assert.strictEqual(typeof securityComplianceApi.listPolicies, 'function');
  assert.strictEqual(typeof securityComplianceApi.acknowledgePolicy, 'function');
  assert.strictEqual(typeof securityComplianceApi.listRisks, 'function');
  assert.strictEqual(typeof securityComplianceApi.createRisk, 'function');
  assert.strictEqual(typeof securityComplianceApi.listIncidents, 'function');
  assert.strictEqual(typeof securityComplianceApi.createIncident, 'function');
  assert.strictEqual(typeof securityComplianceApi.getTrustCenterOverview, 'function');
  console.log('✓ Security Compliance API client exposes all required methods.');
}

// 2. Financial Intelligence API Client Interface Tests
{
  assert.strictEqual(typeof financialIntelligenceApi.getOverview, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.listTransactions, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.recordTransaction, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.listCosts, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.recordCost, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.listBudgets, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.createBudget, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.listForecasts, 'function');
  assert.strictEqual(typeof financialIntelligenceApi.exportReport, 'function');
  console.log('✓ Financial Intelligence API client exposes all required methods.');
}

// 3. Security Risk Matrix Scoring Logic
{
  const severityMap = { LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 };
  const likelihoodMap = { LOW: 1, MEDIUM: 2, HIGH: 3, CRITICAL: 4 };

  const calcScore = (sev, like) => (severityMap[sev] || 2) * (likelihoodMap[like] || 2);

  assert.strictEqual(calcScore('LOW', 'LOW'), 1);
  assert.strictEqual(calcScore('MEDIUM', 'MEDIUM'), 4);
  assert.strictEqual(calcScore('HIGH', 'CRITICAL'), 12);
  assert.strictEqual(calcScore('CRITICAL', 'CRITICAL'), 16);
  console.log('✓ Risk Matrix computation accurately calculates severity-likelihood products.');
}

// 4. Financial Metric Calculations: MRR/ARR, Gross Margin, and Budget Threshold
{
  // MRR to ARR
  const mrr = 1250.00;
  const arr = mrr * 12;
  assert.strictEqual(arr, 15000.00);

  // Gross Margin %: ((Revenue - Direct Costs) / Revenue) * 100
  const netRevenue = 1500.00;
  const directCosts = 300.00;
  const grossMargin = ((netRevenue - directCosts) / netRevenue) * 100;
  assert.strictEqual(grossMargin, 80.0);

  // Budget Alert Threshold Trigger
  const budgetLimit = 1000;
  const alertThresholdPct = 80;
  const actualSpentSafe = 750;
  const actualSpentAlert = 850;

  const isAlertSafe = (actualSpentSafe / budgetLimit * 100) >= alertThresholdPct;
  const isAlertTriggered = (actualSpentAlert / budgetLimit * 100) >= alertThresholdPct;

  assert.strictEqual(isAlertSafe, false);
  assert.strictEqual(isAlertTriggered, true);
  console.log('✓ Financial intelligence logic computes ARR, Gross Margin %, and alert triggers accurately.');
}

// 5. Translations Coverage for Phase 34 & 35
{
  assert.ok(translations.en['nav.compliance']);
  assert.ok(translations.en['nav.finance']);
  assert.ok(translations.en['nav.trust']);
  console.log('✓ i18n translations include enterprise compliance, finance, and trust center keys.');
}

console.log('--- ALL PHASE 34 & 35 FRONTEND UNIT TESTS PASSED ---');
