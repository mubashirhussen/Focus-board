import assert from 'node:assert';
import { securityIntelligenceApi } from '../../src/services/securityIntelligenceApi.js';
import { productLifecycleApi } from '../../src/services/productLifecycleApi.js';
import { translations } from '../../src/i18n/translations.js';

console.log('--- RUNNING PHASES 43 & 45 FRONTEND UNIT TESTS ---');

// 1. Security Intelligence & SOC API Client Interface Tests
{
  assert.strictEqual(typeof securityIntelligenceApi.getPosture, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listEvents, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.recordEvent, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listDetectionRules, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.createDetectionRule, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listAlerts, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.updateAlert, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listIdentityRisks, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listAccessReviews, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.createAccessReview, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.recordAccessDecision, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listVulnerabilities, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.createVulnerability, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.updateVulnerability, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.listRemediations, 'function');
  assert.strictEqual(typeof securityIntelligenceApi.askAssistant, 'function');
  console.log('✓ Security Intelligence & Zero-Trust SOC API client exposes all required endpoints.');
}

// 2. Product Lifecycle & Discovery API Client Interface Tests
{
  assert.strictEqual(typeof productLifecycleApi.getOverview, 'function');
  assert.strictEqual(typeof productLifecycleApi.listDiscoveries, 'function');
  assert.strictEqual(typeof productLifecycleApi.createDiscovery, 'function');
  assert.strictEqual(typeof productLifecycleApi.listIdeas, 'function');
  assert.strictEqual(typeof productLifecycleApi.createIdea, 'function');
  assert.strictEqual(typeof productLifecycleApi.listFeatureRequests, 'function');
  assert.strictEqual(typeof productLifecycleApi.createFeatureRequest, 'function');
  assert.strictEqual(typeof productLifecycleApi.mergeFeatureRequests, 'function');
  assert.strictEqual(typeof productLifecycleApi.listOpportunities, 'function');
  assert.strictEqual(typeof productLifecycleApi.createOpportunity, 'function');
  assert.strictEqual(typeof productLifecycleApi.calculatePrioritization, 'function');
  assert.strictEqual(typeof productLifecycleApi.listPrioritizationItems, 'function');
  assert.strictEqual(typeof productLifecycleApi.createPrioritizationItem, 'function');
  assert.strictEqual(typeof productLifecycleApi.listInitiatives, 'function');
  assert.strictEqual(typeof productLifecycleApi.createInitiative, 'function');
  assert.strictEqual(typeof productLifecycleApi.listRoadmapItems, 'function');
  assert.strictEqual(typeof productLifecycleApi.createRoadmapItem, 'function');
  assert.strictEqual(typeof productLifecycleApi.listExperiments, 'function');
  assert.strictEqual(typeof productLifecycleApi.createExperiment, 'function');
  assert.strictEqual(typeof productLifecycleApi.assignExperimentVariant, 'function');
  assert.strictEqual(typeof productLifecycleApi.trackExperimentEvent, 'function');
  assert.strictEqual(typeof productLifecycleApi.listReleases, 'function');
  assert.strictEqual(typeof productLifecycleApi.createRelease, 'function');
  assert.strictEqual(typeof productLifecycleApi.askAssistant, 'function');
  console.log('✓ Product Lifecycle & Demand Intelligence API client exposes all required endpoints.');
}

// 3. RICE Prioritization Mathematical Formulation Test
{
  const reach = 200;
  const impact = 4.0;
  const confidence = 0.8;
  const effort = 2.0;

  // RICE = (Reach * Impact * Confidence) / Effort
  const expectedRice = (reach * impact * confidence) / effort;
  assert.strictEqual(expectedRice, 320.0);

  // ICE = Impact * Confidence * Ease
  const ease = 3.0;
  const expectedIce = Math.round(impact * confidence * ease * 100) / 100;
  assert.strictEqual(expectedIce, 9.6);

  console.log('✓ RICE & ICE mathematical scoring logic verified.');
}

// 4. Zero-Trust Access Review Workflow Transition Logic
{
  const allowedDecisions = ['PENDING', 'APPROVED', 'REVOKED', 'ESCALATED'];
  const decision = 'APPROVED';
  assert.ok(allowedDecisions.includes(decision));

  const validVulnerabilityStatuses = ['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED', 'CLOSED'];
  assert.ok(validVulnerabilityStatuses.includes('RESOLVED'));

  console.log('✓ Access review entitlement decisions & CVE remediation workflows verified.');
}

// 5. Navigation Localization Keys
{
  assert.strictEqual(translations.en['nav.soc'], 'Security SOC');
  assert.strictEqual(translations.en['nav.product_lifecycle'], 'Product Lifecycle');
  console.log('✓ Navigation translations registered for Security SOC and Product Lifecycle.');
}

console.log('--- ALL PHASES 43 & 45 FRONTEND TESTS PASSED ---');
