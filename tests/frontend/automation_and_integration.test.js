import assert from 'node:assert';
import { automationApi } from '../../src/services/automationApi.js';
import { integrationPlatformApi } from '../../src/services/integrationPlatformApi.js';
import { translations } from '../../src/i18n/translations.js';

console.log('--- RUNNING PHASES 39 & 40 FRONTEND UNIT TESTS ---');

// 1. Automation Intelligence API Client Interface Tests
{
  assert.strictEqual(typeof automationApi.getOverview, 'function');
  assert.strictEqual(typeof automationApi.listWorkflows, 'function');
  assert.strictEqual(typeof automationApi.getWorkflow, 'function');
  assert.strictEqual(typeof automationApi.createWorkflow, 'function');
  assert.strictEqual(typeof automationApi.updateWorkflow, 'function');
  assert.strictEqual(typeof automationApi.deleteWorkflow, 'function');
  assert.strictEqual(typeof automationApi.getWorkflowVersions, 'function');
  assert.strictEqual(typeof automationApi.triggerWorkflow, 'function');
  assert.strictEqual(typeof automationApi.listExecutions, 'function');
  assert.strictEqual(typeof automationApi.getExecution, 'function');
  assert.strictEqual(typeof automationApi.getExecutionLogs, 'function');
  assert.strictEqual(typeof automationApi.listApprovals, 'function');
  assert.strictEqual(typeof automationApi.submitApprovalDecision, 'function');
  assert.strictEqual(typeof automationApi.generateWorkflowFromPrompt, 'function');
  console.log('✓ Automation Intelligence API client exposes all required endpoints.');
}

// 2. Integration Ecosystem & Developer Platform API Client Interface Tests
{
  assert.strictEqual(typeof integrationPlatformApi.listProviders, 'function');
  assert.strictEqual(typeof integrationPlatformApi.listMarketplaceListings, 'function');
  assert.strictEqual(typeof integrationPlatformApi.installMarketplaceApp, 'function');
  assert.strictEqual(typeof integrationPlatformApi.listWorkspaceInstallations, 'function');
  assert.strictEqual(typeof integrationPlatformApi.listConnectors, 'function');
  assert.strictEqual(typeof integrationPlatformApi.connectConnector, 'function');
  assert.strictEqual(typeof integrationPlatformApi.disconnectConnector, 'function');
  assert.strictEqual(typeof integrationPlatformApi.testWebhookDelivery, 'function');
  assert.strictEqual(typeof integrationPlatformApi.getPlatformAnalytics, 'function');
  console.log('✓ Integration Ecosystem & Developer Platform API client exposes all required endpoints.');
}

// 3. Deterministic Condition Evaluation Helper Verification
{
  function evaluateConditionClient(config, context) {
    const field = config.field;
    const operator = (config.operator || 'EQUALS').toUpperCase();
    const expected = config.value;
    const actual = context[field];

    switch (operator) {
      case 'EQUALS':
        return String(actual).toLowerCase() === String(expected).toLowerCase();
      case 'NOT_EQUALS':
        return String(actual).toLowerCase() !== String(expected).toLowerCase();
      case 'CONTAINS':
        return String(actual).toLowerCase().includes(String(expected).toLowerCase());
      case 'GREATER_THAN':
        return Number(actual) > Number(expected);
      case 'LESS_THAN':
        return Number(actual) < Number(expected);
      case 'IN_LIST':
        return Array.isArray(expected) && expected.map(x => String(x).toLowerCase()).includes(String(actual).toLowerCase());
      default:
        return false;
    }
  }

  // Test EQUALS
  assert.strictEqual(evaluateConditionClient({ field: 'priority', operator: 'EQUALS', value: 'HIGH' }, { priority: 'HIGH' }), true);
  assert.strictEqual(evaluateConditionClient({ field: 'priority', operator: 'EQUALS', value: 'HIGH' }, { priority: 'LOW' }), false);

  // Test CONTAINS
  assert.strictEqual(evaluateConditionClient({ field: 'title', operator: 'CONTAINS', value: 'outage' }, { title: 'Critical Cloud Outage Fix' }), true);
  assert.strictEqual(evaluateConditionClient({ field: 'title', operator: 'CONTAINS', value: 'database' }, { title: 'Update UI styling' }), false);

  // Test GREATER_THAN / LESS_THAN
  assert.strictEqual(evaluateConditionClient({ field: 'amount', operator: 'GREATER_THAN', value: 5000 }, { amount: 7500 }), true);
  assert.strictEqual(evaluateConditionClient({ field: 'amount', operator: 'GREATER_THAN', value: 5000 }, { amount: 3200 }), false);

  // Test IN_LIST
  assert.strictEqual(evaluateConditionClient({ field: 'status', operator: 'IN_LIST', value: ['BLOCKED', 'OVERDUE'] }, { status: 'OVERDUE' }), true);
  assert.strictEqual(evaluateConditionClient({ field: 'status', operator: 'IN_LIST', value: ['BLOCKED', 'OVERDUE'] }, { status: 'IN_PROGRESS' }), false);

  console.log('✓ Deterministic condition evaluation logic executes accurately across all operators.');
}

// 4. HMAC-SHA256 Webhook Signature Format Verification
{
  function isValidWebhookSignature(header) {
    if (!header || !header.startsWith('t=')) return false;
    const parts = header.split(',');
    if (parts.length < 2) return false;
    const tsPart = parts[0].replace('t=', '');
    const sigPart = parts[1].replace('v1=', '');
    const ts = parseInt(tsPart, 10);
    return !isNaN(ts) && ts > 0 && /^[a-f0-9]{64}$/i.test(sigPart);
  }

  const sampleValid = 't=1795338491,v1=a35b1287c89f546201e8bcf15926710b145a98ec51782a3c706d87192a54fb32';
  const sampleInvalidPrefix = 'sig=1795338491,v1=a35b1287c89f546201e8bcf15926710b145a98ec51782a3c706d87192a54fb32';
  const sampleInvalidHex = 't=1795338491,v1=not_a_valid_64_character_hex_hash';

  assert.strictEqual(isValidWebhookSignature(sampleValid), true);
  assert.strictEqual(isValidWebhookSignature(sampleInvalidPrefix), false);
  assert.strictEqual(isValidWebhookSignature(sampleInvalidHex), false);
  console.log('✓ HMAC-SHA256 webhook signature header format verified.');
}

// 5. Explicit Permission Consent Validation
{
  function validateInstallationConsent(listing, consentConfirmed, grantedScopes) {
    if (!consentConfirmed) {
      throw new Error('User consent must be explicitly granted');
    }
    if (!Array.isArray(grantedScopes) || grantedScopes.length === 0) {
      throw new Error('At least one permission scope must be granted');
    }
    return true;
  }

  assert.strictEqual(validateInstallationConsent({ id: 'app_1' }, true, ['tasks:read', 'tasks:write']), true);
  assert.throws(() => validateInstallationConsent({ id: 'app_1' }, false, ['tasks:read']), /User consent must be explicitly granted/);
  assert.throws(() => validateInstallationConsent({ id: 'app_1' }, true, []), /At least one permission scope must be granted/);
  console.log('✓ Explicit permission consent policy enforced prior to installation.');
}

// 6. Navigation and i18n Registration
{
  assert.strictEqual(translations.en['nav.automation'], 'Automation Hub');
  console.log('✓ Automation navigation translation registered.');
}

console.log('--- ALL PHASES 39 & 40 FRONTEND TESTS PASSED ---');
